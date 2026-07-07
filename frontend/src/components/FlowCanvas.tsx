import {
  Background,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import clsx from "clsx";
import { GitBranch, Maximize2, Minimize2, RadioReceiver, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

import { statusTone } from "../lib/status";
import type { FlowGraph, FlowNode as FlowNodeData } from "../types";

import "@xyflow/react/dist/style.css";

interface FlowCanvasProps {
  graph: FlowGraph;
}

type FlowNodeRecord = FlowNodeData & Record<string, unknown>;
type FlowGraphNode = Node<FlowNodeRecord, "flowNode">;

const kindIcons = {
  producer: Send,
  topic: GitBranch,
  consumer: RadioReceiver,
};

function FlowNodeCard({ data }: NodeProps<FlowGraphNode>) {
  const Icon = kindIcons[data.kind];
  return (
    <div
      className={clsx(
        "min-w-44 rounded-lg border bg-[#101d27]/95 p-3 shadow-panel backdrop-blur",
        data.status === "warning" ? "border-amber-300/40" : "border-white/10",
      )}
    >
      <Handle className="!h-2 !w-2 !bg-teal-200" position={Position.Left} type="target" />
      <div className="flex items-center gap-2">
        <span className="rounded-md border border-white/10 bg-white/10 p-1.5 text-slate-100">
          <Icon aria-hidden="true" className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-white">{data.label}</p>
          <p className="truncate text-xs text-slate-400">{data.kind}</p>
        </div>
      </div>
      {data.metric ? (
        <span className={`mt-3 inline-flex rounded-md border px-2 py-1 text-xs ${statusTone(data.status)}`}>
          {data.metric}
        </span>
      ) : null}
      <Handle className="!h-2 !w-2 !bg-sky-200" position={Position.Right} type="source" />
    </div>
  );
}

const nodeTypes = {
  flowNode: FlowNodeCard,
};

function FlowGraphView({ graph }: FlowCanvasProps) {
  const nodes: FlowGraphNode[] = graph.nodes.map((node) => ({
    id: node.id,
    type: "flowNode",
    position: node.position,
    data: { ...node },
    draggable: false,
  }));

  const edges: Edge[] = graph.edges.map((edge) => {
    const warning = edge.status === "warning";
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label ?? undefined,
      animated: warning,
      markerEnd: { type: MarkerType.ArrowClosed, color: warning ? "#d9a441" : "#5aa8d6" },
      style: {
        stroke: warning ? "rgba(217, 164, 65, 0.7)" : "rgba(125, 211, 252, 0.45)",
        strokeWidth: warning ? 1.8 : 1.5,
      },
    };
  });

  return (
    <ReactFlow<FlowGraphNode, Edge>
      fitView
      className="flowka-flow"
      edges={edges}
      maxZoom={1.25}
      minZoom={0.4}
      nodes={nodes}
      nodeTypes={nodeTypes}
      nodesConnectable={false}
      nodesDraggable={false}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#1d2c38" gap={24} size={1} />
      <Controls position="bottom-right" showInteractive={false} />
    </ReactFlow>
  );
}

function FlowHeader({
  expanded,
  onToggle,
}: {
  expanded: boolean;
  onToggle: () => void;
}) {
  const Icon = expanded ? Minimize2 : Maximize2;
  return (
    <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
      <div>
        <h2 className="text-base font-semibold text-white">Flow Graph</h2>
        <p className="text-sm text-slate-400">Producer to Topic to Consumer</p>
      </div>
      <button
        aria-label={expanded ? "Collapse flow graph" : "Expand flow graph"}
        className="rounded-md border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
        onClick={onToggle}
        type="button"
      >
        <Icon aria-hidden="true" className="h-4 w-4" />
      </button>
    </div>
  );
}

export function FlowCanvas({ graph }: FlowCanvasProps) {
  const [open, setOpen] = useState(false);
  const [rendered, setRendered] = useState(false);

  useEffect(() => {
    if (open) {
      setRendered(true);
    }
  }, [open]);

  useEffect(() => {
    if (!rendered) {
      return;
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [rendered]);

  return (
    <section className="flex h-full min-h-[460px] flex-col rounded-lg border border-white/10 bg-[#0b1720] shadow-panel">
      <FlowHeader expanded={false} onToggle={() => setOpen(true)} />
      <div className="min-h-0 flex-1">
        <FlowGraphView graph={graph} />
      </div>

      {rendered
        ? createPortal(
            <div
              className={clsx(
                "fixed inset-0 z-50 flex flex-col bg-ink/90 p-4 backdrop-blur-sm sm:p-6",
                open
                  ? "animate-[flowka-fade-in_180ms_ease-out]"
                  : "animate-[flowka-fade-out_160ms_ease-in]",
              )}
              onAnimationEnd={() => {
                if (!open) {
                  setRendered(false);
                }
              }}
            >
              <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-white/10 bg-[#0b1720] shadow-panel">
                <FlowHeader expanded onToggle={() => setOpen(false)} />
                <div className="min-h-0 flex-1">
                  <FlowGraphView graph={graph} />
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </section>
  );
}
