import json
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from adapters.outbound.midi.generator import PrettyMidiGenerator
from adapters.outbound.storage.session_repository import InMemorySessionRepository
from application.generate_music import GenerateMusicUseCase
from domain.errors import LlmOutputInvalidError
from domain.models import new_session
from domain.validation import MusicSpecValidator
from infrastructure.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "music_spec.v1.json"


class MockLlm:
    provider_name = "mock"
    model_name = "mock-model"

    def __init__(self, response: str) -> None:
        self._response = response

    async def generate_spec(self, prompt, controls, history, last_spec_summary=None):
        return self._response

    async def judge(self, prompt, spec_summary):
        return 4.5


@pytest.mark.asyncio
async def test_should_run_full_pipeline_when_mock_llm_returns_valid_spec():
    with (FIXTURES / "valid_spec.json").open(encoding="utf-8") as handle:
        spec_json = handle.read()

    repository = InMemorySessionRepository()
    session = new_session()
    repository.create(session)

    use_case = GenerateMusicUseCase(
        llm=MockLlm(spec_json),
        validator=MusicSpecValidator(SCHEMA_PATH),
        midi_generator=PrettyMidiGenerator(),
        repository=repository,
        settings=Settings(),
    )

    generation = await use_case.execute(
        session.session_id,
        "sad lo-fi beat",
        {"tempo_bpm": 80, "key": "Am", "genre": "lo-fi", "mood": "melancholic"},
    )

    assert generation.generation_id is not None
    assert len(generation.midi_bytes) > 0
    assert generation.metadata.provider == "mock"
    midi = repository.get_midi(generation.generation_id)
    assert midi is not None


@pytest.mark.asyncio
async def test_should_create_session_and_generate_via_api(app, client):
    with (FIXTURES / "valid_spec.json").open(encoding="utf-8") as handle:
        spec_json = handle.read()

    mock_llm = MockLlm(spec_json)
    app.state.app_state.generate_use_case._llm = mock_llm

    session_resp = await client.post("/api/v1/sessions", json={})
    assert session_resp.status_code == 200
    session_id = session_resp.json()["session_id"]

    gen_resp = await client.post(
        f"/api/v1/sessions/{session_id}/generate",
        json={
            "message": "sad lo-fi beat",
            "controls": {"tempo_bpm": 80, "key": "Am", "genre": "lo-fi", "mood": "melancholic"},
        },
    )
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert "generation_id" in data
    assert data["preview_ready"] is True

    midi_resp = await client.get(f"/api/v1/midi/{data['generation_id']}")
    assert midi_resp.status_code == 200
    assert midi_resp.headers["content-type"] == "audio/midi"


@pytest.mark.asyncio
async def test_should_limit_json_repair_retries_to_two():
    call_count = 0

    class InvalidJsonLlm:
        provider_name = "mock"
        model_name = "mock-model"

        async def generate_spec(self, prompt, controls, history, last_spec_summary=None):
            nonlocal call_count
            call_count += 1
            return "not valid json"

        async def judge(self, prompt, spec_summary):
            return 4.5

    repository = InMemorySessionRepository()
    session = new_session()
    repository.create(session)

    use_case = GenerateMusicUseCase(
        llm=InvalidJsonLlm(),
        validator=MusicSpecValidator(SCHEMA_PATH),
        midi_generator=PrettyMidiGenerator(),
        repository=repository,
        settings=Settings(json_repair_retries=2),
    )

    with pytest.raises(LlmOutputInvalidError):
        await use_case.execute(
            session.session_id,
            "test prompt",
            {"tempo_bpm": 80, "key": "Am", "genre": "lo-fi", "mood": "melancholic"},
        )

    assert call_count == 3
