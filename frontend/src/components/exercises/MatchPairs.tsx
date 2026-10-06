"use client";

import { useState } from "react";
import { sfx, speak } from "@/lib/sound";
import { KeyHint } from "./shared";

type Item = { id: number; text: string };

/**
 * "Select the matching pairs": matching is checked tap-by-tap on the client (like Duolingo);
 * when every pair is found we submit the number of mismatches so the tutor can learn from them.
 */
export default function MatchPairs({ data, disabled, onDone }: { data: { left: Item[]; right: Item[] }; disabled: boolean; onDone: (mistakes: number) => void }) {
  const [sel, setSel] = useState<{ side: "l" | "r"; id: number } | null>(null);
  const [matched, setMatched] = useState<number[]>([]);
  const [flash, setFlash] = useState<{ ids: string[]; ok: boolean } | null>(null);
  const [mistakes, setMistakes] = useState(0);

  const tap = (side: "l" | "r", item: Item) => {
    if (disabled || matched.includes(item.id) || flash) return;
    if (side === "l") speak(item.text);
    if (!sel || sel.side === side) {
      sfx.tap();
      setSel({ side, id: item.id });
      return;
    }
    const ok = sel.id === item.id;
    const ids = [`${sel.side}${sel.id}`, `${side}${item.id}`];
    setFlash({ ids, ok });
    setSel(null);
    if (ok) {
      sfx.correct();
      const next = [...matched, item.id];
      setTimeout(() => {
        setMatched(next);
        setFlash(null);
        if (next.length === data.left.length) onDone(mistakes);
      }, 350);
    } else {
      sfx.wrong();
      setMistakes((m) => m + 1);
      setTimeout(() => setFlash(null), 500);
    }
  };

  const cls = (side: "l" | "r", item: Item) => {
    const key = `${side}${item.id}`;
    if (matched.includes(item.id)) return "tile-done opacity-60";
    if (flash?.ids.includes(key)) return flash.ok ? "tile-correct" : "tile-wrong animate-shake";
    if (sel && sel.side === side && sel.id === item.id) return "tile-selected";
    return "";
  };

  return (
    <div>
      <h2 className="mb-6 text-2xl font-extrabold text-ink sm:text-[28px]">Select the matching pairs</h2>
      <div className="grid grid-cols-2 gap-3 sm:gap-5">
        {[
          ["l", data.left],
          ["r", data.right],
        ].map(([side, items]) => (
          <div key={side as string} className="flex flex-col gap-3">
            {(items as Item[]).map((item, i) => (
              <button
                key={item.id}
                disabled={disabled || matched.includes(item.id)}
                onClick={() => tap(side as "l" | "r", item)}
                className={`tile flex min-h-[56px] items-center gap-3 px-3 text-left text-lg ${cls(side as "l" | "r", item)}`}
              >
                <KeyHint n={side === "l" ? i + 1 : i + 1 + data.left.length} />
                <span className="flex-1 text-center">{item.text}</span>
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
