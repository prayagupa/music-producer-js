import json
from pathlib import Path

import pytest

from domain.validation import MusicSpecValidator

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "music_spec.v1.json"
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def validator():
    return MusicSpecValidator(SCHEMA_PATH)


def _load(name: str) -> dict:
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.parametrize(
    "fixture_name",
    ["valid_spec.json"],
)
def test_should_pass_valid_spec_when_constraints_met(validator, fixture_name):
    spec = _load(fixture_name)
    ok, errors = validator.validate(spec)
    assert ok, errors


@pytest.mark.parametrize(
    "fixture_name,expected_fragment",
    [
        ("invalid_bpm.json", "tempo_bpm"),
        ("invalid_key.json", "key"),
        ("invalid_melody_pitch.json", "pitch"),
        ("invalid_drum_beat.json", "start_beat"),
        ("invalid_chord_bar.json", "start_bar"),
        ("missing_version.json", "version"),
        ("too_few_melody.json", "melody"),
        ("invalid_time_sig.json", "time_signature"),
        ("chord_beyond_bars.json", "extends beyond"),
        ("melody_beyond_bars.json", "start_beat"),
    ],
)
def test_should_fail_invalid_spec_when_constraint_violated(validator, fixture_name, expected_fragment):
    spec = _load(fixture_name)
    ok, errors = validator.validate(spec)
    assert not ok
    assert any(expected_fragment in err for err in errors)


def test_should_validate_l3_structure_when_min_requirements_met(validator):
    spec = _load("valid_spec.json")
    ok, errors = validator.validate_l3_structure(spec)
    assert ok, errors
