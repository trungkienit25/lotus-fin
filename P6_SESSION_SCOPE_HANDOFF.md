# LOTUS FIN P6 — SESSION SCOPE INTEGRATION HANDOFF CONTRACT

**Author**: Staff Frontend Security Engineer  
**Date**: 2026-10-13  
**Status**: APPROVED & ACTIVE (P6_SESSION_SECURITY_PASS)  
**Target Consumers**: V1 (Overdue AR), L4 (Mutations & Operations), L5 (Autonomous Action Catalog & Workflows)

---

## 1. Executive Summary

This handoff contract establishes the exact type, lifecycle, and integration interface for `AuthenticatedActionScope`.

Under architecture decision ADR001 and security requirements P4-F01, the React UI lifecycle must bind all protected action controllers strictly to a **server-verified, non-authorizing session-scope identity**. The backend remains strictly authoritative at all times.

- **Zero Secret Exposure**: Raw session IDs (`sid`), HTTP cookies, and raw CSRF secrets are never exposed to React components or consumers.
- **Authoritative Identity**: The identity derives directly from the Frappe `/copilot/session` endpoint and is refreshed on every protected lifecycle event.
- **Strict Isolation**: Distinct user actors (User A vs User B), same-user session replacements/rotations, active vs revoked/Guest states, and CORE vs DEMO profiles are cleanly differentiated and partitioned.

---

## 2. Narrow Typed Contract: `AuthenticatedActionScope`

Exported from `frontend/src/providers/sessionScope.ts` (and re-exported by `frontend/src/providers/sessionBootstrap.ts`):

```typescript
export type ActionScopeState = "VERIFIED" | "UNVERIFIED" | "REVOKED";

export interface AuthenticatedActionScope {
  /**
   * Server-verified authority state:
   * - "VERIFIED": Backend /copilot/session returned 200 with matching valid user and CSRF token.
   * - "UNVERIFIED": Initial mount or pending in-flight revalidation. Protected actions MUST be fenced/blocked.
   * - "REVOKED": Session revoked, 401/403 returned, user logged out, disabled, or Guest. All protected state MUST be cleared.
   */
  readonly state: ActionScopeState;

  /**
   * Non-authorizing actor reference (e.g. user email 'qa-core@example.invalid'),
   * or null when unauthenticated, disabled, or revoked.
   */
  readonly actor: string | null;

  /**
   * Canonical alias for actor reference.
   */
  readonly actorRef: string | null;

  /**
   * Opaque, one-way SHA-256 derived session epoch:
   * Format: `epoch_<sha256_hex_slice>`
   * Derived server-side from `lotus-fin:v1:session:${user}:${csrfToken}`.
   * Never contains raw cookie values, session identifiers, or CSRF secrets.
   */
  readonly sessionEpoch: string;

  /**
   * Origin / Site scope (e.g. 'http://127.0.0.1:8101').
   */
  readonly siteScope: string;

  /**
   * Product authority boundary ('lotus-fin').
   */
  readonly productScope: string;

  /**
   * Monotonic immutable generation counter. Incremented on every invalidation,
   * logout, rotation, or revalidation cycle.
   */
  readonly generation: number;

  /**
   * Convenience boolean flag: strictly true when `state === "VERIFIED"`.
   */
  readonly isVerified: boolean;
}
```

---

## 3. Hook & Store API

### 3.1 Reactive React Hook (Primary)

```typescript
import { useAuthenticatedActionScope } from "@/providers/sessionScope";

export const MyProtectedComponent: React.FC = () => {
  const scope = useAuthenticatedActionScope();

  if (scope.state !== "VERIFIED") {
    return <AccessDeniedNotice reason="Session unverified or revoked" />;
  }

  return <ProtectedContent actor={scope.actor} epoch={scope.sessionEpoch} />;
};
```

### 3.2 Non-React Synchronous Snapshot (Controllers / Handlers)

```typescript
import { getSessionScope } from "@/providers/sessionScope";

function checkActionAdmission(): boolean {
  const scope = getSessionScope();
  return scope.state === "VERIFIED" && scope.actor !== null;
}
```

### 3.3 Active Revalidation Trigger

```typescript
import { revalidateSessionScope } from "@/providers/sessionScope";

async function onCriticalActionTrigger() {
  const freshScope = await revalidateSessionScope();
  if (freshScope.state !== "VERIFIED") {
    throw new Error("Session revalidation failed before admitting protected action");
  }
}
```

---

## 4. Integration Guidelines for V1, L4, L5 Consumers

### 4.1 V1 (Overdue AR & Observability)
- **Scope Key Binding**: Bind any cached query results, table selections, and filters to `${scope.actor}:${scope.sessionEpoch}:${company}`.
- **Clear on Revocation**: When `scope.state !== "VERIFIED"`, immediately reset all cached customer AR observations and clear document drill-down selections.
- **Read-Only Gate**: Disable table row click handlers and export buttons whenever `scope.state !== "VERIFIED"`.

### 4.2 L4 (Mutations & Operations)
- **Fencing In-Flight Mutations**: Before sending any POST mutation request (e.g. payment allocations, journal approvals), capture `const targetEpoch = scope.sessionEpoch`.
- **Pre-Admission Check**: Call `revalidateSessionScope()` prior to submitting high-impact financial mutations.
- **Generation Guard**: If `scope.generation` changes while a mutation request is in-flight, discard the server response and notify the user that the session rotated.
- **Disposal**: When `scope.state === "REVOKED"` or `scope.actor` changes, dispose of all pending proposal queues and clear staged mutation payload forms.

### 4.3 L5 (Autonomous Action Catalog & Workflows)
- **Catalog Execution Scope**: Ensure workflow automation engines and plan executors accept `AuthenticatedActionScope` as an input parameter.
- **Abort Signal**: Pass `scope.generation` or an abort signal bound to `subscribeSessionScope` to cancel autonomous multi-step execution if the user logs out or switches accounts mid-workflow.
- **Audit Logging**: Use `scope.actorRef` and `scope.sessionEpoch` for audit log correlation without leaking raw tokens.

---

## 5. Security & Lifecycle Guarantees

1. **No Page Reload Required**: State clearance occurs purely within the React store lifecycle. When an external tab logs out or another actor logs in, all protected state in open tabs/drawers is purged within ≤ 200ms without forcing a full document reload.
2. **Double Fence**: Both client-side generation checks (`scope.generation`) and server-side session checks (`/copilot/session`) fence delayed or out-of-order network responses.
3. **Fail-Closed Guest Handling**: Unauthenticated users and Frappe `Guest` sessions immediately evaluate to `state: "REVOKED"` and `actor: null`.
