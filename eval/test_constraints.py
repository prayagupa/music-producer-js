from __future__ import annotations

import pytest

from eval.constraints import validate_expected_constraints


def test_should_pass_when_spec_meets_expected_constraints():
    spec = {
        "meta": {"tempo_bpm": 80, "key": "Am", "bars": 4},
        "melody": [{"pitch": 60}] * 4,
        "drums": [{"instrument": "kick", "start_beat": 0, "velocity": 90}],
    }
    constraints = {
        "tempo_range": [70, 90],
        "key": "Am",
        "min_melody_notes": 4,
        "min_drum_hits": 1,
        "bars": 4,
    }
    assert validate_expected_constraints(spec, constraints) == []


def test_should_fail_when_tempo_outside_expected_range():
    spec = {
        "meta": {"tempo_bpm": 120, "key": "C", "bars": 4},
        "melody": [{"pitch": 60}] * 4,
        "drums": [{"instrument": "kick", "start_beat": 0, "velocity": 90}],
    }
    errors = validate_expected_constraints(spec, {"tempo_range": [70, 90]})
    assert any("tempo_bpm" in e for e in errors)


def test_should_fail_when_drum_hits_below_minimum():
    spec = {
        "meta": {"tempo_bpm": 80, "key": "Am", "bars": 4},
        "melody": [{"pitch": 60}] * 4,
        "drums": [{"instrument": "kick", "start_beat": 0, "velocity": 0}],
    }
    errors = validate_expected_constraints(spec, {"min_drum_hits": 2})
    assert any("drums" in e for e in errors)
