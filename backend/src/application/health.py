from __future__ import annotations

import httpx

from infrastructure.config import Settings


class HealthService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(timeout=2.0)
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def check_ollama(self) -> tuple[str, str | None]:
        url = f"{self._settings.ollama_base_url.rstrip('/')}/api/tags"
        try:
            response = await self._client.get(url, timeout=2.0)
            if response.status_code == 200:
                return "up", None
            return "down", f"Ollama returned status {response.status_code}"
        except httpx.HTTPError:
            return "down", f"Ollama sidecar unreachable at {self._settings.ollama_base_url}"

    async def get_health(self) -> dict:
        ollama_status, message = await self.check_ollama()
        if self._settings.effective_llm_provider in ("openai", "mock"):
            ollama_status = "skipped"
            message = None

        status = "ok"
        if ollama_status == "down":
            status = "degraded"

        result = {
            "status": status,
            "version": self._settings.app_version,
            "checks": {"api": "up", "ollama": ollama_status},
        }
        if message:
            result["message"] = message
        return result
