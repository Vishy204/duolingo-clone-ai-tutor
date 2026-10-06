"use client";

import LearningPath from "@/components/path/LearningPath";
import AppShell from "@/components/shell/AppShell";
import VoiceDuo from "@/components/tutor/VoiceDuo";

export default function LearnPage() {
  return (
    <AppShell>
      <LearningPath />
      <VoiceDuo variant="fab" />
    </AppShell>
  );
}
