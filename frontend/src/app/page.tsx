"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Mascot from "@/components/Mascot";
import { ensureToken, hasToken } from "@/lib/api";

export default function Landing() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (hasToken()) router.replace("/learn");
  }, [router]);

  const start = async () => {
    setBusy(true);
    setErr(null);
    try {
      await ensureToken();
      router.push("/learn");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not reach the server");
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-5">
        <span className="text-[32px] font-black tracking-tight text-brand">smartalingo</span>
        <span className="text-sm font-extrabold uppercase text-faint">Site language: English</span>
      </header>
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center justify-center gap-10 px-6 md:flex-row md:gap-20">
        <div className="relative">
          <Mascot size={300} mood="wave" />
          <span className="absolute -right-4 top-6 rounded-2xl border-2 border-line bg-surface px-3 py-2 text-lg">¡Hola!</span>
        </div>
        <div className="flex max-w-md flex-col items-center gap-6 text-center">
          <h1 className="text-[32px] font-extrabold leading-tight text-ink">
            The free, fun, and effective way to learn a language!
          </h1>
          <p className="text-muted">
            Now with <span className="text-duo-purple">Smarto AI</span>: a personal tutor that learns from your mistakes and builds
            practice just for you.
          </p>
          <button className="btn btn-brand w-full max-w-xs" onClick={start} disabled={busy}>
            {busy ? "Getting ready…" : "Get started"}
          </button>
          <button className="btn btn-white w-full max-w-xs" onClick={start} disabled={busy}>
            I already have an account
          </button>
          {err && <p className="text-sm text-duo-red">{err}</p>}
        </div>
      </main>
      <footer className="border-t-2 border-line py-4 text-center text-xs text-faint">
        Smartalingo · a Duolingo-inspired project, not affiliated with Duolingo
      </footer>
    </div>
  );
}
