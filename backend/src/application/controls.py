from __future__ import annotations

import re
from typing import Any

from domain.enums import Genre, Mood, VALID_KEYS
from domain.errors import InvalidControlsError
from domain.models import Controls

CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_message(message: str, max_length: int) -> str:
    cleaned = CONTROL_CHAR_PATTERN.sub("", message.strip())
    if not cleaned:
        raise InvalidControlsError("Message cannot be empty")
    if len(cleaned) > max_length:
        raise InvalidControlsError(f"Message exceeds {max_length} characters")
    return cleaned


def validate_controls(data: dict[str, Any]) -> Controls:
    tempo = data.get("tempo_bpm", 120)
    if not isinstance(tempo, int) or tempo < 40 or tempo > 240:
        raise InvalidControlsError("tempo_bpm must be an integer between 40 and 240")

    key = data.get("key", "C")
    if key not in VALID_KEYS:
        raise InvalidControlsError(f"key must be one of {len(VALID_KEYS)} valid keys")

    genre = data.get("genre", "pop")
    try:
        genre_enum = Genre(genre)
    except ValueError as exc:
        raise InvalidControlsError(f"Invalid genre: {genre}") from exc

    mood = data.get("mood", "happy")
    try:
        mood_enum = Mood(mood)
    except ValueError as exc:
        raise InvalidControlsError(f"Invalid mood: {mood}") from exc

    genre_custom = data.get("genre_custom")
    mood_custom = data.get("mood_custom")

    if genre_enum == Genre.OTHER:
        if not genre_custom or len(str(genre_custom).strip()) == 0:
            raise InvalidControlsError("genre_custom required when genre is 'other'")
        if len(str(genre_custom)) > 50:
            raise InvalidControlsError("genre_custom max 50 characters")
    else:
        genre_custom = None

    if mood_enum == Mood.OTHER:
        if not mood_custom or len(str(mood_custom).strip()) == 0:
            raise InvalidControlsError("mood_custom required when mood is 'other'")
        if len(str(mood_custom)) > 50:
            raise InvalidControlsError("mood_custom max 50 characters")
    else:
        mood_custom = None

    return Controls(
        tempo_bpm=tempo,
        key=key,
        genre=genre_enum.value,
        mood=mood_enum.value,
        genre_custom=genre_custom,
        mood_custom=mood_custom,
    )


def controls_to_dict(controls: Controls) -> dict[str, Any]:
    result: dict[str, Any] = {
        "tempo_bpm": controls.tempo_bpm,
        "key": controls.key,
        "genre": controls.genre,
        "mood": controls.mood,
    }
    if controls.genre_custom:
        result["genre_custom"] = controls.genre_custom
    if controls.mood_custom:
        result["mood_custom"] = controls.mood_custom
    return result
