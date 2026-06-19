# Music Producer App

AI-assisted music composition for creators. Chat with a local LLM to generate MIDI tracks (chords, drums, melody).

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, hexagonal architecture |
| Frontend | React 18, TypeScript, Vite |
| LLM | Ollama `llama3:8b` (default); OpenAI GPT-4o-mini optional |
| MIDI | pretty_midi, Roman numeral chord mapping |
| Playback | Tone.js + @tonejs/midi |
| Eval | 4-layer framework with golden dataset |

## Quick Start

**Requirements:** Docker, 16GB RAM recommended for Ollama.

```bash
cp .env.example .env
docker compose up --build
```

First run pulls the Ollama model (~4.7GB):

```bash
docker compose exec ollama ollama pull llama3:8b
```

Open http://localhost:5173 — chat, set controls, generate, preview, and download MIDI.

### Local Development

```bash
make dev-backend    # FastAPI on :8000
make dev-frontend   # Vite on :5173
make test           # Backend pytest
make eval-quick     # Fast eval (mock LLM in CI)
```

## Architecture

```
┌─────────────┐     REST      ┌──────────────┐     Ollama API    ┌─────────┐
│ React SPA   │ ────────────► │ FastAPI      │ ────────────────► │ llama3  │
│ Chat/Controls│ ◄─────────── │ Hexagonal    │                   │  :8b    │
│ MIDI Preview│   MIDI bytes  │ Backend      │                   └─────────┘
└─────────────┘               └──────────────┘
                                     │
                              MusicSpec → MIDI
                              (3 tracks)
```

See [docs/001/SPEC.md](docs/001/SPEC.md) for full design.

## CI

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `pr-eval.yml` | Pull request | `eval-quick` with mock LLM; blocks if schema < 90% or constraints < 85% |
| `nightly-eval.yml` | Daily 02:00 UTC | Full golden dataset eval |

Judge score is advisory on PRs (warn only). Eval reports uploaded as CI artifacts.

## Environment Variables

See [.env.example](.env.example). No API keys required for default Ollama path.

## Eval

```bash
make eval-quick     # 5 golden prompts, mock LLM for CI
make eval           # Full 20+ prompt dataset
EVAL_MOCK_LLM=true make eval-quick   # Without Ollama
```

## Known Limitations (MVP)

- MIDI output only (no WAV export)
- In-memory sessions (lost on restart)
- No authentication
- Single-user local deployment

## License

See [LICENSE.md](LICENSE.md).
