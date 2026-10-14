# P2-A Configuration Loader Implementation

**Date:** 12 October 2026  
**Timezone:** Asia/Saigon  
**Branch:** `codex/p2a-invoice-read-backend`  
**HEAD:** `5f805ef34f788245a3ec0e9c2f44e224eb16c305`  
**Verdict:** `CONFIG_LOADER = PASS` (Scoped to isolated loader implementation; live site startup remains `BLOCKED` pending site config provisioning)

---

## 1. Overview and Design

To address the architectural gap where no qualified Frappe configuration loader existed for Lotus Fin, `InvoiceActionsConfigLoader` was implemented in:
[invoice_actions_config_loader.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config_loader.py).

The implementation strictly satisfies ADR001 (< 200 lines: actual 124 lines) and adheres to Clean Architecture principles: Frappe provides underlying site-configuration infrastructure without acting as a financial or product authority.

---

## 2. Security & Operational Specifications

### A. Approved Key Enforcement
The loader accepts only explicitly approved configuration keys:
`enabled`, `signing_key_id`, `signing_secret`, `reference_ttl_seconds`, `deadline_ms`, `page_size_default`, `page_size_max`, `allowed_capabilities`, `connections`.
Any unexpected or unapproved key triggers `ConfigurationError` and fails closed.

### B. Secret Handling & Redaction
- Minimum signing secret length of 32 characters is enforced.
- Known weak development keys (e.g. repeated dummy strings) are strictly rejected when `enabled=True`.
- Secrets are never included in exception messages, string representations, or audit logs.
- Secrets are excluded from cache fingerprint computations.

### C. Multi-Tenant & Multi-Site Isolation
- In-memory cache is partitioned strictly by `current_site` (`_site_cache[current_site]`).
- Prevents cross-site or cross-tenant configuration reuse.
- Validates that `ApprovedConnection.site_id` strictly matches the active site.

### D. Rotation & Invalidation Semantics
- Configuration is fingerprinted via SHA256 over canonicalized key-value pairs.
- Configuration rotation in Frappe site config automatically invalidates stale cache entries on next access.
- `clear_cache()` enables deterministic teardown in test fixtures.

### E. Fail-Closed Guarantees
- If Frappe is unavailable, fails closed (`ConfigurationError`).
- If current site cannot be resolved from request context, fails closed.
- If `lotus_fin_invoice_actions` section is absent in site config, fails closed.
- Never generates random secrets on-the-fly.

---

## 3. Test Coverage

Comprehensive test suite in [test_invoice_config_loader.py](file:///e:/lotus-fin/lotus_fin/lotus_fin/tests/test_invoice_config_loader.py):
1. `test_valid_approved_config`: Valid dictionary loads successfully.
2. `test_missing_config`: `None` rejected.
3. `test_missing_site`: Empty site ID rejected.
4. `test_unknown_keys_rejected`: Unapproved keys rejected.
5. `test_missing_secret`: Omitted secret rejected.
6. `test_short_secret`: Secret < 32 characters rejected.
7. `test_weak_development_secret_rejected_when_enabled`: Weak secret rejected.
8. `test_connection_site_mismatch`: Cross-site connection rejected.
9. `test_frappe_site_config_loader`: Ingestion from `frappe.get_site_config()`.
10. `test_frappe_site_config_caching_and_rotation`: Caching and rotation on change.
11. `test_cross_site_cache_isolation`: Cache isolation between site1 and site2.
12. `test_missing_lotus_section_fails_closed`: Missing configuration section fails closed.
13. `test_secret_not_leaked_in_exception`: Secret redacted from exception strings.

**Result:** `13 passed in 0.73s (exit 0)`.
