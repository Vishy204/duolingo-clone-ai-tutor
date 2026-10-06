"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import AppShell from "@/components/shell/AppShell";
import { useToast } from "@/components/ui/Toast";
import { patch, post, resetLearner } from "@/lib/api";
import { useInvalidateLearner, useMe } from "@/lib/hooks";
import type { Me } from "@/lib/types";

const GOALS = [
  { xp: 10, label: "Casual" },
  { xp: 20, label: "Regular" },
  { xp: 30, label: "Serious" },
  { xp: 50, label: "Intense" },
];

export default function SettingsPage() {
  const { data: me } = useMe();
  const invalidate = useInvalidateLearner();
  const toast = useToast();
  const router = useRouter();
  const [name, setName] = useState<string | null>(null);

  const save = async (body: Record<string, unknown>) => {
    await patch<Me>("/me/settings", body);
    invalidate();
  };

  if (!me) return <AppShell><div className="h-96 animate-pulse rounded-2xl bg-line" /></AppShell>;
  return (
    <AppShell>
      <h1 className="mb-6 mt-2 text-2xl font-extrabold text-ink">Settings</h1>

      <Section title="Profile">
        <label className="block text-sm text-muted">Name</label>
        <div className="mt-1 flex gap-2">
          <input
            value={name ?? me.display_name}
            maxLength={40}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 rounded-xl border-2 border-line bg-surface-2 px-4 py-3 text-ink outline-none focus:border-duo-blue-border"
          />
          <button className="btn btn-blue" disabled={!name || name === me.display_name} onClick={() => save({ display_name: name }).then(() => toast({ title: "Saved!", icon: "✅" }))}>
            Save
          </button>
        </div>
      </Section>

      <Section title="Daily goal">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {GOALS.map((g) => (
            <button key={g.xp} onClick={() => save({ daily_goal_xp: g.xp })} className={`tile p-3 ${me.daily_goal_xp === g.xp ? "tile-selected" : ""}`}>
              <div className="font-extrabold">{g.label}</div>
              <div className="text-sm opacity-80">{g.xp} XP / day</div>
            </button>
          ))}
        </div>
      </Section>

      <Section title="Preferences">
        <Toggle label="Sound effects" on={me.settings.sound !== false} onChange={(v) => save({ sound: v })} />
        <Toggle label="Dark mode" on={!!me.settings.dark_mode} onChange={(v) => save({ dark_mode: v })} />
      </Section>

      {me.demo_mode && (
        <Section title="Demo tools (for reviewers)">
          <p className="mb-3 text-sm text-muted">
            Streaks are day-based. &quot;Simulate next day&quot; moves your clock forward 24h (currently day +{me.clock_offset_days}) so you can
            watch a streak extend, freeze or reset, hearts regenerate and quests roll over.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              className="btn btn-white"
              onClick={async () => {
                const r = await post<Me>("/dev/advance-day");
                invalidate();
                toast({ title: `It's now ${r.today}`, body: r.streak ? `Streak: ${r.streak}` : "Your streak needs a lesson today!", icon: "📅", tone: "blue" });
              }}
            >
              Simulate next day
            </button>
            <button
              className="btn btn-ghost"
              onClick={() => {
                resetLearner();
                router.push("/");
              }}
            >
              Start over as a new learner
            </button>
          </div>
        </Section>
      )}

      <Section title="Coming soon">
        <div className="flex flex-wrap gap-2">
          {[
            ["speaking", "🎤 Speaking exercises"],
            ["friends", "🤝 Friends"],
            ["super", "⭐ Super"],
            ["courses", "🌍 More languages"],
            ["notifications", "🔔 Notifications"],
          ].map(([k, label]) => (
            <Link key={k} href={`/soon/${k}`} className="rounded-xl border-2 border-line px-3 py-2 text-sm text-muted hover:bg-surface-2">
              {label}
            </Link>
          ))}
        </div>
      </Section>
    </AppShell>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="mb-3 text-lg font-extrabold text-ink">{title}</h2>
      <div className="card p-5">{children}</div>
    </section>
  );
}

function Toggle({ label, on, onChange }: { label: string; on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button onClick={() => onChange(!on)} className="flex w-full items-center justify-between py-2" role="switch" aria-checked={on}>
      <span className="text-ink">{label}</span>
      <span className={`relative h-8 w-14 rounded-full transition-colors ${on ? "bg-duo-blue" : "bg-line"}`}>
        <span className={`absolute top-1 h-6 w-6 rounded-full bg-white shadow transition-all ${on ? "left-7" : "left-1"}`} />
      </span>
    </button>
  );
}
