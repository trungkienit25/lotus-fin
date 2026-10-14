# Lotus Native Adapter N0 Blockers

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Verdict:** `NATIVE_ADAPTER = BLOCKED` (Stop condition met)

---

## 1. Product Architecture Directive

> **LOTUS FIN IS FULLY INDEPENDENT FROM ERPNEXT.**  
> ERPNext must NOT be a required application, financial data source, role authority, or runtime dependency.  
> An ERPNext Sales Invoice is NOT automatically a Lotus-owned invoice.  
> Do NOT implement `tabSales Invoice` access as the default native Lotus Fin read adapter.

In accordance with Section 8 of the Master Implementation Specification, Batch B5 requires a formal native data authority decision before any database read adapter may be implemented.

---

## 2. Decision Gate Findings (A0 / N0)

An audit of repository documentation (`LOTUS_FIN_PRODUCT_INDEPENDENCE_AUDIT.md`, `LOTUS_FIN_NATIVE_DATA_AUTHORITY_MAP.md`, `LOTUS_FIN_CHATBOT_NATIVE_INTEGRATION_DESIGN.md`) confirms:

1. **Native Data Authority is UNKNOWN:**  
   Lotus Fin owns deterministic calculator algorithms, financial projections, and Clean Architecture schemas, but does NOT own an authoritative native invoice data store in the current repository.
2. **Missing Authoritative Invoice Schema:**  
   The repository contains no Lotus-owned DocType, database table, or persistent storage schema for invoices. The existing `fixtures/custom_field.json` merely attaches custom fields to ERPNext's `Company` DocType.
3. **Missing Tenant Membership Authority:**  
   Tenant and company authorization in existing modules relies on Frappe's installed ERPNext `Company` records. No Lotus-owned tenant membership authority or multi-tenant policy engine exists.
4. **Missing Lifecycle & Field-Level Policy:**  
   There is no approved specification for native invoice lifecycle (e.g. draft/approved/posted/voided transitions), field-level redaction, masking rules, or data freshness SLAs.
5. **No Approved Isolated Test Fixtures:**  
   No approved, isolated native database fixtures exist. Existing tests rely strictly on synthetic memory doubles (`ReadPort`, `FakePort`).

---

## 3. Mandatory Stop Condition Triggered

Because prerequisite N0 approvals are absent, the **STOP CONDITION** is formally executed:
- **No Native DB Adapter Implemented:** We refuse to implement an adapter querying `tabSales Invoice` or ERPNext tables.
- **No Unapproved DocTypes Created:** We refuse to invent a new DocType without Product and Data Architecture authorization.
- **No Migrations Run:** No schema migrations or patch files were created.
- **No Source Mode Relabeling:** We refuse to relabel `ERP_READ` as native authority.
- **Endpoints Kept Disabled:** Public controller and API endpoints remain disabled (`CAPABILITY_DISABLED`).

---

## 4. Requirements for N0 Unblocking

Implementation of a production `IAuthorizedInvoiceReadPort` requires the following approved artifacts:

| Requirement | Required Approver | Required Deliverable |
|---|---|---|
| **Data Authority** | Product & Data Architecture | Approved specification naming the authoritative invoice store and update authority. |
| **Canonical Schema** | Data Architecture | Versioned schema definition for Lotus invoices (e.g., DocType or relational schema). |
| **Tenant Policy** | Security Architecture | Lotus-owned tenant membership, row-level, and field-level permission policy. |
| **Token Contract Migration** | Security Architecture | Migration from `doc_type="Sales Invoice"` in `SelectionClaimsV2` to native token claims. |
| **Isolated Test Fixtures** | Platform & QA | Seeded test records in an isolated, ERP-free test environment. |
