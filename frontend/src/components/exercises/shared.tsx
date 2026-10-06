"use client";

import Mascot from "../Mascot";
import { Speaker } from "../ui/Icons";
import { speak } from "@/lib/sound";

/** Smarto with a speech bubble holding the source sentence (translate / type exercises). */
export function SpeechBubble({ text, lang }: { text: string; lang: "es" | "en" }) {
  const isSpanish = lang === "es";
  return (
    <div className="flex items-end gap-3">
      <Mascot size={110} mood="talk" />
      <div className="relative mb-8 rounded-2xl border-2 border-line px-4 py-3 text-lg text-ink">
        <div className="absolute -left-[9px] bottom-5 h-4 w-4 rotate-45 border-b-2 border-l-2 border-line bg-surface" />
        <div className="flex items-center gap-2">
          {isSpanish && (
            <button onClick={() => speak(text)} aria-label="Listen" className="shrink-0 rounded-lg p-1 hover:bg-surface-2">
              <Speaker size={24} />
            </button>
          )}
          <span className={isSpanish ? "underline decoration-dotted decoration-2 underline-offset-[6px] decoration-line" : ""}>{text}</span>
        </div>
      </div>
    </div>
  );
}

export function KeyHint({ n }: { n: number }) {
  return (
    <span className="hidden h-7 w-7 shrink-0 place-items-center rounded-lg border-2 border-line text-sm text-faint sm:grid">
      {n}
    </span>
  );
}

export type ExerciseProps<A> = {
  data: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  disabled: boolean;
  onChange: (answer: A | null) => void;
  status?: "correct" | "wrong" | null;
};
