# MVP Release Checklist — Feature 001

## Verified Flow

- [x] Chat → generate → preview → download MIDI
- [x] Structured controls (BPM, key, genre, mood)
- [x] Multi-turn session with context
- [x] Health endpoint with Ollama probe
- [x] Eval framework (L1–L4) with golden dataset
- [x] CI PR gate with mock LLM

## P0 FR Traceability

| Requirement | Story |
|-------------|-------|
| FR-001 Chat generation | STORY-07, STORY-08 |
| FR-002 Structured controls | STORY-09 |
| FR-003 LLM → MusicSpec | STORY-04, STORY-05 |
| FR-004 MIDI generation | STORY-06 |
| FR-005 Preview | STORY-10 |
| FR-006 Download | STORY-10 |
| FR-007 Ollama default | STORY-05 |
| FR-008 OpenAI fallback | STORY-05 |
| FR-009 Multi-turn | STORY-07, STORY-14 |
| FR-010 Session API | STORY-07 |
| FR-011 Health | STORY-02 |
| FR-012 Golden dataset | STORY-11 |
| FR-013–016 Eval layers | STORY-12 |
| FR-017 Docker Compose | STORY-03 |
| FR-018 Legacy removal | STORY-01 |

## Known Limitations

- No WAV export (STORY-16 P2)
- No authentication
- In-memory sessions (lost on restart)
- Waveform in UI is placeholder only

## OpenAPI

FastAPI auto-docs: http://localhost:8000/docs
