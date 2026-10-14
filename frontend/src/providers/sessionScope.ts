import { useSyncExternalStore } from "react";

/**
 * LOTUS FIN P6-0 — Server-Verified Session-Scope Security
 *
 * Implements a server-verified, non-authorizing session-scope identity usable
 * by the React lifecycle. Reuses existing session bootstrap against Frappe backend.
 *
 * Differentiates:
 * - User A vs User B
 * - Two authenticated sessions of the same user
 * - Active vs revoked/disabled/Guest
 * - Authenticated site/product scope
 * - CORE vs DEMO source profiles
 *
 * Never exposes raw session IDs, cookies, or CSRF secrets.
 */

export type ActionScopeState = "VERIFIED" | "UNVERIFIED" | "REVOKED";

export interface AuthenticatedActionScope {
  /** Server-verified authority state */
  readonly state: ActionScopeState;
  /** Non-authorizing actor reference (e.g. user email / identifier), or null when unauthenticated/revoked */
  readonly actor: string | null;
  /** Canonical alias for actor reference */
  readonly actorRef: string | null;
  /** Opaque session epoch derived via one-way hash; never contains raw cookies or secrets */
  readonly sessionEpoch: string;
  /** Site / application origin scope */
  readonly siteScope: string;
  /** Product authority scope */
  readonly productScope: string;
  /** Monotonic immutable generation identity; incremented on every session change / invalidation */
  readonly generation: number;
  /** True strictly when state === "VERIFIED" */
  readonly isVerified: boolean;
}

/**
 * Derives a one-way, irreversible, opaque SHA-256 session epoch from server-verified credentials.
 * Conceals raw session cookies and CSRF tokens from the React presentation layer.
 */
export async function deriveOpaqueSessionEpoch(user: string, csrfToken: string): Promise<string> {
  const seed = `lotus-fin:v1:session:${user}:${csrfToken}`;
  try {
    if (typeof crypto !== "undefined" && crypto.subtle) {
      const buffer = new TextEncoder().encode(seed);
      const hash = await crypto.subtle.digest("SHA-256", buffer);
      const hex = Array.from(new Uint8Array(hash))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");
      return `epoch_${hex.slice(0, 32)}`;
    }
  } catch {}
  // Deterministic 64-bit FNV-1a fallback if Web Crypto is unavailable in environment
  let h1 = 0x811c9dc5;
  let h2 = 0x537f;
  for (let i = 0; i < seed.length; i++) {
    const code = seed.charCodeAt(i);
    h1 = Math.imul(h1 ^ code, 0x01000193);
    h2 = Math.imul(h2 ^ (code << 1), 0x5bd1e995);
  }
  return `epoch_${(h1 >>> 0).toString(16).padStart(8, "0")}${(h2 >>> 0).toString(16).padStart(8, "0")}`;
}

function getSiteScope(): string {
  if (typeof window !== "undefined" && window.location && window.location.origin) {
    return window.location.origin;
  }
  return "http://127.0.0.1:8101";
}

let currentScope: AuthenticatedActionScope = {
  state: "UNVERIFIED",
  actor: null,
  actorRef: null,
  sessionEpoch: "",
  siteScope: getSiteScope(),
  productScope: "lotus-fin",
  generation: 0,
  isVerified: false,
};

const listeners = new Set<() => void>();

function notify(): void {
  listeners.forEach((fn) => {
    try {
      fn();
    } catch {}
  });
}

export function markSessionRevoked(): void {
  // If already REVOKED without an actor, do not spam redundant listener dispatches
  if (currentScope.state === "REVOKED" && currentScope.actor === null) {
    return;
  }
  currentScope = {
    state: "REVOKED",
    actor: null,
    actorRef: null,
    sessionEpoch: "",
    siteScope: getSiteScope(),
    productScope: "lotus-fin",
    generation: currentScope.generation + 1,
    isVerified: false,
  };
  notify();
}

export async function markSessionVerified(user: string, csrfToken: string): Promise<AuthenticatedActionScope> {
  if (!user || user === "Guest" || !csrfToken) {
    markSessionRevoked();
    return currentScope;
  }
  const epoch = await deriveOpaqueSessionEpoch(user, csrfToken);
  if (
    currentScope.state === "VERIFIED" &&
    currentScope.actor === user &&
    currentScope.sessionEpoch === epoch
  ) {
    return currentScope;
  }
  currentScope = {
    state: "VERIFIED",
    actor: user,
    actorRef: user,
    sessionEpoch: epoch,
    siteScope: getSiteScope(),
    productScope: "lotus-fin",
    generation: currentScope.generation + 1,
    isVerified: true,
  };
  notify();
  return currentScope;
}

export interface RawSessionResult {
  status: number;
  user: string | null;
  csrfToken: string | null;
}

let inFlightRawSession: Promise<RawSessionResult> | null = null;

export async function fetchServerSession(signal?: AbortSignal): Promise<RawSessionResult> {
  if (inFlightRawSession) {
    return inFlightRawSession;
  }
  inFlightRawSession = (async () => {
    try {
      const doAttempt = async () => {
        return await fetch("/copilot/session", {
          credentials: "same-origin",
          cache: "no-store",
          redirect: "error",
          headers: { Accept: "application/json" },
          signal,
        });
      };

      let resp = await doAttempt();
      // If server returned 500 (transient database commit lock in Frappe get_csrf_token), retry once after 60ms
      if (resp.status === 500) {
        await new Promise((r) => setTimeout(r, 60));
        resp = await doAttempt();
      }

      if (resp.status !== 200) {
        markSessionRevoked();
        return { status: resp.status, user: null, csrfToken: null };
      }

      const data: unknown = await resp.json().catch(() => null);
      if (typeof data !== "object" || data === null || Array.isArray(data)) {
        markSessionRevoked();
        return { status: 502, user: null, csrfToken: null };
      }
      const s = data as Record<string, unknown>;
      if (
        Object.keys(s).length !== 2 ||
        typeof s.user !== "string" ||
        !s.user ||
        s.user === "Guest" ||
        typeof s.csrf_token !== "string" ||
        !s.csrf_token ||
        s.csrf_token.length > 256
      ) {
        markSessionRevoked();
        return { status: 502, user: null, csrfToken: null };
      }

      await markSessionVerified(s.user, s.csrf_token);
      return { status: 200, user: s.user, csrfToken: s.csrf_token };
    } catch {
      markSessionRevoked();
      return { status: 500, user: null, csrfToken: null };
    } finally {
      inFlightRawSession = null;
    }
  })();
  return inFlightRawSession;
}

export async function revalidateSessionScope(signal?: AbortSignal): Promise<AuthenticatedActionScope> {
  await fetchServerSession(signal);
  return currentScope;
}

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)")
  );
  return match ? decodeURIComponent(match[1]) : null;
}

let pollTimer: ReturnType<typeof setInterval> | null = null;
const POLL_INTERVAL_MS = 200;

function startPeriodicRevalidation(): void {
  if (typeof window === "undefined" || pollTimer !== null) return;
  pollTimer = setInterval(() => {
    if (typeof document !== "undefined" && document.hidden) {
      return;
    }
    const cookieUser = getCookie("user_id");
    if (currentScope.state === "VERIFIED") {
      if (!cookieUser || cookieUser === "Guest" || cookieUser !== currentScope.actor) {
        if (!cookieUser || cookieUser === "Guest") {
          markSessionRevoked();
        } else if (!inFlightRawSession) {
          void fetchServerSession();
        }
      }
    } else if (currentScope.state === "REVOKED") {
      if (cookieUser && cookieUser !== "Guest" && !inFlightRawSession) {
        void fetchServerSession();
      }
    } else if (currentScope.state === "UNVERIFIED" && !inFlightRawSession) {
      void fetchServerSession();
    }
  }, POLL_INTERVAL_MS);
}

function stopPeriodicRevalidation(): void {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

let hasRegisteredWindowEvents = false;
function registerWindowEvents(): void {
  if (typeof window === "undefined" || hasRegisteredWindowEvents) return;
  hasRegisteredWindowEvents = true;

  window.addEventListener("focus", () => {
    void revalidateSessionScope();
  });

  if (typeof document !== "undefined") {
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        void revalidateSessionScope();
      }
    });
  }

  window.addEventListener("storage", () => {
    void revalidateSessionScope();
  });
}

export function subscribeSessionScope(fn: () => void): () => void {
  listeners.add(fn);
  registerWindowEvents();
  if (listeners.size === 1) {
    startPeriodicRevalidation();
  }
  if (currentScope.state === "UNVERIFIED") {
    void revalidateSessionScope();
  }
  return () => {
    listeners.delete(fn);
    if (listeners.size === 0) {
      stopPeriodicRevalidation();
    }
  };
}

export function getSessionScope(): AuthenticatedActionScope {
  return currentScope;
}
export const getSessionScopeSnapshot = getSessionScope;

export function useAuthenticatedActionScope(): AuthenticatedActionScope {
  return useSyncExternalStore(subscribeSessionScope, getSessionScope, getSessionScope);
}
