/**
 * Tiny synthesized sound effects (Web Audio), so there are no audio assets to ship or license.
 */
let ctx: AudioContext | null = null;
let enabled = true;

export function setSoundEnabled(on: boolean) {
  enabled = on;
}

function tone(freq: number, start: number, dur: number, type: OscillatorType = "sine", gain = 0.18) {
  if (!ctx) return;
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = type;
  o.frequency.value = freq;
  g.gain.setValueAtTime(0, ctx.currentTime + start);
  g.gain.linearRampToValueAtTime(gain, ctx.currentTime + start + 0.01);
  g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur);
  o.connect(g).connect(ctx.destination);
  o.start(ctx.currentTime + start);
  o.stop(ctx.currentTime + start + dur + 0.05);
}

function ready() {
  if (!enabled || typeof window === "undefined") return false;
  try {
    ctx = ctx || new AudioContext();
    if (ctx.state === "suspended") void ctx.resume();
    return true;
  } catch {
    return false;
  }
}

export const sfx = {
  correct() {
    if (!ready()) return;
    tone(880, 0, 0.12, "triangle");
    tone(1320, 0.09, 0.22, "triangle");
  },
  wrong() {
    if (!ready()) return;
    tone(196, 0, 0.18, "square", 0.08);
    tone(155, 0.12, 0.28, "square", 0.08);
  },
  tap() {
    if (!ready()) return;
    tone(660, 0, 0.05, "sine", 0.08);
  },
  complete() {
    if (!ready()) return;
    [523, 659, 784, 1047].forEach((f, i) => tone(f, i * 0.11, 0.3, "triangle", 0.16));
  },
  streak() {
    if (!ready()) return;
    [392, 523, 659, 784, 1047, 1319].forEach((f, i) => tone(f, i * 0.08, 0.25, "sawtooth", 0.06));
  },
};

/** Browser text-to-speech for Spanish prompts (bonus: audio for exercises). */
export function speak(text: string, lang = "es-ES", rate = 0.9) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang;
  u.rate = rate;
  const voice = window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(lang.slice(0, 2)));
  if (voice) u.voice = voice;
  window.speechSynthesis.speak(u);
}
