from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.config import Settings

FIXTURES_DIR = Path(__file__).resolve().parents[4] / "tests" / "fixtures"


class MockLlmProvider:
    """Deterministic LLM for local dev and manual testing without Ollama."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._spec_json = (FIXTURES_DIR / "valid_spec.json").read_text(encoding="utf-8")

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-model"

    async def generate_spec(
        self,
        prompt: str,
        controls: dict[str, Any],
        history: list[dict[str, str]],
        last_spec_summary: str | None = None,
    ) -> str:
        spec = json.loads(self._spec_json)
        meta = spec.setdefault("meta", {})
        meta["tempo_bpm"] = controls.get("tempo_bpm", meta.get("tempo_bpm", 120))
        meta["key"] = controls.get("key", meta.get("key", "C"))
        meta["genre"] = controls.get("genre", meta.get("genre", "pop"))
        meta["mood"] = controls.get("mood", meta.get("mood", "happy"))
        return json.dumps(spec)

    async def judge(self, prompt: str, spec_summary: str) -> float:
        return 4.5
