import { Layers3 } from "lucide-react";

import { compactNumber } from "../lib/status";
import type { TopicSummary } from "../types";

interface TopicExplorerProps {
  topics: TopicSummary[];
  selectedTopic: string;
  onSelectTopic: (topic: string) => void;
}

export function TopicExplorer({ topics, selectedTopic, onSelectTopic }: TopicExplorerProps) {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.055] shadow-panel">
      <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3">
        <span className="rounded-md border border-sky-300/20 bg-sky-300/10 p-2 text-sky-100">
          <Layers3 aria-hidden="true" className="h-4 w-4" />
        </span>
        <div>
          <h2 className="text-base font-semibold text-white">Topics</h2>
          <p className="text-sm text-slate-400">Partitions, replication and message rate</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="text-xs uppercase tracking-[0.12em] text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Topic</th>
              <th className="px-4 py-3 font-medium">Partitions</th>
              <th className="px-4 py-3 font-medium">RF</th>
              <th className="px-4 py-3 font-medium">Rate</th>
              <th className="px-4 py-3 font-medium">Bytes/s</th>
            </tr>
          </thead>
          <tbody>
            {topics.map((topic) => (
              <tr
                className={
                  topic.name === selectedTopic
                    ? "border-t border-teal-300/20 bg-teal-300/10"
                    : "border-t border-white/10 hover:bg-white/[0.035]"
                }
                key={topic.name}
              >
                <td className="px-4 py-3">
                  <button
                    className="max-w-[220px] truncate text-left font-medium text-white transition hover:text-teal-100"
                    onClick={() => onSelectTopic(topic.name)}
                    title={topic.name}
                    type="button"
                  >
                    {topic.name}
                  </button>
                </td>
                <td className="px-4 py-3 text-slate-300">{topic.partitions}</td>
                <td className="px-4 py-3 text-slate-300">{topic.replication_factor}</td>
                <td className="px-4 py-3 text-teal-100">{topic.message_rate.toFixed(1)}/s</td>
                <td className="px-4 py-3 text-slate-300">{compactNumber(topic.bytes_in_per_second)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
