"use client";

import Mascot from "@/components/Mascot";
import AppShell from "@/components/shell/AppShell";
import { QuestRow } from "@/components/shell/RightRail";
import { useQuests } from "@/lib/hooks";
import { Clock, Users } from "lucide-react";

export default function QuestsPage() {
  const { data } = useQuests();
  const hours = 24 - new Date().getHours();
  return (
    <AppShell>
      <div className="mb-6 flex items-center gap-4 rounded-2xl bg-duo-purple p-6 text-white">
        <div className="flex-1">
          <div className="text-sm font-extrabold uppercase opacity-80">October</div>
          <h1 className="text-2xl font-extrabold">Complete quests to earn rewards!</h1>
          <p className="flex items-center gap-1.5 opacity-90"><Clock size={16} /> {hours} hours left today</p>
        </div>
        <Mascot size={96} mood="cheer" />
      </div>
      <h2 className="mb-3 text-xl font-extrabold text-ink">Daily Quests</h2>
      <div className="card space-y-5 p-5">
        {(data || []).map((q) => (
          <QuestRow key={q.key} title={q.title} questKey={q.key} progress={q.progress} target={q.target} />
        ))}
      </div>
      <div className="card mt-6 p-5 text-center text-muted">
        <Users size={32} className="mx-auto text-duo-blue" />
        <div className="mt-2 font-extrabold text-ink">Friends Quests</div>
        Coming soon: team up with a friend to complete quests together.
      </div>
    </AppShell>
  );
}
