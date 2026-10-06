"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Bell, BellRing, Check, Loader2, Play, RotateCcw, Sparkles, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useState, useSyncExternalStore } from "react";
import Mascot from "@/components/Mascot";
import AppShell from "@/components/shell/AppShell";
import { useToast } from "@/components/ui/Toast";
import { post } from "@/lib/api";
import { keys, useCustomPractice } from "@/lib/hooks";
import type { CustomTopic, PlanView } from "@/lib/types";

const GROUPS: { kind: string; title: string }[] = [
  { kind: "vocab", title: "Vocabulary" },
  { kind: "grammar", title: "Grammar" },
  { kind: "verb", title: "Verbs" },
  { kind: "spelling", title: "Spelling" },
];
const MAX_TOPICS = 3;

export default function CustomPracticePage() {
  const { data } = useCustomPractice();
  const qc = useQueryClient();
  const toast = useToast();
  const [picked, setPicked] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  const names = Object.fromEntries((data?.topics || []).map((t) => [t.key, t.name]));
  const toggle = (key: string) =>
    setPicked((p) => (p.includes(key) ? p.filter((k) => k !== key) : p.length < MAX_TOPICS ? [...p, key] : p));

  const build = async () => {
    setBusy(true);
    try {
      await post("/tutor/custom", { concepts: picked });
      toast({
        title: "Smarto is building your practice",
        body: "About 30 seconds. You'll get a notification when it's ready.",
        icon: <Sparkles className="text-brand" />,
        tone: "purple",
      });
      setPicked([]);
      // The run starts right after the response; refresh so the new card (and polling) shows up.
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: keys.custom });
        qc.invalidateQueries({ queryKey: keys.insights });
      }, 600);
    } catch (e) {
      toast({ title: "Couldn't start the practice", body: (e as Error).message, icon: <TriangleAlert className="text-duo-red" />, tone: "red" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell rail={false} wide>
      <div className="space-y-6 pt-2">
        <header className="card flex flex-col items-center gap-5 p-6 sm:flex-row">
          <Mascot size={96} mood="wave" />
          <div className="min-w-0 flex-1 text-center sm:text-left">
            <div className="text-sm font-extrabold uppercase tracking-wide text-brand">Smartalingo · Custom Practice</div>
            <h1 className="text-[28px] font-extrabold leading-tight text-ink">Practise exactly what you want</h1>
            <p className="mt-1 text-muted">
              Pick up to {MAX_TOPICS} topics and Smarto builds a practice for you in about 30 seconds. You can also ask
              Smarto in{" "}
              <Link href="/tutor" className="text-brand">
                chat or by voice
              </Link>
              ; those practices land here too.
            </p>
          </div>
          <NotifyButton />
        </header>

        <section className="card p-5">
          <h2 className="text-xl font-extrabold text-ink">1. Pick topics</h2>
          <p className="mb-4 text-sm text-muted">The bar shows how well you know each topic. Topics you haven&apos;t reached yet work too.</p>
          {!data ? (
            <div className="py-8 text-center text-muted">Loading topics…</div>
          ) : (
            <div className="space-y-5">
              {GROUPS.map((g) => {
                const topics = data.topics.filter((t) => t.kind === g.kind);
                if (!topics.length) return null;
                return (
                  <div key={g.kind}>
                    <div className="mb-2 text-xs font-extrabold uppercase tracking-wide text-faint">{g.title}</div>
                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                      {topics.map((t) => (
                        <TopicTile
                          key={t.key}
                          topic={t}
                          selected={picked.includes(t.key)}
                          disabled={!picked.includes(t.key) && picked.length >= MAX_TOPICS}
                          onClick={() => toggle(t.key)}
                        />
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="card flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
          <div className="min-w-0 flex-1">
            <h2 className="text-xl font-extrabold text-ink">2. Build it</h2>
            <p className="text-sm text-muted">
              {picked.length ? picked.map((k) => names[k]).join(" · ") : "No topics picked yet."}
            </p>
            {data && data.budget_left <= 0 && (
              <p className="mt-1 text-sm text-duo-orange">
                You&apos;ve used today&apos;s 15 AI actions, so Smarto will pick course exercises instead of writing new ones.
              </p>
            )}
          </div>
          <button className="btn btn-brand w-full sm:w-auto" disabled={!picked.length || busy} onClick={build}>
            {busy ? "Starting…" : `Build practice${picked.length ? ` (${picked.length})` : ""}`}
          </button>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-extrabold text-ink">Your practices</h2>
          {!data || data.practices.length === 0 ? (
            <div className="card flex flex-col items-center gap-2 p-8 text-center text-muted">
              <Mascot size={64} mood="think" />
              Nothing here yet. Pick topics above, or ask Smarto: &quot;Make me a practice on animals&quot;.
            </div>
          ) : (
            <div className="space-y-3">
              {data.practices.map((p) => (
                <PracticeCard key={p.id} plan={p} names={names} />
              ))}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}

function TopicTile({ topic, selected, disabled, onClick }: { topic: CustomTopic; selected: boolean; disabled: boolean; onClick: () => void }) {
  const m = topic.mastery;
  const color = m === null ? "var(--text-faint)" : m < 0.35 ? "#FF4B4B" : m < 0.55 ? "#FF9600" : m < 0.8 ? "#7C5CFF" : "#58CC02";
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-pressed={selected}
      className={`tile flex flex-col gap-2 p-3 text-left disabled:opacity-50 ${selected ? "tile-selected" : ""}`}
    >
      <span className="flex items-center justify-between gap-2 text-[15px]">
        <span className="font-extrabold">{topic.name}</span>
        {selected && <Check size={18} strokeWidth={3} className="shrink-0" />}
      </span>
      <span className="flex items-center gap-2 text-xs text-muted">
        <span className="h-2 flex-1 rounded-full bg-line">
          <span className="block h-2 rounded-full" style={{ width: `${m === null ? 0 : Math.max(6, m * 100)}%`, background: color }} />
        </span>
        <span className="w-14 text-right">{m === null || topic.attempts === 0 ? "new" : `${Math.round(m * 100)}%`}</span>
      </span>
    </button>
  );
}

const SOURCE: Record<string, string> = { custom: "You picked", chat: "Asked in chat", voice: "Asked by voice" };

function PracticeCard({ plan, names }: { plan: PlanView; names: Record<string, string> }) {
  const topics = plan.focus_concepts.map((k) => names[k] || k).join(" · ");
  const when = new Date(plan.created_at + "Z").toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const pending = plan.status === "pending";
  const done = plan.status === "consumed" || plan.status === "superseded";
  return (
    <div className={`card flex flex-col gap-3 p-4 sm:flex-row sm:items-center ${pending ? "border-brand-border" : ""}`}>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <StatusChip status={plan.status} />
          <span className="text-faint">
            {SOURCE[plan.trigger] || "Smarto"} · {when}
            {plan.exercise_count ? ` · ${plan.exercise_count} exercises` : ""}
          </span>
        </div>
        <div className="mt-1 text-[16px] font-extrabold text-ink">{topics || "Your weakest topics"}</div>
        <div className="text-sm text-muted">
          {pending ? "Smarto is writing your exercises. This takes about 30 seconds." : plan.status === "failed" ? plan.error || "This one didn't work. Try building it again." : plan.summary}
        </div>
      </div>
      {plan.status === "ready" && (
        <Link href={`/practice?mode=personalized&plan=${plan.id}`} className="btn btn-brand w-full sm:w-auto">
          <Play size={18} fill="currentColor" /> Start
        </Link>
      )}
      {done && (
        <Link href={`/practice?mode=personalized&plan=${plan.id}`} className="btn btn-white w-full sm:w-auto">
          <RotateCcw size={18} /> Practise again
        </Link>
      )}
    </div>
  );
}

function StatusChip({ status }: { status: string }) {
  if (status === "pending")
    return (
      <span className="flex items-center gap-1 rounded-full bg-brand-light px-2 py-0.5 font-extrabold text-brand">
        <Loader2 size={12} className="animate-spin" /> Building
      </span>
    );
  if (status === "ready") return <span className="rounded-full bg-brand px-2 py-0.5 font-extrabold text-white">Ready</span>;
  if (status === "failed") return <span className="rounded-full bg-duo-red px-2 py-0.5 font-extrabold text-white">Failed</span>;
  return <span className="rounded-full bg-surface-2 px-2 py-0.5 font-extrabold text-muted">Done</span>;
}

/** Browser notification permission, read without effects so it renders correctly on first paint. */
function subscribe() {
  return () => {};
}
function permission(): string {
  return typeof Notification === "undefined" ? "unsupported" : Notification.permission;
}

function NotifyButton() {
  const initial = useSyncExternalStore(subscribe, permission, () => "unsupported");
  const [state, setState] = useState<string | null>(null);
  const current = state ?? initial;
  if (current === "unsupported" || current === "denied") return null;
  if (current === "granted")
    return (
      <span className="flex items-center gap-2 text-sm font-extrabold text-brand">
        <BellRing size={18} /> Notifications on
      </span>
    );
  return (
    <button
      className="btn btn-white w-full sm:w-auto"
      onClick={async () => {
        try {
          setState(await Notification.requestPermission());
        } catch {
          setState("denied");
        }
      }}
    >
      <Bell size={18} /> Notify me
    </button>
  );
}
