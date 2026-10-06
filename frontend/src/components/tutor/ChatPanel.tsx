"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { api, post } from "@/lib/api";
import { keys } from "@/lib/hooks";
import type { ChatMessage } from "@/lib/types";
import Mascot from "../Mascot";

const SUGGESTIONS = [
  "Is 'hola amigo' correct?",
  "What should I practise?",
  "When do I use el vs la?",
  "Make me a practice on verbs",
];

export default function ChatPanel() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: keys.chat, queryFn: () => api<{ messages: ChatMessage[] }>("/tutor/chat") });
  const [pending, setPending] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const messages = (data?.messages || []).filter((m) => m.channel !== "voice" || true);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages.length, pending]);

  const send = async (text: string) => {
    const msg = text.trim();
    if (!msg || pending) return;
    setInput("");
    setErr(null);
    setPending(msg);
    try {
      const r = await post<{ reply: string; practice_requested: string[] }>("/tutor/chat", { message: msg });
      if (r.practice_requested?.length) qc.invalidateQueries({ queryKey: keys.insights });
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setPending(null);
      qc.invalidateQueries({ queryKey: keys.chat });
      qc.invalidateQueries({ queryKey: keys.brain });
    }
  };

  return (
    <div className="card flex h-[520px] flex-col">
      <div className="flex items-center gap-3 border-b-2 border-line px-5 py-3">
        <Mascot size={44} animate={false} />
        <div>
          <div className="font-extrabold text-ink">Chat with Duo</div>
          <div className="text-xs text-muted">Agents SDK · tools + guardrails · remembers your mistakes</div>
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
        {messages.length === 0 && !pending && (
          <div className="text-center text-sm text-muted">Ask anything about your Spanish. Try one of these:</div>
        )}
        {messages.map((m, i) => (
          <Bubble key={i} m={m} />
        ))}
        {pending && (
          <>
            <Bubble m={{ role: "user", content: pending }} />
            <div className="flex items-center gap-2 text-sm text-muted">
              <Mascot size={28} mood="think" /> <span className="animate-pulse">Duo is thinking…</span>
            </div>
          </>
        )}
        {err && <div className="text-sm text-duo-red">{err}</div>}
        <div ref={bottom} />
      </div>
      <div className="flex flex-wrap gap-2 px-5 pb-2">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => send(s)} disabled={!!pending} className="rounded-full border-2 border-line px-3 py-1 text-xs text-muted hover:bg-surface-2">
            {s}
          </button>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send(input);
        }}
        className="flex gap-2 border-t-2 border-line p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={500}
          placeholder="Ask Duo…"
          className="flex-1 rounded-xl border-2 border-line bg-surface-2 px-4 text-ink outline-none focus:border-duo-blue-border"
        />
        <button className="btn btn-blue h-11" disabled={!input.trim() || !!pending}>Send</button>
      </form>
    </div>
  );
}

function Bubble({ m }: { m: ChatMessage }) {
  const mine = m.role === "user";
  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-[15px] ${
          mine ? "bg-duo-blue text-white" : m.blocked ? "border-2 border-duo-orange text-ink" : "border-2 border-line text-ink"
        }`}
      >
        {m.channel === "voice" && <span className="mr-1 text-xs opacity-70">🎙️</span>}
        {m.content}
        {m.blocked && <div className="mt-1 text-[11px] uppercase text-duo-orange">blocked by topic guardrail</div>}
      </div>
    </div>
  );
}
