import type { LucideIcon } from "lucide-react";
import { ArrowUpRight } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone?: "mint" | "sky" | "amber" | "rose";
}

const toneClasses = {
  mint: "border-teal-300/25 bg-teal-300/10 text-teal-100",
  sky: "border-sky-300/25 bg-sky-300/10 text-sky-100",
  amber: "border-amber-300/25 bg-amber-300/10 text-amber-100",
  rose: "border-rose-300/25 bg-rose-300/10 text-rose-100",
};

export function MetricCard({ title, value, detail, icon: Icon, tone = "mint" }: MetricCardProps) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.055] p-4 shadow-panel">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-400">{title}</p>
          <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
        </div>
        <div className={`rounded-md border p-2 ${toneClasses[tone]}`}>
          <Icon aria-hidden="true" className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-4 flex items-center gap-2 text-sm text-slate-300">
        <ArrowUpRight aria-hidden="true" className="h-4 w-4 text-teal-200" />
        <span className="truncate">{detail}</span>
      </div>
    </article>
  );
}
