from __future__ import annotations

import io
from typing import Any, Protocol

import pretty_midi

from domain.chord_mapping import roman_to_pitches
from domain.enums import DRUM_MAP, TIME_SIGNATURE_BEATS


class MidiGeneratorPort(Protocol):
    def generate(self, spec: dict[str, Any]) -> bytes:
        ...


class PrettyMidiGenerator:
    def generate(self, spec: dict[str, Any]) -> bytes:
        meta = spec["meta"]
        tempo = float(meta["tempo_bpm"])
        key = meta["key"]
        bars = int(meta["bars"])
        time_sig = meta.get("time_signature", "4/4")
        beats_per_bar = TIME_SIGNATURE_BEATS.get(time_sig, 4)
        seconds_per_beat = 60.0 / tempo

        midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)

        chord_track = pretty_midi.Instrument(program=0, name="Chords")
        for chord in spec.get("chords", []):
            start_bar = int(chord["start_bar"])
            duration_beats = float(chord["duration_beats"])
            start_time = (start_bar - 1) * beats_per_bar * seconds_per_beat
            end_time = start_time + duration_beats * seconds_per_beat
            pitches = roman_to_pitches(key, chord["symbol"])
            for pitch in pitches:
                note = pretty_midi.Note(velocity=80, pitch=pitch, start=start_time, end=end_time)
                chord_track.notes.append(note)
        midi.instruments.append(chord_track)

        drum_track = pretty_midi.Instrument(program=0, is_drum=True, name="Drums")
        for hit in spec.get("drums", []):
            instrument = hit["instrument"]
            pitch = DRUM_MAP.get(instrument, 36)
            start_time = float(hit["start_beat"]) * seconds_per_beat
            velocity = int(hit["velocity"])
            note = pretty_midi.Note(
                velocity=velocity,
                pitch=pitch,
                start=start_time,
                end=start_time + 0.1,
            )
            drum_track.notes.append(note)
        midi.instruments.append(drum_track)

        melody_track = pretty_midi.Instrument(program=0, name="Melody")
        for note_data in spec.get("melody", []):
            start_time = float(note_data["start_beat"]) * seconds_per_beat
            duration = float(note_data["duration_beats"]) * seconds_per_beat
            note = pretty_midi.Note(
                velocity=int(note_data["velocity"]),
                pitch=int(note_data["pitch"]),
                start=start_time,
                end=start_time + duration,
            )
            melody_track.notes.append(note)
        midi.instruments.append(melody_track)

        buffer = io.BytesIO()
        midi.write(buffer)
        return buffer.getvalue()
