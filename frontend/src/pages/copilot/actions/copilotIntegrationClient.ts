import { bootstrapSession } from "../../../providers/sessionBootstrap.ts";
import { getSessionScopeSnapshot, markSessionRevoked, type AuthenticatedActionScope } from "../../../providers/sessionScope.ts";

export function sameActionScope(a: AuthenticatedActionScope, b: AuthenticatedActionScope): boolean {
  return a.state === "VERIFIED" && b.state === "VERIFIED" && a.actor === b.actor &&
    a.sessionEpoch === b.sessionEpoch && a.generation === b.generation &&
    a.siteScope === b.siteScope && a.productScope === b.productScope;
}

export async function callIntegration(profile: "CORE" | "DEMO", action: string, payload: Record<string, unknown> = {}, action_name?: string) {
  const before = getSessionScopeSnapshot();
  const session = await bootstrapSession();
  const admitted = getSessionScopeSnapshot();
  if (!sameActionScope(before, admitted)) throw new Error("Session changed; review again.");
  const response = await fetch("/api/method/lotus_fin.api.copilot_integration_api.dispatch", {
    method: "POST", credentials: "same-origin", cache: "no-store",
    headers: { "Content-Type": "application/json", "X-Frappe-CSRF-Token": session.csrfToken },
    body: JSON.stringify({ profile, action, payload, ...(action_name ? { action_name } : {}) }),
  });
  if (response.status === 401 || response.status === 403) {
    // A policy denial is distinct from session revocation; verify against the server.
    const { revalidateSessionScope } = await import("../../../providers/sessionScope.ts");
    await revalidateSessionScope();
  }
  if (!sameActionScope(admitted, getSessionScopeSnapshot())) throw new Error("Session changed; response discarded.");
  const wire = await response.json();
  if (!wire || typeof wire.message !== "object" || !wire.message) throw new Error("Invalid integration response");
  return { status: response.status, data: wire.message };
}
