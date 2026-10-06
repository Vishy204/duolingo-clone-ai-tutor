"use client";

import { motion } from "motion/react";

export type Mood = "happy" | "cheer" | "sad" | "think" | "wave" | "talk";

const BODY = "#7C5CFF";
const BODY_DARK = "#5B3FE0";
const BELLY = "#D9CFFF";
const CREST = "#FFB020";
const BEAK = "#FF8A00";
const FRAME = "#2D2A5A";

/** Smarto: the app's mascot, an original round bird with a gold crest and reading glasses. */
export default function Mascot({ mood = "happy", size = 120, animate = true }: { mood?: Mood; size?: number; animate?: boolean }) {
  const eyeY = 56;
  const pupilDy = mood === "think" ? -4 : mood === "sad" ? 3 : 0;
  const pupilDx = mood === "think" ? 4 : 0;
  const bounce =
    mood === "cheer"
      ? { y: [0, -14, 0], rotate: [0, -4, 4, 0] }
      : mood === "talk"
        ? { scaleY: [1, 1.03, 1] }
        : { y: [0, -3, 0] };
  const flap = animate && (mood === "wave" || mood === "cheer");

  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      animate={animate ? bounce : undefined}
      transition={{ duration: mood === "cheer" ? 0.8 : 2.4, repeat: Infinity, ease: "easeInOut" }}
      aria-label="Smarto the bird"
      role="img"
    >
      {/* feet */}
      <path d="M44 106 l-6 8 M44 106 l0 9 M44 106 l6 8" stroke={BEAK} strokeWidth="3.5" strokeLinecap="round" />
      <path d="M76 106 l-6 8 M76 106 l0 9 M76 106 l6 8" stroke={BEAK} strokeWidth="3.5" strokeLinecap="round" />

      {/* crest */}
      <path d="M60 28 C52 18 50 8 56 4 C60 12 62 20 60 28 Z" fill={CREST} />
      <path d="M60 28 C66 16 74 12 80 14 C74 20 68 26 60 28 Z" fill={CREST} />
      <path d="M60 28 C52 22 42 20 38 24 C46 28 54 30 60 28 Z" fill="#FFCB5C" />

      {/* body */}
      <ellipse cx="60" cy="68" rx="42" ry="42" fill={BODY} />
      <ellipse cx="60" cy="84" rx="27" ry="23" fill={BELLY} />

      {/* wings */}
      <motion.path
        d="M20 66 C8 74 8 92 22 100 C26 88 26 76 20 66 Z"
        fill={BODY_DARK}
        animate={flap ? { rotate: [0, 20, 0] } : undefined}
        style={{ transformBox: "fill-box", transformOrigin: "top right" }}
        transition={{ duration: 0.6, repeat: Infinity }}
      />
      <path d="M100 66 C112 74 112 92 98 100 C94 88 94 76 100 66 Z" fill={BODY_DARK} />

      {/* cheeks */}
      <ellipse cx="30" cy="76" rx="6" ry="4" fill="#FF7AA8" opacity="0.45" />
      <ellipse cx="90" cy="76" rx="6" ry="4" fill="#FF7AA8" opacity="0.45" />

      {/* eyes */}
      <circle cx="45" cy={eyeY} r="13" fill="#fff" />
      <circle cx="75" cy={eyeY} r="13" fill="#fff" />
      <motion.g
        animate={animate ? { scaleY: [1, 1, 0.1, 1] } : undefined}
        transition={{ duration: 4, repeat: Infinity, times: [0, 0.92, 0.96, 1] }}
        style={{ transformBox: "fill-box", transformOrigin: "center" }}
      >
        <circle cx={46 + pupilDx} cy={eyeY + 1 + pupilDy} r="6.5" fill="#26233F" />
        <circle cx={74 + pupilDx} cy={eyeY + 1 + pupilDy} r="6.5" fill="#26233F" />
        <circle cx={48 + pupilDx} cy={eyeY - 2 + pupilDy} r="2.2" fill="#fff" />
        <circle cx={76 + pupilDx} cy={eyeY - 2 + pupilDy} r="2.2" fill="#fff" />
      </motion.g>

      {/* glasses */}
      <circle cx="45" cy={eyeY} r="16" fill="none" stroke={FRAME} strokeWidth="3.5" />
      <circle cx="75" cy={eyeY} r="16" fill="none" stroke={FRAME} strokeWidth="3.5" />
      <path d={`M61 ${eyeY - 2} q-1 -4 -2 0`} stroke={FRAME} strokeWidth="3.5" fill="none" />
      <path d={`M29 ${eyeY - 4} L22 ${eyeY - 8} M91 ${eyeY - 4} L98 ${eyeY - 8}`} stroke={FRAME} strokeWidth="3" strokeLinecap="round" />

      {mood === "sad" && (
        <>
          <path d="M32 34 L54 38" stroke={FRAME} strokeWidth="3.5" strokeLinecap="round" />
          <path d="M88 34 L66 38" stroke={FRAME} strokeWidth="3.5" strokeLinecap="round" />
        </>
      )}

      {/* beak */}
      {mood === "cheer" || mood === "talk" ? (
        <>
          <path d="M51 74 Q60 70 69 74 L60 80 Z" fill={BEAK} />
          <path d="M53 79 Q60 90 67 79 Z" fill="#C2410C" />
        </>
      ) : (
        <path d="M52 74 Q60 70 68 74 L60 84 Z" fill={BEAK} stroke="#D96F00" strokeWidth="1.2" strokeLinejoin="round" />
      )}
    </motion.svg>
  );
}
