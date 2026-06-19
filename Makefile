.PHONY: install dev-backend dev-frontend test eval eval-quick up down logs

BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install: install-backend install-frontend

install-backend:
	cd $(BACKEND_DIR) && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

install-frontend:
	cd $(FRONTEND_DIR) && npm install

dev-backend:
	cd $(BACKEND_DIR) && .venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --app-dir src

dev-frontend:
	cd $(FRONTEND_DIR) && npm run dev

test:
	cd $(BACKEND_DIR) && .venv/bin/python -m pytest tests/ -v

eval:
	PYTHONPATH=backend/src:. $(PYTHON) -m eval.run

eval-quick:
	PYTHONPATH=backend/src:. EVAL_MOCK_LLM=true $(PYTHON) -m eval.run --quick --mock

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f
