# AI002 Cash-flow Forecast Copilot — Technical Documentation

## 1. System Overview & Architecture

The **AI-F002 Cash-flow Forecast Copilot** provides a deterministic 30-day daily EOD cash forecast with bounded agentic AI explanation, built on ERPNext/Frappe.

### Governing Architectural Invariant
> `ERP truth → deterministic policy → deterministic finance → typed evidence → bounded agent → grounded explanation`

The Large Language Model (LLM) never computes, estimates, or alters financial numbers. Financial truth is strictly computed in-memory using Python `Decimal` arithmetic.

**Remediation status (round 5, this revision):** rounds 3–4 closed the six confirmed P0 defects (AR/AP error→zero, fabricated reconciled zero, silent 50-account UI scope, totals-only TB reconciliation, unverified no-events baseline, authorization-after-scope-query). Round 5 closes two more: (7) **Account read permission** is now enforced in scope resolution — a doctype-level check plus a permission-aware `frappe.get_list` read with full pagination (`frappe.get_all` is never used as authorization evidence); partial Account visibility (visible < existing) is a typed permission failure, never a partial scope; (8) the **approved per-company Cash/Bank scope** (`Company.ai002_approved_cash_accounts`, JSON list, installed via Custom Field fixture on `bench migrate`) is the only account authorization — the `restricted` name heuristic is removed; missing/invalid/stale configuration yields `NEEDS_REVIEW` and blocks the forecast, and a client-supplied scope must exactly equal the approved scope. **Last known test run: 79/79** (operator-run on the round-4 revision). **Round-5 code has NOT been executed** (authoring session cannot spawn a shell: `spawn bash.exe EACCES`); §6 lists the commands that must run before any PASS is claimed.

---

## 2. Core Components

### 2.1 Data Models & Types (`models.py`)
- **`ForecastRequest`**: Strictly validated typed parameters including `company`, `financial_as_of`, `forecast_start`, `forecast_end`, `reporting_currency`, and `coverage_scope` (`TRADE_ONLY`).
- **`ForecastResponse`**: Formal envelope returning `status`, `opening_cash`, `forecast_points`, `obligations`, `cash_events`, `coverage`, `shortfall_events`, `explanation`, and `evidence_refs`.
- **`OpeningCash`**: Aggregated cash & bank balance reconciled with Trial Balance, tracking `has_constituent_deficit`.
- **`ShortfallEvent`**: Explicit tracking of negative modeled cash (`INHERITED_FROM_OPENING` vs `NEW_MODELED_DEFICIT`).

### 2.2 Deterministic Forecast Engine (`engine.py`)
- $O(N)$ in-memory daily running sum:
  $$\text{modeled\_cash}(EOD_t) = \text{opening\_cash} + \sum \text{inflows}_{\le t} - \sum \text{outflows}_{\le t}$$
- Evaluates exactly 30 calendar days.
- Implements the Shortfall State Machine (distinguishing inherited deficits from newly modeled negative balances).

### 2.3 Data Adapters & Sources (`adapters.py`, `source_interface.py`)
- **GL Opening Cash**: Single SQL query window over `tabGL Entry` filtered by authorized company and posting date.
- **Trade Obligations (Fix A, fail closed)**: point-in-time `Accounts Receivable` / `Accounts Payable` report reads with `report_date = financial_as_of`. A leg is accepted **only** with an explicit `"status": "success"` payload whose `data` is a list of dicts; `None` responses, error or unknown statuses, non-list payloads, a payload company that mismatches the requested company, **any** non-dict row, rows missing an outstanding field, non-numeric or non-finite (e.g. NaN) amounts, unsupported row currencies, positive outstanding without a voucher reference, malformed due dates, exceptions and permission denials all raise typed `ObligationSourceError` / `ObligationPermissionError`. AR and AP are read independently; a failure on either leg aborts the whole read, so a failed leg can never be presented as a complete or zero leg. Without a Frappe DB the adapter raises instead of returning `[]`. Error messages carry no party, invoice or amount. Party names are pseudonymous hashes (`SHA256[:12]`).
- **Opening-cash reconciliation (Fix B, per-account)**: after the GL aggregation, the authorized ERPNext `Trial Balance` report is read independently. Reconciliation is granted (`ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED`, or `..._INTRADAY_UNCLOSED` when `financial_as_of == today()`) only when **every** account of the explicit scope appears exactly once in the TB rows **and the per-account GL balance equals the per-account TB balance** — a totals-only match is not sufficient (offsetting GL balances against zeroed TB rows fail closed). A missing scope account — including a genuine zero — or a duplicate TB row yields `INCONSISTENT_DATA`; a TB read failure, error status, foreign-company payload or missing data yields `RECONCILIATION_UNAVAILABLE`. Runtime without a Frappe DB returns `RECONCILIATION_UNAVAILABLE` and never fabricates a reconciled zero. The verified label set is exported as `VERIFIED_RECONCILIATION_STATUSES`.
- **Account scope resolution (Fix C/D, round 5)**: `resolve_cash_account_scope(company, user)` resolves the **approved** scope server-side. Account read permission is enforced first (doctype-level `frappe.has_permission`, then a permission-aware `frappe.get_list` leaf listing with full pagination — a partial read, i.e. fewer visible accounts than exist for the company, raises a typed permission error). The only account authorization is the Company configuration `ai002_approved_cash_accounts` (JSON list, Custom Field fixture, `bench migrate`): missing/empty/malformed → `NEEDS_REVIEW (MISSING_CONFIG/INVALID_CONFIG)`; an approved account that no longer exists as an enabled leaf Bank/Cash account of that company → `NEEDS_REVIEW (STALE_CONFIG)`; each configured account's continued validity is re-verified on every call. Read errors are typed `ObligationSourceError`, never an empty-but-valid scope. `service.resolve_request_scope(company, user)` wraps it: company authorization (`get_verified_company`) runs **before** any scope query and Account permission failures keep their typed identity (generic `FORBIDDEN`, no names).
- **Future Settlement Events**: Uses `FutureEventSource` abstract interface. Defaults to `FailClosedSource` (returning `FORECAST_UNAVAILABLE` with `NO_CONFIRMED_SETTLEMENT_EVENTS` when no confirmed settlement events exist). `SyntheticFixtureSource` is provided for test/evaluation suites.

### 2.4 Bounded Agentic Copilot (`agent.py`, `tools.py`, `grounding.py`)
- Bounded read-only architecture with 6 allowlisted tools:
  - `cash_forecast.get`
  - `cash_forecast.get_coverage`
  - `cash_forecast.get_obligations`
  - `cash_forecast.get_drivers`
  - `cash_forecast.get_evidence`
  - `cash_forecast.get_missing_inputs`
- **Security & Safety Controls**:
  - 5000ms circuit breaker on model invocations.
  - Strips free-text (`remarks`, `notes`, `description`) to neutralize indirect prompt injection.
  - Grounding validator verifies that claims match deterministic financial facts.
  - Deterministic Next-Checks allowlist with ERPNext deep links (`RECONCILE_BANK_TRANSACTIONS`, `FOLLOW_UP_OVERDUE_AR`, etc.).

### 2.5 Security, Hardening & Observability (`access.py`, `observability.py`, `cache.py`)
- Server-side company authorization check (`get_verified_company`).
- Compile-time report allowlist (`General Ledger`, `Accounts Receivable`, `Accounts Payable`, `Trial Balance`).
- Re-authorization of evidence drilldowns (`verify_evidence_access`).
- Zero-PII structured JSON audit logging (`log_ai002_event`) with sentinel canary verification. Telemetry `source_status` follows SSOT §10: a successful correctly-scoped empty event read may be `VERIFIED_ZERO_RECORDS`; the fail-closed default source is `NOT_AVAILABLE` — a source error is never labeled as a verified zero.
- Compound SHA256 cache key with 300s TTL and single-flight concurrency lock. **Fail-closed and error responses are never cached**; only `FORECAST_UNAVAILABLE` (valid baseline) and `PARTIAL` results are cached, so a later call always re-reads failed sources.

---

## 3. API Contract Reference

### 3.1 Primary Forecast Endpoint
`POST /api/method/lotus_fin.api.ai_insights.get_ai002_cash_forecast`

#### Parameters:
- `company` (str, required): The target company name (must be authorized).
- `financial_as_of` (str YYYY-MM-DD, optional, default: yesterday): As-of snapshot date. Malformed dates return a typed `VALIDATION_ERROR`, not a raw 500.
- `forecast_start` (str YYYY-MM-DD, optional, default: financial_as_of + 1): Start date of forecast.
- `forecast_end` (str YYYY-MM-DD, optional, default: forecast_start + 29): End date of forecast (exactly 30 days).
- `currency` (str, default: "VND"): Supported reporting currency.
- `cash_account_scope` (list[str] or comma-separated str, optional): Explicit leaf Cash/Bank accounts. **When omitted, the server resolves the scope itself** via `resolve_cash_account_scope` (no client-side cap, restricted cash excluded). When supplied, every account is validated server-side (exists, same company, leaf, enabled, Bank/Cash type, currency match) and restricted-cash accounts are rejected with `DATA_PIPELINE_ERROR`. The browser is never trusted for the scope.
- `include_explanation` (bool, default: False): Whether to invoke the bounded AI copilot.

#### Fail-closed responses (no financial payload, never cached):
| Outcome | status | reason_code |
| --- | --- | --- |
| AR/AP report error, unknown status, malformed payload/row, company/currency mismatch, invalid amount, timeout | `SOURCE_ERROR` | `DATA_PIPELINE_ERROR` |
| AR/AP permission denial | `FORBIDDEN` | `UNAUTHORIZED_ACCESS` |
| GL↔TB per-account mismatch, missing or duplicate TB rows | `INCONSISTENT_DATA` | `DATA_PIPELINE_ERROR` |
| Reconciliation evidence unavailable (incl. no-events requests with unverified opening cash) | `INSUFFICIENT_DATA` | `DATA_PIPELINE_ERROR` |
| Unresolved account scope (unauthorized company → `FORBIDDEN`; resolution failure → `SOURCE_ERROR`) | see left | `DATA_PIPELINE_ERROR` / `UNAUTHORIZED_ACCESS` |

> [!IMPORTANT]
> The opening-cash verification gate runs **before every response branch**: `FORECAST_UNAVAILABLE` (the no-events baseline) is only returned and cached when the opening cash carries a verified reconciliation label. Unverified opening cash is never returned or cached as a valid result.

> [!IMPORTANT]
> The public endpoint does **NOT** expose a `use_fixture_source` parameter. Fixture mode is only permissible in test environments via server-side flag (`frappe.flags.in_test` or `frappe.flags.ai002_use_fixture_source`), guaranteeing that production requests default fail-closed to `FailClosedSource()`.

### 3.2 Account Scope Endpoint (new)
`POST /api/method/lotus_fin.api.ai_insights.get_ai002_cash_account_scope`

- `company` (str, required, authorized).
- Returns `{status, approval, company, scope[], unapproved_excluded[], total_cash_bank_accounts, count}`.
  - `status: RESOLVED` — approved configuration valid and fully readable by the caller; `scope` is the approved list.
  - `status: NEEDS_REVIEW` — approved configuration missing (`MISSING_CONFIG`), malformed (`INVALID_CONFIG`) or stale (`STALE_CONFIG`); `scope` is empty and the UI blocks the forecast. `unapproved_excluded` lists the existing Bank/Cash leaf accounts that are not approved (display only).
- Missing Account read permission or partial Account visibility raises a generic `FORBIDDEN` (no account or company names). Config-read errors raise a typed generic error, never an empty scope.

### 3.3 Evidence Drilldown Endpoint
`POST /api/method/lotus_fin.api.ai_insights.get_ai002_evidence`

#### Parameters:
- `evidence_ref` (str, required): Document reference in format `DocType:Name` (e.g. `Sales Invoice:SINV-2026-0001`).
- `company` (str, required): Company ownership token to be validated.

Enforces server-side document read permissions (`frappe.has_permission(doctype, "read", docname)`) and verifies that the document's company matches the requested company.

---

## 4. UI Architecture (`cash_forecast.js`)

Located at Frappe Page `/app/cash-forecast`:
1. **Tier 1 (Ledger Truth)**: Opening cash card, account breakdown, 30-day daily EOD trajectory table.
2. **Tier 2 (Trade Obligations)**: AR / AP contractual due dates with pseudonymous party hashes.
3. **Tier 3 (Copilot Sidebar)**: Verified ledger facts, grounded AI interpretation, deterministic next checks, and contract limitations.
4. **Account scope banner (Fix C/D, round 5)**: the page calls `get_ai002_cash_account_scope` first and displays "Cash Scope: N approved account(s) — APPROVED" plus the count of existing-but-unapproved accounts excluded from the scope. On `NEEDS_REVIEW` the UI shows the specific reason (`MISSING_CONFIG`/`INVALID_CONFIG`/`STALE_CONFIG`), a "Scope Needs Review" state, and **does not** run the forecast. The old client-side fetch with an implicit `limit: 50` is removed.
5. **Dynamic verification badge (Fix B)**: "Ledger Truth Verified" is rendered only for the verified reconciliation labels; `INCONSISTENT_DATA` renders a red "Ledger Inconsistent" badge, and anything unverified renders amber "Ledger Unverified". The badge is no longer static.
6. **Alerts**:
   - Red banner on `NEW_MODELED_DEFICIT`.
   - Amber banner on `INHERITED_FROM_OPENING` or `has_constituent_deficit`.
   - Typed failure cards for `SOURCE_ERROR`/`TIMEOUT`, `INSUFFICIENT_DATA` and `INCONSISTENT_DATA` — no financial number is presented as verified in those states.
   - Zero-leakage `FORBIDDEN` landing card on unauthorized access.
7. **Stale-response guard (unchanged)**: `request_generation` token discards out-of-order scope/forecast responses; company switch clears scope banner, badge, tables and copilot content immediately.

---

## 5. Fail-Closed Semantics Matrix (decision record)

Canonical outcome per case (SSOT §10/§12; decisions below are code-enforced):

| Case | API status / reason | Financial payload allowed | Opening-cash reconciliation | Cache |
| --- | --- | --- | --- | --- |
| AR/AP read success, correct company/cutoff, 0 records | normal flow (`PARTIAL`/`FORECAST_UNAVAILABLE`) | other leg's obligations + opening cash; empty leg is a verified zero | independent | yes (valid result) |
| AR or AP error status / unknown status / `None` / missing or non-list `data` / any malformed row / company or currency mismatch / invalid amount / timeout / exception | `SOURCE_ERROR` / `DATA_PIPELINE_ERROR` | none (no opening cash, obligations, points) | n/a | **no** |
| AR or AP permission denied | `FORBIDDEN` / `UNAUTHORIZED_ACCESS` | none, `verified_company=""` | n/a | no |
| AP fails after AR success | `SOURCE_ERROR` (whole read fails closed) | none | n/a | no |
| Scope resolution for unauthorized company, or caller without Account read / with partial Account visibility | `FORBIDDEN` / `UNAUTHORIZED_ACCESS` — raised **before** any scope use | none | n/a | no |
| Approved scope config missing/invalid/stale (resolver `NEEDS_REVIEW`) | `VALIDATION_ERROR`/`DATA_PIPELINE_ERROR` (client scope path) or UI-blocked `NEEDS_REVIEW` | none | n/a | no |
| Client-supplied scope ≠ approved scope (extra or silently dropped accounts) | `VALIDATION_ERROR` / `DATA_PIPELINE_ERROR` | none | n/a | no |
| GL=TB per-account for full scope, incl. genuine zero balances with the account present in TB | normal flow | full forecast when events exist | verified label | yes |
| TB per-account mismatch (incl. offsetting GL vs zeroed TB), missing scope account, duplicate TB rows | `INCONSISTENT_DATA` / `DATA_PIPELINE_ERROR` | **none** (gate blocks before any response branch) | `INCONSISTENT_DATA` | no |
| TB report error / wrong-company payload | `INSUFFICIENT_DATA` / `DATA_PIPELINE_ERROR` | **none** | `RECONCILIATION_UNAVAILABLE` | no |
| No Frappe DB (no-DB runtime) | `SOURCE_ERROR` (obligations) / `INSUFFICIENT_DATA` (opening) | none | `RECONCILIATION_UNAVAILABLE` — never reconciled | no |
| No confirmed future cash events (valid baseline, verified opening) | `FORECAST_UNAVAILABLE` / `NO_CONFIRMED_SETTLEMENT_EVENTS` | opening cash + obligations, no points | verified label required | yes |
| No events **and** unverified opening cash | `INSUFFICIENT_DATA` or `INCONSISTENT_DATA` / `DATA_PIPELINE_ERROR` | none — never presented as a valid baseline | gate blocks first | no |
| Scope resolves to zero eligible accounts | `VALIDATION_ERROR` / `MISSING_ACCOUNT_SCOPE` (via validation) | none | n/a | no |
| Client-supplied restricted-cash account | `VALIDATION_ERROR` / `DATA_PIPELINE_ERROR` | none | n/a | no |

Key decisions (recorded here because the SSOT did not pin them down):
1. `SOURCE_ERROR` responses carry **no** financial payload at all (strictest reading of "preserve typed source failure, never map to zero").
2. `RECONCILIATION_UNAVAILABLE` (evidence absent) maps to `INSUFFICIENT_DATA`; `INCONSISTENT_DATA` (evidence contradicts) maps to `INCONSISTENT_DATA`. Duplicate TB rows for a scope account are a **data conflict** (`INCONSISTENT_DATA`), not an unavailable read.
3. The opening-cash verification gate runs before every response branch, so the no-events `FORECAST_UNAVAILABLE` baseline is only reachable with verified opening cash; the gold no-events contract is preserved for verified data.
4. Timeout is reported as `SOURCE_ERROR` because the ERP report layer does not expose a typed timeout signal.
5. Reconciliation is per-account; a totals-only match is never sufficient.
6. Company authorization precedes every account-scope query; denials are generic.

---

## 6. Test Verification Record

> **Status for this revision (round 4): NOT_VERIFIED — test execution blocked in the authoring session.**
> Every shell invocation failed with `spawn C:\Program Files\Git\bin\bash.exe EACCES` (probed again at the start of round 4). **No command below has been run against the round-4 code.** Last known run: **67/69 passed**, executed by the operator on the **round-3** revision; the two failures (duplicate-TB status; a wrong fixture-date assertion in `test_verified_reconciliation_allows_forecast`) are fixed in round-4 code and must be re-proven. Historical figures from earlier rounds (`100/100` Docker, `30/30` local) refer to older commits and are **not** evidence for this revision.

### 6.1 Commands to run (must be executed before any PASS claim)

Pure-Python local suites (do not touch site data):
```bash
cd E:\lotus-fin\lotus_fin
python -m unittest lotus_fin.tests.test_cashflow_failclosed -v
python -m unittest lotus_fin.tests.test_cashflow_engine lotus_fin.tests.test_cashflow_security -v
```

Docker Frappe suites (cashflow modules only — do **not** run `test_access_and_reports` on the shared `frontend` site: its setUp/tearDown mutates User Permission records):
```bash
docker exec frappe_docker-backend-1 bash -c \
  "bench --site frontend run-tests --module lotus_fin.tests.test_cashflow_failclosed"
docker exec frappe_docker-backend-1 bash -c \
  "bench --site frontend run-tests --module lotus_fin.tests.test_cashflow_engine --module lotus_fin.tests.test_cashflow_security"
```
Before running, verify the container files match the workspace (path or SHA256): `lotus_fin/cashflow/adapters.py`, `service.py`, `validation.py`, `api/ai_insights.py`, `lotus_fin_ai/page/cash_forecast/cash_forecast.js`, `tests/test_cashflow_failclosed.py`, `hooks.py`, `fixtures/custom_field.json`. A suite that does not contain the new test names proves a stale container, not a pass.

Round-5 runtime prerequisites (on the isolated test site only):
```bash
# Import the Custom Field fixture (Company.ai002_approved_cash_accounts), then
# approve the scope for the test company before any runtime forecast/UI check:
bench --site <isolated-test-site> migrate
bench --site <isolated-test-site> console
# >>> company = frappe.get_doc("Company", "AI002 Fixture 2026")
# >>> company.ai002_approved_cash_accounts = '["Cash - A2F"]'
# >>> company.save(); frappe.db.commit()
```
Without this configuration the resolver correctly returns `NEEDS_REVIEW (MISSING_CONFIG)` and every forecast/UI runtime check will be blocked — that is the intended fail-closed behavior, not a defect.

### 6.2 Regression coverage added (test names to be confirmed by execution)

`lotus_fin/tests/test_cashflow_failclosed.py`:
- Fix A: `test_ar_ap_success_zero_records_is_verified_zero`, `test_ar_error_status_raises_typed`, `test_ar_unknown_status_raises_typed`, `test_ar_none_response_raises_typed`, `test_ar_missing_data_key_raises_typed`, `test_ar_non_list_data_raises_typed`, `test_ar_exception_raises_typed_without_leak`, `test_ar_permission_denied_raises_typed`, `test_malformed_row_missing_outstanding_raises_typed`, `test_positive_outstanding_without_voucher_raises_typed`, `test_malformed_due_date_raises_typed`, `test_ap_exception_after_ar_success_fails_closed`, `test_ap_error_status_after_ar_success_fails_closed`, `test_rows_parsed_with_hash_and_zero_rows_skipped`
- Fix A (round 4, row-level fail closed): `test_non_dict_row_fails_closed`, `test_payload_company_mismatch_fails_closed`, `test_row_currency_mismatch_fails_closed`, `test_non_numeric_amount_fails_closed`, `test_nan_amount_fails_closed`
- Fix B: `test_gl_equals_tb_full_scope_reconciled`, `test_tb_missing_scope_account_is_inconsistent`, `test_duplicate_tb_rows_are_inconsistent`, `test_tb_total_mismatch_is_inconsistent`, `test_offsetting_accounts_with_zeroed_tb_are_inconsistent`, `test_tb_error_is_reconciliation_unavailable`, `test_tb_error_status_is_reconciliation_unavailable`, `test_tb_wrong_company_is_reconciliation_unavailable`, `test_valid_zero_balance_reconciles_when_account_present_in_tb`, `test_zero_without_tb_row_is_inconsistent`, `test_opening_permission_denied_raises_typed`, `test_gl_query_failure_raises_typed`, `test_empty_scope_returns_unavailable_without_selection`, `test_intraday_label_when_as_of_is_today`
- Fix B (service): `test_source_error_response_and_recovery_after_retry`, `test_permission_error_returns_forbidden_without_payload`, `test_reconciliation_unavailable_blocks_computation`, `test_inconsistent_reconciliation_blocks_computation`, `test_unknown_reconciliation_label_fails_closed`, `test_verified_reconciliation_allows_forecast`, `test_unverified_opening_with_no_events_is_not_valid_baseline` (round 4: gate before every response branch)
- Fix C/D (round 5, approved scope + Account permissions): `test_scope_approved_resolved_without_cap`, `test_scope_uses_full_pagination`, `test_scope_no_account_read_permission_fails_closed`, `test_scope_partial_account_visibility_fails_closed`, `test_scope_cross_company_visibility_denied`, `test_scope_read_error_is_typed_not_empty`, `test_scope_zero_accounts_is_needs_review`, `test_scope_missing_config_needs_review_blocks`, `test_scope_invalid_config_needs_review`, `test_scope_vietnamese_named_account_requires_approval`, `test_scope_stale_config_needs_review`, `test_scope_config_read_error_is_typed`, `test_scope_requires_db`, `test_validation_accepts_matching_approved_scope`, `test_validation_rejects_scope_not_matching_approved`, `test_validation_forbidden_when_account_read_denied`, `test_validation_needs_review_when_scope_unapproved`, `test_scope_permission_failure_not_swallowed`
- Fix D (round 4, scope authorization ordering): `test_permission_failure_blocks_scope_query`, `test_scope_resolved_for_verified_company_only`, `test_resolution_failure_is_typed_source_error`

Updated in `test_cashflow_engine.py` (old assertions relied on fail-open mock behavior):
- `test_gold_strict_no_future_event` (now injects verified adapter evidence explicitly)
- `test_no_db_opening_cash_is_never_reconciled` (replaces `test_trial_balance_reconciled_when_gl_equals_tb`)
- `test_no_db_trade_obligations_fail_closed` (replaces `test_trade_obligations_point_in_time_query`)
- `test_no_db_service_fails_closed_typed`

### 6.3 Known evidence limits
- `validate_artifacts.py` (per the Round-2 remediation prompt) was **not located and not executed** in this session: the shell failure also prevents directory listing, and no execution is possible. It must be run alongside the suites above; its output is part of the outstanding evidence.
- UI behavior (scope banner, badge, stale-response discard) is code-reviewed only; no browser/E2E run occurred in this session. Playwright evidence must be re-captured per §5 of the previous round before user-ready claims.
- The confirmed future cash source remains `CONFIRMED_FUTURE_EVENT_SOURCE=NOT_VERIFIED`; the JSON fixture is `SYNTHETIC_TEST_ONLY` and is not real SME data.
- Shared-site timezone mismatch (`Africa/Abidjan` vs `Asia/Ho_Chi_Minh`) remains a deployment requirement.
