"use client";

import AppShell from "@/components/shell/AppShell";
import { NavLeague } from "@/components/ui/Icons";
import { useLeaderboard } from "@/lib/hooks";

const MEDALS = ["🥇", "🥈", "🥉"];

export default function LeaderboardPage() {
  const { data } = useLeaderboard();
  return (
    <AppShell>
      <div className="flex flex-col items-center border-b-2 border-line pb-6 pt-2 text-center">
        <div className="mb-3 flex items-end gap-3">
          {["#CD7F32", "#C0C0C0", "#FFC800", "#1CB0F6", "#CE82FF"].map((c, i) => (
            <div key={c} style={{ opacity: i === 0 ? 1 : 0.35, transform: i === 0 ? "scale(1.25)" : undefined }}>
              <svg width="52" height="60" viewBox="0 0 32 36" aria-hidden>
                <path d="M16 1l14 5v11c0 9-7 15-14 18C9 32 2 26 2 17V6z" fill={c} />
                <path d="M16 6l9 3v8c0 6-4 10-9 12z" fill="#000" opacity={0.12} />
              </svg>
            </div>
          ))}
        </div>
        <h1 className="text-2xl font-extrabold text-ink">{data?.league.name || "League"}</h1>
        <p className="text-muted">Top {data?.league.promote ?? 5} advance to the next league</p>
        <p className="mt-1 font-extrabold text-duo-yellow">{data?.days_left ?? "–"} days left</p>
      </div>
      <div className="mt-2">
        {(data?.rows || []).map((r) => (
          <div key={r.user_id}>
            <div
              className={`flex items-center gap-4 rounded-2xl px-4 py-3 ${r.is_me ? "bg-duo-green-light" : "hover:bg-surface-2"}`}
            >
              <span className={`w-8 text-center text-lg font-extrabold ${r.rank <= 3 ? "" : "text-muted"}`}>
                {MEDALS[r.rank - 1] || r.rank}
              </span>
              <span className="grid h-12 w-12 place-items-center rounded-full text-xl font-extrabold text-white" style={{ background: r.avatar_color }}>
                {r.name[0]}
              </span>
              <span className={`flex-1 text-lg ${r.is_me ? "text-duo-green-dark" : "text-ink"}`}>
                {r.name} {r.is_me && "(you)"}
              </span>
              <span className="text-muted">{r.xp} XP</span>
            </div>
            {data && r.rank === data.league.promote && (
              <div className="my-2 flex items-center gap-3 text-sm font-extrabold uppercase text-duo-green">
                <span className="h-0.5 flex-1 bg-duo-green/40" /> ⬆ Promotion zone <span className="h-0.5 flex-1 bg-duo-green/40" />
              </div>
            )}
            {data && r.rank === data.rows.length - data.league.demote && (
              <div className="my-2 flex items-center gap-3 text-sm font-extrabold uppercase text-duo-red">
                <span className="h-0.5 flex-1 bg-duo-red/40" /> ⬇ Demotion zone <span className="h-0.5 flex-1 bg-duo-red/40" />
              </div>
            )}
          </div>
        ))}
      </div>
      {!data && (
        <div className="grid place-items-center py-16">
          <NavLeague size={64} />
        </div>
      )}
    </AppShell>
  );
}
