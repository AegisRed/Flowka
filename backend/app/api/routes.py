from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.models.schemas import (
    ClusterOverview,
    ConsumerGroupSummary,
    DashboardSnapshot,
    FlowGraph,
    MetricPoint,
    TopicMessage,
    TopicSummary,
)
from app.services.database import Database
from app.services.metrics_repository import MetricsRepository
from app.services.telemetry import TelemetryService

router = APIRouter(prefix="/api", tags=["flowka"])


def get_telemetry(request: Request) -> TelemetryService:
    return request.app.state.telemetry


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_metrics(request: Request) -> MetricsRepository:
    return request.app.state.metrics


DatabaseDep = Annotated[Database, Depends(get_database)]
TelemetryDep = Annotated[TelemetryService, Depends(get_telemetry)]
MetricsDep = Annotated[MetricsRepository, Depends(get_metrics)]
MessageLimit = Annotated[int, Query(ge=1, le=200)]
MessageSearch = Annotated[str | None, Query(min_length=1)]
HistoryLimit = Annotated[int, Query(ge=1, le=2000)]


@router.get("/health", tags=["system"])
async def health(database: DatabaseDep) -> dict[str, object]:
    database_ok = await database.ping()
    return {
        "service": "flowka-api",
        "status": "ok" if database_ok else "degraded",
        "checks": {
            "database": "ok" if database_ok else "unavailable",
        },
    }


@router.get("/dashboard", response_model=DashboardSnapshot)
async def dashboard(telemetry: TelemetryDep) -> DashboardSnapshot:
    return await telemetry.snapshot()


@router.get("/cluster", response_model=ClusterOverview)
async def cluster(telemetry: TelemetryDep) -> ClusterOverview:
    return (await telemetry.snapshot()).overview


@router.get("/topics", response_model=list[TopicSummary])
async def topics(telemetry: TelemetryDep) -> list[TopicSummary]:
    return (await telemetry.snapshot()).topics


@router.get("/consumer-groups", response_model=list[ConsumerGroupSummary])
async def consumer_groups(
    telemetry: TelemetryDep,
) -> list[ConsumerGroupSummary]:
    return (await telemetry.snapshot()).consumer_groups


@router.get("/flow", response_model=FlowGraph)
async def flow(telemetry: TelemetryDep) -> FlowGraph:
    return (await telemetry.snapshot()).flow


@router.get("/metrics/history", response_model=list[MetricPoint])
async def metrics_history(
    metrics: MetricsDep,
    limit: HistoryLimit = 240,
) -> list[MetricPoint]:
    return await metrics.history(limit=limit)


@router.get("/topics/{topic}/messages", response_model=list[TopicMessage])
async def topic_messages(
    topic: str,
    telemetry: TelemetryDep,
    limit: MessageLimit = 25,
    search: MessageSearch = None,
) -> list[TopicMessage]:
    return await telemetry.messages(topic=topic, limit=limit, search=search)
