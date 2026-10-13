# P2-A Controller and Application Service Wiring

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Verdict:** `CONTROLLER_WIRING = PASS` (Scoped to typed dependency composition; public API exposure remains `CAPABILITY_DISABLED` pending N0 approval)

---

## 1. Architectural Composition

The presentation controller ([invoice_actions_controller.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py)) completes the Clean Architecture dependency injection path:

```
Authenticated Lotus Fin API (invoice_actions_api.py)
       │ (Calls controller when composed; default disabled helper)
       ▼
InvoiceActionsController
  ├── ResolveReadContextService (Capability authorization & context fingerprinting)
  ├── ActionReferenceCodec (HMAC reference minting & constant-time verification)
  ├── InvoiceActionDelivery (Terminal single-envelope response & required audit)
  ├── SearchInvoicesService (Optional; typed bounded search orchestration)
  └── OpenAuthorizedInvoiceService (Optional; typed single-document reader orchestration)
       │
       ▼
IAuthorizedInvoiceReadPort (Native read adapter seam; test doubles only)
```

---

## 2. Controller Pipeline Invariants

### A. Lifecycle and Capability Guarding
- If `search_service` or `open_service` is omitted, the respective endpoint immediately returns `ActionStatus.NOT_AVAILABLE` with `ActionReasonCode.CAPABILITY_DISABLED` (HTTP 503).
- If the required audit sink is missing or failing, `self._delivery.available` is False, and all admissions fail closed (HTTP 503).
- If `config.enabled` is False, all endpoints fail closed (HTTP 503).

### B. Shared Context Resolution & Reference Verification (`_scope_context`)
The helper method `_scope_context` enforces uniform scope binding across `search_invoices` and `open_invoice`:
1. Parses the signed `context_ref` and safely extracts `company_id`.
2. Resolves fresh capability authorization via `ResolveReadContextService.execute(...)` for the specific capability (`invoice.search` or `invoice.open`).
3. Re-verifies `context_ref` against the freshly resolved context using `ActionReferenceCodec.verify_reference`.
4. Enforces strict `context_version` equality (`expected_context_version == context.context_version`).
5. Returns `(context, None)` on success, or `(None, failure_response)` on any mismatch or denial.

### C. Clean Architecture & Line Limits
- Implemented in 183 lines (strictly `< 200 lines`, satisfying ADR001).
- No business mutations, no SQL queries, no direct database access.

---

## 3. Public API Protection

In [invoice_actions_api.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/api/invoice_actions_api.py):
The public Frappe endpoints (`get_context`, `search_invoices`, `open_invoice`) maintain `_frappe_post_handler` returning `CAPABILITY_DISABLED`.
Even though unit and integration tests verify that controller wiring functions correctly when services are injected, public execution must NOT be enabled until an approved native read adapter (N0) is provided.

---

## 4. Test Evidence

Tested via [test_invoice_controller_wiring.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/tests/test_invoice_controller_wiring.py):
- `test_controller_disabled_by_default_without_services`: PASS (`CAPABILITY_DISABLED`, 503).
- `test_controller_full_pipeline_with_injected_services`: PASS (Full pipeline `get_context` -> `search_invoices` -> `open_invoice` returns 200 OK and expected projections).
- `test_controller_invalid_request_fails_closed`: PASS (`INVALID_REQUEST`, 422).
- `test_controller_tampered_context_ref_fails_closed`: PASS (Fails closed on tampered ref).

**Result:** `4 passed in 1.28s (exit 0)`.
