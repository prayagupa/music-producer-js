from __future__ import annotations

import json
from typing import Any

import httpx

from adapters.outbound.llm.port import (
    JUDGE_PROMPT,
    SYSTEM_PROMPT,
    build_user_message,
)
from domain.errors import GenerationTimeoutError, OpenAiUnavailableError
from infrastructure.config import Settings


class OpenAiLlmProvider:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(timeout=settings.llm_timeout_seconds)
        self._owns_client = client is None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._settings.openai_model

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _chat(self, user_content: str, temperature: float) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self._settings.openai_api_key}"}
        payload = {
            "model": self._settings.openai_model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        }
        try:
            response = await self._client.post(
                url, headers=headers, json=payload, timeout=self._settings.llm_timeout_seconds
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError("LLM request exceeded timeout") from exc
        except httpx.HTTPError as exc:
            raise OpenAiUnavailableError(f"OpenAI request failed: {exc}") from exc

        data = response.json()
        return str(data["choices"][0]["message"]["content"]).strip()

    async def generate_spec(
        self,
        prompt: str,
        controls: dict[str, Any],
        history: list[dict[str, str]],
        last_spec_summary: str | None = None,
    ) -> str:
        user_content = build_user_message(prompt, controls, history, last_spec_summary)
        return await self._chat(user_content, self._settings.llm_temperature)

    async def judge(self, prompt: str, spec_summary: str) -> float:
        user_content = f"{JUDGE_PROMPT}\nPrompt: {prompt}\nSpec: {spec_summary}"
        raw = await self._chat(user_content, 0.0)
        try:
            data = json.loads(raw)
            return float(data.get("score", 3.0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return 3.0
