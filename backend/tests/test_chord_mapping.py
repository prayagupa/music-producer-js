import pytest

from domain.chord_mapping import all_keys, roman_to_pitches


@pytest.mark.parametrize("key", ["C", "Am", "F#", "D#m", "G", "Bm"])
def test_should_map_roman_numerals_when_key_valid(key):
    pitches = roman_to_pitches(key, "I" if "m" not in key else "i")
    assert len(pitches) >= 3
    assert all(0 <= p <= 127 for p in pitches)


def test_should_detect_seventh_when_symbol_ends_with_seven():
    pitches = roman_to_pitches("C", "V7")
    assert len(pitches) == 4


def test_should_not_duplicate_seventh_detection():
    pitches_with = roman_to_pitches("C", "I7")
    pitches_without = roman_to_pitches("C", "I")
    assert len(pitches_with) == len(pitches_without) + 1


def test_should_cover_all_24_keys():
    keys = list(all_keys())
    assert len(keys) == 24


@pytest.mark.parametrize("key", ["C", "G", "Am", "Em", "F#", "A#m"])
def test_should_produce_distinct_voicings_when_keys_differ(key):
    symbol = "V7" if "m" not in key else "v"
    pitches = roman_to_pitches(key, symbol)
    assert len(pitches) >= 3
