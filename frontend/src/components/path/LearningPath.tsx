"use client";

import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { post } from "@/lib/api";
import { useInvalidateLearner, usePath } from "@/lib/hooks";
import type { PathNode, PlanCard, Unit } from "@/lib/types";
import Mascot from "../Mascot";
import { Check, Chest, Crown, Lock, Sparkle, Star, Trophy } from "../ui/Icons";
import Modal from "../ui/Modal";
import { useToast } from "../ui/Toast";
import { BookOpen, Gem as GemIcon } from "lucide-react";

// Horizontal offsets that make the path snake like Duolingo's.
const OFFSETS = [0, 44, 70, 44, 0, -44, -70, -44];

function shade(hex: string, amt: number) {
  const n = parseInt(hex.slice(1), 16);
  const f = (c: number) => Math.max(0, Math.min(255, c + amt));
  return `#${((f(n >> 16) << 16) | (f((n >> 8) & 255) << 8) | f(n & 255)).toString(16).padStart(6, "0")}`;
}

export default function LearningPath() {
  const { data, isLoading, error } = usePath();
  const activeRef = useRef<HTMLDivElement>(null);
  const scrolled = useRef(false);

  useEffect(() => {
    if (data && activeRef.current && !scrolled.current) {
      scrolled.current = true;
      activeRef.current.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [data]);

  if (isLoading) return <PathSkeleton />;
  if (error || !data) return <div className="p-10 text-center text-muted">Couldn&apos;t load your path. Is the API running?</div>;

  const activeNodeId = data.units.flatMap((u) => u.nodes).find((n) => n.status === "active")?.id;

  return (
    <div className="pb-10">
      {data.units.map((unit) => (
        <UnitSection
          key={unit.id}
          unit={unit}
          activeNodeId={activeNodeId}
          activeRef={activeRef}
          duoPractice={data.duo_practice}
        />
      ))}
    </div>
  );
}

function UnitSection({
  unit,
  activeNodeId,
  activeRef,
  duoPractice,
}: {
  unit: Unit;
  activeNodeId?: number;
  activeRef: React.RefObject<HTMLDivElement | null>;
  duoPractice: PlanCard | null;
}) {
  const [guide, setGuide] = useState(false);
  const locked = unit.nodes.every((n) => n.status === "locked");
  const color = locked ? "#AFAFAF" : unit.color;
  return (
    <section className="mb-10">
      <div
        className="sticky top-14 z-[150] mb-8 flex items-center justify-between rounded-2xl px-5 py-4 text-white lg:top-2"
        style={{ background: color, boxShadow: `0 4px 0 ${shade(color, -40)}` }}
      >
        <div>
          <div className="text-[13px] font-extrabold uppercase tracking-wider opacity-80">
            Section 1, Unit {unit.position}
          </div>
          <div className="text-xl font-extrabold">{unit.title}</div>
        </div>
        <button
          onClick={() => setGuide(true)}
          className="flex items-center gap-2 rounded-xl border-2 border-b-4 px-3 py-2.5 text-sm font-extrabold uppercase"
          style={{ borderColor: shade(color, -40), background: color }}
        >
          <BookOpen size={20} strokeWidth={2.5} /> <span className="hidden sm:inline">Guidebook</span>
        </button>
      </div>

      <div className="relative flex flex-col items-center gap-5">
        {unit.nodes.map((node, i) => {
          const isActive = node.id === activeNodeId;
          return (
            // Earlier nodes stack above later ones so a node's popover is never covered by the next node.
            <div key={node.id} className="relative flex w-full flex-col items-center" style={{ zIndex: 100 - i }}>
              <div className="relative z-[2]" style={{ transform: `translateX(${OFFSETS[i % OFFSETS.length]}px)` }} ref={isActive ? activeRef : undefined}>
                <Node node={node} color={unit.color} isActive={isActive} />
              </div>
              {isActive && duoPractice && (duoPractice.status === "ready" || duoPractice.status === "pending") && (
                <div style={{ transform: `translateX(${OFFSETS[(i + 1) % OFFSETS.length]}px)` }} className="relative z-[1] mt-5">
                  <DuoPracticeNode plan={duoPractice} />
                </div>
              )}
              {/* Smarto cheers next to the path, like in the app */}
              {i === 2 && (
                <div className="pointer-events-none absolute top-0 hidden sm:block" style={{ left: OFFSETS[i] > 0 ? "12%" : "auto", right: OFFSETS[i] > 0 ? "auto" : "12%" }}>
                  <Mascot size={110} mood={locked ? "sad" : "happy"} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <Modal open={guide} onClose={() => setGuide(false)} wide>
        <div className="text-left">
          <div className="text-sm font-extrabold uppercase text-muted">Unit {unit.position} guidebook</div>
          <h2 className="mb-1 text-2xl font-extrabold text-ink">{unit.title}</h2>
          <p className="mb-4 text-muted">{unit.description}</p>
          <div className="space-y-2">
            {unit.guidebook.map((g) => (
              <div key={g.es} className="card p-3">
                <div className="font-extrabold text-ink">{g.es}</div>
                <div className="text-sm text-muted">{g.en}</div>
              </div>
            ))}
          </div>
          <button className="btn btn-blue mt-5 w-full" onClick={() => setGuide(false)}>Got it</button>
        </div>
      </Modal>
    </section>
  );
}

function ProgressRing({ value, color }: { value: number; color: string }) {
  const r = 46;
  const c = 2 * Math.PI * r;
  return (
    <svg width={104} height={104} className="absolute -left-[13px] -top-[13px] -rotate-90" aria-hidden>
      <circle cx={52} cy={52} r={r} stroke="var(--border)" strokeWidth={8} fill="none" />
      <circle cx={52} cy={52} r={r} stroke={color} strokeWidth={8} fill="none" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c * (1 - value)} />
    </svg>
  );
}

function Node({ node, color, isActive }: { node: PathNode; color: string; isActive: boolean }) {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const toast = useToast();
  const invalidate = useInvalidateLearner();

  if (node.kind === "chest") {
    const claimable = node.status === "active";
    return (
      <button
        disabled={!claimable}
        onClick={async () => {
          const r = await post<{ gems_awarded: number }>(`/path/chest/${node.id}`);
          toast({ title: `+${r.gems_awarded} gems!`, body: "You opened a treasure chest", icon: <GemIcon className="text-duo-blue" />, tone: "blue" });
          invalidate();
        }}
        className={`relative transition-transform ${claimable ? "animate-bounce hover:scale-105" : ""} ${node.status === "locked" ? "opacity-50 grayscale" : ""}`}
        aria-label="Treasure chest"
      >
        <Chest size={76} open={node.status === "completed"} />
      </button>
    );
  }
  if (node.kind === "trophy") {
    return (
      <div className="py-2" aria-label="Unit trophy">
        <Trophy size={76} muted={node.status !== "completed"} />
      </div>
    );
  }

  const locked = node.status === "locked";
  const done = node.status === "completed";
  const legendary = node.is_legendary;
  const bg = locked ? "var(--locked)" : legendary ? "#CE82FF" : color;
  const lip = locked ? "var(--locked-dark)" : legendary ? "#A568CC" : shade(color, -45);
  const progress = node.lessons_total ? node.lessons_completed / node.lessons_total : 0;

  return (
    <div className="relative">
      {isActive && !open && (
        <div className="animate-bob absolute -top-14 left-1/2 z-10 whitespace-nowrap rounded-xl border-2 border-line bg-surface px-3 py-2 text-[15px] font-extrabold uppercase tracking-wide" style={{ color }}>
          Start
          <div className="absolute -bottom-[9px] left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-b-2 border-r-2 border-line bg-surface" />
        </div>
      )}
      <div className="relative">
        {isActive && <ProgressRing value={progress} color={color} />}
        <motion.button
          whileTap={{ y: 6 }}
          onClick={() => setOpen((o) => !o)}
          className="relative grid h-[78px] w-[78px] place-items-center rounded-full"
          style={{ background: bg, boxShadow: `0 8px 0 ${lip}` }}
          aria-label={`${node.title} (${node.status})`}
        >
          {locked ? <Lock size={34} /> : done ? (legendary ? <Crown size={36} /> : <Check size={38} />) : <Star size={36} />}
        </motion.button>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8 }}
            className="absolute left-1/2 top-[100px] z-20 w-[300px] -translate-x-1/2 rounded-2xl p-4 text-white"
            style={{ background: locked ? "var(--surface-2)" : bg, color: locked ? "var(--text-faint)" : "#fff", border: locked ? "2px solid var(--border)" : undefined }}
          >
            <div className="absolute -top-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45" style={{ background: locked ? "var(--surface-2)" : bg }} />
            <div className="text-lg font-extrabold">{node.title}</div>
            <div className="mb-3 text-[15px] opacity-90">
              {locked
                ? "Complete all levels above to unlock this!"
                : done
                  ? legendary ? "You're Legendary at this skill!" : "Level complete! Practice or go Legendary."
                  : `Lesson ${node.lessons_completed + 1} of ${node.lessons_total}`}
            </div>
            {!locked && (
              <div className="flex flex-col gap-2">
                <button
                  className="btn w-full bg-white"
                  style={{ color: bg, borderColor: "rgba(0,0,0,0.15)" }}
                  onClick={() => router.push(`/lesson/${node.next_lesson_id}`)}
                >
                  {done ? "Practice +10 XP" : "Start +10 XP"}
                </button>
                {done && !legendary && (
                  <button className="btn btn-yellow w-full" onClick={() => router.push(`/practice?mode=legendary&skill=${node.id}`)}>
                    Legendary +40 XP
                  </button>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function DuoPracticeNode({ plan }: { plan: PlanCard }) {
  const ready = plan.status === "ready";
  return (
    <Link
      href={ready ? "/practice?mode=personalized" : "/tutor?tab=learn"}
      className="group relative flex flex-col items-center"
      aria-label="Smarto's personalized practice"
    >
      <div
        className={`relative grid h-[78px] w-[78px] place-items-center rounded-full ${ready ? "animate-pulse-ring" : ""}`}
        style={{ background: "#CE82FF", boxShadow: "0 8px 0 #A568CC" }}
      >
        <Mascot size={58} animate={false} mood={ready ? "happy" : "think"} />
        <span className="absolute -right-1 -top-1"><Sparkle size={22} color="#FFC800" /></span>
      </div>
      <div className="mt-4 max-w-[220px] rounded-xl border-2 border-duo-purple bg-surface px-3 py-1.5 text-center text-xs font-extrabold uppercase tracking-wide text-duo-purple">
        {ready ? `Smarto's practice · ${plan.exercise_count} for you` : "Smarto is building your practice…"}
      </div>
    </Link>
  );
}

function PathSkeleton() {
  return (
    <div className="flex flex-col items-center gap-6 pt-6">
      <div className="h-20 w-full animate-pulse rounded-2xl bg-line" />
      {OFFSETS.slice(0, 6).map((o, i) => (
        <div key={i} className="h-[78px] w-[78px] animate-pulse rounded-full bg-line" style={{ transform: `translateX(${o}px)` }} />
      ))}
    </div>
  );
}
