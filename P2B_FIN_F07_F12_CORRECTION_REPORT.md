# LOTUS FIN — P2-B FINAL RESIDUAL SECURITY CORRECTION REPORT (FIN-F07 & FIN-F12)

**Report Date:** 2026-10-12  
**Role:** Senior React/TypeScript Security Engineer and Regression-Driven Debugger  
**Target Repository:** `E:/lotus-fin`  
**Verdict:** `P2B_RESIDUAL_BUILDER_READY_FOR_RECHECK`

---

## 1. Executive Summary

This report documents the resolution of the residual security findings **FIN-F07** (search handling of malformed/unverifiable responses retaining protected context and handles) and **FIN-F12** (lack of strict real UTC timestamp validation on `source.observed_at`) in P2-B without regressing previously established P1, P2-A, P2-B, or L3 protections.

### Summary of Results

| Suite / Check | Previous Baseline | Post-Correction Status | Exit Code | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Expanded Node Oracle (`new_oracle.mjs`)** | 25 PASS / 16 FAIL | **41 PASS / 0 FAIL** | 0 | **100% Green** |
| **Actual React DOM Qualified (`P2B_REACT_NEW_QUALIFIED.py`)** | 36 PASS / 3 FAIL | **39 PASS / 0 FAIL** | 0 | **100% Green** |
| **P2-B Node Units (`frontend/tests/p2b/*.test.ts`)** | 66 PASS / 0 FAIL | **66 PASS / 0 FAIL** | 0 | **100% Green** |
| **Original Node Oracle (`original23.mjs`)** | 23 PASS / 0 FAIL | **23 PASS / 0 FAIL** | 0 | **100% Green** |
| **L3 Preview Node Oracle (`l3_oracle.mjs`)** | 16 PASS / 0 FAIL | **16 PASS / 0 FAIL** | 0 | **100% Green** |
| **L3 Followup Preview Units (`followupPreview*.test.ts`)** | 20 PASS / 0 FAIL | **20 PASS / 0 FAIL** | 0 | **100% Green** |
| **B1-S Fail-Closed E2E (`test_copilot_failclosed.py`)** | 4 PASS / 0 FAIL | **4 PASS / 0 FAIL** | 0 | **100% Green** |
| **TypeScript Typecheck & Build (`tsc -b && vite build`)** | Passed | **Passed (374 modules)** | 0 | **Clean** |
| **OxLint Security & Code Quality (`oxlint`)** | 0 errors | **0 errors, 0 warnings** | 0 | **Clean** |

---

## 2. Pre-Flight Repository & Environment State

- **Git Branch:** `codex/p2a-invoice-read-backend`
- **Git HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`
- **Architectural Isolation:** Lotus Fin remains strictly decoupled from ERPNext. No ERPNext SDK, permission logic, routes, or database assumptions were introduced.
- **Untracked / Dirty Files Preserved:** All existing workspace modifications outside the target scope remain intact.

---

## 3. Root Cause Analysis & Implementations

### Fix 1 — FIN-F07: Invalid Search Response Must Clear Protected State

**File:** `frontend/src/pages/copilot/actions/invoiceActionController.ts`

- **Root Cause:**
  In the `search` method's `vm.kind === "unavailable"` branch, any unavailable outcome set `results: null` and recorded the notice, but left `state.context` intact. For recoverable transport failures (`SOURCE_ERROR`, `TIMEOUT`), retaining context is permitted by contract to allow retry. However, for `INVALID_RESPONSE` (malformed wire, foreign `context_version`, contradictory pagination cursor, duplicate rows, wrong request ID / correlation ID), retaining context permitted handle reuse and subsequent searches against an unverifiable/corrupted context.

- **Implementation:**
  In `invoiceActionController.ts`:
  ```typescript
  else if (vm.kind === "unavailable") {
    if (vm.reason === "INVALID_RESPONSE") {
      this.clearProtected(vm);
    } else {
      this.set({ busy: null, results: null, notice: vm });
    }
  }
  ```
  When an `INVALID_RESPONSE` occurs:
  1. `clearProtected(vm)` is invoked.
  2. Authorized context is purged (`state.context = null`).
  3. Results, selection, cursor, and read view are cleared.
  4. Pending protected operations are fenced (`this.fence()`).
  5. The React UI physically disables the search submit button (`disabled={busy || !ctx}`).
  6. Automatic reuse of the context handle is prevented; a fresh context must be loaded before subsequent searches.
  7. Recoverable outages (`SOURCE_ERROR`, `TIMEOUT`) remain non-destructive as specified by contract.

---

### Fix 2 — FIN-F12: Strict Real UTC Observation Timestamp

**File:** `frontend/src/pages/copilot/actions/invoiceActionDecoderHelpers.ts`

- **Root Cause:**
  `source.observed_at` was only validated as a bounded string (`typeof s === "string" && s.length <= 64`) with control characters stripped for presentation. It lacked calendar validity, timezone verification, and ISO format constraints. Arbitrary strings, date-only values (`2026-02-28`), timezone-naive timestamps, and impossible rollover dates (`2026-02-30T01:02:03Z`) were admitted into protected state.

- **Implementation:**
  In `invoiceActionDecoderHelpers.ts`, created a dedicated, strict UTC validator `isObservationUtc` that accommodates legitimate backend precision (including microseconds `\.\d{1,6}`):
  ```typescript
  export const isObservationUtc = (s: unknown): s is string => {
    if (typeof s !== "string" || s.length < 20 || s.length > 35) return false;
    const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|\+00:00)$/.exec(s);
    if (!match) return false;
    const year = Number(match[1]);
    const month = Number(match[2]);
    const day = Number(match[3]);
    const hour = Number(match[4]);
    const minute = Number(match[5]);
    const second = Number(match[6]);

    if (year < 2000 || year > 2100) return false;
    if (month < 1 || month > 12) return false;
    if (hour > 23 || minute > 59 || second > 59) return false;

    const daysInMonth = (y: number, m: number): number => {
      if (m === 2) {
        const leap = (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
        return leap ? 29 : 28;
      }
      return [4, 6, 9, 11].includes(m) ? 30 : 31;
    };
    if (day < 1 || day > daysInMonth(year, month)) return false;

    const parsed = Date.parse(s);
    return Number.isFinite(parsed);
  };
  ```
  Integrated into `parseSource()`:
  ```typescript
  export const parseSource = (raw: Record<string, unknown> | null | undefined): SourceAnchor | null => {
    if (!raw) return bad();
    if (!isObservationUtc(raw.observed_at)) return bad();
    ...
  ```
  Any invalid observation time now causes `parseSource` to fail closed (`null`), rejecting admission into `context`, `search`, or `open` responses.

---

## 4. Test Matrix & Qualification Evidence

### 4.1 Expanded Node Oracle (`new_oracle.mjs`) — 41 PASS / 0 FAIL
Executed against all 6 invalid search cleanup assertions, 6 handle-reuse assertions, and 4 observation timestamp checks:

| Test Identifier | Status | Note |
| :--- | :--- | :--- |
| `INVALID_SEARCH_CLEARS_EXTRA_FIELD` | **PASS** | Extra unauthorized field in search response purges context |
| `INVALID_SEARCH_CLEARS_FOREIGN_VERSION` | **PASS** | Mismatched context_version purges context |
| `INVALID_SEARCH_CLEARS_CONTRADICTORY_CURSOR` | **PASS** | Next cursor without continuation purges context |
| `INVALID_SEARCH_CLEARS_WRONG_COUNT` | **PASS** | Result count mismatch fails closed and purges context |
| `INVALID_SEARCH_CLEARS_DUPLICATE_ROWS` | **PASS** | Duplicate item rows purge context |
| `INVALID_SEARCH_CLEARS_WRONG_RID` | **PASS** | Corrupted request ID purges context |
| `INVALID_SEARCH_NO_HANDLE_REUSE_EXTRA_FIELD` | **PASS** | Handle cannot be reused after extra field rejection |
| `INVALID_SEARCH_NO_HANDLE_REUSE_FOREIGN_VERSION` | **PASS** | Handle cannot be reused after version mismatch |
| `INVALID_SEARCH_NO_HANDLE_REUSE_CONTRADICTORY_CURSOR` | **PASS** | Handle cannot be reused after cursor corruption |
| `INVALID_SEARCH_NO_HANDLE_REUSE_WRONG_COUNT` | **PASS** | Handle cannot be reused after count mismatch |
| `INVALID_SEARCH_NO_HANDLE_REUSE_DUPLICATE_ROWS` | **PASS** | Handle cannot be reused after duplicate row rejection |
| `INVALID_SEARCH_NO_HANDLE_REUSE_WRONG_RID` | **PASS** | Handle cannot be reused after RID mismatch |
| `SOURCE_OBSERVATION_TIMESTAMP_REJECT_GARBAGE` | **PASS** | Arbitrary prose rejected |
| `SOURCE_OBSERVATION_TIMESTAMP_REJECT_IMPOSSIBLE_CALENDAR` | **PASS** | `2026-02-30T01:02:03Z` rejected |
| `SOURCE_OBSERVATION_TIMESTAMP_REJECT_DATE_ONLY` | **PASS** | Date-only string rejected |
| `SOURCE_OBSERVATION_TIMESTAMP_REJECT_LOCAL_NAIVE` | **PASS** | Naive non-UTC string rejected |

### 4.2 Actual React Qualified DOM Oracle (`P2B_REACT_NEW_QUALIFIED.py`) — 39 PASS / 0 FAIL
Real browser interaction via Playwright executing real Vite server with real React components:

- `DOM01_ONE_ROW_REQUIRES_CLICK`: **PASS**
- `DOM02_EXACT_READER`: **PASS**
- `DOM03_FOREIGN_SCOPE_NOT_RENDERED`: **PASS**
- `DOM04_VALID_EMPTY_RENDERED`: **PASS**
- `DOM05_VALID_PARTIAL_EMPTY_RENDERED`: **PASS**
- `DOM06_XSS_TEXT_ONLY`: **PASS**
- `DOM07_NO_RAW_REFERENCE_STORAGE_NAV`: **PASS**
- `DOM08_UNMOUNT_CLEARS_READER`: **PASS**
- `DOM09_NO_PAGE_ERROR`: **PASS**
- 10 `DOM_R2_PIN_search_*` checks (all axes): **PASS**
- 11 `DOM_R2_PIN_open_*` checks (all axes): **PASS**
- `DOM_R2_NULL_CONTEXT_OUTER_REJECT`: **PASS**
- `DOM_R2_EXPIRED_RESPONSE_search`: **PASS**
- `DOM_R2_EXPIRED_RESPONSE_open`: **PASS**
- `DOM_R2_INVALID_OPEN_HANDLES_CLEARED`: **PASS**
- `NEW_DOM_INVALID_SEARCH_CONTEXT_CLEARED`: **PASS** (previously FAIL)
- `NEW_DOM_INVALID_SEARCH_HANDLE_NOT_REUSED`: **PASS** (previously FAIL)
- `NEW_DOM_INVALID_OBSERVATION_REJECTED`: **PASS** (previously FAIL)
- `DOM_R2_DENIAL_401`: **PASS**
- `DOM_R2_DENIAL_403`: **PASS**

---

## 5. Source Fingerprints & Checksums

| File Path | SHA256 Hash |
| :--- | :--- |
| `frontend/src/pages/copilot/actions/invoiceActionController.ts` | `485341B353915D0E5EC05DA9AD1A7247833B5BC2482BC3B3AA0917F8DC176843` |
| `frontend/src/pages/copilot/actions/invoiceActionDecoderHelpers.ts` | `8F575B3C6471B7A5A7428BC7FABE4366CE11B19E35656EB686564DED5D745F0F` |

---

## 6. Remaining Product / Security Decisions

1. **Independent Formal Acceptance:**
   The corrections made here turn all offline reproduced test cases and browser oracles 100% green. Formal production deployment, mount approval, or enterprise permission authority requires independent review sign-off.
2. **Scope Fencing vs Native Authorization:**
   Client-side lifecycle fencing and handle clearing protect the local React session from stale or malformed data reuse; they do not replace server-side authorization enforcement.

---

## 7. Submission Verdict

`P2B_RESIDUAL_BUILDER_READY_FOR_RECHECK`
