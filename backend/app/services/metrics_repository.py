import logging

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    Table,
    insert,
    select,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.schemas import MetricPoint

logger = logging.getLogger(__name__)

metadata = MetaData()

metric_samples = Table(
    "metric_samples",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", DateTime(timezone=True), nullable=False, index=True),
    Column("messages_per_second", Float, nullable=False),
    Column("lag", BigInteger, nullable=False),
    Column("throughput_kbps", Float, nullable=False),
    Column("active_consumers", Integer, nullable=False),
)


class MetricsRepository:
    """Durable storage for realtime metric samples.

    Degrades to a no-op when no database engine is configured so the API keeps
    working in demo / backend-only mode.
    """

    def __init__(self, engine: AsyncEngine | None) -> None:
        self._engine = engine

    @property
    def enabled(self) -> bool:
        return self._engine is not None

    async def create_schema(self) -> None:
        if self._engine is None:
            return
        async with self._engine.begin() as connection:
            await connection.run_sync(metadata.create_all)

    async def record(self, metric: MetricPoint) -> None:
        if self._engine is None:
            return
        statement = insert(metric_samples).values(
            timestamp=metric.timestamp,
            messages_per_second=metric.messages_per_second,
            lag=metric.lag,
            throughput_kbps=metric.throughput_kbps,
            active_consumers=metric.active_consumers,
        )
        async with self._engine.begin() as connection:
            await connection.execute(statement)

    async def history(self, limit: int = 240) -> list[MetricPoint]:
        if self._engine is None:
            return []
        statement = (
            select(
                metric_samples.c.timestamp,
                metric_samples.c.messages_per_second,
                metric_samples.c.lag,
                metric_samples.c.throughput_kbps,
                metric_samples.c.active_consumers,
            )
            .order_by(metric_samples.c.timestamp.desc())
            .limit(limit)
        )
        async with self._engine.connect() as connection:
            rows = (await connection.execute(statement)).all()
        points = [
            MetricPoint(
                timestamp=row.timestamp,
                messages_per_second=row.messages_per_second,
                lag=row.lag,
                throughput_kbps=row.throughput_kbps,
                active_consumers=row.active_consumers,
            )
            for row in rows
        ]
        points.reverse()  # return chronological ascending order for charts
        return points
