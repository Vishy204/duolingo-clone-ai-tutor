"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useCallback } from "react";
import LessonPlayer from "@/components/lesson/LessonPlayer";
import { post } from "@/lib/api";
import type { SessionData } from "@/lib/types";

function Practice() {
  const params = useSearchParams();
  const mode = (params.get("mode") || "practice") as SessionData["mode"];
  const skill = params.get("skill");
  const start = useCallback(
    () => post<SessionData>("/sessions", { mode, skill_id: skill ? Number(skill) : null }),
    [mode, skill],
  );
  return <LessonPlayer key={`${mode}-${skill}`} start={start} />;
}

export default function PracticePage() {
  return (
    <Suspense>
      <Practice />
    </Suspense>
  );
}
