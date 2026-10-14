# LOTUS FIN P4-A — FRONTEND PROFILE ISOLATION & DEMO SECURITY FIX

**Document Identity:** `P4A_FRONTEND_SECURITY_FIX.md`  
**Date:** 2026-10-13  
**Status:** COMPLETE & QUALIFIED  
**Authors:** Staff React/TypeScript Engineer, Frontend Security Engineer  
**Target:** Lotus Fin Copilot Frontend (`frontend/src/pages/copilot/`)  

---

## 1. Executive Summary

During Phase 3 independent acceptance (`LOTUS_P3_INDEPENDENT_ACCEPTANCE.md`), three critical findings were flagged against the Copilot UI:
1. **P1-01 (Profile Isolation):** Protected DEMO records incorrectly persisted when switching from DEMO to CORE profile in Invoice Actions.
2. **P2-04 (Demo Scope & Forgery):** Demo provider accepted forged contexts, wrong context versions, arbitrary selection handles, and cross-instance references due to unbounded fallback (`DEMO_RECORDS[0]`).
3. **P2-07 (Mobile & Accessibility):** Layout clipping observed on narrow viewports (390×844), oversized module (`VercelChatPanel.tsx` at ~770 lines violating ADR001), missing accessible labels on header buttons and scenario selector.

This deliverable confirms the complete resolution of all three findings. The implementation strictly adheres to:
- **Zero ERPNext Dependency:** Lotus Fin runs independently.
- **Strict Profile Isolation:** CORE transport never uses DEMO records, synthetic keys, or fallback authority. N0 native financial authority remains fail-closed (`CAPABILITY_DISABLED` / 503).
- **ADR001 Line Limit (< 200 lines per file):** All modified and created files are strictly under 200 lines.

---

## 2. Root Cause Analysis & Security Remediations

### 2.1 P1-01 — Controller Ownership & Dynamic Profile Isolation

#### Root Cause
`useInvoiceActions.ts` previously instantiated `InvoiceActionController` once within a `useRef` or initializer, without disposing and rebuilding the controller when the presentation/security scope changed (`transport`, `allowDemoSource`, or `scopeKey`). As a result, switching from DEMO to CORE left stale in-memory search results, open document view models, and pending asynchronous promises intact.

#### Security Fix
In `frontend/src/pages/copilot/actions/useInvoiceActions.ts`:
- Detects scope, transport, or `allowDemoSource` mismatch during render:
  ```typescript
  if (
    lastScopeRef.current !== scopeKey ||
    lastAllowDemoRef.current !== allowDemoSource ||
    lastTransportRef.current !== transport
  ) {
    if (controllerRef.current) {
      controllerRef.current.reset(); // Aborts in-flight fetches, increments internal generation
    }
    // Immediately clear all protected state
    setContextData(null);
    setSearchResults(null);
    setSelectedInvoice(null);
    setNotice(null);
    setSearchError(null);
    setOpenError(null);
    setGeneration((g) => g + 1);

    lastScopeRef.current = scopeKey;
    lastAllowDemoRef.current = allowDemoSource;
    lastTransportRef.current = transport;

    controllerRef.current = new InvoiceActionController({
      transport,
      companyCandidate,
      scopeKey,
      allowDemoSource,
    });
  }
  ```
- **Abort Fencing:** `controller.reset()` aborts any in-flight requests and invalidates the previous generation. In-flight DEMO requests completing after a switch to CORE are rejected and cannot mutate CORE state.
- **Scope Key Binding:** In `InvoiceActionsTabView.tsx`, `scopeKey` is bound to `${company}:${contextKey || "default"}:${demoProfile}:${demoScenario}`, ensuring instantaneous re-initialization on any scope change.
- **Form Reset:** `InvoiceActionPanel.tsx` subscribes to `scopeKey` changes to wipe search form inputs (`prefix`, `from`, `to`, `status`, `ask`).

---

### 2.2 P2-04 — Bounded Per-Instance Demo Capabilities

#### Root Cause
`demoInvoiceProvider.ts` previously used global static identifiers and defaulted open requests to `DEMO_RECORDS[0]` whenever a lookup key was unrecognized, allowing forged context references and cross-instance handle replay.

#### Security Fix
Decomposed and refactored into three ADR001-compliant files:
1. `frontend/src/pages/copilot/demo/demoInvoiceTypes.ts` (62 lines)
2. `frontend/src/pages/copilot/demo/demoInvoiceResponses.ts` (167 lines)
3. `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts` (99 lines)

Implemented bounded capability guarantees:
- **Per-Instance Scope Isolation:** Every `createDemoInvoiceTransport` call instantiates an isolated `DemoInvoiceProvider` with a cryptographically secure `instanceId` (UUID4).
- **Strict Context Version Pinning:** Rejects any search request where `expected_context_version !== DEMO_CONTEXT_VERSION` (`ctx_demo_2026_v1`), returning 422 `NOT_AVAILABLE`.
- **Instance Context Verification:** Enforces context ref format `ref.v1.ctx.demo.${instanceId}.${correlationId}`. Mismatched or forged context refs return 422.
- **Monotonic TTL Expiry:** Context lifetime is bounded to 10 minutes (`now + 600_000 ms`). Requests beyond expiry return 409 `CONTEXT_CHANGED`.
- **Exact Active Selection Lookup:** During `invoice.search`, valid rows register ephemeral capability tokens into an `activeSelections` map (`ref.v2.sel.demo.${instanceId}.${invoice_id}`).
- **Elimination of Fallback:** `invoice.open` requires an exact match in `activeSelections`. Unknown, replayed, or forged tokens return 422 `DOCUMENT_UNAVAILABLE`.
- **Non-Actionable PARTIAL Scenario:** Under the `PARTIAL` scenario, returned rows have `selection_ref: null` and `selection_required: true`, rendering them non-actionable in the UI.

---

### 2.3 P2-07 — Mobile Viewport (390×844) & Accessibility

#### Root Cause
`VercelChatPanel.tsx` had grown to ~770 lines, mixing stream parsing, header rendering, tab switching, and composer controls. On mobile viewports (390px), the uncollapsed left navigation sidebar and non-wrapping header elements caused horizontal clipping.

#### Remediation & Decomposition
Decomposed `VercelChatPanel.tsx` into modular sub-components:
- `frontend/src/pages/copilot/components/VercelChatPanelTypes.ts` (22 lines)
- `frontend/src/pages/copilot/components/ChatHeaderBar.tsx` (150 lines)
- `frontend/src/pages/copilot/components/ChatMessageStream.tsx` (145 lines)
- `frontend/src/pages/copilot/components/ChatInputComposer.tsx` (128 lines)
- `frontend/src/pages/copilot/components/InvoiceActionsTabView.tsx` (115 lines)
- `frontend/src/pages/copilot/components/VercelChatPanel.tsx` (166 lines)

Layout & Accessibility Enhancements:
- **Responsive Sidebar Drawer:** On viewports < 1024px (`LotusCopilotPage.tsx`), the left navigation sidebar initializes to collapsed (`w-0 overflow-hidden`). When opened via the header toggle button, it renders as a sliding drawer overlay (`fixed inset-y-0 left-0 w-64 shadow-xl z-20`) with a dark backdrop (`fixed inset-0 bg-slate-900/40 lg:hidden`).
- **Responsive Header & Tabs:** Header bar wraps/shrinks seamlessly down to 390px width. Tablist has `role="tablist"` with `aria-label="Copilot modes"`, and each tab button has `role="tab"` and explicit `aria-label`.
- **Accessible Form Controls:** Scenario selector features `<label htmlFor="demo-scenario-select">Test Scenario:</label>` and `aria-label="Test Scenario"`.
- **Drawer Viewport Guard:** `LotusCopilotDrawer.tsx` uses `w-[calc(100vw-32px)] sm:w-[400px]` with `max-h-[calc(100vh-40px)]`, ensuring 16px lateral padding on 390px mobile screens without horizontal clipping.

---

## 3. ADR001 Compliance Audit Table

All modified and newly created source files strictly comply with the ADR001 200-line limit:

| File Path | Lines | ADR001 Status |
| :--- | :---: | :---: |
| `frontend/src/pages/copilot/actions/useInvoiceActions.ts` | 79 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/actions/InvoiceActionPanel.tsx` | 122 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/demo/demoInvoiceTypes.ts` | 62 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/demo/demoInvoiceResponses.ts` | 167 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts` | 99 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/components/VercelChatPanelTypes.ts` | 22 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/components/ChatHeaderBar.tsx` | 150 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/components/ChatMessageStream.tsx` | 145 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/components/ChatInputComposer.tsx` | 128 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/components/InvoiceActionsTabView.tsx` | 115 | ✅ PASS (< 200) |
| `frontend/src/pages/copilot/components/VercelChatPanel.tsx` | 166 | ✅ PASS (< 200) |
| `frontend/src/components/copilot/LotusCopilotDrawer.tsx` | 51 | ✅ PASS (< 200) |

---

## 4. Verification Summary & Gate Verdicts

| Gate / Verdict ID | Scope | Exit Code | Result |
| :--- | :--- | :---: | :---: |
| `P1_01_PROFILE_ISOLATION` | DEMO↔CORE mounted isolation & state wipe | 0 | **PASS** |
| `P2_04_DEMO_SCOPE` | Forged reference denial & bounded capabilities | 0 | **PASS** |
| `P2_07_UI` | 390×844 mobile layout, drawer & accessibility | 0 | **PASS** |
| `P2B_REGRESSION` | 39 React qualification tests | 0 | **PASS** |
| `BUILDER_READY_FOR_INDEPENDENT_RECHECK` | Full test suite, linter, TypeScript build | 0 | **PASS** |
