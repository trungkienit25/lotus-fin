# LOTUS FIN P6 — SESSION SECURITY IMPLEMENTATION REPORT

**Author**: Staff Frontend Security Engineer  
**Date**: 2026-10-13  
**Status**: COMPLETE (P6_SESSION_SECURITY_PASS)  
**Security References**: ADR001, Security Code V3, P4-F01, P4-F02

---

## 1. Overview & Problem Definition

In Phase 4 security re-evaluations, two critical frontend security blockers were identified:
- **P4-F01**: `LotusCopilotPage` and `LotusCopilotDrawer` did not bind their action-controller lifetime to the server-verified actor/session identity. External logouts, user account rotation, or session revocation in another tab left sensitive search results, opened invoice documents, and selection handles visible and interactable in existing open tabs without a full document reload.
- **P4-F02**: Mobile responsiveness clipping on the Scenario Selector in `InvoiceActionsTabView.tsx` prevented action admission controls on small screens.

---

## 2. Technical Architecture & Implementation

### 2.1 Server-Verified Non-Authorizing Session Scope (`sessionScope.ts`)
Created `frontend/src/providers/sessionScope.ts` to implement a centralized external store providing `AuthenticatedActionScope`.
- **Authoritative Backend**: Delegates to the existing Frappe session endpoint (`/copilot/session`) with `credentials: "same-origin"`, `cache: "no-store"`, and strict payload shape validation (`{ user: string, csrf_token: string }`).
- **Opaque Session Epoch**: Computes `epoch_${sha256(user + csrf_token)}` via Web Crypto API (with deterministic fallback). Neither cookies nor raw CSRF tokens are exposed to the presentation layer.
- **Event Revalidation & Cookie Sensing**:
  - Focus and `visibilitychange` listeners revalidate the session immediately when a tab is focused or restored.
  - A 200ms periodic tick senses changes in the document cookie (`user_id`) without performing redundant network requests unless the cookie changes or the session is unverified.
  - Request coalescing (`inFlightRawSession`) prevents redundant parallel network calls.
  - Transient 500 retry handles Frappe database commit locks gracefully.

### 2.2 Integration with Session Bootstrap (`sessionBootstrap.ts`)
- Refactored `bootstrapSession()` to delegate directly to `fetchServerSession()`.
- Standardized `clearSessionBootstrap()` to trigger `markSessionRevoked()`.
- Enforced strict 2-key dictionary contracts, ensuring unauthenticated or Guest users immediately fail closed.

### 2.3 Surface Mount Lifecycle Integration
- **`LotusCopilotPage.tsx`**: Injects `useAuthenticatedActionScope()` and passes `scope={scope}` to `VercelChatPanel`.
- **`LotusCopilotDrawer.tsx`**: Injects `useAuthenticatedActionScope()` and passes `scope={scope}` to `VercelChatPanel`.
- **`VercelChatPanel.tsx`**: Accepts `scope?: AuthenticatedActionScope`, memoizes synthetic demo transports by `[demoScenario, scope.sessionEpoch, scope.actor, scope.state]`, and passes `scope` to `InvoiceActionsTabView`.
- **`InvoiceActionsTabView.tsx`**:
  - Computes a strict composite `scopeKey`: `${scope?.actor}:${scope?.sessionEpoch}:${company}:${contextKey}:${demoProfile}:${demoScenario}`.
  - Fixed mobile responsive layout bounds on the scenario selector dropdown using `sm:flex-row`, `w-full sm:w-auto max-w-full` (resolving P4-F02).
- **`InvoiceActionPanel.tsx`**:
  - Guards all protected actions with `isVerified = !scope || scope.state === "VERIFIED"`.
  - Disables action submission buttons and renders `data-testid="scope-revoked-banner"` when unverified or revoked.
  - Monitors `lastVerifiedActorRef` and `lastVerifiedEpochRef`. On external logout or session revocation, immediately executes `controller.reset()`, wipes search inputs, and resets selected documents.
  - Allows seamless initial verification transition from mount to verified without clearing user inputs or tearing down in-flight searches.
- **`useInvoiceActions.ts`**:
  - Immediately disposes old controllers (`record.controller.reset()`) on genuine scope mismatch (actor change, session rotation, transport switch, profile switch).
  - Preserves controller continuity on initial anonymous-to-verified transition during mount.

---

## 3. Security Guarantees & Verification Matrix

| Blocker / Requirement | Implementation Mechanism | Verification Result |
| :--- | :--- | :--- |
| **Differentiate User A vs User B** | Scope tracks authoritative `actor`. Controller is destroyed and reset on actor mismatch. | PASS (`actor_scope_browser.py`) |
| **Differentiate Same-User Sessions** | Opaque session epoch derived from SHA-256 of session seed. Rotates on new session. | PASS (`scope_browser.py`) |
| **Active vs Revoked / Guest** | 401/403 or Guest returns `state: "REVOKED"`, `actor: null`. | PASS (`actor_scope_browser.py`) |
| **Clear Protected State on Logout** | Controller resets `results`, `document`, `selectedId`, and inputs immediately. | PASS (No reload required) |
| **Delayed Response Fencing** | Controller increment generation (`fence()`); responses from prior sessions are dropped. | PASS (`real-delayed-core-reply-fenced`) |
| **Page and Drawer Parity** | Both surfaces consume identical `useAuthenticatedActionScope()` hook. | PASS (6/6 checks across both surfaces) |
| **CORE / DEMO Isolation** | Profile switcher enforces distinct transport instances and `allowDemoSource` flags. | PASS (Zero leakage across profiles) |
| **P4-F02 Responsive Bounds** | Responsive flex and max-width wrapping on Scenario selector. | PASS (`mobile-scenario-selector-bounds`) |
