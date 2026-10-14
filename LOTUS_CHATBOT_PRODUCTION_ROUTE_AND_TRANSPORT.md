# LOTUS FIN — CHATBOT PRODUCTION ROUTE AND TRANSPORT SPECIFICATION

**Document Version:** 1.0.0  
**Target Environment:** Frappe Framework v15+ Core (ERPNext-Independent)  
**Security Classification:** Strict Fail-Closed  

---

## 1. Architecture Overview

The Lotus Fin Chatbot transport layer bridges the React frontend (`InvoiceActionPanel`, `VercelChatPanel`) with Frappe Core backend endpoints. It operates under a strict "Build Now, Data Later" model:
- **No ERPNext RPCs**: Does not rely on `erpnext.*` Python modules, `Sales Invoice` DocType CRUD, or GL entry queries.
- **Dedicated RPC Namespace**: All invoice operations route exclusively through `lotus_fin.api.invoice_actions_api.*`.
- **Truthful Status Codes**: When native financial data authority (N0) is blocked, the backend returns HTTP 503 `CAPABILITY_DISABLED`. The transport surfaces this limitation directly to the user without fabricating invoice rows or minting synthetic HMAC signatures in CORE mode.

---

## 2. Declared RPC Endpoints

| Operation | HTTP Method | Endpoint URI | Purpose | Payload Schema |
| :--- | :---: | :--- | :--- | :--- |
| **Context** | `POST` | `/api/method/lotus_fin.api.invoice_actions_api.context` | Request admission & retrieve session context token | `{"request_id": "<uuid>", "company_candidate": "<name>"}` |
| **Search** | `POST` | `/api/method/lotus_fin.api.invoice_actions_api.search` | Query invoice identifiers within date/status scope | `{"request_id": "<uuid>", "context_ref": "<sig>", "filters": {...}}` |
| **Open** | `POST` | `/api/method/lotus_fin.api.invoice_actions_api.open` | Retrieve 5 approved read-only fields for selected invoice | `{"request_id": "<uuid>", "selection_ref": "<sig>"}` |

### HTTP Method Rules
- All requests **MUST** use `POST`. `GET`, `PUT`, `DELETE`, or query-parameterized mutations are rejected with HTTP 405 / 400.
- Payload bodies **MUST** be `application/json; charset=utf-8`.

---

## 3. Security & Transport Controls

### 3.1. CSRF Token Handling
- The transport extracts the CSRF token from the browser cookie (`frappe.csrf_token` or `window.csrf_token` if defined) or the `X-Frappe-CSRF-Token` meta tag.
- Every outgoing POST request attaches the token header:
  ```http
  X-Frappe-CSRF-Token: <token_value>
  ```
- If the token is rejected (HTTP 403), the transport immediately maps the outcome to `ACCESS_DENIED`, clearing all protected context and selection handles.

### 3.2. Correlation ID & Generation Fencing
- Outgoing requests generate a unique correlation ID (`x-correlation-id`) via UUIDv4 or monotonic counter.
- The transport accepts an `AbortSignal` for request lifecycle management:
  - If a user cancels the query, changes companies, or unmounts the component, the signal aborts the active fetch.
  - Aborted requests never mutate controller state or surface stale callbacks.

### 3.3. Response Envelope & Decoding
- Frappe Framework standard envelope wraps responses inside `{"message": { ... }}`.
- The transport strips the single `message` wrapper and validates the inner contract:
  ```json
  {
    "contract_version": "p1.invoice.v1",
    "status": "OK | NOT_AVAILABLE | CAPABILITY_DISABLED | FORBIDDEN",
    "reason_code": "<code_string>",
    "correlation_id": "<uuid>",
    "request_id": "<uuid>",
    "capability": "invoice.context | invoice.search | invoice.open",
    "source": { ... },
    "context_version": "<string>",
    "data": { ... }
  }
  ```

---

## 4. Status Code Mapping Contract

| HTTP Status | Payload Status | Transport Mapped Outcome | UI Presentation Behavior |
| :---: | :---: | :--- | :--- |
| **200** | `OK` | `SUCCESS` | Normal data presentation; verified signatures exposed for selection. |
| **200** | `PARTIAL` | `SUCCESS (Incomplete)` | Rows displayed for inspection; selection handles disabled. |
| **401 / 403** | Any / None | `ACCESS_DENIED` | Clear protected state; show permission denied notice. |
| **409** | `CONTEXT_CHANGED` | `EXPIRED` | Clear selections; prompt user to refresh context. |
| **422** | `INVALID_INPUT` | `INVALID_REQUEST` | Display input validation error; no retry with same arguments. |
| **503** | `CAPABILITY_DISABLED` | `CAPABILITY_DISABLED` | Display truthful limitation notice: native authority blocked. |
| **500 / 504** | Any / None | `SERVER_ERROR` | Display service unavailable; do not fake successful read. |

---

## 5. N0 Blocked Handling in CORE Profile

When N0 native data authority is blocked:
1. `invoice_actions_api.search` and `invoice_actions_api.open` return:
   ```json
   {
     "message": {
       "contract_version": "p1.invoice.v1",
       "status": "CAPABILITY_DISABLED",
       "reason_code": "N0_AUTHORITY_BLOCKED",
       "data": null,
       "user_message": "Native financial data authority is blocked in this Frappe Core runtime."
     }
   }
   ```
2. The transport decodes this as `CAPABILITY_DISABLED`.
3. The UI strictly renders:
   > **Notice:** Nguồn dữ liệu tài chính gốc (N0) đang bị tạm khóa (CAPABILITY_DISABLED). Không thể truy xuất hóa đơn từ Core production.
4. **Invariant:** The frontend **NEVER** mints synthetic signatures, **NEVER** returns synthetic mock rows, and **NEVER** falls back silently to demo records in CORE mode.
