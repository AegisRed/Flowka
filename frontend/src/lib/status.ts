import type { ConnectionStatus } from "../types";

export function statusLabel(status: ConnectionStatus): string {
  const labels: Record<ConnectionStatus, string> = {
    healthy: "Healthy",
    warning: "Warning",
    critical: "Critical",
    down: "Down",
  };
  return labels[status];
}

export function statusTone(status: ConnectionStatus): string {
  const tones: Record<ConnectionStatus, string> = {
    healthy: "text-emerald-200 bg-emerald-500/10 border-emerald-400/30",
    warning: "text-amber-200 bg-amber-500/10 border-amber-300/30",
    critical: "text-rose-200 bg-rose-500/10 border-rose-300/30",
    down: "text-zinc-200 bg-zinc-600/20 border-zinc-400/25",
  };
  return tones[status];
}

export function compactNumber(value: number): string {
  if (value >= 1_000_000) {
    return `${trimCompact(value / 1_000_000)}M`;
  }
  if (value >= 10_000) {
    return `${trimCompact(value / 1_000)}K`;
  }
  return new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(value);
}

function trimCompact(value: number): string {
  return value.toFixed(1).replace(/\.0$/, "");
}
