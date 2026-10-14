# LOTUS FIN — P2-A Offline Implementation & Evidence Report

**Verdict:** `P2A_OFFLINE_LOCAL_PASS`  
**Execution Timestamp:** 2026-10-12T11:09:00+07:00  
**Environment:** Windows (win32), Python 3.13.7, pytest 9.0.2, Pydantic 2.12.5  
**Git Working Tree / Branch:** `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`

---

## 1. Executive Summary & Status

- **P2A_OFFLINE_BUILD_READY:** YES.
- **P2A_TARGET_READY:** BLOCKED (Live ERP image lacks P1/P2 host source; fixtures not provisioned).
- **P2A_LIVE_PERMISSION_QUALIFIED:** NO (Live ERP tests are `NOT_RUN`, no credentials, no live mutations).
- **Search & Open Endpoints Status:** STRICTLY DISABLED in default composition/API handlers (`CAPABILITY_DISABLED`). No ERP writes, no financial operations, no SDK dependencies.
- **P1 Baseline Verification:** 173/173 PASS (100% regression preserved).
- **P2-A Offline Unit/Contract Tests:** 19/19 PASS (100%).

---

## 2. Changed & Created Files Inventory

### A. New Modules (Domain, Port, Application, Presentation, Security)
1. `lotus_fin/lotus_fin/domain/schema/invoice_read.py`:
   - Typed filters (`InvoiceReadFilters`): bounded `invoice_name_prefix` (NFC ≤128 chars, no control/null chars), date pair invariants (`posting_from`, `posting_to` max 365 days window, no partial pairs), `docstatus` enum (`DRAFT`, `SUBMITTED`, `BOTH`).
   - Projection models: `InvoiceReadRow`, `InvoiceReadPage`, `InvoiceReadDocument`.
   - Rejects financial amounts, extra fields, arbitrary queries.
2. `lotus_fin/lotus_fin/application/port/i_authorized_invoice_read.py`:
   - Port interface `IAuthorizedInvoiceReadPort` defining `search_invoices` and `open_invoice` contracts.
3. `lotus_fin/lotus_fin/infrastructure/security/invoice_reference_claims.py`:
   - Dedicated purpose-bound claims: `SelectionClaimsV2` (`ref.v2`, `invoice.open`, exact `doc_id`, `record_version`), `CursorClaimsV2` (`ref.v2`, `invoice.cursor`, `last_id`, `page_index`, `query_fingerprint`).
4. `lotus_fin/lotus_fin/application/service/search_invoices.py`:
   - Orchestrates server-authorized search. Enforces resource bounds (page_size 1..50).
   - Invariant: Mints signed `ref.v2` selection refs for complete results (`PAGE_COMPLETE`). Strips all selection refs to `None` for `PARTIAL` results.
5. `lotus_fin/lotus_fin/application/service/open_authorized_invoice.py`:
   - Validates signed `ref.v2` selection tokens. Enforces exact scope, actor, session, company, and version match.
   - Enforces record version consistency (returns `STALE_SELECTION` if mismatch).
6. `lotus_fin/lotus_fin/presentation/dto/invoice_action_response.py`:
   - Typed response data models: `SearchResponseDataDTO`, `OpenResponseDataDTO`.

### B. Modified Files (Allowlisted)
1. `lotus_fin/lotus_fin/infrastructure/security/action_reference_codec.py`:
   - Added `sign_selection_v2` and `verify_selection_v2` supporting `ref.v2` selection tokens with constant-time HMAC-SHA256 verification and expiration checks. Preserved existing `ref.v1` context token methods.
2. `lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py`:
   - Updated `SearchRequestDTO` to require closed, typed `InvoiceReadFilters`.
3. `lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py`:
   - Integrated optional dependency injection for `search_service` and `open_service`.
   - Guaranteed `search_invoices` and `open_invoice` fail closed with `CAPABILITY_DISABLED`.

### C. Test Suites
1. `lotus_fin/lotus_fin/tests/test_invoice_read.py` (11 tests, Stage A)
2. `lotus_fin/lotus_fin/tests/test_search_invoices.py` (4 tests, Stage B)
3. `lotus_fin/lotus_fin/tests/test_open_authorized_invoice.py` (4 tests, Stage C)

---

## 3. TDD RED / GREEN Verification History

| Stage | Action / Test Module | Initial RED Output | GREEN Resolution | Final Status |
|---|---|---|---|---|
| **Stage A** | `test_invoice_read.py` | `ModuleNotFoundError: No module named 'lotus_fin.domain.schema.invoice_read'` | Implemented schema and port interface | 11 passed in 0.66s |
| **Stage B** | `test_search_invoices.py` | `ModuleNotFoundError: No module named 'lotus_fin.application.service.search_invoices'` | Implemented `SearchInvoicesService` and codec v2 signing | 4 passed in 0.68s |
| **Stage C** | `test_open_authorized_invoice.py` | `ModuleNotFoundError: No module named 'lotus_fin.application.service.open_authorized_invoice'` | Implemented `OpenAuthorizedInvoiceService` and codec v2 verification | 4 passed in 0.62s |
| **Stage D** | `invoice_actions_controller.py` & DTOs | Verified dependency wiring and disabled controller responses | Injected services; `search` and `open` return `CAPABILITY_DISABLED` | Clean composition |

---

## 4. Test Execution Evidence & Regression Matrix

### A. New P2-A Suites Run
```text
python -m pytest lotus_fin/lotus_fin/tests/test_invoice_read.py lotus_fin/lotus_fin/tests/test_search_invoices.py lotus_fin/lotus_fin/tests/test_open_authorized_invoice.py
Exit code: 0
Output: 19 passed in 0.87s
```

### B. Core P1 Regression Verification
```text
python -m pytest lotus_fin/lotus_fin/tests/test_action_outcome.py lotus_fin/lotus_fin/tests/test_action_delivery.py lotus_fin/lotus_fin/tests/test_action_security_regressions.py lotus_fin/lotus_fin/tests/test_invoice_context.py lotus_fin/lotus_fin/tests/test_action_references.py lotus_fin/lotus_fin/tests/test_invoice_auth_delivery.py lotus_fin/lotus_fin/tests/test_action_sink_ack.py lotus_fin/lotus_fin/tests/test_invoice_permission_seam.py lotus_fin/lotus_fin/tests/test_action_denial_policy.py lotus_fin/lotus_fin/tests/test_action_reference_privacy.py lotus_fin/lotus_fin/tests/test_invoice_terminal_delivery.py lotus_fin/lotus_fin/tests/test_invoice_delivery_boundary.py
Exit code: 0
Output: 173 passed in 2.66s
```

### C. Combined Related Regression Check (92 items)
```text
python -m pytest lotus_fin/lotus_fin/tests/test_invoice_read.py lotus_fin/lotus_fin/tests/test_search_invoices.py lotus_fin/lotus_fin/tests/test_open_authorized_invoice.py lotus_fin/lotus_fin/tests/test_action_references.py lotus_fin/lotus_fin/tests/test_action_reference_privacy.py lotus_fin/lotus_fin/tests/test_invoice_delivery_boundary.py lotus_fin/lotus_fin/tests/test_invoice_context.py lotus_fin/lotus_fin/tests/test_action_denial_policy.py
Exit code: 0
Output: 92 passed in 2.02s
```

### D. Syntax & Lint Compilation
```text
python -m py_compile [all new and modified files]
Exit code: 0 (No syntax or parsing errors)
```

---

## 5. Security & Boundary Checks

1. **Denial Precedence:**
   - Invalid / expired / forged tokens fail closed (`ACCESS_DENIED` or `STALE_SELECTION`).
   - Cross-scope requests (e.g. valid token for Company A presented in Company B context) are rejected immediately without invoking underlying data queries.
2. **Partial Result Safety:**
   - Incomplete or partial search results (`coverage == INCOMPLETE`) have all actionable `selection_ref` fields stripped to `None`. No executable handles can be returned for partial scans.
3. **Audit Sink & No Protected Bypass:**
   - Delivery boundary verifies required terminal events. Single correlation ID maintained throughout lifecycle.
4. **No ERP Business Writes:**
   - Pure typed ports and adapters; no `insert`, `save`, `submit`, `db_set`, or `ViewLog` modifications.
5. **Disabled Production Endpoints:**
   - Both HTTP endpoints (`search_invoices`, `open_invoice`) in `api/invoice_actions_api.py` and `presentation/controller/invoice_actions_controller.py` remain strictly disabled.

---

## 6. Real ERP Checks: NOT_RUN Notice

As mandated by preconditions and safety rules:
- **Real ERP Operations:** `NOT_RUN`
- **Live Permission Fixtures:** `NOT_RUN`
- **Docker In-Container Integration:** `NOT_RUN`
- Target container qualification remains blocked until live ERP fixtures and environment mappings are approved.

---

## 7. Next Steps & Handoff to ChatGPT Work

- Offline backend implementation of P2-A is complete and verified against local contracts.
- Ready for Work review and approval before any target deployment or P2-B frontend integration.
