from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from application.generate_music import GenerateMusicUseCase, SessionService
from application.health import HealthService
from domain.models import new_session

router = APIRouter(prefix="/api/v1")


class CreateSessionRequest(BaseModel):
    client_label: str | None = None


class CreateSessionResponse(BaseModel):
    session_id: str
    created_at: str


class ControlsRequest(BaseModel):
    tempo_bpm: int = Field(default=120, ge=40, le=240)
    key: str = "C"
    genre: str = "pop"
    mood: str = "happy"
    genre_custom: str | None = None
    mood_custom: str | None = None


class GenerateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    controls: ControlsRequest


class GenerationMetadataResponse(BaseModel):
    tempo_bpm: int
    key: str
    genre: str
    mood: str
    time_signature: str
    bars: int
    model: str
    provider: str
    latency_ms: int


class GenerateResponse(BaseModel):
    generation_id: str
    session_id: str
    assistant_message: str
    metadata: GenerationMetadataResponse
    spec: dict[str, Any]
    midi_url: str
    preview_ready: bool = True


class ErrorResponse(BaseModel):
    code: str
    message: str


@dataclass
class AppState:
    health_service: HealthService
    session_service: SessionService
    generate_use_case: GenerateMusicUseCase
    repository: Any


def get_state(request: Request) -> AppState:
    return request.app.state.app_state


@router.get("/health")
async def health(state: AppState = Depends(get_state)) -> dict:
    return await state.health_service.get_health()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    body: CreateSessionRequest,
    state: AppState = Depends(get_state),
) -> CreateSessionResponse:
    session = new_session(body.client_label)
    state.repository.create(session)
    return CreateSessionResponse(
        session_id=str(session.session_id),
        created_at=session.created_at.isoformat(),
    )


@router.get("/sessions/{session_id}")
async def get_session(session_id: UUID, state: AppState = Depends(get_state)) -> dict:
    session = state.session_service.get_session(session_id)
    return {
        "session_id": str(session.session_id),
        "messages": [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
            for m in session.messages
        ],
        "generations": [str(g.generation_id) for g in session.generations],
    }


@router.post("/sessions/{session_id}/generate", response_model=GenerateResponse)
async def generate_music(
    session_id: UUID,
    body: GenerateRequest,
    state: AppState = Depends(get_state),
) -> GenerateResponse:
    generation = await state.generate_use_case.execute(
        session_id,
        body.message,
        body.controls.model_dump(exclude_none=True),
    )
    meta = generation.metadata
    return GenerateResponse(
        generation_id=str(generation.generation_id),
        session_id=str(session_id),
        assistant_message=generation.assistant_message,
        metadata=GenerationMetadataResponse(
            tempo_bpm=meta.tempo_bpm,
            key=meta.key,
            genre=meta.genre,
            mood=meta.mood,
            time_signature=meta.time_signature,
            bars=meta.bars,
            model=meta.model,
            provider=meta.provider,
            latency_ms=meta.latency_ms,
        ),
        spec=generation.spec,
        midi_url=f"/api/v1/midi/{generation.generation_id}",
    )


@router.get("/generations/{generation_id}")
async def get_generation(generation_id: UUID, state: AppState = Depends(get_state)) -> dict:
    generation = state.generate_use_case.get_generation(generation_id)
    meta = generation.metadata
    return {
        "metadata": {
            "tempo_bpm": meta.tempo_bpm,
            "key": meta.key,
            "genre": meta.genre,
            "mood": meta.mood,
            "time_signature": meta.time_signature,
            "bars": meta.bars,
            "model": meta.model,
            "provider": meta.provider,
            "latency_ms": meta.latency_ms,
        },
        "spec": generation.spec,
        "midi_url": f"/api/v1/midi/{generation_id}",
    }


@router.get("/midi/{generation_id}")
async def get_midi(generation_id: UUID, state: AppState = Depends(get_state)) -> Response:
    midi_bytes = state.generate_use_case.get_midi(generation_id)
    return Response(
        content=midi_bytes,
        media_type="audio/midi",
        headers={"Content-Disposition": f'attachment; filename="{generation_id}.mid"'},
    )
