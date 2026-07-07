from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Flowka"
    environment: str = "local"
    use_demo_data: bool = Field(default=True, description="Use deterministic telemetry fallback.")
    cors_origins: list[str] | str = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    database_url: str = ""
    kafka_bootstrap_servers: str = "redpanda:9092"
    kafka_client_id: str = "flowka-api"
    kafka_group_probe_timeout_ms: int = 1500
    metrics_interval_seconds: float = 1.5
    metrics_persist_interval_seconds: float = 5.0
    metrics_history_limit: int = 240
    cluster_name: str = "Local Demo"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FLOWKA_",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
