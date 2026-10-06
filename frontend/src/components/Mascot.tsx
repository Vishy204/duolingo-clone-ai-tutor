"use client";

import { motion } from "motion/react";

export type Mood = "happy" | "cheer" | "sad" | "think" | "wave" | "talk";

/** An original owl mascot drawn from scratch in SVG (no Duolingo artwork is used). */
export default function Mascot({ mood = "happy", size = 120, animate = true }: { mood?: Mood; size?: number; animate?: boolean }) {
  const eyeY = mood === "sad" ? 52 : 50;
  const pupilDy = mood === "think" ? -4 : mood === "sad" ? 3 : 0;
  const pupilDx = mood === "think" ? 4 : 0;
  const bounce =
    mood === "cheer"
      ? { y: [0, -14, 0], rotate: [0, -4, 4, 0] }
      : mood === "talk"
        ? { scaleY: [1, 1.03, 1] }
        : { y: [0, -3, 0] };

  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      animate={animate ? bounce : undefined}
      transition={{ duration: mood === "cheer" ? 0.8 : 2.4, repeat: Infinity, ease: "easeInOut" }}
      aria-label="Duo the owl"
      role="img"
    >
      <ellipse cx="46" cy="110" rx="9" ry="5" fill="#FF9600" />
      <ellipse cx="74" cy="110" rx="9" ry="5" fill="#FF9600" />
      <path d="M20 58 C20 28 38 14 60 14 C82 14 100 28 100 58 L100 82 C100 100 84 110 60 110 C36 110 20 100 20 82 Z" fill="#58CC02" />
      <path d="M28 30 L22 10 L42 22 Z" fill="#58CC02" />
      <path d="M92 30 L98 10 L78 22 Z" fill="#58CC02" />
      <path d="M36 78 C36 66 46 60 60 60 C74 60 84 66 84 78 C84 96 74 104 60 104 C46 104 36 96 36 78 Z" fill="#89E219" />
      <path d="M48 80 q4 -3 8 0 M64 80 q4 -3 8 0 M56 90 q4 -3 8 0" stroke="#58A700" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      <motion.path
        d="M20 62 C10 70 10 86 22 94 C24 84 24 72 20 62 Z"
        fill="#58A700"
        animate={animate && (mood === "wave" || mood === "cheer") ? { rotate: [0, 18, 0] } : undefined}
        style={{ transformBox: "fill-box", transformOrigin: "top right" }}
        transition={{ duration: 0.6, repeat: Infinity }}
      />
      <path d="M100 62 C110 70 110 86 98 94 C96 84 96 72 100 62 Z" fill="#58A700" />
      <circle cx="44" cy={eyeY} r="15" fill="#fff" />
      <circle cx="76" cy={eyeY} r="15" fill="#fff" />
      <motion.g
        animate={animate ? { scaleY: [1, 1, 0.1, 1] } : undefined}
        transition={{ duration: 4, repeat: Infinity, times: [0, 0.92, 0.96, 1] }}
        style={{ transformBox: "fill-box", transformOrigin: "center" }}
      >
        <circle cx={46 + pupilDx} cy={eyeY + 1 + pupilDy} r="7.5" fill="#3C3C3C" />
        <circle cx={74 + pupilDx} cy={eyeY + 1 + pupilDy} r="7.5" fill="#3C3C3C" />
        <circle cx={48 + pupilDx} cy={eyeY - 2 + pupilDy} r="2.5" fill="#fff" />
        <circle cx={76 + pupilDx} cy={eyeY - 2 + pupilDy} r="2.5" fill="#fff" />
      </motion.g>
      {mood === "sad" && (
        <>
          <path d="M30 36 L56 42" stroke="#58A700" strokeWidth="4" strokeLinecap="round" />
          <path d="M90 36 L64 42" stroke="#58A700" strokeWidth="4" strokeLinecap="round" />
        </>
      )}
      {mood === "cheer" || mood === "talk" ? (
        <path d="M52 64 L68 64 L60 76 Z" fill="#FF9600" stroke="#CD7900" strokeWidth="1.5" strokeLinejoin="round" />
      ) : (
        <path d="M53 62 L67 62 L60 71 Z" fill="#FFC800" stroke="#E5A000" strokeWidth="1.5" strokeLinejoin="round" />
      )}
    </motion.svg>
  );
}
