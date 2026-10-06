"use client";

import { useEffect, useState } from "react";
import { sfx, speak } from "@/lib/sound";
import { KeyHint, type ExerciseProps } from "./shared";

type Choice = { text: string };

export default function MultipleChoice({ data, disabled, onChange, status }: ExerciseProps<{ choice: number }>) {
  const [picked, setPicked] = useState<number | null>(null);
  const choices: Choice[] = data.choices;

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
      <div className="flex flex-col gap-3">
        {choices.map((c, i) => {
          const sel = picked === i;
          const cls = sel ? (status === "correct" ? "tile-correct" : status === "wrong" ? "tile-wrong" : "tile-selected") : "";
          return (
            <button key={i} disabled={disabled} onClick={() => pick(i)}
              className={`tile flex items-center gap-4 p-4 text-left text-lg ${cls} ${sel && status === "wrong" ? "animate-shake" : ""}`}>
              <KeyHint n={i + 1} />
              <span>{c.text}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
