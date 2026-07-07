from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ConnectionStatus = Literal["healthy", "warning", "critical", "down"]


class ClusterOverview(BaseModel):
    cluster_name: str
    topic_count: int = Field(ge=0)
    partition_count: int = Field(ge=0)
    consumer_group_count: int = Field(ge=0)
    broker_count: int = Field(ge=0)
    status: ConnectionStatus
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TopicSummary(BaseModel):
    name: str
    partitions: int = Field(ge=0)
    replication_factor: int = Field(ge=0)
    message_rate: float = Field(ge=0)
    bytes_in_per_second: float = Field(ge=0)


class ConsumerPartitionLag(BaseModel):
    topic: str
    partition: int = Field(ge=0)
    current_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    lag: int = Field(ge=0)


class ConsumerGroupSummary(BaseModel):
    group_id: str
    current_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    lag: int = Field(ge=0)
    messages_per_second: float = Field(ge=0)
    status: ConnectionStatus
    partitions: list[ConsumerPartitionLag] = Field(default_factory=list)


class MetricPoint(BaseModel):
    timestamp: datetime
    messages_per_second: float = Field(ge=0)
    lag: int = Field(ge=0)
    throughput_kbps: float = Field(ge=0)
    active_consumers: int = Field(ge=0)


class TopicMessage(BaseModel):
    topic: str
    partition: int = Field(ge=0)
    offset: int = Field(ge=0)
    key: str | None = None
    value: dict[str, object] | str
    timestamp: datetime
    headers: dict[str, str] = Field(default_factory=dict)


class FlowNode(BaseModel):
    id: str
    label: str
    kind: Literal["producer", "topic", "consumer"]
    status: ConnectionStatus
    metric: str | None = None
    position: dict[str, float]


class FlowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None
    status: ConnectionStatus = "healthy"


class FlowGraph(BaseModel):
    nodes: list[FlowNode]
    edges: list[FlowEdge]


class DashboardSnapshot(BaseModel):
    overview: ClusterOverview
    topics: list[TopicSummary]
    consumer_groups: list[ConsumerGroupSummary]
    metrics: list[MetricPoint]
    recent_messages: list[TopicMessage]
    flow: FlowGraph

