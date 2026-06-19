from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidControlsError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_CONTROLS", message, 400)


class LlmOutputInvalidError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("LLM_OUTPUT_INVALID", message, 422)


class OllamaUnavailableError(AppError):
    def __init__(self, message: str = "Ollama sidecar is unavailable") -> None:
        super().__init__("OLLAMA_UNAVAILABLE", message, 503)


class OpenAiUnavailableError(AppError):
    def __init__(self, message: str = "OpenAI API is unavailable") -> None:
        super().__init__("OPENAI_UNAVAILABLE", message, 503)


class GenerationTimeoutError(AppError):
    def __init__(self, message: str = "Generation exceeded timeout") -> None:
        super().__init__("GENERATION_TIMEOUT", message, 504)


class MidiGenerationFailedError(AppError):
    def __init__(self, message: str = "MIDI generation failed") -> None:
        super().__init__("MIDI_GENERATION_FAILED", message, 500)


class SessionNotFoundError(AppError):
    def __init__(self, session_id: str) -> None:
        super().__init__("SESSION_NOT_FOUND", f"Session {session_id} not found", 404)


class GenerationNotFoundError(AppError):
    def __init__(self, generation_id: str) -> None:
        super().__init__("GENERATION_NOT_FOUND", f"Generation {generation_id} not found", 404)


class SessionLimitError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("SESSION_LIMIT", message, 400)
