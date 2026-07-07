import type { DashboardSnapshot, TopicMessage } from "../types";

const apiBase = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function getDashboardSnapshot(): Promise<DashboardSnapshot> {
  return request<DashboardSnapshot>("/api/dashboard");
}

export function getTopicMessages(
  topic: string,
  search: string,
  limit = 50,
): Promise<TopicMessage[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (search.trim()) {
    params.set("search", search.trim());
  }
  return request<TopicMessage[]>(`/api/topics/${encodeURIComponent(topic)}/messages?${params}`);
}

export function realtimeUrl(): string {
  const configured = import.meta.env.VITE_WS_URL;
  if (configured) {
    return `${configured.replace(/\/$/, "")}/ws/realtime`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/realtime`;
}

