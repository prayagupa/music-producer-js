import pytest

from application.controls import validate_controls
from domain.errors import InvalidControlsError


def test_should_accept_valid_controls_when_enums_match():
    controls = validate_controls(
        {"tempo_bpm": 120, "key": "Am", "genre": "lo-fi", "mood": "melancholic"}
    )
    assert controls.key == "Am"


def test_should_reject_invalid_bpm_when_out_of_range():
    with pytest.raises(InvalidControlsError):
        validate_controls({"tempo_bpm": 300, "key": "C", "genre": "pop", "mood": "happy"})


def test_should_require_custom_genre_when_other_selected():
    with pytest.raises(InvalidControlsError):
        validate_controls({"tempo_bpm": 120, "key": "C", "genre": "other", "mood": "happy"})
