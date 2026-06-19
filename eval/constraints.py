from __future__ import annotations

from typing import Any


def validate_expected_constraints(spec: dict[str, Any], constraints: dict[str, Any]) -> list[str]:
    """Validate generated spec against golden-prompt expected_constraints."""
    if not constraints:
        return []

    errors: list[str] = []
    meta = spec.get("meta", {})

    if "tempo_range" in constraints:
        tempo = meta.get("tempo_bpm")
        lo, hi = constraints["tempo_range"]
        if tempo is None or not (lo <= int(tempo) <= hi):
            errors.append(f"tempo_bpm {tempo!r} not in range [{lo}, {hi}]")

    if "key" in constraints:
        actual_key = meta.get("key")
        if actual_key != constraints["key"]:
            errors.append(f"key {actual_key!r} != expected {constraints['key']!r}")

    min_melody = constraints.get("min_melody_notes")
    if min_melody is not None and len(spec.get("melody", [])) < min_melody:
        errors.append(f"melody has {len(spec.get('melody', []))} notes, need >= {min_melody}")

    min_drums = constraints.get("min_drum_hits")
    if min_drums is not None:
        active_drums = sum(1 for d in spec.get("drums", []) if d.get("velocity", 0) > 0)
        if active_drums < min_drums:
            errors.append(f"drums has {active_drums} hits, need >= {min_drums}")

    if "bars" in constraints:
        actual_bars = meta.get("bars")
        if actual_bars != constraints["bars"]:
            errors.append(f"bars {actual_bars!r} != expected {constraints['bars']!r}")

    return errors
