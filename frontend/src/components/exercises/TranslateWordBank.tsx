"use client";

import { LayoutGroup, motion } from "motion/react";
import { useState } from "react";
import { sfx, speak } from "@/lib/sound";
import { SpeechBubble, type ExerciseProps } from "./shared";

type Answer = { tokens: string[] } | { text: string };

/** "Write this in Spanish": tap word tiles into the answer line (or switch to the keyboard). */
export default function TranslateWordBank({ data, disabled, onChange }: ExerciseProps<Answer>) {
  const bank: string[] = data.bank;
  const [chosen, setChosen] = useState<number[]>([]);
  const [keyboard, setKeyboard] = useState(false);
  const [text, setText] = useState("");

  const update = (next: number[]) => {
    setChosen(next);
    onChange(next.length ? { tokens: next.map((i) => bank[i]) } : null);
  };

  return (
    <div>
      <h2 className="mb-4 text-2xl font-extrabold text-ink sm:text-[28px]">
        Write this in {data.target_lang === "es" ? "Spanish" : "English"}
      </h2>
      <SpeechBubble text={data.source} lang={data.source_lang} />

      {keyboard ? (
        <textarea
          autoFocus
          disabled={disabled}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            onChange(e.target.value.trim() ? { text: e.target.value } : null);
          }}
          placeholder={`Type in ${data.target_lang === "es" ? "Spanish" : "English"}`}
          className="mt-2 h-36 w-full resize-none rounded-2xl border-2 border-line bg-surface-2 p-4 text-lg text-ink outline-none focus:border-duo-blue-border"
        />
      ) : (
        <LayoutGroup>
          <div className="ruled mt-2 flex min-h-[124px] flex-wrap content-start gap-2 py-2">
            {chosen.map((i) => (
              <motion.button
                layoutId={`tile-${i}`}
                key={i}
                disabled={disabled}
                onClick={() => {
                  sfx.tap();
                  update(chosen.filter((x) => x !== i));
                }}
                className="tile h-[50px] px-4 text-lg"
              >
                {bank[i]}
              </motion.button>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap justify-center gap-2">
            {bank.map((word, i) => (
              <div key={i} className="relative h-[50px] rounded-xl bg-line">
                <span className="invisible block px-4 text-lg">{word}</span>
                {!chosen.includes(i) && (
                  <motion.button
                    layoutId={`tile-${i}`}
                    disabled={disabled}
                    onClick={() => {
                      sfx.tap();
                      if (data.target_lang === "es") speak(word);
                      update([...chosen, i]);
                    }}
                    className="tile absolute inset-0 text-lg"
                  >
                    {word}
                  </motion.button>
                )}
              </div>
            ))}
          </div>
        </LayoutGroup>
      )}
      <div className="mt-6 text-center">
        <button
          disabled={disabled}
          onClick={() => {
            setKeyboard((k) => !k);
            update([]);
            setText("");
          }}
          className="text-sm font-extrabold uppercase tracking-wide text-faint hover:text-muted"
        >
          {keyboard ? "Use word bank" : "Use keyboard"}
        </button>
      </div>
    </div>
  );
}
