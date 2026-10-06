"use client";

import { MicOff, PhoneOff, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { api, voiceSocketUrl } from "@/lib/api";
import Mascot from "../Mascot";
import RichText from "../ui/RichText";
import { Mic } from "../ui/Icons";

type Status = { enabled: boolean; max_session_secs?: number; sessions_left_today?: number };
type Line = { who: "you" | "duo"; text: string };
type State = "idle" | "connecting" | "listening" | "you" | "duo" | "error";

/** Stitch streamed sentences back together without a space before closing quotes or punctuation. */
function joinSentences(parts: string[]): string {
  return parts.reduce((acc, p) => (!acc ? p : /^[”"’'»)\].,!?;:]/.test(p) ? acc + p : `${acc} ${p}`), "");
}

function friendlyError(raw: string): string {
  if (/1006|websocket|connect/i.test(raw)) return "Couldn't connect to voice. Check your connection and try again.";
  if (/permission|notallowed|denied/i.test(raw)) return "Microphone access is blocked. Allow it in your browser and try again.";
  if (/limit|429|tomorrow/i.test(raw)) return "You've used today's voice chats. Come back tomorrow!";
  return "Something went wrong. Please try again.";
}

/**
 * Voice Smarto: speak a phrase ("¿hola amigo está bien?") and hear Smarto's answer.
 * Browser mic <-> Pipecat over a WebSocket (speech-to-text -> LLM -> text-to-speech on the server).
 */
export default function VoiceDuo({ variant = "card" }: { variant?: "card" | "fab" }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [state, setState] = useState<State>("idle");
  const [lines, setLines] = useState<Line[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  type Client = { disconnect: () => Promise<void>; enableMic: (on: boolean) => void };
  const client = useRef<Client | null>(null);
  const [micOn, setMicOn] = useState(true);
  // The server can emit the same sentence more than once; keep one copy per Smarto turn.
  const turn = useRef<string[]>([]);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<Status>("/voice/status").then(setStatus).catch(() => setStatus({ enabled: false }));
    // Download the voice client while the page is idle, so tapping the mic doesn't wait for it.
    const warm = () => void Promise.all([import("@pipecat-ai/client-js"), import("@pipecat-ai/websocket-transport")]);
    const idle = typeof window.requestIdleCallback === "function" ? window.requestIdleCallback(warm) : window.setTimeout(warm, 1500);
    return () => {
      if (typeof window.cancelIdleCallback === "function") window.cancelIdleCallback(idle);
      else window.clearTimeout(idle);
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

  const toggleMic = () => {
    const next = !micOn;
    client.current?.enableMic(next);
    setMicOn(next);
  };

  const startCall = async () => {
    await stop();
    setMicOn(true);
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
            const joined = joinSentences(turn.current);
            setLines((l) => {
              const last = l[l.length - 1];
              if (last?.who === "duo") return [...l.slice(0, -1), { who: "duo", text: joined }];
              return [...l, { who: "duo", text: joined }];
            });
          },
        },
      });
      client.current = pc as unknown as Client;
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
    connecting: "Starting…",
    listening: micOn ? "Go ahead, I'm listening" : "Mic off. Tap it when you want to talk",
    you: "Hearing you…",
    duo: "Smarto is speaking",
    error: "Couldn't connect",
  }[state];

  const panel = (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <Mascot size={variant === "fab" ? 96 : 112} mood={state === "duo" ? "talk" : state === "you" ? "think" : "happy"} />
        {state === "you" && <span className="absolute -right-2 top-2 h-4 w-4 animate-ping rounded-full bg-duo-blue" />}
      </div>
      {live && state !== "connecting" ? (
        <div className="flex items-center gap-5">
          <button
            onClick={toggleMic}
            aria-pressed={micOn}
            aria-label={micOn ? "Turn microphone off" : "Turn microphone on"}
            className={`grid h-20 w-20 place-items-center rounded-full shadow-[0_6px_0_rgba(0,0,0,0.2)] transition-transform active:translate-y-1 ${
              micOn ? "bg-brand ring-8 ring-brand/25" : "border-2 border-line bg-surface-2 text-muted"
            }`}
          >
            {micOn ? <Mic size={36} /> : <MicOff size={34} strokeWidth={2.5} />}
          </button>
          <button
            onClick={stop}
            aria-label="End voice chat"
            className="flex flex-col items-center gap-1 text-xs font-extrabold uppercase tracking-wide text-duo-red"
          >
            <span className="grid h-12 w-12 place-items-center rounded-full bg-duo-red text-white shadow-[0_4px_0_rgba(0,0,0,0.2)] active:translate-y-0.5">
              <PhoneOff size={22} strokeWidth={2.5} />
            </span>
            End
          </button>
        </div>
      ) : (
        <button
          onClick={state === "connecting" ? stop : startCall}
          className={`relative grid h-20 w-20 place-items-center rounded-full bg-brand shadow-[0_6px_0_rgba(0,0,0,0.2)] transition-transform active:translate-y-1 ${
            state === "connecting" ? "animate-pulse ring-8 ring-brand/25" : ""
          }`}
          aria-label={state === "connecting" ? "Cancel" : "Start voice chat"}
        >
          {state === "connecting" ? (
            <span className="h-8 w-8 animate-spin rounded-full border-4 border-white/40 border-t-white" />
          ) : (
            <Mic size={36} />
          )}
        </button>
      )}
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
                {l.who === "duo" ? <RichText text={l.text} /> : l.text}
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
        className="fixed bottom-20 right-4 z-40 grid h-16 w-16 place-items-center rounded-full bg-brand shadow-[0_6px_0_#5B3FE0] md:bottom-6"
        aria-label={open ? "End voice chat" : "Talk to Smarto"}
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
