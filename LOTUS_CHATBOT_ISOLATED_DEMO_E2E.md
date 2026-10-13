# LOTUS FIN — ISOLATED SYNTHETIC DEMO E2E REPORT

**Document Version:** 1.0.0  
**Implementation File:** `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts`  
**Test Suite:** `frontend/tests/p3_transport_and_demo.test.ts` & `tests_e2e/test_invoice_actions_e2e.py`  

---

## 1. Objective and Architecture Constraints

The **DEMO Profile** provides a fully interactive, runnable demonstration of the canonical Sales Invoice actions lifecycle without requiring access to native production data (N0) or ERPNext dependencies.

### Invariants:
1. **Fictional Data Only**: All demo records use synthetic identifiers (`DEMO-SINV-2026-*`).
2. **Explicit Labeling**: Prominently designated in the UI as:
   `⚠️ DEMO DATA (ISOLATED SYNTHETIC PROFILE) — Fictional records for demonstration only`.
3. **Strict Source Identity**: Every response uses `mode: "DEMO_ISOLATED"`.
4. **Boundary Isolation**: The CORE profile sets `allowDemoSource = false`. If demo records are ever returned to CORE, `parseSource` fails closed with `INVALID_RESPONSE`.
5. **No Synthetic Fallback in CORE**: CORE returns 503 `CAPABILITY_DISABLED` and never silently switches to DEMO data.

---

## 2. Synthetic Fixture Inventory

| Invoice ID | Status | Posting Date | Record Version | Selection Ref | Purpose |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `DEMO-SINV-2026-001` | Submitted (`1`) | `2026-09-15` | `rec_demo_001` | `ref.v2.sel.DEMO-SINV-2026-001` | Standard submitted invoice match |
| `DEMO-SINV-2026-002` | Draft (`0`) | `2026-09-28` | `rec_demo_002` | `ref.v2.sel.DEMO-SINV-2026-002` | Draft invoice filter test |
| `DEMO-SINV-2026-003` | Submitted (`1`) | `2026-10-02` | `rec_demo_003` | `ref.v2.sel.DEMO-SINV-2026-003` | Date boundary filtering |

---

## 3. Supported Test Scenarios

The DEMO profile includes a interactive scenario selector supporting 6 distinct execution paths:

### 3.1. NORMAL Scenario (Complete Lifecycle)
1. **Context Admission**:
   - Client sends candidate company candidate (`Lotus-fin (Demo)`).
   - Server admits candidate, returns `context_ref` and date defaults (`2026-07-01` to `2026-10-12`).
2. **Search Execution**:
   - Query: `DEMO-SINV` with status `BOTH`.
   - Results: 3 rows returned with valid `selection_ref` handles.
3. **Explicit Selection**:
   - User clicks `View details` on `DEMO-SINV-2026-001`.
   - Single item or multi-item matches require explicit click (no auto-open).
4. **Read View Presentation**:
   - Read view displays exactly 5 approved fields:
     - Invoice ID: `DEMO-SINV-2026-001`
     - Invoice Type: `SALES`
     - Status: `Submitted`
     - Posting Date: `2026-09-15`
     - Record Version: `rec_demo_001`
   - Navigation kind: `LOTUS_READ_VIEW`.

### 3.2. PARTIAL Scenario
- Server returns partial invoice list with `coverage: "INCOMPLETE"`.
- Results render with warning: `Data is partial. Some items may be missing.`
- **Security Check:** All `selection_ref` handles are `null`; selection is disabled to prevent acting on unverified records.

### 3.3. EMPTY Scenario
- Query returns 0 records (`RESULTS_FOUND` with empty list, or `EMPTY_RESULT`).
- UI cleanly transitions to `No invoices found matching criteria.` without errors.

### 3.4. FORBIDDEN Scenario
- Server simulates HTTP 403 `PERMISSION_DENIED`.
- All selection handles, cached results, and open documents are purged.
- UI renders access denied notice.

### 3.5. EXPIRED Scenario
- Server simulates context expiration (HTTP 409 `CONTEXT_CHANGED`).
- UI indicates context has expired and prompts the user to re-initialize.

### 3.6. STALE Scenario
- Simulates version mismatch between context admission and search dispatch.
- Controller rejects mismatched version fail-closed.

---

## 4. Verification & Isolation Evidence

### 4.1. Unit Test Verification (`p3_transport_and_demo.test.ts`)
```
ok 90 - DEMO profile: complete Search -> Select -> Open lifecycle with DEMO_ISOLATED source (13.9ms)
ok 91 - DEMO profile: PARTIAL scenario disables selection handles (3.1ms)
ok 92 - DEMO profile: EMPTY scenario produces clean empty result (2.8ms)
ok 93 - DEMO profile: FORBIDDEN scenario clears protected state to denied notice (1.6ms)
ok 94 - DEMO Isolation: attempted DEMO source in CORE profile without allowDemoSource fails closed (1.6ms)
```

### 4.2. Playwright E2E Verification (`test_invoice_actions_e2e.py`)
```
tests_e2e/test_invoice_actions_e2e.py::test_p2b_invoice_search_select_open_flow PASSED
tests_e2e/test_invoice_actions_e2e.py::test_p2b_invoice_empty_and_partial_results PASSED
tests_e2e/test_invoice_actions_e2e.py::test_p2b_invoice_scope_switch_clears_state PASSED
```
All Playwright browser steps verified that DOM interactions, radio buttons, and open document viewers execute smoothly and teardown cleanly.
