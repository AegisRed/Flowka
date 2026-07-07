import asyncio
import json
import os
import signal
from dataclasses import dataclass

from aiokafka import AIOKafkaConsumer


@dataclass(frozen=True)
class Settings:
    bootstrap_servers: str
    group_id: str
    topics: list[str]
    processing_delay_seconds: float


def load_settings() -> Settings:
    topics = [
        topic.strip()
        for topic in os.getenv("FLOWKA_TOPICS", "orders.created").split(",")
        if topic.strip()
    ]
    return Settings(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092"),
        group_id=os.getenv("FLOWKA_GROUP_ID", "analytics-service"),
        topics=topics,
        processing_delay_seconds=float(os.getenv("FLOWKA_PROCESSING_DELAY_SECONDS", "0.05")),
    )


async def run() -> None:
    settings = load_settings()
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    consumer = AIOKafkaConsumer(
        *settings.topics,
        bootstrap_servers=settings.bootstrap_servers,
        group_id=settings.group_id,
        client_id=f"flowka-demo-consumer-{settings.group_id}",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )
    await consumer.start()
    try:
        async for message in consumer:
            if stop.is_set():
                break
            await asyncio.sleep(settings.processing_delay_seconds)
            print(
                json.dumps(
                    {
                        "group": settings.group_id,
                        "topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                        "event": message.value.get("event"),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            await consumer.commit()
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run())

