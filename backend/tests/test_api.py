import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_dashboard_returns_demo_snapshot() -> None:
    settings = Settings(use_demo_data=True, database_url="")
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overview"]["cluster_name"] == "Local Demo"
    assert payload["overview"]["topic_count"] >= 4
    assert payload["topics"][0]["name"] == "orders.created"
    assert payload["flow"]["nodes"]


def test_message_search_filters_payloads() -> None:
    settings = Settings(use_demo_data=True, database_url="")
    with TestClient(create_app(settings)) as client:
        response = client.get(
            "/api/topics/payments.completed/messages",
            params={"search": "payment"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all(message["topic"] == "payments.completed" for message in payload)


def test_health_allows_database_to_be_disabled() -> None:
    settings = Settings(use_demo_data=True, database_url="")
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_history_empty_without_database() -> None:
    settings = Settings(use_demo_data=True, database_url="")
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/metrics/history")

    assert response.status_code == 200
    assert response.json() == []


def test_metrics_history_persists_with_sqlite(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'api-metrics.db'}"
    settings = Settings(
        use_demo_data=True,
        database_url=database_url,
        metrics_persist_interval_seconds=0.05,
    )
    with TestClient(create_app(settings)) as client:
        # let the background sampler persist at least one point
        deadline = time.time() + 5
        payload: list[dict[str, object]] = []
        while time.time() < deadline:
            payload = client.get("/api/metrics/history").json()
            if payload:
                break
            time.sleep(0.1)

    assert payload, "expected the background sampler to persist metric samples"
    assert {"timestamp", "lag", "messages_per_second"} <= payload[0].keys()
