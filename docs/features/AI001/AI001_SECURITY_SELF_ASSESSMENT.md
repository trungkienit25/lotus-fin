# AI001 — Security Self-Assessment (Retro-Documentation)

```yaml
feature_id: AI001
feature_name: Financial Health Analyst (Financial Snapshot)
document_type: security_self_assessment
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

> Verdict precedence and "ALIGNED WITH, not certified" framing as in the AI003
> Security Self-Assessment. Documentation only — no security controls were
> added or changed during this retro pass.

## 1. Document Control

Retro-documented 2026-10-02 from source (`security/access.py`, `api/ai_insights.py`,
`ai/observability.py`, `ai/explanation.py`), existing suites, and the AI003
foundation remediation chain. Dispositions distinguish remediated (with
commits) from open items.

## 2. Scope

The financial-snapshot endpoint, its report fetch chokepoint, calculators,
explanation LLM layer, observability logging, and the financial-health page.
Excludes AI002/AI003 specifics (assessed separately) and infrastructure.

## 3. Assets / Protected Information

Financial metrics and raw report rows, party/invoice identities, company
scope, snapshot/evidence refs, LLM API keys (env), prompts (minimized).

## 4. Trust Boundaries

Browser ⇄ whitelisted API (session/CSRF); untrusted company/date params ⇄
`get_verified_company`; ERPNext reports ⇄ envelope validation (status/company/
shape, footer separation WV-01); report data ⇄ calculators (fail-closed
parse); LLM ⇄ grounding/schema validation.

## 5. Roles / Permission Tiers

Page roles: Accounts User/Accounts Manager/System Manager. API: any
authenticated user passing company authorization + report permission. No
Administrator-ambient reliance in the current code (post PB-SEC-01).

## 6. Authentication

`@frappe.whitelist()` (no allow_guest) — Frappe session required; Guest has no
report permissions and fails company authorization.

## 7. Authorization / Company Isolation

`get_verified_company(company, user)` — existence + Company read permission;
CompanyAccessError → generic FORBIDDEN envelope without scope disclosure.
Evidence refs and snapshot data are company-bound; cross-company comparison
attempts are rejected (Bucket C currency/company guards).

## 8. Report & Document Permissions

All report reads go through `extract_key_report_data` →
`check_report_permission(report_name, user)` — Report.is_permitted evaluated
for the checked user with session restore (PB-SEC-01, commit 99b4388).
Allowlist enforced in `core/use_cases/source_validation.py` (REPORT_ALLOWLIST).

## 9. Evidence Authorization

Evidence refs in AI001 are snapshot-lineage metadata only (report metadata and
checksum, not bearer tokens or resolvable document drilldown endpoints). AI001
renders evidence metadata only and exposes no document drilldown endpoint;
document-level evidence drilldown reauthorizing via `verify_evidence_access` is
specific to AI002 cashflow paths (`api/ai_insights.py`, `security/access.py`).

## 10. Agent / Tool Security

No agent tool surface in AI001; the LLM receives a minimized payload and
returns narrative only — no tool execution, no thresholds, no filters from the
model.

## 11. LLM Boundary / Prompt Injection

Report remarks/descriptions are excluded from the minimized payload; prompt
templates are static; output validated by strict schema + numeric grounding
(numbers must exist in payload) + prohibited-claim screening ("guaranteed
profit", "tax exempt"); failure → UNAVAILABLE. Data never alters metrics.

## 12. Data Validation

Fail-closed source validation (Bucket A): malformed rows/unknown status/missing
data → typed unavailable; only success + valid rows (or legitimate empty) yield
values; as_of validation (ISO, ≥ period_start mid-period semantics — Bucket B);
currency authority server-side (no client relabeling; FX unsupported — Bucket C).

## 13. Financial Integrity Controls

Decimal-only arithmetic; 4dp HALF_UP ratio; no zero-fill on failure; duplicate
voucher dedupe with provenance (PB-DATA-02, shared helper); overdue basis
missing ≠ zero (PB-DATA-01); datetime due_date normalization (abc3212).

## 14. Failure / Fail-Closed Design

Envelope statuses + per-metric availability; INSUFFICIENT_DATA for missing
inputs; explanation degradation never touches metrics; cache (AI002-shared
patterns) reauthorizes on hit and evicts on revocation (Bucket D).

## 15. Logging / Sensitive-Data Handling

INV-03 zero-PII: JSON events with hashed company/user ids, allowlisted detail
keys (unknown dropped), bounded values; no raw rows/parties/amounts; PII
canary-tested (test_cashflow_security).

## 16. Docker / Runtime Security Assumptions

Same demo runtime as AI003 (§16 of AI003 assessment). `allow_tests: true` on
the demo site is an accepted demo posture. Demo data (FY2020) is synthetic.

## 17. Threat & Risk Register

| ID | Threat | Treatment | Residual |
|---|---|---|---|
| T1 | Cross-company snapshot access | verified company + generic FORBIDDEN | Low |
| T2 | Report permission bypass/revocation | checked-user Report.is_permitted (PB-SEC-01) | Low |
| T3 | Malformed source rows → fake zeros | fail-closed typed unavailable (Bucket A) | Low |
| T4 | Duplicate voucher inflation | identity dedupe (PB-DATA-02) | Low |
| T5 | Overdue-basis misread | explicit basis resolution; unknown → unavailable | Low |
| T6 | LLM ungrounded/PII leak | minimized payload + grounding + schema | Low-Medium |
| T7 | Client currency relabeling | server currency authority (Bucket C) | Low |
| T8 | Brute-force/DoS | none implemented | Accepted (demo) |
| T9 | Endpoint default period confusion (FY2020) | documented; explicit dates required by contracts | Open |

## 18. Security Test Matrix

Executed: hermetic Buckets A–D suites (test_ai001_foundation_blockers,
test_ai003_foundation_remediation), cashflow security canaries (PII, generic
FORBIDDEN, Decimal), live restricted-user report revoke/regrant probes
(foundation retests 2026-10-01, 51/51), cross-company/currency/Finance Book
rejections. NOT_RUN in this pass: fresh live pentest round (out of AI003
retro scope; last independent round 2026-10-01).

## 19. Security Test Results

| Area | Result | Evidence |
|---|---|---|
| Buckets A–D hermetic | PASS | 196-test run at b4eba4d |
| PB-SEC-01 live revoke/regrant | PASS | AI003_FINAL_FOUNDATION_RETEST_cdb9933_2026-10-01.md |
| PB-DATA-01/02 live probes | PASS (51/51) | AI003_FINAL_FOUNDATION_RESULTS_2026-10-01_51of51.json |
| PII canary | PASS | test_cashflow_security |
| Fresh live pentest round | NOT_RUN this pass | — |

## 20. Known Risks

1. No rate limiting on whitelisted endpoints (demo).
2. Site `frontend` runs with `allow_tests: true` and a known demo credential —
   demo-only posture, never exposed publicly.
3. LLM provider key handling relies on env hygiene; no provider call budget.
4. test_access_and_reports pollution can mask regressions in full-discovery
   runs (mitigation: targeted invocations; documented).

## 21. Residual Risks

Accepted for competition demo scope; production adoption would require the
future-control list in the AI003 assessment plus an AI001-specific live
pentest round.

## 22. Demo-vs-Production Restrictions

Competition demo data only; no production calibration claim; ISO alignment
statements are conceptual. The feature makes no production-readiness claim in
any artifact.

## 23. Recommended Future Controls

Rate limiting; per-provider call budgets; production credential management;
site-hardening (allow_tests off, unique admin credentials); disallowed-period
guard for the endpoint defaults; full-discovery test isolation refactor.

## 24. Security Evidence Index

`docs/features/AI003/AI003_EVIDENCE_INDEX.md` (shared stack); PB remediation
evidence: `docs/reviews/AI003_FINAL_FOUNDATION_RETEST_cdb9933_2026-10-01.md`,
`docs/reviews/evidence/*`, commits 99b4388 / 6c07e00 / abc3212.
