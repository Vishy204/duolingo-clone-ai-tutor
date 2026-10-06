"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post } from "./api";
import type { Brain, Insights, Leaderboard, Me, PathData, Profile, Quest } from "./types";

export const keys = {
  me: ["me"] as const,
  path: ["path"] as const,
  insights: ["insights"] as const,
  brain: ["brain"] as const,
  leaderboard: ["leaderboard"] as const,
  profile: ["profile"] as const,
  quests: ["quests"] as const,
  chat: ["chat"] as const,
};

export const useMe = () => useQuery({ queryKey: keys.me, queryFn: () => api<Me>("/me") });
export const usePath = () => useQuery({ queryKey: keys.path, queryFn: () => api<PathData>("/path") });
export const useLeaderboard = () => useQuery({ queryKey: keys.leaderboard, queryFn: () => api<Leaderboard>("/leaderboard") });
export const useProfile = () => useQuery({ queryKey: keys.profile, queryFn: () => api<Profile>("/profile") });
export const useQuests = () =>
  useQuery({ queryKey: keys.quests, queryFn: async () => (await api<{ daily: Quest[] }>("/quests")).daily });

/** Polls while the tutor pipeline is running so new plans appear without a refresh. */
export const useInsights = () =>
  useQuery({
    queryKey: keys.insights,
    queryFn: () => api<Insights>("/tutor/insights"),
    refetchInterval: (q) => (q.state.data?.running ? 2500 : 20000),
  });

export const useBrain = () =>
  useQuery({
    queryKey: keys.brain,
    queryFn: () => api<Brain>("/tutor/brain"),
    refetchInterval: (q) => (q.state.data?.running || q.state.data?.plans?.[0]?.status === "pending" ? 2000 : false),
  });

export function useInvalidateLearner() {
  const qc = useQueryClient();
  return () => {
    for (const k of [keys.me, keys.path, keys.insights, keys.brain, keys.leaderboard, keys.profile, keys.quests]) {
      qc.invalidateQueries({ queryKey: k });
    }
  };
}

export function useAction<TBody, TResult>(path: string) {
  const invalidate = useInvalidateLearner();
  return useMutation({
    mutationFn: (body: TBody) => post<TResult>(path, body),
    onSuccess: () => invalidate(),
  });
}
