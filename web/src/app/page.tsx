"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type VectorStore = {
  id: string;
  name: string;
  status?: string;
  fileCounts?: {
    total?: number;
    completed?: number;
    in_progress?: number;
    failed?: number;
    cancelled?: number;
  };
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function Home() {
  const suggestedQuestions = useMemo(
    () => [
      "📋 What topics are covered in the documents?",
      "🎯 What are the key learning objectives?",
      "📄 Can you provide a summary of the main document?",
      "🔑 What are the most important concepts?",
    ],
    [],
  );

  const [vectorStores, setVectorStores] = useState<VectorStore[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string>("");
  const selectedStore = useMemo(
    () => vectorStores.find((s) => s.id === selectedStoreId),
    [vectorStores, selectedStoreId],
  );

  const [assistantId, setAssistantId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    async function loadVectorStores() {
      setError(null);
      try {
        const res = await fetch("/api/vector-stores");
        const json = (await res.json()) as { data?: VectorStore[]; error?: string };
        if (!res.ok) throw new Error(json.error || "Failed to load vector stores");
        const stores = json.data || [];
        setVectorStores(stores);
        if (stores.length > 0) setSelectedStoreId(stores[0].id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load vector stores");
      }
    }

    loadVectorStores();
  }, []);

  useEffect(() => {
    async function initSession() {
      if (!selectedStoreId) return;
      setError(null);
      setLoading(true);
      setMessages([]);
      setAssistantId(null);
      setThreadId(null);

      try {
        const res = await fetch("/api/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            vectorStoreId: selectedStoreId,
            vectorStoreName: selectedStore?.name,
          }),
        });
        const json = (await res.json()) as {
          assistantId?: string;
          threadId?: string;
          model?: string;
          error?: string;
        };
        if (!res.ok) throw new Error(json.error || "Failed to initialize session");

        setAssistantId(json.assistantId || null);
        setThreadId(json.threadId || null);
        setModel(json.model || null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to initialize session");
      } finally {
        setLoading(false);
      }
    }

    initSession();
  }, [selectedStoreId, selectedStore?.name]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    if (!assistantId || !threadId) return;

    setError(null);
    setLoading(true);

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assistantId,
          threadId,
          message: trimmed,
        }),
      });

      const json = (await res.json()) as { reply?: string; error?: string };
      if (!res.ok) throw new Error(json.error || "Request failed");

      setMessages((prev) => [...prev, { role: "assistant", content: json.reply || "" }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat request failed");
    } finally {
      setLoading(false);
    }
  }

  function onComposerKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key !== "Enter") return;
    if (e.shiftKey) return;
    e.preventDefault();
    void sendMessage(input);
  }

  async function copyMessage(idx: number) {
    const msg = messages[idx];
    if (!msg) return;
    try {
      await navigator.clipboard.writeText(msg.content);
      setCopiedIndex(idx);
      window.setTimeout(() => setCopiedIndex((v) => (v === idx ? null : v)), 1200);
    } catch {
      // ignore
    }
  }

  return (
    <div className="h-dvh bg-[var(--background)] text-[var(--foreground)]">
      <div className="flex h-dvh">
        <aside className="hidden w-[320px] flex-col border-r border-[var(--border)] bg-[var(--card)] lg:flex">
          <div className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-[11px] font-semibold tracking-wide text-[var(--brand-2)]">
                  PENTECOST UNIVERSITY
                </div>
                <div className="mt-1 text-base font-extrabold tracking-tight">
                  AI Knowledge Assistant
                </div>
                <div className="mt-1 text-xs leading-5 text-[color:var(--muted)]">
                  ChatGPT-style interface over OpenAI Vector Stores.
                </div>
              </div>
              <div className="rounded-full border border-[rgba(245,179,1,0.35)] bg-[rgba(245,179,1,0.18)] px-2.5 py-1 text-[11px] font-semibold text-[var(--brand-2)]">
                🎓 PoC
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-[var(--border)] bg-[var(--background)] p-3">
              <div className="text-[11px] font-semibold text-[color:var(--muted)]">Knowledge Base</div>

              <select
                className="mt-2 w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[rgba(11,61,145,0.25)]"
                value={selectedStoreId}
                onChange={(e) => setSelectedStoreId(e.target.value)}
                disabled={loading}
              >
                {vectorStores.length === 0 ? (
                  <option value="">No vector stores found</option>
                ) : (
                  vectorStores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name || s.id}
                    </option>
                  ))
                )}
              </select>

              <div className="mt-3 grid gap-1.5 text-[11px] text-[color:var(--muted)]">
                <div className="flex items-center justify-between">
                  <span>Status</span>
                  <span className="font-semibold text-[var(--foreground)]">
                    {loading ? "Working..." : assistantId && threadId ? "Ready" : "Initializing"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Files</span>
                  <span className="font-semibold text-[var(--foreground)]">
                    {selectedStore?.fileCounts?.total ?? "-"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Model</span>
                  <span className="font-semibold text-[var(--foreground)]">{model || "-"}</span>
                </div>
              </div>
            </div>

            <div className="mt-3 rounded-xl border border-[var(--border)] bg-[var(--background)] p-3">
              <div className="text-[11px] font-semibold text-[color:var(--muted)]">Suggested</div>
              <div className="mt-2 grid gap-2">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] px-3 py-2 text-left text-sm font-medium hover:bg-[rgba(11,61,145,0.05)]"
                    onClick={() => sendMessage(q)}
                    disabled={loading || !assistantId || !threadId}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {error ? (
              <div className="mt-3 rounded-xl border border-[rgba(239,68,68,0.25)] bg-[rgba(239,68,68,0.08)] p-3 text-sm text-red-700">
                {error}
              </div>
            ) : null}

            <div className="mt-3 text-[11px] text-[color:var(--muted)]">
              Tip: Set <span className="font-mono">OPENAI_MODEL</span> in <span className="font-mono">web/.env.local</span>.
            </div>
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col">
          <div className="border-b border-[var(--border)] bg-[var(--card)] px-4 py-3 lg:hidden">
            <div className="text-sm font-semibold">AI Knowledge Assistant</div>
            <div className="mt-1 flex items-center gap-2">
              <select
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[rgba(11,61,145,0.25)]"
                value={selectedStoreId}
                onChange={(e) => setSelectedStoreId(e.target.value)}
                disabled={loading}
              >
                {vectorStores.length === 0 ? (
                  <option value="">No vector stores found</option>
                ) : (
                  vectorStores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name || s.id}
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-auto">
            <div className="mx-auto w-full max-w-3xl px-0 py-0">
              {messages.length === 0 ? (
                <div className="px-4 py-6">
                  <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6">
                    <div className="text-base font-semibold">Welcome</div>
                    <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
                      Select a knowledge base and ask a question. Your answers are grounded in the selected documents.
                    </p>
                    <div className="mt-4 grid gap-2 sm:grid-cols-2">
                      {suggestedQuestions.map((q) => (
                        <button
                          key={`center-${q}`}
                          className="rounded-2xl border border-[var(--border)] bg-[var(--background)] px-4 py-3 text-left text-sm font-semibold hover:bg-[rgba(11,61,145,0.05)] disabled:opacity-60"
                          onClick={() => sendMessage(q)}
                          disabled={loading || !assistantId || !threadId}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="divide-y divide-[var(--border)]">
                {messages.map((m, idx) => (
                  <div
                    key={`${m.role}-${idx}`}
                    className={
                      m.role === "assistant"
                        ? "bg-[var(--background)]"
                        : "bg-[var(--card)]"
                    }
                  >
                    <div className="mx-auto flex w-full max-w-3xl gap-4 px-4 py-6">
                      <div
                        className={
                          m.role === "user"
                            ? "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--brand)] text-xs font-bold text-white"
                            : "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[rgba(2,6,23,0.10)] text-xs font-bold text-[var(--foreground)]"
                        }
                      >
                        {m.role === "user" ? "U" : "A"}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-3">
                          <div className="text-xs font-semibold text-[color:var(--muted)]">
                            {m.role === "user" ? "You" : "Assistant"}
                          </div>
                          {m.role === "assistant" ? (
                            <button
                              type="button"
                              className="text-[11px] font-semibold text-[color:var(--muted)] hover:text-[var(--foreground)]"
                              onClick={() => void copyMessage(idx)}
                            >
                              {copiedIndex === idx ? "Copied" : "Copy"}
                            </button>
                          ) : null}
                        </div>
                        <div className="mt-1 whitespace-pre-wrap text-sm leading-7">
                          {m.content}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {loading ? (
                  <div className="bg-[var(--background)]">
                    <div className="mx-auto flex w-full max-w-3xl gap-4 px-4 py-6">
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[rgba(2,6,23,0.10)] text-xs font-bold text-[var(--foreground)]">
                        A
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-xs font-semibold text-[color:var(--muted)]">Assistant</div>
                        <div className="mt-2 h-4 w-40 animate-pulse rounded bg-[rgba(2,6,23,0.10)]" />
                      </div>
                    </div>
                  </div>
                ) : null}

                <div ref={bottomRef} />
              </div>
            </div>
          </div>

          <form
            className="border-t border-[var(--border)] bg-[var(--card)]"
            onSubmit={(e) => {
              e.preventDefault();
              void sendMessage(input);
            }}
          >
            <div className="mx-auto w-full max-w-3xl px-4 py-4">
              <div className="rounded-3xl border border-[var(--border)] bg-[var(--background)] p-2 shadow-sm">
                <div className="flex items-end gap-2">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onComposerKeyDown}
                    placeholder="Message the assistant…"
                    rows={1}
                    className="max-h-48 min-h-[44px] w-full resize-none rounded-2xl bg-transparent px-3 py-2 text-sm leading-6 outline-none"
                    disabled={loading || !assistantId || !threadId}
                  />
                  <button
                    type="submit"
                    className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--brand)] text-white hover:bg-[var(--brand-2)] disabled:opacity-60"
                    disabled={loading || !assistantId || !threadId}
                    aria-label="Send"
                    title="Send"
                  >
                    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
                      <path
                        d="M3 11.5L21 3l-8.5 18-2.8-7.2L3 11.5Z"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M21 3 9.7 13.8"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="mt-2 text-[11px] text-[color:var(--muted)]">
                Enter to send, Shift+Enter for a new line. Your OpenAI API key stays server-side.
              </div>

              {error ? (
                <div className="mt-3 rounded-xl border border-[rgba(239,68,68,0.25)] bg-[rgba(239,68,68,0.08)] p-3 text-sm text-red-700">
                  {error}
                </div>
              ) : null}
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}
