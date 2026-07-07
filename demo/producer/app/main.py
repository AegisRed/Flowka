import asyncio
import json
import os
import random
import signal
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic


@dataclass(frozen=True)
class Settings:
    bootstrap_servers: str
    topic: str
    kind: str
    rate_per_second: float
    partitions: int
    replication_factor: int


def load_settings() -> Settings:
    return Settings(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092"),
        topic=os.getenv("FLOWKA_TOPIC", "orders.created"),
        kind=os.getenv("FLOWKA_PRODUCER_KIND", "orders"),
        rate_per_second=float(os.getenv("FLOWKA_RATE_PER_SECOND", "10")),
        partitions=int(os.getenv("FLOWKA_TOPIC_PARTITIONS", "3")),
        replication_factor=int(os.getenv("FLOWKA_TOPIC_REPLICATION_FACTOR", "1")),
    )


async def ensure_topic(settings: Settings) -> None:
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.bootstrap_servers)
    await admin.start()
    try:
        await admin.create_topics(
            [
                NewTopic(
                    name=settings.topic,
                    num_partitions=settings.partitions,
                    replication_factor=settings.replication_factor,
                )
            ],
            validate_only=False,
        )
    except Exception:
        pass
    finally:
        await admin.close()


def build_event(kind: str) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    if kind == "payments":
        amount = random.randint(30, 900)
        return {
            "event": "payment_completed",
            "payment_id": str(uuid.uuid4()),
            "amount": amount,
            "currency": "USDT",
            "status": "success" if random.random() > 0.07 else "retry",
            "created_at": now,
        }
    if kind == "users":
        return {
            "event": "user_updated",
            "user_id": random.randint(10_000, 99_999),
            "field": random.choice(["tier", "risk_score", "kyc_status"]),
            "created_at": now,
        }
    if kind == "notifications":
        return {
            "event": "notification_sent",
            "notification_id": str(uuid.uuid4()),
            "channel": random.choice(["email", "telegram", "push"]),
            "status": "delivered",
            "created_at": now,
        }
    return {
        "event": "order_created",
        "order_id": str(uuid.uuid4()),
        "amount": random.randint(20, 700),
        "currency": "USDT",
        "created_at": now,
    }


async def run() -> None:
    settings = load_settings()
    await ensure_topic(settings)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.bootstrap_servers,
        client_id=f"flowka-demo-producer-{settings.kind}",
        value_serializer=lambda payload: json.dumps(payload).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8"),
    )
    await producer.start()
    interval = 1 / max(settings.rate_per_second, 0.1)
    try:
        while not stop.is_set():
            event = build_event(settings.kind)
            key = str(event.get("order_id") or event.get("payment_id") or event.get("user_id"))
            await producer.send_and_wait(settings.topic, key=key, value=event)
            await asyncio.sleep(interval)
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run())

