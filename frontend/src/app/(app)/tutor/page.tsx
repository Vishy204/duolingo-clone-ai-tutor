"use client";

import AppShell from "@/components/shell/AppShell";
import ChatPanel from "@/components/tutor/ChatPanel";
import TutorBrain from "@/components/tutor/TutorBrain";
import VoiceDuo from "@/components/tutor/VoiceDuo";

export default function TutorPage() {
  return (
    <AppShell rail={false} wide>
      <div className="space-y-8 pt-2">
        <TutorBrain />
        <section>
          <h2 className="mb-1 text-2xl font-extrabold text-ink">Ask Duo</h2>
          <p className="mb-4 text-muted">
            Text chat runs on the Agents SDK (Duo calls the analyst as a tool and can build practice for you). Voice runs
            on a real-time Pipecat pipeline tuned for speed.
          </p>
          <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
            <ChatPanel />
            <VoiceDuo />
          </div>
        </section>
      </div>
    </AppShell>
  );
}
