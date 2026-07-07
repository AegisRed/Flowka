from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.models.schemas import MetricPoint
from app.services.metrics_repository import MetricsRepository


def _metric(offset_seconds: int, lag: int) -> MetricPoint:
    return MetricPoint(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=offset_seconds),
        messages_per_second=10.0 + offset_seconds,
        lag=lag,
        throughput_kbps=42.0,
        active_consumers=3,
    )


async def test_repository_is_noop_without_engine() -> None:
    repository = MetricsRepository(engine=None)
    assert repository.enabled is False
    await repository.create_schema()
    await repository.record(_metric(0, 5))
    assert await repository.history() == []


async def test_repository_persists_and_reads_history(tmp_path: Path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'metrics.db'}")
    repository = MetricsRepository(engine=engine)
    try:
        await repository.create_schema()
        for index in range(3):
            await repository.record(_metric(index, lag=index * 100))

        history = await repository.history(limit=10)
    finally:
        await engine.dispose()

    assert [point.lag for point in history] == [0, 100, 200]
    # ascending chronological order for charts
    assert history[0].timestamp < history[-1].timestamp


async def test_history_limit_returns_most_recent(tmp_path: Path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'metrics.db'}")
    repository = MetricsRepository(engine=engine)
    try:
        await repository.create_schema()
        for index in range(5):
            await repository.record(_metric(index, lag=index))

        history = await repository.history(limit=2)
    finally:
        await engine.dispose()

    assert [point.lag for point in history] == [3, 4]


@pytest.mark.parametrize("limit", [1, 240])
async def test_history_empty_table(tmp_path: Path, limit: int) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'metrics.db'}")
    repository = MetricsRepository(engine=engine)
    try:
        await repository.create_schema()
        history = await repository.history(limit=limit)
    finally:
        await engine.dispose()

    assert history == []
