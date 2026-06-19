# Backend

FastAPI application with hexagonal architecture.

- `src/domain/` — MusicSpec, validation, chord mapping
- `src/application/` — Use cases and session service
- `src/adapters/` — HTTP routes, LLM, MIDI, storage
- `src/infrastructure/` — Config, logging, middleware
- `tests/` — pytest unit and integration tests
- `schemas/` — Canonical JSON schemas
