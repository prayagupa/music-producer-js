import io
import json
import time
from pathlib import Path

import pretty_midi
import pytest

from adapters.outbound.midi.generator import PrettyMidiGenerator

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def generator():
    return PrettyMidiGenerator()


@pytest.fixture
def valid_spec():
    with (FIXTURES / "valid_spec.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def test_should_generate_midi_bytes_when_spec_valid(generator, valid_spec):
    midi_bytes = generator.generate(valid_spec)
    assert len(midi_bytes) > 0
    parsed = pretty_midi.PrettyMIDI(io.BytesIO(midi_bytes))
    assert len(parsed.instruments) == 3


def test_should_complete_within_two_seconds_when_golden_fixture(generator, valid_spec):
    start = time.perf_counter()
    generator.generate(valid_spec)
    elapsed = time.perf_counter() - start
    assert elapsed <= 2.0
