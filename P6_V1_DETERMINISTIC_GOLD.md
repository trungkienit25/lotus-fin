# P6 V1 PastFinalDue — Deterministic Gold Fixtures & Matrix

This document defines the independent financial oracle truth matrix for **PAST_FINAL_DUE_INVOICES (Option B)**.

Evaluation instant: `2026-10-13T12:00:00+00:00` (Site local date in `Asia/Ho_Chi_Minh` is `2026-10-13`).
Authorized Scope: `tenant_alpha:Company Alpha`.

| Case ID | Final Due Date | Residual Amount | Lifecycle | Is Return | Currency | Scope | Expected Decision | Reason / Rule |
|---|---|---|---|---|---|---|---|---|
| **GOLD-01** | `2026-10-01` | `1000000.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Alpha` | **ELIGIBLE** | Past final due by 12 days, positive residual. |
| **GOLD-02** | `2026-10-12` | `250.75` | `APPROVED` | False | VND | `tenant_alpha:Company Alpha` | **ELIGIBLE** | Due yesterday (+1 day), positive residual. |
| **GOLD-03** | `2026-10-13` | `500000.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Due TODAY is not past final due! |
| **GOLD-04** | `2026-10-14` | `750000.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Due in future. |
| **GOLD-05** | `2026-10-05` | `0.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Settled invoice; residual is zero. |
| **GOLD-06** | `2026-10-05` | `-1500.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Credit balance; negative residual. |
| **GOLD-07** | `2026-10-05` | `200000.00` | `SUBMITTED` | True | VND | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Return document excluded. |
| **GOLD-08** | `2026-10-05` | `200000.00` | `DRAFT` | False | VND | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Unsubmitted lifecycle. |
| **GOLD-09** | `2026-10-05` | `200000.00` | `CANCELLED` | False | VND | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Cancelled lifecycle. |
| **GOLD-10** | `2026-10-05` | `500.00` | `SUBMITTED` | False | USD | `tenant_alpha:Company Alpha` | **NOT_ELIGIBLE** | Currency filter mismatch when filtered by VND. |
| **GOLD-11** | `2026-10-05` | `100000.00` | `SUBMITTED` | False | VND | `tenant_beta:Company Alpha` | **NOT_ELIGIBLE** | Cross-tenant scope mismatch. |
| **GOLD-12** | `2026-10-05` | `100000.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Beta` | **NOT_ELIGIBLE** | Cross-company scope mismatch. |
| **GOLD-13** | `2026-10-05` | `100000.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Alpha` | **UNQUALIFIED** | Posting date `2026-10-20` is future-posted. |
| **GOLD-14** | `2026-10-05` | `100000.00` | `SUBMITTED` | False | VND | `tenant_alpha:Company Alpha` | **UNQUALIFIED** | Source completeness is `PARTIAL`. |
