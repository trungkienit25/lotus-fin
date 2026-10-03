# AI003 — Security Self-Assessment

```yaml
feature_id: AI003
feature_name: Risk Signal Agent
document_type: security_self_assessment
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

> **Verdict precedence:** final verdict `IMPLEMENTATION_COMPLETE_FOR_WORK_REVIEW`
> supersedes any embedded PASS label; all gate PASS strings are scoped to
> method/design/demo. Not approved for production. Alignment with ISO/IEC
> standards below is conceptual (**ALIGNED WITH, not certified/compliant**);
> no ISO text is reproduced.

## 1. Document Control

Owner: Lotus Fin team (builder: Zcode). Date: 2026-10-02. Authority: owner task
packet 2026-10-02 + SSOT §16–§19 + METHOD/POLICY GOLD evidence. Independent
verification (G4B) pending — next owner: Work review.

## 2. Scope

Security surface of the AI003 implementation: two whitelisted API endpoints,
the risk_signal package, the /app/risk-signal page, the additive access.py
allowlist, and the evidence/agent layers on the isolated verification runtime.
Out of scope: AI001/AI002 internals (inherited, separately assessed),
infrastructure hardening beyond the AI003-local overlay, G4B runtime
acceptance.

## 3. Assets / Protected Information

Financial observations (AR/AP amounts, ratios, due dates), party references,
company identity/scope, evidence payload hashes, policy constants, LLM API
keys (env-only, never logged), LLM prompts (minimized authorized payload
only).

## 4. Trust Boundaries

1. Browser ⇄ whitelisted API (session cookie + CSRF via frappe.call POST).
2. Untrusted request payload ⇄ `parse_signal_request` (additional_properties
   false, strict date, allowlisted signal, bounded correlation_id).
3. AI003 ⇄ AI001 public snapshot / key-report boundary (typed envelopes,
   envelope company/currency/filters verified, versions pinned).
4. AI003 ⇄ Frappe DocType metadata (checked-user permission gate).
5. LLM provider ⇄ explanation validator (banned terms + numeric grounding;
   failure degrades explanation only).

## 5. Roles / Permission Tiers

- **Guest/unauthenticated:** A1 rejects — FORBIDDEN/UNAUTHORIZED_ACCESS, no
  structure disclosure (pinned test; gold STAGE_A).
- **Accounts User / Accounts Manager:** page access + evaluation via role-gated
  report permissions (ERPNext Report.is_permitted for the checked user).
- **System Manager:** administration; no AI003-specific privilege beyond role
  permissions.
- **Administrator:** used only for wiring smoke evidence on the isolated site;
  all production-path authorization is checked-user based; security tests run
  as restricted users (hermetic fakes) and live restricted-user probes exist in
  METHOD GOLD (CHECKED_USER_METADATA_PERMISSION_REAL, live report denial).

## 6. Authentication

`@frappe.whitelist()` endpoints (no allow_guest) require an authenticated
session; the service re-verifies (`_is_authenticated`, Guest rejected) at A1 —
pinned test unauth+malformed → FORBIDDEN. Synchronous-only design: no queue or
background path exists where the session user would be absent; the service
fail-closes without a session user (pinned test).

## 7. Authorization / Company Isolation

The client `company` parameter is a requested scope, never authoritative;
`get_verified_company(company, user=checked_user)` resolves and authorizes it.
Denied/unknown/cross-company all collapse to generic ACCESS_DENIED with no
company/resource identity or financial payload (gold-checked; pinned tests).
Evidence replay re-verifies record company binding on every access.

## 8. Report & Document Permissions

Additive compile-time allowlist `AI003_PERMITTED_REPORTS = ("Accounts
Receivable", "Accounts Payable")` + `check_ai003_report_permission(report,
user=)` following the AI002 pattern (access.py, additive; GitNexus impact
CRITICAL recorded — additive-only change, regression suites unchanged). Parent
metadata requires explicit `doc.has_permission('read', user=checked_user)`;
`get_doc` alone is never treated as authorization (SSOT §17.4). Report
permission is re-evaluated for the checked user (PB-SEC-01 semantics inherited
from access.py).

## 9. Evidence Authorization

Opaque refs (`AI003-EV-…`) are resolvable server-side records, never tokens:
unknown ref, malformed ref, and cross-company requests all return the same
generic FORBIDDEN with no existence disclosure (pinned tests). Replay re-runs
the approved source path in checked-user context per access; outcomes MATCH /
RESTATED / UNAVAILABLE / FORBIDDEN; a changed source is never silently MATCHed.
Evidence records are persisted in a shared Redis store (`ai003:evidence:*`)
with bounded 3600-second TTL, ensuring cross-worker consistency (verified
20/20 MATCH across multi-worker Gunicorn processes) without reliance on
per-process memory. On TTL expiration or key eviction, replay safely fails
closed to generic FORBIDDEN.

**Previous defect (G4B finding, remediated).** Evidence was initially held in a
process-local dict. With 2 Gunicorn workers, an evaluation on worker A followed
by a replay on worker B found no record and returned a false FORBIDDEN (observed:
12/20 MATCH, 8/20 false FORBIDDEN). This was an integrity/correctness defect of
the access decision, not merely an availability risk: a legitimate user was
denied depending on routing. Root cause: authorization state lived in per-process
memory. Mitigation: shared Redis-backed store; the ref remains opaque and is never
an authorization token; user, company scope and report permission are rechecked on
every replay (verified live: revoke → FORBIDDEN with no payload, restore → MATCH).

**Residual limits (not production-grade).** TTL is 3600 s; expiry or cache
eviction/flush fails closed to FORBIDDEN and the evidence must be re-created by
re-evaluating. Records are not durable across a Redis flush or restart. Cache
backend failure is logged with structured, PII-free diagnostics (correlation_id,
stage, exception_type, reason_code, operation) and returns a safe typed outcome;
no stack trace reaches the client. TTL expiry over live HTTP was not exercised
(unit-level only).

**Standards references (aligned / referenced only; no certification claimed):**
ISO/IEC 27001:2022, ISO/IEC 27002:2022, ISO/IEC 23894:2023, ISO/IEC 42001:2023.


## 10. Agent / Tool Security

Two typed tools only; schema-allowlisted inputs (company/signal/date/ref);
no tool can carry thresholds, filters, report names, SQL, URLs or user
identities. Tools run in the request context under the session user. The
deterministic engine, policy registry and evidence service sit outside the
model. Next-check actions are a fixed allowlist.

## 11. LLM Boundary / Prompt Injection

Source strings (remarks, party names, descriptions) never enter prompts — the
minimized payload contains only authorized derived fields. Report data is
treated as data, never instructions. Provider output is validated: AI003
banned-term screening + numeric grounding against the deterministic result;
any violation or provider failure → explanation UNAVAILABLE, deterministic
result untouched (pinned tests: banned term, ungrounded number, provider
failure). Prompt-injection source cases are proven in gold evidence
(injection probes leave results unchanged).

## 12. Data Validation

Strict types at the boundary (unknown keys rejected, strict YYYY-MM-DD, enum
signals); finite-Decimal money parsing (non-numeric/non-finite → SOURCE_ERROR);
malformed vs missing due dates distinguished; envelope echo checks (company,
report identity, exact filter dict — drift → INCONSISTENT_DATA); version pins
(contract 1.0.0 / formula 2026.1 / report name). VND-only gate before identity
(V2-01); Finance Book unsupported (absent from schema → rejected at A2).

## 13. Financial Integrity Controls

Exact Decimal arithmetic with operand-derived headroom; authoritative AP
comparison `N ≥ T×D` (display share never an operand); HIGH before WATCH with
GTE; materiality gates defined per signal (CURRENT_NET_AR_TOTAL /
AP_DUE_WINDOW_AMOUNT); dedupe/conflict fail-closed before aggregation
(CONFLICTING_OBSERVATION); multi-schedule fail-closed; zero denominators typed
(ZERO_DENOMINATOR / INVALID_DENOMINATOR / BASELINE_/CURRENT_DENOMINATOR_INVALID);
no zero-fill, no fabrication, no clamping of AI001 facts. Wire serialization
pinned (money 2dp / ratio 4dp / pp 2dp, ROUND_HALF_UP, no exponent, −0
normalized — POLICY GOLD traps pinned by tests).

## 14. Failure / Fail-Closed Design

First-failed-stage A1→A11; a failure established before policy can never
become POLICY_PENDING and no failure can become BENIGN. FORBIDDEN/
VALIDATION_ERROR/SOURCE_ERROR strip financial payload, source/evidence refs,
coverage and explanation text (enforced in-contract; tested at wire level).
Unexpected API exceptions are logged server-side (`frappe.log_error`) and
returned as sanitized SOURCE_ERROR without internals.

## 15. Logging / Sensitive-Data Handling

`observability.py`: pure JSON events; SHA256[:12]-hashed ids only; allowlisted
fields with enum validation (unknown keys dropped — fail closed); no raw
report rows, party names, amounts, invoice text, credentials or LLM
prompts/tokens; latency/count bounded. Events: evaluation completion,
evidence access outcomes. Matches the INV-03 zero-PII conventions of AI001/AI002.

## 16. Docker / Runtime Security Assumptions

Single-host Docker demo runtime; named volumes preserved; MariaDB/Redis on the
internal network; only port 8080 published. The AI003-local overlay bakes
application code into the image (no bind mounts); nginx Host-map is
config-only and does not change which site serves which data. `allow_tests`
remains enabled on the demo sites (accepted demo posture). Administrator
credential on the isolated verify site set to the stack standard (documented).
Read-only probe pattern (bind + tmpfs) used by gold evidence remains the
template for independent verification.

## 17. Threat & Risk Register

| ID | Threat | Treatment | Residual |
|---|---|---|---|
| T1 | Cross-company data access | verified company + envelope checks + evidence binding; generic denials | Low (demo) |
| T2 | Permission bypass via cached/ambient auth | checked-user gates at report/doc/evidence layers; synchronous-only | Low |
| T3 | Report/filter drift changing financial semantics | pinned filter dict + envelope echo verification | Low |
| T4 | Multi-schedule/multi-account miscounting | fail-closed preflight + provenance gate | Low |
| T5 | LLM prompt injection / ungrounded claims | minimized payload; banned-term + grounding validation; failure → UNAVAILABLE | Low-Medium |
| T6 | Evidence ref treated as bearer token | refs are non-authoritative; reauth per access | Low |
| T7 | Sensitive data in logs | allowlisted zero-PII events | Low |
| T8 | Policy tampering via client | policy fields absent from schema; server-side registry | Low |
| T9 | Brute-force/DoS on evaluation endpoints | none implemented (demo scope) | **Accepted for demo** |
| T10 | Evidence store cross-worker defect | shared Redis store with bounded 3600s TTL + fail-closed | Low |

## 18. Security Test Matrix

Executed (packet §18 mapped): unauthenticated access (A1, Guest, invalid
signal+malformed combined); unauthorized/unknown company; cross-company
evidence; report revoke/regrant + restricted-user metadata denial (live, METHOD
GOLD); malformed request / loose dates / unknown keys; future as-of;
unsupported currency (company + row contradiction); Finance Book unsupported;
currency-before-identity; duplicate/conflicting observations; multi-schedule
flattened-report; metadata permission denial + cross-company + nonexistent
parent (live); LLM failure/timeout/ungrounded/banned; payload suppression on
FORBIDDEN/VALIDATION_ERROR/SOURCE_ERROR; unexpected exception sanitization;
cross-worker evidence consistency (20/20 sequential replays across 2 workers);
live HTTP report permission revoke/regrant (`tests_e2e/test_security_revoke_regrant.py`).

## 19. Security Test Results

| Area | Result | Evidence |
|---|---|---|
| Stage/payload suppression (hermetic) | PASS | test_risk_signal_service.py (StageA/PayloadSuppression classes) |
| Identity/dedupe/currency gates (hermetic) | PASS | test_risk_signal_sources.py |
| Evidence authorization (hermetic) | PASS 21/21 | test_risk_signal_evidence.py |
| Live smoke incl. unauth/unknown-company suppression | PASS 7/7 | evidence/ai003_smoke_results_2026-10-02.json |
| Restricted-user live probes (report/metadata) | PASS (reused) | AI003_METHOD_GOLD_MANIFEST.yaml SECURITY cases |
| Cross-worker evidence consistency (live multi-worker) | PASS 20/20 | 20 sequential HTTP replays across Gunicorn workers (20/20 MATCH, 0 false FORBIDDEN) |
| Live HTTP revoke/regrant via AI003 endpoint | PASS 4/4 | `tests_e2e/test_security_revoke_regrant.py` live HTTP test |
| Semgrep SAST (repo CI) | PASS (unchanged baseline) | .github/workflows/ci.yml |
| Bandit on new code | No HIGH severity findings | bandit -ll run 2026-10-02 |

## 20. Known Risks

1. No rate limiting/backpressure on evaluation endpoints (demo scope).
2. Evidence store bounded TTL (3600s) — records expire after 1 hour, failing
   closed to generic FORBIDDEN.
3. Explanation provider endpoint/keys configured via env — mock default in
   demo; a real provider adds an external dependency inside the trust
   boundary (validated output, still data-only).

## 21. Residual Risks

Accepted for DEMO_ONLY: T9, risk 3 above; unknown unknowns normally
caught by G4B remain (G4B pending). No production exposure is intended or
supported.

## 22. Demo-vs-Production Restrictions

`policy_scope: DEMO_ONLY`; `production_calibrated: false` embedded in every
result and surfaced on the UI ("DEMO_ONLY — NOT APPROVED FOR PRODUCTION").
No automatic promotion path; production use requires Finance/Product-approved
calibrated policy, G4B acceptance, rate limiting and persistent audit storage.

## 23. Recommended Future Controls

1. Permanent evidence record archiving (DocType or cold audit log) beyond Redis TTL.
2. Rate limiting / request budget on AI003 endpoints.
3. Per-request provider budget + circuit breaker for LLM explanation.
4. Signed evidence records (hash chaining) if AS_KNOWN_AT semantics are ever
   approved (currently explicitly not offered).

## 24. Security Evidence Index

See `docs/features/AI003/AI003_EVIDENCE_INDEX.md` (per-item command, host/container,
date, revision, path). Primary: smoke JSON, METHOD/POLICY GOLD manifests,
hermetic suites, blocker note, revision b4eba4d.
