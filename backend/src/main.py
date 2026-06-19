from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from adapters.inbound.routes import AppState, router
from adapters.outbound.llm.factory import create_llm_provider
from adapters.outbound.midi.generator import PrettyMidiGenerator
from adapters.outbound.storage.session_repository import InMemorySessionRepository
from application.generate_music import GenerateMusicUseCase, SessionService
from application.health import HealthService
from domain.errors import AppError
from domain.validation import MusicSpecValidator
from infrastructure.config import get_settings
from infrastructure.logging import configure_logging, get_logger
from infrastructure.middleware import RequestIdMiddleware

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Music Producer API", version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    repository = InMemorySessionRepository()
    llm = create_llm_provider(settings)
    validator = MusicSpecValidator(settings.schema_path)
    midi_generator = PrettyMidiGenerator()

    app.state.app_state = AppState(
        health_service=HealthService(settings),
        session_service=SessionService(repository, settings),
        generate_use_case=GenerateMusicUseCase(llm, validator, midi_generator, repository, settings),
        repository=repository,
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        logger.error("app_error", code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )

    app.include_router(router)
    return app


app = create_app()
