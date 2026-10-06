/* Hand-drawn SVG icons in the Duolingo colour language. */
type P = { size?: number; className?: string; muted?: boolean };

export const Flame = ({ size = 24, muted }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M12 2c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 1.5-4.6 3-6 .3 2 1.3 3 2.5 3.4C10.5 8 11 5 12 2z" fill={muted ? "#E5E5E5" : "#FF9600"} />
    <path d="M12 12c.6 2 3 2.7 3 5a3 3 0 0 1-6 0c0-1.4.7-2.3 1.5-3 .2.9.7 1.4 1.3 1.6-.2-1.3-.1-2.4.2-3.6z" fill={muted ? "#AFAFAF" : "#FFC800"} />
  </svg>
);

export const Gem = ({ size = 24 }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M6 3h12l4 6-10 13L2 9z" fill="#1CB0F6" />
    <path d="M6 3l3 6h6l3-6M2 9h20M9 9l3 13 3-13" stroke="#1899D6" strokeWidth="1.2" fill="none" />
    <path d="M7 4.5l2 3.5" stroke="#DDF4FF" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const Heart = ({ size = 24, muted }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M12 21s-8-5.2-8-11.2A4.8 4.8 0 0 1 12 6.6a4.8 4.8 0 0 1 8 3.2C20 15.8 12 21 12 21z" fill={muted ? "#E5E5E5" : "#FF4B4B"} />
    <path d="M7.5 8.5a2.4 2.4 0 0 1 2.6-1" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" fill="none" opacity={0.7} />
  </svg>
);

export const Lock = ({ size = 28 }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <rect x="5" y="10" width="14" height="11" rx="3" fill="#AFAFAF" />
    <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="#AFAFAF" strokeWidth="2.5" fill="none" />
  </svg>
);

export const Check = ({ size = 28, color = "#fff" }: P & { color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M5 12.5l4.5 4.5L19 7.5" stroke={color} strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Star = ({ size = 28, color = "#fff" }: P & { color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M12 2.8l2.7 5.7 6.2.8-4.6 4.3 1.2 6.2L12 16.8l-5.5 3 1.2-6.2L3.1 9.3l6.2-.8z" fill={color} />
  </svg>
);

export const Crown = ({ size = 22 }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z" fill="#FFC800" stroke="#E5A000" strokeWidth="1.2" />
  </svg>
);

export const Speaker = ({ size = 26 }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M4 9h4l5-4v14l-5-4H4z" fill="#1CB0F6" />
    <path d="M16 9a4 4 0 0 1 0 6M18.5 6.5a7.5 7.5 0 0 1 0 11" stroke="#1CB0F6" strokeWidth="2" fill="none" strokeLinecap="round" />
  </svg>
);

export const Close = ({ size = 22 }: P) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
  </svg>
);

export const Chest = ({ size = 56, open = false }: P & { open?: boolean }) => (
  <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden>
    <rect x="8" y="26" width="48" height="30" rx="6" fill="#CD7900" />
    <rect x="8" y="26" width="48" height="10" fill="#FF9600" />
    {open ? (
      <path d="M8 26 L14 8 H50 L56 26 Z" fill="#FFB020" />
    ) : (
      <path d="M8 26 C8 14 16 10 32 10 C48 10 56 14 56 26 Z" fill="#FFB020" />
    )}
    <rect x="27" y="28" width="10" height="12" rx="2" fill="#FFC800" stroke="#E5A000" strokeWidth="2" />
    {open && <circle cx="32" cy="18" r="5" fill="#1CB0F6" />}
  </svg>
);

export const Trophy = ({ size = 56, muted }: P) => (
  <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden>
    <path d="M18 8h28v14a14 14 0 0 1-28 0z" fill={muted ? "#E5E5E5" : "#FFC800"} />
    <path d="M18 12H8a10 10 0 0 0 10 12M46 12h10a10 10 0 0 1-10 12" stroke={muted ? "#E5E5E5" : "#FFC800"} strokeWidth="4" fill="none" />
    <rect x="28" y="36" width="8" height="10" fill={muted ? "#D0D0D0" : "#E5A000"} />
    <rect x="18" y="46" width="28" height="8" rx="3" fill={muted ? "#D0D0D0" : "#E5A000"} />
  </svg>
);

/* Sidebar navigation icons */
export const NavLearn = ({ size = 32 }: P) => (
  <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
    <path d="M4 15L16 4l12 11v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" fill="#FF9600" />
    <path d="M2 15L16 2.5 30 15" stroke="#FF4B4B" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    <rect x="12" y="18" width="8" height="11" rx="1.5" fill="#CD7900" />
  </svg>
);

export const NavLeague = ({ size = 32 }: P) => (
  <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
    <path d="M16 2l12 4v9c0 8-6 13-12 15C10 28 4 23 4 15V6z" fill="#FFC800" />
    <path d="M16 6l8 2.7V15c0 5.5-4 9-8 10.5z" fill="#E5A000" />
    <path d="M16 10l1.8 3.7 4 .6-2.9 2.8.7 4L16 19.2l-3.6 1.9.7-4-2.9-2.8 4-.6z" fill="#fff" />
  </svg>
);

export const NavQuests = ({ size = 32 }: P) => <Chest size={size} />;

export const NavShop = ({ size = 32 }: P) => (
  <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
    <path d="M4 11h24l-2 17H6z" fill="#FF4B4B" />
    <path d="M3 8h26v5H3z" fill="#EA2B2B" />
    <path d="M11 11V8a5 5 0 0 1 10 0v3" stroke="#CE82FF" strokeWidth="2.5" fill="none" />
    <circle cx="16" cy="19" r="3.5" fill="#FFC800" />
  </svg>
);

export const NavProfile = ({ size = 32, color = "#1CB0F6" }: P & { color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
    <circle cx="16" cy="16" r="14" fill={color} opacity={0.25} />
    <circle cx="16" cy="13" r="5.5" fill={color} />
    <path d="M6.5 25.5a11 11 0 0 1 19 0" fill={color} />
  </svg>
);

export const NavMore = ({ size = 32 }: P) => (
  <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
    <circle cx="16" cy="16" r="14" fill="#CE82FF" />
    <circle cx="10" cy="16" r="2.5" fill="#fff" />
    <circle cx="16" cy="16" r="2.5" fill="#fff" />
    <circle cx="22" cy="16" r="2.5" fill="#fff" />
  </svg>
);

export const Sparkle = ({ size = 18, color = "#CE82FF" }: P & { color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <path d="M12 2l2.2 6.4L21 11l-6.8 2.6L12 20l-2.2-6.4L3 11l6.8-2.6z" fill={color} />
  </svg>
);

export const Mic = ({ size = 24, color = "#fff" }: P & { color?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
    <rect x="9" y="3" width="6" height="11" rx="3" fill={color} />
    <path d="M6 11a6 6 0 0 0 12 0M12 17v4" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" />
  </svg>
);

export const FlagES = ({ size = 32 }: P) => (
  <svg width={size} height={(size * 3) / 4} viewBox="0 0 32 24" aria-label="Spanish" role="img" className="rounded-md">
    <rect width="32" height="24" rx="4" fill="#C60B1E" />
    <rect y="6" width="32" height="12" fill="#FFC400" />
    <rect x="7" y="9" width="5" height="6" rx="1" fill="#C60B1E" opacity="0.8" />
  </svg>
);
