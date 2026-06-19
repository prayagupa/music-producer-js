import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from adapters.outbound.llm.ollama import OllamaLlmProvider
from adapters.outbound.llm.openai import OpenAiLlmProvider
from domain.errors import GenerationTimeoutError, OllamaUnavailableError, OpenAiUnavailableError
from infrastructure.config import Settings


@pytest.fixture
def settings():
    return Settings(ollama_base_url="http://localhost:11434", llm_model="llama3:8b", llm_timeout_seconds=25)


@pytest.mark.asyncio
async def test_should_return_valid_json_when_ollama_responds(settings):
    valid = json.dumps({"version": "1.0", "meta": {}, "chords": [], "drums": [], "melody": []})
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": valid}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)

    provider = OllamaLlmProvider(settings, client=mock_client)
    result = await provider.generate_spec("test", {"tempo_bpm": 120}, [])
    assert json.loads(result)


@pytest.mark.asyncio
async def test_should_raise_unavailable_when_connection_fails(settings):
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    provider = OllamaLlmProvider(settings, client=mock_client)
    with pytest.raises(OllamaUnavailableError):
        await provider.generate_spec("test", {"tempo_bpm": 120}, [])


@pytest.mark.asyncio
async def test_should_raise_timeout_when_ollama_slow(settings):
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    provider = OllamaLlmProvider(settings, client=mock_client)
    with pytest.raises(GenerationTimeoutError):
        await provider.generate_spec("test", {"tempo_bpm": 120}, [])


@pytest.fixture
def openai_settings():
    return Settings(
        use_openai=True,
        openai_api_key="test-key",
        openai_model="gpt-4o-mini",
        llm_timeout_seconds=25,
    )


@pytest.mark.asyncio
async def test_should_raise_unavailable_when_openai_http_error(openai_settings):
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
        "server error", request=MagicMock(), response=MagicMock(status_code=500)
    ))

    provider = OpenAiLlmProvider(openai_settings, client=mock_client)
    with pytest.raises(OpenAiUnavailableError):
        await provider.generate_spec("test", {"tempo_bpm": 120}, [])


@pytest.mark.asyncio
async def test_should_raise_timeout_when_openai_slow(openai_settings):
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    provider = OpenAiLlmProvider(openai_settings, client=mock_client)
    with pytest.raises(GenerationTimeoutError):
        await provider.generate_spec("test", {"tempo_bpm": 120}, [])
