"use client";

import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useState } from "react";
import { post } from "@/lib/api";
import { useBrain, useInvalidateLearner } from "@/lib/hooks";
import type { AgentRun, Brain, Mastery, Mistake, PlanView } from "@/lib/types";
import Mascot from "../Mascot";
import { Sparkle } from "../ui/Icons";
import { useToast } from "../ui/Toast";

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

const STEP_ORDER = ["Learner Analyst", "Curriculum Planner", "Exercise Generator", "Rules Engine"];
const STEP_ICON: Record<string, string> = {
  "Learner Analyst": "🔍",
  "Curriculum Planner": "🗺️",
  "Exercise Generator": "✍️",
  "Rules Engine": "⚙️",
};

export default function TutorBrain() {
  const { data, isLoading } = useBrain();
  if (isLoading || !data) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-muted">
        <Mascot mood="think" /> Loading Duo&apos;s brain…
      </div>
    );
  }
  return (
    <div className="space-y-8">
      <Hero data={data} />
      <ReviewerPanel data={data} />
      <WhatDuoSees data={data} />
      <section>
        <h2 className="mb-1 text-2xl font-extrabold text-ink">How Duo adapted</h2>
        <p className="mb-4 text-muted">
          Each run is the multi-agent pipeline reacting to your latest answers. Newest first. Expand a step to see its
          tool calls and structured output.
        </p>
        <div className="space-y-5">
          {data.plans.map((p, i) => (
            <PlanCardView key={p.id} plan={p} defaultOpen={i === 0} />
          ))}
          {data.plans.length === 0 && <div className="card p-6 text-center text-muted">No runs yet. Finish a lesson!</div>}
        </div>
      </section>
    </div>
  );
}

function Hero({ data }: { data: Brain }) {
  const invalidate = useInvalidateLearner();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const rerun = async () => {
    setBusy(true);
    try {
      await post("/tutor/plan", { focus: [] });
      toast({ title: "Duo is re-analysing your learning", icon: "🔍", tone: "purple" });
      invalidate();
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="card flex flex-col items-center gap-5 border-duo-purple p-6 sm:flex-row">
      <Mascot size={120} mood={data.running ? "think" : "wave"} />
      <div className="flex-1">
        <div className="flex items-center gap-2 text-sm font-extrabold uppercase tracking-wide text-duo-purple">
          <Sparkle /> Duo AI · adaptive tutor
        </div>
        <h1 className="text-[28px] font-extrabold leading-tight text-ink">Duo studies your mistakes and rewrites your practice.</h1>
        <p className="mt-1 text-muted">
          A team of agents (OpenAI Agents SDK) analyses every answer you give, finds the misconception behind it, plans a
          session and writes new exercises grounded in what you&apos;ve learned.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <Chip color={data.agents_enabled ? "#58CC02" : "#FF9600"}>{data.agents_enabled ? `agents on · ${data.model}` : "rules fallback (no API key)"}</Chip>
          <Chip color="#1CB0F6">{data.budget_left} agent runs left today</Chip>
          {data.running && <Chip color="#CE82FF">running now…</Chip>}
        </div>
      </div>
      <button className="btn btn-purple w-full sm:w-auto" onClick={rerun} disabled={busy || data.running}>
        {data.running ? "Thinking…" : "Re-analyse now"}
      </button>
    </div>
  );
}

function Chip({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span className="rounded-full border-2 px-2.5 py-0.5 font-extrabold" style={{ borderColor: color, color }}>
      {children}
    </span>
  );
}

function ReviewerPanel({ data }: { data: Brain }) {
  const invalidate = useInvalidateLearner();
  const toast = useToast();
  const [busy, setBusy] = useState<string | null>(null);
  const [last, setLast] = useState<{ profile: string; examples: { answer: string; correct: string; error_type: string }[] } | null>(null);

  const inject = async (profile: string) => {
    setBusy(profile);
    try {
      const r = await post<{ profile: string; injected: number; examples: { answer: string; correct: string; error_type: string }[] }>(
        "/tutor/simulate",
        { profile },
      );
      setLast(r);
      toast({ title: `Injected ${r.injected} mistakes`, body: "The agents are re-planning. Watch the timeline below.", icon: "🧪", tone: "purple" });
      invalidate();
    } catch (e) {
      toast({ title: "Couldn't inject", body: (e as Error).message, icon: "⚠️", tone: "red" });
    } finally {
      setBusy(null);
    }
  };

  return (
    <section className="rounded-2xl border-2 border-dashed border-duo-purple p-5">
      <div className="text-sm font-extrabold uppercase tracking-wide text-duo-purple">🧪 For reviewers: test the adaptation live</div>
      <p className="mt-1 text-[15px] text-muted">
        This learner was seeded with sample history (mostly el/la mistakes and missing accents). Pick a different
        behaviour below: it injects ~14 realistic wrong answers derived from real exercises, through the same grader
        and learner model as live answers, and re-runs the agents. You can also{" "}
        <Link href="/learn" className="text-duo-blue">do a real lesson</Link> and get things wrong on purpose.
      </p>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {data.profiles.map((p) => (
          <button
            key={p.key}
            disabled={!!busy || data.running}
            onClick={() => inject(p.key)}
            className="tile flex flex-col items-start p-3 text-left disabled:opacity-60"
          >
            <span className="font-extrabold text-ink">{busy === p.key ? "Injecting…" : p.label}</span>
            <span className="text-xs text-muted">{p.description}</span>
          </button>
        ))}
      </div>
      {last && last.examples.length > 0 && (
        <div className="mt-3 text-xs text-muted">
          Sample injected answers:{" "}
          {last.examples.map((e, i) => (
            <span key={i} className="mr-2">
              <span className="text-duo-red-dark line-through">{e.answer}</span> → <span className="text-duo-green-dark">{e.correct}</span>
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

function WhatDuoSees({ data }: { data: Brain }) {
  const errors = Object.entries(data.error_breakdown.errors_by_type);
  const maxErr = Math.max(1, ...errors.map(([, n]) => n));
  return (
    <section className="grid gap-5 lg:grid-cols-2">
      <div className="card p-5">
        <h3 className="mb-1 text-lg font-extrabold text-ink">Learner model</h3>
        <p className="mb-4 text-xs text-muted">
          Per-concept mastery, updated deterministically on every answer. R = recognition (choosing), P = production (typing/building).
        </p>
        <div className="space-y-3">
          {data.mastery.map((m) => (
            <MasteryRow key={m.concept_key} m={m} />
          ))}
        </div>
      </div>
      <div className="space-y-5">
        <div className="card p-5">
          <h3 className="mb-3 text-lg font-extrabold text-ink">Error types (last {data.error_breakdown.attempts_analysed} answers)</h3>
          <div className="space-y-2">
            {errors.map(([k, n]) => (
              <div key={k} className="flex items-center gap-3 text-sm">
                <span className="w-40 shrink-0 text-muted">{ERROR_LABEL[k] || k}</span>
                <div className="h-3 flex-1 rounded-full bg-line">
                  <div className="h-3 rounded-full bg-duo-red" style={{ width: `${(n / maxErr) * 100}%` }} />
                </div>
                <span className="w-6 text-right text-ink">{n}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 flex gap-4 text-sm text-muted">
            <span>Recognition accuracy: <b className="text-ink">{pct(data.error_breakdown.accuracy_recognition)}</b></span>
            <span>Production accuracy: <b className="text-ink">{pct(data.error_breakdown.accuracy_production)}</b></span>
          </div>
        </div>
        <div className="card p-5">
          <h3 className="mb-3 text-lg font-extrabold text-ink">Recent mistakes</h3>
          <div className="max-h-[300px] space-y-2 overflow-y-auto pr-1">
            {data.recent_mistakes.map((m) => (
              <MistakeRow key={m.attempt_id} m={m} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

const pct = (v: number | null) => (v === null ? "–" : `${Math.round(v * 100)}%`);

function MasteryRow({ m }: { m: Mastery }) {
  const color = m.mastery < 0.35 ? "#FF4B4B" : m.mastery < 0.55 ? "#FF9600" : m.mastery < 0.8 ? "#1CB0F6" : "#58CC02";
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-ink">
          {m.name} {m.due_for_review && <span className="ml-1 rounded bg-duo-yellow px-1 text-[10px] text-white">REVIEW</span>}
        </span>
        <span className="text-xs text-muted">
          R {pct(m.recognition_accuracy)} · P {pct(m.production_accuracy)} · {m.attempts} tries
        </span>
      </div>
      <div className="mt-1 h-2.5 rounded-full bg-line">
        <motion.div className="h-2.5 rounded-full" style={{ background: color }} initial={{ width: 0 }} animate={{ width: `${Math.max(4, m.mastery * 100)}%` }} />
      </div>
    </div>
  );
}

function MistakeRow({ m }: { m: Mistake }) {
  const simulated = m.learner_answer === "(simulated)";
  return (
    <div className="rounded-xl bg-surface-2 p-3 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-muted">{m.task}</span>
        <span className={`shrink-0 rounded-md px-1.5 py-0.5 text-[11px] text-white ${m.typo_only ? "bg-duo-orange" : "bg-duo-red"}`}>
          {ERROR_LABEL[m.error_type || ""] || m.error_type}
        </span>
      </div>
      <div className="mt-1">
        {simulated ? (
          <span className="text-faint">seeded sample mistake</span>
        ) : (
          <span className="text-duo-red-dark line-through">{m.learner_answer}</span>
        )}{" "}
        → <span className="text-duo-green-dark">{m.correct_answer}</span>
        {m.sample && !simulated && <span className="ml-2 text-[11px] text-faint">(sample data)</span>}
      </div>
    </div>
  );
}

function PlanCardView({ plan, defaultOpen }: { plan: PlanView; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const steps = (plan.runs || []).filter((r) => r.kind === "step").sort((a, b) => STEP_ORDER.indexOf(a.agent) - STEP_ORDER.indexOf(b.agent) || a.id - b.id);
  const root = (plan.runs || []).find((r) => r.kind === "pipeline");
  const pending = plan.status === "pending";
  return (
    <div className={`card overflow-hidden ${pending ? "border-duo-purple" : ""}`}>
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center gap-4 p-5 text-left">
        <Mascot size={52} animate={pending} mood={pending ? "think" : "happy"} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Chip color={plan.engine === "agents" ? "#CE82FF" : "#FF9600"}>{plan.engine === "agents" ? "multi-agent" : "rules fallback"}</Chip>
            <Chip color={pending ? "#CE82FF" : plan.status === "ready" ? "#58CC02" : "#AFAFAF"}>{plan.status}</Chip>
            <span className="text-muted">trigger: {plan.trigger.replace("_", " ")} · {new Date(plan.created_at + "Z").toLocaleTimeString()}</span>
            {root && <span className="text-muted">· {(root.latency_ms / 1000).toFixed(1)}s</span>}
          </div>
          <div className="mt-1 text-[16px] text-ink">{pending ? "Agents are working on it…" : plan.summary || plan.error}</div>
        </div>
        <span className="text-faint">{open ? "▲" : "▼"}</span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
            <div className="space-y-5 border-t-2 border-line p-5">
              <Pipeline steps={steps} pending={pending} engine={plan.engine} />
              {plan.diagnosis && <DiagnosisView plan={plan} />}
              {plan.items.length > 0 && <PlanItems plan={plan} />}
              {plan.exercises && plan.exercises.length > 0 && <GeneratedExercises plan={plan} />}
              {plan.status === "ready" && (
                <Link href="/practice?mode=personalized" className="btn btn-purple w-full">
                  Start this practice ({plan.exercise_count})
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Pipeline({ steps, pending, engine }: { steps: AgentRun[]; pending: boolean; engine: string }) {
  const expected = engine === "rules" ? ["Rules Engine"] : ["Learner Analyst", "Curriculum Planner", "Exercise Generator"];
  return (
    <div>
      <div className="mb-2 text-sm font-extrabold uppercase tracking-wide text-muted">Pipeline</div>
      <div className="grid gap-3 md:grid-cols-3">
        {expected.map((name, i) => {
          const runs = steps.filter((s) => s.agent === name);
          const run = runs[runs.length - 1];
          return <StepCard key={name} name={name} run={run} retries={runs.length - 1} index={i} pending={pending} />;
        })}
      </div>
    </div>
  );
}

function StepCard({ name, run, retries, index, pending }: { name: string; run?: AgentRun; retries: number; index: number; pending: boolean }) {
  const [show, setShow] = useState(false);
  const state = run ? run.status : pending ? "waiting" : "skipped";
  const color = state === "ok" ? "#58CC02" : state === "running" ? "#CE82FF" : state === "error" || state === "blocked" ? "#FF4B4B" : state === "fallback" ? "#FF9600" : "#AFAFAF";
  return (
    <div className="rounded-xl border-2 p-3" style={{ borderColor: color }}>
      <div className="flex items-center gap-2">
        <span className="text-xl">{STEP_ICON[name]}</span>
        <div className="flex-1">
          <div className="text-[15px] font-extrabold text-ink">{index + 1}. {name}</div>
          <div className="text-xs" style={{ color }}>
            {state === "running" ? <span className="animate-pulse">running…</span> : state}
            {run && run.status !== "running" && ` · ${(run.latency_ms / 1000).toFixed(1)}s · ${run.input_tokens + run.output_tokens} tok`}
            {retries > 0 && ` · ${retries} repair round`}
          </div>
        </div>
        {run && run.status !== "running" && (
          <button className="text-xs font-extrabold uppercase text-duo-blue" onClick={() => setShow((s) => !s)}>
            {show ? "hide" : "details"}
          </button>
        )}
      </div>
      {run && run.tool_calls.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {run.tool_calls.map((t, i) => (
            <span key={i} className="rounded-md bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-muted">
              🔧 {t.tool}()
            </span>
          ))}
        </div>
      )}
      {show && run && (
        <pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-surface-2 p-2 text-[11px] leading-snug text-muted">
          {run.error ? `ERROR: ${run.error}\n\n` : ""}
          {JSON.stringify(run.output, null, 2)}
        </pre>
      )}
    </div>
  );
}

function DiagnosisView({ plan }: { plan: PlanView }) {
  const d = plan.diagnosis!;
  return (
    <div>
      <div className="mb-2 text-sm font-extrabold uppercase tracking-wide text-muted">
        Diagnosis {typeof d.confidence === "number" && <span className="normal-case">· confidence {Math.round(d.confidence * 100)}%</span>}
      </div>
      {d.overall_summary && <p className="mb-3 text-[15px] text-ink">{d.overall_summary}</p>}
      <div className="grid gap-2 md:grid-cols-2">
        {d.weak_concepts.map((w) => (
          <div key={w.concept_key} className="rounded-xl bg-surface-2 p-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-extrabold text-ink">{w.concept_key}</span>
              <span className={`rounded px-1.5 text-[11px] text-white ${w.severity === "high" ? "bg-duo-red" : w.severity === "medium" ? "bg-duo-orange" : "bg-duo-yellow"}`}>
                {w.severity}
              </span>
              <span className="rounded bg-duo-blue px-1.5 text-[11px] text-white">{w.weakness_mode}</span>
            </div>
            <div className="mt-1 text-muted">{w.evidence}</div>
            {w.likely_misconception && <div className="mt-1 text-ink">💡 {w.likely_misconception}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

function PlanItems({ plan }: { plan: PlanView }) {
  return (
    <div>
      <div className="mb-2 text-sm font-extrabold uppercase tracking-wide text-muted">Plan</div>
      {plan.strategy && <p className="mb-2 text-[15px] italic text-ink">{plan.strategy}</p>}
      <div className="space-y-2">
        {plan.items.map((it) => (
          <div key={it.concept_key} className="flex flex-col gap-1 rounded-xl bg-surface-2 p-3 text-sm sm:flex-row sm:items-center sm:gap-3">
            <span className="font-extrabold text-ink">{it.concept_key}</span>
            <span className="text-muted">×{it.exercise_count} · {it.exercise_types.join(", ")} · lvl {it.difficulty}</span>
            <span className="text-muted sm:ml-auto sm:max-w-[50%] sm:text-right">{it.reason}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function GeneratedExercises({ plan }: { plan: PlanView }) {
  return (
    <div>
      <div className="mb-2 text-sm font-extrabold uppercase tracking-wide text-muted">
        Exercises · {plan.generated_count} written by the generator, {plan.seeded_count} picked from the course
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {plan.exercises!.map((e) => (
          <div key={e.id} className="rounded-xl border-2 border-line p-3 text-sm">
            <div className="flex items-center gap-2">
              <span className={`rounded px-1.5 text-[11px] text-white ${e.source === "agent" ? "bg-duo-purple" : "bg-faint"}`}>
                {e.source === "agent" ? "AI-written" : "course"}
              </span>
              <span className="text-muted">{e.type.replace("_", " ")}</span>
              <span className="ml-auto truncate text-xs text-faint">{e.concepts.join(", ")}</span>
            </div>
            <div className="mt-1 text-ink">{previewText(e.type, e.preview)}</div>
            <div className="text-duo-green-dark">✓ {e.answer}</div>
            {e.rationale && <div className="mt-1 text-xs text-muted">Why: {e.rationale}</div>}
          </div>
        ))}
      </div>
      {plan.validation_errors.length > 0 && (
        <details className="mt-3 text-sm text-muted">
          <summary className="cursor-pointer font-extrabold text-duo-orange">
            🛡️ Validator rejected {plan.validation_errors.length} generated item(s)
          </summary>
          <ul className="mt-2 list-disc pl-5">
            {plan.validation_errors.map((v, i) => (
              <li key={i}>{v}</li>
            ))}
          </ul>
        </details>
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
