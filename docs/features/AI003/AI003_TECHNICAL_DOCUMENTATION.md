# AI003 — Technical Documentation

```yaml
feature_id: AI003
feature_name: Risk Signal Agent
document_type: technical_documentation
document_version: "1.0.0"
feature_version: "1.0.0"
contract_version: "2.2.0"
method_version: V2.2_REVIEWED_METHOD_SPEC
policy_version: AI003_DEMO_POLICY_V1
scope: DEMO_ONLY
evidence_date: 2026-10-02
implementation_revision: b4eba4d (feature/ai003-risk-signal)
status: IMPLEMENTATION_COMPLETE_FOR_WORK_REVIEW
```

> **Verdict precedence:** the final verdict of this document is
> `IMPLEMENTATION_COMPLETE_FOR_WORK_REVIEW`. Embedded gate labels (METHOD GOLD
> PASS, POLICY GOLD PASS, G1–G4A PASS) describe method/design/demo-gate scope
> only and never imply production readiness. G4B is NOT_APPLICABLE_YET and is
> owned by independent Work review.

## 1. Document Control

| Field | Value |
|---|---|
| Owner | Lotus Fin team (builder: Zcode) |
| Date | 2026-10-02 |
| Contract authority | V2.2 reviewed ruleset (SSOT §16–§19); owner task packet 2026-10-02 |
| Review status | Independent Work review (G4B) pending — next owner |
| Related | AI003_MASTER_SSOT.md (§1–22), AI003_SECURITY_SELF_ASSESSMENT.md, AI003_EVIDENCE_INDEX.md |

## 2. Feature Purpose & Business Problem

AI003 turns raw AR/AP accounting state into two deterministic, explainable risk
signals so finance staff can see *what changed, why, and what to inspect next*
without re-deriving numbers from ERPNext reports: AR_OVERDUE_SPIKE (overdue
receivables ratio drift vs previous month) and AP_DUE_CLUSTER (near-term
payables due concentration). Every value is server-computed; the LLM only
explains results.

## 3. Scope / Non-Scope

**In (P0):** two-signal allowlist (AR_OVERDUE_SPIKE, AP_DUE_CLUSTER); VND only;
Asia/Ho_Chi_Minh accounting tz; AI001 public snapshot + fixed Accounts Payable
report + Purchase Invoice schedule metadata; typed fail-closed envelope;
evidence replay; explanation-only agent; `/app/risk-signal` page; demo policy
AI003_DEMO_POLICY_V1.

**Out:** other signals; FX and non-VND companies; Finance Book scoping;
multi-installment (multi-schedule) evaluation; production-calibrated policy;
dedicated AI003 cache; persistent signal history; scheduler/background
evaluation; G4B acceptance (owner-side).

## 4. Architecture Context

Lotus Fin Frappe app (`lotus_fin`) on ERPNext v16, Docker runtime
(`frappe_docker` pwd.yml + `docker/ai003-local` overlay, image
`lotus-fin:ai003-local`, digest sha256:21f61183…). AI003 sits beside AI001
(financial snapshot) and AI002 (cash-flow forecast) and consumes only their
public boundaries. Verification site: `ai003-verify.localhost`
(tz Asia/Ho_Chi_Minh, gold fixture companies "AI003 MG *").

## 5. Component / Module Architecture

`lotus_fin/lotus_fin/risk_signal/` — each module maps 1:1 to the frozen
scaffold plan (S1–S5):

| Module | Responsibility |
|---|---|
| contracts.py | Typed envelope (SignalRequest/SignalResult + blocks), enums, impossible-state validation, Decimal wire serialization (money 2dp / ratio 4dp / pp 2dp, no exponent, −0 normalized) |
| interfaces.py | Provider protocols + DTOs (ARSnapshot, APReportSnapshot, APRow, ScheduleMetadata) — DIP boundary |
| sources.py | The only Frappe-touching adapters: AI001 public snapshot (2× explicit dates), fixed `accounts_payable` key report, permission-gated Purchase Invoice metadata |
| coverage.py | Baseline resolver (prev-month same-day + month-end clamp), AP window D0–D30, eligibility/selection, due-date resolution |
| provenance.py | Source hashing, V2.2 identity (economic / observation / count keys), dedupe & conflict, currency gate, typed SourceFailure |
| policy.py | Immutable AI003_DEMO_POLICY_V1 registry; POLICY_PENDING vs INVALID_POLICY_CONFIG resolution |
| evaluation.py | Deterministic AR delta_pp and AP N≥T×D engines |
| evidence.py | Evidence records (scope fingerprint + payload hash), dynamic authorized replay (MATCH/RESTATED/UNAVAILABLE/FORBIDDEN) |
| observability.py | Zero-PII JSON audit events (hashed ids, allowlisted fields), latency timer |
| service.py | A1→A11 first-failed-stage pipeline, result composition |
| agent.py | Typed tools (risk_signal_evaluate, risk_signal_evidence_get), explanation via AI001 provider pattern, banned-term + numeric-grounding validation, allowlisted next-check actions |

Frontend: `lotus_fin_ai/page/risk_signal/` (Page `risk-signal`, roles Accounts
User/Accounts Manager/System Manager) + additive entry links on financial-health
and cash-forecast pages + workspace card.

## 6. Dependency Direction

```
API (api/ai_insights.py get_risk_signal*)  /  Page JS
        → service.py → policy.py / evaluation.py / coverage.py / provenance.py
                              ↑ interfaces.py (typed DTOs)
        → sources.py (only Frappe-touching layer)
              → AI001 public snapshot | key_reports accounts_payable | PI metadata
        → evidence.py / observability.py
```

Domain code never imports frappe; shared-surface changes are additive only
(`security/access.py` +`AI003_PERMITTED_REPORTS`/`check_ai003_report_permission`;
`api/ai_insights.py` +2 whitelisted endpoints).

## 7. Public Interfaces / API Contract

`@frappe.whitelist() get_risk_signal(company, signal_id, as_of_date,
correlation_id?, include_explanation?)` — additional_properties=false
(unknown form keys → VALIDATION_ERROR/INVALID_REQUEST). Response: strict
SignalResult wire (`result_to_dict`): status OK/INCONCLUSIVE/FORBIDDEN/
VALIDATION_ERROR/SOURCE_ERROR/POLICY_PENDING; finding/severity/triggered only
on OK; observed/baseline/rule blocks; reason_code; evidence refs; coverage;
limitations; policy_scope=DEMO_ONLY + production_calibrated=false; stage_trace.
FORBIDDEN returns only generic metadata (no company, no financial payload).

`@frappe.whitelist() get_risk_signal_evidence(evidence_ref, company?)` →
`{status: MATCH|RESTATED|UNAVAILABLE|FORBIDDEN, payload}`. Agent tools:
`risk_signal_evaluate`, `risk_signal_evidence_get` (packet §14 names; mapping
documented here — one operation per name pair).

## 8. Data Sources & Lineage

- **AR:** `lotus_fin.api.ai_insights.get_financial_snapshot` called twice with
  explicit periods/as-of (current cutoff + baseline cutoff = previous calendar
  month same day, month-end clamp, resolver `PREV_MONTH_SAME_DAY_CLAMP_V1`).
  Pins contract 1.0.0 / formula 2026.1; values via `Decimal(str(published))`.
  AI001 endpoint FY2020 defaults bypassed; comparison block never used.
- **AP:** `extract_key_report_data(report_key="accounts_payable", filters=
  {report_date=as_of, based_on_payment_terms:0, in_party_currency:0,
  show_future_payments:0, ageing_based_on:"Due Date", age_as_on:"Report Date"},
  company=verified)` — envelope company/filters echoed and verified; company
  provenance = authorized envelope (rows carry none).
- **Schedule metadata:** `frappe.get_doc('Purchase Invoice', …)` +
  explicit checked-user read permission + company match + submitted state;
  count from `payment_schedule`. `get_doc` alone is never authorization.
- Every source contributes `source_refs` (kind/version/cutoff/captured_at) and
  a canonical `source_hash`.

## 9. AR Algorithm

`delta_pp = (current_published_ratio − baseline_published_ratio) × 100` on the
published 4-decimal ratio grid (`.01` pp quantum), exact Decimal (prec-60
localcontext). Materiality floor gates CURRENT_NET_AR_TOTAL (strict `<`).
Evaluation: HIGH first (`≥ 15.00` pp), then WATCH (`≥ 5.00` pp), else BENIGN —
equality included (GTE), gold-pinned boundaries 4.99/5.00/10.00/14.99/15.00/
15.01 pp. Failure states: HISTORY_INSUFFICIENT (no valid prior observation),
BASELINE_/CURRENT_DENOMINATOR_INVALID (verified zero), never clamped or
zero-filled.

## 10. AP Algorithm

Numerator N = positive future payables due in [as_of, as_of+30] (W is an
offset; D0–D30 inclusive); denominator D = positive future payables due
≥ as_of. Past-due and nonpositive (credit) rows excluded from both and from
counts; valid nonpositive rows never require due-date coverage. Preflight per
SSOT §17.4 for every unique positive voucher: non-PI → INCONCLUSIVE/
UNSUPPORTED_ALLOCATION_SCOPE; >1 schedules → INCONCLUSIVE/
UNSUPPORTED_MULTI_SCHEDULE (real flattened-report proof in METHOD GOLD);
0/1 schedules use verified invoice/report due date with disagreement
detection. Authoritative comparison **exact `N ≥ T×D`** (never
`round(N/D) ≥ T`); display share = `N/D` quantized 4dp ROUND_HALF_UP, never an
operand. D=0 → ZERO_DENOMINATOR; D<0 → INVALID_DENOMINATOR (fail-closed).
Counts published as distinct-voucher cardinalities (count_basis
distinct_voucher).

## 11. Policy & Method Versioning

Registry keyed `(signal_id, policy_version)`; active version resolved
server-side (client cannot pass policy fields). AI003_DEMO_POLICY_V1
(owner-approved 2026-10-02, Project Owner, DEMO_ONLY, production_calibrated
false): AR floor 0 / WATCH 5.00pp / HIGH 15.00pp; AP floor 0 / WATCH 0.50 /
HIGH 0.75; AP W=30. POLICY_PENDING only for registered-but-unapproved versions
after all method prerequisites pass; missing/malformed/partial/reversed
registry state → SOURCE_ERROR/INVALID_POLICY_CONFIG. Method version string
`V2.2_REVIEWED_METHOD_SPEC` (gold manifest identifier; owner-packet alias
`AI003_AR_SPIKE_PREV_MONTH_V1` recorded here and in the SSOT record only).

## 12. Agent/LLM Architecture

Tools are schema-allowlisted server functions in the request context; no
arbitrary tools, thresholds, filters or user params. Explanation reuses the
AI001 `LLMExplanationProvider` (env-configured, mock default, 15s timeout);
input = minimized authorized payload (no raw rows/parties/remarks); output
validated for AI003 banned terms (fraud, default, bankruptcy, guaranteed cash
shortage, creditworthiness, …) and numeric grounding against the deterministic
result. Any provider/validation failure → explanation UNAVAILABLE; the
deterministic result is composed before A11 and never altered. Next-check
actions are allowlisted per signal/status.

## 13. Security Architecture Summary

Session-user-is-authority at every layer (no ambient Administrator reliance, no
user parameter, synchronous-only, fail-closed without a session user — pinned
tests). Checked-user report allowlist (`AI003_PERMITTED_REPORTS` =
Accounts Receivable, Accounts Payable) + per-access evidence reauthorization +
checked-user parent metadata permission. Company isolation via
`get_verified_company`; generic ACCESS_DENIED for denied/unknown/cross-company
scope. Details in AI003_SECURITY_SELF_ASSESSMENT.md.

## 14. Failure-State Architecture

Sole normative A1→A11 ordering (SSOT §19.2), first failed stage wins and is
never replaced: A1 Authentication→FORBIDDEN; A2 Structural→VALIDATION_ERROR;
A3 Company→FORBIDDEN; A4 Semantic scope (future date)→VALIDATION_ERROR;
A5 Source authorization→FORBIDDEN; A6 Source+currency→VALIDATION_ERROR/
SOURCE_ERROR; A7 Integrity/identity→SOURCE_ERROR; A8 Method prerequisites
(schedules, coverage, denominators)→INCONCLUSIVE/FORBIDDEN; A9 Policy→
POLICY_PENDING; A10 Evaluation→OK; A11 Explanation degrades only itself.
Pinned test: unauthenticated+malformed → FORBIDDEN (A1 before A2).
FORBIDDEN/VALIDATION_ERROR/SOURCE_ERROR carry no financial payload, no
source/evidence refs, no explanation text.

## 15. Evidence / Explainability

Evidence records bind verified company, signal, cutoff, report key, filter
echo, currency, tz, schema+method versions (scope fingerprint) plus a payload
hash over sanitized derived values. Replay re-runs the approved source path in
checked-user context and compares hashes: MATCH (unchanged) / RESTATED
(changed; current values returned, original evaluation unchanged) /
UNAVAILABLE (typed source failure) / FORBIDDEN (revoked/denied). Refs are
opaque resolvable record ids, never authorization tokens. Evaluation
explanation: grounded narrative or explicit UNAVAILABLE state.

## 16. Observability & Debugging

Every evaluation emits `ai003_evaluate_completed` (correlation_id, signal,
stage, status, reason_code, method/policy version, data_mode, latency) and
every evidence access emits `ai003_evidence_<outcome>`. JSON events,
SHA256[:12] hashed ids, allowlisted fields only — no raw rows, party names,
amounts, prompts or tokens. `stage_trace` on the wire lists pipeline stages
entered (debug metadata, same envelope for all statuses).

## 17. Deployment / Docker Runtime

Build: `docker build -f docker/ai003-local/Dockerfile -t lotus-fin:ai003-local .`
(repo root; bakes app code + include assets). Run: `docker compose -f
<compose-project-dir>/pwd.yml -f docker/ai003-local/compose.override.yml up -d
--force-recreate backend frontend websocket scheduler queue-short queue-long`
(compose dir discovered via `docker inspect frappe_docker-backend-1 --format
'{{index .Config.Labels "com.docker.compose.project.working_dir"}}'` — here
`E:\frappe_docker`). Then per target site: `bench --site ai003-verify.localhost
migrate && bench --site ai003-verify.localhost clear-cache`. Named volumes
preserved; queues are not on the synchronous AI003 path. Current image digest:
sha256:21f61183dd3d62ed6a6c2142a933f9ef7ec100c631bb513e2fc649d7ac2be110.
See AI003_REPRODUCTION_GUIDE.md for the full verified sequence and the
runbook fixes applied (apps.txt, set-admin-password, setup_complete,
nginx Host-map).

## 18. Testing Strategy

Pyramid: 128 hermetic unittest cases (contracts 25 / sources 37 / policy 18 /
evidence 16 / service+security 32) on host and in-container; in-container
targeted verification set (279 tests incl. AI001/AI002 regression suites);
full in-container discovery; live API smoke probe with METHOD GOLD number
assertions; Playwright E2E script (implemented; live run blocked — §19).
Security matrix from the owner packet §18 mapped to hermetic tests + live gold
probes (restricted-user report revoke/regrant and metadata denial proven in
METHOD/POLICY GOLD live evidence). No unrun category is marked PASS.

## 19. Test Results

| Layer | Status | Evidence |
|---|---|---|
| Contract/boundary/policy/evidence/service units (host, hermetic) | PASS 128/128 | `python -m unittest …` (see §22) |
| In-container targeted set (AI003 + foundation + AI001/AI002 regression) | PASS 279/279 | docker exec unittest run, 2026-10-02 |
| Full in-container discovery | 428 run; 20F+2E all pre-existing test-order pollution | exclusion rerun (AI003 modules removed → identical failures); every failing test passes individually |
| Live API smoke (verify site, real boundaries, gold numbers) | PASS 7/7 | evidence/ai003_smoke_results_2026-10-02.json |
| METHOD GOLD (oracle equivalence) | PASS 66/66 (pre-build evidence, reused) | AI003_METHOD_GOLD_MANIFEST.yaml |
| POLICY GOLD | PASS 17/17 + 4 proved N/A | AI003_POLICY_GOLD_EVIDENCE.md |
| Playwright E2E (live) | NOT_RUN — implemented script; blocked by verify-site desk boot loop (root-caused: stale bootinfo `setup_complete:"0"` vs DB 1; env issue, not AI003 code) | AI003_E2E_BLOCKER_NOTE_2026-10-02.md |
| UI/UX review | PARTIAL — screenshots from probes (HIGH/INCONCLUSIVE/render states); full pass deferred with E2E | tests_e2e/screenshots/rs_*.png |
| AI001/AI002 regression | PASS (hermetic 196; in-container targeted set included) | unittest run above |

## 20. Quality Attributes (ISO/IEC 25010:2023 — ALIGNED WITH, not certified)

| Characteristic | Evidence |
|---|---|
| Functional suitability | Gold-aligned engines; 66/66 METHOD GOLD; smoke 7/7 live |
| Performance efficiency | Synchronous path; AR = 2 AI001 snapshot builds + AP report per evaluation; no cache by design (SSOT §16.7); latency logged per event |
| Compatibility | Additive-only shared-file changes; AI001/AI002 regression suites unchanged-pass; version pins fail closed |
| Interaction capability | /app/risk-signal UX states, glossary, curated reason copy, keyboard flow; E2E run deferred (§19) |
| Reliability | Fail-closed typed failures; no zero-fill; first-failed-stage; evidence replay states |
| Security | See Security Self-Assessment §18–19 (matrix + results) |
| Maintainability | 1:1 module↔scaffold mapping; pinned constants with tests; 128-case unit suite |
| Flexibility | Policy registry (versioned); signal enum allowlist; new policy = registry entry, no engine change |
| Safety | DEMO_ONLY disclosure everywhere; banned-word screening; no production promotion path |

## 21. Known Limitations

1. **E2E live run deferred** — verify-site desk boot loop (stale bootinfo
   `setup_complete:"0"` cache layer vs DB=1); root-caused in
   AI003_E2E_BLOCKER_NOTE_2026-10-02.md; not AI003 code.
2. **Evidence store is in-memory per process** (bounded FIFO 500) — with
   multiple workers or after restart, refs resolve FORBIDDEN/UNAVAILABLE;
   durability (DocType/Redis persistence) is future work (audit P1).
3. Demo policy is inert-by-design: floor 0 means no materiality filtering
   (labelled in UI); WATCH/HIGH bands reachable and pinned by POLICY GOLD.
4. AR authorization delegates to AI001's AR report allowlist; a future AI001
   contract/formula bump turns AR evaluation into SOURCE_ERROR by design
   (fail-closed coupling, documented).
5. Banned-term screening is substring-based; a real (non-mock) provider may be
   degraded to UNAVAILABLE more often than strictly necessary (fail-closed).
6. No persistent signal history; no scheduler; single-site verification
   runtime only.

## 22. Reproduction Guide

See **AI003_REPRODUCTION_GUIDE.md** — environment preflight, backend unit +
in-container suites, Docker rebuild/recreate/migrate, API smoke, E2E script,
with exact Windows commands and named shell per step.

## 23. Version / Change History

| Date | Change | Revision |
|---|---|---|
| 2026-10-02 | Baseline: METHOD/POLICY GOLD artifacts, SSOT §16–21, IVL probes | efd7046 |
| 2026-10-02 | S1–S5 engine, API, agent (127 hermetic tests) | 7bb0487 |
| 2026-10-02 | /app/risk-signal page + entry links + workspace card | 131b57e |
| 2026-10-02 | E2E script + runbook fixes (nginx host-map, baked assets, apps.txt) + smoke evidence | 4b22d93 |
| 2026-10-02 | Audit round 1 fixes (4 HIGH + quick wins) | b4eba4d |

## 24. Competition Evidence Mapping

| Competition requirement | Evidence artifact |
|---|---|
| Implementation/source | risk_signal package + API + page (revisions above) |
| Tests | 5 unit suites (128) + in-container runs + smoke probe JSON |
| Technical Documentation | This document |
| Security Self-Assessment | AI003_SECURITY_SELF_ASSESSMENT.md |
| Execution evidence | evidence/ai003_smoke_results_2026-10-02.json; METHOD/POLICY GOLD manifests + evidence |
| Known limitations | §21 + E2E blocker note |
| Deployment/reproduction | AI003_REPRODUCTION_GUIDE.md + §17 |
| Independent verification | Next owner: Work review (G4B) — verdict reserved |
