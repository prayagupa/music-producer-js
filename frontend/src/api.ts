import type { ApiError, Controls, GenerateResponse, HealthResponse } from './types';

const API_BASE = '/api/v1';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = (await response.json().catch(() => ({
      code: 'UNKNOWN',
      message: response.statusText,
    }))) as ApiError;
    throw error;
  }
  return response.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  return handleResponse<HealthResponse>(response);
}

export async function createSession(): Promise<{ session_id: string; created_at: string }> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  return handleResponse(response);
}

export async function generateMusic(
  sessionId: string,
  message: string,
  controls: Controls,
): Promise<GenerateResponse> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, controls }),
  });
  return handleResponse<GenerateResponse>(response);
}

export async function fetchMidi(generationId: string): Promise<ArrayBuffer> {
  const response = await fetch(`${API_BASE}/midi/${generationId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch MIDI');
  }
  return response.arrayBuffer();
}

export function downloadMidi(generationId: string, buffer: ArrayBuffer): void {
  const blob = new Blob([buffer], { type: 'audio/midi' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${generationId}.mid`;
  anchor.click();
  URL.revokeObjectURL(url);
}
