# Product Requirements Document (PRD)

## 1. Overview

| Field | Value |
|-------|-------|
| **Product Name** | Music Producer App |
| **Feature ID** | 001 |
| **Author** | PM Agent |
| **Date** | 2026-06-19 |
| **Version** | 1.0 |
| **Status** | Draft |

---

## 2. Problem Statement

Independent music creators, hobbyists, and small-studio producers want to explore musical ideas quickly without deep music theory expertise or expensive DAW workflows. Today, the repository contains a legacy Angular chatbot with an Express/WebSocket backend that uses hard-coded pattern matching ("Aria" bot) — it cannot generate music and does not use an LLM.

Creators need a conversational tool that turns natural-language intent (mood, genre, tempo, key) into playable musical output they can iterate on. The product must run locally with open-source models (no API keys required by default), include a quality evaluation framework, and replace the entire legacy stack with a purpose-built architecture.

**For whom:** Music creators who want AI-assisted composition starting from chat, with structured controls for musical parameters.

---

## 3. Goals & Success Metrics

| Goal | Metric | Target |
|------|--------|--------|
| Replace legacy stack | Legacy files removed; new stack deployable via Docker Compose | 100% legacy code deleted in Story 1 |
| Generate usable MIDI | Golden-prompt pass rate (schema + musical constraints) | ≥ 90% on golden dataset |
| Creative adherence | LLM-as-judge score on golden prompts | ≥ 4.0 / 5.0 average |
| Local-first OSS | App runs with Ollama + Llama 3, no API keys | Default path works out of the box |
| Creator iteration speed | Time from prompt to playable MIDI preview | ≤ 30 seconds (P95) on local dev hardware |
| Eval in CI | Automated eval suite runs on every PR | 100% of PRs run eval checks |
| User satisfaction (MVP) | Creator can complete end-to-end flow without docs | 3/3 internal test users succeed unaided |

---

## 4. User Personas

### Persona 1: Indie Creator "Alex"
- **Profile:** Bedroom producer, basic DAW experience, limited music theory
- **Needs:** Quick chord progressions and drum patterns from mood descriptions; preview before exporting
- **Pain points:** Staring at blank piano roll; translating "sad lo-fi beat" into notes

### Persona 2: Content Creator "Jordan"
- **Profile:** YouTuber/podcaster needing background loops
- **Needs:** Fast iteration on tempo, key, and genre; repeatable results for similar prompts
- **Pain points:** Licensing stock music; matching mood to content theme

### Persona 3: Developer-Producer "Sam"
- **Profile:** Engineer who self-hosts tools; cares about OSS and eval transparency
- **Needs:** Local LLM, no vendor lock-in, inspectable outputs (JSON/MIDI), CI-evaluated quality
- **Pain points:** Proprietary APIs, black-box generation, no regression testing for creative outputs

---

## 5. Functional Requirements

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-001 | Chat UI for natural-language music requests | P0 | Replaces legacy Angular chat; modern web stack |
| FR-002 | Structured controls: tempo (BPM), key, genre, mood | P0 | Controls augment chat; sent with each generation request |
| FR-003 | LLM generates structured music spec (JSON) from prompt + controls | P0 | Schema-defined output; not free-form text only |
| FR-004 | Backend converts music spec to MIDI (chords, drums, melody) | P0 | Primary output format for MVP |
| FR-005 | In-browser MIDI preview/playback | P0 | Web Audio / MIDI.js or equivalent |
| FR-006 | Download generated MIDI file | P0 | `.mid` export |
| FR-007 | Ollama + Llama 3 as default LLM provider | P0 | No API keys required |
| FR-008 | Optional OpenAI fallback via environment flag | P1 | `OPENAI_API_KEY` + feature flag; off by default |
| FR-009 | Conversation history within session | P1 | Multi-turn refinement ("make it darker", "add hi-hats") |
| FR-010 | Display generation metadata (BPM, key, genre, model used) | P1 | Transparency for creators |
| FR-011 | Error messages for invalid prompts or LLM failures | P0 | Actionable user-facing errors |
| FR-012 | Golden prompt dataset (versioned, in repo) | P0 | Foundation for eval framework |
| FR-013 | Automated eval: JSON schema validation | P0 | Every generation must parse and validate |
| FR-014 | Automated eval: musical constraint checks | P0 | Valid key, BPM range, time signature, note ranges |
| FR-015 | Automated eval: LLM-as-judge for creative adherence | P0 | Scores prompt-to-output alignment |
| FR-016 | Eval CLI / script runnable locally and in CI | P0 | `make eval` or equivalent |
| FR-017 | Docker Compose: app + Ollama sidecar | P0 | Single-command local dev |
| FR-018 | Delete all legacy Angular/Express/WebSocket code | P0 | First implementation story |
| FR-019 | WAV/audio export | P2 | Stretch goal; MIDI sufficient for MVP |
| FR-020 | User accounts / persistence | P2 | Session-only for MVP |

---

## 6. Non-Functional Requirements

### Performance
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | LLM inference latency (local Llama 3) | P95 ≤ 25s for music spec generation |
| NFR-002 | MIDI synthesis latency | P95 ≤ 2s after spec received |
| NFR-003 | Chat UI responsiveness | Input acknowledgment ≤ 200ms |
| NFR-004 | End-to-end prompt-to-playback | P95 ≤ 30s on recommended dev hardware (16GB RAM, Apple M1 / equivalent) |

### Scalability
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-005 | Concurrent users (MVP) | 1–5 local dev users; no multi-tenant requirement |
| NFR-006 | Golden dataset size | ≥ 20 prompts at launch; extensible to 100+ |

### Security
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-007 | No secrets in repo | API keys via env vars only |
| NFR-008 | Input sanitization | Chat input length limits; no arbitrary code execution |
| NFR-009 | OSS default | App fully functional without external paid APIs |

### Availability
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-010 | Graceful Ollama unavailability | Clear error + retry guidance if sidecar down |
| NFR-011 | Offline-capable (local) | Full flow works without internet once images pulled |

### Observability
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-012 | Structured logging | Request ID, model, latency, eval pass/fail |
| NFR-013 | Eval reports | JSON/HTML summary artifact per CI run |

### OSS Constraint
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-014 | Default LLM | Ollama + Llama 3 (or Llama 3.x); fully open weights |
| NFR-015 | License compatibility | All dependencies compatible with project OSS license |
| NFR-016 | No required proprietary services | OpenAI optional fallback only |

---

## 7. LLM Strategy (Open Source First)

### Default Path: Ollama + Llama 3 (Local)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Chat UI    │────▶│  FastAPI     │────▶│  Ollama         │
│  + Controls │     │  Backend     │     │  (Llama 3)      │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │  Music Spec  │────▶│  MIDI Generator │
                    │  (JSON)      │     │  + Preview      │
                    └──────────────┘     └─────────────────┘
```

**Rationale:** Local inference eliminates API costs and keys, aligns with developer-producer persona, and enables reproducible eval runs in CI (with mocked or lightweight model for speed where appropriate).

### Prompt Architecture
1. **System prompt:** Role as music producer assistant; output must conform to JSON schema
2. **User context:** Chat message + structured controls (tempo, key, genre, mood)
3. **Output:** Structured music specification (not raw MIDI from LLM — backend handles MIDI conversion)

### Optional Fallback: OpenAI
- Enabled via `USE_OPENAI=true` + `OPENAI_API_KEY`
- Same JSON schema contract; provider abstracted behind interface
- Used for comparison benchmarking in eval, not required for MVP

### Model Selection Criteria
| Criterion | Weight |
|-----------|--------|
| JSON/schema adherence | High |
| Music theory vocabulary | High |
| Local inference speed | Medium |
| Context window | Medium |

---

## 8. Evaluation Requirements

### 8.1 Eval Layers

| Layer | Check | Pass Criteria |
|-------|-------|---------------|
| L1: Schema | JSON schema validation | 100% parseable, all required fields present |
| L2: Musical constraints | Key in valid set; BPM 40–240; notes within MIDI range 0–127; valid time signatures | 100% constraint compliance |
| L3: Structural | Non-empty chord progression; drum pattern has ≥1 hit; melody has ≥4 notes | Per golden prompt expectations |
| L4: LLM-as-judge | Creative adherence to prompt + controls | Score ≥ 4.0/5.0 per prompt (configurable threshold) |

### 8.2 Golden Prompt Dataset

- **Location:** `eval/golden/` (versioned in repo)
- **Format:** YAML or JSON with fields: `id`, `prompt`, `controls` (tempo, key, genre, mood), `expected_constraints`, optional `reference_notes`
- **Initial size:** ≥ 20 diverse prompts covering genres (lo-fi, pop, jazz, electronic), moods (happy, melancholic, energetic), and edge cases (minimal prompt, conflicting mood/genre)
- **Versioning:** Dataset version tagged in eval reports; breaking changes bump version

### 8.3 Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| `schema_pass_rate` | % outputs passing JSON schema | ≥ 95% |
| `constraint_pass_rate` | % passing musical constraint checks | ≥ 90% |
| `judge_score_mean` | Mean LLM-as-judge adherence score | ≥ 4.0/5.0 |
| `judge_score_p10` | 10th percentile judge score | ≥ 3.0/5.0 |
| `latency_p95_ms` | 95th percentile end-to-end latency | ≤ 30000ms |

### 8.4 CI Integration

- Eval suite runs on every PR via GitHub Actions (or equivalent)
- PR blocked if `schema_pass_rate < 90%` or `constraint_pass_rate < 85%`
- Judge score thresholds advisory in MVP (warn, not block); blocking threshold added after baseline established
- Eval uses deterministic seed where possible; LLM-as-judge may use same Ollama instance or cached responses for CI speed
- Eval report uploaded as CI artifact

### 8.5 Local Eval

```bash
# Expected developer workflow
make eval          # Run full golden dataset
make eval-quick    # Run subset (5 prompts) for fast iteration
```

---

## 9. User Stories

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|----|---------|--------------|------------|---------------------|
| US-001 | Creator | Describe a beat in chat ("sad lo-fi at 80 BPM") | I get a matching MIDI preview | Chat sends prompt; MIDI plays in browser within 30s; metadata shows BPM ≈ 80 |
| US-002 | Creator | Set tempo, key, genre, and mood via controls | The LLM respects my constraints | Controls visible in UI; generated spec reflects control values |
| US-003 | Creator | Preview generated music in the browser | I can evaluate before downloading | Play/pause works; MIDI audible |
| US-004 | Creator | Download the MIDI file | I can import into my DAW | `.mid` file downloads; opens in standard DAW |
| US-005 | Creator | Refine output via follow-up chat | I can iterate without starting over | Follow-up prompt modifies prior generation context |
| US-006 | Developer | Run the app locally with Docker Compose | I don't need manual service setup | `docker compose up` starts app + Ollama; health check passes |
| US-007 | Developer | Run eval suite locally | I can validate changes before PR | `make eval` produces report with pass/fail per prompt |
| US-008 | Developer | Use Ollama without API keys | I can develop offline | Fresh clone + Docker Compose works without `.env` secrets |
| US-009 | Developer | Optionally enable OpenAI fallback | I can compare model quality | Setting env flag switches provider; same API contract |
| US-010 | Maintainer | Delete legacy code in first story | No confusion between old and new systems | No Angular, Express, WebSocket, or pattern-matching bot files remain |

---

## 10. Scope & Boundaries

### In Scope (MVP)
- Fresh FastAPI backend + modern web chat frontend
- Chat UI with structured musical controls
- Ollama + Llama 3 local LLM integration
- JSON music spec → MIDI generation (chords, drums, melody)
- In-browser MIDI preview and download
- Golden prompt dataset + 3-layer automated eval (schema, constraints, LLM-judge)
- Docker Compose local deployment (app + Ollama sidecar)
- CI eval integration
- Complete deletion of legacy Angular/Express/WebSocket codebase

### Out of Scope (MVP)
- WAV/audio rendering and export (P2 stretch)
- User accounts, auth, cloud persistence
- Multi-track DAW-style editing
- Real-time collaborative sessions
- Mobile-native apps
- Production cloud deployment (K8s, scaling)
- Fine-tuning or training custom models
- Copyright/licensing detection for generated content
- Integration with external DAWs (Ableton Link, VST)

### Future Work (Post-MVP)
- Audio synthesis (WAV/MP3 export via FluidSynth or similar)
- Stem separation / individual track export
- Prompt templates and saved presets
- Model comparison dashboard (Ollama vs OpenAI vs others)
- Expanded golden dataset with community contributions
- GPU-optimized deployment guides
- Streaming LLM responses in chat UI

---

## 11. Migration Plan (Delete Legacy Code)

### Current Legacy Stack (to be removed)

| Component | Path / Technology |
|-----------|-------------------|
| Angular frontend | `app/ts/`, `app/index.html`, `app/css/` |
| Webpack/TypeScript build | `webpack.config.js`, `tsconfig.json`, `typings.json`, `tslint.json` |
| Express + WebSocket server | `server.js` |
| Pattern-matching bot ("Aria") | Intent matchers in `server.js` |
| Legacy static assets | `public/` (JS, CSS from old build) |
| Legacy tests | `test/`, `karma.conf.js`, `test.bundle.js` |
| Legacy npm tooling | `package.json` (Node/Angular dependencies) |

### Migration Strategy

**Story 1 (P0 — Fresh Start):** Delete all legacy files listed above before adding new code. Retain:
- `LICENSE.md`
- `.gitignore` (updated for Python/Node as needed)
- `docs/` (including this PRD and `initial-thought.md`)
- `README.md` (rewritten for new stack)

**Story 2+:** Scaffold new architecture:
- `backend/` — FastAPI application
- `frontend/` — Modern web chat UI
- `eval/` — Golden dataset and eval scripts
- `docker-compose.yml` — App + Ollama sidecar
- `Makefile` — Dev and eval commands

### Rollback
Not applicable — greenfield replacement. Git history preserves legacy code if needed.

---

## 12. Assumptions

| # | Assumption |
|---|------------|
| A1 | **Music output:** MVP delivers MIDI (chord progressions, drum patterns, melody); WAV/audio is a stretch goal (P2) |
| A2 | **Creator workflow:** Chat UI combined with structured controls (tempo, key, genre, mood) |
| A3 | **OSS LLM:** Ollama + Llama 3 locally by default; no API keys required; optional OpenAI fallback via env flag |
| A4 | **Deployment:** Local dev first via Docker Compose with Ollama as sidecar |
| A5 | **Eval scope:** Golden prompt dataset + automated checks (JSON schema, musical constraints) + LLM-as-judge for creative adherence |
| A6 | **Fresh start:** All legacy files deleted in first implementation story |
| A7 | **Frontend:** Modern web chat UI with MIDI preview/playback |
| A8 | **Backend:** Python FastAPI (preferred for audio/MIDI libraries and eval tooling) |
| A9 | **Hardware:** Target dev machine has ≥ 16GB RAM for local Llama 3 inference |
| A10 | **Session scope:** No persistent storage in MVP; conversation state is in-memory per session |
| A11 | **Single-user local:** No multi-tenant or auth requirements for MVP |

---

## 13. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Llama 3 JSON adherence poor | High | Medium | Strict schema prompting; retry with repair prompt; optional OpenAI for comparison |
| Local inference too slow | Medium | Medium | Document hardware requirements; eval quick mode; consider smaller model variant |
| MIDI output sounds mechanical | Medium | High | Set expectations (MVP = structural, not production-ready); iterate on generation rules |
| LLM-as-judge inconsistency | Medium | Medium | Multiple judge runs; temperature 0; cache judge responses in CI |
| Ollama sidecar complexity in CI | Medium | Medium | Mock LLM responses for CI schema/constraint checks; full eval nightly |
| Scope creep to audio/WAV | Medium | Medium | Explicit P2; MIDI-only gate for MVP release |
| Legacy deletion breaks something unknown | Low | Low | Legacy is self-contained; no external consumers documented |

---

## 14. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Ollama | Runtime | Sidecar container; pulls Llama 3 model on first run |
| Llama 3 (via Ollama) | Model | Open-weight; ~4GB+ disk |
| Python 3.11+ | Runtime | FastAPI backend |
| Docker & Docker Compose | Dev tooling | Local deployment |
| MIDI library (e.g., `mido`, `pretty_midi`) | Python package | MIDI generation |
| JSON Schema validator | Python package | Eval L1 |
| Frontend MIDI playback library | JS package | In-browser preview |
| GitHub Actions (or CI) | Infrastructure | Eval on PR |

---

## 15. Timeline & Milestones

| Milestone | Deliverable | Target |
|-----------|-------------|--------|
| M1: Fresh Start | Legacy code deleted; repo scaffold (backend, frontend, eval, Docker) | Week 1 |
| M2: Core Loop | Chat → LLM → JSON spec → MIDI → preview works end-to-end | Week 2–3 |
| M3: Eval Framework | Golden dataset (20+ prompts); schema + constraint + judge eval; CI integration | Week 3–4 |
| M4: MVP Polish | Structured controls, download, error handling, README, Docker Compose docs | Week 4–5 |
| M5: Stretch (P2) | WAV export (if time permits) | Post-MVP |

*Timeline assumes 1–2 developers, part-time. Adjust in spec phase based on team capacity.*

---

## 16. Open Questions for Spec Phase

1. **Frontend framework:** React, Vue, Svelte, or vanilla TS? Spec should align with team preference and MIDI library ecosystem.
2. **Music spec JSON schema:** Exact fields for chords (roman numerals vs absolute notes?), drum pattern format (grid vs event list?), melody representation. Spec must define canonical schema.
3. **Llama 3 variant:** 8B vs 70B — tradeoff between quality and local hardware. Spec should document minimum and recommended specs.
4. **LLM-as-judge model:** Same Llama 3 instance, separate judge prompt, or dedicated smaller model? Cost/latency vs consistency tradeoff.
5. **CI eval strategy:** Full Ollama in CI (slow, heavy) vs mocked LLM responses for schema/constraint + nightly full eval. Spec should propose CI architecture.
6. **Multi-turn context:** How many prior turns sent to LLM? Full session or sliding window? Token budget management.
7. **MIDI playback library:** Tone.js, Web MIDI API, or other? Browser compatibility requirements.
8. **Genre/mood taxonomy:** Fixed enum vs free text? Controls UI design depends on this.
9. **Error recovery:** If JSON parse fails, auto-retry count and user-facing behavior?
10. **OpenAI fallback scope:** Same model family (GPT-4o) or configurable? Eval parity requirements between providers?

---

## 17. Traceability Matrix

| Problem | Goal | Requirement | User Story |
|---------|------|-------------|------------|
| Legacy bot can't make music | Replace stack | FR-018, FR-001–006 | US-010, US-001–004 |
| Creators need parameter control | Structured workflow | FR-002 | US-002 |
| No local OSS LLM path | OSS-first | FR-007, NFR-014–016 | US-006, US-008 |
| No quality regression testing | Eval framework | FR-012–016 | US-007 |
| Black-box creative outputs | Transparency + eval | FR-010, Eval L4 | US-001 |
| Can't preview before export | MIDI playback | FR-005, FR-006 | US-003, US-004 |

---

## Handoff

PRD complete. Next step: invoke the **Spec Agent** (`/spec`) to run the full design pipeline (Software Design Specification, self-review, execution plan), or `/spec-design` to create the specification step by step.
