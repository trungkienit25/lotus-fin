# P2-A Backend Root Cause Report

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Verdict:** `BACKEND_BUILDER_READINESS = PASS` (Scoped strictly to tested backend hardening; independent acceptance pending)

---

## 1. Executive Summary

This report documents the root-cause investigation, reproduction, minimal correction, and verification across the Lotus Fin P2-A backend architecture and read-family contracts.

In accordance with the non-negotiable architectural invariant:
> **LOTUS FIN IS FULLY INDEPENDENT FROM ERPNEXT.** Frappe is utilized purely as an underlying application framework (routing, sessions, caching, site infrastructure). ERPNext is NOT a required application, financial data source, role authority, or runtime dependency.

### Root-Cause Analysis Matrix

| ID | Issue Description | Root Cause | Impact | Verification | Status |
|---|---|---|---|---|---|
| **RC-01** | Wire string dates rejected in `InvoiceReadRow`, `InvoiceReadDocument`, `ContextDataDTO` | Models enforced `strict=True` with `date` / `datetime` types without `mode="before"` wire parsing adapters. Deserialized JSON payloads passed string representations which triggered `ValidationError`. | Legitimate JSON wire round-trips failed at deserialization boundary. | Added `@field_validator(..., mode="before")` parsing ISO dates canonically. 35/35 tests green in `test_pydantic_b1_hardening.py`. | **RESOLVED** |
| **RC-02** | Absence of Lotus-owned Frappe Configuration Loader | Production configuration relied on test factories (`make_test_config`); no site-isolated, schema-validated loader existed to ingest Frappe site config. | Startup and configuration composition lacked qualified framework binding and secret-isolation guarantees. | Implemented `InvoiceActionsConfigLoader` (< 200 lines) with site binding, cache isolation, weak-secret rejection, and reload support. 13/13 tests green in `test_invoice_config_loader.py`. | **RESOLVED** |
| **RC-03** | Controller search & open endpoints hardcoded to disabled stubs without dependency wiring | Controller methods `search_invoices` and `open_invoice` returned hardcoded `CAPABILITY_DISABLED` unconditionally; dependency injection of application services was incomplete. | Search and open use cases could not be executed through controller composition even in controlled testing environments. | Implemented typed composition with `_scope_context`, capability checks, and injected `search_service` / `open_service`. Public endpoints remain disabled by default. 4/4 tests green in `test_invoice_controller_wiring.py`. | **RESOLVED** |
| **RC-04** | Missing native invoice data source & tenant authority (N0 gate) | No Lotus-owned invoice DocType, table, schema, or update authority exists. Product models inherited ERPNext `tabSales Invoice` semantics without an approved native contract. | Real database read adapter cannot be implemented without inventing unapproved data structures or violating ERP independence. | Explicit STOP CONDITION triggered at Batch B5. Prohibited `tabSales Invoice` fallback. Documented in `LOTUS_NATIVE_ADAPTER_N0_BLOCKERS.md`. | **STOP CONDITION MET / BLOCKED** |

---

## 2. Source Integrity and Manifest

### Modified Production Files
1. `lotus_fin/lotus_fin/domain/schema/invoice_read.py` (172 lines, ADR001 compliant)
2. `lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py` (107 lines, ADR001 compliant)
3. `lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py` (183 lines, ADR001 compliant)

### New Production Files
1. `lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config_loader.py` (124 lines, ADR001 compliant)

### New Test Suites
1. `lotus_fin/lotus_fin/tests/test_pydantic_b1_hardening.py` (35 test cases)
2. `lotus_fin/lotus_fin/tests/test_invoice_config_loader.py` (13 test cases)
3. `lotus_fin/lotus_fin/tests/test_invoice_controller_wiring.py` (4 test cases)

---

## 3. Regression & Invariant Verification

- **P1/P2-A Unit Regression Suite:** 395 tests passing (343 baseline + 52 new hardening cases), 0 failures, 0 errors in 5.12s.
- **A16 Required Sink Preservation:** 14/14 PASS.
- **B03 Seam & Exact Permission Checks:** 8/8 PASS.
- **Backend Independent Oracle Replay:** 36/36 PASS.
- **Boundary Oracle:** 14/14 PASS.
- **Denial Oracle:** 12/12 PASS.
- **Frontend Source:** 0 lines modified (read-only preservation maintained).
