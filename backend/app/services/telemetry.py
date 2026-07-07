import asyncio
import json
import logging
import math
import time
from collections import deque
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from app.core.config import Settings
from app.models.schemas import (
    ClusterOverview,
    ConnectionStatus,
    ConsumerGroupSummary,
    ConsumerPartitionLag,
    DashboardSnapshot,
    FlowEdge,
    FlowGraph,
    FlowNode,
    MetricPoint,
    TopicMessage,
    TopicSummary,
)

logger = logging.getLogger(__name__)


class TelemetryService(Protocol):
    async def snapshot(self) -> DashboardSnapshot:
        ...

    async def messages(
        self,
        topic: str,
        limit: int = 25,
        search: str | None = None,
    ) -> list[TopicMessage]:
        ...

    async def close(self) -> None:
        ...


def create_telemetry(settings: Settings) -> TelemetryService:
    if settings.use_demo_data:
        return DemoTelemetry(settings.cluster_name)
    return LiveKafkaTelemetry(settings)


class DemoTelemetry:
    def __init__(self, cluster_name: str = "Local Demo") -> None:
        self._cluster_name = cluster_name
        self._started_at = time.monotonic()
        self._metric_history: deque[MetricPoint] = deque(maxlen=48)

    async def close(self) -> None:
        return None

    async def snapshot(self) -> DashboardSnapshot:
        now = datetime.now(UTC)
        elapsed = max(time.monotonic() - self._started_at, 1)
        topics = self._topics(elapsed)
        groups = self._consumer_groups(elapsed)
        cluster_status: ConnectionStatus = (
            "warning" if any(group.status == "warning" for group in groups) else "healthy"
        )
        metric = MetricPoint(
            timestamp=now,
            messages_per_second=round(sum(topic.message_rate for topic in topics), 2),
            lag=sum(group.lag for group in groups),
            throughput_kbps=round(34 + (math.sin(elapsed / 5) + 1) * 18, 2),
            active_consumers=sum(1 for group in groups if group.status != "down"),
        )
        self._metric_history.append(metric)

        return DashboardSnapshot(
            overview=ClusterOverview(
                cluster_name=self._cluster_name,
                topic_count=len(topics),
                partition_count=sum(topic.partitions for topic in topics),
                consumer_group_count=len(groups),
                broker_count=1,
                status=cluster_status,
                updated_at=now,
            ),
            topics=topics,
            consumer_groups=groups,
            metrics=list(self._metric_history),
            recent_messages=await self.messages(topic="orders.created", limit=8),
            flow=self._flow(groups),
        )

    async def messages(
        self,
        topic: str,
        limit: int = 25,
        search: str | None = None,
    ) -> list[TopicMessage]:
        now = datetime.now(UTC)
        templates = {
            "orders.created": lambda index: {
                "event": "order_created",
                "order_id": 10_000 + index,
                "amount": 90 + (index % 12) * 17,
                "currency": "USDT",
                "source": "order-service",
            },
            "payments.completed": lambda index: {
                "event": "payment_completed",
                "payment_id": 20_000 + index,
                "status": "success" if index % 9 else "retry",
                "amount": 75 + (index % 8) * 21,
                "currency": "USDT",
                "source": "payment-service",
            },
            "user.updated": lambda index: {
                "event": "user_updated",
                "user_id": 30_000 + index,
                "field": "risk_score" if index % 3 else "tier",
                "source": "profile-service",
            },
            "notification.sent": lambda index: {
                "event": "notification_sent",
                "channel": "email" if index % 2 else "telegram",
                "status": "delivered",
                "source": "notification-service",
            },
        }
        factory = templates.get(topic, templates["orders.created"])
        base_offset = int(time.monotonic() * 10)
        messages = [
            TopicMessage(
                topic=topic,
                partition=index % 3,
                offset=base_offset - index,
                key=f"{topic}:{base_offset - index}",
                value=factory(base_offset - index),
                timestamp=now,
            )
            for index in range(limit * 2)
        ]
        if search:
            needle = search.lower()
            messages = [
                message
                for message in messages
                if needle in json.dumps(message.value, ensure_ascii=False).lower()
                or needle in (message.key or "").lower()
            ]
        return messages[:limit]

    def _topics(self, elapsed: float) -> list[TopicSummary]:
        specs = [
            ("orders.created", 3, 1, 10.0),
            ("payments.completed", 3, 1, 5.0),
            ("user.updated", 2, 1, 3.0),
            ("notification.sent", 2, 1, 6.0),
        ]
        return [
            TopicSummary(
                name=name,
                partitions=partitions,
                replication_factor=replication,
                message_rate=round(base + (math.sin(elapsed / (index + 2)) + 1) * 0.8, 2),
                bytes_in_per_second=round((base * 1024) + (index + 1) * 640, 2),
            )
            for index, (name, partitions, replication, base) in enumerate(specs)
        ]

    def _consumer_groups(self, elapsed: float) -> list[ConsumerGroupSummary]:
        slow_lag = int(80 + (math.sin(elapsed / 8) + 1) * 145)
        analytics_lag = int((math.sin(elapsed / 4) + 1) * 12)
        billing_lag = int((math.sin(elapsed / 3) + 1) * 8)
        return [
            self._group("billing-service", "orders.created", billing_lag, 8.7),
            self._group("analytics-service", "orders.created", analytics_lag, 13.2),
            self._group("slow-consumer", "payments.completed", slow_lag, 1.1),
            self._group("notification-service", "notification.sent", 0, 5.5),
        ]

    @staticmethod
    def _group(
        group_id: str,
        topic: str,
        lag: int,
        rate: float,
    ) -> ConsumerGroupSummary:
        end_offset = 125_000
        current_offset = max(end_offset - lag, 0)
        status: ConnectionStatus = "warning" if lag >= 80 else "healthy"
        return ConsumerGroupSummary(
            group_id=group_id,
            current_offset=current_offset,
            end_offset=end_offset,
            lag=lag,
            messages_per_second=rate,
            status=status,
            partitions=[
                ConsumerPartitionLag(
                    topic=topic,
                    partition=partition,
                    current_offset=max(current_offset - partition * 7, 0),
                    end_offset=end_offset + partition * 11,
                    lag=max(lag // 3 + partition * 4, 0),
                )
                for partition in range(3)
            ],
        )

    @staticmethod
    def _flow(groups: list[ConsumerGroupSummary]) -> FlowGraph:
        lag_by_consumer = {group.group_id: group.lag for group in groups}
        return FlowGraph(
            nodes=[
                FlowNode(
                    id="order-service",
                    label="order-service",
                    kind="producer",
                    status="healthy",
                    metric="10 msg/s",
                    position={"x": 0, "y": 70},
                ),
                FlowNode(
                    id="payment-service",
                    label="payment-service",
                    kind="producer",
                    status="healthy",
                    metric="5 msg/s",
                    position={"x": 0, "y": 230},
                ),
                FlowNode(
                    id="orders.created",
                    label="orders.created",
                    kind="topic",
                    status="healthy",
                    metric="3 partitions",
                    position={"x": 310, "y": 70},
                ),
                FlowNode(
                    id="payments.completed",
                    label="payments.completed",
                    kind="topic",
                    status="healthy",
                    metric="3 partitions",
                    position={"x": 310, "y": 230},
                ),
                FlowNode(
                    id="billing-service",
                    label="billing-service",
                    kind="consumer",
                    status="healthy",
                    metric=f"lag {lag_by_consumer.get('billing-service', 0)}",
                    position={"x": 650, "y": 0},
                ),
                FlowNode(
                    id="analytics-service",
                    label="analytics-service",
                    kind="consumer",
                    status="healthy",
                    metric=f"lag {lag_by_consumer.get('analytics-service', 0)}",
                    position={"x": 650, "y": 130},
                ),
                FlowNode(
                    id="slow-consumer",
                    label="slow-consumer",
                    kind="consumer",
                    status="warning",
                    metric=f"lag {lag_by_consumer.get('slow-consumer', 0)}",
                    position={"x": 650, "y": 275},
                ),
            ],
            edges=[
                FlowEdge(id="order-to-orders", source="order-service", target="orders.created"),
                FlowEdge(
                    id="payment-to-payments",
                    source="payment-service",
                    target="payments.completed",
                ),
                FlowEdge(id="orders-to-billing", source="orders.created", target="billing-service"),
                FlowEdge(
                    id="orders-to-analytics",
                    source="orders.created",
                    target="analytics-service",
                ),
                FlowEdge(
                    id="payments-to-slow",
                    source="payments.completed",
                    target="slow-consumer",
                    status="warning",
                    label="lag rising",
                ),
            ],
        )


class LiveKafkaTelemetry:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._admin: Any | None = None
        self._fallback = DemoTelemetry(settings.cluster_name)
        self._previous_offsets: dict[str, int] = {}
        self._previous_group_offsets: dict[str, int] = {}
        self._previous_sample_at = time.monotonic()
        self._metric_history: deque[MetricPoint] = deque(maxlen=48)

    async def close(self) -> None:
        if self._admin is not None:
            await self._admin.close()
            self._admin = None
        await self._fallback.close()

    async def snapshot(self) -> DashboardSnapshot:
        try:
            return await self._snapshot_from_kafka()
        except Exception as exc:
            logger.warning("Falling back to demo telemetry after Kafka probe failed: %s", exc)
            snapshot = await self._fallback.snapshot()
            snapshot.overview.status = "warning"
            return snapshot

    async def messages(
        self,
        topic: str,
        limit: int = 25,
        search: str | None = None,
    ) -> list[TopicMessage]:
        try:
            return await self._messages_from_kafka(topic=topic, limit=limit, search=search)
        except Exception as exc:
            logger.warning("Falling back to demo messages for %s: %s", topic, exc)
            return await self._fallback.messages(topic=topic, limit=limit, search=search)

    async def _ensure_admin(self) -> Any:
        if self._admin is None:
            from aiokafka.admin import AIOKafkaAdminClient

            self._admin = AIOKafkaAdminClient(
                bootstrap_servers=self._settings.kafka_bootstrap_servers,
                client_id=self._settings.kafka_client_id,
                request_timeout_ms=self._settings.kafka_group_probe_timeout_ms,
            )
            await self._admin.start()
        return self._admin

    async def _snapshot_from_kafka(self) -> DashboardSnapshot:
        from aiokafka import AIOKafkaConsumer
        from aiokafka.structs import TopicPartition

        admin = await self._ensure_admin()
        topic_names = sorted(
            name for name in await admin.list_topics() if not str(name).startswith("_")
        )
        descriptions = (
            cast(list[Any], await admin.describe_topics(topic_names)) if topic_names else []
        )
        raw_groups = cast(list[Any], await admin.list_consumer_groups())
        group_ids = [_group_id(group) for group in raw_groups]

        consumer = AIOKafkaConsumer(
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            client_id=f"{self._settings.kafka_client_id}-offset-probe",
            enable_auto_commit=False,
        )
        await consumer.start()
        try:
            topic_summaries: list[TopicSummary] = []
            topic_end_offsets: dict[str, int] = {}
            for description in descriptions:
                name = str(_value(description, "topic", ""))
                partitions = cast(list[Any], _value(description, "partitions", []) or [])
                topic_partitions = [
                    TopicPartition(name, _int_value(partition, "partition"))
                    for partition in partitions
                ]
                end_offsets = (
                    await consumer.end_offsets(topic_partitions) if topic_partitions else {}
                )
                total_end = sum(int(offset) for offset in end_offsets.values())
                topic_end_offsets[name] = total_end
                topic_summaries.append(
                    TopicSummary(
                        name=name,
                        partitions=len(partitions),
                        replication_factor=_replication_factor(partitions),
                        message_rate=0,
                        bytes_in_per_second=0,
                    )
                )

            sample_now = time.monotonic()
            elapsed = max(sample_now - self._previous_sample_at, 0.001)
            topic_summaries = self._with_rates(topic_summaries, topic_end_offsets, elapsed)
            consumer_groups = await self._consumer_groups(
                admin, consumer, group_ids, elapsed
            )
            self._previous_sample_at = sample_now
        finally:
            await _safe_stop(consumer)

        now = datetime.now(UTC)
        total_rate = sum(topic.message_rate for topic in topic_summaries)
        total_lag = sum(group.lag for group in consumer_groups)
        metric = MetricPoint(
            timestamp=now,
            messages_per_second=round(total_rate, 2),
            lag=total_lag,
            throughput_kbps=round(
                sum(topic.bytes_in_per_second for topic in topic_summaries) / 1024,
                2,
            ),
            active_consumers=len(consumer_groups),
        )
        self._metric_history.append(metric)

        return DashboardSnapshot(
            overview=ClusterOverview(
                cluster_name=self._settings.cluster_name,
                topic_count=len(topic_summaries),
                partition_count=sum(topic.partitions for topic in topic_summaries),
                consumer_group_count=len(consumer_groups),
                broker_count=1,
                status="warning" if total_lag > 0 else "healthy",
                updated_at=now,
            ),
            topics=topic_summaries,
            consumer_groups=consumer_groups,
            metrics=list(self._metric_history),
            recent_messages=await self.messages(topic=topic_summaries[0].name, limit=8)
            if topic_summaries
            else [],
            flow=self._flow_from_live(topic_summaries, consumer_groups),
        )

    def _with_rates(
        self,
        topics: list[TopicSummary],
        topic_end_offsets: dict[str, int],
        elapsed: float,
    ) -> list[TopicSummary]:
        enriched: list[TopicSummary] = []
        for topic in topics:
            previous = self._previous_offsets.get(topic.name, topic_end_offsets.get(topic.name, 0))
            current = topic_end_offsets.get(topic.name, 0)
            rate = max((current - previous) / elapsed, 0)
            enriched.append(
                topic.model_copy(
                    update={
                        "message_rate": round(rate, 2),
                        "bytes_in_per_second": round(rate * 512, 2),
                    }
                )
            )
        self._previous_offsets = topic_end_offsets
        return enriched

    async def _consumer_groups(
        self,
        admin: Any,
        consumer: Any,
        group_ids: list[str],
        elapsed: float,
    ) -> list[ConsumerGroupSummary]:
        groups: list[ConsumerGroupSummary] = []
        new_group_offsets: dict[str, int] = {}
        for group_id in group_ids:
            offsets = cast(
                dict[Any, Any],
                await admin.list_consumer_group_offsets(group_id) or {},
            )
            partitions: list[ConsumerPartitionLag] = []
            current_total = 0
            end_total = 0
            if offsets:
                end_offsets = cast(
                    dict[Any, int],
                    await consumer.end_offsets(list(offsets.keys())),
                )
                for topic_partition, metadata in offsets.items():
                    current_offset = max(_int_value(metadata, "offset"), 0)
                    end_offset = max(int(end_offsets.get(topic_partition, current_offset)), 0)
                    lag = max(end_offset - current_offset, 0)
                    current_total += current_offset
                    end_total += end_offset
                    partitions.append(
                        ConsumerPartitionLag(
                            topic=topic_partition.topic,
                            partition=topic_partition.partition,
                            current_offset=current_offset,
                            end_offset=end_offset,
                            lag=lag,
                        )
                    )
            lag_total = max(end_total - current_total, 0)
            status: ConnectionStatus = "warning" if lag_total >= 80 else "healthy"
            previous_consumed = self._previous_group_offsets.get(group_id, current_total)
            consumed_rate = max((current_total - previous_consumed) / elapsed, 0)
            new_group_offsets[group_id] = current_total
            groups.append(
                ConsumerGroupSummary(
                    group_id=group_id,
                    current_offset=current_total,
                    end_offset=end_total,
                    lag=lag_total,
                    messages_per_second=round(consumed_rate, 2),
                    status=status,
                    partitions=partitions,
                )
            )
        self._previous_group_offsets = new_group_offsets
        return groups

    async def _messages_from_kafka(
        self,
        topic: str,
        limit: int,
        search: str | None,
    ) -> list[TopicMessage]:
        from aiokafka import AIOKafkaConsumer
        from aiokafka.structs import TopicPartition

        consumer = AIOKafkaConsumer(
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            client_id=f"{self._settings.kafka_client_id}-message-viewer",
            enable_auto_commit=False,
            auto_offset_reset="latest",
        )
        await consumer.start()
        try:
            # partitions_for_topic is synchronous in aiokafka and returns None
            # until metadata is loaded; force a refresh before giving up.
            partitions = consumer.partitions_for_topic(topic)
            if not partitions:
                await consumer.topics()
                partitions = consumer.partitions_for_topic(topic)
            topic_partitions = [
                TopicPartition(topic, partition) for partition in sorted(partitions or set())
            ]
            if not topic_partitions:
                return []
            consumer.assign(topic_partitions)
            end_offsets = await consumer.end_offsets(topic_partitions)
            for topic_partition in topic_partitions:
                end = int(end_offsets.get(topic_partition, 0))
                consumer.seek(topic_partition, max(end - max(limit, 10), 0))

            records = await consumer.getmany(timeout_ms=750, max_records=limit * 2)
            messages: list[TopicMessage] = []
            for record_batch in records.values():
                for record in record_batch:
                    value = _decode_record_value(record.value)
                    key = record.key.decode("utf-8") if record.key else None
                    message = TopicMessage(
                        topic=record.topic,
                        partition=record.partition,
                        offset=record.offset,
                        key=key,
                        value=value,
                        timestamp=datetime.fromtimestamp(record.timestamp / 1000, tz=UTC),
                    )
                    messages.append(message)
            messages.sort(key=lambda item: item.offset, reverse=True)
            if search:
                needle = search.lower()
                messages = [
                    message
                    for message in messages
                    if needle in json.dumps(message.value, ensure_ascii=False).lower()
                    or needle in (message.key or "").lower()
                ]
            return messages[:limit]
        finally:
            await _safe_stop(consumer)

    @staticmethod
    def _flow_from_live(
        topics: list[TopicSummary],
        groups: list[ConsumerGroupSummary],
    ) -> FlowGraph:
        nodes: list[FlowNode] = []
        edges: list[FlowEdge] = []
        for index, topic in enumerate(topics[:6]):
            topic_node = f"topic:{topic.name}"
            producer_node = f"producer:{topic.name}"
            nodes.append(
                FlowNode(
                    id=producer_node,
                    label=f"{topic.name.split('.')[0]} producer",
                    kind="producer",
                    status="healthy",
                    metric=f"{topic.message_rate:.1f} msg/s",
                    position={"x": 0, "y": index * 115},
                )
            )
            nodes.append(
                FlowNode(
                    id=topic_node,
                    label=topic.name,
                    kind="topic",
                    status="healthy",
                    metric=f"{topic.partitions} partitions",
                    position={"x": 320, "y": index * 115},
                )
            )
            edges.append(
                FlowEdge(
                    id=f"{producer_node}->{topic_node}",
                    source=producer_node,
                    target=topic_node,
                )
            )

        consumer_y = 0
        for group in groups[:8]:
            consumer_node = f"consumer:{group.group_id}"
            nodes.append(
                FlowNode(
                    id=consumer_node,
                    label=group.group_id,
                    kind="consumer",
                    status=group.status,
                    metric=f"lag {group.lag}",
                    position={"x": 670, "y": consumer_y},
                )
            )
            consumer_y += 105
            linked_topics = sorted({partition.topic for partition in group.partitions})
            for linked_topic in linked_topics:
                topic_node = f"topic:{linked_topic}"
                if any(node.id == topic_node for node in nodes):
                    edges.append(
                        FlowEdge(
                            id=f"{topic_node}->{consumer_node}",
                            source=topic_node,
                            target=consumer_node,
                            status=group.status,
                        )
                    )
        return FlowGraph(nodes=nodes, edges=edges)


async def _safe_stop(consumer: Any) -> None:
    """Stop a short-lived probe consumer, swallowing teardown errors.

    aiokafka can surface a ``CancelledError`` (a ``BaseException``) from its own
    coordinator shutdown; that must never turn a successful probe into a 500.
    """
    with suppress(Exception, asyncio.CancelledError):
        await consumer.stop()


def _group_id(group: object) -> str:
    if isinstance(group, tuple):
        return str(group[0])
    return str(_value(group, "group_id", group))


def _replication_factor(partitions: list[Any]) -> int:
    replication = 1
    for partition in partitions:
        replicas = cast(list[Any], _value(partition, "replicas", []) or [])
        replication = max(replication, len(replicas))
    return replication


def _value(item: object, key: str, default: object) -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _int_value(item: object, key: str, default: int = 0) -> int:
    value = _value(item, key, default)
    try:
        return int(cast(Any, value))
    except (TypeError, ValueError):
        return default


def _decode_record_value(value: bytes | None) -> dict[str, object] | str:
    if value is None:
        return ""
    decoded = value.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError:
        return decoded
    if isinstance(parsed, dict):
        return parsed
    return decoded
