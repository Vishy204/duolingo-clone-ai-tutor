import { Award, BookOpen, Crown, Flame, Footprints, Gem, Library, Medal, Sparkles, Target, Zap, type LucideIcon } from "lucide-react";

/** Icons are chosen by key on the client, so the API never has to ship emoji. */
const QUEST: Record<string, LucideIcon> = { xp: Zap, lessons: BookOpen, accuracy: Target, duo: Sparkles };
const ACHIEVEMENT: Record<string, LucideIcon> = {
  first_lesson: Footprints,
  scholar: Library,
  wildfire_3: Flame,
  wildfire_7: Flame,
  sage_100: Zap,
  sage_500: Zap,
  sharpshooter: Target,
  perfectionist: Gem,
  conqueror: Crown,
  duo_student: Sparkles,
  legendary: Medal,
};

export function QuestIcon({ questKey, size = 28 }: { questKey: string; size?: number }) {
  const I = QUEST[questKey] || Target;
  return <I size={size} strokeWidth={2.5} className="shrink-0 text-duo-yellow" />;
}

export function AchievementIcon({ achievementKey, size = 30 }: { achievementKey: string; size?: number }) {
  const I = ACHIEVEMENT[achievementKey] || Award;
  return <I size={size} strokeWidth={2.5} className="text-white" />;
}
