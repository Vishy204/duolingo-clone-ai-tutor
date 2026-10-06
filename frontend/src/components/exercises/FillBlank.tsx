"use client";

import { useEffect, useState } from "react";
import { sfx, speak } from "@/lib/sound";
import Mascot from "../Mascot";
import { KeyHint, type ExerciseProps } from "./shared";

export default function FillBlank({ data, disabled, onChange, status }: ExerciseProps<{ choice: string }>) {
  const [picked, setPicked] = useState<string | null>(null);
  const [before, after] = (data.sentence as string).split("___");
  const choices: string[] = data.choices;

  const pick = (c: string) => {
    if (disabled) return;
    sfx.tap();
    const next = picked === c ? null : c;
    setPicked(next);
    onChange(next ? { choice: next } : null);
    if (next) speak(`${before}${next}${after}`);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const n = Number(e.key);
      if (n >= 1 && n <= choices.length) pick(choices[n - 1]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const blankCls = status === "correct" ? "tile-correct" : status === "wrong" ? "tile-wrong" : "";
  return (
    <div>
      <h2 className="mb-6 text-2xl font-extrabold text-ink sm:text-[28px]">Fill in the blank</h2>
      <div className="flex items-center gap-4">
        <Mascot size={96} mood="think" />
        <div>
          <div className="flex flex-wrap items-center gap-2 text-2xl text-ink">
            <span>{before}</span>
            <span className={`inline-flex min-w-[90px] justify-center border-b-[3px] border-line px-2 pb-1 ${picked ? "" : "text-transparent"}`}>
              {picked ? <span className={`tile px-3 py-1 ${blankCls}`}>{picked}</span> : "____"}
            </span>
            <span>{after}</span>
          </div>
          {data.translation && <div className="mt-2 text-muted">{data.translation}</div>}
        </div>
      </div>
      <div className="mt-10 flex flex-wrap justify-center gap-3">
        {choices.map((c, i) => (
          <button
            key={c}
            disabled={disabled}
            onClick={() => pick(c)}
            className={`tile flex h-[56px] items-center gap-3 px-5 text-lg ${picked === c ? "tile-done text-transparent" : ""}`}
          >
            <KeyHint n={i + 1} />
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}
