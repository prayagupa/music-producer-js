# Execution Plan — Music Producer App

## 1. Overview

| Field | Value |
|-------|-------|
| **Feature ID** | 001 |
| **Feature Name** | Music Producer App |
| **Date** | 2026-06-19 |
| **Estimated Duration** | 4–5 weeks (1–2 developers, part-time) |
| **Related Spec** | [docs/001/SPEC.md](./SPEC.md) |
| **Related PRD** | [docs/001/PRD.md](./PRD.md) |

This plan decomposes the Music Producer App MVP into ordered epics and stories. Story IDs use the format `STORY-NN`. Each story includes explicit acceptance criteria traceable to PRD requirements.

---

## 2. Epics & Stories

### Epic E1: Fresh Start & Repository Scaffold

---

#### STORY-01 — Delete Legacy Code & Initialize Repo Structure

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 1 day |
| **Dependencies** | None |
| **Status** | todo |
| **PRD Trace** | FR-018, US-010 |

**Description:** Remove all legacy Angular/Express/WebSocket code and scaffold the new monorepo layout. Retain `LICENSE.md`, `.gitignore` (updated), `docs/`, and rewrite `README.md`.

**Delete list:**
- `app/` (Angular TS, HTML, CSS)
- `public/` (legacy static assets)
- `test/` (Karma tests)
- `server.js`
- `webpack.config.js`, `tsconfig.json`, `typings.json`, `tslint.json`
- `karma.conf.js`, `test.bundle.js`
- Legacy `package.json` / `package-lock.json`
- Legacy `Makefile` targets (replace entirely)

**Scaffold:**
```
backend/   frontend/   eval/   docker-compose.yml   Makefile   .env.example
```

**Acceptance Criteria:**
- [ ] No files remain under `app/`, `public/`, legacy `test/`
- [ ] `server.js`, `webpack.config.js`, `karma.conf.js` deleted
- [ ] New directory skeleton exists with placeholder README sections
- [ ] `.gitignore` covers Python (`__pycache__`, `.venv`), Node (`node_modules`, `dist`), eval reports
- [ ] Root `README.md` describes new stack (FastAPI + React + Ollama)
- [ ] `git status` shows only new scaffold + deletions (no orphaned legacy imports)

---

#### STORY-02 — Backend Foundation & Health API

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 2 days |
| **Dependencies** | STORY-01 |
| **Status** | todo |
| **PRD Trace** | FR-011, NFR-012, US-006 |

**Description:** Scaffold FastAPI application with hexagonal folder structure, configuration, structured logging, CORS, and health endpoint with Ollama probe.

**Acceptance Criteria:**
- [ ] `backend/pyproject.toml` with FastAPI, uvicorn, httpx, structlog, pydantic-settings
- [ ] `GET /api/v1/health` returns `{ status, version, checks: { api, ollama } }`
- [ ] Ollama probe hits `OLLAMA_BASE_URL/api/tags` with 2s timeout; reports `up` or `down`
- [ ] Structlog JSON logging with `request_id` middleware
- [ ] CORS allows `http://localhost:5173` in dev
- [ ] `pytest` unit tests for health endpoint (mock Ollama up/down)
- [ ] `make dev-backend` starts uvicorn with hot reload

---

#### STORY-03 — Docker Compose & Dev Tooling

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 1.5 days |
| **Dependencies** | STORY-02 |
| **Status** | todo |
| **PRD Trace** | FR-017, US-006, US-008, NFR-010 |

**Description:** Docker Compose with Ollama sidecar, backend container, and frontend container. Makefile targets for common workflows.

**Acceptance Criteria:**
- [ ] `docker compose up --build` starts `ollama`, `backend`, `frontend`
- [ ] Ollama volume persists model downloads
- [ ] Backend `depends_on` ollama with healthcheck
- [ ] `.env.example` documents all env vars (no secrets)
- [ ] `make up`, `make down`, `make logs` work
- [ ] Fresh clone + `docker compose up` works without API keys
- [ ] README documents hardware requirements (16GB RAM) and first-run model pull
- [ ] Ollama down → health returns `degraded` with actionable message

---

### Epic E2: Music Spec & Generation Core

---

#### STORY-04 — Music Spec JSON Schema & Domain Validation

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 2 days |
| **Dependencies** | STORY-02 |
| **Status** | todo |
| **PRD Trace** | FR-003, FR-013, FR-014 |

**Description:** Implement canonical `music_spec.v1.json` schema and domain validation layer (L1 + L2 checks).

**Acceptance Criteria:**
- [ ] Schema file at `backend/schemas/music_spec.v1.json` matches SPEC §8.1
- [ ] `MusicSpecValidator` validates JSON Schema (L1) and musical constraints (L2)
- [ ] L2 checks: BPM 40–240, pitch 0–127, valid key regex, time signature enum
- [ ] L2 checks: drum/melody/chord events within `bars × beats_per_bar`
- [ ] Unit tests with valid and invalid fixtures (≥10 cases)
- [ ] Schema published for eval and LLM prompt inclusion

---

#### STORY-05 — LLM Provider Abstraction (Ollama + OpenAI)

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 2.5 days |
| **Dependencies** | STORY-04 |
| **Status** | todo |
| **PRD Trace** | FR-003, FR-007, FR-008, US-009 |

**Description:** Port/adapter LLM layer with Ollama default and optional OpenAI fallback. System prompt enforces JSON schema output. JSON repair retry (max 2).

**Acceptance Criteria:**
- [ ] `LlmProviderPort` interface with `generate_spec(prompt, controls, history) -> str`
- [ ] `OllamaLlmProvider` calls `llama3:8b` with `format: json`, temperature 0.3
- [ ] `OpenAiLlmProvider` activated when `USE_OPENAI=true` + `OPENAI_API_KEY` set
- [ ] System prompt includes schema summary and example
- [ ] On JSON parse failure, retry up to 2× with repair prompt
- [ ] Sliding window: last 6 turns + last spec summary in context
- [ ] Unit tests with mocked HTTP responses (valid, invalid, timeout)
- [ ] 504 returned when LLM exceeds 25s timeout

---

#### STORY-06 — MIDI Generation Engine

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 3 days |
| **Dependencies** | STORY-04 |
| **Status** | todo |
| **PRD Trace** | FR-004, NFR-002 |

**Description:** Deterministic `MusicSpec` → MIDI converter using `pretty_midi`. Three tracks: chords, drums, melody.

**Acceptance Criteria:**
- [ ] Roman numeral → chord voicing mapping for all 24 major/minor keys
- [ ] Drum map: kick=36, snare=38, hihat_closed=42, hihat_open=46, clap=39, tom=45
- [ ] Output SMF Type 1 with 3 tracks; tempo from spec meta
- [ ] P95 MIDI generation ≤ 2s (unit test benchmark on golden fixture)
- [ ] Generated `.mid` opens in MuseScore/GarageBand without errors
- [ ] Unit tests per key for Roman numeral mapping (spot check 6 keys)
- [ ] Handles 1–8 bars; 4/4 default

---

#### STORY-07 — Session & Generation API

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 2 days |
| **Dependencies** | STORY-05, STORY-06 |
| **Status** | todo |
| **PRD Trace** | FR-001–004, FR-009, FR-010, FR-011, US-001, US-005 |

**Description:** In-memory session store and generation endpoints wiring the full backend pipeline.

**Acceptance Criteria:**
- [ ] `POST /api/v1/sessions` creates session; returns `session_id`
- [ ] `POST /api/v1/sessions/{id}/generate` runs full pipeline
- [ ] Response includes `metadata`, `spec`, `midi_url`, `assistant_message`
- [ ] `GET /api/v1/midi/{generation_id}` returns `audio/midi` attachment
- [ ] `GET /api/v1/generations/{generation_id}` returns metadata + spec
- [ ] Session stores message history; follow-up prompts include prior context
- [ ] Session caps: 50 messages, 20 generations (per SPEC review R5)
- [ ] Input validation: message max 2000 chars; controls validated against enums
- [ ] Error codes: `INVALID_CONTROLS`, `LLM_OUTPUT_INVALID`, `OLLAMA_UNAVAILABLE`, `GENERATION_TIMEOUT`
- [ ] Integration test: mock LLM → valid spec → MIDI bytes returned

---

### Epic E3: Frontend Experience

---

#### STORY-08 — Frontend Scaffold & Chat UI

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 2 days |
| **Dependencies** | STORY-03, STORY-07 |
| **Status** | todo |
| **PRD Trace** | FR-001, FR-011, NFR-003, US-001 |

**Description:** React + Vite + TypeScript app with chat panel, session management, and generation flow.

**Acceptance Criteria:**
- [ ] Vite + React 18 + TypeScript scaffold in `frontend/`
- [ ] Chat UI: message list, input, send button, loading state
- [ ] Auto-create session on first load; persist `session_id` in sessionStorage
- [ ] Send calls `POST .../generate`; displays assistant response
- [ ] Input acknowledgment ≤ 200ms (optimistic UI + spinner)
- [ ] Error toasts for API failures with retry for 503
- [ ] Responsive layout matching SPEC §7.1 wireframe
- [ ] `make dev-frontend` runs Vite dev server on port 5173

---

#### STORY-09 — Structured Controls Panel

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 1.5 days |
| **Dependencies** | STORY-08 |
| **Status** | todo |
| **PRD Trace** | FR-002, US-002 |

**Description:** UI controls for tempo, key, genre, mood with enum validation and custom text for "other".

**Acceptance Criteria:**
- [ ] Controls panel with BPM slider/input (40–240), key dropdown (24 keys)
- [ ] Genre and mood dropdowns with fixed enums + "other"
- [ ] Custom text field appears when "other" selected (max 50 chars)
- [ ] Controls sent with every generate request
- [ ] Client-side validation mirrors backend; inline error messages
- [ ] Controls state persists in sessionStorage for session duration
- [ ] Generated metadata displayed in METADATA panel (BPM, key, genre, model)

---

#### STORY-10 — MIDI Preview, Playback & Download

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 2 days |
| **Dependencies** | STORY-08, STORY-07 |
| **Status** | todo |
| **PRD Trace** | FR-005, FR-006, US-003, US-004 |

**Description:** In-browser MIDI playback with Tone.js and file download.

**Acceptance Criteria:**
- [ ] Fetch MIDI from `GET /api/v1/midi/{generation_id}`
- [ ] Play/Pause/Stop controls using Tone.js + `@tonejs/midi`
- [ ] No autoplay — user must click Play (browser policy)
- [ ] Download button saves `{generation_id}.mid`
- [ ] Downloaded file imports into at least one DAW (manual test documented)
- [ ] Preview panel shows duration and bar count from metadata
- [ ] Loading state while fetching MIDI bytes

---

### Epic E4: Evaluation Framework

---

#### STORY-11 — Golden Prompt Dataset

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 1.5 days |
| **Dependencies** | STORY-04 |
| **Status** | todo |
| **PRD Trace** | FR-012, NFR-006 |

**Description:** Versioned golden prompt dataset with ≥20 diverse prompts.

**Acceptance Criteria:**
- [ ] `eval/golden/prompts.v1.yaml` with ≥20 prompts
- [ ] Coverage: genres (lo-fi, pop, jazz, electronic, hip-hop, ambient, rock, classical)
- [ ] Coverage: moods (happy, melancholic, energetic, dark, calm, tense, romantic)
- [ ] Edge cases: minimal prompt, conflicting mood/genre, max BPM, min BPM
- [ ] Each prompt has `id`, `prompt`, `controls`, `expected_constraints`
- [ ] Dataset version `1.0.0` tagged; loader validates format
- [ ] `eval-quick` subset defined (5 prompt IDs)

---

#### STORY-12 — Eval CLI (4-Layer Framework)

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 3 days |
| **Dependencies** | STORY-05, STORY-06, STORY-11 |
| **Status** | todo |
| **PRD Trace** | FR-013–016, US-007 |

**Description:** Eval runner implementing L1 (schema), L2 (constraints), L3 (structure), L4 (LLM-as-judge).

**Acceptance Criteria:**
- [ ] `python -m eval.run` executes golden dataset
- [ ] L1: JSON schema validation — 100% parseable target
- [ ] L2: Musical constraint checks per SPEC
- [ ] L3: Structure checks (non-empty chords, ≥1 drum hit, ≥4 melody notes)
- [ ] L4: LLM-as-judge prompt scores 1–5; temperature 0; threshold 4.0
- [ ] Mock LLM mode (`EVAL_MOCK_LLM=true`) for CI with deterministic fixtures
- [ ] JSON report written to `eval/reports/eval-{timestamp}.json`
- [ ] Console summary matches SPEC §7.5 mockup
- [ ] `make eval` (full) and `make eval-quick` (5 prompts) targets
- [ ] Exit code non-zero if schema < 90% or constraints < 85%

---

#### STORY-13 — CI Eval Integration

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimate** | 1.5 days |
| **Dependencies** | STORY-12 |
| **Status** | todo |
| **PRD Trace** | FR-016, NFR-013 |

**Description:** GitHub Actions workflows for PR gating and nightly full eval.

**Acceptance Criteria:**
- [ ] `.github/workflows/pr-eval.yml` runs on PR: `eval-quick` with mock LLM
- [ ] PR blocked if `schema_pass_rate < 90%` or `constraint_pass_rate < 85%`
- [ ] Judge score advisory (warn only) in MVP
- [ ] `.github/workflows/nightly-eval.yml` runs full dataset (Ollama or cached)
- [ ] Eval report uploaded as CI artifact (JSON)
- [ ] Workflow README section documents CI architecture

---

### Epic E5: Polish & Release Readiness

---

#### STORY-14 — Error Handling & Multi-Turn Polish

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimate** | 1.5 days |
| **Dependencies** | STORY-07, STORY-08 |
| **Status** | todo |
| **PRD Trace** | FR-009, FR-011, US-005, NFR-010 |

**Description:** Harden error paths, multi-turn refinement UX, and Ollama degraded-state handling.

**Acceptance Criteria:**
- [ ] All API error codes have user-friendly messages in UI
- [ ] Ollama down shows banner with `docker compose up ollama` guidance + Retry
- [ ] Follow-up prompts ("make it darker", "add hi-hats") modify prior generation context
- [ ] Assistant messages summarize what changed vs prior generation
- [ ] LLM invalid JSON after retries shows actionable error (suggest simpler prompt)
- [ ] Manual test: 3 internal users complete E2E flow unaided (document results)

---

#### STORY-15 — Documentation & MVP Release Checklist

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimate** | 1 day |
| **Dependencies** | STORY-03, STORY-10, STORY-13 |
| **Status** | todo |
| **PRD Trace** | All US-* |

**Description:** Final README, API docs, and MVP release verification.

**Acceptance Criteria:**
- [ ] README: quick start, architecture diagram, env vars, eval commands, hardware reqs
- [ ] OpenAPI docs available at `/docs` (FastAPI auto-generated)
- [ ] MVP checklist verified: chat → generate → preview → download
- [ ] All P0 FR requirements traced to implemented stories
- [ ] Known limitations documented (no WAV, no auth, in-memory sessions)

---

### Epic E6: Stretch (P2 — Post-MVP)

---

#### STORY-16 — WAV Audio Export (Stretch)

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Estimate** | 3 days |
| **Dependencies** | STORY-06 |
| **Status** | todo |
| **PRD Trace** | FR-019 |

**Description:** Optional FluidSynth-based WAV rendering from MIDI. **Not required for MVP release.**

**Acceptance Criteria:**
- [ ] `GET /api/v1/audio/{generation_id}` returns WAV
- [ ] FluidSynth or similar OSS synthesizer in backend container
- [ ] Download WAV button in frontend
- [ ] Document increased container size and latency

---

## 3. Execution Phases

### Phase 1: Foundation (Week 1)

| Order | Story | Rationale |
|-------|-------|-----------|
| 1 | STORY-01 | Clean slate; eliminates legacy confusion |
| 2 | STORY-02 | Backend skeleton + health API |
| 3 | STORY-03 | Docker Compose enables integrated dev for all subsequent stories |

**Exit criteria:** `docker compose up` starts stack; health endpoint responds.

---

### Phase 2: Core Features (Weeks 2–3)

| Order | Story | Rationale |
|-------|-------|-----------|
| 4 | STORY-04 | Schema is contract for LLM, MIDI, and eval |
| 5 | STORY-05 | LLM provider — critical path |
| 6 | STORY-06 | MIDI engine — can develop in parallel with STORY-05 after STORY-04 |
| 7 | STORY-07 | Wire backend pipeline end-to-end |
| 8 | STORY-08 | Frontend chat — unblocks UI stories |
| 9 | STORY-09 | Controls panel |
| 10 | STORY-10 | Preview + download — completes creator loop |

**Exit criteria:** User can chat → generate → preview → download MIDI via browser.

---

### Phase 3: Integration & Hardening (Weeks 3–5)

| Order | Story | Rationale |
|-------|-------|-----------|
| 11 | STORY-11 | Golden dataset required before eval |
| 12 | STORY-12 | 4-layer eval framework |
| 13 | STORY-13 | CI gates protect quality |
| 14 | STORY-14 | Error handling + multi-turn polish |
| 15 | STORY-15 | Documentation + MVP sign-off |
| — | STORY-16 | P2 stretch; only if ahead of schedule |

**Exit criteria:** `make eval` passes; CI green; 3/3 internal users succeed unaided.

---

## 4. Definition of Done

Per story:
- [ ] Code compiles/builds without errors
- [ ] Unit tests pass for new backend logic
- [ ] Acceptance criteria above verified
- [ ] No secrets committed
- [ ] Structured logging on new API paths

Per MVP release:
- [ ] All P0 stories (STORY-01 through STORY-13) complete
- [ ] Backend unit test coverage ≥ 80% on domain + application layers
- [ ] Integration test covers mock LLM → MIDI pipeline
- [ ] `make eval-quick` passes locally
- [ ] CI PR workflow green
- [ ] README documents full quick-start flow
- [ ] No critical security vulnerabilities in dependency scan

---

## 5. Risks & Blockers

| Risk | Stories Affected | Mitigation |
|------|------------------|------------|
| Llama 3 JSON adherence poor | STORY-05, STORY-12 | Repair retries; mock fixtures; OpenAI comparison |
| Roman numeral mapping bugs | STORY-06 | Per-key unit tests; golden eval L3 |
| Ollama slow on CI nightly | STORY-13 | Cache responses; run nightly not per-PR |
| Tone.js browser quirks | STORY-10 | Manual test Chrome/Firefox/Safari |
| Scope creep to WAV | STORY-16 | Gate behind P2; MIDI-only MVP |

**Blockers:**
- None identified. STORY-01 must complete before any implementation to avoid legacy conflicts.

---

## 6. Assumptions

| ID | Assumption |
|----|------------|
| EA-1 | 1–2 developers available part-time for 4–5 weeks |
| EA-2 | Dev hardware meets 16GB RAM minimum for Ollama |
| EA-3 | GitHub Actions available for CI |
| EA-4 | No external consumers depend on legacy API |
| EA-5 | MVP release criteria = MIDI only; STORY-16 optional |

---

## Story Index

| ID | Title | Priority | Estimate | Phase |
|----|-------|----------|----------|-------|
| STORY-01 | Delete Legacy Code & Initialize Repo Structure | P0 | 1d | 1 |
| STORY-02 | Backend Foundation & Health API | P0 | 2d | 1 |
| STORY-03 | Docker Compose & Dev Tooling | P0 | 1.5d | 1 |
| STORY-04 | Music Spec JSON Schema & Domain Validation | P0 | 2d | 2 |
| STORY-05 | LLM Provider Abstraction (Ollama + OpenAI) | P0 | 2.5d | 2 |
| STORY-06 | MIDI Generation Engine | P0 | 3d | 2 |
| STORY-07 | Session & Generation API | P0 | 2d | 2 |
| STORY-08 | Frontend Scaffold & Chat UI | P0 | 2d | 2 |
| STORY-09 | Structured Controls Panel | P0 | 1.5d | 2 |
| STORY-10 | MIDI Preview, Playback & Download | P0 | 2d | 2 |
| STORY-11 | Golden Prompt Dataset | P0 | 1.5d | 3 |
| STORY-12 | Eval CLI (4-Layer Framework) | P0 | 3d | 3 |
| STORY-13 | CI Eval Integration | P0 | 1.5d | 3 |
| STORY-14 | Error Handling & Multi-Turn Polish | P1 | 1.5d | 3 |
| STORY-15 | Documentation & MVP Release Checklist | P1 | 1d | 3 |
| STORY-16 | WAV Audio Export (Stretch) | P2 | 3d | Post-MVP |

**Total MVP estimate (STORY-01 – STORY-15):** ~27 days → ~4–5 weeks part-time

---

## Handoff

**Next step:** Invoke `/story-impl-plan` for **STORY-01** (Delete Legacy Code & Initialize Repo Structure) to create its detailed implementation design.
