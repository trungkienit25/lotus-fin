# AI003 Foundation Remediation Report — AI001/AI002 platform blockers

- Date: 2026-09-29
- Base commit: `030ccc3c46bd6e22443c1a008818954829a6ec3b` (branch `feature/cash-flow-forecast-copilot`)
- Scope: Platform blockers in AI001/AI002 that gate AI003 contract freeze (SSOT §23 "STILL OPEN" rows). No AI003 code was built.
- Gate note (updated 2026-09-30): foundation code/unit verification is PASS and the next Work verification can begin. Formal AI003 contract gates remain separate; see SSOT §29.

## FIXED

### Bucket A — AI001 fail-closed source validation
- `parse_ar_data` / `parse_ap_data` now raise typed `FinancialSourceDataError` on: non-dict rows, rows missing every outstanding-amount alias, or unparseable amount values. Malformed rows are never silently skipped; a valid row beside a malformed one never produces a partial sum.
- New `validate_source_payload()`: a report response counts as data ONLY when `status == "success"` AND `data` is present AND `data` is a list. Unknown status (`status=mystery`), missing `data`, and non-list `data` become typed unavailable/error states. `status="error"` keeps existing handling. Raw list payloads remain accepted for the trusted `raw_sources` test/mock injection path.
- In `build_financial_snapshot`: malformed AR/AP data (parser raise) or invalid envelope → metrics `UNAVAILABLE` with limitation `AR/AP source data invalid: ...`, source added to `missing_inputs`, never `AVAILABLE=0`. Legitimate `status=success, data=[]` remains the only verified zero.
- Same envelope validation applied to the Trial Balance cash source (missing `data` no longer reads as empty ledger).
- Deprecated `predict_cashflow` (AR−AP proxy): non-dict rows, missing amounts, or non-numeric amounts now return a typed error instead of being summed as `0.0`.

### Bucket B — AI001 request/cutoff validation
- `as_of` is now fully validated (strict ISO date / ISO datetime); invalid values return a typed `VALIDATION_ERROR` and are never silently replaced by `period_end` (old code truncated to 10 chars and fell back).
- `as_of < period_start` → typed `VALIDATION_ERROR`.
- `as_of > period_end` continues to clamp to `period_end` (cutoff semantics, not a fallback).
- Previous-period comparison now uses a consistent effective period length: the previous snapshot is fetched with `as_of = prev_start + (effective_end − period_start)`, so a mid-period cutoff compares equal-length windows (SSOT replay case: current `2026-01-01..06-30` ⇄ prior `2025-01-01..06-30`, not the full 2025 year).
- Explicit limitation added whenever a mid-period cutoff is used: posting-date semantics only; `as_known_at` historical replay of backdated/cancelled postings is NOT supported (no such support is claimed anywhere).

### Bucket C — Currency safety
- New `security/access.py::get_company_accounting_currency()` reads `Company.default_currency` server-side.
- `build_financial_snapshot` resolves the company accounting currency in the Frappe-DB environment: a requested currency that does not match (case-insensitive) returns a typed `VALIDATION_ERROR` ("FX conversion is not implemented"); the metric label is always the server-resolved currency. Undeterminable company currency also fails closed. USD-on-VND relabeling is now impossible.
- `build_comparison_block` refuses current/baseline comparison across different currencies (previously only company was compared).
- AI002 Finance Book: `get_ai002_cash_forecast` now accepts `finance_book` and forwards it to `ForecastRequest`; `validate_forecast_request` rejects any supplied value with a typed error "Finance Book scope is not supported in this version" — the field in the request contract is no longer silently ignored. No Finance Book support was invented.

### Bucket D — AI002 cache authorization
- New `_reauthorize_cached_resources()` in `cashflow/service.py`: every cache hit re-runs `check_ai002_report_permission` for the full AI002 report allowlist (General Ledger, Accounts Receivable, Accounts Payable, Trial Balance) for the requesting user before any cached financial data is returned.
- On reauthorization failure: the stale entry is evicted (`evict_cached_response`) and a typed `FORBIDDEN` fail-closed response with no financial payload (no opening cash, obligations, events, points) is returned — even inside the 300s TTL.
- Cache isolation untouched: the compound key still includes user/company/cutoff/horizon/scope/source mode/version; only success responses are still cached.

## NOT FIXED (explicitly out of scope / remaining)
- P&L account-name heuristic mapping and TB cash-account matching (SSOT §23 "P&L mapping") — unchanged.
- `as_known_at` historical replay (backdated/cancelled postings) — still unsupported, now explicitly declared in limitations.
- FX conversion — still unimplemented (rejected, not approximated).
- Finance Book end-to-end filtering — still unsupported (explicit rejection instead).
- Container/runtime alignment, `ai002_approved_cash_accounts` migration on the site, site timezone `Africa/Abidjan` vs contract `Asia/Ho_Chi_Minh` — deployment concerns, not code-addressable here.
- AI001 evidence replay/drilldown, AI003 temporal/role/gold E2E — not started (AI003 build out of scope).

## FILES CHANGED
| File | Change |
| --- | --- |
| `lotus_fin/ai/financial_snapshot.py` | `FinancialSourceDataError`, `validate_source_payload`, strict AR/AP parsers, strict envelope validation for P&L/AR/AP/TB, as_of validation, previous-period alignment, currency authority, as_known_at limitation |
| `lotus_fin/ai/financial_health.py` | Cross-currency comparison block refusal |
| `lotus_fin/security/access.py` | `get_company_accounting_currency()` |
| `lotus_fin/cashflow/validation.py` | `finance_book` explicit NOT_SUPPORTED check |
| `lotus_fin/cashflow/service.py` | Cache-hit report reauthorization + eviction + typed FORBIDDEN |
| `lotus_fin/cashflow/cache.py` | `evict_cached_response()` |
| `lotus_fin/api/ai_insights.py` | `finance_book` endpoint param; deprecated `predict_cashflow` strict row/amount validation |

## TESTS ADDED
`lotus_fin/tests/test_ai003_foundation_remediation.py` — 32 tests:

- Bucket A (16): malformed AR/AP row (missing amount, unparseable amount, `None`, non-dict row), mixed valid/invalid rows (parser-level and snapshot-level), unknown report status, missing `data`, non-list `data`, success-empty verified zero (parser + snapshot), unknown-status snapshot `PARTIAL` not `OK`.
- Bucket B (7): invalid `as_of` (`2026-13-01`), garbage `as_of`, `as_of < period_start`, mid-period cutoff filter propagation + `as_known_at` limitation, previous-period effective-length alignment (P&L window + AR `report_date`), full-year previous period when no cutoff, zero prior denominator → relative change unavailable.
- Bucket C (6): USD-on-VND tampering rejected, case-insensitive match normalized to server currency, undeterminable company currency fails closed, `get_company_accounting_currency` unit behavior, cross-currency comparison block, AI002 `finance_book` explicit rejection.
- Bucket D (3): revoked permission on cache hit → `FORBIDDEN` with no financial payload + eviction; regrant restores authorized behavior; cross-user cache isolation preserved.

## TEST RESULTS

```yaml
environment:
  verified_on: 2026-09-30
  workspace: Windows PowerShell, local Python
  docker: frappe/erpnext:v16.35.0 plus current lotus_fin in image lotus-fin:ai003-local
commit: 030ccc3c46bd6e22443c1a008818954829a6ec3b + uncommitted remediation changes
commands:
  - python -m unittest -q lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_financial_health lotus_fin.tests.test_explanation lotus_fin.tests.test_cashflow_engine lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed
  - python -m unittest -q lotus_fin.tests.test_ai003_foundation_remediation
  - docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -q lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_financial_health lotus_fin.tests.test_explanation lotus_fin.tests.test_cashflow_engine lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed lotus_fin.tests.test_ai003_foundation_remediation
collected: 159 (127 existing + 32 new)
workspace: 159 passed, 0 failed
docker: 159 passed, 0 failed
```

The Docker run initially exposed four cash-scope tests that mocked `frappe.db` but allowed real Company authorization to run when Frappe was installed. Those tests now mock the Company authorization dependency; the forbidden-account test also asserts that its target resolver was called. No production authorization logic was changed. The local image includes the AI002 fixture required by the existing tests. This is unit-test verification; live site behavior and CI remain separate gates.

## BEHAVIOR BEFORE → AFTER (key cases)
| Case | Before | After |
| --- | --- | --- |
| AR/AP row without amount (`status=success,data=[{"party":"X"}]`) | `AVAILABLE=0` (SSOT §23 observed) | `UNAVAILABLE`, `AR/AP source data invalid`, source in `missing_inputs` |
| Report `status=mystery,data=[]` | `AVAILABLE=0` | Source unavailable (typed), metrics `UNAVAILABLE` |
| `status=success` without `data` | `AVAILABLE=0` | Source unavailable (typed) |
| `status=success,data=[]` | `AVAILABLE=0` | `AVAILABLE=0` (verified zero — unchanged, now the only zero path) |
| `as_of=2026-13-01` | Silently used `period_end` | `VALIDATION_ERROR` |
| `as_of` before `period_start` | `PARTIAL` with inverted P&L window | `VALIDATION_ERROR` |
| Mid-period cutoff + `PREVIOUS_PERIOD` | Prior window full length (`as_of=None`) | Prior window aligned to effective current length + explicit `as_known_at` limitation |
| VND company + `currency=USD` request | Revenue labeled `USD`, no FX | `VALIDATION_ERROR` ("FX conversion is not implemented") |
| Current vs baseline different currency labels | Compared anyway | Comparison `UNAVAILABLE` |
| AI002 request with `finance_book` | Field silently ignored | Typed validation error (explicitly not supported) |
| Permission revoked while AI002 response cached (TTL 300s) | Cache hit returned financial data without report reauthorization | Reauthorization on hit → `FORBIDDEN`, no financial payload, cache evicted; regrant restores |

## REMAINING LIMITATIONS
1. The 159 unit tests pass in the workspace and Docker image. Live site report queries, authorization with real users, and CI are not covered by these unit runs.
2. In a live Frappe-DB environment the new currency check depends on `Company.default_currency` being set; a company without it now fails closed (`VALIDATION_ERROR`) instead of returning mislabeled metrics.
3. The previous-period alignment changes the ERPNext filter values for prior snapshots when a mid-period `as_of` is used (intended); prior P&L/AR/AP numbers for such requests will differ from the old (inconsistent) behavior.
4. The cache-hit reauthorization adds 4 report-permission checks per cache hit (cheap DB/permission lookups) — accepted for correctness; the single-flight key still omits user/scope (pre-existing perf gap, SSOT §14, untouched).
5. This remediation clears the code-level trust blockers listed in SSOT §23 rows 1–3 and the currency/Finance Book rows at unit-test level. The local Docker image is aligned to the workspace; migration, timezone, and live site behavior still need separate verification.

## READY FOR WORK VERIFICATION: YES

The 159-test unit gate passed in the workspace and Docker, and the local image contains the current app. This YES authorizes the next verification phase; it does not mean live site or AI003 contract gates passed. Read-only checks on 2026-09-30 still found `Company.ai002_approved_cash_accounts` absent and site timezone `Africa/Abidjan`. CI, migration, live report/security replay, and independent gold remain outstanding. AI001/AI002 remain upstream candidates; AI003 contract freeze stays NOT_READY.

## POST-VERIFICATION UPDATE — 2026-09-30

Work verification has now run on a separate migrated site, `ai003-verify.localhost`. The original site's schema and timezone remain as described above. Live ERPNext AR/AP reports include a total footer row that the current AI001/AI002 parsers reject, leaving AI001 AR/AP unavailable and AI002 forecast at typed `SOURCE_ERROR`. A missing Party Type master also exposed potential AR/AP cross-leg misclassification. See [`evidence/AI003_WORK_VERIFICATION_2026-09-30.md`](evidence/AI003_WORK_VERIFICATION_2026-09-30.md) and SSOT §30 for the source oracle, security checks, remediation requirements, and latest gate. **Work verification is blocked by WV-01/WV-02; contract freeze remains NOT_READY.**
