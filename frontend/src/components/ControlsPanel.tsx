import { useEffect, useState } from 'react';
import type { Controls } from '../types';
import { DEFAULT_CONTROLS, GENRES, KEYS, MOODS } from '../types';

const CONTROLS_KEY = 'music_producer_controls';

interface ControlsPanelProps {
  controls: Controls;
  onChange: (controls: Controls) => void;
  errors: Record<string, string>;
}

export function ControlsPanel({ controls, onChange, errors }: ControlsPanelProps) {
  const update = (partial: Partial<Controls>) => {
    onChange({ ...controls, ...partial });
  };

  return (
    <div className="panel">
      <h2>Controls</h2>
      <div className="control-group">
        <label htmlFor="tempo">Tempo (BPM)</label>
        <input
          id="tempo"
          type="number"
          min={40}
          max={240}
          value={controls.tempo_bpm}
          onChange={(e) => update({ tempo_bpm: Number(e.target.value) })}
        />
        {errors.tempo_bpm && <div className="error-text">{errors.tempo_bpm}</div>}
      </div>
      <div className="control-group">
        <label htmlFor="key">Key</label>
        <select id="key" value={controls.key} onChange={(e) => update({ key: e.target.value })}>
          {KEYS.map((key) => (
            <option key={key} value={key}>{key}</option>
          ))}
        </select>
        {errors.key && <div className="error-text">{errors.key}</div>}
      </div>
      <div className="control-group">
        <label htmlFor="genre">Genre</label>
        <select
          id="genre"
          value={controls.genre}
          onChange={(e) => update({ genre: e.target.value as Controls['genre'], genre_custom: undefined })}
        >
          {GENRES.map((genre) => (
            <option key={genre} value={genre}>{genre}</option>
          ))}
        </select>
        {controls.genre === 'other' && (
          <input
            style={{ marginTop: '0.5rem' }}
            placeholder="Custom genre (max 50 chars)"
            maxLength={50}
            value={controls.genre_custom ?? ''}
            onChange={(e) => update({ genre_custom: e.target.value })}
          />
        )}
        {errors.genre && <div className="error-text">{errors.genre}</div>}
      </div>
      <div className="control-group">
        <label htmlFor="mood">Mood</label>
        <select
          id="mood"
          value={controls.mood}
          onChange={(e) => update({ mood: e.target.value as Controls['mood'], mood_custom: undefined })}
        >
          {MOODS.map((mood) => (
            <option key={mood} value={mood}>{mood}</option>
          ))}
        </select>
        {controls.mood === 'other' && (
          <input
            style={{ marginTop: '0.5rem' }}
            placeholder="Custom mood (max 50 chars)"
            maxLength={50}
            value={controls.mood_custom ?? ''}
            onChange={(e) => update({ mood_custom: e.target.value })}
          />
        )}
        {errors.mood && <div className="error-text">{errors.mood}</div>}
      </div>
    </div>
  );
}

export function usePersistedControls(): [Controls, (c: Controls) => void] {
  const [controls, setControls] = useState<Controls>(() => {
    try {
      const stored = sessionStorage.getItem(CONTROLS_KEY);
      return stored ? { ...DEFAULT_CONTROLS, ...JSON.parse(stored) } : DEFAULT_CONTROLS;
    } catch {
      return DEFAULT_CONTROLS;
    }
  });

  useEffect(() => {
    sessionStorage.setItem(CONTROLS_KEY, JSON.stringify(controls));
  }, [controls]);

  return [controls, setControls];
}

export function validateControlsClient(controls: Controls): Record<string, string> {
  const errors: Record<string, string> = {};
  if (controls.tempo_bpm < 40 || controls.tempo_bpm > 240) {
    errors.tempo_bpm = 'BPM must be between 40 and 240';
  }
  if (!KEYS.includes(controls.key as typeof KEYS[number])) {
    errors.key = 'Invalid key';
  }
  if (!GENRES.includes(controls.genre)) {
    errors.genre = 'Invalid genre';
  }
  if (!MOODS.includes(controls.mood)) {
    errors.mood = 'Invalid mood';
  }
  if (controls.genre === 'other' && !controls.genre_custom?.trim()) {
    errors.genre = 'Custom genre required';
  }
  if (controls.mood === 'other' && !controls.mood_custom?.trim()) {
    errors.mood = 'Custom mood required';
  }
  return errors;
}
