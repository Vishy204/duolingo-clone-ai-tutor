"use client";

import { AnimatePresence, motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, post } from "@/lib/api";
import { useInvalidateLearner, useMe } from "@/lib/hooks";
import { sfx } from "@/lib/sound";
import type { AnswerResult, CompleteResult, Exercise, SessionData } from "@/lib/types";
import FillBlank from "../exercises/FillBlank";
import MatchPairs from "../exercises/MatchPairs";
import MultipleChoice from "../exercises/MultipleChoice";
import TranslateWordBank from "../exercises/TranslateWordBank";
import TypeAnswer from "../exercises/TypeAnswer";
import Mascot from "../Mascot";
import { Close, Gem, Heart, Sparkle } from "../ui/Icons";
import Modal from "../ui/Modal";
import { useToast } from "../ui/Toast";
import FeedbackSheet from "./FeedbackSheet";
import LessonComplete from "./LessonComplete";
import { Award, Gem as GemIcon, HeartCrack, TriangleAlert } from "lucide-react";

type Phase = "loading" | "answering" | "feedback" | "complete" | "error";

export default function LessonPlayer({ start }: { start: () => Promise<SessionData> }) {
  const router = useRouter();
  const toast = useToast();
  const invalidate = useInvalidateLearner();
  const { data: me } = useMe();

  const [session, setSession] = useState<SessionData | null>(null);
  const [queue, setQueue] = useState<Exercise[]>([]);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState<Record<string, unknown> | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [hearts, setHearts] = useState(5);
  const [progress, setProgress] = useState(0);
  const [combo, setCombo] = useState(0);
  const [mistakes, setMistakes] = useState(0);
  const [quitOpen, setQuitOpen] = useState(false);
  const [noHearts, setNoHearts] = useState(false);
  const [summary, setSummary] = useState<CompleteResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const exStartedAt = useRef(0);
  const started = useRef(false);

  const boot = useCallback(() => {
    setPhase("loading");
    setError(null);
    start()
      .then((s) => {
        setSession(s);
        setQueue(s.exercises);
        setHearts(s.hearts);
        setPhase("answering");
        if (s.time_limit_seconds) setSecondsLeft(s.time_limit_seconds);
        exStartedAt.current = Date.now();
      })
      .catch((e: ApiError) => {
        if (e.code === "no_hearts") setNoHearts(true);
        setError(e.message);
        setPhase("error");
      });
  }, [start]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    boot();
  }, [boot]);

  // Legendary mode is timed.
  useEffect(() => {
    if (secondsLeft === null || phase === "complete" || phase === "error") return;
    const t = setTimeout(() => {
      if (secondsLeft <= 1) {
        setSecondsLeft(0);
        setError("Time's up! Legendary challenges are timed. Try again!");
        setPhase("error");
      } else setSecondsLeft(secondsLeft - 1);
    }, 1000);
    return () => clearTimeout(t);
  }, [secondsLeft, phase]);

  const current = queue[index];

  const finish = useCallback(async () => {
    if (!session) return;
    setBusy(true);
    try {
      const done = await post<CompleteResult>(`/sessions/${session.id}/complete`);
      sfx.complete();
      setSummary(done);
      setPhase("complete");
      done.achievements.forEach((a, i) =>
        setTimeout(() => toast({ title: `Achievement unlocked: ${a.title}`, body: a.description, icon: <Award className="text-duo-yellow" />, tone: "green" }), 600 + i * 900),
      );
      invalidate();
    } catch (e) {
      setError((e as Error).message);
      setPhase("error");
    } finally {
      setBusy(false);
    }
  }, [session, toast, invalidate]);

  const check = useCallback(
    async (override?: Record<string, unknown>) => {
      const payload = override ?? answer;
      if (!session || !current || !payload || busy) return;
      setBusy(true);
      try {
        const r = await post<AnswerResult>(`/sessions/${session.id}/answers`, {
          exercise_id: current.id,
          answer: payload,
          time_ms: Date.now() - exStartedAt.current,
        });
        setResult(r);
        setHearts(r.hearts);
        setProgress(r.progress);
        setCombo(r.combo);
        if (r.correct) sfx.correct();
        else {
          sfx.wrong();
          setMistakes((m) => m + 1);
        }
        if (r.requeued) setQueue((q) => [...q, current]);
        setPhase("feedback");
        if (r.failed) setTimeout(() => setError("Three mistakes: the Legendary challenge is over. Practice and try again!"), 50);
      } catch (e) {
        const err = e as ApiError;
        if (err.code === "no_hearts") setNoHearts(true);
        else toast({ title: "Hmm, that didn't go through", body: err.message, icon: <TriangleAlert className="text-duo-red" />, tone: "red" });
      } finally {
        setBusy(false);
      }
    },
    [answer, session, current, busy, toast],
  );

  const next = useCallback(() => {
    if (result?.failed) {
      setPhase("error");
      return;
    }
    if (result?.out_of_hearts) {
      setNoHearts(true);
      return;
    }
    setResult(null);
    setAnswer(null);
    exStartedAt.current = Date.now();
    if (index + 1 >= queue.length) {
      void finish();
    } else {
      setIndex((i) => i + 1);
      setPhase("answering");
    }
  }, [result, index, queue.length, finish]);

  // Enter = check / continue (Duolingo's keyboard flow).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Enter" || quitOpen || noHearts) return;
      if (phase === "answering" && answer) void check();
      else if (phase === "feedback") next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, answer, check, next, quitOpen, noHearts]);

  const quit = async () => {
    if (session) await post(`/sessions/${session.id}/quit`).catch(() => {});
    invalidate();
    router.push("/learn");
  };

  const refill = async () => {
    try {
      await post("/shop/refill-hearts");
      setHearts(5);
      setNoHearts(false);
      invalidate();
      if (result?.out_of_hearts) {
        setResult((r) => (r ? { ...r, out_of_hearts: false } : r));
      }
      if (!session) boot(); // ran out before the lesson even started: start it now
    } catch (e) {
      toast({ title: "Not enough gems", body: (e as Error).message, icon: <GemIcon className="text-duo-blue" />, tone: "blue" });
    }
  };

  if (phase === "complete" && summary) {
    return <LessonComplete summary={summary} onDone={() => router.push("/learn")} />;
  }

  const legendary = session?.mode === "legendary";
  const modeLabel =
    session?.mode === "personalized" ? "Duo's personalized practice" : session?.mode === "practice" ? "Practice" : legendary ? "Legendary" : null;

  return (
    <div className="flex min-h-[100dvh] flex-col">
      {/* Header: quit, progress bar, hearts */}
      <header className="mx-auto flex w-full max-w-[1040px] items-center gap-4 px-4 pt-6 sm:px-10 sm:pt-10">
        <button onClick={() => setQuitOpen(true)} className="text-faint hover:text-muted" aria-label="Quit lesson">
          <Close size={26} />
        </button>
        <div className="relative h-4 flex-1 rounded-full bg-line">
          <motion.div
            className="h-4 rounded-full"
            style={{ background: legendary ? "#CE82FF" : "#58CC02" }}
            animate={{ width: `${Math.max(progress * 100, 2)}%` }}
            transition={{ type: "spring", stiffness: 120, damping: 18 }}
          >
            <div className="mx-2 mt-1 h-1.5 rounded-full bg-white/30" />
          </motion.div>
          <AnimatePresence>
            {combo >= 3 && phase === "feedback" && result?.correct && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="absolute -top-7 left-0 text-sm font-extrabold uppercase text-duo-orange"
              >
                {combo} in a row
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        {legendary ? (
          <div className="flex items-center gap-3 font-extrabold">
            <span className="text-duo-purple">⏱ {secondsLeft ?? "–"}s</span>
            <span className="text-duo-red">✕ {Math.max(0, (session?.max_mistakes ?? 3) - mistakes)}</span>
          </div>
        ) : session?.uses_hearts === false ? (
          <div className="flex items-center gap-1 text-lg font-extrabold text-duo-red"><Heart size={28} />∞</div>
        ) : (
          <motion.div key={hearts} initial={{ scale: 1.4 }} animate={{ scale: 1 }} className="flex items-center gap-1.5 text-lg font-extrabold text-duo-red">
            <Heart size={28} muted={hearts === 0} /> {hearts}
          </motion.div>
        )}
      </header>

      {/* Exercise */}
      <main className="mx-auto flex w-full max-w-[640px] flex-1 flex-col justify-center px-4 py-8 sm:py-12">
        {phase === "loading" && (
          <div className="flex flex-col items-center gap-4 text-muted">
            <Mascot mood="think" size={120} />
            Loading your lesson…
          </div>
        )}
        {phase === "error" && (
          <div className="flex flex-col items-center gap-5 text-center">
            <Mascot mood="sad" size={140} />
            <p className="text-lg text-ink">{error}</p>
            <button className="btn btn-blue w-56" onClick={() => router.push("/learn")}>Back to path</button>
          </div>
        )}
        {current && (phase === "answering" || phase === "feedback") && (
          <AnimatePresence mode="wait">
            <motion.div key={`${current.id}-${index}`} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }}>
              {(current.personalized || modeLabel) && (
                <div className="mb-3 flex items-center gap-1.5 text-sm font-extrabold uppercase tracking-wide text-duo-purple">
                  <Sparkle size={16} /> {current.personalized ? "Duo's pick for you" : modeLabel}
                </div>
              )}
              <ExerciseView
                ex={current}
                disabled={phase === "feedback" || busy}
                status={phase === "feedback" ? (result?.correct ? "correct" : "wrong") : null}
                onChange={setAnswer}
                onAutoSubmit={(a) => void check(a)}
              />
            </motion.div>
          </AnimatePresence>
        )}
      </main>

      {/* Footer: check / feedback */}
      {(phase === "answering" || phase === "feedback") && current && (
        <FeedbackSheet
          phase={phase}
          canCheck={!!answer && !busy}
          hideCheck={current.type === "match_pairs"}
          result={result}
          onCheck={() => void check()}
          onContinue={next}
          onSkip={() => void check({ text: "" , tokens: [], choice: -1, mistakes: 1 })}
        />
      )}

      <Modal open={quitOpen} onClose={() => setQuitOpen(false)}>
        <Mascot mood="sad" size={120} />
        <h2 className="mt-3 text-2xl font-extrabold text-ink">Wait, don&apos;t go!</h2>
        <p className="mb-6 mt-2 text-muted">You&apos;ll lose your progress if you quit now.</p>
        <button className="btn btn-blue mb-3 w-full" onClick={() => setQuitOpen(false)}>Keep learning</button>
        <button className="w-full py-3 font-extrabold uppercase tracking-wide text-duo-red" onClick={quit}>End session</button>
      </Modal>

      <Modal open={noHearts}>
        <HeartCrack size={64} className="mx-auto text-duo-red" />
        <h2 className="mt-3 text-2xl font-extrabold text-ink">You ran out of hearts!</h2>
        <p className="mb-6 mt-2 text-muted">Refill your hearts to keep going, or practice to earn them back.</p>
        <button className="btn btn-blue mb-3 w-full justify-between" onClick={refill} disabled={(me?.gems ?? 0) < (me?.refill_cost ?? 350)}>
          <span>Refill</span>
          <span className="flex items-center gap-1"><Gem size={18} /> {me?.refill_cost ?? 350}</span>
        </button>
        <button className="btn btn-white mb-3 w-full" onClick={() => router.push("/practice?mode=practice")}>
          Practice to earn hearts
        </button>
        <button className="w-full py-3 font-extrabold uppercase tracking-wide text-faint" onClick={quit}>No thanks</button>
      </Modal>
    </div>
  );
}

function ExerciseView({
  ex,
  disabled,
  status,
  onChange,
  onAutoSubmit,
}: {
  ex: Exercise;
  disabled: boolean;
  status: "correct" | "wrong" | null;
  onChange: (a: Record<string, unknown> | null) => void;
  onAutoSubmit: (a: Record<string, unknown>) => void;
}) {
  const props = { data: ex.data, disabled, onChange, status };
  switch (ex.type) {
    case "multiple_choice":
      return <MultipleChoice {...props} />;
    case "translate":
      return <TranslateWordBank {...props} />;
    case "fill_blank":
      return <FillBlank {...props} />;
    case "type_answer":
      return <TypeAnswer {...props} />;
    case "match_pairs":
      return <MatchPairs data={ex.data} disabled={disabled} onDone={(mistakes) => onAutoSubmit({ mistakes })} />;
  }
}
