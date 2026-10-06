"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Mascot from "../Mascot";
import { NavLeague, NavLearn, NavMore, NavProfile, NavQuests, NavShop } from "../ui/Icons";

const OwlIcon = ({ size = 32 }: { size?: number }) => (
  <div style={{ width: size, height: size }} className="grid place-items-center">
    <Mascot size={size + 4} animate={false} />
  </div>
);

export const NAV = [
  { href: "/learn", label: "Learn", Icon: NavLearn },
  { href: "/tutor", label: "Duo AI", Icon: OwlIcon, badge: "NEW" },
  { href: "/leaderboard", label: "Leaderboards", Icon: NavLeague },
  { href: "/quests", label: "Quests", Icon: NavQuests },
  { href: "/shop", label: "Shop", Icon: NavShop },
  { href: "/profile", label: "Profile", Icon: NavProfile },
  { href: "/settings", label: "More", Icon: NavMore },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="sticky top-0 hidden h-screen w-[88px] shrink-0 flex-col border-r-2 border-line px-3 py-6 md:flex lg:w-[256px] lg:px-4">
      <Link href="/learn" className="mb-6 hidden px-4 text-[32px] font-black tracking-tight text-duo-green lg:block">
        smartalingo
      </Link>
      <Link href="/learn" className="mb-6 grid place-items-center lg:hidden">
        <Mascot size={44} animate={false} />
      </Link>
      <nav className="flex flex-col gap-2">
        {NAV.map(({ href, label, Icon, badge }) => {
          const active = path === href || (href !== "/learn" && path.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-5 rounded-xl border-2 px-3 py-2 text-[15px] font-extrabold uppercase tracking-wide transition-colors lg:px-4 ${
                active
                  ? "border-duo-blue-border bg-duo-blue-light text-duo-blue"
                  : "border-transparent text-muted hover:bg-surface-2"
              }`}
            >
              <Icon size={32} />
              <span className="hidden lg:inline">{label}</span>
              {badge && (
                <span className="ml-auto hidden rounded-md bg-duo-purple px-1.5 py-0.5 text-[10px] text-white lg:inline">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export function MobileNav() {
  const path = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex h-16 items-center justify-around border-t-2 border-line bg-surface md:hidden">
      {NAV.slice(0, 6).map(({ href, label, Icon }) => {
        const active = path === href || (href !== "/learn" && path.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            aria-label={label}
            className={`grid h-12 w-12 place-items-center rounded-xl border-2 ${
              active ? "border-duo-blue-border bg-duo-blue-light" : "border-transparent"
            }`}
          >
            <Icon size={28} />
          </Link>
        );
      })}
    </nav>
  );
}
