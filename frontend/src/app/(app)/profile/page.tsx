"use client";

import AppShell from "@/components/shell/AppShell";
import { Crown, Flame } from "@/components/ui/Icons";
import { useProfile } from "@/lib/hooks";

export default function ProfilePage() {
  const { data } = useProfile();
  if (!data) return <AppShell><div className="h-96 animate-pulse rounded-2xl bg-line" /></AppShell>;
  const { user, stats, achievements, xp_history, active_days, mastery } = data;
  const maxXp = Math.max(10, ...xp_history.map((d) => d.xp));
  return (
    <AppShell>
      <div className="flex items-center gap-6 border-b-2 border-line pb-6 pt-2">
        <div className="grid h-28 w-28 place-items-center rounded-full border-4 border-dashed text-5xl font-extrabold text-white" style={{ background: user.avatar_color, borderColor: user.avatar_color }}>
          {user.display_name[0]}
        </div>
        <div>
          <h1 className="text-[28px] font-extrabold text-ink">{user.display_name}</h1>
          <div className="text-muted">@{user.username}</div>
          <div className="text-sm text-muted">Joined {stats.joined} · Learning Spanish</div>
        </div>
      </div>

      <h2 className="mb-3 mt-6 text-2xl font-extrabold text-ink">Statistics</h2>
      <div className="grid grid-cols-2 gap-3">
        <Stat icon={<Flame size={28} />} value={user.streak} label="Day streak" />
        <Stat icon={<span className="text-2xl">⚡</span>} value={user.total_xp} label="Total XP" />
        <Stat icon={<Crown size={28} />} value={stats.skills} label="Levels completed" />
        <Stat icon={<span className="text-2xl">📘</span>} value={stats.lessons} label="Lessons" />
        <Stat icon={<span className="text-2xl">🎯</span>} value={stats.perfect} label="Perfect lessons" />
        <Stat icon={<span className="text-2xl">🏅</span>} value={user.longest_streak} label="Longest streak" />
      </div>

      <h2 className="mb-3 mt-8 text-2xl font-extrabold text-ink">XP this week</h2>
      <div className="card flex h-44 items-end gap-3 p-5">
        {xp_history.map((d) => (
          <div key={d.day} className="flex flex-1 flex-col items-center gap-1">
            <span className="text-xs text-muted">{d.xp || ""}</span>
            <div className="w-full rounded-t-lg bg-duo-yellow" style={{ height: `${(d.xp / maxXp) * 100}px`, minHeight: d.xp ? 6 : 2 }} />
            <span className="text-xs text-faint">{new Date(d.day + "T00:00").toLocaleDateString(undefined, { weekday: "short" })}</span>
          </div>
        ))}
      </div>

      <h2 className="mb-3 mt-8 text-2xl font-extrabold text-ink">Streak calendar</h2>
      <div className="card grid grid-cols-7 gap-2 p-5">
        {Array.from({ length: 35 }).map((_, i) => {
          const day = new Date(new Date(user.today + "T00:00").getTime() - (34 - i) * 86400000);
          const iso = day.toISOString().slice(0, 10);
          const on = active_days.includes(iso);
          return (
            <div key={i} title={iso} className={`grid aspect-square place-items-center rounded-full text-xs ${on ? "bg-duo-orange text-white" : "text-faint"}`}>
              {day.getDate()}
            </div>
          );
        })}
      </div>

      <h2 className="mb-3 mt-8 text-2xl font-extrabold text-ink">Achievements</h2>
      <div className="card divide-y-2 divide-line">
        {achievements.map((a) => (
          <div key={a.key} className={`flex items-center gap-4 p-4 ${a.unlocked ? "" : "opacity-60"}`}>
            <div className="grid h-16 w-14 place-items-center rounded-xl text-3xl" style={{ background: a.unlocked ? a.color : "var(--locked)" }}>
              {a.icon}
            </div>
            <div className="flex-1">
              <div className="font-extrabold text-ink">{a.title}</div>
              <div className="text-sm text-muted">{a.description}</div>
              <div className="mt-1 h-3 rounded-full bg-line">
                <div className="h-3 rounded-full bg-duo-yellow" style={{ width: `${((a.progress ?? 0) / (a.threshold ?? 1)) * 100}%` }} />
              </div>
            </div>
            <span className="text-sm text-muted">{a.progress}/{a.threshold}</span>
          </div>
        ))}
      </div>

      <h2 className="mb-3 mt-8 text-2xl font-extrabold text-ink">What Duo knows about you</h2>
      <div className="card space-y-3 p-5">
        {mastery.map((m) => (
          <div key={m.concept_key}>
            <div className="flex justify-between text-sm">
              <span className="text-ink">{m.name}</span>
              <span className="text-muted">{m.level}</span>
            </div>
            <div className="mt-1 h-2.5 rounded-full bg-line">
              <div className="h-2.5 rounded-full bg-duo-blue" style={{ width: `${Math.max(4, m.mastery * 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}

function Stat({ icon, value, label }: { icon: React.ReactNode; value: number | string; label: string }) {
  return (
    <div className="card flex items-center gap-3 p-4">
      {icon}
      <div>
        <div className="text-xl font-extrabold text-ink">{value}</div>
        <div className="text-sm text-muted">{label}</div>
      </div>
    </div>
  );
}
