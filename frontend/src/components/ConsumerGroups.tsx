import { Gauge } from "lucide-react";

import { compactNumber, statusLabel, statusTone } from "../lib/status";
import type { ConsumerGroupSummary } from "../types";

interface ConsumerGroupsProps {
  groups: ConsumerGroupSummary[];
}

export function ConsumerGroups({ groups }: ConsumerGroupsProps) {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.055] shadow-panel">
      <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3">
        <span className="rounded-md border border-amber-300/20 bg-amber-300/10 p-2 text-amber-100">
          <Gauge aria-hidden="true" className="h-4 w-4" />
        </span>
        <div>
          <h2 className="text-base font-semibold text-white">Consumer Groups</h2>
          <p className="text-sm text-slate-400">Lag, offsets and processing pressure</p>
        </div>
      </div>
      <div className="divide-y divide-white/10">
        {groups.map((group) => (
          <article className="px-4 py-3" key={group.group_id}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate font-medium text-white">{group.group_id}</h3>
                <p className="mt-1 text-sm text-slate-400">
                  {compactNumber(group.current_offset)} / {compactNumber(group.end_offset)} offsets
                </p>
              </div>
              <span className={`shrink-0 rounded-md border px-2 py-1 text-xs ${statusTone(group.status)}`}>
                {statusLabel(group.status)}
              </span>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
              <div className="rounded-md border border-white/10 bg-black/20 px-3 py-2">
                <p className="text-slate-500">Lag</p>
                <p className="font-semibold text-amber-100">{compactNumber(group.lag)}</p>
              </div>
              <div className="rounded-md border border-white/10 bg-black/20 px-3 py-2">
                <p className="text-slate-500">Rate</p>
                <p className="font-semibold text-teal-100">{group.messages_per_second.toFixed(1)}/s</p>
              </div>
              <div className="rounded-md border border-white/10 bg-black/20 px-3 py-2">
                <p className="text-slate-500">Parts</p>
                <p className="font-semibold text-sky-100">{group.partitions.length}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
