"use client";

import { useRef, useState } from "react";
import { SpeechBubble, type ExerciseProps } from "./shared";

const SPECIAL = ["á", "é", "í", "ó", "ú", "ñ", "ü", "¿", "¡"];

export default function TypeAnswer({ data, disabled, onChange }: ExerciseProps<{ text: string }>) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const toSpanish = data.target_lang === "es";

  const set = (v: string) => {
    setText(v);
    onChange(v.trim() ? { text: v } : null);
  };

  return (
    <div>
      <h2 className="mb-4 text-2xl font-extrabold text-ink sm:text-[28px]">Type this in {toSpanish ? "Spanish" : "English"}</h2>
      <SpeechBubble text={data.source} lang={data.source_lang} />
      <textarea
        ref={ref}
        autoFocus
        disabled={disabled}
        value={text}
        onChange={(e) => set(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") e.preventDefault(); // Enter is "Check" (handled by the player)
        }}
        placeholder={`Type in ${toSpanish ? "Spanish" : "English"}`}
        className="mt-2 h-36 w-full resize-none rounded-2xl border-2 border-line bg-surface-2 p-4 text-lg text-ink outline-none focus:border-brand-border"
        spellCheck={false}
        autoCapitalize="off"
        autoComplete="off"
      />
      {toSpanish && (
        <div className="mt-3 flex flex-wrap gap-2">
          {SPECIAL.map((ch) => (
            <button
              key={ch}
              disabled={disabled}
              onClick={() => {
                const el = ref.current;
                const pos = el?.selectionStart ?? text.length;
                set(text.slice(0, pos) + ch + text.slice(pos));
                requestAnimationFrame(() => {
                  el?.focus();
                  el?.setSelectionRange(pos + 1, pos + 1);
                });
              }}
              className="tile h-10 w-10 text-lg"
            >
              {ch}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
