from __future__ import annotations

import json
import time
from typing import Any
from uuid import UUID, uuid4

from adapters.outbound.llm.port import REPAIR_PROMPT, LlmProviderPort, summarize_spec
from adapters.outbound.midi.generator import MidiGeneratorPort
from adapters.outbound.storage.session_repository import InMemorySessionRepository
from application.controls import controls_to_dict, sanitize_message, validate_controls
from domain.errors import (
    GenerationNotFoundError,
    LlmOutputInvalidError,
    MidiGenerationFailedError,
    SessionLimitError,
    SessionNotFoundError,
)
from domain.models import ChatMessage, GenerationMetadata, GenerationRecord
from domain.validation import MusicSpecValidator
from infrastructure.config import Settings
from infrastructure.logging import get_logger

logger = get_logger(__name__)


class SessionService:
    def __init__(self, repository: InMemorySessionRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    def get_session(self, session_id: UUID):
        session = self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(str(session_id))
        return session


class GenerateMusicUseCase:
    def __init__(
        self,
        llm: LlmProviderPort,
        validator: MusicSpecValidator,
        midi_generator: MidiGeneratorPort,
        repository: InMemorySessionRepository,
        settings: Settings,
    ) -> None:
        self._llm = llm
        self._validator = validator
        self._midi_generator = midi_generator
        self._repository = repository
        self._settings = settings

    async def execute(self, session_id: UUID, message: str, controls_data: dict[str, Any]) -> GenerationRecord:
        session = self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(str(session_id))

        if len(session.messages) >= self._settings.max_messages_per_session:
            raise SessionLimitError(f"Session message limit ({self._settings.max_messages_per_session}) reached")
        if len(session.generations) >= self._settings.max_generations_per_session:
            raise SessionLimitError(
                f"Session generation limit ({self._settings.max_generations_per_session}) reached"
            )

        cleaned_message = sanitize_message(message, self._settings.max_message_length)
        controls = validate_controls(controls_data)
        controls_dict = controls_to_dict(controls)

        history = [{"role": m.role, "content": m.content} for m in session.messages]
        last_spec_summary = None
        if session.generations:
            last_spec_summary = summarize_spec(session.generations[-1].spec)

        start = time.perf_counter()
        raw_json = await self._llm.generate_spec(cleaned_message, controls_dict, history, last_spec_summary)

        spec: dict[str, Any] | None = None
        last_error = "Invalid JSON from LLM"
        for attempt in range(self._settings.json_repair_retries + 1):
            try:
                spec = json.loads(raw_json)
            except json.JSONDecodeError:
                if attempt < self._settings.json_repair_retries:
                    raw_json = await self._llm.generate_spec(
                        f"{REPAIR_PROMPT}\n\nInvalid response:\n{raw_json}\n\nOriginal request: {cleaned_message}",
                        controls_dict,
                        history,
                        last_spec_summary,
                    )
                    continue
                raise LlmOutputInvalidError(
                    "Could not parse music specification. Try a simpler prompt with fewer details."
                ) from None

            ok, errors = self._validator.validate(spec)
            if ok:
                break
            last_error = "; ".join(errors)
            if attempt < self._settings.json_repair_retries:
                raw_json = await self._llm.generate_spec(
                    f"Fix schema errors: {last_error}. Original: {cleaned_message}",
                    controls_dict,
                    history,
                    last_spec_summary,
                )
                continue
            raise LlmOutputInvalidError(
                f"Music specification failed validation. Try a simpler prompt. Details: {last_error}"
            )

        assert spec is not None

        try:
            midi_bytes = self._midi_generator.generate(spec)
        except Exception as exc:
            logger.error("midi_generation_failed", error=str(exc))
            raise MidiGenerationFailedError(str(exc)) from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        meta = spec.get("meta", {})
        assistant_message = self._build_assistant_message(cleaned_message, controls, spec, session.generations)

        metadata = GenerationMetadata(
            tempo_bpm=int(meta.get("tempo_bpm", controls.tempo_bpm)),
            key=str(meta.get("key", controls.key)),
            genre=str(meta.get("genre", controls.genre)),
            mood=str(meta.get("mood", controls.mood)),
            time_signature=str(meta.get("time_signature", "4/4")),
            bars=int(meta.get("bars", 4)),
            model=self._llm.model_name,
            provider=self._llm.provider_name,
            latency_ms=latency_ms,
        )

        generation = GenerationRecord(
            generation_id=uuid4(),
            user_message=cleaned_message,
            controls=controls,
            spec=spec,
            midi_bytes=midi_bytes,
            metadata=metadata,
            assistant_message=assistant_message,
        )

        session.messages.append(ChatMessage(role="user", content=cleaned_message))
        session.messages.append(ChatMessage(role="assistant", content=assistant_message))
        session.generations.append(generation)
        self._repository.save(session)
        self._repository.store_midi(generation.generation_id, midi_bytes)

        logger.info(
            "generation_complete",
            session_id=str(session_id),
            generation_id=str(generation.generation_id),
            provider=metadata.provider,
            model=metadata.model,
            latency_ms=latency_ms,
        )
        return generation

    def get_generation(self, generation_id: UUID) -> GenerationRecord:
        generation = self._repository.get_generation(generation_id)
        if generation is None:
            raise GenerationNotFoundError(str(generation_id))
        return generation

    def get_midi(self, generation_id: UUID) -> bytes:
        midi = self._repository.get_midi(generation_id)
        if midi is None:
            raise GenerationNotFoundError(str(generation_id))
        return midi

    @staticmethod
    def _build_assistant_message(
        message: str,
        controls,
        spec: dict[str, Any],
        prior_generations: list[GenerationRecord],
    ) -> str:
        meta = spec.get("meta", {})
        base = (
            f"Created a {meta.get('mood', controls.mood)} {meta.get('genre', controls.genre)} "
            f"progression in {meta.get('key', controls.key)} at {meta.get('tempo_bpm', controls.tempo_bpm)} BPM "
            f"({meta.get('bars', 4)} bars)."
        )
        if prior_generations:
            prev = prior_generations[-1]
            prev_meta = prev.spec.get("meta", {})
            changes = []
            if prev_meta.get("tempo_bpm") != meta.get("tempo_bpm"):
                changes.append(f"tempo {prev_meta.get('tempo_bpm')}→{meta.get('tempo_bpm')} BPM")
            if prev_meta.get("key") != meta.get("key"):
                changes.append(f"key {prev_meta.get('key')}→{meta.get('key')}")
            if prev_meta.get("mood") != meta.get("mood"):
                changes.append(f"mood {prev_meta.get('mood')}→{meta.get('mood')}")
            if len(spec.get("drums", [])) > len(prev.spec.get("drums", [])):
                changes.append("added drum hits")
            if len(spec.get("melody", [])) > len(prev.spec.get("melody", [])):
                changes.append("expanded melody")
            if changes:
                return f"{base} Changes from previous: {', '.join(changes)}."
        return base
