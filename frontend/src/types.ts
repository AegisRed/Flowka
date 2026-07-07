export type ConnectionStatus = "healthy" | "warning" | "critical" | "down";

export interface ClusterOverview {
  cluster_name: string;
  topic_count: number;
  partition_count: number;
  consumer_group_count: number;
  broker_count: number;
  status: ConnectionStatus;
  updated_at: string;
}

export interface TopicSummary {
  name: string;
  partitions: number;
  replication_factor: number;
  message_rate: number;
  bytes_in_per_second: number;
}

export interface ConsumerPartitionLag {
  topic: string;
  partition: number;
  current_offset: number;
  end_offset: number;
  lag: number;
}

export interface ConsumerGroupSummary {
  group_id: string;
  current_offset: number;
  end_offset: number;
  lag: number;
  messages_per_second: number;
  status: ConnectionStatus;
  partitions: ConsumerPartitionLag[];
}

export interface MetricPoint {
  timestamp: string;
  messages_per_second: number;
  lag: number;
  throughput_kbps: number;
  active_consumers: number;
}

export interface TopicMessage {
  topic: string;
  partition: number;
  offset: number;
  key: string | null;
  value: Record<string, unknown> | string;
  timestamp: string;
  headers: Record<string, string>;
}

export interface FlowNode {
  id: string;
  label: string;
  kind: "producer" | "topic" | "consumer";
  status: ConnectionStatus;
  metric: string | null;
  position: { x: number; y: number };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  label: string | null;
  status: ConnectionStatus;
}

export interface FlowGraph {
  nodes: FlowNode[];
  edges: FlowEdge[];
}

export interface DashboardSnapshot {
  overview: ClusterOverview;
  topics: TopicSummary[];
  consumer_groups: ConsumerGroupSummary[];
  metrics: MetricPoint[];
  recent_messages: TopicMessage[];
  flow: FlowGraph;
}

