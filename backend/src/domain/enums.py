from __future__ import annotations

from enum import Enum


class Genre(str, Enum):
    LO_FI = "lo-fi"
    POP = "pop"
    JAZZ = "jazz"
    ELECTRONIC = "electronic"
    HIP_HOP = "hip-hop"
    AMBIENT = "ambient"
    ROCK = "rock"
    CLASSICAL = "classical"
    OTHER = "other"


class Mood(str, Enum):
    HAPPY = "happy"
    MELANCHOLIC = "melancholic"
    ENERGETIC = "energetic"
    DARK = "dark"
    CALM = "calm"
    TENSE = "tense"
    ROMANTIC = "romantic"
    OTHER = "other"


VALID_KEYS = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
    "Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm",
]

TIME_SIGNATURE_BEATS = {"4/4": 4, "3/4": 3, "6/8": 6}

DRUM_MAP = {
    "kick": 36,
    "snare": 38,
    "clap": 39,
    "hihat_closed": 42,
    "tom": 45,
    "hihat_open": 46,
}

MAX_CUSTOM_TEXT_LENGTH = 50
