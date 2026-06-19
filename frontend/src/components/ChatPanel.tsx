import { useRef, useState } from 'react';
import type { ChatMessage } from '../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  isGenerating: boolean;
  onSend: (message: string) => void;
}

export function ChatPanel({ messages, isGenerating, onSend }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [optimistic, setOptimistic] = useState<ChatMessage[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isGenerating) return;
    setOptimistic([{ role: 'user', content: trimmed }]);
    setInput('');
    onSend(trimmed);
    setTimeout(() => setOptimistic([]), 50);
  };

  const displayMessages = [...messages, ...optimistic];

  return (
    <div className="panel">
      <h2>Chat</h2>
      <div className="chat-messages">
        {displayMessages.length === 0 && (
          <div className="message assistant">Describe the music you want to create...</div>
        )}
        {displayMessages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong> {msg.content}
          </div>
        ))}
        {isGenerating && (
          <div className="message assistant">
            <span className="spinner" /> Generating...
          </div>
        )}
      </div>
      <div className="chat-input-row">
        <input
          ref={inputRef}
          value={input}
          placeholder='Refine... e.g. "add hi-hats"'
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={isGenerating}
        />
        <button className="primary" onClick={handleSend} disabled={isGenerating || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
