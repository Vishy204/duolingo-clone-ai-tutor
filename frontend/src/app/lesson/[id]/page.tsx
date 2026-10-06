"use client";

import { useParams } from "next/navigation";
import { useCallback } from "react";
import LessonPlayer from "@/components/lesson/LessonPlayer";
import { post } from "@/lib/api";
import type { SessionData } from "@/lib/types";

export default function LessonPage() {
  const { id } = useParams<{ id: string }>();
  const start = useCallback(() => post<SessionData>("/sessions", { mode: "lesson", lesson_id: Number(id) }), [id]);
  return <LessonPlayer start={start} />;
}
