# AI001 — Technical Documentation (Retro-Documentation)

```yaml
feature_id: AI001
feature_name: Financial Health Analyst (Financial Snapshot)
document_type: technical_documentation
document_version: "1.0.0"
feature_version: "1.0.0"
contract_version: "1.0.0"
method_version: FORMULA_2026.1
policy_version: NONE
scope: COMPETITION_DEMO
evidence_date: 2026-10-02
implementation_revision: b4eba4d (documented as-found; AI003 retro pass)
status: IMPLEMENTED_PREVIOUSLY_RETRO_DOCUMENTED
```

> **Verdict precedence:** this document describes what exists in source,
> tests and verified evidence as of revision b4eba4d. It is documentation
> only — AI001 was NOT redesigned during this pass (AI003 retro rule, packet
> §27–28). Weaknesses are recorded under Known Limitations/Risks with a
> disposition column; none were silently fixed here.

## 1. Document Control

Owner: Lotus Fin team. Retro-documented 2026-10-02 from actual source
(`lotus_fin/lotus_fin/ai/`, `core/`, `api/ai_insights.py`), existing suites,
and the AI003 foundation remediation evidence chain (PB-SEC-01/PB-DATA-01/
PB-DATA-02 verified in commits 99b4388, 6c07e00, abc3212).

## 2. Feature Purpose & Business Problem

Financial Health workspace: computes a company financial snapshot (revenue,
COGS, gross margin, AR outstanding, overdue AR ratio, AP outstanding, cash
balance) from ERPNext key reports with a grounded LLM narrative, so an SME
owner sees financial health without manual spreadsheet work.

## 3. Scope / Non-Scope

**In:** snapshot envelope (contract 1.0.0, formula 2026.1) with typed
per-metric states, previous-period comparison block, evidence refs, LLM
explanation (grounded, zero-PII), `/app/financial-health` page, public
whitelisted API used by AI003. **Out:** signals (AI003), cash forecasting
(AI002), production calibration, multi-currency (VND demo), FX.

## 4. Architecture Context

Single Frappe app lotus_fin; AI001 modules live in `ai/` (facade
`financial_snapshot.py`, `financial_health.py`, `explanation.py`,
`observability.py`), use cases in `core/use_cases/` (SnapshotCoordinator,
SourceGatherer, MetricAssembler), calculators in `core/domain/calculators/`
(ar_extractor, pnl_extractor, ap_cash_extractor, observation_reconciliation),
DTOs in `core/dto/`. Served on site `frontend` (demo FY2020 dataset) at
`/app/financial-health`.

## 5. Component / Module Architecture

- `api/ai_insights.py::get_financial_snapshot` — whitelisted entry
  (company/period/as_of/currency/comparison/include_explanation), wires the
  report fetcher, clears frappe.message_log.
- `ai/financial_snapshot.py::build_financial_snapshot` — facade; exports
  CONTRACT_VERSION "1.0.0", FORMULA_VERSION "2026.1".
- `core/use_cases/snapshot_coordinator.py` — orchestration (gather → validate
  → assemble).
- `core/use_cases/source_validation.py` — fail-closed source validation
  (REPORT_ALLOWLIST; malformed/unknown status rows become typed unavailable).
- `core/domain/calculators/ar_extractor.py` — Decimal AR parsing; WR-01/WR-02
  guards; PB-DATA-01 overdue basis (explicit overdue column else due_date <
  as_of; unknown basis → overdue metrics unavailable, total retained);
  datetime due_date normalization (abc3212).
- `core/domain/calculators/observation_reconciliation.py` — voucher-identity
  dedupe (PB-DATA-02), shared by AI002.
- `ai/explanation.py` — LLMExplanationProvider (env provider, mock default,
  15s timeout), minimized zero-PII payload, grounding validation, PROMPT_VERSION
  "2026.09-v1".
- `ai/observability.py` — JSON events, hashed ids, allowlisted details,
  MetricsCollector, trace_span.
- Page: `lotus_fin_ai/page/financial_health/` (roles Accounts
  User/Manager/System Manager) + workspace.

## 6. Dependency Direction

API → facade → coordinator → gatherer/validators → calculators → ERPNext
reports (via `api/key_reports.py` chokepoint). DTO/entities shared in `core/`.
AI002 re-exports through the same API module; AI003 consumes the public
snapshot (see AI003 docs).

## 7. Public Interfaces / API Contract

`get_financial_snapshot(company, period_start, period_end, currency="VND",
as_of, correlation_id, comparison, include_explanation)` → envelope
`{feature_id, contract_version, status OK|PARTIAL|INSUFFICIENT_DATA|
SOURCE_ERROR|FORBIDDEN|VALIDATION_ERROR, correlation_id, company, period,
as_of, snapshot_id, data_mode:"actual", metrics[{metric_id, status
AVAILABLE|UNAVAILABLE, value, currency_or_unit, period, formula_version,
snapshot_id, evidence_refs, limitations}], comparison, explanation{status,
facts, interpretations, next_checks}, missing_inputs, limitations,
evidence_refs}`. Endpoint defaults period to FY2020 when omitted (documented
behavior; AI003 passes explicit dates).

## 8. Data Sources & Lineage

ERPNext standard reports through `api/key_reports.py::extract_key_report_data`
(P&L, Accounts Receivable, Accounts Payable, Trial Balance; report permission
checked per call). Money parsed as Decimal; per-metric evidence_refs +
snapshot_id lineage; source validation fail-closed.

## 9. AR Algorithm (as implemented)

`parse_ar_data(ar_data, as_of_date, company, currency)` → total_ar, overdue_ar,
overdue_ratio (4dp Decimal ROUND_HALF_UP), limitations. Overdue basis: explicit
overdue column when present, else due_date strictly before as_of; unknown basis
→ overdue metrics typed unavailable while total stays available. Voucher
identity dedupe; cross-leg party/voucher consistency (WV-02); currency
mismatch raises FinancialSourceDataError.

## 10. AP Algorithm (as implemented)

`ap_cash_extractor` parses AP report rows for ap_outstanding (net). Not used
for AI003 (which uses the raw report path itself).

## 11. Policy & Method Versioning

No numeric policy layer (formulas only). Version identity = contract_version
1.0.0 + formula_version 2026.1 surfaced on every metric; consumers (AI003) pin
these and fail closed on change.

## 12. Agent/LLM Architecture

Explanation-only LLM (no orchestration authority): provider from
LOTUS_LLM_PROVIDER (mock default), model/endpoint/key via env; temperature 0,
JSON response, strict schema validation, numeric grounding
(validate_grounding), PII minimization, telemetry events; failure →
explanation status UNAVAILABLE with deterministic metrics preserved.

## 13. Security Architecture Summary

Session-user authorization; company via get_verified_company; report
permission via Report.is_permitted for the checked user (PB-SEC-01 fix);
generic FORBIDDEN envelopes without scope disclosure; zero-PII logging
(INV-03); fail-closed source validation. Details in the companion Security
Self-Assessment.

## 14. Failure-State Architecture

Envelope-level typed statuses; per-metric AVAILABLE/UNAVAILABLE so one broken
source does not zero-fill others; INSUFFICIENT_DATA for missing periods;
comparison block carries per-metric limitations; LLM failure degrades
explanation only.

## 15. Evidence / Explainability

Per-metric evidence_refs (report snapshot lineage) + snapshot_id; explanation
facts/interpretations/next_checks grounded on metric values; grounding
validation rejects numbers absent from the payload.

## 16. Observability & Debugging

JSON event log (event_type, correlation_id, hashed company/user, duration,
status, allowlisted details), bounded in-memory metrics (latency p50/p95,
status counters), trace_span helper; AI002 wrapper shares the surface.

## 17. Deployment / Docker Runtime

Same stack as AI003 (§4/§17 of the AI003 tech doc): frappe_docker pwd.yml +
ai003-local overlay, site `frontend` with FY2020 demo data, timezone
Africa/Abidjan (accepted demo posture; accounting tz contract is exercised on
the AI003 verify site). Deployment path: run.ps1 sync (docker cp + install-app
+ migrate + build) or image bake.

## 18. Testing Strategy

Hermetic unittest suites (fake-frappe pattern): test_financial_snapshot,
test_financial_health, test_explanation, test_ai001_foundation_blockers,
test_numeric_contract; site-connected suites in-container
(test_access_and_reports, test_workspace_ui). 196 hermetic regression tests
rerun green at b4eba4d. Known suite-order pollution documented (§21).

## 19. Test Results (as of 2026-10-02, revision b4eba4d)

| Suite | Result |
|---|---|
| Hermetic AI001 suites (host) | PASS (196 combined run incl. AI002/AI003-foundation) |
| In-container targeted set incl. test_financial_snapshot | PASS (279 combined) |
| test_access_and_reports / test_workspace_ui in discovery | FAIL under full discovery — pre-existing order pollution (proven by exclusion rerun; pass individually) |
| FY2020 gold E2E (Playwright, 2026-09 era) | PASS historically (test_financial_health_workspace.py); not rerun in this pass |

## 20. Quality Attributes (ISO/IEC 25010:2023 — ALIGNED WITH, not certified)

| Characteristic | Evidence |
|---|---|
| Functional suitability | 196-test hermetic suite; FY2020 gold reconciliation |
| Performance efficiency | One snapshot = 4 report fetches + parse; adequate for demo single-user |
| Compatibility | Contract 1.0.0 pinned; AI003 consumes without changes |
| Interaction capability | financial-health page with loading/error/degraded states |
| Reliability | Fail-closed metric states; explanation degradation |
| Security | PB-SEC-01/PB-DATA fixes verified; see Security Self-Assessment |
| Maintainability | Layered modules; shared calculators; conventions documented |
| Safety | Zero-PII logging; grounded LLM output |

## 21. Known Limitations (with disposition)

| # | Limitation / Risk | Disposition |
|---|---|---|
| L1 | Endpoint defaults to FY2020 demo period when dates omitted | OPEN — accepted demo behavior; AI003 passes explicit dates |
| L2 | No rate limiting on whitelisted endpoints | OPEN — future control |
| L3 | Suite-order pollution under full unittest discovery (site-connected suites) | OPEN — documented in WR remediation report §4; targeted invocations used |
| L4 | frontend site timezone Africa/Abidjan (not Asia/Ho_Chi_Minh) | OPEN — accepted demo posture; AI003 uses its own site |
| L5 | Comparison block exposes rounded deltas (not for machine recomputation) | OPEN — AI003 contract forbids its use |
| L6 | Snapshot cost: full 4-report gather even when a consumer needs one metric | OPEN — acceptable at demo scale |
| L7 | Malformed AR/AP rows → typed unavailable (PB-DATA-01/02) | REMEDIATED — commits 99b4388, abc3212; verified in AI003 foundation retests (51/51 probe) |
| L8 | Report permission used ambient user (PB-SEC-01) | REMEDIATED — 99b4388 (checked-user Report.is_permitted with session restore) |
| L9 | Duplicate voucher double-count (PB-DATA-02) | REMEDIATED — 99b4388/6c07e00 shared observation_reconciliation |

## 22. Reproduction Guide

See `docs/features/AI003/AI003_REPRODUCTION_GUIDE.md` (shared stack) plus:
`python tests_e2e/test_financial_health_workspace.py` (frontend site, FY2020
gold) and the hermetic suite command (§18/§19 of AI003 doc). Do NOT create
fixture companies on `frontend` (site-cleanliness invariant).

## 23. Version / Change History

| Date | Change |
|---|---|
| 2026-09 era | Feature implementation + freeze docs (see docs/features/AI001/*) |
| 2026-10-01 | Foundation remediation: PB-SEC-01, PB-DATA-01/02 (99b4388, 6c07e00, abc3212) |
| 2026-10-02 | Retro-documented (this file) — no code changes |

## 24. Competition Evidence Mapping

Implementation/source: ai/ + core/ + api/ai_insights.py. Tests: suites listed
in §18. Documentation: this pair + docs/features/AI001/* (freeze docs).
Execution evidence: FY2020 gold E2E artifacts (tests_e2e/screenshots, videos),
AI003 smoke probe (consumes AI001 boundary live). Known limitations: §21.
Deployment/reproduction: §22.
