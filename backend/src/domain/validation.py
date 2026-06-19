from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema

from domain.enums import TIME_SIGNATURE_BEATS, VALID_KEYS

KEY_PATTERN = re.compile(r"^(A|A#|B|C|C#|D|D#|E|F|F#|G|G#)(m)?$")


class MusicSpecValidator:
    def __init__(self, schema_path: Path) -> None:
        with schema_path.open(encoding="utf-8") as handle:
            self._schema = json.load(handle)

    def validate_l1(self, spec: dict[str, Any]) -> list[str]:
        validator = jsonschema.Draft202012Validator(self._schema)
        return [f"{'.'.join(str(p) for p in err.path)}: {err.message}" for err in validator.iter_errors(spec)]

    def validate_l2(self, spec: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        meta = spec.get("meta", {})
        key = meta.get("key", "")
        if key not in VALID_KEYS and not KEY_PATTERN.match(str(key)):
            errors.append(f"meta.key: invalid key '{key}'")

        time_sig = meta.get("time_signature", "4/4")
        beats_per_bar = TIME_SIGNATURE_BEATS.get(time_sig, 4)
        bars = meta.get("bars", 1)
        max_beats = bars * beats_per_bar

        for idx, chord in enumerate(spec.get("chords", [])):
            start_bar = chord.get("start_bar", 0)
            duration = chord.get("duration_beats", 0)
            end_beat = (start_bar - 1) * beats_per_bar + duration
            if start_bar < 1 or start_bar > bars:
                errors.append(f"chords[{idx}].start_bar: out of range 1-{bars}")
            if end_beat > max_beats:
                errors.append(f"chords[{idx}]: extends beyond {bars} bars")

        for idx, drum in enumerate(spec.get("drums", [])):
            start_beat = drum.get("start_beat", -1)
            if start_beat < 0 or start_beat >= max_beats:
                errors.append(f"drums[{idx}].start_beat: must be within 0-{max_beats - 1}")

        for idx, note in enumerate(spec.get("melody", [])):
            pitch = note.get("pitch", -1)
            if pitch < 0 or pitch > 127:
                errors.append(f"melody[{idx}].pitch: must be 0-127")
            start_beat = note.get("start_beat", -1)
            if start_beat < 0 or start_beat >= max_beats:
                errors.append(f"melody[{idx}].start_beat: must be within 0-{max_beats - 1}")

        return errors

    def validate(self, spec: dict[str, Any]) -> tuple[bool, list[str]]:
        errors = self.validate_l1(spec) + self.validate_l2(spec)
        return len(errors) == 0, errors

    @staticmethod
    def validate_l3_structure(spec: dict[str, Any]) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not spec.get("chords"):
            errors.append("chords: must be non-empty")
        if not any(d.get("velocity", 0) > 0 for d in spec.get("drums", [])):
            errors.append("drums: at least one hit required")
        if len(spec.get("melody", [])) < 4:
            errors.append("melody: at least 4 notes required")
        return len(errors) == 0, errors

    @property
    def schema_json(self) -> dict[str, Any]:
        return self._schema
