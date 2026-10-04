# AI001 — Security Self-Assessment (Current Source and Evidence Review)

```yaml
feature_id: AI001
feature_name: Financial Health Analyst (Financial Snapshot)
document_type: security_self_assessment
document_version: "1.1.0"
feature_version: "1.0.0"
contract_version: "1.0.0"
method_version: FORMULA_2026.1
policy_version: NONE
scope: COMPETITION_DEMO
evidence_date: 2026-10-03
implementation_revision: 4d1c73a1515237018ad035bf5356fbdb61641048
verification_scope: AI001_SOURCE_REVIEW_AND_77_HERMETIC_TESTS
status: UPDATED_DOCUMENTATION_DEMO_SCOPE
```

This is a source-based security self-assessment for the competition demo,
not an ISO certification, independent full pentest or production approval.
No security control or production code was changed in this documentation update.

## 1. Document Control

Original retrospective record: 2026-10-02. Updated 2026-10-03 against the
pinned revision, `security/access.py`, the public snapshot endpoint,
coordinator/gatherer, observability and existing foundation artifacts.
The five AI001 host suites in the technical documentation freshly pass
**77/77**. Live permission/data evidence is historical and explicitly reused.
Risk labels below are qualitative reviewer judgments, not measured
probabilities or formal Product/Finance risk acceptance.

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

| Tier | Capability / enforcement |
|---|---|
| Guest | Snapshot endpoint is not guest-whitelisted; Frappe authentication is required |
| Authenticated user | API additionally requires verified Company read access and report permissions |
| Accounts User / Accounts Manager / System Manager | Listed page roles permit UI access; page visibility does not replace server-side checks |
| Administrator / target-user checks | Report permission uses the checked user; when it differs from the session, `set_user` is scoped with `try/finally` restoration |

Browser-supplied roles, company strings, snapshot IDs and evidence hashes
never grant permission. Company and report authorization remain server-owned.

## 6. Authentication

`@frappe.whitelist()` (no allow_guest) — Frappe session required; Guest has no
report permissions and fails company authorization.

## 7. Authorization / Company Isolation

`get_verified_company(company, user)` — existence + Company read permission;
CompanyAccessError → generic FORBIDDEN envelope without scope disclosure.
Evidence refs and snapshot data are company-bound; source company mismatches
are rejected by source validation; comparison remains within the verified
company. Bucket C concerns server-owned currency, not a general cross-company
comparison endpoint. Hermetic no-DB fallbacks are testing behavior, not an
authorized deployment mode; the HTTP endpoint must run with live Frappe.

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
inputs; explanation degradation never touches metrics. AI001 has no snapshot
result cache/replay store in this path: each request gathers sources anew.
AI002 cache hit reauthorization/eviction and AI003 Redis evidence TTL are
separate feature controls and must not be credited as AI001 controls.

## 15. Logging / Sensitive-Data Handling

INV-03 zero-PII: JSON events with hashed company/user ids, allowlisted detail
keys (unknown dropped), bounded values; no raw rows/parties/amounts; PII
historically canary-tested (shared `test_cashflow_security`, not rerun in
this update). Hashes are pseudonymous identifiers, not guaranteed anonymity.
The logger catches logging exceptions without a durable failure diagnostic;
process-local metrics are not a multi-worker central monitoring system.
SourceGatherer stores exception strings that can enter client limitations;
log allowlisting does not prove those client messages are sanitized.

## 16. Docker / Runtime Security Assumptions

Historical AI001 evidence uses the FY2020 `frontend` sandbox; AI003 uses
`ai003-verify.localhost`. Prior AI001 records describe `allow_tests: true` and
known demo credentials. These settings/network exposure were not re-inspected
here. Treat them as demo-only assumptions requiring enforcement, not proof
of isolation. Verification-site settings must not be inferred for frontend.
Synthetic/controlled data is not business calibration evidence.

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
| T8 | Brute-force/DoS | no endpoint rate limit/provider budget verified | Open; demo scope restriction is not a technical mitigation |
| T9 | Endpoint default period confusion (FY2020) | documented; consumers should pass explicit dates | Open |
| T10 | Internal error detail disclosure | log fields are allowlisted, but client source-error text needs separate sanitization review | Open; exploitability not assessed here |
| T11 | Missing audit events / per-worker operational visibility | logging exceptions swallowed; metrics process-local | Open |

## 18. Security Test Matrix

Fresh validation is limited to the five AI001 hermetic suites in the
technical document. Their security-related coverage includes checked-user
permission guards, malformed/missing overdue basis, duplicate/conflicting
observations and public snapshot regression. Fake-Frappe tests cannot prove
actual Frappe session/CSRF behavior, live revocation, network isolation or
real provider security.

## 19. Security Test Results and Provenance

| Area | Result | Evidence / scope |
|---|---|---|
| Five AI001 suites (security and numeric regression combined) | **77/77 PASS**, fresh 2026-10-03 at 4d1c73a | Exact command and output in [technical document](AI001_TECHNICAL_DOCUMENTATION.md) §18–19; not 77 security-only cases |
| PB-SEC-01 live revoke/regrant | Historical PASS, reused | [Foundation retest](../../reviews/AI003_FINAL_FOUNDATION_RETEST_cdb9933_2026-10-01.md) |
| PB-DATA-01/02 live probe | Historical 51/51 PASS, reused | [Result artifact](../AI003/evidence/AI003_FINAL_FOUNDATION_RESULTS_2026-10-01_51of51.json) |
| Datetime/public snapshot | Historical host/Docker PASS plus current regression | [Artifacts](../../reviews/evidence/final-8941cfb-2026-10-01/) |
| Shared PII canary / combined 196-suite baseline | Historical reported PASS | b4eba4d record; includes AI002, not a new AI001-only result |
| AI003 independent security/UI results | Reused for unchanged shared consumer boundaries only | [Final review](../../reviews/AI003_FINAL_INDEPENDENT_REVERIFY_3eb8207_2026-10-03.md); does not establish full AI001 coverage |
| Fresh AI001 live pentest / workspace E2E / full site suites / infrastructure audit | **NOT_RUN** | No new result claimed |

## 20. Known Risks

1. No rate limiting on whitelisted endpoints (demo).
2. Site `frontend` runs with `allow_tests: true` and a known demo credential —
   demo-only posture; current network exposure is NOT VERIFIED in this update.
3. LLM provider key handling relies on env hygiene; no provider call budget.
4. test_access_and_reports pollution can mask regressions in full-discovery
   runs (mitigation: targeted invocations; documented).

## 21. Residual Risks

Restricted to competition demo scope; formal risk acceptance is not established
by this documentation update. Production adoption would require the
future-control list in the AI003 assessment plus an AI001-specific live
pentest round.

## 22. Demo-vs-Production Restrictions

Competition demo data only; no production calibration claim; ISO alignment
statements are conceptual. The feature makes no production-readiness claim in
any artifact.

## 23. Recommended Future Controls

Rate limiting; per-provider call budgets; production credential management;
site-hardening (allow_tests off, unique credentials, verified network isolation);
source-error message sanitization; durable safe logging-failure diagnostics;
central operational telemetry; disallowed-period guard for endpoint defaults;
full-discovery test isolation and fresh AI001-specific live security tests.
These are open controls, not changes implemented by this assessment.

## 24. Security Evidence Index

`docs/features/AI003/evidence/AI003_EVIDENCE_INDEX.md` (shared stack); PB remediation
evidence: `docs/reviews/AI003_FINAL_FOUNDATION_RETEST_cdb9933_2026-10-01.md`,
`docs/reviews/evidence/*`, commits 99b4388 / 6c07e00 / abc3212.

Documentation revision 1.1.0 (2026-10-03): separated AI001 controls from
AI002 cache/AI003 replay, corrected test attribution, added permission tiers,
updated evidence provenance and residual risks. The supplied competition rule
categories (security design, permission tiers and known risks) are documented;
completion of these categories is not certification or full submission approval.
