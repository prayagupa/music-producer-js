from __future__ import annotations

import json
from typing import Any, Protocol


class LlmProviderPort(Protocol):
    async def generate_spec(
        self,
        prompt: str,
        controls: dict[str, Any],
        history: list[dict[str, str]],
        last_spec_summary: str | None = None,
    ) -> str:
        ...

    async def judge(self, prompt: str, spec_summary: str) -> float:
        ...

    @property
    def provider_name(self) -> str:
        ...

    @property
    def model_name(self) -> str:
        ...


SYSTEM_PROMPT = """You are a music composition assistant. Return ONLY valid JSON matching music_spec version 1.0.

Schema summary:
- version: "1.0"
- meta: tempo_bpm (40-240), key (e.g. Am, C), genre, mood, time_signature (4/4|3/4|6/8), bars (1-8)
- chords: array of {symbol (Roman numeral e.g. i, IV, V7), start_bar, duration_beats}
- drums: array of {instrument (kick|snare|hihat_closed|hihat_open|clap|tom), start_beat, velocity}
- melody: array of at least 4 notes {pitch (0-127), start_beat, duration_beats, velocity}

Example:
{"version":"1.0","meta":{"tempo_bpm":80,"key":"Am","genre":"lo-fi","mood":"melancholic","time_signature":"4/4","bars":4},"chords":[{"symbol":"i","start_bar":1,"duration_beats":4}],"drums":[{"instrument":"kick","start_beat":0,"velocity":90}],"melody":[{"pitch":69,"start_beat":0,"duration_beats":1,"velocity":80},{"pitch":67,"start_beat":1,"duration_beats":1,"velocity":75},{"pitch":65,"start_beat":2,"duration_beats":1,"velocity":70},{"pitch":64,"start_beat":3,"duration_beats":1,"velocity":72}]}

Respect user controls for tempo, key, genre, and mood. Keep events within bar boundaries."""

REPAIR_PROMPT = "Your previous response was invalid JSON. Return ONLY valid JSON matching schema version 1.0."

JUDGE_PROMPT = """Rate how well this music specification matches the user prompt on a scale of 1-5.
Return JSON: {"score": <number 1-5>, "reason": "<brief>"}"""


def build_user_message(
    prompt: str,
    controls: dict[str, Any],
    history: list[dict[str, str]],
    last_spec_summary: str | None,
) -> str:
    parts = [f"User request: {prompt}", f"Controls: {json.dumps(controls)}"]
    if last_spec_summary:
        parts.append(f"Previous spec summary: {last_spec_summary}")
    if history:
        parts.append("Recent conversation:")
        for turn in history[-6:]:
            parts.append(f"{turn['role']}: {turn['content']}")
    return "\n".join(parts)


def summarize_spec(spec: dict[str, Any]) -> str:
    meta = spec.get("meta", {})
    return (
        f"BPM={meta.get('tempo_bpm')}, key={meta.get('key')}, "
        f"bars={meta.get('bars')}, chords={len(spec.get('chords', []))}, "
        f"drums={len(spec.get('drums', []))}, melody_notes={len(spec.get('melody', []))}"
    )
