# Software Design Specification — Music Producer App

## 1. Overview

| Field | Value |
|-------|-------|
| **Feature ID** | 001 |
| **Feature Name** | Music Producer App |
| **Date** | 2026-06-19 |
| **Author** | Spec Agent |
| **Related PRD** | [docs/001/PRD.md](./PRD.md) |
| **Status** | Approved (post self-review) |

This specification defines a greenfield replacement of the legacy Angular/Express "Aria" chatbot with a local-first, AI-assisted music composition application. MVP output is **MIDI** (chords, drums, melody). WAV export is explicitly out of scope (P2).

---

## 2. Problem & Goals

### Problem
Independent creators cannot turn natural-language musical intent into playable output using the current codebase. The legacy stack is a pattern-matching chatbot with no LLM and no music generation.

### Primary User
Music creators (bedroom producers, content creators, developer-producers) who want conversational AI-assisted composition with structured parameter control and local OSS inference.

### Success Metrics (from PRD)

| Metric | Target |
|--------|--------|
| Legacy removal | 100% legacy files deleted (Story 1) |
| Golden-prompt schema pass rate | ≥ 95% |
| Golden-prompt constraint pass rate | ≥ 90% |
| LLM-as-judge mean score | ≥ 4.0 / 5.0 |
| End-to-end latency (P95) | ≤ 30s on 16GB RAM / M1-class hardware |
| Internal unaided E2E success | 3/3 test users |
| CI eval on every PR | 100% |

---

## 3. Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Browser (React SPA)                           │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │ Chat Panel   │  │ Controls Panel  │  │ MIDI Preview + Download  │  │
│  │ (multi-turn) │  │ BPM/key/genre/  │  │ Tone.js playback         │  │
│  │              │  │ mood            │  │                          │  │
│  └──────┬───────┘  └────────┬────────┘  └────────────┬─────────────┘  │
└─────────┼───────────────────┼──────────────────────────┼────────────────┘
          │ REST + SSE        │                          │ GET /midi/{id}
          ▼                   ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python 3.11+)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ API Layer   │→ │ Application  │→ │ Domain      │→ │ Adapters     │ │
│  │ (routes)    │  │ Services     │  │ (MusicSpec, │  │ (LLM, MIDI,  │ │
│  │             │  │              │  │  Session)   │  │  Storage)    │ │
│  └─────────────┘  └──────────────┘  └─────────────┘  └──────┬───────┘ │
└───────────────────────────────────────────────────────────────┼─────────┘
                                                                │
          ┌─────────────────────────────────────────────────────┤
          │                                                     │
          ▼                                                     ▼
┌──────────────────┐                              ┌───────────────────────┐
│ Ollama Sidecar   │                              │ In-Memory Session     │
│ llama3:8b        │                              │ Store (per session_id)│
│ (default)        │                              │ + ephemeral MIDI blobs│
└──────────────────┘                              └───────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         Eval CLI (offline / CI)                         │
│  golden prompts → LLM (or mock) → schema L1 → constraints L2 →          │
│  structure L3 → LLM-judge L4 → JSON/HTML report                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow (Happy Path)

1. User enters chat message + structured controls (BPM, key, genre, mood).
2. Frontend `POST /api/v1/sessions/{session_id}/generate` with message and controls.
3. Backend assembles prompt (system + sliding window of last 6 turns + controls).
4. `LlmProvider` calls Ollama (`llama3:8b`) → raw JSON string.
5. `MusicSpecValidator` parses and validates against JSON Schema (retry up to 2× on failure).
6. `MidiGenerator` converts validated spec → `.mid` bytes (3 tracks: chords, drums, melody).
7. Backend stores spec + MIDI in session; returns metadata + playback URL.
8. Frontend loads MIDI via Tone.js, plays preview; user downloads via `GET /api/v1/midi/{generation_id}`.

### Architecture Style

**Clean / Hexagonal Architecture** with explicit ports:

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Domain | `backend/src/domain/` | `MusicSpec`, enums, validation rules, pure MIDI mapping logic |
| Application | `backend/src/application/` | Orchestration: `GenerateMusicUseCase`, `SessionService` |
| Adapters (in) | `backend/src/adapters/inbound/` | FastAPI routes, request/response DTOs |
| Adapters (out) | `backend/src/adapters/outbound/` | Ollama client, OpenAI client, in-memory repos |
| Infrastructure | `backend/src/infrastructure/` | Config, logging, dependency injection |

---

## 4. Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Backend runtime | Python 3.11+ | PRD A8; rich MIDI/eval ecosystem |
| Backend framework | FastAPI + Uvicorn | Async HTTP, OpenAPI, SSE support |
| Frontend | React 18 + TypeScript + Vite | PRD default; strong component ecosystem |
| LLM (default) | Ollama + `llama3:8b` | Local OSS; fits 16GB RAM (PRD A9) |
| LLM (fallback) | OpenAI GPT-4o-mini | Cost-effective; env-gated (FR-008) |
| MIDI generation | `pretty_midi` + `mido` | Mature Python MIDI libraries |
| Schema validation | `jsonschema` (Python), Ajv (frontend preview) | L1 eval + API contract |
| In-browser playback | Tone.js + `@tonejs/midi` | Reliable Web Audio MIDI playback |
| Containerization | Docker Compose | App + Ollama sidecar (FR-017) |
| CI | GitHub Actions | Eval on PR (FR-016) |
| Testing | pytest, pytest-asyncio, httpx, Playwright (smoke) | Backend + E2E smoke |
| Logging | structlog (JSON) | NFR-012 structured logs |

**Note:** No `.cursor/rules/repo-config.mdc` exists. Stack follows PRD defaults, not Java/Spring defaults.

---

## 5. Component Design

### 5.1 Frontend — Chat Panel

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Capture user messages, display assistant responses and generation status |
| **Interfaces** | `POST /api/v1/sessions`, `POST .../generate`, SSE optional for status |
| **Dependencies** | React Query, session context, controls state |
| **State** | `sessionId`, `messages[]`, `isGenerating`, `lastGeneration` |

### 5.2 Frontend — Controls Panel

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Structured inputs: tempo, key, genre, mood |
| **Interfaces** | Bundled into generate request body |
| **Dependencies** | Shared form state with chat |
| **Validation** | Client-side range checks mirror backend enums |

**Control enums (fixed taxonomy + optional free text):**

| Control | Type | Values |
|---------|------|--------|
| `tempo_bpm` | integer | 40–240 (default 120) |
| `key` | enum | C, C#, D, …, B + major/minor (24 values) |
| `genre` | enum | lo-fi, pop, jazz, electronic, hip-hop, ambient, rock, classical, other |
| `mood` | enum | happy, melancholic, energetic, dark, calm, tense, romantic, other |
| `genre_custom` | string? | Required when genre=other (max 50 chars) |
| `mood_custom` | string? | Required when mood=other (max 50 chars) |

### 5.3 Frontend — MIDI Preview

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Play/pause/stop generated MIDI; show metadata; trigger download |
| **Interfaces** | `GET /api/v1/midi/{generation_id}` |
| **Dependencies** | Tone.js Transport, `@tonejs/midi` parser |

### 5.4 Backend — GenerateMusicUseCase

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Orchestrate LLM → validate → MIDI → persist |
| **Interfaces** | `GenerateMusicCommand` → `GenerationResult` |
| **Dependencies** | `LlmProviderPort`, `MusicSpecValidator`, `MidiGeneratorPort`, `SessionRepositoryPort` |
| **Retry policy** | Up to 2 JSON repair retries before surfacing error |

### 5.5 Backend — LlmProvider (Port)

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Abstract LLM inference behind common interface |
| **Implementations** | `OllamaLlmProvider` (default), `OpenAiLlmProvider` (env-gated) |
| **Selection** | `LLM_PROVIDER=ollama` (default) or `openai` when `USE_OPENAI=true` + key present |

### 5.6 Backend — MidiGenerator

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Deterministic conversion MusicSpec → Standard MIDI File |
| **Output tracks** | Track 1: Chords (program 0 piano), Track 2: Drums (channel 10), Track 3: Melody (program 0) |
| **Dependencies** | `pretty_midi` |
| **Constraints** | 4/4 default; 1 bar minimum, 8 bars maximum for MVP |

### 5.7 Backend — SessionRepository (In-Memory)

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Store session messages, generations, MIDI bytes |
| **TTL** | 24h in-memory; lost on restart (MVP acceptable per PRD A10) |
| **Future** | Interface allows Redis/DB swap without domain changes |

### 5.8 Eval CLI

| Attribute | Detail |
|-----------|--------|
| **Responsibility** | Run golden dataset through 4 eval layers; emit report |
| **Entry points** | `make eval`, `make eval-quick`, `python -m eval.run` |
| **CI modes** | `eval-quick` with mock LLM on PR; full Ollama on nightly workflow |

---

## 6. API Design

Base URL: `/api/v1`

| Method | Endpoint | Request | Response | Notes |
|--------|----------|---------|----------|-------|
| GET | `/health` | — | `{ "status": "ok", "ollama": "up\|down", "version": "..." }` | Docker healthcheck |
| POST | `/sessions` | `{ "client_label"?: string }` | `{ "session_id": "uuid", "created_at": "ISO8601" }` | Creates in-memory session |
| GET | `/sessions/{session_id}` | — | `{ "session_id", "messages", "generations" }` | Session history |
| POST | `/sessions/{session_id}/generate` | See below | See below | Core generation |
| GET | `/midi/{generation_id}` | — | `application/octet-stream` (.mid) | Download |
| GET | `/generations/{generation_id}` | — | `{ metadata, spec, midi_url }` | Poll after generate |

### POST `/sessions/{session_id}/generate`

**Request:**
```json
{
  "message": "sad lo-fi beat with soft drums",
  "controls": {
    "tempo_bpm": 80,
    "key": "Am",
    "genre": "lo-fi",
    "mood": "melancholic"
  }
}
```

**Response (200):**
```json
{
  "generation_id": "uuid",
  "session_id": "uuid",
  "assistant_message": "Created a melancholic lo-fi progression in A minor at 80 BPM.",
  "metadata": {
    "tempo_bpm": 80,
    "key": "Am",
    "genre": "lo-fi",
    "mood": "melancholic",
    "time_signature": "4/4",
    "bars": 4,
    "model": "llama3:8b",
    "provider": "ollama",
    "latency_ms": 12450
  },
  "spec": { "...": "validated MusicSpec JSON" },
  "midi_url": "/api/v1/midi/{generation_id}",
  "preview_ready": true
}
```

**Error responses:**

| Status | Code | When |
|--------|------|------|
| 400 | `INVALID_CONTROLS` | BPM/key/genre out of range |
| 422 | `LLM_OUTPUT_INVALID` | JSON/schema failed after retries |
| 503 | `OLLAMA_UNAVAILABLE` | Sidecar down |
| 504 | `GENERATION_TIMEOUT` | LLM exceeded 25s |
| 500 | `MIDI_GENERATION_FAILED` | Unexpected conversion error |

---

## 7. Mockups

### 7.1 Mockup — Main Application UI

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ♪ Music Producer                                    [Ollama ● Connected]  │
├──────────────────────────────┬─────────────────────────────────────────────┤
│  CONTROLS                    │  CHAT                                       │
│  ┌────────────────────────┐  │  ┌─────────────────────────────────────────┐│
│  │ Tempo (BPM)  [  80  ]  │  │  │ You: sad lo-fi beat, minimal drums      ││
│  │ Key          [ Am  ▼]  │  │  │                                         ││
│  │ Genre        [lo-fi▼]  │  │  │ Assistant: Created a melancholic lo-fi  ││
│  │ Mood         [melan▼]  │  │  │ progression in A minor at 80 BPM.       ││
│  └────────────────────────┘  │  └─────────────────────────────────────────┘│
│                              │  ┌─────────────────────────────────────────┐│
│  METADATA (last generation)  │  │ Refine... e.g. "add hi-hats"     [Send]││
│  BPM: 80  Key: Am            │  └─────────────────────────────────────────┘│
│  Genre: lo-fi  Model: llama3 │                                             │
├──────────────────────────────┴─────────────────────────────────────────────┤
│  MIDI PREVIEW                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │  [▶ Play]  [⏸ Pause]  [⏹ Stop]          [⬇ Download MIDI]              ││
│  │  ▁▂▃▅▇▅▃▂▁▂▃▅▇  (waveform placeholder)   Duration: 0:12  Bars: 4       ││
│  └────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Mockup — Error State (Ollama Down)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ⚠ Ollama unavailable                                                      │
│  The local LLM service is not running. Start it with:                      │
│    docker compose up ollama                                                │
│  Then click [Retry]                                                       │
└────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Mockup — API Health Response

```json
{
  "status": "degraded",
  "version": "0.1.0",
  "checks": {
    "api": "up",
    "ollama": "down"
  },
  "message": "Ollama sidecar unreachable at http://ollama:11434"
}
```

### 7.4 Mockup — Generation SSE Status Events (optional P1 enhancement)

```
event: status
data: {"phase":"llm","message":"Generating music specification..."}

event: status
data: {"phase":"midi","message":"Building MIDI tracks..."}

event: complete
data: {"generation_id":"abc-123","midi_url":"/api/v1/midi/abc-123"}
```

### 7.5 Mockup — Eval CLI Output

```
$ make eval-quick

Music Producer Eval — dataset v1.0.0 (5/20 prompts)
────────────────────────────────────────────────────
L1 Schema          ████████████████████  5/5  (100%)
L2 Constraints     ████████████████████  5/5  (100%)
L3 Structure       ███████████████████░  4/5  ( 80%)
L4 Judge (mean)    4.2/5.0  (threshold: 4.0) ✓
Latency P95        18,432 ms  (threshold: 30,000 ms) ✓

Report: eval/reports/eval-20260619-143022.json
Status: PASS (PR gate)
```

### 7.6 Mockup — CI Eval Report Summary (JSON artifact)

```json
{
  "dataset_version": "1.0.0",
  "run_id": "ci-12345",
  "mode": "quick-mock",
  "metrics": {
    "schema_pass_rate": 1.0,
    "constraint_pass_rate": 1.0,
    "structure_pass_rate": 0.95,
    "judge_score_mean": 4.1,
    "latency_p95_ms": 2100
  },
  "gates": {
    "schema": { "threshold": 0.90, "passed": true },
    "constraints": { "threshold": 0.85, "passed": true },
    "judge": { "threshold": 4.0, "passed": true, "blocking": false }
  },
  "prompts": [ { "id": "gp-001", "l1": true, "l2": true, "l3": true, "judge": 4.5 } ]
}
```

---

## 8. Data Model

### 8.1 Music Spec JSON Schema (Canonical)

File: `backend/schemas/music_spec.v1.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "music_spec.v1",
  "type": "object",
  "required": ["version", "meta", "chords", "drums", "melody"],
  "properties": {
    "version": { "const": "1.0" },
    "meta": {
      "type": "object",
      "required": ["tempo_bpm", "key", "genre", "mood", "time_signature", "bars"],
      "properties": {
        "tempo_bpm": { "type": "integer", "minimum": 40, "maximum": 240 },
        "key": { "type": "string", "pattern": "^(A|A#|B|C|C#|D|D#|E|F|F#|G|G#)(m)?$" },
        "genre": { "type": "string", "maxLength": 50 },
        "mood": { "type": "string", "maxLength": 50 },
        "time_signature": { "enum": ["4/4", "3/4", "6/8"] },
        "bars": { "type": "integer", "minimum": 1, "maximum": 8 }
      }
    },
    "chords": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["symbol", "start_bar", "duration_beats"],
        "properties": {
          "symbol": { "type": "string", "description": "Roman numeral e.g. i, iv, V7" },
          "start_bar": { "type": "integer", "minimum": 1 },
          "duration_beats": { "type": "number", "minimum": 0.5 }
        }
      }
    },
    "drums": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["instrument", "start_beat", "velocity"],
        "properties": {
          "instrument": { "enum": ["kick", "snare", "hihat_closed", "hihat_open", "clap", "tom"] },
          "start_beat": { "type": "number", "minimum": 0 },
          "velocity": { "type": "integer", "minimum": 1, "maximum": 127 }
        }
      }
    },
    "melody": {
      "type": "array",
      "minItems": 4,
      "items": {
        "type": "object",
        "required": ["pitch", "start_beat", "duration_beats", "velocity"],
        "properties": {
          "pitch": { "type": "integer", "minimum": 0, "maximum": 127 },
          "start_beat": { "type": "number", "minimum": 0 },
          "duration_beats": { "type": "number", "minimum": 0.25 },
          "velocity": { "type": "integer", "minimum": 1, "maximum": 127 }
        }
      }
    }
  }
}
```

**Design decisions (PRD open questions resolved):**
- Chords use **Roman numerals** relative to key (compact, genre-agnostic).
- Drums use **event list** with beat positions (simpler for LLM than 16×N grid).
- Melody uses **MIDI pitch numbers** (unambiguous for L2 validation).

### 8.2 Session Domain Model (In-Memory)

```python
@dataclass
class Session:
    session_id: UUID
    created_at: datetime
    messages: list[ChatMessage]          # role, content, timestamp
    generations: list[GenerationRecord]

@dataclass
class GenerationRecord:
    generation_id: UUID
    user_message: str
    controls: Controls
    spec: dict                           # validated MusicSpec
    midi_bytes: bytes
    metadata: GenerationMetadata
    created_at: datetime
```

### 8.3 Golden Prompt Record

File: `eval/golden/prompts.v1.yaml`

```yaml
version: "1.0.0"
prompts:
  - id: gp-001
    prompt: "sad lo-fi beat with minimal drums"
    controls: { tempo_bpm: 80, key: "Am", genre: "lo-fi", mood: "melancholic" }
    expected_constraints:
      tempo_range: [70, 90]
      key: "Am"
      min_melody_notes: 4
      min_drum_hits: 1
    reference_notes: "Should feel sparse, minor key"
```

### 8.4 Indexes / Constraints

No persistent DB in MVP. In-memory maps:

| Map | Key | Value |
|-----|-----|-------|
| `sessions` | `session_id` | `Session` |
| `midi_blobs` | `generation_id` | `bytes` |

Validation constraints enforced at domain layer (L2): BPM range, pitch 0–127, valid key regex, non-empty arrays.

---

## 9. Integration Points

### 9.1 Ollama

| Setting | Value |
|---------|-------|
| URL | `http://ollama:11434` (Compose) / `http://localhost:11434` (local) |
| Model | `llama3:8b` (default pull) |
| Endpoint | `POST /api/generate` with `format: json` |
| Timeout | 25s (NFR-001) |
| Temperature | 0.3 (generation), 0.0 (judge) |

**Minimum hardware:** 16GB RAM, ~6GB disk for model.
**Recommended:** Apple M1+ / 8-core CPU, 16GB+ RAM.
**Optional:** `llama3:70b` documented but not default (requires 48GB+ RAM).

### 9.2 OpenAI (Optional Fallback)

| Env Var | Purpose |
|---------|---------|
| `USE_OPENAI` | `true` to enable |
| `OPENAI_API_KEY` | API key (never in repo) |
| `OPENAI_MODEL` | Default `gpt-4o-mini` |

Same JSON schema contract; provider selected via factory.

### 9.3 Docker Compose Services

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    volumes: [ollama_data:/root/.ollama]
    ports: ["11434:11434"]
  backend:
    build: ./backend
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      LLM_MODEL: llama3:8b
    depends_on: [ollama]
    ports: ["8000:8000"]
  frontend:
    build: ./frontend
    ports: ["5173:80"]
    depends_on: [backend]
```

### 9.4 CI (GitHub Actions)

| Workflow | Trigger | Eval Mode |
|----------|---------|-------------|
| `pr-eval.yml` | Pull request | `eval-quick` — mock LLM, 5 prompts, L1–L3 blocking |
| `nightly-eval.yml` | Cron 02:00 UTC | Full 20+ prompts with Ollama, all 4 layers |

---

## 10. Security & Compliance

| Requirement | Implementation |
|-------------|----------------|
| NFR-007 No secrets in repo | `.env.example` only; keys via env |
| NFR-008 Input sanitization | `message` max 2000 chars; strip control chars; no HTML rendering |
| NFR-009 OSS default | Ollama path fully functional without external APIs |
| No auth (MVP) | Single-user local; no PII collected |
| Audit | Structured logs with `request_id`, no chat content in prod logs (configurable debug) |

No GDPR-sensitive PII in MVP. Session data ephemeral.

---

## 11. Observability

### Logging (structlog JSON)

```json
{
  "event": "generation_complete",
  "request_id": "req-uuid",
  "session_id": "sess-uuid",
  "generation_id": "gen-uuid",
  "provider": "ollama",
  "model": "llama3:8b",
  "latency_ms": 12450,
  "eval_schema_ok": true
}
```

### Metrics (Prometheus-compatible `/metrics` — P1)

| Metric | Type | Description |
|--------|------|-------------|
| `generation_latency_seconds` | histogram | End-to-end |
| `llm_latency_seconds` | histogram | LLM call only |
| `generation_errors_total` | counter | By error code |
| `ollama_up` | gauge | Health probe result |

### Health Checks

- `GET /health` — API + Ollama reachability
- Docker `HEALTHCHECK` on backend and ollama services

### Tracing

OpenTelemetry deferred post-MVP; `request_id` correlation sufficient for MVP.

---

## 12. Error Handling & Resilience

| Failure Scenario | Acceptable Behaviour |
|------------------|---------------------|
| Ollama sidecar down | 503 with actionable message; UI retry button (NFR-010) |
| LLM returns invalid JSON | Auto-retry up to 2× with repair prompt; then 422 user error |
| LLM timeout (>25s) | 504; suggest shorter prompt or check hardware |
| MIDI generation error | 500; log spec payload; user sees generic failure |
| Session not found | 404 |
| Browser audio autoplay blocked | UI shows "Click Play to hear preview" (no autoplay) |

**Multi-turn context:** Last **6 turns** (3 user + 3 assistant) plus summary of last `MusicSpec` sent to LLM. Token budget ~4096 tokens input.

**JSON repair prompt:** On parse failure, send: "Your previous response was invalid JSON. Return ONLY valid JSON matching schema version 1.0."

---

## 13. Deployment

### Local Development

```bash
docker compose up --build          # Full stack
make dev-backend                   # FastAPI hot reload
make dev-frontend                  # Vite dev server
make eval-quick                    # Fast eval subset
```

### Directory Layout (post Story 1)

```
music-producer/
├── backend/
│   ├── src/
│   ├── tests/
│   ├── schemas/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── eval/
│   ├── golden/
│   ├── reports/
│   └── run.py
├── docker-compose.yml
├── Makefile
├── docs/
└── LICENSE.md
```

### Environments

| Env | Purpose | LLM |
|-----|---------|-----|
| local | Developer machine | Ollama sidecar |
| CI PR | Gate merges | Mock LLM fixtures |
| CI nightly | Quality baseline | Ollama or cached responses |

---

## 14. Assumptions & Open Questions

### Assumptions (validated by engineering)

| ID | Assumption |
|----|------------|
| AS-1 | `llama3:8b` achieves ≥90% schema pass with repair retries |
| AS-2 | In-memory sessions sufficient for MVP (no persistence) |
| AS-3 | 4/4 time signature covers ≥90% of golden prompts |
| AS-4 | Tone.js works in Chrome/Firefox/Safari latest (desktop) |
| AS-5 | Mock LLM fixtures sufficient for PR CI gating |
| AS-6 | Roman numeral chord mapping covers major/minor keys |

### Resolved Open Questions (PRD §16)

| # | Decision |
|---|----------|
| 1 | React + Vite + TypeScript |
| 2 | Schema defined in §8.1 |
| 3 | Default `llama3:8b`; 70b optional |
| 4 | Same Ollama instance, judge prompt at temperature 0; cache judge in CI |
| 5 | Mock on PR; full Ollama nightly |
| 6 | Sliding window 6 turns + last spec summary |
| 7 | Tone.js + @tonejs/midi |
| 8 | Fixed enums + "other" with custom text |
| 9 | 2 auto-retries then user error |
| 10 | GPT-4o-mini default fallback; eval parity via same schema |

---

## 15. Risks & Technical Debt

| Risk | Impact | Mitigation |
|------|--------|------------|
| Llama 3 JSON quality | High | Repair retries; golden eval gate |
| Mechanical MIDI | Medium | MVP expectations; iterate post-launch |
| In-memory session loss | Low | Document; persistence P2 |
| CI Ollama weight | Medium | Mock on PR; nightly full run |
| No WAV export | Low | P2 stretch (FR-019) |

**Accepted debt:** No auth, no persistence, no SSE in MVP (polling OK), Prometheus metrics P1.

---

## Review Summary

Self-review performed immediately after draft. Initial High findings addressed in spec revisions above.

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| R1 | Drum/chord timing ambiguity — LLM could emit beats beyond bar count | **High** | Added `bars` limit (max 8), L3 checks that events fall within `bars × beats_per_bar` |
| R2 | CI full Ollama eval would block PRs (>30 min) | **High** | Split CI: mock LLM + 5 prompts on PR; nightly full eval |
| R3 | Mockups showed waveform but no waveform API exists | **Med** | Marked waveform as placeholder UI; no backend scope |
| R4 | Roman numeral → MIDI mapping complexity understated | **Med** | `MidiGenerator` owns deterministic mapping table; unit tests required per key |
| R5 | Session memory unbounded growth | **Med** | Cap generations per session at 20; cap messages at 50 |
| R6 | Autoplay policy not addressed | **Med** | Added explicit user-gesture Play button behaviour |
| R7 | OpenAI eval parity unclear | **Low** | Same schema + shared eval pipeline; provider field in report |
| R8 | No CORS config for Vite dev | **Low** | Backend allows `localhost:5173` in dev CORS middleware |

**Verdict:** ✅ **APPROVED** — No unresolved High severity findings after revision. Spec ready for execution planning.
