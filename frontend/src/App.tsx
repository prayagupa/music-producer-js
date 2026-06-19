import { useCallback, useEffect, useState } from 'react';
import { createSession, fetchHealth, generateMusic } from './api';
import { ChatPanel } from './components/ChatPanel';
import {
  ControlsPanel,
  usePersistedControls,
  validateControlsClient,
} from './components/ControlsPanel';
import { MidiPreview } from './components/MidiPreview';
import type { ApiError, ChatMessage, GenerateResponse, HealthResponse } from './types';
import { ERROR_MESSAGES } from './types';

const SESSION_KEY = 'music_producer_session_id';

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [controls, setControls] = usePersistedControls();
  const [controlErrors, setControlErrors] = useState<Record<string, string>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastGeneration, setLastGeneration] = useState<GenerateResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);

  const loadHealth = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000);
    return () => clearInterval(interval);
  }, [loadHealth]);

  useEffect(() => {
    const init = async () => {
      const stored = sessionStorage.getItem(SESSION_KEY);
      if (stored) {
        setSessionId(stored);
        return;
      }
      try {
        const session = await createSession();
        sessionStorage.setItem(SESSION_KEY, session.session_id);
        setSessionId(session.session_id);
      } catch {
        setToast('Failed to create session. Check backend connection.');
      }
    };
    init();
  }, []);

  const showError = (error: ApiError, retryMessage?: string) => {
    const message = ERROR_MESSAGES[error.code] ?? error.message;
    setToast(message);
    if (retryMessage) setLastFailedMessage(retryMessage);
  };

  const handleSend = async (message: string) => {
    if (!sessionId) return;

    const errors = validateControlsClient(controls);
    setControlErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsGenerating(true);
    setMessages((prev) => [...prev, { role: 'user', content: message }]);

    try {
      const result = await generateMusic(sessionId, message, controls);
      setLastGeneration(result);
      setMessages((prev) => [...prev, { role: 'assistant', content: result.assistant_message }]);
      setLastFailedMessage(null);
      loadHealth();
    } catch (err) {
      const apiError = err as ApiError;
      setMessages((prev) => prev.slice(0, -1));
      showError(apiError, message);
      if (apiError.code === 'OLLAMA_UNAVAILABLE') {
        loadHealth();
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const retryLast = () => {
    if (lastFailedMessage) {
      handleSend(lastFailedMessage);
    }
  };

  const ollamaDown = health?.checks.ollama === 'down';

  return (
    <div className="app-shell">
      <header className="header">
        <h1>♪ Music Producer</h1>
        <span className={`status-badge ${health?.status === 'ok' ? 'ok' : 'degraded'}`}>
          Ollama {health?.checks.ollama === 'up' ? '● Connected' : health?.checks.ollama === 'down' ? '● Down' : '● Checking'}
        </span>
      </header>

      {ollamaDown && (
        <div className="banner">
          <div>
            <strong>⚠ Ollama unavailable</strong>
            <p style={{ margin: '0.25rem 0 0' }}>
              Start the local LLM with: <code>docker compose up ollama</code>
            </p>
          </div>
          <button className="secondary" onClick={() => { loadHealth(); retryLast(); }}>
            Retry
          </button>
        </div>
      )}

      <div className="layout">
        <aside>
          <ControlsPanel controls={controls} onChange={setControls} errors={controlErrors} />
          {lastGeneration && (
            <div className="panel" style={{ marginTop: '1rem' }}>
              <h2>Metadata</h2>
              <div className="metadata-grid">
                <span>BPM:</span><span>{lastGeneration.metadata.tempo_bpm}</span>
                <span>Key:</span><span>{lastGeneration.metadata.key}</span>
                <span>Genre:</span><span>{lastGeneration.metadata.genre}</span>
                <span>Mood:</span><span>{lastGeneration.metadata.mood}</span>
                <span>Model:</span><span>{lastGeneration.metadata.model}</span>
              </div>
            </div>
          )}
        </aside>
        <main>
          <ChatPanel messages={messages} isGenerating={isGenerating} onSend={handleSend} />
        </main>
      </div>

      <MidiPreview
        generationId={lastGeneration?.generation_id ?? null}
        metadata={lastGeneration?.metadata ?? null}
      />

      {toast && (
        <div className="toast" onClick={() => setToast(null)}>
          {toast}
          {(toast.includes('unavailable') || toast.includes('503')) && lastFailedMessage && (
            <button className="secondary" style={{ marginLeft: '0.5rem' }} onClick={retryLast}>
              Retry
            </button>
          )}
        </div>
      )}
    </div>
  );
}
