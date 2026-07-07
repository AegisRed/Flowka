.PHONY: up stop dev down backend-test frontend-test lint docker-config

up:
	python scripts/flowka_up.py

stop:
	python scripts/flowka_up.py --down

dev:
	docker compose up --build

down:
	docker compose down --remove-orphans

backend-test:
	cd backend && python -m pytest

frontend-test:
	cd frontend && npm test

lint:
	cd backend && ruff check . && mypy app tests
	cd frontend && npm run lint && npm run typecheck

docker-config:
	docker compose config

