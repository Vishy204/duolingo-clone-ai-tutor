"use client";

import { X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { api, voiceSocketUrl } from "@/lib/api";
import Mascot from "../Mascot";
import { Mic } from "../ui/Icons";

type Status = { enabled: boolean; max_session_secs?: number; sessions_left_today?: number };
type Line = { who: "you" | "duo"; text: string };
type State = "idle" | "connecting" | "listening" | "you" | "duo" | "error";

function friendlyError(raw: string): string {
  if (/1006|websocket|connect/i.test(raw)) return "Couldn't connect to voice. Check your connection and try again.";
  if (/permission|notallowed|denied/i.test(raw)) return "Microphone access is blocked. Allow it in your browser and try again.";
  if (/limit|429|tomorrow/i.test(raw)) return "You've used today's voice chats. Come back tomorrow!";
  return "Something went wrong. Please try again.";
}

/**
 * Voice Duo: speak a phrase ("¿hola amigo está bien?") and hear Duo's answer.
 * Browser mic <-> Pipecat over a WebSocket (speech-to-text -> LLM -> text-to-speech on the server).
 */
export default function VoiceDuo({ variant = "card" }: { variant?: "card" | "fab" }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [state, setState] = useState<State>("idle");
  const [lines, setLines] = useState<Line[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const client = useRef<{ disconnect: () => Promise<void> } | null>(null);
  // The server can emit the same sentence more than once; keep one copy per Duo turn.
  const turn = useRef<string[]>([]);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<Status>("/voice/status").then(setStatus).catch(() => setStatus({ enabled: false }));
    return () => {
      void client.current?.disconnect();
    };
  }, []);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [lines]);

  const stop = async () => {
    const c = client.current;
    client.current = null;
    await c?.disconnect().catch(() => {});
    setState("idle");
  };

  const startCall = async () => {
    await stop();
    setErr(null);
    setLines([]);
    turn.current = [];
    setState("connecting");
    try {
      const [{ PipecatClient }, { WebSocketTransport }] = await Promise.all([
        import("@pipecat-ai/client-js"),
        import("@pipecat-ai/websocket-transport"),
      ]);
      const pc = new PipecatClient({
        transport: new WebSocketTransport(),
        enableMic: true,
        enableCam: false,
        callbacks: {
          onBotReady: () => setState("listening"),
          onDisconnected: () => setState((s) => (s === "error" ? s : "idle")),
          onError: (m) => {
            setErr(friendlyError((m?.data as { message?: string })?.message || ""));
            setState("error");
          },
          onBotStartedSpeaking: () => setState("duo"),
          onUserStartedSpeaking: () => {
            setState("you");
            turn.current = [];
          },
          onBotStoppedSpeaking: () => setState("listening"),
          onUserTranscript: (d) => {
            if (d.final && d.text.trim()) setLines((l) => [...l, { who: "you", text: d.text.trim() }]);
          },
          onBotOutput: (d) => {
            const text = d.text?.trim();
            if (!text || d.aggregated_by === "word" || turn.current.includes(text)) return;
            turn.current.push(text);
            const joined = turn.current.join(" ");
            setLines((l) => {
              const last = l[l.length - 1];
              if (last?.who === "duo") return [...l.slice(0, -1), { who: "duo", text: joined }];
              return [...l, { who: "duo", text: joined }];
            });
          },
        },
      });
      client.current = pc as unknown as { disconnect: () => Promise<void> };
      await pc.connect({ wsUrl: await voiceSocketUrl() });
    } catch (e) {
      client.current = null;
      setErr(friendlyError(e instanceof Error ? e.message : String(e)));
      setState("error");
    }
  };

  if (!status?.enabled) {
    if (variant === "fab") return null;
    return <div className="card p-5 text-sm text-muted">Voice chat isn&apos;t available right now.</div>;
  }

  const live = state !== "idle" && state !== "error";
  const label = {
    idle: "Tap to talk",
    connecting: "Connecting…",
    listening: "Listening",
    you: "Hearing you…",
    duo: "Duo is speaking",
    error: "Couldn't connect",
  }[state];

  const panel = (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <Mascot size={variant === "fab" ? 96 : 112} mood={state === "duo" ? "talk" : state === "you" ? "think" : "happy"} />
        {state === "you" && <span className="absolute -right-2 top-2 h-4 w-4 animate-ping rounded-full bg-duo-blue" />}
      </div>
      <button
        onClick={live ? stop : startCall}
        className={`grid h-20 w-20 place-items-center rounded-full ${live ? "bg-duo-red" : "bg-duo-blue"} shadow-[0_6px_0_rgba(0,0,0,0.2)] transition-transform active:translate-y-1`}
        aria-label={live ? "End voice chat" : "Start voice chat"}
      >
        {live ? <span className="h-6 w-6 rounded-md bg-white" /> : <Mic size={36} />}
      </button>
      <div className="text-sm font-extrabold uppercase tracking-wide text-muted">{label}</div>
      {err && (
        <div className="w-full rounded-xl bg-duo-red/10 px-3 py-2 text-center text-sm text-duo-red">
          {err}{" "}
          <button className="font-extrabold underline" onClick={startCall}>
            Try again
          </button>
        </div>
      )}
      {lines.length > 0 && (
        <div ref={scroller} className="max-h-56 w-full space-y-2 overflow-y-auto pr-1">
          {lines.map((l, i) => (
            <div key={i} className={`flex ${l.who === "you" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-[15px] leading-snug ${l.who === "you" ? "bg-duo-blue text-white" : "border-2 border-line text-ink"}`}>
                {l.text}
              </div>
            </div>
          ))}
        </div>
      )}
      {typeof status.sessions_left_today === "number" && state === "idle" && (
        <div className="text-xs text-faint">{status.sessions_left_today} voice chats left today</div>
      )}
    </div>
  );

  if (variant === "card") {
    return (
      <div className="card p-5">
        <div className="mb-1 text-lg font-extrabold text-ink">Voice chat</div>
        <p className="mb-5 text-sm text-muted">
          Ask out loud, like <i>&quot;Is hola amigo correct?&quot;</i> or <i>&quot;How do I say I&apos;m hungry?&quot;</i>
        </p>
        {panel}
      </div>
    );
  }

  const close = () => {
    void stop();
    setOpen(false);
  };

  return (
    <>
      <button
        onClick={() => {
          if (open) close();
          else {
            setOpen(true);
            void startCall();
          }
        }}
        className="fixed bottom-20 right-4 z-40 grid h-16 w-16 place-items-center rounded-full bg-duo-blue shadow-[0_6px_0_#1899D6] md:bottom-6"
        aria-label={open ? "End voice chat" : "Talk to Duo"}
      >
        {open ? <X size={30} color="#fff" strokeWidth={3} /> : <Mic size={30} />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            className="fixed bottom-40 right-4 z-40 w-[340px] max-w-[calc(100vw-2rem)] rounded-3xl border-2 border-line bg-surface p-5 shadow-2xl md:bottom-28"
          >
            <button className="absolute right-4 top-4 text-faint hover:text-ink" onClick={close} aria-label="Close">
              <X size={20} strokeWidth={3} />
            </button>
            {panel}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
