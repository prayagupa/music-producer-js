# E2E Test Results — STORY-14

Results from automated API integration tests (`backend/tests/test_integration.py`) run against the FastAPI app with mock LLM responses. These verify the full session → generate → MIDI download pipeline without simulated user acceptance.

**Run date:** 2026-06-19  
**Command:** `cd backend && .venv/bin/python -m pytest tests/test_integration.py -v`

| Test | Endpoint / Flow | Result | Verified |
|------|-----------------|--------|----------|
| `test_should_run_full_pipeline_when_mock_llm_returns_valid_spec` | Use case: session → generate → MIDI bytes | Pass | Valid spec parsed, MIDI generated, metadata populated |
| `test_should_create_session_and_generate_via_api` | POST `/api/v1/sessions` → POST `/api/v1/sessions/{id}/generate` → GET `/api/v1/midi/{id}` | Pass | 200 responses, `generation_id` returned, `audio/midi` content-type |
| `test_should_limit_json_repair_retries_to_two` | Use case: invalid JSON → repair retries capped at 2 | Pass | LLM called at most 3 times (1 initial + 2 repairs) |

**Summary:** 3/3 integration tests passed. API E2E pipeline (session creation, music generation, MIDI retrieval) and JSON repair budget verified programmatically.
