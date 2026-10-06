"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAction, useMe } from "@/lib/hooks";
import type { Me } from "@/lib/types";
import { useToast } from "../ui/Toast";
import { FlagES, Flame, Gem, Heart } from "../ui/Icons";

function useCountdown(iso: string | null) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!iso) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [iso]);
  if (!iso) return null;
  const ms = new Date(iso + "Z").getTime() - now;
  if (ms <= 0) return "any moment";
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  return h ? `${h}h ${m}m` : `${m}m ${Math.floor((ms % 60_000) / 1000)}s`;
}

type Pop = "streak" | "gems" | "hearts" | null;

export default function TopStats({ compact = false }: { compact?: boolean }) {
  const { data: me } = useMe();
  const [open, setOpen] = useState<Pop>(null);
  if (!me) return <div className="h-12" />;
  return (
    <div className={`relative flex items-center ${compact ? "justify-between" : "justify-between gap-2"}`} onMouseLeave={() => setOpen(null)}>
      <Stat onEnter={() => setOpen(null)}>
        <FlagES size={32} />
      </Stat>
      <Stat onEnter={() => setOpen("streak")} label={`${me.streak} day streak`}>
        <Flame size={26} muted={!me.streak_extended_today} />
        <span className={me.streak_extended_today ? "text-duo-orange" : "text-faint"}>{me.streak}</span>
      </Stat>
      <Stat onEnter={() => setOpen("gems")} label={`${me.gems} gems`}>
        <Gem size={24} />
        <span className="text-duo-blue">{me.gems}</span>
      </Stat>
      <Stat onEnter={() => setOpen("hearts")} label={`${me.hearts} hearts`}>
        <Heart size={26} muted={me.hearts === 0} />
        <span className={me.hearts ? "text-duo-red" : "text-faint"}>{me.hearts}</span>
      </Stat>
      {open && (
        <div className="absolute right-0 top-12 z-30 w-[340px] rounded-2xl border-2 border-line bg-surface p-5 shadow-xl">
          {open === "streak" && <StreakPop me={me} />}
          {open === "gems" && <GemsPop me={me} />}
          {open === "hearts" && <HeartsPop me={me} />}
        </div>
      )}
    </div>
  );
}

function Stat({ children, onEnter, label }: { children: React.ReactNode; onEnter: () => void; label?: string }) {
  return (
    <button
      onMouseEnter={onEnter}
      onClick={onEnter}
      aria-label={label}
      className="flex items-center gap-1.5 rounded-xl px-2 py-2 text-[17px] font-extrabold hover:bg-surface-2"
    >
      {children}
    </button>
  );
}

function StreakPop({ me }: { me: Me }) {
  return (
    <div>
      <div className="flex items-center gap-3">
        <Flame size={48} muted={!me.streak_extended_today} />
        <div>
          <div className="text-xl font-extrabold text-ink">{me.streak} day streak</div>
          <div className="text-sm text-muted">
            {me.streak_extended_today ? "You extended your streak today! 🎉" : "Do a lesson today to extend your streak!"}
          </div>
        </div>
      </div>
      <div className="mt-3 rounded-xl bg-surface-2 p-3 text-sm text-muted">
        🧊 {me.streak_freezes} streak freeze{me.streak_freezes === 1 ? "" : "s"} equipped · longest streak {me.longest_streak}
      </div>
    </div>
  );
}

function GemsPop({ me }: { me: Me }) {
  return (
    <div className="flex items-center gap-4">
      <Gem size={52} />
      <div>
        <div className="text-xl font-extrabold text-ink">Gems</div>
        <div className="text-sm text-muted">You have {me.gems} gems.</div>
        <Link href="/shop" className="mt-1 inline-block text-sm font-extrabold uppercase text-duo-blue">
          Go to shop
        </Link>
      </div>
    </div>
  );
}

function HeartsPop({ me }: { me: Me }) {
  const countdown = useCountdown(me.next_heart_at);
  const refill = useAction<void, Me>("/shop/refill-hearts");
  const toast = useToast();
  return (
    <div>
      <div className="text-xl font-extrabold text-ink">Hearts</div>
      <div className="my-3 flex gap-1">
        {Array.from({ length: me.max_hearts }).map((_, i) => (
          <Heart key={i} size={34} muted={i >= me.hearts} />
        ))}
      </div>
      <div className="text-sm text-muted">
        {me.hearts >= me.max_hearts ? "You have full hearts. Keep on learning!" : `Next heart in ${countdown}`}
      </div>
      {me.hearts < me.max_hearts && (
        <div className="mt-4 flex flex-col gap-2">
          <button
            className="btn btn-white w-full justify-between"
            disabled={me.gems < me.refill_cost || refill.isPending}
            onClick={() =>
              refill.mutate(undefined, {
                onSuccess: () => toast({ title: "Hearts refilled!", icon: "❤️", tone: "red" }),
              })
            }
          >
            <span>Refill hearts</span>
            <span className="flex items-center gap-1 text-duo-blue">
              <Gem size={18} /> {me.refill_cost}
            </span>
          </button>
          <Link href="/practice?mode=practice" className="btn btn-white w-full justify-between">
            <span>Practice to earn hearts</span>
            <Heart size={20} />
          </Link>
        </div>
      )}
    </div>
  );
}
