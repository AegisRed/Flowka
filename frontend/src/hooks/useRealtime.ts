import { useEffect, useRef, useState } from "react";

import { getDashboardSnapshot, realtimeUrl } from "../api/client";
import type { DashboardSnapshot } from "../types";

export type RealtimeState = "connecting" | "live" | "polling" | "offline";

export function useRealtime() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [state, setState] = useState<RealtimeState>("connecting");
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let disposed = false;
    let pollingTimer: number | undefined;

    const poll = async () => {
      try {
        const next = await getDashboardSnapshot();
        if (!disposed) {
          setSnapshot(next);
          setState("polling");
        }
      } catch {
        if (!disposed) {
          setState("offline");
        }
      }
    };

    const startPolling = () => {
      window.clearInterval(pollingTimer);
      void poll();
      pollingTimer = window.setInterval(poll, 2000);
    };

    try {
      const socket = new WebSocket(realtimeUrl());
      socketRef.current = socket;
      socket.onopen = () => {
        if (!disposed) {
          setState("live");
        }
      };
      socket.onmessage = (event: MessageEvent<string>) => {
        if (!disposed) {
          setSnapshot(JSON.parse(event.data) as DashboardSnapshot);
          setState("live");
        }
      };
      socket.onerror = () => {
        socket.close();
      };
      socket.onclose = () => {
        if (!disposed) {
          startPolling();
        }
      };
    } catch {
      startPolling();
    }

    return () => {
      disposed = true;
      window.clearInterval(pollingTimer);
      socketRef.current?.close();
    };
  }, []);

  return { snapshot, state };
}

