"use client";

import { motion } from "motion/react";
import Link from "next/link";
import { useRef, useState } from "react";
import { post } from "@/lib/api";
import { useBrain, useInvalidateLearner } from "@/lib/hooks";
import type { Brain, Mastery, Mistake, PlanView } from "@/lib/types";
import { CircleCheck, FlaskConical, Map as MapIcon, PenLine, Search, ShieldCheck, Target, TriangleAlert } from "lucide-react";
import Mascot from "../Mascot";
import { useToast } from "../ui/Toast";

/**
 * "How Duo learns": the latest adaptation told as a story.
 * Your mistakes -> what Duo concluded -> what it changed -> the exercises it wrote.
 * Agent traces are not shown here; they are stored in agent_runs and visible via /api/v1/tutor/brain.
 */

const ERROR_LABEL: Record<string, string> = {
  gender_article: "Wrong article (el/la)",
  accent: "Missing accent",
  spelling: "Spelling slip",
  agreement: "Adjective agreement",
  verb_form: "Wrong verb form",
  word_order: "Word order",
  missing_word: "Missing word",
  extra_word: "Extra word",
  vocabulary: "Wrong word",
};

const TYPE_LABEL: Record<string, string> = {
  multiple_choice: "multiple choice",
  translate: "build the sentence",
  match_pairs: "match pairs",
  fill_blank: "fill the blank",
  type_answer: "type the answer",
};

const SEVERITY: Record<string, { label: string; color: string }> = {
  high: { label: "Big gap", color: "#FF4B4B" },
  medium: { label: "Some gap", color: "#FF9600" },
  low: { label: "Small gap", color: "#FFC800" },
};

const MODE: Record<string, string> = {
  recognition: "even when choosing from options",
  production: "when typing or building sentences",
  both: "both when choosing and when typing",
};

type Names = Record<string, string>;

/** Which mistake types point at which topic, so "Mistakes that led here" shows the relevant ones. */
const CONCEPT_ERRORS: Record<string, string[]> = {
  "grammar.gender_articles": ["gender_article"],
  "spelling.accents": ["accent"],
  "grammar.adjective_agreement": ["agreement"],
  "grammar.word_order": ["word_order", "missing_word", "extra_word"],
};

function evidenceFor(concept: string, mistakes: Mistake[]): Mistake[] {
  const tagged = mistakes.filter((m) => m.concepts.includes(concept));
  const wanted = CONCEPT_ERRORS[concept] || (concept.startsWith("verb.") ? ["verb_form"] : concept.startsWith("vocab.") ? ["vocabulary", "spelling"] : []);
  const exact = tagged.filter((m) => m.error_type && wanted.includes(m.error_type));
  return (exact.length ? exact : tagged).slice(0, 3);
}

const humanize = (key: string) => {
  const last = key.split(".").pop() || key;
  const s = last.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
};
const pct = (v: number | null) => (v === null ? "–" : `${Math.round(v * 100)}%`);
const when = (iso: string) => {
  const mins = Math.round((Date.now() - new Date(iso + "Z").getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  if (mins < 60 * 24) return `${Math.round(mins / 60)} h ago`;
  return new Date(iso + "Z").toLocaleDateString();
};

function triggerLabel(trigger: string, profiles: Brain["profiles"]) {
  if (trigger === "onboarding") return "you joined";
  if (trigger === "lesson_complete") return "you finished a lesson";
  if (trigger.endsWith("_complete")) return "you finished a practice";
  if (trigger === "manual") return "you asked Duo to re-analyse";
  if (trigger === "chat") return "you asked for practice in chat";
  if (trigger === "voice") return "you asked for practice by voice";
  if (trigger.startsWith("simulated:")) {
    const p = profiles.find((x) => x.key === trigger.split(":")[1]);
    return `test mistakes were added (“${p?.label ?? "simulated learner"}”)`;
  }
  return trigger.replace(/_/g, " ");
}

export default function TutorBrain() {
  const { data, isLoading } = useBrain();
  const storyRef = useRef<HTMLDivElement>(null);
  if (isLoading || !data) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-muted">
        <Mascot mood="think" /> Loading…
      </div>
    );
  }
  const names: Names = Object.fromEntries(data.mastery.map((m) => [m.concept_key, m.name]));
  const [latest, ...older] = data.plans;

  return (
    <div className="space-y-6">
      <HowItWorks />
      <TryIt data={data} onInjected={() => storyRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })} />

      <div ref={storyRef} className="scroll-mt-24">
        {latest ? (
          <Story plan={latest} data={data} names={names} latest />
        ) : (
          <div className="card flex flex-col items-center gap-3 p-8 text-center text-muted">
            <Mascot size={80} mood="think" />
            Duo hasn&apos;t analysed you yet. Finish a lesson, or add test mistakes above.
          </div>
        )}
      </div>

      <LearnerModel data={data} />

      {older.length > 0 && (
        <section>
          <h3 className="mb-3 text-lg font-extrabold text-ink">Earlier updates</h3>
          <div className="space-y-3">
            {older.map((p) => (
              <OlderPlan key={p.id} plan={p} data={data} names={names} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ overview */

function HowItWorks() {
  const steps = [
    { Icon: PenLine, title: "You answer", body: "Every answer is graded and the mistake gets a type: wrong article, missing accent, word order…" },
    { Icon: Search, title: "Duo finds the cause", body: "After each lesson Duo reads those mistakes and works out what you misunderstand." },
    { Icon: MapIcon, title: "Duo plans", body: "Duo picks the topics to fix and the exercise types that train them." },
    { Icon: Target, title: "Duo writes practice", body: "Duo writes new exercises using only words you've learned, and checks each one before you see it." },
  ];
  return (
    <section className="card p-5">
      <div className="flex items-center gap-3">
        <Mascot size={56} animate={false} />
        <div>
          <h2 className="text-xl font-extrabold text-ink">How Duo learns from your mistakes</h2>
          <p className="text-sm text-muted">This repeats after every lesson. Below is exactly what happened the last time.</p>
        </div>
      </div>
      <ol className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((s, i) => (
          <li key={s.title} className="rounded-xl bg-surface-2 p-3">
            <div className="flex items-center gap-2 font-extrabold text-ink">
              <s.Icon size={20} strokeWidth={2.5} className="text-duo-blue" /> {i + 1}. {s.title}
            </div>
            <p className="mt-1 text-[13px] leading-snug text-muted">{s.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

/* ------------------------------------------------------------------ try it */

function TryIt({ data, onInjected }: { data: Brain; onInjected: () => void }) {
  const invalidate = useInvalidateLearner();
  const toast = useToast();
  const [busy, setBusy] = useState<string | null>(null);
  const [rerunning, setRerunning] = useState(false);
  const [last, setLast] = useState<{ label: string; injected: number; examples: { answer: string; correct: string }[] } | null>(null);

  const inject = async (key: string, label: string) => {
    setBusy(key);
    try {
      const r = await post<{ injected: number; examples: { answer: string; correct: string }[] }>("/tutor/simulate", { profile: key });
      setLast({ label, ...r });
      invalidate();
      onInjected();
    } catch (e) {
      toast({ title: "Couldn't add mistakes", body: (e as Error).message, icon: <TriangleAlert className="text-duo-red" />, tone: "red" });
    } finally {
      setBusy(null);
    }
  };

  const rerun = async () => {
    setRerunning(true);
    try {
      await post("/tutor/plan", { focus: [] });
      invalidate();
      onInjected();
    } finally {
      setRerunning(false);
    }
  };

  const disabled = !!busy || data.running;
  return (
    <section className="rounded-2xl border-2 border-dashed border-duo-purple p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-2xl">
          <h3 className="flex items-center gap-2 text-lg font-extrabold text-ink"><FlaskConical size={20} className="text-duo-purple" /> Try it: give Duo new mistakes</h3>
          <p className="mt-1 text-sm text-muted">
            Pick a kind of learner. We add ~14 realistic wrong answers (graded like real ones) and Duo re-analyses.
            Then check whether the diagnosis and new practice below match what you picked. You can also{" "}
            <Link href="/learn" className="font-bold text-duo-blue">do a real lesson</Link> and make mistakes on purpose.
          </p>
        </div>
        <button className="btn btn-white h-10 px-4 text-[13px]" onClick={rerun} disabled={rerunning || data.running}>
          {data.running ? "Duo is thinking…" : "Re-analyse now"}
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {data.profiles.map((p) => (
          <button
            key={p.key}
            disabled={disabled}
            onClick={() => inject(p.key, p.label)}
            title={p.description}
            className="tile px-4 py-2 text-sm font-extrabold text-ink disabled:opacity-50"
          >
            {busy === p.key ? "Adding…" : p.label}
          </button>
        ))}
      </div>
      {last && (
        <div className="mt-3 rounded-xl bg-surface-2 p-3 text-sm">
          <b className="text-ink">Added {last.injected} “{last.label}” mistakes</b>
          {last.examples.length > 0 && (
            <span className="text-muted">
              , e.g.{" "}
              {last.examples.slice(0, 3).map((e, i) => (
                <span key={i} className="mr-2 whitespace-nowrap">
                  <span className="text-duo-red-dark line-through">{e.answer}</span> → <span className="text-duo-green-dark">{e.correct}</span>
                </span>
              ))}
            </span>
          )}
          <div className="mt-1 text-muted">{data.running ? "Duo is re-analysing. Steps below fill in live (about 30s)." : "Done. See the update below."}</div>
        </div>
      )}
    </section>
  );
}

/* ------------------------------------------------------------------ story */

/** Steps fill in order as the pipeline persists them: diagnosis, then plan, then exercises. */
function stepStates(plan: PlanView): string[] {
  const done = [!!plan.diagnosis, plan.items.length > 0, !!plan.exercises?.length];
  const active = plan.status === "pending" ? "working" : plan.status === "failed" ? "failed" : "done";
  let blocked = false;
  return done.map((ok) => {
    if (ok && !blocked) return "done";
    if (blocked) return active === "working" ? "waiting" : active === "failed" ? "skipped" : "done";
    blocked = true;
    return active;
  });
}

function Story({ plan, data, names, latest }: { plan: PlanView; data: Brain; names: Names; latest?: boolean }) {
  const pending = plan.status === "pending";
  const failed = plan.status === "failed";
  const d = plan.diagnosis;
  const [s2, s3, s4] = stepStates(plan);

  return (
    <section className={`card overflow-hidden ${pending ? "border-duo-purple" : ""}`}>
      <header className="flex flex-wrap items-center gap-3 border-b-2 border-line px-5 py-4">
        <Mascot size={44} mood={pending ? "think" : "happy"} animate={pending} />
        <div className="min-w-0 flex-1">
          <div className="text-xs font-extrabold uppercase tracking-wide text-duo-purple">
            {latest ? "Latest update" : "Update"} · {when(plan.created_at)}
          </div>
          <div className="text-[17px] font-extrabold text-ink">
            {pending ? "Duo is analysing your answers…" : `Duo updated your practice because ${triggerLabel(plan.trigger, data.profiles)}`}
          </div>
        </div>
      </header>

      <div className="px-5 py-5">
        <Step n={1} title="What Duo saw" subtitle="Your recent wrong answers, sorted by type of mistake" state="done">
          <Evidence data={data} patterns={d?.error_patterns || []} latest={latest} />
        </Step>

        <Step
          n={2}
          title="What Duo concluded"
          subtitle="The topics behind those mistakes, and the likely reason"
          state={s2}
          working="Reading your answers…"
        >
          {d && <Diagnosis plan={plan} data={data} names={names} latest={latest} />}
        </Step>

        <Step
          n={3}
          title="What Duo changed"
          subtitle="Which topics you'll practise, and how"
          state={s3}
          working="Choosing topics and exercise types…"
        >
          {plan.items.length > 0 && <PlanItems plan={plan} names={names} />}
        </Step>

        <Step
          n={4}
          title="Your new practice"
          subtitle={
            plan.exercise_count
              ? `${plan.exercise_count} exercises: ${plan.generated_count} written just for you, ${plan.seeded_count} picked from the course`
              : "New exercises for you"
          }
          state={s4}
          working="Writing exercises and checking each one…"
          last
        >
          {plan.exercises && plan.exercises.length > 0 && <Exercises plan={plan} names={names} />}
        </Step>

        {failed && <p className="ml-12 text-sm text-duo-red">This update failed: {plan.error}</p>}
      </div>
    </section>
  );
}

function Step({
  n,
  title,
  subtitle,
  state,
  working,
  last,
  children,
}: {
  n: number;
  title: string;
  subtitle: string;
  state: string;
  working?: string;
  last?: boolean;
  children?: React.ReactNode;
}) {
  const color = { done: "bg-duo-green", working: "bg-duo-purple", waiting: "bg-faint", skipped: "bg-faint" }[state] || "bg-duo-red";
  return (
    <div className="relative flex gap-4">
      <div className="flex flex-col items-center">
        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-extrabold text-white ${color} ${state === "working" ? "animate-pulse" : ""}`}>
          {state === "failed" ? "!" : state === "working" ? "…" : n}
        </span>
        {!last && <span className="w-0.5 flex-1 bg-line" />}
      </div>
      <div className={`min-w-0 flex-1 ${last ? "" : "pb-7"}`}>
        <h3 className="text-[17px] font-extrabold leading-8 text-ink">{title}</h3>
        <p className="mb-3 text-sm text-muted">{subtitle}</p>
        {state === "working" ? (
          <div className="flex items-center gap-2 rounded-xl bg-surface-2 p-3 text-sm text-duo-purple">
            <span className="animate-pulse">●</span> {working}
          </div>
        ) : state === "waiting" || state === "skipped" ? (
          <div className="rounded-xl bg-surface-2 p-3 text-sm text-faint">{state === "waiting" ? "Waiting for the previous step…" : "Skipped"}</div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

function Evidence({ data, patterns, latest }: { data: Brain; patterns: string[]; latest?: boolean }) {
  const eb = data.error_breakdown;
  const errors = Object.entries(eb.errors_by_type).sort((a, b) => b[1] - a[1]);
  const total = errors.reduce((s, [, n]) => s + n, 0);
  return (
    <div className="space-y-3">
      {latest && errors.length > 0 && (
        <>
          <div className="flex flex-wrap gap-2">
            {errors.map(([k, n]) => (
              <span key={k} className="rounded-full bg-surface-2 px-3 py-1 text-sm">
                <b className="text-ink">{n}×</b> <span className="text-muted">{ERROR_LABEL[k] || k}</span>
              </span>
            ))}
          </div>
          <p className="text-sm text-muted">
            {total} mistakes in your last {eb.attempts_analysed} answers. You get <b className="text-ink">{pct(eb.accuracy_recognition)}</b> right when
            choosing from options and <b className="text-ink">{pct(eb.accuracy_production)}</b> when typing or building sentences.
          </p>
        </>
      )}
      {patterns.length > 0 && (
        <ul className="space-y-1 text-sm text-ink">
          {patterns.map((p, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-duo-purple">•</span> {p}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Diagnosis({ plan, data, names, latest }: { plan: PlanView; data: Brain; names: Names; latest?: boolean }) {
  const d = plan.diagnosis!;
  const mastery = Object.fromEntries(data.mastery.map((m) => [m.concept_key, m]));
  return (
    <div className="space-y-3">
      {d.overall_summary && <p className="text-[15px] text-ink">{d.overall_summary}</p>}
      {d.weak_concepts.map((w) => {
        const sev = SEVERITY[w.severity] || SEVERITY.low;
        const examples = latest ? evidenceFor(w.concept_key, data.recent_mistakes) : [];
        const m = mastery[w.concept_key];
        return (
          <div key={w.concept_key} className="rounded-xl border-2 border-line p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[16px] font-extrabold text-ink">{names[w.concept_key] || humanize(w.concept_key)}</span>
              <span className="rounded-md px-2 py-0.5 text-[11px] font-extrabold uppercase text-white" style={{ background: sev.color }}>
                {sev.label}
              </span>
              {m && <span className="ml-auto text-xs text-muted">mastery {Math.round(m.mastery * 100)}%</span>}
            </div>
            <dl className="mt-2 grid gap-1.5 text-sm sm:grid-cols-[110px_1fr]">
              <dt className="font-bold text-muted">Struggles</dt>
              <dd className="text-ink">{MODE[w.weakness_mode] || w.weakness_mode}</dd>
              <dt className="font-bold text-muted">Evidence</dt>
              <dd className="text-ink">{w.evidence}</dd>
              {w.likely_misconception && (
                <>
                  <dt className="font-bold text-muted">Likely reason</dt>
                  <dd className="text-ink">{w.likely_misconception}</dd>
                </>
              )}
            </dl>
            {examples.length > 0 && (
              <div className="mt-3 border-t-2 border-line pt-2">
                <div className="mb-1 text-xs font-bold uppercase text-muted">Mistakes that led here</div>
                <div className="space-y-1">
                  {examples.map((ex) => (
                    <MistakeLine key={ex.attempt_id} m={ex} />
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
      {d.strengths.length > 0 && (
        <p className="text-sm text-muted">
          <span className="font-bold text-duo-green-dark">Doing well:</span> {d.strengths.map((s) => names[s] || humanize(s)).join(", ")}
        </p>
      )}
    </div>
  );
}

function MistakeLine({ m }: { m: Mistake }) {
  const simulated = m.learner_answer === "(simulated)" || !m.learner_answer;
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
      <span className="text-muted">“{m.task}”</span>
      {!simulated && <span className="text-duo-red-dark line-through">{m.learner_answer}</span>}
      <span className="text-duo-green-dark">→ {m.correct_answer}</span>
      {m.error_type && <span className="rounded bg-surface-2 px-1.5 text-[11px] text-muted">{ERROR_LABEL[m.error_type] || m.error_type}</span>}
      {(simulated || m.sample) && <span className="text-[11px] text-faint">sample data</span>}
    </div>
  );
}

function PlanItems({ plan, names }: { plan: PlanView; names: Names }) {
  return (
    <div className="space-y-2">
      {plan.strategy && <p className="text-[15px] text-ink">{plan.strategy}</p>}
      {plan.items.map((it) => (
        <div key={it.concept_key} className="flex gap-3 rounded-xl bg-surface-2 p-3 text-sm">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-duo-blue text-base font-extrabold text-white">
            {it.exercise_count}×
          </span>
          <div className="min-w-0">
            <div className="font-extrabold text-ink">
              {names[it.concept_key] || humanize(it.concept_key)}
              <span className="font-normal text-muted"> · {it.exercise_types.map((t) => TYPE_LABEL[t] || t).join(", ")}</span>
            </div>
            <div className="text-muted">{it.reason}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function Exercises({ plan, names }: { plan: PlanView; names: Names }) {
  const [all, setAll] = useState(false);
  const list = plan.exercises || [];
  const shown = all ? list : list.slice(0, 4);
  return (
    <div className="space-y-3">
      <div className="grid gap-2 md:grid-cols-2">
        {shown.map((e) => (
          <div key={e.id} className="rounded-xl border-2 border-line p-3 text-sm">
            <div className="flex items-center gap-2 text-xs">
              <span className={`rounded px-1.5 py-0.5 font-extrabold text-white ${e.source === "agent" ? "bg-duo-purple" : "bg-faint"}`}>
                {e.source === "agent" ? "New for you" : "From the course"}
              </span>
              <span className="text-muted">{TYPE_LABEL[e.type] || e.type}</span>
              <span className="ml-auto truncate text-faint">{e.concepts.map((c) => names[c] || humanize(c)).join(", ")}</span>
            </div>
            <div className="mt-2 text-ink">{previewText(e.type, e.preview)}</div>
            <div className="text-duo-green-dark">✓ {e.answer}</div>
            {e.rationale && <div className="mt-1 text-xs text-muted">Why this one: {e.rationale}</div>}
          </div>
        ))}
      </div>
      {list.length > 4 && (
        <button className="block text-sm font-extrabold uppercase text-duo-blue" onClick={() => setAll((a) => !a)}>
          {all ? "Show fewer" : `Show all ${list.length}`}
        </button>
      )}
      {plan.validation_errors.length > 0 && (
        <p className="text-xs text-muted">
          <ShieldCheck size={14} className="mr-1 inline text-duo-green" /> {plan.validation_errors.length} new exercise(s) didn&apos;t pass Duo&apos;s quality check and were replaced before reaching you.
        </p>
      )}
      {plan.status === "ready" && (
        <Link href="/practice?mode=personalized" className="btn btn-purple mt-2 w-full sm:w-auto">
          Start this practice
        </Link>
      )}
      {plan.status === "consumed" && <p className="flex items-center gap-1.5 text-sm text-muted"><CircleCheck size={16} className="text-duo-green" /> You already did this practice.</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ learner model + history */

function LearnerModel({ data }: { data: Brain }) {
  const [open, setOpen] = useState(false);
  return (
    <section className="card p-5">
      <button className="flex w-full items-center justify-between text-left" onClick={() => setOpen((o) => !o)}>
        <div>
          <h3 className="text-lg font-extrabold text-ink">Everything Duo tracks about you</h3>
          <p className="text-sm text-muted">A score for each topic, updated after every answer.</p>
        </div>
        <span className="text-faint">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="mt-4 grid gap-x-8 gap-y-3 md:grid-cols-2">
          {data.mastery.map((m) => (
            <MasteryRow key={m.concept_key} m={m} />
          ))}
        </div>
      )}
    </section>
  );
}

function MasteryRow({ m }: { m: Mastery }) {
  const color = m.mastery < 0.35 ? "#FF4B4B" : m.mastery < 0.55 ? "#FF9600" : m.mastery < 0.8 ? "#1CB0F6" : "#58CC02";
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-ink">
          {m.name} {m.due_for_review && <span className="ml-1 rounded bg-duo-yellow px-1 text-[10px] text-white">REVIEW DUE</span>}
        </span>
        <span className="text-xs text-muted" title="Accuracy when choosing / when typing">
          choose {pct(m.recognition_accuracy)} · type {pct(m.production_accuracy)}
        </span>
      </div>
      <div className="mt-1 h-2.5 rounded-full bg-line">
        <motion.div className="h-2.5 rounded-full" style={{ background: color }} initial={{ width: 0 }} animate={{ width: `${Math.max(4, m.mastery * 100)}%` }} />
      </div>
    </div>
  );
}

function OlderPlan({ plan, data, names }: { plan: PlanView; data: Brain; names: Names }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button onClick={() => setOpen((o) => !o)} className="card flex w-full items-center gap-3 p-4 text-left">
        <span className="text-faint">{open ? "▾" : "▸"}</span>
        <div className="min-w-0 flex-1">
          <div className="text-xs text-muted">
            {when(plan.created_at)} · because {triggerLabel(plan.trigger, data.profiles)}
          </div>
          <div className="truncate text-[15px] text-ink">{plan.summary || plan.error || plan.status}</div>
        </div>
      </button>
      {open && (
        <div className="mt-2">
          <Story plan={plan} data={data} names={names} />
        </div>
      )}
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function previewText(type: string, p: any): string {
  if (type === "multiple_choice") return p.question;
  if (type === "fill_blank") return `${p.sentence}  (${p.translation})`;
  if (type === "match_pairs") return p.left.map((l: { text: string }) => l.text).join(" · ");
  return p.source;
}
