# LOTUS FIN P4-A — REAL MOUNTED REGRESSION REPORT

**Document Identity:** `P4A_REAL_MOUNT_REGRESSION.md`  
**Date:** 2026-10-13  
**Status:** COMPLETE & QUALIFIED  
**Authors:** Staff React/TypeScript Engineer, Frontend Security Engineer  
**Target:** Playwright E2E Harness (`tests_e2e/`), Vitest/Node Unit Suites (`frontend/tests/`), Python Oracles  

---

## 1. Overview

This document presents end-to-end evidence of real mounted browser executions verifying the resolution of P1-01 and confirming zero regression across all existing P2-B, L3, and Copilot security features.

---

## 2. P1-01 Real Mounted Reproduction & Resolution Journey

### 2.1 The Mounted User Journey

The real mounted user journey mandated by Work's reproduction was implemented and verified under Playwright (`tests_e2e/test_invoice_actions_e2e.py::test_p1_01_real_mounted_reproduction`):

```
VercelChatPanel (Panel Mode)
  └─► Switch tab to "Invoice Actions"
        └─► Click "DEMO (Synthetic)" profile button
              └─► Switch tab to "Chat"
                    └─► Switch tab to "Invoice Actions"
                          └─► Fill prefix "DEMO-SINV" & Submit
                                └─► 3 synthetic DEMO rows rendered (DEMO-SINV-2026-001, -002, -003)
                                      └─► Click "Open" on record 2 (DEMO-SINV-2026-002)
                                            └─► Read-only viewer opens with approved fields
                                                  └─► Click "CORE (Frappe HTTP)" profile button
```

### 2.2 Security Assertions Verified Under Real Browser Mount

1. **Immediate Purge of Protected DEMO State:**
   - Read-only viewer (`[data-testid="read-view"]`) was unmounted instantly (`count == 0`).
   - Selected record reference (`[data-invoice-id="DEMO-SINV-2026-002"]`) was purged (`count == 0`).
   - Results container (`[data-testid="results"]`) was purged (`count == 0`).
   - Input search criteria (`[data-testid="f-prefix"]`) was cleared (`value == ""`).
2. **CORE Production Transport Guard:**
   - Under CORE, RPC `/api/method/lotus_fin.api.invoice_actions_api.get_context` returned truthful 503 `CAPABILITY_DISABLED`.
   - UI correctly displayed `<div data-testid="notice" data-reason="DISABLED">` stating *"Invoice lookup is not enabled in this environment."*
   - The search button (`[data-testid="search-btn"]`) remained strictly disabled, preventing unauthorized queries.
   - **Zero DEMO records** appeared under CORE.
3. **Clean Scenario Switches Without Remount:**
   - `CORE → DEMO`: Recovered cleanly, fetched DEMO context, enabled search button.
   - `NORMAL → PARTIAL`: Displayed incomplete results banner; open buttons disabled.
   - `PARTIAL → EMPTY`: Clean empty result notice displayed.
   - `FORBIDDEN → NORMAL`: 403 Access Denied notice rendered; cleanly recovered upon switching back to NORMAL.

---

## 3. End-to-End Test Execution Results

### 3.1 Pytest Playwright E2E Suite (10/10 Passed)

Command executed:
```bash
python -m pytest tests_e2e/test_copilot_failclosed.py tests_e2e/test_followup_preview_e2e.py tests_e2e/test_invoice_actions_e2e.py -q -p no:cacheprovider
```

Output:
```
..........                                                               [100%]
10 passed in 106.01s (0:01:46)
```

Test cases covered:
- `test_copilot_failclosed.py::test_chat_failclosed_unauthenticated` ✅ PASS
- `test_copilot_failclosed.py::test_financial_health_unqualified_toast` ✅ PASS
- `test_copilot_failclosed.py::test_xss_sanitization_in_body` ✅ PASS
- `test_copilot_failclosed.py::test_network_tampering_abort` ✅ PASS
- `test_followup_preview_e2e.py::test_followup_preview_prepare_lifecycle` ✅ PASS
- `test_invoice_actions_e2e.py::test_p2b_invoice_search_select_open_flow` ✅ PASS
- `test_invoice_actions_e2e.py::test_p2b_invoice_empty_and_partial_results` ✅ PASS
- `test_invoice_actions_e2e.py::test_p2b_invoice_scope_switch_clears_state` ✅ PASS
- `test_invoice_actions_e2e.py::test_p1_01_real_mounted_reproduction` ✅ PASS
- `test_invoice_actions_e2e.py::test_p2_07_mobile_and_accessibility` ✅ PASS

---

### 3.2 P2B React Qualification Oracle (`P2B_REACT_NEW_QUALIFIED.py`)

Command executed:
```bash
python docs/reviews/evidence/p3-independent-2026-10-13/P2B_REACT_NEW_QUALIFIED.py
```

Output (Exit Code 0):
```json
{
  "counts": { "PASS": 39, "FAIL": 0 },
  "original9": { "PASS": 9, "FAIL": 0 },
  "fresh": { "PASS": 30, "FAIL": 0 },
  "cleanup": { "server_pid": 20532, "server_exited": true, "port_released": true },
  "real_erp_calls": 0,
  "builder_factories_imported": false,
  "actual_React_components": true,
  "unexpected_network": []
}
```

---

### 3.3 Independent JS Oracles

| Script | Command | Output | Result |
| :--- | :--- | :--- | :---: |
| `demo_negative.mts` | `node --experimental-strip-types docs/reviews/evidence/p3-independent-2026-10-13/demo_negative.mts` | 4 PASS, 0 FAIL | ✅ PASS |
| `l3_oracle.mjs` | `node docs/reviews/evidence/p3-independent-2026-10-13/l3_oracle.mjs` | `{"counts":{"PASS":16,"FAIL":0}}` | ✅ PASS |
| `new_oracle.mjs` | `node docs/reviews/evidence/p3-independent-2026-10-13/new_oracle.mjs` | `{"counts":{"PASS":41,"FAIL":0}}` | ✅ PASS |
| `fresh_oracle.mjs` | `node docs/reviews/evidence/p3-independent-2026-10-13/fresh_oracle.mjs` | `{"counts":{"PASS":96,"FAIL":0}}` | ✅ PASS |
| `original23.mjs` | `node docs/reviews/evidence/p3-independent-2026-10-13/original23.mjs` | `{"counts":{"PASS":23,"FAIL":0}}` | ✅ PASS |

---

### 3.4 Frontend Unit Suites (`frontend/tests/`)

Command executed:
```bash
node --test --experimental-strip-types frontend/tests/*.test.ts frontend/tests/p2b/*.test.ts
```

Output:
```
1..106
# tests 106
# suites 0
# pass 106
# fail 0
# duration_ms 928.0396
```

All 106 unit tests passed with zero failures.
