from __future__ import annotations

import re
from typing import Sequence

NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
    "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11,
}

MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]

ROMAN_DEGREES = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7,
}


def parse_key(key: str) -> tuple[int, bool]:
    match = re.match(r"^(A|A#|B|C|C#|D|D#|E|F|F#|G|G#)(m)?$", key)
    if not match:
        raise ValueError(f"Invalid key: {key}")
    root = NOTE_TO_SEMITONE[match.group(1)]
    is_minor = match.group(2) == "m"
    return root, is_minor


def _scale_for_key(root: int, is_minor: bool) -> list[int]:
    intervals = MINOR_SCALE if is_minor else MAJOR_SCALE
    return [(root + interval) % 12 for interval in intervals]


def _normalize_symbol(symbol: str) -> tuple[int, bool, bool]:
    cleaned = symbol.strip()
    has_seventh = cleaned.endswith("7")
    base = cleaned.rstrip("7").rstrip("°").rstrip("dim")
    is_dim = "dim" in cleaned.lower() or "°" in cleaned
    degree = ROMAN_DEGREES.get(base)
    if degree is None:
        degree = ROMAN_DEGREES.get(base.upper(), 1)
    return degree, has_seventh, is_dim


def roman_to_pitches(key: str, symbol: str, octave: int = 4) -> list[int]:
    root, is_minor = parse_key(key)
    scale = _scale_for_key(root, is_minor)
    degree, has_seventh, is_dim = _normalize_symbol(symbol)
    idx = max(0, min(6, degree - 1))
    base_note = scale[idx]
    base_midi = 12 * (octave + 1) + base_note

    if is_minor:
        third = scale[(idx + 2) % 7]
        fifth = scale[(idx + 4) % 7]
        pitches = [base_midi, 12 * (octave + 1) + third, 12 * (octave + 1) + fifth]
        if has_seventh:
            seventh = scale[(idx + 6) % 7]
            pitches.append(12 * (octave + 1) + seventh)
    else:
        third = scale[(idx + 2) % 7]
        fifth = scale[(idx + 4) % 7]
        pitches = [base_midi, 12 * (octave + 1) + third, 12 * (octave + 1) + fifth]
        if has_seventh:
            seventh = scale[(idx + 6) % 7]
            pitches.append(12 * (octave + 1) + seventh)

    if is_dim:
        pitches[1] = pitches[0] + 3
        pitches[2] = pitches[0] + 6

    return sorted(set(pitches))


def all_keys() -> Sequence[str]:
    majors = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    minors = [f"{k}m" for k in majors]
    return majors + minors
