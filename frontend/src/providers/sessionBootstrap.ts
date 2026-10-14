import { markSessionRevoked, fetchServerSession } from "./sessionScope.ts";
export * from "./sessionScope.ts";

/** Session tokens live only in memory and are acquired from the current cookie. */
export interface SessionState { user: string; csrfToken: string }

export class SessionBootstrapError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, data: unknown) {
    super("Authenticated session bootstrap failed");
    this.name = "SessionBootstrapError";
    this.status = status;
    this.data = data;
  }
}

let generation = 0;

export function requireSameOrigin(baseUrl: string): void {
  if (typeof window !== "undefined" && new URL(baseUrl || "/", window.location.origin).origin !== window.location.origin) {
    throw new Error("Invoice transport requires the application origin");
  }
}

export function clearSessionBootstrap(): void {
  generation += 1;
  markSessionRevoked();
}

export function sessionGeneration(): number { return generation; }

export function assertSessionGeneration(expected: number): void {
  if (expected !== generation) throw new DOMException("Session changed", "AbortError");
}

/** No cached token: each protected operation binds to the latest server session. */
export async function bootstrapSession(signal?: AbortSignal): Promise<SessionState> {
  const expected = generation;
  const result = await fetchServerSession(signal);
  assertSessionGeneration(expected);
  if (result.status !== 200 || !result.user || !result.csrfToken) {
    throw new SessionBootstrapError(result.status || 502, null);
  }
  return { user: result.user, csrfToken: result.csrfToken };
}
