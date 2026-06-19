# Eval Framework

4-layer evaluation: L1 schema, L2 constraints (+ golden expected_constraints), L3 structure, L4 LLM judge.

- `golden/prompts.v1.yaml` — Versioned golden prompt dataset
- `mock/` — Per-prompt JSON fixtures (`gp-NNN.json`) aligned with `expected_constraints`
- `reports/` — Generated eval reports (gitignored)
- `run.py` — CLI entry point (`python -m eval.run`)

Mock mode (`EVAL_MOCK_LLM=true` or `--mock`) loads cached specs from `mock/` instead of calling Ollama/OpenAI.
