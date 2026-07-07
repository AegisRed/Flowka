# Flowka

Flowka is an open-source Kafka observability MVP: realtime cluster overview, topics, consumer lag, message viewer and a Producer -> Topic -> Consumer flow graph.

## Stack

- Backend: Python 3.12, FastAPI, aiokafka, SQLAlchemy, PostgreSQL
- Frontend: React, TypeScript, React Flow, TailwindCSS, Recharts
- Infra: Docker Compose, Redpanda Kafka, PostgreSQL, demo producers and consumers
- Quality: pytest, ruff, mypy, Vitest, Testing Library, ESLint, GitHub Actions

## Run Locally

Animated installer (builds images, pulls dependencies and waits for health with a
braille progress animation):

```bash
python scripts/flowka_up.py    # or: make up
```

Stop everything with `python scripts/flowka_up.py --down` (or `make stop`).

Plain Docker Compose works too:

```bash
docker compose up --build
```

Open:

- Dashboard: http://localhost:8080
- API docs: http://localhost:8000/docs
- Kafka broker from host: `localhost:19092`
- Optional Redpanda Console: `docker compose --profile tools up console`

The demo starts producers for `orders.created`, `payments.completed`, `user.updated`
and `notification.sent`. It also starts normal consumers (`billing-service`,
`analytics-service`, `notification-service`) and a `slow-consumer` so the dashboard
can show growing lag.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

For backend-only work without Kafka, keep `FLOWKA_USE_DEMO_DATA=true`. The API will serve deterministic telemetry and the UI remains functional.

## Checks

```bash
cd backend && ruff check . && mypy app tests && pytest
cd frontend && npm ci && npm run lint && npm run typecheck && npm test && npm run build
docker compose config
```

## API Surface

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/cluster`
- `GET /api/topics`
- `GET /api/consumer-groups`
- `GET /api/flow`
- `GET /api/metrics/history`
- `GET /api/topics/{topic}/messages`
- `WS /ws/realtime`

When `FLOWKA_DATABASE_URL` is set, a background sampler persists metric samples to
PostgreSQL so realtime chart history survives restarts and `GET /api/metrics/history`
serves durable data (the foundation for historical analytics). Without a database the
API still runs and the endpoint returns an empty history.

## Repository Layout

```text
backend/          FastAPI service and unit tests
frontend/         React dashboard and unit tests
demo/producer/    Kafka demo producers
demo/consumer/    Kafka demo consumers
docs/             Project notes
.github/          CI/CD workflows
docker-compose.yml
```
