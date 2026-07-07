# Flowka Architecture

Flowka is a Kafka observability MVP built around a realtime dashboard and a demo Kafka environment.

## Runtime Components

- `frontend`: React, TypeScript, React Flow, Recharts and Tailwind dashboard.
- `backend`: FastAPI API exposing REST endpoints and `/ws/realtime`.
- `redpanda`: Kafka-compatible broker used for local demos.
- `postgres`: Durable metrics storage. A background sampler writes metric samples to the
  `metric_samples` table when `FLOWKA_DATABASE_URL` is configured; this backs
  `GET /api/metrics/history` and is the foundation for historical analytics.
- `demo/producer`: Generates topic traffic for orders, payments and users.
- `demo/consumer`: Creates normal and intentionally slow consumer groups.

## Data Flow

1. Demo producers publish JSON events to Kafka topics.
2. Demo consumers commit offsets at different speeds.
3. The backend probes topic metadata, end offsets and consumer group offsets.
4. A background sampler persists each metric sample to PostgreSQL for durable history.
5. The frontend receives snapshots over WebSocket and falls back to REST polling.
6. Flow Graph renders Producer -> Topic -> Consumer relationships and highlights lag.

The original overview document uses `StreamLens` in a few places. This scaffold keeps the repository and product name as `Flowka`.

