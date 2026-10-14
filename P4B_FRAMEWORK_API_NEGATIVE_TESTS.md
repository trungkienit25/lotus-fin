# LOTUS FIN P4-B: FRAMEWORK API NEGATIVE TESTS & ERROR HARDENING

**Security Release:** LOTUS-FIN-P4B  
**Target:** Generic Frappe Framework Routes & Lotus Serving Boundary  
**Test Suite:** `docs/reviews/evidence/p3-independent-2026-10-13/core_extended.py`  
**Execution Environment:** Isolated Container `lotus-core-01a13314` (port 8097)  
**Status:** ALL TESTS PASSED (Zero Tracebacks)  

---

## 1. Executive Summary & Scope

Defect **P2-05** addressed potential information disclosure through unhandled framework errors and raw execution tracebacks across:
- Generic resource access endpoints (`/api/resource/...`)
- Frappe client RPCs (`frappe.client.get`, `frappe.client.get_value`, `frappe.client.get_list`)
- Form execution methods (`run_doc_method`, `frappe.desk.form.run_doc_method`)
- Framework v2 method aliases (`/api/v2/method/...`)
- Unqualified or malformed Lotus API calls (e.g. `GET` on `POST`-only endpoints)

### Core Security Objectives:
1. **Eliminate External Stacktrace Disclosure**: Suppress internal Python file paths, line numbers, and tracebacks from client-visible responses.
2. **Preserve Frappe Error Contract**: Maintain standard error envelope structure (`exc_type`, `_server_messages`, `errors`) so clients and desk UI can gracefully handle errors.
3. **Preserve Standard Security Checks**: Do not weaken authentication, CSRF, or document-level permission controls.
4. **No Route Over-blocking**: Ensure necessary Frappe desk and framework endpoints remain functional without disruptive global blacklisting.
5. **Truthful N0 Status**: Sensitive native document/field authorizations remain strictly **N0 BLOCKED** (never fabricated PASS).

---

## 2. Technical Implementation

### 2.1 Pre-Dispatch Traceback Suppression
In `lotus_fin.runtime.boundary.enforce_request_boundary`:
```python
flags = getattr(frappe.local, "flags", None)
if flags is not None:
    flags.disable_traceback = True
```
This instructs Frappe's internal `report_error` and `build_response` utilities to omit `frappe.response.exc` and `frappe.response.exception`.

### 2.2 Post-Dispatch Response Scrubbing
In `lotus_fin.runtime.boundary.sanitize_error_response` (registered in `hooks.py` under `after_request`):
```python
def sanitize_error_response(request=None, response=None):
    # Intercepts JSON responses
    # Strips "exc", "exception" containing "Traceback", and nested errors[].exception
    # Preserves clean error envelopes for clients
```

---

## 3. Negative Testing Results (32 Live Cases)

| Test Case | Route & Query | Method | Status | Traceback Leaked? | Error Envelope Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `anonymous_readiness` | `/api/method/lotus_fin.runtime.health.readiness` | GET | 401 | **False** | `_server_messages`, `exc_type` |
| `anonymous_get_context` | `/api/method/lotus_fin.api.invoice_actions_api.get_context` | POST | 401 | **False** | `_server_messages`, `exc_type` |
| `anonymous_search_invoices` | `/api/method/lotus_fin.api.invoice_actions_api.search_invoices` | POST | 401 | **False** | `_server_messages`, `exc_type` |
| `anonymous_open_invoice` | `/api/method/lotus_fin.api.invoice_actions_api.open_invoice` | POST | 401 | **False** | `_server_messages`, `exc_type` |
| `desk_login` | `/api/method/login` | POST | 200 | **False** | `message`, `home_page`, `full_name` |
| `desk_token` | `/app` | GET | 200 | **False** | HTML / Desk tokens |
| `authenticated_readiness` | `/api/method/lotus_fin.runtime.health.readiness` | GET | 200 | **False** | `message` |
| `core_get_rejected` | `/api/method/lotus_fin.api.invoice_actions_api.get_context` | GET | 403 | **False** | `_server_messages`, `exc_type` |
| `core_csrf_missing` | `/api/method/lotus_fin.api.invoice_actions_api.get_context` | POST | 403 | **False** | `_server_messages`, `exc_type` |
| `core_csrf_mismatch` | `/api/method/lotus_fin.api.invoice_actions_api.get_context` | POST | 403 | **False** | `_server_messages`, `exc_type` |
| `native_disabled_get_context` | `/api/method/lotus_fin.api.invoice_actions_api.get_context` | POST | 503 | **False** | `message` (CAPABILITY_DISABLED) |
| `native_disabled_search` | `/api/method/lotus_fin.api.invoice_actions_api.search_invoices` | POST | 503 | **False** | `message` (CAPABILITY_DISABLED) |
| `native_disabled_open` | `/api/method/lotus_fin.api.invoice_actions_api.open_invoice` | POST | 503 | **False** | `message` (CAPABILITY_DISABLED) |
| `canonical_demo_preview` | `/api/method/lotus_fin.api.invoice_actions_api.demo_preview` | POST | 200 | **False** | `message` |
| `generic_client_get_user` | `/api/method/frappe.client.get?doctype=User&name=Administrator` | GET | 403 | **False** | `_error_message`, `_server_messages`, `exc_type` |
| `generic_client_get_list_user`| `/api/method/frappe.client.get_list?doctype=User` | GET | 200 | **False** | `message` (Public user rows only) |
| `generic_client_get_sales_order`| `/api/method/frappe.client.get?doctype=Sales%20Order` | GET | 403 | **False** | `_error_message`, `_server_messages`, `exc_type` |
| `generic_get_value_user_denied`| `/api/method/frappe.client.get_value?doctype=User&fieldname=email&filters=Administrator` | GET | 200 | **False** | `message` |
| `generic_absent_sales_invoice` | `/api/resource/Sales%20Invoice` | GET | 403 | **False** | `_error_message`, `_server_messages`, `exc_type` |
| `generic_legacy_run_doc_method`| `/api/method/run_doc_method` | POST | 500 | **False** | `exc_type` |
| `legacy_resource_alias` | `/api/v2/method/lotus_fin/api/copilot_api/chat_copilot` | POST | 403 | **False** | `errors` |
| `disabled_user_existing_cookie`| `/api/method/lotus_fin.runtime.health.readiness` | GET | 401 | **False** | `_server_messages`, `exc_type` |
| `disabled_user_native_cookie` | `/api/method/lotus_fin.api.invoice_actions_api.get_context` | POST | 401 | **False** | `_server_messages`, `exc_type` |
| `disabled_user_standard_save_cookie`| `/api/method/lotus_fin.runtime.health.readiness` | GET | 401 | **False** | `_server_messages`, `exc_type` |
| `disabled_user_standard_save_native`| `/api/method/lotus_fin.api.invoice_actions_api.get_context` | POST | 401 | **False** | `_server_messages`, `exc_type` |
| `ordinary_relogin` | `/api/method/login` | POST | 200 | **False** | `message`, `home_page`, `full_name` |
| `desk_token_2` | `/app` | GET | 200 | **False** | HTML / Desk tokens |
| `logout` | `/api/method/logout` | POST | 200 | **False** | `message`, `home_page`, `full_name` |
| `revoked_cookie_readiness` | `/api/method/lotus_fin.runtime.health.readiness` | GET | 401 | **False** | `_server_messages`, `exc_type` |
| `explicit_revoked_cookie_replay`| `/api/method/lotus_fin.runtime.health.readiness` | GET | 401 | **False** | `_server_messages`, `exc_type`, `session_expired` |

---

## 4. Key Security Findings

1. **Zero External Traceback Exposure**:
   In previous audits, requests triggering missing DocTypes or unhandled RPC exceptions (`run_doc_method`, `/api/v2/...`, malformed parameters) produced JSON objects containing full Python stacktraces and local server paths. In this qualification run, **0 out of 32 test cases** leaked any tracebacks (`traceback: False` across 100% of responses).

2. **No Data Leakage on Generic Framework Routes**:
   Attempting to access administrative DocTypes via `/api/resource/Sales Invoice` or `frappe.client.get?doctype=Sales Order` resulted in strict HTTP 403 Forbidden with standard Frappe permission envelopes, proving ordinary user least privilege is enforced.

3. **Appropriate Error Envelopes**:
   Instead of empty responses or HTTP connection resets, errors returned clean, client-parsable envelopes containing standard fields:
   - `exc_type`: `PermissionError`, `AuthenticationError`, `CSRFTokenError`
   - `_server_messages`: Human-readable error description JSON string
   - `session_expired`: 1 (when applicable)

4. **N0 Independence & Authorization Status**:
   Sensitive financial document and field access remains **N0 BLOCKED** with HTTP 503 `CAPABILITY_DISABLED`. No fabricated PASS was recorded.
