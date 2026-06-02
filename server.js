'use strict';

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = process.env.PORT || 3000;

// Serve static files from /public
app.use(express.static(path.join(__dirname, 'public')));

// ──────────────────────────────────────────────
// Bot brain – simple intent matcher
// ──────────────────────────────────────────────
const BOT_NAME = 'Aria';

const INTENTS = [
  {
    patterns: [/\bhello\b|\bhi\b|\bhey\b|\bgreetings\b/i],
    responses: [
      "Hey there! 👋 I'm Aria. How can I help you today?",
      "Hello! Great to see you. What's on your mind?",
      "Hi! I'm here and ready to chat. What can I do for you?"
    ]
  },
  {
    patterns: [/\bbye\b|\bgoodbye\b|\bsee you\b|\btake care\b/i],
    responses: [
      "Goodbye! 👋 Come back anytime.",
      "Take care! I'll be here when you need me.",
      "See you later! Have a great day! 😊"
    ]
  },
  {
    patterns: [/\bhow are you\b|\bhow do you do\b|\bwhat's up\b|\bwassup\b/i],
    responses: [
      "I'm doing great, thanks for asking! How about you?",
      "All systems go! 🤖 What about yourself?",
      "Feeling fantastic! Ready to help. What do you need?"
    ]
  },
  {
    patterns: [/\byour name\b|\bwho are you\b|\bwhat are you\b/i],
    responses: [
      "I'm Aria, your AI assistant. Nice to meet you! 😊",
      "The name's Aria — your friendly chatbot. How can I assist?",
      "I'm Aria, an AI built to chat and help. What can I do for you?"
    ]
  },
  {
    patterns: [/\bhelp\b|\bsupport\b|\bwhat can you do\b|\bcapabilit/i],
    responses: [
      "I can answer questions, have a conversation, tell jokes, and more! Just ask me anything.",
      "Happy to help! I can chat, answer questions, or just keep you company. Try me!",
      "I'm here to assist with questions, small talk, jokes, or anything you want to chat about."
    ]
  },
  {
    patterns: [/\bjoke\b|\bmake me laugh\b|\bfunny\b/i],
    responses: [
      "Why don't scientists trust atoms? Because they make up everything! 😄",
      "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads. 🍫",
      "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
      "How do you comfort a JavaScript bug? You console it. 😂"
    ]
  },
  {
    patterns: [/\btime\b|\bwhat time\b|\bclock\b/i],
    responses: [
      () => `It's currently ${new Date().toLocaleTimeString()} on your server. ⏰`,
    ]
  },
  {
    patterns: [/\bdate\b|\btoday\b|\bwhat day\b/i],
    responses: [
      () => `Today is ${new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}. 📅`,
    ]
  },
  {
    patterns: [/\bweather\b/i],
    responses: [
      "I don't have live weather data yet, but I'd recommend checking weather.com! 🌤️",
      "I can't pull live weather, but a quick search will have you covered! ⛅"
    ]
  },
  {
    patterns: [/\bthank(s| you)\b|\bthanks\b/i],
    responses: [
      "You're welcome! 😊 Anything else I can help with?",
      "Happy to help! Let me know if there's anything else.",
      "Anytime! That's what I'm here for. 🤖"
    ]
  },
  {
    patterns: [/\bsorry\b|\bapologi/i],
    responses: [
      "No worries at all! 😊",
      "It's totally fine! Don't sweat it.",
      "No problem whatsoever! How can I help?"
    ]
  },
];

const FALLBACKS = [
  "Hmm, I'm not sure I follow. Could you rephrase that?",
  "Interesting! Tell me more? 🤔",
  "I didn't quite catch that. Can you try asking differently?",
  "I'm still learning! Could you be more specific?",
  "That's outside my knowledge right now, but I'm always improving! 🚀"
];

function pickRandom(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function getBotReply(text) {
  for (const intent of INTENTS) {
    if (intent.patterns.some(p => p.test(text))) {
      const response = pickRandom(intent.responses);
      return typeof response === 'function' ? response() : response;
    }
  }
  return pickRandom(FALLBACKS);
}

// ──────────────────────────────────────────────
// WebSocket handler
// ──────────────────────────────────────────────
wss.on('connection', (ws) => {
  const clientId = uuidv4();
  console.log(`[+] Client connected: ${clientId}`);

  // Send welcome message
  const welcome = {
    id: uuidv4(),
    sender: BOT_NAME,
    type: 'bot',
    text: "👋 Hi! I'm **Aria**, your AI assistant. Ask me anything or just say hello!",
    timestamp: new Date().toISOString()
  };
  ws.send(JSON.stringify(welcome));

  ws.on('message', (raw) => {
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      return;
    }

    const userText = (payload.text || '').trim();
    if (!userText) return;

    console.log(`[${clientId}] User: ${userText}`);

    // Simulate typing delay (600–1400 ms)
    const delay = 600 + Math.random() * 800;

    // Send "typing" indicator immediately
    ws.send(JSON.stringify({ type: 'typing', sender: BOT_NAME }));

    setTimeout(() => {
      if (ws.readyState !== WebSocket.OPEN) return;

      const reply = {
        id: uuidv4(),
        sender: BOT_NAME,
        type: 'bot',
        text: getBotReply(userText),
        timestamp: new Date().toISOString()
      };

      console.log(`[${clientId}] Bot: ${reply.text}`);
      ws.send(JSON.stringify(reply));
    }, delay);
  });

  ws.on('close', () => {
    console.log(`[-] Client disconnected: ${clientId}`);
  });

  ws.on('error', (err) => {
    console.error(`[!] Error for ${clientId}:`, err.message);
  });
});

server.listen(PORT, () => {
  console.log(`\nChatbot server running → http://localhost:${PORT}\n`);
});
