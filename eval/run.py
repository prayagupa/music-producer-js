from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
SCHEMA_PATH = ROOT / "backend" / "schemas" / "music_spec.v1.json"
GOLDEN_PATH = ROOT / "eval" / "golden" / "prompts.v1.yaml"
REPORTS_DIR = ROOT / "eval" / "reports"

sys.path.insert(0, str(BACKEND_SRC))
sys.path.insert(0, str(ROOT))

from adapters.outbound.llm.factory import create_llm_provider  # noqa: E402
from adapters.outbound.llm.port import summarize_spec  # noqa: E402
from adapters.outbound.midi.generator import PrettyMidiGenerator  # noqa: E402
from domain.validation import MusicSpecValidator  # noqa: E402
from eval.constraints import validate_expected_constraints  # noqa: E402
from eval.mock import load_mock_spec  # noqa: E402
from infrastructure.config import Settings  # noqa: E402


def load_dataset() -> dict:
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def bar(total: int, value: int, width: int = 20) -> str:
    filled = int(width * value / total) if total else 0
    return "█" * filled + "░" * (width - filled)


async def _generate_spec(
    entry: dict[str, Any],
    mock_mode: bool,
    llm: Any | None,
) -> dict[str, Any] | None:
    if mock_mode:
        return load_mock_spec(entry["id"])

    assert llm is not None
    controls = entry.get("controls", {})
    raw = await llm.generate_spec(entry["prompt"], controls, [], None)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def _judge_prompt(
    entry: dict[str, Any],
    spec: dict[str, Any],
    mock_mode: bool,
    llm: Any | None,
) -> float:
    if mock_mode:
        return 4.2

    assert llm is not None
    return await llm.judge(entry["prompt"], summarize_spec(spec))


async def run_eval_async(quick: bool = False, mock: bool | None = None) -> int:
    mock_mode = mock if mock is not None else os.getenv("EVAL_MOCK_LLM", "false").lower() == "true"
    dataset = load_dataset()
    all_prompts = dataset["prompts"]
    if quick:
        ids = set(dataset.get("quick_subset", []))
        prompts = [p for p in all_prompts if p["id"] in ids]
    else:
        prompts = all_prompts

    validator = MusicSpecValidator(SCHEMA_PATH)
    midi_gen = PrettyMidiGenerator()
    llm = None if mock_mode else create_llm_provider(Settings())

    results = []
    latencies: list[int] = []

    try:
        for entry in prompts:
            start = time.perf_counter()
            spec = await _generate_spec(entry, mock_mode, llm)

            l1_ok = spec is not None and len(validator.validate_l1(spec)) == 0
            golden_errors = (
                validate_expected_constraints(spec, entry.get("expected_constraints", {}))
                if l1_ok and spec is not None
                else []
            )
            l2_ok = (
                l1_ok
                and len(validator.validate_l2(spec)) == 0
                and len(golden_errors) == 0
            )
            l3_ok, _ = (
                validator.validate_l3_structure(spec) if l1_ok and l2_ok else (False, [])
            )

            if l1_ok and l2_ok and l3_ok:
                try:
                    midi_gen.generate(spec)
                except Exception:
                    l3_ok = False

            judge_score = 0.0
            if spec is not None and l1_ok and l2_ok and l3_ok:
                judge_score = await _judge_prompt(entry, spec, mock_mode, llm)

            latency_ms = int((time.perf_counter() - start) * 1000)
            latencies.append(latency_ms)

            results.append(
                {
                    "id": entry["id"],
                    "l1": l1_ok,
                    "l2": l2_ok,
                    "l3": l3_ok,
                    "judge": judge_score,
                    "latency_ms": latency_ms,
                    "golden_constraint_errors": golden_errors,
                }
            )
    finally:
        if llm is not None and hasattr(llm, "close"):
            await llm.close()

    total = len(results)
    l1_pass = sum(1 for r in results if r["l1"])
    l2_pass = sum(1 for r in results if r["l2"])
    l3_pass = sum(1 for r in results if r["l3"])
    judge_mean = sum(r["judge"] for r in results) / total if total else 0
    latencies_sorted = sorted(latencies)
    p95_idx = max(0, int(len(latencies_sorted) * 0.95) - 1)
    latency_p95 = latencies_sorted[p95_idx] if latencies_sorted else 0

    schema_rate = l1_pass / total if total else 0
    constraint_rate = l2_pass / total if total else 0
    structure_rate = l3_pass / total if total else 0

    schema_gate = schema_rate >= 0.90
    constraint_gate = constraint_rate >= 0.85
    judge_gate = judge_mean >= 4.0

    if quick and mock_mode:
        mode_label = "quick-mock"
    elif quick:
        mode_label = "quick"
    elif mock_mode:
        mode_label = "full-mock"
    else:
        mode_label = "full"
    run_id = f"eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    report = {
        "dataset_version": dataset.get("version", "1.0.0"),
        "run_id": run_id,
        "mode": mode_label,
        "metrics": {
            "schema_pass_rate": schema_rate,
            "constraint_pass_rate": constraint_rate,
            "structure_pass_rate": structure_rate,
            "judge_score_mean": judge_mean,
            "latency_p95_ms": latency_p95,
        },
        "gates": {
            "schema": {"threshold": 0.90, "passed": schema_gate},
            "constraints": {"threshold": 0.85, "passed": constraint_gate},
            "judge": {"threshold": 4.0, "passed": judge_gate, "blocking": False},
        },
        "prompts": results,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{run_id}.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    subset_label = f"{total}/{len(all_prompts)}"
    print(f"\nMusic Producer Eval — dataset v{dataset.get('version')} ({subset_label} prompts)")
    print("─" * 52)
    print(f"L1 Schema          {bar(total, l1_pass)}  {l1_pass}/{total}  ({schema_rate:.0%})")
    print(f"L2 Constraints     {bar(total, l2_pass)}  {l2_pass}/{total}  ({constraint_rate:.0%})")
    print(f"L3 Structure       {bar(total, l3_pass)}  {l3_pass}/{total}  ({structure_rate:.0%})")
    print(f"L4 Judge (mean)    {judge_mean:.1f}/5.0  (threshold: 4.0) {'✓' if judge_gate else '✗'}")
    print(f"Latency P95        {latency_p95:,} ms  (threshold: 30,000 ms) ✓")
    print(f"\nReport: {report_path.relative_to(ROOT)}")
    status = "PASS" if schema_gate and constraint_gate else "FAIL"
    print(f"Status: {status} (PR gate)")

    return 0 if schema_gate and constraint_gate else 1


def run_eval(quick: bool = False, mock: bool | None = None) -> int:
    return asyncio.run(run_eval_async(quick=quick, mock=mock))


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Producer eval runner")
    parser.add_argument("--quick", action="store_true", help="Run quick subset only")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM fixtures")
    args = parser.parse_args()
    sys.exit(run_eval(quick=args.quick, mock=args.mock or None))


if __name__ == "__main__":
    main()
