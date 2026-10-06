"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { post } from "@/lib/api";
import type { AnswerResult } from "@/lib/types";
import { Check, Close, Sparkle } from "../ui/Icons";

const PRAISE = ["Nicely done!", "Great job!", "Amazing!", "Excellent!", "You're on fire!", "Correct!"];

type Explanation = { headline: string; explanation: string; example_es: string; example_en: string };

/** The signature bottom bar: grey "Check" -> green "Correct!" or red "Correct solution". */
export default function FeedbackSheet({
  phase,
  canCheck,
  hideCheck,
  result,
  onCheck,
  onContinue,
  onSkip,
}: {
  phase: "answering" | "feedback";
  canCheck: boolean;
  hideCheck: boolean;
  result: AnswerResult | null;
  onCheck: () => void;
  onContinue: () => void;
  onSkip: () => void;
}) {
  const [explain, setExplain] = useState<{ for: number; data?: Explanation; loading?: boolean; error?: string } | null>(null);
  const fb = phase === "feedback" && result;
  const correct = !!result?.correct;
  const praise = result ? PRAISE[result.attempt_id % PRAISE.length] : "";

  const askDuo = async () => {
    if (!result) return;
    setExplain({ for: result.attempt_id, loading: true });
    try {
      const data = await post<Explanation>("/tutor/explain", { attempt_id: result.attempt_id });
      setExplain({ for: result.attempt_id, data });
    } catch (e) {
      setExplain({ for: result.attempt_id, error: (e as Error).message });
    }
  };
  const ex = explain && result && explain.for === result.attempt_id ? explain : null;

  return (
    <div
      className={`border-t-2 transition-colors ${
        fb ? (correct ? "border-transparent bg-duo-green-light" : "border-transparent bg-duo-red-light") : "border-line"
      }`}
    >
      <div className="mx-auto flex min-h-[140px] w-full max-w-[1040px] flex-col justify-center gap-4 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-10">
        <AnimatePresence mode="wait">
          {fb ? (
            <motion.div key="fb" initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="flex flex-1 items-start gap-4">
              <div className={`hidden h-20 w-20 shrink-0 place-items-center rounded-full bg-surface sm:grid`}>
                {correct ? <Check size={44} color="#58A700" /> : <span className="text-duo-red-dark"><Close size={40} /></span>}
              </div>
              <div className={correct ? "text-duo-green-dark" : "text-duo-red-dark"}>
                <div className="text-2xl font-extrabold">{correct ? (result.typo ? "You have a typo." : praise) : "Correct solution:"}</div>
                {!correct && <div className="text-lg">{result.correct_answer}</div>}
                {correct && result.typo && <div className="text-[15px]">{result.correct_answer}</div>}
                {result.feedback && <div className="mt-1 text-[15px] opacity-90">{result.feedback}</div>}
                {!correct && !ex && (
                  <button onClick={askDuo} className="mt-2 flex items-center gap-1.5 text-sm font-extrabold uppercase tracking-wide text-duo-purple">
                    <Sparkle size={16} /> Why? Ask Duo
                  </button>
                )}
                {ex && (
                  <div className="mt-2 max-w-xl rounded-xl bg-surface p-3 text-[15px] text-ink">
                    {ex.loading && <span className="animate-pulse text-muted">Duo is looking at your answer…</span>}
                    {ex.error && <span className="text-muted">{ex.error}</span>}
                    {ex.data && (
                      <>
                        <div className="font-extrabold text-duo-purple">{ex.data.headline}</div>
                        <div className="mt-1">{ex.data.explanation}</div>
                        <div className="mt-2 text-muted">
                          <span className="text-ink">{ex.data.example_es}</span> · {ex.data.example_en}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div key="skip" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="hidden sm:block">
              {!hideCheck && (
                <button className="btn btn-ghost w-36" onClick={onSkip}>
                  Skip
                </button>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {fb ? (
          <button className={`btn w-full sm:w-44 ${correct ? "btn-green" : "btn-red"}`} onClick={onContinue} autoFocus>
            {correct ? "Continue" : "Got it"}
          </button>
        ) : (
          !hideCheck && (
            <button className={`btn w-full sm:w-44 ${canCheck ? "btn-green" : "btn-disabled"}`} disabled={!canCheck} onClick={onCheck}>
              Check
            </button>
          )
        )}
      </div>
    </div>
  );
}
