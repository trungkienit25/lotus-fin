# P6 V1 PastFinalDue — Native Data Handoff Specification

## 1. Handoff Purpose
This document provides the enterprise Data Engineering team with the exact requirements, field mappings, precision rules, and qualification prerequisites for unlocking the **N0 Native Data Gate**.

---

## 2. Field Mapping & Typings

| Native Source Field | Required Domain Mapping | Type | Required Semantics | Fallback Permitted |
|---|---|---|---|---|
| `invoice_id` / `name` | `invoice_id` | `str` (max 128) | Unique invoice identifier within company. | **NO** |
| `tenant_id` / `site` | `tenant_id` | `str` (max 128) | Multi-tenant tenant identifier. | **NO** |
| `company` | `company_id` | `str` (max 128) | Legal company entity. | **NO** |
| `docstatus` / `status` | `lifecycle_status` | `str` | Must be `SUBMITTED`, `APPROVED`, or `1`. | **NO** |
| `is_return` | `is_return` | `bool` | True if document is a return/credit note. | **NO** |
| `due_date` | `final_due_date` | `date` (ISO 8601) | Authoritative latest contractual final due date. | **NO** (never guess) |
| `outstanding_amount` | `outstanding_balance` | `str` (finite Decimal) | Current outstanding residual balance. | **NO** (never substitute 0) |
| `party_account_currency`| `party_account_currency` | `str` (3-char ISO) | Currency of the receivable party account. | **NO** |
| `modified` | `document_version` | `str` | Optimistic locking token / version string. | **NO** |

---

## 3. Qualification & Audit Prerequisites for N0 Gate Unblock

1. **Independent Balance Reconciliation Oracle:**
   The source must prove that `outstanding_amount` directly reconciles with verified General Ledger / Payment Ledger entries, excluding settled credits and returns.
2. **Authoritative Final Due Date Audit:**
   For invoices with payment term schedules, the final due date must be verified as the latest contractual installment date.
3. **Multi-Tenant Isolation Verification:**
   Cross-tenant or cross-company queries must strictly return empty sets without latency or error variance that could leak entity existence.
4. **Zero Accounting Mutation Proof:**
   The adapter must execute purely read-only queries with zero side effects on accounting tables, ledger state, or document update timestamps.
