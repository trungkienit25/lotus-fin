# P2-A API HTTP and E2E Qualification

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Verdict:** `HTTP_INTEGRATION = BLOCKED / NOT_RUN` (L1–L3 Qualified; L4–L7 Blocked/Not Run due to N0 gate)

---

## 1. Testing Layer Hierarchy

The integration and end-to-end qualification is structured in 7 distinct layers:

| Layer | Scope | Prerequisites | Status | Evidence |
|---|---|---|---|---|
| **L1** | Pydantic DTOs & HMAC Token Lifecycles | Python 3.13, Pydantic v2 | **QUALIFIED (PASS)** | 395 unit tests green (35 new B1 hardening tests). |
| **L2** | Controller Composition & Service Wiring | Application services, test port doubles | **QUALIFIED (PASS)** | 4/4 tests green in `test_invoice_controller_wiring.py`. |
| **L3** | Config Loader & Framework Integration | Frappe mock context, site config loader | **QUALIFIED (PASS)** | 13/13 tests green in `test_invoice_config_loader.py`. |
| **L4** | Real Native Read Adapter | N0 Approved Native Authority | **BLOCKED** | N0 data authority unapproved; tabSales Invoice forbidden. |
| **L5** | Serving HTTP (CSRF, POST, Headers, Envelope) | Deployed Frappe site, running workers | **BLOCKED / NOT_RUN** | No approved native runtime; public routes disabled. |
| **L6** | Browser-to-Native-Backend E2E | Integrated React UI + Native HTTP API | **BLOCKED / NOT_RUN** | UI transport disabled; backend routes disabled. |
| **L7** | Runtime No-Write Qualification | Isolated database snapshots before/after | **BLOCKED / NOT_RUN** | Requires persistent native store. |

---

## 2. API Wire Contract & HTTP Specification

The declared Frappe endpoints in [invoice_actions_api.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/api/invoice_actions_api.py) enforce:

1. **POST Only:** Any GET request is rejected with `405 Method Not Allowed`.
2. **Guest Forbidden:** `allow_guest=False`. Unauthenticated or Guest sessions receive `401 Authentication Required`.
3. **Single Response Envelope:** All responses follow the strict P1 outcome format:
   ```json
   {
     "message": {
       "contract_version": "p1.invoice.v1",
       "status": "OK",
       "reason_code": "CONTEXT_READY",
       "correlation_id": "c1234567-89ab-4cde-8fab-0123456789ab",
       "request_id": "b1234567-89ab-4cde-8fab-0123456789ab",
       "capability": "invoice.context",
       "source": { ... },
       "context_version": "...",
       "data": { ... },
       "user_message": "..."
     }
   }
   ```
4. **Header Invariants:**
   - `Content-Type: application/json`
   - `Cache-Control: no-store, no-cache, must-revalidate`
   - `X-Correlation-Id: <server_cid>`

---

## 3. Reproducible HTTP Client Examples (cURL)

Below are sanitized examples for live testing once the native runtime is qualified:

### A. Context Resolution (`invoice.context`)
```bash
curl -X POST "https://<SITE_DOMAIN>/api/method/lotus_fin.api.invoice_actions_api.get_context" \
  -H "Content-Type: application/json" \
  -H "X-Frappe-CSRF-Token: <CSRF_TOKEN>" \
  -H "Cookie: sid=<ACTIVE_SESSION_ID>" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "company_candidate": "<COMPANY_LABEL>"
  }'
```

### B. Bounded Invoice Search (`invoice.search`)
```bash
curl -X POST "https://<SITE_DOMAIN>/api/method/lotus_fin.api.invoice_actions_api.search_invoices" \
  -H "Content-Type: application/json" \
  -H "X-Frappe-CSRF-Token: <CSRF_TOKEN>" \
  -H "Cookie: sid=<ACTIVE_SESSION_ID>" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440001",
    "context_ref": "<CONTEXT_REF_FROM_GET_CONTEXT>",
    "expected_context_version": "<CONTEXT_VERSION_FROM_GET_CONTEXT>",
    "invoice_type": "SALES",
    "filters": {
      "posting_from": "2026-07-15",
      "posting_to": "2026-10-12",
      "docstatus": "BOTH"
    },
    "page_size": 20
  }'
```

### C. Open Authorized Invoice (`invoice.open`)
```bash
curl -X POST "https://<SITE_DOMAIN>/api/method/lotus_fin.api.invoice_actions_api.open_invoice" \
  -H "Content-Type: application/json" \
  -H "X-Frappe-CSRF-Token: <CSRF_TOKEN>" \
  -H "Cookie: sid=<ACTIVE_SESSION_ID>" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440002",
    "context_ref": "<CONTEXT_REF_FROM_GET_CONTEXT>",
    "expected_context_version": "<CONTEXT_VERSION_FROM_GET_CONTEXT>",
    "selection_ref": "<SELECTION_REF_FROM_SEARCH_ROW>"
  }'
```

*(Note: In current deployment, all three endpoints truthfully return `503 CAPABILITY_DISABLED` pending N0 qualification.)*
