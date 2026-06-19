import { useCallback, useEffect, useRef, useState } from 'react';
import * as Tone from 'tone';
import { Midi } from '@tonejs/midi';
import { downloadMidi, fetchMidi } from '../api';
import type { GenerationMetadata } from '../types';

interface MidiPreviewProps {
  generationId: string | null;
  metadata: GenerationMetadata | null;
}

export function MidiPreview({ generationId, metadata }: MidiPreviewProps) {
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const midiRef = useRef<Midi | null>(null);
  const bufferRef = useRef<ArrayBuffer | null>(null);
  const scheduledRef = useRef<number[]>([]);

  const stopPlayback = useCallback(() => {
    scheduledRef.current.forEach((id) => Tone.getTransport().clear(id));
    scheduledRef.current = [];
    Tone.getTransport().stop();
    Tone.getTransport().cancel();
    setIsPlaying(false);
  }, []);

  useEffect(() => {
    stopPlayback();
    midiRef.current = null;
    bufferRef.current = null;
    setDuration(0);

    if (!generationId) return;

    let cancelled = false;
    setLoading(true);
    fetchMidi(generationId)
      .then((buffer) => {
        if (cancelled) return;
        bufferRef.current = buffer;
        const midi = new Midi(buffer);
        midiRef.current = midi;
        setDuration(midi.duration);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      stopPlayback();
    };
  }, [generationId, stopPlayback]);

  const play = async () => {
    if (!midiRef.current) return;
    await Tone.start();
    stopPlayback();
    Tone.getTransport().bpm.value = metadata?.tempo_bpm ?? 120;
    const now = Tone.now();
    midiRef.current.tracks.forEach((track) => {
      track.notes.forEach((note) => {
        const synth = track.instrument.percussion
          ? new Tone.MembraneSynth().toDestination()
          : new Tone.PolySynth(Tone.Synth).toDestination();
        const id = Tone.getTransport().schedule((time) => {
          synth.triggerAttackRelease(note.name, note.duration, time, note.velocity / 127);
        }, now + note.time);
        scheduledRef.current.push(id);
      });
    });
    Tone.getTransport().start();
    setIsPlaying(true);
  };

  const pause = () => {
    Tone.getTransport().pause();
    setIsPlaying(false);
  };

  const handleDownload = () => {
    if (generationId && bufferRef.current) {
      downloadMidi(generationId, bufferRef.current);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="panel preview-panel">
      <h2>MIDI Preview</h2>
      {loading && <p>Loading MIDI...</p>}
      {!generationId && !loading && (
        <p className="preview-meta">Generate music to preview and download MIDI.</p>
      )}
      {generationId && !loading && (
        <>
          <div className="preview-controls">
            <button className="secondary" onClick={play} disabled={!midiRef.current}>
              ▶ Play
            </button>
            <button className="secondary" onClick={pause} disabled={!isPlaying}>
              ⏸ Pause
            </button>
            <button className="secondary" onClick={stopPlayback}>
              ⏹ Stop
            </button>
            <button className="primary" onClick={handleDownload} disabled={!bufferRef.current}>
              ⬇ Download MIDI
            </button>
          </div>
          <p className="preview-meta">
            Duration: {formatDuration(duration)} · Bars: {metadata?.bars ?? '—'}
          </p>
          <p className="preview-meta">Click Play to hear preview (no autoplay).</p>
        </>
      )}
    </div>
  );
}
