from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain.models import GenerationRecord, Session


class SessionRepositoryPort(Protocol):
    def create(self, session: Session) -> Session:
        ...

    def get(self, session_id: UUID) -> Session | None:
        ...

    def save(self, session: Session) -> Session:
        ...

    def get_generation(self, generation_id: UUID) -> GenerationRecord | None:
        ...

    def get_midi(self, generation_id: UUID) -> bytes | None:
        ...


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[UUID, Session] = {}
        self._midi_blobs: dict[UUID, bytes] = {}

    def create(self, session: Session) -> Session:
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: UUID) -> Session | None:
        return self._sessions.get(session_id)

    def save(self, session: Session) -> Session:
        self._sessions[session.session_id] = session
        return session

    def get_generation(self, generation_id: UUID) -> GenerationRecord | None:
        for session in self._sessions.values():
            for generation in session.generations:
                if generation.generation_id == generation_id:
                    return generation
        return None

    def get_midi(self, generation_id: UUID) -> bytes | None:
        return self._midi_blobs.get(generation_id)

    def store_midi(self, generation_id: UUID, midi_bytes: bytes) -> None:
        self._midi_blobs[generation_id] = midi_bytes
