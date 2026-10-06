"use client";

import { AnimatePresence, motion } from "motion/react";
import { createContext, useCallback, useContext, useState } from "react";

type Toast = { id: number; title: string; body?: string; icon?: string; tone?: "green" | "purple" | "blue" | "red" };
const ToastCtx = createContext<(t: Omit<Toast, "id">) => void>(() => {});

export const useToast = () => useContext(ToastCtx);

const TONES = {
  green: "border-duo-green",
  purple: "border-duo-purple",
  blue: "border-duo-blue",
  red: "border-duo-red",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((t: Omit<Toast, "id">) => {
    const id = Date.now() + Math.random();
    setToasts((all) => [...all.slice(-2), { ...t, id }]);
    setTimeout(() => setToasts((all) => all.filter((x) => x.id !== id)), 5000);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-4 z-[100] flex flex-col items-center gap-2 px-4">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ y: -40, opacity: 0, scale: 0.9 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -30, opacity: 0 }}
              className={`pointer-events-auto flex max-w-md items-center gap-3 rounded-2xl border-2 border-b-4 bg-surface px-4 py-3 shadow-lg ${TONES[t.tone || "green"]}`}
            >
              {t.icon && <span className="text-3xl">{t.icon}</span>}
              <div>
                <div className="font-extrabold text-ink">{t.title}</div>
                {t.body && <div className="text-sm text-muted">{t.body}</div>}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}
