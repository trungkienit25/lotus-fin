# Lotus Fin L3 Local Preview — Lifecycle & Concurrency Correction Report

**DECISION:** `L3_BUILDER_READY_FOR_RECHECK`  
**DATE:** 12 October 2026 (Asia/Saigon)  
**SCOPE ENFORCEMENT:** Strictly bounded to `frontend/src/pages/copilot/prepare/` and directly associated L3 tests/fixture harnesses. Zero modifications to P2-B modules, backend contracts, ERPNext packages, or production mount points.

---

## 1. Executive Summary & Failure Reconciliation

Historical independent audit (`CHATBOT_FINAL_SECURITY_ASSESSMENT.md`, `CHATBOT_FINAL_INTEGRATION_REPORT.md`) recorded:
- **L3 Independent Controller Oracle:** 12 PASS / 4 FAIL (`L3_MISSING_SCOPE`, `L3_PENDING_COPY_EDIT`, `L3_OLD_FINALLY_COPY_LOCK`, `L3_DEFAULT_MONOTONIC_CLOCK`)
- **L3 Independent React DOM Oracle:** 7 PASS / 4 FAIL (`L3_DOM_IDLE_EXPIRY`, `L3_DOM_COPY_REVISION`, `L3_DOM_UNMOUNT_FENCE`, `L3_DOM_MISSING_SCOPE`)

Following systematic implementation of FIN-F03, FIN-F04, FIN-F05, and FIN-F10:
- **L3 Independent Controller Oracle (`l3_oracle.mjs`):** **16 PASS / 0 FAIL** (Exit Code: 0)
- **L3 Independent React DOM Oracle (`l3_dom_oracle.py`):** **11 PASS / 0 FAIL** (Exit Code: 0)
- **Builder Unit & Negative Test Suites:** **20 PASS / 0 FAIL** (Exit Code: 0)
- **Builder E2E Fixture (`test_followup_preview_e2e.py`):** **1 PASS / 0 FAIL** (Exit Code: 0)
- **Affected B1-S / P2-B Regressions:** **4/4 B1-S PASS**, **3/3 P2-B PASS** (Exit Code: 0)
- **Typecheck & Lint & Production Build:** `tsc` clean (0 errors), `oxlint` clean (0 errors), Vite production build clean (Exit Code: 0)

---

## 2. Hardened Architecture & Concrete Fixes

### FIN-F03 [P1] — Copy Operation Ownership & Lock Fencing
- **Operation Ownership:** Implemented monotonically increasing `copyOperationId`, tracking `generation` and `bodyRevision`.
- **Lock Integrity:** When `copy()` initiates, `activeCopyLockId` is claimed. If user edits the text while copy is in-flight, `bodyRevision` increments and invalidates the pending operation. Stale promise resolution cannot set `COPIED` notice or acknowledge a newer revision.
- **Lock Release:** Stale `finally` blocks verify `activeCopyLockId === opId` before clearing the lock; older operations from prior generations or discarded drafts can never release a newer copy lock or trigger overlapping clipboard writes.
- **Irreversible Clipboard Outcome:** Clipboard writes cannot be retracted once initiated, but their local UI acknowledgment is strictly fenced by generation, revision, and scope.

### FIN-F04 [P1] — Unmount Cleanup & Component Lifecycle Discard
- **Disposal on Unmount:** React component `FollowupPreview` registers an unmount cleanup effect that invokes `controller.dispose()`.
- **Fence Pending Promises:** `dispose()` increments generation/revision, clears listeners, resets state to `EMPTY`, and clears `localText` in the DOM. Late clipboard promises settling after unmount are completely suppressed.
- **Remount Isolation:** Every new mount instantiates a clean, independent controller starting in `EMPTY` state with no retained user text.

### FIN-F05 [P1] — Monotonic Time Accounting & Non-Sliding Expiry
- **Monotonic Clock Fallback:** Built-in default clock combines `performance.timeOrigin + performance.now()` when available to guarantee strictly monotonic elapsed-time calculation, immune to wall-clock rollbacks.
- **Idle Expiry:** Component schedules periodic timer polling (every 500ms) and listens to browser `visibilitychange` events (foreground resume) to immediately invalidate expired drafts even without user interaction.
- **Action Revalidation:** `getState()`, `prepare()`, `updateBody()`, `setReviewed()`, and `copy()` revalidate expiry at the exact `now - createdAt >= ABSOLUTE_TTL_MS` (600,000ms) boundary. Edits, focus, or copy clicks do not slide or extend the TTL. Expired body is immediately cleared from state and DOM.

### FIN-F10 [P2] — Lifecycle Scope Validation & Fencing
- **Strict Scope Validation:** `prepare()` rejects missing, undefined, or whitespace-only `scopeEpoch` with user-facing notification `"Phạm vi phiên làm việc không khả dụng."` and keeps state `EMPTY`.
- **Scope Transition Guard:** `setScopeEpoch` immediately discards state and fences in-flight operations when the scope changes. Any attempt to edit or copy under unavailable scope is immediately rejected.
- **Fencing vs. Authorization:** Documented and verified that `scopeEpoch` serves exclusively as client-side lifecycle fencing and does not substitute for server-side authorization.

---

## 3. Regression & Concurrency Verification Matrix

| Category / ID | Test Trace | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| **L3 Oracle: L3_EXACT_LITERAL** | Standard valid prepare request | Exact NFC Vietnamese literal returned | Exact match | **PASS** |
| **L3 Oracle: L3_REJECT_EXTRA** | Extra fields (`invoice_id`, `amount`, etc.) | `INVALID_INPUT`, null preview | Rejected | **PASS** |
| **L3 Oracle: L3_MISSING_SCOPE** | Blank scope epoch at prepare/copy | `CONTEXT_UNAVAILABLE`, empty body, 0 clipboard calls | Empty, 0 calls | **PASS** |
| **L3 Oracle: L3_EXACT_TTL** | Elapsed time = 600,000ms | `EXPIRED`, 0 clipboard calls | `EXPIRED`, 0 calls | **PASS** |
| **L3 Oracle: L3_PENDING_COPY_EDIT** | Edit body while copy in flight, resolve old | No `COPIED` notice for uncopied revision | No notice, revision intact | **PASS** |
| **L3 Oracle: L3_OLD_FINALLY_COPY_LOCK** | Copy A held -> discard -> prepare B -> copy B held -> resolve A -> click copy | At most 2 writes initiated; generation B stays locked | Exact 2 calls, 0 leak | **PASS** |
| **L3 Oracle: L3_SCOPE_FENCES_COPY** | Scope changes while copy is pending | State resets to `EMPTY`, no success notice | `EMPTY`, null notice | **PASS** |
| **L3 Oracle: L3_COPY_REJECT** | Clipboard promise rejects | Notice sets `COPY_FAILED`, body preserved | `COPY_FAILED`, preserved | **PASS** |
| **L3 Oracle: L3_DEFAULT_MONOTONIC_CLOCK**| Wall clock rewound by 1h, monotonic elapsed > 600s | Evaluates to `EXPIRED`, body cleared | `EXPIRED`, body empty | **PASS** |
| **L3 Oracle: L3_MAX_2000 / OVER_2000** | 2000 emojis vs 2001 chars | 2000 valid, 2001 rejected | As expected | **PASS** |
| **L3 Oracle: L3_BIDI** | Bidi override characters (`\u202E`) | Rejected with `FORBIDDEN_BIDI_CONTROL` | Rejected | **PASS** |
| **L3 Oracle: L3_XSS_LITERAL** | `<img src=x onerror=alert(1)>` payload | Handled as safe literal string | Plain text literal | **PASS** |
| **DOM Oracle: L3_DOM_BASELINE** | Prepare -> Review -> Copy | Copied plain text once | 1 clipboard call | **PASS** |
| **DOM Oracle: L3_DOM_IDLE_EXPIRY** | Advance clock past TTL, wait 1200ms idle | Textarea unmounted/cleared from DOM | Textarea count = 0 | **PASS** |
| **DOM Oracle: L3_DOM_COPY_REVISION** | Hold copy -> edit textarea -> resolve copy | No `COPIED` notice rendered | Notice count = 0 | **PASS** |
| **DOM Oracle: L3_DOM_UNMOUNT_FENCE** | Hold copy -> unmount -> resolve copy | Controller `EMPTY`, body empty, notice null | Clean empty state | **PASS** |
| **DOM Oracle: L3_DOM_REMOUNT_EMPTY** | Unmount then toggle mount | New instance starts in `EMPTY` state | Prepare button present | **PASS** |
| **DOM Oracle: L3_DOM_SCOPE_CLEAR** | Scope switch button click | Editor cleared | Textarea count = 0 | **PASS** |
| **DOM Oracle: L3_DOM_MISSING_SCOPE** | Blank scope epoch button click | Prepare fails closed; no textarea rendered | Textarea count = 0 | **PASS** |
| **DOM Oracle: L3_DOM_XSS** | Inject script / HTML in textarea | Literal plain text, 0 img tags, no script execution | Safe plain text | **PASS** |
| **DOM Oracle: L3_DOM_STORAGE** | Audit local and session storage keys | Zero keys written | `local: [], session: []` | **PASS** |
| **DOM Oracle: L3_DOM_NETWORK** | Network route interceptor | Zero external / API requests made | 0 unexpected requests | **PASS** |
| **DOM Oracle: L3_DOM_ERRORS** | Page error listener | Zero runtime page errors | 0 errors | **PASS** |

---

## 4. Actual Command & Exit Evidence

```json
[
  {
    "command": "node docs/reviews/evidence/chatbot-final-integration-2026-10-12-01a1303a/l3_oracle.mjs",
    "exit": 0,
    "summary": "Independent L3 Controller Oracle",
    "output": "{\"counts\":{\"PASS\":16,\"FAIL\":0},\"failed\":[]}"
  },
  {
    "command": "python docs/reviews/evidence/chatbot-final-integration-2026-10-12-01a1303a/l3_dom_oracle.py",
    "exit": 0,
    "summary": "Independent L3 React DOM Oracle",
    "output": "{\"counts\": {\"PASS\": 11, \"FAIL\": 0}, \"cleanup\": {\"owned_pid\": 18548, \"exited\": true, \"port_released\": true}}"
  },
  {
    "command": "node --experimental-strip-types --test frontend/tests/followupPreview.test.ts frontend/tests/followupPreviewController.test.ts",
    "exit": 0,
    "summary": "Unit and Negative Concurrency Tests",
    "output": "20 tests passed, 0 failed"
  },
  {
    "command": "node frontend/node_modules/typescript/bin/tsc -p frontend/tsconfig.app.json --noEmit",
    "exit": 0,
    "summary": "TypeScript Typecheck",
    "output": "Clean exit, 0 errors"
  },
  {
    "command": "node frontend/node_modules/oxlint/bin/oxlint frontend/src/pages/copilot/actions frontend/src/pages/copilot/prepare",
    "exit": 0,
    "summary": "Oxlint Selected Lint",
    "output": "Found 1 warning (regex control char) and 0 errors across 17 files"
  },
  {
    "command": "node node_modules/vite/bin/vite.js build --configLoader runner --outDir .../BUILD",
    "exit": 0,
    "summary": "Vite Production Build",
    "output": "built in 4.48s, 374 modules transformed"
  },
  {
    "command": "python -B -m pytest tests_e2e/test_followup_preview_e2e.py -v",
    "exit": 0,
    "summary": "L3 Builder E2E Fixture",
    "output": "1 passed in 9.76s"
  },
  {
    "command": "python -B -m pytest tests_e2e/test_invoice_actions_e2e.py -v",
    "exit": 0,
    "summary": "P2-B Regression E2E",
    "output": "3 passed in 22.06s"
  },
  {
    "command": "python -B -m pytest tests_e2e/test_copilot_failclosed.py -v",
    "exit": 0,
    "summary": "B1-S Regression E2E",
    "output": "4 passed in 28.85s"
  }
]
```

---

## 5. Source Fingerprint & Diff Manifest

### Modified & Created Source Files
| File Path | Lines | SHA-1 Git Hash | Role / Modification Summary |
|---|---|---|---|
| `frontend/src/pages/copilot/prepare/followupPreviewController.ts` | 183 | `d5724250c23954f90f2321a5f50be29c8820f960` | Added copy operation IDs, generation & revision binding, monotonic time, disposal, and scope validation |
| `frontend/src/pages/copilot/prepare/FollowupPreview.tsx` | 136 | `99452e618fdf8fdec019d167cf0dd21632ec1f39` | Unmount cleanup hook, idle 500ms check, `visibilitychange` handling, DOM clearing |
| `frontend/src/pages/copilot/prepare/followupPreview.ts` | 170 | `9dc520c21c3f9700e6bb6c97cf4ef17c0bf3c946` | Preserved pure template generator and normalization logic |
| `frontend/tests/followupPreviewController.test.ts` | 280 | `24c2eda350fd8181d3255ccfcd40c7c5968243ef` | Added negative concurrency, unmount fencing, monotonic rollback, and scope fencing tests |

All files in `frontend/src/pages/copilot/prepare/` remain strictly below 200 lines:
- `followupPreview.ts`: 170 lines
- `followupPreviewController.ts`: 183 lines
- `FollowupPreview.tsx`: 136 lines

### Preservation of Dirty Source
- All pre-existing dirty working tree changes in `lotus_fin/` and other directories were strictly preserved without reverts or modification.
- Zero Git commits or pushes were performed.

---

## 6. Remaining Product / Security Decisions

1. **Production Mount Policy:** `FollowupPreview` remains deliberately **unmounted** from production React tree (`LotusCopilotDrawer`, `CopilotPage`). Product & Security approval is required prior to introducing an entry point in production.
2. **Template & TTL Formal Freeze:** The literal template (`followup.neutral.vi.v1`) and 600-second absolute TTL remain **PROPOSED**. Formal organizational sign-off (L3-01 through L3-04) is required.
3. **Clipboard Telemetry / Audit Requirements:** The local preview operates without telemetry or persistence. If operational audit logging is required for copied plain text, a privacy review must define the non-retention boundary.

---

## 7. Submission Verdict

`L3_BUILDER_READY_FOR_RECHECK`
