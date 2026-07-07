import { DatabaseZap, RadioTower } from "lucide-react";

import { statusLabel, statusTone } from "../lib/status";
import type { ClusterOverview } from "../types";
import type { RealtimeState } from "../hooks/useRealtime";

interface DashboardHeaderProps {
  overview: ClusterOverview;
  realtimeState: RealtimeState;
}

export function DashboardHeader({ overview, realtimeState }: DashboardHeaderProps) {
  return (
    <header className="flex flex-col gap-4 border-b border-white/10 px-5 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-8">
      <div className="flex min-w-0 items-center gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-teal-300/30 bg-teal-300/10">
          <DatabaseZap aria-hidden="true" className="h-6 w-6 text-teal-100" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">Flowka</p>
          <h1 className="truncate text-2xl font-semibold text-white">{overview.cluster_name}</h1>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <span className={`rounded-md border px-3 py-2 text-sm font-medium ${statusTone(overview.status)}`}>
          {statusLabel(overview.status)}
        </span>
        <span className="inline-flex items-center gap-2 rounded-md border border-sky-300/20 bg-sky-300/10 px-3 py-2 text-sm font-medium text-sky-100">
          <RadioTower aria-hidden="true" className="h-4 w-4" />
          {realtimeState}
        </span>
      </div>
    </header>
  );
}

