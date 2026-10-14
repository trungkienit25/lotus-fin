# P6 V1 PastFinalDue — Security Self-Assessment

## 1. Threat Modeling & Attack Surface Review

| Attack Vector | Vulnerability Preconditions | Mitigation Implemented | Verdict |
|---|---|---|---|
| **Cross-Tenant Leakage** | Multi-tenant observation store or mixed query criteria | Strict predicate equality: `observation.tenant_id == context.site_id` and `observation.company_id == context.company_id`. Mismatches return `EMPTY_RESULT` without error details or existence leakage. | **SECURE** |
| **Token Forgery / Tampering** | Client tampering with `selection_ref` | Purpose-bound HMAC-SHA256 (`ActionReferenceCodec`) with canonical JSON claims (`opaque_actor`, `auth_session_binding`, `site_id`, `company_id`, `doc_id`, `record_version`). Validated in constant time. | **SECURE** |
| **Partial Data Reference Poisoning** | Attacker selects unverified invoices from an incomplete scan | Invariant enforced in `SearchOverdueInvoicesService`: If `is_truncated` or `missing_data_encountered`, `selection_ref` is stripped to `None` for all items. | **SECURE** |
| **Timezone / Boundary Manipulation** | Client attempts to claim an invoice is overdue by manipulating local clock | Server derives `site_local_date` exclusively from server-observed UTC instant (`observed_at_utc`) transformed into the authoritative IANA `site_timezone`. Client timestamps are completely ignored. | **SECURE** |
| **Floating-Point Precision Exploits** | Sub-cent residuals or NaN/Infinity causing incorrect eligibility | Monetary fields are validated as finite `Decimal` strings. Rejects `NaN`, `Infinity`, and unparseable values via Pydantic model validators. Calculations never use float. | **SECURE** |
| **Future-Posted Record Injection** | Adversarial future-dated record bypassing date filters | Evaluator detects $\text{posting\_date} > \text{site\_local\_date}$ as an unqualified anomaly, immediately downgrading the scan to `PARTIAL`. | **SECURE** |
| **ERPNext Runtime Escalation** | Code importing ERPNext SQL or bypassing Frappe permissions | Complete isolation: no imports of `erpnext.*` or direct SQL query execution. Domain model and ports are pure Python/Pydantic. | **SECURE** |

---

## 2. Cryptographic Token Invariants

1. **HMAC Binding:** Tokens are bound to the caller's session, actor identity hash, site, company, and document version.
2. **TTL Enforcement:** Expiry defaults to 300 seconds; future-issued timestamps (>60s) are rejected.
3. **Detail Navigation Reauthorization:** Possessing a signed `selection_ref` does not bypass permission checks during detail opening; fresh authorization is always required.
