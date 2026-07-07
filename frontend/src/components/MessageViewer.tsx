import { Search, TerminalSquare } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getTopicMessages } from "../api/client";
import type { TopicMessage, TopicSummary } from "../types";

interface MessageViewerProps {
  topics: TopicSummary[];
  selectedTopic: string;
  recentMessages: TopicMessage[];
}

export function MessageViewer({ topics, selectedTopic, recentMessages }: MessageViewerProps) {
  const [search, setSearch] = useState("");
  const [messages, setMessages] = useState<TopicMessage[]>(recentMessages);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMessages(recentMessages);
  }, [recentMessages]);

  useEffect(() => {
    if (!selectedTopic) {
      return;
    }

    const timer = window.setTimeout(() => {
      setLoading(true);
      getTopicMessages(selectedTopic, search)
        .then(setMessages)
        .catch(() => setMessages(recentMessages.filter((message) => message.topic === selectedTopic)))
        .finally(() => setLoading(false));
    }, 250);

    return () => window.clearTimeout(timer);
  }, [recentMessages, search, selectedTopic]);

  const topicNames = useMemo(() => topics.map((topic) => topic.name), [topics]);

  return (
    <section className="rounded-lg border border-white/10 bg-[#0d1b24] shadow-panel">
      <div className="flex flex-col gap-3 border-b border-white/10 px-4 py-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <span className="rounded-md border border-rose-300/20 bg-rose-300/10 p-2 text-rose-100">
            <TerminalSquare aria-hidden="true" className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-white">Message Viewer</h2>
            <p className="text-sm text-slate-400">{selectedTopic || topicNames[0] || "no topic"}</p>
          </div>
        </div>
        <label className="relative w-full md:w-72">
          <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            className="h-10 w-full rounded-md border border-white/10 bg-black/20 pl-9 pr-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-teal-300/40"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search JSON"
            value={search}
          />
        </label>
      </div>
      <div className="max-h-[440px] overflow-auto p-4">
        {loading ? <p className="text-sm text-slate-400">Loading messages...</p> : null}
        <div className="space-y-3">
          {messages.map((message) => (
            <article className="rounded-lg border border-white/10 bg-black/20 p-3" key={`${message.topic}:${message.partition}:${message.offset}`}>
              <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <span className="rounded-md bg-white/10 px-2 py-1 text-slate-200">p{message.partition}</span>
                <span>offset {message.offset}</span>
                {message.key ? <span className="truncate">key {message.key}</span> : null}
              </div>
              <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-5 text-slate-100">
                {typeof message.value === "string" ? message.value : JSON.stringify(message.value, null, 2)}
              </pre>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
