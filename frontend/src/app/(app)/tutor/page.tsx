"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Brain, MessageCircle } from "lucide-react";
import AppShell from "@/components/shell/AppShell";
import ChatPanel from "@/components/tutor/ChatPanel";
import TutorBrain from "@/components/tutor/TutorBrain";
import VoiceDuo from "@/components/tutor/VoiceDuo";

const TABS = [
  { key: "talk", label: "Talk to Smarto", Icon: MessageCircle },
  { key: "learn", label: "How Smarto learns", Icon: Brain },
] as const;
type Tab = (typeof TABS)[number]["key"];

export default function TutorPage() {
  return (
    <AppShell rail={false} wide>
      <Suspense fallback={null}>
        <TutorTabs />
      </Suspense>
    </AppShell>
  );
}

function TutorTabs() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const tab: Tab = params.get("tab") === "learn" ? "learn" : "talk";

  return (
    <div className="pt-2">
      <div role="tablist" className="mb-6 flex gap-2 rounded-2xl border-2 border-line p-1.5">
        {TABS.map((t) => {
          const active = t.key === tab;
          return (
            <button
              key={t.key}
              role="tab"
              aria-selected={active}
              onClick={() => router.replace(`${pathname}?tab=${t.key}`, { scroll: false })}
              className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-3 text-[15px] font-extrabold uppercase tracking-wide transition-colors ${
                active ? "bg-brand-light text-brand border-2 border-brand-border" : "border-2 border-transparent text-muted hover:bg-surface-2"
              }`}
            >
              <t.Icon size={20} strokeWidth={2.5} /> {t.label}
            </button>
          );
        })}
      </div>

      {tab === "talk" ? (
        <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
          <ChatPanel />
          <VoiceDuo />
        </div>
      ) : (
        <TutorBrain />
      )}
    </div>
  );
}
