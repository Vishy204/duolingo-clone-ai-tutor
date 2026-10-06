"use client";

import { useEffect, useRef } from "react";
import { useInsights, useInvalidateLearner, useMe } from "@/lib/hooks";
import { setSoundEnabled } from "@/lib/sound";
import { useToast } from "../ui/Toast";
import RightRail from "./RightRail";
import Sidebar, { MobileNav } from "./Sidebar";
import TopStats from "./TopStats";
import { Snowflake, Sparkles } from "lucide-react";

/** Applies learner preferences (theme, sound) and announces new tutor plans. */
export function useLearnerEffects() {
  const { data: me } = useMe();
  const { data: insights } = useInsights();
  const toast = useToast();
  const invalidate = useInvalidateLearner();
  const lastPlan = useRef<number | null>(null);

  useEffect(() => {
    if (!me) return;
    document.documentElement.dataset.theme = me.settings.dark_mode ? "dark" : "light";
    try {
      localStorage.setItem("duo_theme", me.settings.dark_mode ? "dark" : "light");
    } catch {
      /* ignore */
    }
    setSoundEnabled(me.settings.sound !== false);
    if (me.streak_events?.streak_lost) {
      toast({ title: "Your streak was reset", body: "Start a new one today!", icon: <Snowflake className="text-duo-blue" />, tone: "blue" });
    } else if (me.streak_events?.freezes_used) {
      toast({ title: "Streak freeze used!", body: "Your streak is safe.", icon: <Snowflake className="text-duo-blue" />, tone: "blue" });
    }
  }, [me, toast]);

  useEffect(() => {
    const id = insights?.ready_plan?.id ?? null;
    if (id && lastPlan.current !== null && id !== lastPlan.current) {
      toast({ title: "Smarto built you a new practice!", body: insights?.ready_plan?.summary || "", icon: <Sparkles className="text-duo-purple" />, tone: "purple" });
      invalidate();
    }
    if (id) lastPlan.current = id;
  }, [insights?.ready_plan?.id, insights?.ready_plan?.summary, toast, invalidate]);
}

export default function AppShell({ children, rail = true, wide = false }: { children: React.ReactNode; rail?: boolean; wide?: boolean }) {
  useLearnerEffects();
  return (
    <div className="flex min-h-screen w-full justify-center">
      <Sidebar />
      <div className="flex min-w-0 flex-1 justify-center gap-6 lg:gap-10">
        <main className={`w-full ${wide ? "max-w-[1080px]" : "max-w-[640px]"} min-w-0 px-4 pb-24 pt-4 md:px-6 md:pb-10`}>
          <div className="sticky top-0 z-[160] -mx-4 mb-2 bg-bg px-4 py-2 lg:hidden">
            <TopStats compact />
          </div>
          {children}
        </main>
        {rail && <RightRail />}
      </div>
      <MobileNav />
    </div>
  );
}
