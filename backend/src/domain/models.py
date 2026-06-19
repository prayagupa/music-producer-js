from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=utc_now)


@dataclass
class Controls:
    tempo_bpm: int = 120
    key: str = "C"
    genre: str = "pop"
    mood: str = "happy"
    genre_custom: str | None = None
    mood_custom: str | None = None


@dataclass
class GenerationMetadata:
    tempo_bpm: int
    key: str
    genre: str
    mood: str
    time_signature: str
    bars: int
    model: str
    provider: str
    latency_ms: int


@dataclass
class GenerationRecord:
    generation_id: UUID
    user_message: str
    controls: Controls
    spec: dict[str, Any]
    midi_bytes: bytes
    metadata: GenerationMetadata
    assistant_message: str
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class Session:
    session_id: UUID
    created_at: datetime = field(default_factory=utc_now)
    messages: list[ChatMessage] = field(default_factory=list)
    generations: list[GenerationRecord] = field(default_factory=list)
    client_label: str | None = None


def new_session(client_label: str | None = None) -> Session:
    return Session(session_id=uuid4(), client_label=client_label)
