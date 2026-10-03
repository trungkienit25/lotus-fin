# AI003 — G4B Re-verification Prompt (for ChatGPT Work)

Branch: `feature/ai003-risk-signal` (repo `trungkienit25/lotus-fin`). Base the review on the pushed HEAD of this branch, not on any earlier report.
Scope is frozen: `DEMO_ONLY / COMPETITION`, Contract V2.2, `AI003_DEMO_POLICY_V1`, `production_calibrated=false`. Do **not** propose changes to thresholds, contract or method.

## Your role
Independent G4B re-verifier. Be adversarial and evidence-driven. A claim is only true if you can point to a file/line or a reproducible command. Report `NOT VERIFIED` rather than assuming. Do not start a new remediation cycle; produce findings only.

## What was remediated (verify each, do not trust)
1. **P1 cross-worker evidence defect**: process-local dict replaced by a Redis-backed store (`frappe.cache()`, key prefix `ai003:evidence:`, TTL 3600 s) in `lotus_fin/lotus_fin/risk_signal/evidence.py`. Check: opaque ref is not an auth token; user + company + report permission are rechecked on every replay; unknown/cross-company/expired all collapse to generic FORBIDDEN without existence leak; serialization (Decimal/date) is safe; payload holds no raw rows/party names; **there must be no silent fallback to a per-process dict that would re-introduce the defect** (inspect `get/put/delete` carefully — a local fallback exists in the code path; decide whether it is a hole under multi-worker).
2. **Silent exception swallowing**: `service.py::_ap_evidence` and `evidence.py` replay paths now log structured PII-free events via `observability.py`. Check allowlist, absence of raw rows/tokens/prompts, distinguishable event types (store failure vs. denial vs. unavailable), no stack traces to client.
3. **`sources.py`**: `PermissionError` mapped to typed FORBIDDEN failure. **`api/ai_insights.py`, `agent.py`**: replay re-checks report permission, passes `correlation_id`.
4. **`hooks.py`**: `persistent_cache_keys = ["ai003:evidence"]` was added — assess whether this is valid/needed in this Frappe version and whether it weakens the "bounded TTL / fail closed" claim.
5. **Playwright**: `tests_e2e/test_risk_signal_workspace.py` explicit `as_of_date=2026-09-26` for AR (HIGH, 72.73), AR has no evidence button, AP case opens evidence replay. Login uses `?redirect-to=/app/risk-signal`.
6. Docs: `docs/features/AI003/evidence/AI003_EVIDENCE_INDEX.md`, `AI003_TECHNICAL_DOCUMENTATION.md`, `AI003_SECURITY_SELF_ASSESSMENT.md`, `docs/features/AI001/AI001_SECURITY_SELF_ASSESSMENT.md` (AI001 must state it renders evidence metadata only; `verify_evidence_access` is AI002-specific).

## Evidence to inspect (claimed results)
- Playwright live: **16/16 PASS**, video `tests_e2e/videos/ai003_risk_signal_e2e.webm`, screenshots `tests_e2e/screenshots/rs_01..rs_05*.png`.
- Cross-worker: `tests_e2e/test_cross_worker_evidence.py` → 20/20 MATCH, 0 false FORBIDDEN; cross-company and unknown ref → FORBIDDEN.
- Revoke/regrant: `tests_e2e/test_security_revoke_regrant.py` → MATCH → revoke → FORBIDDEN (no payload) → restore → MATCH.
- AI003 container unit suite: **134/134 OK** (`python -m unittest discover -s lotus_fin/tests -p "test_risk_signal*.py" -t .` inside backend container).
- Runtime image id: `sha256:bb2fa7ce05680bb54bcbb335894ddcefe08f1cdc8aaa4683c91cc6b03383d975` (image was **not rebuilt** in this pass).

## Known gaps — confirm whether they block G4B (do not hide them)
- **No Docker rebuild** was done; the plan asked for one rebuild from the remediation HEAD. Determine whether the running container actually runs the working-tree code (bind mount vs. baked image) and whether that invalidates the evidence.
- **AI001/AI002 regression (earlier "196") and the "280" container count were NOT re-verified.** Broad discovery inside the container without Frappe site context ran 164 tests with 20 import failures/errors (modules needing a site). `bench run-tests` is disabled on the site (`allow_tests`). Decide whether this is acceptable or requires a proper in-site run.
- TTL expiry was only unit-tested, not live over HTTP.
- Records are not durable across Redis flush/restart (documented limitation).
- **Operational finding**: after Docker restart the `configurator` service rewrites `sites/apps.txt` without `lotus_fin`, causing `Module Lotus Fin AI not found` (404 `getpage`) and a blank workspace. Workaround: rewrite `apps.txt` (`frappe`, `erpnext`, `lotus_fin`), `bench clear-cache`, restart backend. Not fixed in compose. Judge severity for the demo.
- GitNexus reported CRITICAL (125 files / 49 flows) — recorded as non-blocking, no broad refactor attempted.
- Test credentials (`Administrator/admin`, a throw-away test user password) appear in e2e scripts for the isolated local verify site only. Confirm nothing real is exposed.

## Frozen behaviour to spot-check (must be unchanged)
AR: 4.99→BENIGN, 5.00→WATCH, 10.00→WATCH, 14.99→WATCH, 15.00→HIGH, 15.01→HIGH.
AP: exact `N >= T × D`; 199.99/400 (display .5000) → BENIGN; 299.99/400 (display .7500) → WATCH. UI must show `DEMO_ONLY` and `NOT production calibrated`.

## Required output
```
VERDICT: G4B_PASS | G4B_PASS_WITH_CONDITIONS | G4B_FAIL
FINDINGS (severity, file:line, evidence, reproduction)
CLAIMS VERIFIED / NOT VERIFIED (table)
DOC ACCURACY ISSUES
BLOCKERS vs. NON-BLOCKING DEBT
MINIMAL NEXT STEPS (if any), max 5
```
