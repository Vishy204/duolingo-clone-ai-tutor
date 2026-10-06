"use client";

import Link from "next/link";
import { useInsights, useLeaderboard, useMe, useQuests } from "@/lib/hooks";
import Mascot from "../Mascot";
import { NavLeague, Sparkle } from "../ui/Icons";
import TopStats from "./TopStats";

export default function RightRail({ showStats = true }: { showStats?: boolean }) {
  return (
    <aside className="sticky top-0 hidden h-screen w-[368px] shrink-0 flex-col gap-5 overflow-y-auto px-6 py-6 no-scrollbar lg:flex [&>*]:shrink-0">
      {showStats && <TopStats />}
      <DuoInsightsCard />
      <DailyGoalCard />
      <QuestsCard />
      <LeagueCard />
      <footer className="flex flex-wrap justify-center gap-x-4 gap-y-1 pb-4 text-xs font-extrabold uppercase text-faint">
        <span>About</span>
        <span>Blog</span>
        <span>Help</span>
        <span>Privacy</span>
      </footer>
    </aside>
  );
}

export function DuoInsightsCard() {
  const { data } = useInsights();
  if (!data) return <div className="card h-40 animate-pulse" />;
  const plan = data.ready_plan;
  return (
    <div className="card relative overflow-hidden border-duo-purple p-5">
      <div className="mb-2 flex items-center gap-2 text-sm font-extrabold uppercase tracking-wide text-duo-purple">
        <Sparkle /> Duo&apos;s insights
        {data.running && <span className="ml-auto animate-pulse text-xs normal-case text-muted">thinking…</span>}
      </div>
      <div className="flex gap-3">
        <div className="shrink-0">
          <Mascot size={64} mood={data.running ? "think" : "happy"} />
        </div>
        <div className="text-[15px] leading-snug text-ink">
          {plan?.summary || "Finish a lesson and I'll analyse your answers to build practice just for you!"}
        </div>
      </div>
      {data.weakest.length > 0 && (
        <div className="mt-4 space-y-2">
          {data.weakest.slice(0, 3).map((m) => (
            <div key={m.concept_key}>
              <div className="flex justify-between text-xs text-muted">
                <span>{m.friendly || m.name}</span>
                <span>{Math.round(m.mastery * 100)}%</span>
              </div>
              <div className="h-2.5 rounded-full bg-line">
                <div
                  className="h-2.5 rounded-full"
                  style={{ width: `${Math.max(6, m.mastery * 100)}%`, background: m.mastery < 0.35 ? "#FF4B4B" : m.mastery < 0.55 ? "#FF9600" : "#58CC02" }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="mt-4 flex gap-2">
        {plan && (
          <Link href="/practice?mode=personalized" className="btn btn-purple h-11 flex-1 text-[13px]">
            Start ({plan.exercise_count})
          </Link>
        )}
        <Link href="/tutor?tab=learn" className="btn btn-white h-11 flex-1 text-[13px]">
          See how
        </Link>
      </div>
    </div>
  );
}

export function DailyGoalCard() {
  const { data: me } = useMe();
  if (!me) return null;
  const pct = Math.min(100, (me.xp_today / me.daily_goal_xp) * 100);
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xl font-extrabold text-ink">Daily goal</h3>
        <Link href="/settings" className="text-sm font-extrabold uppercase text-duo-blue">Edit</Link>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-4xl">⚡</span>
        <div className="flex-1">
          <div className="relative h-4 rounded-full bg-line">
            <div className="h-4 rounded-full bg-duo-yellow transition-all" style={{ width: `${pct}%` }} />
          </div>
          <div className="mt-1 text-sm text-muted">
            {me.xp_today} / {me.daily_goal_xp} XP {pct >= 100 && "· Goal reached! 🎉"}
          </div>
        </div>
      </div>
    </div>
  );
}

export function QuestsCard() {
  const { data } = useQuests();
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xl font-extrabold text-ink">Daily Quests</h3>
        <Link href="/quests" className="text-sm font-extrabold uppercase text-duo-blue">View all</Link>
      </div>
      <div className="space-y-4">
        {(data || []).slice(0, 3).map((q) => (
          <QuestRow key={q.key} title={q.title} icon={q.icon} progress={q.progress} target={q.target} />
        ))}
      </div>
    </div>
  );
}

export function QuestRow({ title, icon, progress, target }: { title: string; icon: string; progress: number; target: number }) {
  const done = progress >= target;
  return (
    <div className="flex items-center gap-3">
      <span className="text-3xl">{icon}</span>
      <div className="flex-1">
        <div className="mb-1.5 text-[15px] text-ink">{title}</div>
        <div className="relative h-4 rounded-full bg-line">
          <div className={`h-4 rounded-full ${done ? "bg-duo-green" : "bg-duo-yellow"}`} style={{ width: `${(progress / target) * 100}%` }} />
          <span className="absolute inset-0 grid place-items-center text-[11px] text-faint mix-blend-multiply">
            {progress} / {target}
          </span>
        </div>
      </div>
      <span className="text-2xl">{done ? "🎁" : "📦"}</span>
    </div>
  );
}

function LeagueCard() {
  const { data } = useLeaderboard();
  const me = data?.rows.find((r) => r.is_me);
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xl font-extrabold text-ink">{data?.league.name || "League"}</h3>
        <Link href="/leaderboard" className="text-sm font-extrabold uppercase text-duo-blue">View league</Link>
      </div>
      <div className="flex items-center gap-4">
        <NavLeague size={48} />
        <div className="text-[15px] text-muted">
          {me ? (
            <>
              You&apos;re ranked <span className="font-extrabold text-ink">#{me.rank}</span> with {me.xp} XP this week.
            </>
          ) : (
            "Loading…"
          )}
        </div>
      </div>
    </div>
  );
}
