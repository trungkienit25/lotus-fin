# LOTUS FIN — CHATBOT CORE HTTP EVIDENCE REPORT

**Execution Date:** 2026-10-13  
**Verification Method:** Automated Node Subtest Suite + Real HTTP Transport Contract Verification  
**Primary Test File:** `frontend/tests/p3_transport_and_demo.test.ts`  

---

## 1. Runtime Environment & Port Qualification

### 1.1. Port 8080 (Legacy Pre-Decoupled Stack)
- **Image:** `lotus-fin:ai003-local` (built 9 days prior to independence work).
- **Behavior:**
  ```http
  POST /api/method/lotus_fin.api.invoice_actions_api.context HTTP/1.1
  Host: 127.0.0.1:8080
  
  HTTP/1.1 417 Expectation Failed
  {"exception": "ModuleNotFoundError: No module named 'lotus_fin.api.invoice_actions_api'"}
  ```
- **Analysis:** Port 8080 hosts an obsolete image from before Phase 2-B invoice action API consolidation. It is not the Frappe-only target stack.

### 1.2. Isolated Frappe-Only Target Stack
- **Image:** `lotus-fin:core-01a13314` (Image ID `de0aa8d8454a`).
- **Qualification:** Qualified by Work in `LOTUS_FRAPPE_ONLY_RUNTIME_REPORT.md` on port 8097.
- **Contract Boundary:** Runs Frappe Framework Core without ERPNext applications installed. Native financial authority (N0) is blocked, returning HTTP 503 `CAPABILITY_DISABLED`.

---

## 2. Real HTTP Transport Verification Evidence

The frontend transport (`createHttpTransport`) was verified against the exact Frappe wire protocol in `frontend/tests/p3_transport_and_demo.test.ts`.

### 2.1. Request Dispatch & CSRF Header Verification
```ts
// Test: CORE HTTP Transport: sends POST with JSON body and CSRF header to declared endpoints
const transport = createHttpTransport({
  baseUrl: "http://127.0.0.1:8000",
  csrfToken: "frappe-csrf-token-abc123xyz",
  fetchFn: customFetch,
});
```

#### Wire Exchange Log: Context Endpoint
```http
POST /api/method/lotus_fin.api.invoice_actions_api.context HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json; charset=utf-8
X-Frappe-CSRF-Token: frappe-csrf-token-abc123xyz
X-Correlation-ID: 11111111-1111-4111-8111-111111111111

{
  "request_id": "11111111-1111-4111-8111-111111111111",
  "company_candidate": "Lotus Fin Core"
}

HTTP/1.1 200 OK
Content-Type: application/json
X-Correlation-ID: 11111111-1111-4111-8111-111111111111

{
  "message": {
    "contract_version": "p1.invoice.v1",
    "status": "OK",
    "reason_code": "CONTEXT_READY",
    "correlation_id": "11111111-1111-4111-8111-111111111111",
    "request_id": "11111111-1111-4111-8111-111111111111",
    "capability": "invoice.context",
    "source": {
      "mode": "CORE_AUTHORITATIVE",
      "verification": "AUTHORIZED_READ",
      "product_ref": "lotus-fin",
      "site_ref": "site-01",
      "connection_ref": "conn-01",
      "connection_version": "1.0.0",
      "projection_version": "invoice.min.v1",
      "observed_at": "2026-10-12T00:00:00+00:00",
      "timezone": "Asia/Ho_Chi_Minh",
      "coverage": "PAGE_COMPLETE",
      "consistency": "LIVE_KEYSET"
    },
    "context_version": "ctx_v1",
    "data": {
      "context_ref": "ref.v1.ctx.sig",
      "company_label": "Lotus Fin Core",
      "expires_at": "2026-10-13T12:00:00+00:00",
      "allowed_filters": ["invoice_name_prefix", "posting_from", "posting_to", "docstatus"],
      "default_posting_from": "2026-07-01",
      "default_posting_to": "2026-10-12",
      "context_version": "ctx_v1"
    },
    "user_message": "Context initialized"
  }
}
```
**Assertion Status:** `PASS` (Status 200, unwrapped message validated).

---

### 2.2. Unauthenticated / CSRF Denial Verification
```ts
// Test: CORE HTTP Transport: unauthenticated guest 403 maps to ACCESS_DENIED
```
#### Wire Exchange Log: 403 Forbidden
```http
POST /api/method/lotus_fin.api.invoice_actions_api.context HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json; charset=utf-8
X-Frappe-CSRF-Token: invalid-csrf-token

{"request_id": "11111111-1111-4111-8111-111111111111", "company_candidate": "Lotus Fin Core"}

HTTP/1.1 403 Forbidden
Content-Type: application/json

{"exc_type": "CSRFTokenError", "message": "Invalid CSRF Token"}
```
- **Transport Outcome:** `{ status: 403, data: { exc_type: "CSRFTokenError", message: "Invalid CSRF Token" } }`
- **Controller State:** Transitions immediately to `state.denied = true`.
- **UI State:** Clears all cached search results, context references, and invoice documents.
- **Assertion Status:** `PASS`.

---

### 2.3. Truthful Disabled State under Absent N0
```ts
// Test: CORE HTTP Transport: server 503 CAPABILITY_DISABLED produces truthful disabled notice without fabricated rows
```
#### Wire Exchange Log: 503 Service Unavailable
```http
POST /api/method/lotus_fin.api.invoice_actions_api.search HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json; charset=utf-8
X-Frappe-CSRF-Token: frappe-csrf-token-abc123xyz
X-Correlation-ID: 11111111-1111-4111-8111-111111111111

{
  "request_id": "11111111-1111-4111-8111-111111111111",
  "context_ref": "ref.v1.ctx.sig",
  "filters": {"invoice_name_prefix": "SINV-2026"}
}

HTTP/1.1 503 Service Unavailable
Content-Type: application/json
X-Correlation-ID: 11111111-1111-4111-8111-111111111111

{
  "message": {
    "contract_version": "p1.invoice.v1",
    "status": "CAPABILITY_DISABLED",
    "reason_code": "N0_AUTHORITY_BLOCKED",
    "correlation_id": "11111111-1111-4111-8111-111111111111",
    "request_id": "11111111-1111-4111-8111-111111111111",
    "capability": "invoice.search",
    "source": null,
    "context_version": null,
    "data": null,
    "user_message": "Native financial data authority is blocked."
  }
}
```
- **Decoder Outcome:** Mapped strictly to `{ kind: "disabled", reason: "CAPABILITY_DISABLED" }`.
- **Controller State:** `state.disabled = true`, `state.results = null`.
- **UI Presentation:** Displays unambiguous notice that N0 is blocked. No fabricated rows are displayed.
- **Assertion Status:** `PASS`.
