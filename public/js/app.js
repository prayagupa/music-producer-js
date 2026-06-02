/* ── Chatbot frontend ─────────────────────────────── */
(function () {
  'use strict';

  // ── DOM refs ────────────────────────────────────
  const messagesList    = document.getElementById('messagesList');
  const messagesContainer = document.getElementById('messagesContainer');
  const msgInput        = document.getElementById('msgInput');
  const sendBtn         = document.getElementById('sendBtn');
  const typingIndicator = document.getElementById('typingIndicator');
  const statusDot       = document.getElementById('statusDot');
  const statusText      = document.getElementById('statusText');
  const headerStatus    = document.getElementById('headerStatus');
  const clearBtn        = document.getElementById('clearBtn');
  const newChatBtn      = document.getElementById('newChatBtn');
  const convoList       = document.getElementById('convoList');

  // ── State ───────────────────────────────────────
  let ws           = null;
  let reconnectTimer = null;
  let messageCount = 0;
  const USER_NAME  = 'You';
  const BOT_NAME   = 'Aria';

  // ── Helpers ─────────────────────────────────────
  function formatTime(isoString) {
    const d = isoString ? new Date(isoString) : new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /** Render simple **bold** markdown */
  function renderMarkdown(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g,     '<em>$1</em>');
  }

  function scrollToBottom() {
    messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: 'smooth' });
  }

  // ── Empty state ─────────────────────────────────
  function showEmptyState() {
    messagesList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🤖</div>
        <h2 class="empty-title">Chat with Aria</h2>
        <p class="empty-sub">Ask me anything — I'm here to help, answer questions, or just chat.</p>
        <div class="suggestion-chips">
          <button class="chip" data-msg="Hello! Who are you?">👋 Who are you?</button>
          <button class="chip" data-msg="Tell me a joke">😄 Tell me a joke</button>
          <button class="chip" data-msg="What can you do?">🛠️ What can you do?</button>
          <button class="chip" data-msg="What's the time?">⏰ What's the time?</button>
        </div>
      </div>
    `;
    // Wire up chips
    messagesList.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const msg = chip.getAttribute('data-msg');
        msgInput.value = msg;
        sendMessage();
      });
    });
  }

  // ── Append a message bubble ──────────────────────
  function appendMessage({ sender, type, text, timestamp }) {
    // Remove empty state on first real message
    if (messageCount === 0) {
      messagesList.innerHTML = '';
    }
    messageCount++;

    const isUser = type === 'user';
    const row = document.createElement('div');
    row.className = `msg-row ${type}`;
    row.innerHTML = `
      <div class="msg-avatar">${isUser ? '🧑' : '🤖'}</div>
      <div class="msg-content">
        <span class="msg-sender">${isUser ? USER_NAME : BOT_NAME}</span>
        <div class="msg-bubble">${renderMarkdown(escapeHtml(text))}</div>
        <span class="msg-time">${formatTime(timestamp)}</span>
      </div>
    `;
    messagesList.appendChild(row);
    scrollToBottom();
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Send a message ───────────────────────────────
  function sendMessage() {
    const text = msgInput.value.trim();
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

    appendMessage({ sender: USER_NAME, type: 'user', text, timestamp: new Date().toISOString() });

    ws.send(JSON.stringify({ text }));

    msgInput.value = '';
    msgInput.style.height = 'auto';
    sendBtn.disabled = true;
  }

  // ── Connection status helpers ────────────────────
  function setStatus(state) {
    statusDot.className = 'status-dot ' + state;
    if (state === 'connected') {
      statusText.textContent = 'Connected';
      headerStatus.textContent = 'Online';
      headerStatus.className = 'bot-status online';
    } else if (state === 'disconnected') {
      statusText.textContent = 'Disconnected';
      headerStatus.textContent = 'Offline';
      headerStatus.className = 'bot-status';
    } else {
      statusText.textContent = 'Connecting…';
      headerStatus.textContent = 'Connecting…';
      headerStatus.className = 'bot-status';
    }
  }

  // ── WebSocket ────────────────────────────────────
  function connect() {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${protocol}://${location.host}`;

    setStatus('connecting');
    ws = new WebSocket(url);

    ws.addEventListener('open', () => {
      setStatus('connected');
      clearTimeout(reconnectTimer);
      console.log('[WS] connected');
    });

    ws.addEventListener('message', (event) => {
      let payload;
      try { payload = JSON.parse(event.data); } catch { return; }

      if (payload.type === 'typing') {
        typingIndicator.classList.remove('hidden');
        scrollToBottom();
        return;
      }

      typingIndicator.classList.add('hidden');
      appendMessage(payload);
    });

    ws.addEventListener('close', () => {
      setStatus('disconnected');
      console.log('[WS] disconnected — retrying in 3 s');
      reconnectTimer = setTimeout(connect, 3000);
    });

    ws.addEventListener('error', (err) => {
      console.error('[WS] error', err);
      ws.close();
    });
  }

  // ── Clear chat ───────────────────────────────────
  function clearChat() {
    messageCount = 0;
    typingIndicator.classList.add('hidden');
    showEmptyState();
  }

  // ── New chat (sidebar) ───────────────────────────
  function addConvoItem(name) {
    const li = document.createElement('li');
    li.className = 'convo-item active';
    li.innerHTML = `<span class="convo-icon">💬</span><span class="convo-name">${name}</span>`;
    // Deactivate others
    convoList.querySelectorAll('.convo-item').forEach(i => i.classList.remove('active'));
    convoList.appendChild(li);
    li.addEventListener('click', () => {
      convoList.querySelectorAll('.convo-item').forEach(i => i.classList.remove('active'));
      li.classList.add('active');
    });
  }

  // ── Auto-grow textarea ───────────────────────────
  msgInput.addEventListener('input', () => {
    sendBtn.disabled = msgInput.value.trim() === '';
    msgInput.style.height = 'auto';
    msgInput.style.height = Math.min(msgInput.scrollHeight, 160) + 'px';
  });

  msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);

  clearBtn.addEventListener('click', clearChat);

  newChatBtn.addEventListener('click', () => {
    clearChat();
    const num = convoList.querySelectorAll('.convo-item').length + 1;
    addConvoItem(`Chat ${num}`);
  });

  // ── Boot ─────────────────────────────────────────
  showEmptyState();
  connect();

})();
