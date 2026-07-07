import { Activity, Boxes, Gauge, Network, RadioTower } from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useState } from "react";

import { ConsumerGroups } from "./components/ConsumerGroups";
import { DashboardHeader } from "./components/DashboardHeader";
import { MessageViewer } from "./components/MessageViewer";
import { MetricCard } from "./components/MetricCard";
import { TopicExplorer } from "./components/TopicExplorer";
import { compactNumber } from "./lib/status";
import { useRealtime } from "./hooks/useRealtime";

const FlowCanvas = lazy(() =>
  import("./components/FlowCanvas").then((module) => ({ default: module.FlowCanvas })),
);
const MetricsChart = lazy(() =>
  import("./components/MetricsChart").then((module) => ({ default: module.MetricsChart })),
);

export default function App() {
  const { snapshot, state } = useRealtime();
  const [selectedTopic, setSelectedTopic] = useState("orders.created");

  useEffect(() => {
    if (snapshot?.topics.length && !snapshot.topics.some((topic) => topic.name === selectedTopic)) {
      setSelectedTopic(snapshot.topics[0].name);
    }
  }, [selectedTopic, snapshot?.topics]);

  const latestMetric = useMemo(() => {
    if (!snapshot?.metrics.length) {
      return null;
    }
    return snapshot.metrics[snapshot.metrics.length - 1];
  }, [snapshot?.metrics]);

  if (!snapshot || !latestMetric) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-ink px-6 text-white">
        <div className="w-full max-w-md rounded-lg border border-white/10 bg-white/[0.055] p-6 shadow-panel">
          <div className="mb-5 flex items-center gap-3">
            <span className="rounded-md border border-teal-300/25 bg-teal-300/10 p-3 text-teal-100">
              <RadioTower aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm uppercase tracking-[0.16em] text-slate-400">Flowka</p>
              <h1 className="text-xl font-semibold">Connecting to telemetry</h1>
            </div>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-1/2 animate-pulse rounded-full bg-teal-300" />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-ink text-slate-100">
      <DashboardHeader overview={snapshot.overview} realtimeState={state} />

      <div className="mx-auto grid w-full max-w-[1540px] gap-5 px-5 py-5 lg:px-8">
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            detail={`${snapshot.overview.partition_count} partitions tracked`}
            icon={Boxes}
            title="Topics"
            tone="sky"
            value={compactNumber(snapshot.overview.topic_count)}
          />
          <MetricCard
            detail="cluster-wide ingress"
            icon={Activity}
            title="Messages"
            tone="mint"
            value={`${latestMetric.messages_per_second.toFixed(1)}/s`}
          />
          <MetricCard
            detail={`${snapshot.overview.consumer_group_count} consumer groups`}
            icon={Gauge}
            title="Lag"
            tone="amber"
            value={compactNumber(latestMetric.lag)}
          />
          <MetricCard
            detail={`${latestMetric.active_consumers} active consumers`}
            icon={Network}
            title="Throughput"
            tone="rose"
            value={`${latestMetric.throughput_kbps.toFixed(1)} KB/s`}
          />
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(380px,0.65fr)]">
          <Suspense fallback={<VisualFallback title="Flow Graph" />}>
            <FlowCanvas graph={snapshot.flow} />
          </Suspense>
          <ConsumerGroups groups={snapshot.consumer_groups} />
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(380px,0.75fr)_minmax(0,1.25fr)]">
          <TopicExplorer
            onSelectTopic={setSelectedTopic}
            selectedTopic={selectedTopic}
            topics={snapshot.topics}
          />
          <Suspense fallback={<VisualFallback title="Realtime Metrics" />}>
            <MetricsChart metrics={snapshot.metrics} />
          </Suspense>
        </section>

        <MessageViewer
          recentMessages={snapshot.recent_messages}
          selectedTopic={selectedTopic}
          topics={snapshot.topics}
        />
      </div>
    </main>
  );
}

function VisualFallback({ title }: { title: string }) {
  return (
    <section className="min-h-72 rounded-lg border border-white/10 bg-white/[0.055] p-4 shadow-panel">
      <h2 className="text-base font-semibold text-white">{title}</h2>
      <div className="mt-6 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full w-1/2 animate-pulse rounded-full bg-teal-300" />
      </div>
    </section>
  );
}
