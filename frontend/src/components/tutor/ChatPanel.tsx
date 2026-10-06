"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { api, post } from "@/lib/api";
import Link from "next/link";
import { keys, useInsights } from "@/lib/hooks";
import type { ChatMessage } from "@/lib/types";
import Mascot from "../Mascot";
import { Mic } from "lucide-react";

const SUGGESTIONS = [
  "Is 'hola amigo' correct?",
  "What should I practise?",
  "When do I use el vs la?",
  "Make me a practice on animal names",
];

export default function ChatPanel() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: keys.chat, queryFn: () => api<{ messages: ChatMessage[] }>("/tutor/chat") });
  const [pending, setPending] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [practiceAsked, setPracticeAsked] = useState(false);
  const { data: insights } = useInsights();
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
      const r = await post<{ reply: string; practice_requested: boolean }>("/tutor/chat", { message: msg });
      if (r.practice_requested) {
        setPracticeAsked(true);
        // The run starts in the background; poll insights so the card below flips to "ready".
        setTimeout(() => qc.invalidateQueries({ queryKey: keys.insights }), 800);
      }
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
          <div className="font-extrabold text-ink">Chat with Smarto</div>
          <div className="text-xs text-muted">Check a phrase, ask about grammar, or ask for practice</div>
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
        {messages.length === 0 && !pending && (
          <Bubble
            m={{
              role: "assistant",
              content:
                "Hi! I'm Smarto. I can check your Spanish, explain grammar, and create custom exercises on anything you want. They show up in the Custom Practice tab. Try one of these:",
            }}
          />
        )}
        {messages.map((m, i) => (
          <Bubble key={i} m={m} />
        ))}
        {pending && (
          <>
            <Bubble m={{ role: "user", content: pending }} />
            <div className="flex items-center gap-2 text-sm text-muted">
              <Mascot size={28} mood="think" /> <span className="animate-pulse">Smarto is thinking…</span>
            </div>
          </>
        )}
        {err && <div className="text-sm text-duo-red">{err}</div>}
        {practiceAsked && (
          <div className="flex items-center gap-3 rounded-2xl border-2 border-duo-purple p-3 text-sm">
            <Mascot size={36} animate={insights?.latest_custom?.status === "pending"} mood={insights?.latest_custom?.status === "ready" ? "happy" : "think"} />
            <div className="flex-1 text-ink">
              {insights?.latest_custom?.status === "ready"
                ? "Your practice is ready in the Custom Practice tab."
                : "Building your practice. It will appear in the Custom Practice tab."}
            </div>
            <Link href="/custom" className="btn btn-brand h-10 px-4 text-[13px]">
              {insights?.latest_custom?.status === "ready" ? "Open" : "View"}
            </Link>
          </div>
        )}
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
          placeholder="Ask Smarto…"
          className="flex-1 rounded-xl border-2 border-line bg-surface-2 px-4 text-ink outline-none focus:border-brand-border"
        />
        <button className="btn btn-brand h-11" disabled={!input.trim() || !!pending}>Send</button>
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
          mine ? "bg-brand text-white" : m.blocked ? "border-2 border-duo-orange text-ink" : "border-2 border-line text-ink"
        }`}
      >
        {m.channel === "voice" && <Mic size={13} className="mr-1 inline opacity-70" />}
        {m.content}
        
      </div>
    </div>
  );
}
