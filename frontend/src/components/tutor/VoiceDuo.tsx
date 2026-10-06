"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { api, voiceSocketUrl } from "@/lib/api";
import Mascot from "../Mascot";
import { Mic } from "../ui/Icons";

type Status = { enabled: boolean; llm?: string; stt?: string; tts?: string; max_session_secs?: number; sessions_left_today?: number };
type Line = { who: "you" | "duo"; text: string };
type State = "idle" | "connecting" | "listening" | "you" | "duo" | "error";

/**
 * Voice Duo: speak a phrase ("¿hola amigo está bien?") and hear Duo's answer.
 * Browser mic <-> Pipecat over a WebSocket (Deepgram STT -> Cerebras -> Deepgram TTS on the server).
 */
export default function VoiceDuo({ variant = "card" }: { variant?: "card" | "fab" }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [state, setState] = useState<State>("idle");
  const [lines, setLines] = useState<Line[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const client = useRef<{ disconnect: () => Promise<void> } | null>(null);
  // Bot text arrives more than once per sentence; keep one copy per segment id.
  const segments = useRef(new Map<string | number, string>());

  useEffect(() => {
    api<Status>("/voice/status").then(setStatus).catch(() => setStatus({ enabled: false }));
    return () => {
      void client.current?.disconnect();
    };
  }, []);

  const stop = async () => {
    await client.current?.disconnect().catch(() => {});
    client.current = null;
    setState("idle");
  };

  const startCall = async () => {
    setErr(null);
    setLines([]);
    setOpen(true);
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
          onDisconnected: () => setState("idle"),
          onError: (m) => {
            setErr((m?.data as { message?: string })?.message || "Voice connection error");
            setState("error");
          },
          onBotStartedSpeaking: () => setState("duo"),
          onUserStartedSpeaking: () => {
            setState("you");
            segments.current = new Map();
          },
          onBotStoppedSpeaking: () => setState("listening"),
          onUserTranscript: (d) => {
            if (d.final && d.text.trim()) setLines((l) => [...l.slice(-6), { who: "you", text: d.text }]);
          },
          onBotOutput: (d) => {
            if (!d.text || d.aggregated_by === "word") return;
            segments.current.set(d.segment_id ?? d.text, d.text);
            const text = [...segments.current.values()].join(" ");
            setLines((l) => {
              const last = l[l.length - 1];
              if (last?.who === "duo") return [...l.slice(0, -1), { who: "duo", text }];
              return [...l.slice(-6), { who: "duo", text }];
            });
          },
        },
      });
      client.current = pc as unknown as { disconnect: () => Promise<void> };
      await pc.connect({ wsUrl: await voiceSocketUrl() });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't start the microphone");
      setState("error");
    }
  };

  if (!status?.enabled) {
    if (variant === "fab") return null;
    return (
      <div className="card p-5 text-sm text-muted">
        🎙️ Voice Duo isn&apos;t configured on this server (needs DEEPGRAM_API_KEY + CEREBRAS_API_KEY).
      </div>
    );
  }

  const live = state !== "idle" && state !== "error";
  const label = {
    idle: "Tap to talk",
    connecting: "Connecting…",
    listening: "Listening… say a phrase!",
    you: "Hearing you…",
    duo: "Duo is speaking",
    error: "Something went wrong",
  }[state];

  const panel = (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <Mascot size={variant === "fab" ? 110 : 120} mood={state === "duo" ? "talk" : state === "you" ? "think" : "happy"} />
        {state === "you" && <span className="absolute -right-2 top-2 h-4 w-4 animate-ping rounded-full bg-duo-blue" />}
      </div>
      <button
        onClick={live ? stop : startCall}
        className={`grid h-20 w-20 place-items-center rounded-full ${live ? "bg-duo-red" : "bg-duo-blue"} shadow-[0_6px_0_rgba(0,0,0,0.2)] transition-transform active:translate-y-1`}
        aria-label={live ? "Stop talking to Duo" : "Talk to Duo"}
      >
        {live ? <span className="h-6 w-6 rounded-md bg-white" /> : <Mic size={36} />}
      </button>
      <div className="text-sm font-extrabold uppercase tracking-wide text-muted">{label}</div>
      {err && <div className="text-sm text-duo-red">{err}</div>}
      <div className="w-full space-y-2">
        {lines.map((l, i) => (
          <div key={i} className={`flex ${l.who === "you" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-[15px] ${l.who === "you" ? "bg-duo-blue text-white" : "border-2 border-line text-ink"}`}>
              {l.text}
            </div>
          </div>
        ))}
      </div>
      <div className="text-center text-xs text-faint">
        {status.stt} → {status.llm} → {status.tts} · {status.sessions_left_today} sessions left today
      </div>
    </div>
  );

  if (variant === "card") {
    return (
      <div className="card p-5">
        <div className="mb-1 text-lg font-extrabold text-ink">🎙️ Talk to Duo</div>
        <p className="mb-4 text-sm text-muted">
          Say something like <i>&quot;Is hola amigo correct?&quot;</i> or <i>&quot;How do I say I&apos;m hungry?&quot;</i>. Real-time
          voice: streaming speech-to-text, a fast LLM, and streaming text-to-speech.
        </p>
        {panel}
      </div>
    );
  }

  return (
    <>
      <button
        onClick={() => (open ? setOpen(false) : (setOpen(true), void startCall()))}
        className="fixed bottom-20 right-4 z-40 grid h-16 w-16 place-items-center rounded-full bg-duo-blue shadow-[0_6px_0_#1899D6] md:bottom-6"
        aria-label="Talk to Duo"
      >
        <Mic size={30} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            className="fixed bottom-40 right-4 z-40 w-[320px] rounded-3xl border-2 border-line bg-surface p-5 shadow-2xl md:bottom-28"
          >
            <button className="absolute right-4 top-3 text-faint" onClick={() => (void stop(), setOpen(false))} aria-label="Close">
              ✕
            </button>
            {panel}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
