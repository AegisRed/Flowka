import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MetricPoint } from "../types";

interface MetricsChartProps {
  metrics: MetricPoint[];
}

export function MetricsChart({ metrics }: MetricsChartProps) {
  const data = metrics.map((metric) => ({
    time: new Date(metric.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }),
    mps: metric.messages_per_second,
    lag: metric.lag,
    throughput: metric.throughput_kbps,
  }));

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.055] p-4 shadow-panel">
      <div className="mb-4">
        <h2 className="text-base font-semibold text-white">Realtime Metrics</h2>
        <p className="text-sm text-slate-400">Messages, lag and throughput sampled every few seconds</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer height="100%" width="100%">
          <AreaChart data={data} margin={{ bottom: 0, left: 0, right: 8, top: 10 }}>
            <defs>
              <linearGradient id="messages" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.45} />
                <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="lag" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.36} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#22313d" strokeDasharray="4 4" />
            <XAxis dataKey="time" minTickGap={24} stroke="#8a9bad" tickLine={false} />
            <YAxis stroke="#8a9bad" tickLine={false} width={42} />
            <Tooltip
              contentStyle={{
                background: "#0d1b24",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: "#f8fafc",
              }}
            />
            <Area dataKey="mps" name="msg/s" stroke="#2dd4bf" fill="url(#messages)" strokeWidth={2} />
            <Area dataKey="lag" name="lag" stroke="#f59e0b" fill="url(#lag)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

