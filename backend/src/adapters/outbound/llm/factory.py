from __future__ import annotations

from adapters.outbound.llm.mock import MockLlmProvider
from adapters.outbound.llm.ollama import OllamaLlmProvider
from adapters.outbound.llm.openai import OpenAiLlmProvider
from adapters.outbound.llm.port import LlmProviderPort
from infrastructure.config import Settings


def create_llm_provider(settings: Settings) -> LlmProviderPort:
    if settings.effective_llm_provider == "openai":
        return OpenAiLlmProvider(settings)
    if settings.effective_llm_provider == "mock":
        return MockLlmProvider(settings)
    return OllamaLlmProvider(settings)
