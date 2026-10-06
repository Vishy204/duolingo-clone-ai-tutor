"use client";

import AppShell from "@/components/shell/AppShell";
import { Gem, Heart } from "@/components/ui/Icons";
import { useToast } from "@/components/ui/Toast";
import { useAction, useMe } from "@/lib/hooks";
import type { Me } from "@/lib/types";

export default function ShopPage() {
  const { data: me } = useMe();
  const refill = useAction<void, Me>("/shop/refill-hearts");
  const freeze = useAction<void, Me>("/shop/streak-freeze");
  const toast = useToast();
  const fail = (e: Error) => toast({ title: "Can't buy that", body: e.message, icon: "💎", tone: "blue" });

  return (
    <AppShell>
      <h2 className="mb-2 mt-2 text-2xl font-extrabold text-ink">Hearts</h2>
      <Item
        icon={<Heart size={64} />}
        title="Refill hearts"
        body={me && me.hearts >= me.max_hearts ? "You have full hearts" : "Get full hearts so you can worry less about making mistakes"}
        action={
          <button
            className="btn btn-white w-36"
            disabled={!me || me.hearts >= me.max_hearts || refill.isPending}
            onClick={() => refill.mutate(undefined, { onSuccess: () => toast({ title: "Hearts refilled!", icon: "❤️", tone: "red" }), onError: fail })}
          >
            {me && me.hearts >= me.max_hearts ? "Full" : <><Gem size={18} /> {me?.refill_cost ?? 350}</>}
          </button>
        }
      />
      <h2 className="mb-2 mt-8 text-2xl font-extrabold text-ink">Power-ups</h2>
      <Item
        icon={<span className="text-6xl">🧊</span>}
        title="Streak Freeze"
        body={`Streak Freeze allows your streak to remain in place for one full day of inactivity. ${me?.streak_freezes ?? 0} / 2 equipped`}
        action={
          <button
            className="btn btn-white w-36"
            disabled={!me || me.streak_freezes >= 2 || freeze.isPending}
            onClick={() => freeze.mutate(undefined, { onSuccess: () => toast({ title: "Streak Freeze equipped!", icon: "🧊", tone: "blue" }), onError: fail })}
          >
            <Gem size={18} /> 200
          </button>
        }
      />
      <h2 className="mb-2 mt-8 text-2xl font-extrabold text-ink">Super</h2>
      <div className="rounded-2xl bg-gradient-to-br from-[#26075e] to-[#1a8bd6] p-6 text-white">
        <div className="text-sm font-extrabold uppercase opacity-80">Super Duolingo</div>
        <div className="text-2xl font-extrabold">Unlimited hearts, no ads</div>
        <p className="mt-1 opacity-80">In-app purchases are mocked for this clone. Coming soon!</p>
      </div>
    </AppShell>
  );
}

function Item({ icon, title, body, action }: { icon: React.ReactNode; title: string; body: string; action: React.ReactNode }) {
  return (
    <div className="flex items-center gap-5 border-t-2 border-line py-5">
      <div className="grid w-20 place-items-center">{icon}</div>
      <div className="flex-1">
        <div className="text-lg font-extrabold text-ink">{title}</div>
        <div className="text-muted">{body}</div>
      </div>
      {action}
    </div>
  );
}
