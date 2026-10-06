"use client";

import confetti from "canvas-confetti";
import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { sfx } from "@/lib/sound";
import type { CompleteResult } from "@/lib/types";
import Mascot from "../Mascot";
import { Flame } from "../ui/Icons";

function fmt(s: number) {
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function LessonComplete({ summary, onDone }: { summary: CompleteResult; onDone: () => void }) {
  const [step, setStep] = useState<"summary" | "streak">("summary");

  useEffect(() => {
    const end = Date.now() + 900;
    const frame = () => {
      confetti({ particleCount: 6, angle: 60, spread: 70, origin: { x: 0, y: 0.7 }, colors: ["#58CC02", "#FFC800", "#1CB0F6", "#FF4B4B", "#CE82FF"] });
      confetti({ particleCount: 6, angle: 120, spread: 70, origin: { x: 1, y: 0.7 }, colors: ["#58CC02", "#FFC800", "#1CB0F6", "#FF4B4B", "#CE82FF"] });
      if (Date.now() < end) requestAnimationFrame(frame);
    };
    frame();
  }, []);

  const pct = Math.round(summary.accuracy * 100);
  const accuracyLabel = pct === 100 ? "Perfect" : pct >= 80 ? "Amazing" : pct >= 60 ? "Good" : "Nice try";
  const title =
    summary.mode === "personalized" ? "Personalized practice complete!" : summary.mode === "legendary" ? "You're Legendary!" : summary.mode === "practice" ? "Practice complete!" : "Lesson complete!";

  const next = () => {
    if (step === "summary" && summary.streak_extended) {
      sfx.streak();
      setStep("streak");
    } else onDone();
  };

  return (
    <div className="flex min-h-[100dvh] flex-col">
      <main className="mx-auto flex w-full max-w-[640px] flex-1 flex-col items-center justify-center gap-8 px-4 text-center">
        {step === "summary" ? (
          <>
            <Mascot mood="cheer" size={190} />
            <motion.h1 initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="text-[32px] font-extrabold text-duo-yellow">
              {title}
            </motion.h1>
            <div className="grid w-full grid-cols-3 gap-3">
              <StatCard label="Total XP" color="#FFC800" value={`⚡ ${summary.xp_earned}`} delay={0.1} />
              <StatCard label={accuracyLabel} color="#58CC02" value={`🎯 ${pct}%`} delay={0.25} />
              <StatCard label={summary.duration_seconds < 120 ? "Speedy" : "Committed"} color="#1CB0F6" value={`⏱ ${fmt(summary.duration_seconds)}`} delay={0.4} />
            </div>
            {summary.skill_completed && <div className="text-lg text-duo-green">👑 Level complete! The next one is unlocked.</div>}
            {summary.tutor_updating && (
              <div className="flex items-center gap-2 rounded-2xl border-2 border-duo-purple px-4 py-3 text-left text-[15px] text-ink">
                <span className="text-2xl">🦉</span>
                Duo is reviewing your answers to personalize your next practice…
              </div>
            )}
          </>
        ) : (
          <>
            <motion.div initial={{ scale: 0.3 }} animate={{ scale: [0.3, 1.2, 1] }} transition={{ duration: 0.7 }}>
              <Flame size={170} />
            </motion.div>
            <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>
              <div className="text-[96px] font-black leading-none text-duo-orange">{summary.streak}</div>
              <div className="text-2xl font-extrabold text-duo-orange">day streak!</div>
            </motion.div>
            <WeekRow streak={summary.streak} />
            <p className="max-w-sm text-muted">
              {summary.streak === 1 ? "A new streak begins! Come back tomorrow to keep it going." : "You're on fire! Practice each day so your streak won't reset."}
            </p>
          </>
        )}
      </main>
      <footer className="border-t-2 border-line">
        <div className="mx-auto flex max-w-[1040px] justify-end px-4 py-6 sm:px-10">
          <button className="btn btn-green w-full sm:w-52" onClick={next} autoFocus>
            Continue
          </button>
        </div>
      </footer>
    </div>
  );
}

function StatCard({ label, value, color, delay }: { label: string; value: string; color: string; delay: number }) {
  return (
    <motion.div
      initial={{ y: 30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay }}
      className="overflow-hidden rounded-2xl border-2"
      style={{ borderColor: color, background: color }}
    >
      <div className="py-1 text-xs font-extrabold uppercase tracking-wider text-white">{label}</div>
      <div className="rounded-xl bg-surface py-4 text-xl font-extrabold" style={{ color }}>
        {value}
      </div>
    </motion.div>
  );
}

function WeekRow({ streak }: { streak: number }) {
  const days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
  const today = (new Date().getDay() + 6) % 7;
  return (
    <div className="card flex gap-3 p-4">
      {days.map((d, i) => {
        const on = i <= today && today - i < streak;
        return (
          <div key={d} className="flex flex-col items-center gap-1">
            <span className={`text-xs ${i === today ? "text-duo-orange" : "text-faint"}`}>{d}</span>
            <span className={`grid h-8 w-8 place-items-center rounded-full ${on ? "bg-duo-orange text-white" : "bg-line"}`}>{on ? "✓" : ""}</span>
          </div>
        );
      })}
    </div>
  );
}
