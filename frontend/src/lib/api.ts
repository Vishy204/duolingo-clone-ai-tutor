/**
 * Typed API client. The learner is identified by a signed guest token kept in localStorage
 * (the brief allows simplified auth). If the backend forgets us (e.g. a fresh free-tier disk),
 * a 401 transparently creates a new guest and retries once.
 */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "duo_clone_token";

export class ApiError extends Error {
  constructor(public status: number, message: string, public code?: string) {
    super(message);
  }
}

function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* private mode: the session just won't persist across reloads */
  }
}

let guestPromise: Promise<string> | null = null;

export async function ensureToken(): Promise<string> {
  const existing = getToken();
  if (existing) return existing;
  if (!guestPromise) {
    guestPromise = fetch(`${API_URL}/api/v1/auth/guest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    })
      .then(async (r) => {
        if (!r.ok) throw new ApiError(r.status, (await r.json().catch(() => ({}))).detail || "Could not start");
        const { token } = await r.json();
        setToken(token);
        return token as string;
      })
      .finally(() => {
        guestPromise = null;
      });
  }
  return guestPromise;
}

export function hasToken() {
  return !!getToken();
}

export function resetLearner() {
  setToken(null);
}

export async function api<T>(path: string, init: RequestInit = {}, retried = false): Promise<T> {
  const token = await ensureToken();
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(init.headers || {}) },
  });
  if (res.status === 401 && !retried) {
    setToken(null);
    return api<T>(path, init, true);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : "Something went wrong";
    throw new ApiError(res.status, detail, body.code);
  }
  return res.json() as Promise<T>;
}

export const post = <T,>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? "{}" : JSON.stringify(body) });

export const patch = <T,>(path: string, body: unknown) => api<T>(path, { method: "PATCH", body: JSON.stringify(body) });

/** Exchanges the session token for a single-use voice ticket so the JWT never appears in a URL. */
export async function voiceSocketUrl(): Promise<string> {
  const { ticket } = await post<{ ticket: string }>("/voice/ticket");
  const ws = API_URL.replace(/^http/, "ws");
  return `${ws}/api/v1/voice/ws?ticket=${encodeURIComponent(ticket)}`;
}
