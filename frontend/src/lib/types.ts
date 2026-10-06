export type Me = {
  id: number;
  display_name: string;
  username: string;
  avatar_color: string;
  course: { title: string; flag: string };
  total_xp: number;
  gems: number;
  hearts: number;
  max_hearts: number;
  next_heart_at: string | null;
  heart_regen_minutes: number;
  refill_cost: number;
  streak: number;
  longest_streak: number;
  streak_extended_today: boolean;
  streak_freezes: number;
  streak_events: { freezes_used?: number; streak_lost?: number };
  daily_goal_xp: number;
  xp_today: number;
  today: string;
  clock_offset_days: number;
  settings: { sound?: boolean; dark_mode?: boolean };
  agents_enabled: boolean;
  demo_mode: boolean;
};

export type PathNode = {
  id: number;
  title: string;
  icon: string;
  kind: "lesson" | "chest" | "trophy";
  status: "completed" | "active" | "locked";
  lessons_total: number;
  lessons_completed: number;
  crowns: number;
  is_legendary: boolean;
  next_lesson_id: number | null;
};

export type Unit = {
  id: number;
  position: number;
  title: string;
  description: string;
  color: string;
  guidebook: { es: string; en: string }[];
  nodes: PathNode[];
};

export type PlanCard = {
  plan_id: number;
  status: "pending" | "ready" | "consumed" | "failed" | "superseded";
  engine: "agents" | "rules";
  summary: string | null;
  focus_concepts: string[];
  exercise_count: number;
  created_at: string;
};

export type PathData = { course: { title: string; flag: string }; units: Unit[]; duo_practice: PlanCard | null };

export type ExerciseType = "multiple_choice" | "translate" | "match_pairs" | "fill_blank" | "type_answer";

export type Exercise = {
  id: number;
  type: ExerciseType;
  prompt: string;
  data: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  concepts: string[];
  difficulty: number;
  personalized: boolean;
  speak: string | null;
};

export type SessionData = {
  id: number;
  mode: "lesson" | "practice" | "personalized" | "legendary";
  lesson_id: number | null;
  skill_id: number | null;
  status: string;
  exercises: Exercise[];
  answered: number;
  hearts: number;
  uses_hearts: boolean;
  max_mistakes: number | null;
  time_limit_seconds: number | null;
};

export type AnswerResult = {
  attempt_id: number;
  correct: boolean;
  typo: boolean;
  error_type: string | null;
  feedback: string | null;
  correct_answer: string;
  requeued: boolean;
  hearts: number;
  out_of_hearts: boolean;
  failed: boolean;
  combo: number;
  remaining: number;
  progress: number;
};

export type Achievement = {
  key: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  progress?: number;
  threshold?: number;
  unlocked?: boolean;
};

export type CompleteResult = {
  session_id: number;
  mode: string;
  xp_earned: number;
  accuracy: number;
  mistakes: number;
  best_combo: number;
  duration_seconds: number;
  streak: number;
  streak_extended: boolean;
  skill_completed: boolean;
  hearts: number;
  total_xp: number;
  xp_today: number;
  daily_goal_xp: number;
  achievements: Achievement[];
  tutor_updating: boolean;
};

export type Mastery = {
  concept_key: string;
  name: string;
  mastery: number;
  level: "strong" | "good" | "shaky" | "weak";
  attempts: number;
  accuracy: number | null;
  recognition_accuracy: number | null;
  production_accuracy: number | null;
  due_for_review: boolean;
  friendly?: string;
};

export type AgentRun = {
  id: number;
  parent_id: number | null;
  kind: string;
  agent: string;
  status: string;
  input: string | null;
  output: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  tool_calls: { tool: string; arguments: string }[];
  model: string | null;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  trace_id: string | null;
  error: string | null;
  created_at: string;
};

export type Diagnosis = {
  weak_concepts: {
    concept_key: string;
    severity: string;
    weakness_mode: string;
    evidence: string;
    likely_misconception: string;
  }[];
  strengths: string[];
  error_patterns: string[];
  overall_summary: string;
  confidence: number;
};

export type PlanView = {
  id: number;
  status: string;
  trigger: string;
  engine: string;
  summary: string | null;
  focus_concepts: string[];
  diagnosis: Diagnosis | null;
  error: string | null;
  strategy: string | null;
  items: { concept_key: string; exercise_count: number; exercise_types: string[]; difficulty: number; reason: string }[];
  generated_count: number;
  seeded_count: number;
  validation_errors: string[];
  exercise_count: number;
  created_at: string;
  completed_at: string | null;
  exercises?: {
    id: number;
    type: ExerciseType;
    source: string;
    concepts: string[];
    rationale: string | null;
    difficulty: number;
    preview: any; // eslint-disable-line @typescript-eslint/no-explicit-any
    answer: string;
  }[];
  runs?: AgentRun[];
};

export type Mistake = {
  attempt_id: number;
  exercise_type: string;
  concepts: string[];
  task: string;
  learner_answer: string | null;
  correct_answer: string;
  error_type: string | null;
  typo_only: boolean;
  sample?: boolean;
  when: string;
};

export type Brain = {
  agents_enabled: boolean;
  model: string;
  running: boolean;
  budget_left: number;
  mastery: Mastery[];
  error_breakdown: {
    attempts_analysed: number;
    errors_by_type: Record<string, number>;
    error_rate_by_concept: Record<string, { wrong: number; total: number; rate: number }>;
    accuracy_recognition: number | null;
    accuracy_production: number | null;
  };
  recent_mistakes: Mistake[];
  plans: PlanView[];
  other_runs: AgentRun[];
  profiles: { key: string; label: string; description: string; concepts: string[] }[];
};

export type Insights = {
  agents_enabled: boolean;
  running: boolean;
  latest_plan: PlanView | null;
  ready_plan: PlanView | null;
  weakest: Mastery[];
  budget_left: number;
};

export type LeaderboardRow = {
  rank: number;
  user_id: number;
  name: string;
  avatar_color: string;
  xp: number;
  is_me: boolean;
  streak: number;
};

export type Leaderboard = {
  league: { name: string; color: string; promote: number; demote: number };
  week_start: string;
  days_left: number;
  rows: LeaderboardRow[];
};

export type Quest = { key: string; title: string; icon: string; progress: number; target: number };

export type Profile = {
  user: Me;
  stats: Record<string, number | string>;
  achievements: Achievement[];
  xp_history: { day: string; xp: number }[];
  active_days: string[];
  mastery: Mastery[];
};

export type ChatMessage = { role: "user" | "assistant"; content: string; blocked?: boolean; channel?: string };
