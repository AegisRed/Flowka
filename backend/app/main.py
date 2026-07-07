import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.services.database import Database
from app.services.metrics_repository import MetricsRepository
from app.services.telemetry import TelemetryService, create_telemetry

logger = logging.getLogger(__name__)


async def _sample_metrics(
    telemetry: TelemetryService,
    metrics: MetricsRepository,
    interval_seconds: float,
) -> None:
    """Periodically persist the latest metric sample so history survives restarts."""
    while True:
        try:
            snapshot = await telemetry.snapshot()
            if snapshot.metrics:
                await metrics.record(snapshot.metrics[-1])
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Metrics sampler iteration failed: %s", exc)
        await asyncio.sleep(interval_seconds)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        database = Database(settings.database_url)
        metrics = MetricsRepository(database.engine)
        telemetry = create_telemetry(settings)
        app.state.database = database
        app.state.metrics = metrics
        app.state.telemetry = telemetry

        await metrics.create_schema()
        sampler: asyncio.Task[None] | None = None
        if metrics.enabled:
            sampler = asyncio.create_task(
                _sample_metrics(telemetry, metrics, settings.metrics_persist_interval_seconds)
            )
        try:
            yield
        finally:
            if sampler is not None:
                sampler.cancel()
                with suppress(asyncio.CancelledError):
                    await sampler
            await telemetry.close()
            await database.close()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Realtime Kafka observability API for Flowka.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "service": "flowka-api",
            "docs": "/docs",
            "health": "/api/health",
            "dashboard": "/api/dashboard",
        }

    @app.websocket("/ws/realtime")
    async def realtime(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                snapshot = await websocket.app.state.telemetry.snapshot()
                await websocket.send_json(snapshot.model_dump(mode="json"))
                await asyncio.sleep(settings.metrics_interval_seconds)
        except WebSocketDisconnect:
            return

    app.include_router(router)
    return app


app = create_app()
