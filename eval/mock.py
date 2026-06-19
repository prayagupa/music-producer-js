from __future__ import annotations

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "mock"


def load_mock_spec(prompt_id: str) -> dict:
    fixture_path = FIXTURES_DIR / f"{prompt_id}.json"
    if fixture_path.exists():
        with fixture_path.open(encoding="utf-8") as handle:
            return json.load(handle)
    return _default_spec()


def _default_spec() -> dict:
    return {
        "version": "1.0",
        "meta": {
            "tempo_bpm": 80,
            "key": "Am",
            "genre": "lo-fi",
            "mood": "melancholic",
            "time_signature": "4/4",
            "bars": 4,
        },
        "chords": [
            {"symbol": "i", "start_bar": 1, "duration_beats": 4},
            {"symbol": "iv", "start_bar": 2, "duration_beats": 4},
            {"symbol": "v", "start_bar": 3, "duration_beats": 4},
            {"symbol": "i", "start_bar": 4, "duration_beats": 4},
        ],
        "drums": [
            {"instrument": "kick", "start_beat": 0, "velocity": 90},
            {"instrument": "snare", "start_beat": 2, "velocity": 80},
            {"instrument": "hihat_closed", "start_beat": 1, "velocity": 60},
            {"instrument": "hihat_closed", "start_beat": 3, "velocity": 60},
        ],
        "melody": [
            {"pitch": 69, "start_beat": 0, "duration_beats": 1, "velocity": 80},
            {"pitch": 67, "start_beat": 1, "duration_beats": 1, "velocity": 75},
            {"pitch": 65, "start_beat": 2, "duration_beats": 1, "velocity": 70},
            {"pitch": 64, "start_beat": 3, "duration_beats": 1, "velocity": 72},
        ],
    }
