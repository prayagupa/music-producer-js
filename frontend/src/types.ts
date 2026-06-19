export const KEYS = [
  'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
  'Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm',
] as const;

export const GENRES = [
  'lo-fi', 'pop', 'jazz', 'electronic', 'hip-hop', 'ambient', 'rock', 'classical', 'other',
] as const;

export const MOODS = [
  'happy', 'melancholic', 'energetic', 'dark', 'calm', 'tense', 'romantic', 'other',
] as const;

export type Genre = (typeof GENRES)[number];
export type Mood = (typeof MOODS)[number];

export interface Controls {
  tempo_bpm: number;
  key: string;
  genre: Genre;
  mood: Mood;
  genre_custom?: string;
  mood_custom?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface GenerationMetadata {
  tempo_bpm: number;
  key: string;
  genre: string;
  mood: string;
  time_signature: string;
  bars: number;
  model: string;
  provider: string;
  latency_ms: number;
}

export interface GenerateResponse {
  generation_id: string;
  session_id: string;
  assistant_message: string;
  metadata: GenerationMetadata;
  spec: Record<string, unknown>;
  midi_url: string;
  preview_ready: boolean;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  version: string;
  checks: { api: string; ollama: string };
  message?: string;
}

export interface ApiError {
  code: string;
  message: string;
}

export const ERROR_MESSAGES: Record<string, string> = {
  INVALID_CONTROLS: 'Check your controls — BPM, key, genre, or mood may be invalid.',
  LLM_OUTPUT_INVALID: 'Could not generate valid music. Try a simpler prompt with fewer details.',
  OLLAMA_UNAVAILABLE: 'Local LLM is unavailable. Start Ollama with: docker compose up ollama',
  OPENAI_UNAVAILABLE: 'OpenAI API is unavailable. Check your API key and network connection.',
  GENERATION_TIMEOUT: 'Generation timed out. Try a shorter prompt or check your hardware.',
  MIDI_GENERATION_FAILED: 'Failed to build MIDI from the specification.',
  SESSION_NOT_FOUND: 'Session expired. Refresh the page to start a new session.',
  SESSION_LIMIT: 'Session limit reached. Refresh to start a new session.',
};

export const DEFAULT_CONTROLS: Controls = {
  tempo_bpm: 120,
  key: 'C',
  genre: 'pop',
  mood: 'happy',
};
