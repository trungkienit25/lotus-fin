# P2-A Pydantic Validation Recheck

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Verdict:** `PYDANTIC_VALIDATION = PASS`

---

## 1. Scope of Audit

All Pydantic v2 models in the Lotus Fin read-family were systematically audited:
- `ContextRequestDTO` ([invoice_action_request.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py))
- `ContextDataDTO` ([invoice_action_request.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py))
- `SearchRequestDTO` ([invoice_action_request.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py))
- `OpenRequestDTO` ([invoice_action_request.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py))
- `InvoiceReadFilters` ([invoice_read.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/domain/schema/invoice_read.py))
- `InvoiceReadRow` ([invoice_read.py](file:///e:/lotus-fin/lotus_fin/domain/schema/invoice_read.py))
- `InvoiceReadPage` ([invoice_read.py](file:///e:/lotus-fin/lotus_fin/domain/schema/invoice_read.py))
- `InvoiceReadDocument` ([invoice_read.py](file:///e:/lotus-fin/lotus_fin/domain/schema/invoice_read.py))
- `SearchResponseDataDTO` ([invoice_action_response.py](file:///e:/lotus-fin/lotus_fin/presentation/dto/invoice_action_response.py))
- `OpenResponseDataDTO` ([invoice_action_response.py](file:///e:/lotus-fin/lotus_fin/presentation/dto/invoice_action_response.py))

---

## 2. Invariant & Boundary Verification

### A. Required vs. Optional Fields & Null Handling
- `SearchRequestDTO.filters`: Required (`Field(...)`), cannot be omitted or `None`.
- `SearchRequestDTO.page_size`: Optional when omitted (defaults to 20); explicit `null` rejects with `ValidationError`.
- `InvoiceReadFilters.posting_from` / `posting_to`: Optional when omitted. Explicit `null` rejects with `ValidationError("Posting dates may be omitted, never explicitly null")`.
- `ContextDataDTO`: All fields required. Omission or `null` values reject.

### B. Strict Wire Date Parsing and Canonicalization
- `strict=True` is preserved on all models (`extra="forbid", strict=True`).
- Legitimate JSON wire date strings (e.g., `"2026-10-12"`) are accepted via canonical `mode="before"` validators on:
  - `InvoiceReadRow.posting_date`
  - `InvoiceReadDocument.posting_date`
  - `ContextDataDTO.default_posting_from`, `default_posting_to`, `expires_at`
- Non-canonical strings (e.g., `"2026/10/12"`, `"20261012"`, `"2026-1-1"`) are strictly rejected.

### C. Calendar and Date Range Boundaries
- **Valid Leap Year:** `"2024-02-29"` accepted.
- **Invalid Leap Year:** `"2025-02-29"` rejected (`ValueError`).
- **Calendar Boundary:** `"2026-04-31"` (April has 30 days) rejected.
- **One-Sided Pair:** Providing only `posting_from` without `posting_to` (or vice-versa) rejected.
- **Reversed Range:** `posting_to < posting_from` rejected.
- **Oversized Window:** `(posting_to - posting_from).days + 1 > 365` rejected.
- **Future Dates:** Posting dates past `today` in normalized filters rejected.

### D. Enum & Numeric Type Restrictions
- `InvoiceReadFilters.docstatus`: Only `"DRAFT"`, `"SUBMITTED"`, `"BOTH"` accepted. Arbitrary values (`"CANCELLED"`, numeric `2`, booleans) rejected.
- `InvoiceReadRow.docstatus`: Strictly integer `0` or `1`. Booleans (`True`/`False`), floats (`1.0`), and strings rejected.
- `page_size`: Must be integer `1 <= page_size <= 50`. Booleans, floats, strings rejected.

### E. Security & Privacy Guarantees
- `extra="forbid"` on all DTOs ensures parameter injection / unknown fields are rejected.
- Validation errors are sanitized at the presentation layer; raw exceptions and internal fields (secrets, keys) are never exposed to clients.
- NFC Unicode normalization is enforced on string filters (`invoice_name_prefix`).

---

## 3. Test Evidence

Executed via Python 3.13.7, pytest 9.0.2:
```powershell
$env:PYTHONPATH="e:\lotus-fin\lotus_fin;$env:PYTHONPATH"
python -m pytest lotus_fin/lotus_fin/tests/test_pydantic_b1_hardening.py
```
**Results:** `35 passed in 0.74s (exit 0)`.
Combined with existing `test_invoice_request_correction.py` (35 tests): **70 Pydantic validation tests 100% green**.
