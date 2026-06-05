.PHONY: install dev backend frontend

install:
	uv sync
	cd webapp/frontend && npm install

backend:
	uv run uvicorn webapp.backend.main:app --reload --port 8000

frontend:
	cd webapp/frontend && npm run dev

dev:
	@echo "Starting backend (:8000) and frontend (:5173)…"
	@trap 'kill 0' INT TERM EXIT; \
	uv run uvicorn webapp.backend.main:app --reload --port 8000 & \
	(cd webapp/frontend && npm run dev) & \
	wait
