"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import Mascot from "@/components/Mascot";
import AppShell from "@/components/shell/AppShell";

const COPY: Record<string, string> = {
  speaking: "Pronunciation exercises with speech recognition",
  friends: "Follow friends and compete together",
  super: "Super: unlimited hearts and no ads",
  courses: "More language courses",
  notifications: "Practice reminders",
};

export default function ComingSoon() {
  const { feature } = useParams<{ feature: string }>();
  return (
    <AppShell>
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <Mascot mood="think" size={160} />
        <h1 className="text-2xl font-extrabold text-ink">Coming soon!</h1>
        <p className="max-w-sm text-muted">{COPY[feature] || "This feature"} isn&apos;t part of this clone yet. Smarto is working on it.</p>
        <Link href="/learn" className="btn btn-brand mt-2 w-56">Back to learning</Link>
      </div>
    </AppShell>
  );
}
