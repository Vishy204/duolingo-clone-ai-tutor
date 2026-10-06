"use client";

import { useEffect, useState } from "react";
import { sfx, speak } from "@/lib/sound";
import { KeyHint, type ExerciseProps } from "./shared";

type Choice = { text: string; emoji?: string | null };

export default function MultipleChoice({ data, disabled, onChange, status }: ExerciseProps<{ choice: number }>) {
  const [picked, setPicked] = useState<number | null>(null);
  const choices: Choice[] = data.choices;
  const withPictures = choices.every((c) => c.emoji);

  const pick = (i: number) => {
    if (disabled) return;
    sfx.tap();
    speak(choices[i].text);
    setPicked(i);
    onChange({ choice: i });
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const n = Number(e.key);
      if (n >= 1 && n <= choices.length) pick(n - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  return (
    <div>
      <h2 className="mb-6 text-2xl font-extrabold text-ink sm:text-[28px]">{data.question}</h2>
      <div className={withPictures ? "grid grid-cols-2 gap-3 sm:grid-cols-3" : "flex flex-col gap-3"}>
        {choices.map((c, i) => {
          const sel = picked === i;
          const cls = sel ? (status === "correct" ? "tile-correct" : status === "wrong" ? "tile-wrong" : "tile-selected") : "";
          return withPictures ? (
            <button key={i} disabled={disabled} onClick={() => pick(i)}
              className={`tile flex flex-col items-center justify-between gap-2 p-4 ${cls} ${sel && status === "wrong" ? "animate-shake" : ""}`}>
              <span className="py-3 text-6xl sm:text-7xl">{c.emoji}</span>
              <span className="flex w-full items-center justify-between text-lg">
                <span>{c.text}</span>
                <KeyHint n={i + 1} />
              </span>
            </button>
          ) : (
            <button key={i} disabled={disabled} onClick={() => pick(i)}
              className={`tile flex items-center gap-4 p-4 text-left text-lg ${cls}`}>
              <KeyHint n={i + 1} />
              {c.emoji && <span className="text-2xl">{c.emoji}</span>}
              <span>{c.text}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
