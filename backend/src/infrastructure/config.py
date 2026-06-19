from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_version: str = "0.1.0"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3:8b"
    llm_timeout_seconds: float = 25.0
    llm_provider: str = "ollama"
    llm_temperature: float = 0.3

    use_openai: bool = False
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    max_message_length: int = 2000
    max_messages_per_session: int = 50
    max_generations_per_session: int = 20
    context_turn_limit: int = 6
    json_repair_retries: int = 2

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_llm_provider(self) -> str:
        if self.use_openai and self.openai_api_key:
            return "openai"
        return self.llm_provider

    @property
    def schema_path(self) -> Path:
        return SCHEMA_DIR / "music_spec.v1.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
