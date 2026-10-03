# AI003 â€” Evidence Index

Concise, navigable index. Each item: artifact, producing command, environment,
date, revision, path. No raw logs are duplicated here. Language note: the
SSOT and decision-sheet authority records are substantially Vietnamese;
section numbers/titles are cited so claims trace across languages.

Pre-build authority chain (committed baseline efd7046):
- METHOD GOLD 66/66 â€” `AI003_METHOD_GOLD_MANIFEST.yaml` + `AI003_METHOD_GOLD_EVIDENCE.md` + oracle `AI003_METHOD_GOLD_ORACLE.py`
- POLICY GOLD 17/17 + 4 proved N/A â€” `AI003_POLICY_GOLD_MANIFEST.yaml` + `AI003_POLICY_GOLD_EVIDENCE.md`
- Owner policy approval â€” `AI003_BUSINESS_POLICY_DECISION_SHEET.md` (top binding, 2026-10-02)
- Foundation retests â€” `docs/reviews/AI003_FINAL_FOUNDATION_RETEST_cdb9933_2026-10-01.md`, `docs/reviews/AI003_FOUNDATION_INDEPENDENT_RETEST_d8dd7c8_2026-10-01.md` + `docs/reviews/evidence/`

| # | Artifact | Command (shell) | Env | Date | Revision | Path |
|---|---|---|---|---|---|---|
| 1 | Contract unit tests (25) | `python -m unittest -q lotus_fin.tests.test_risk_signal_contract` | PowerShell, host, `PYTHONPATH=E:\lotus-fin\lotus_fin` | 2026-10-03 | current | `lotus_fin/lotus_fin/tests/test_risk_signal_contract.py` |
| 2 | Source tests (37) | `â€¦ test_risk_signal_sources` | same | 2026-10-03 | current | `tests/test_risk_signal_sources.py` |
| 3 | Policy/evaluation boundary tests (18) | `â€¦ test_risk_signal_policy` | same | 2026-10-03 | current | `tests/test_risk_signal_policy.py` |
| 4 | Evidence/observability tests (21) | `â€¦ test_risk_signal_evidence` | same | 2026-10-03 | current | `tests/test_risk_signal_evidence.py` |
| 5 | Service + security matrix tests (32) | `â€¦ test_risk_signal_service` | same | 2026-10-03 | current | `tests/test_risk_signal_service.py` |
| 6 | In-container AI003 suite (134) | `docker exec -w /home/frappe/frappe-bench/apps/lotus_fin frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest discover -s lotus_fin/tests -p "test_risk_signal*.py" -t .` | Docker backend container | 2026-10-03 | 316c5bd + working tree | 134/134 OK (0.92s). Earlier 285/280 container counts are superseded. |
| 7 | Live API smoke (gold-number assertions) | `docker cp docker/ai003-local/ai003_smoke_probe.py frappe_docker-backend-1:/tmp/` then `docker exec -w /home/frappe/frappe-bench/sites â€¦ python /tmp/ai003_smoke_probe.py` | backend container, site `ai003-verify.localhost` | 2026-10-02 | 4b22d93 | `evidence/ai003_smoke_results_2026-10-02.json` (not re-run in this pass) |
| 8 | E2E Playwright, live (16/16 PASS) | `python -u tests_e2e\\test_risk_signal_workspace.py` | host Chromium â†’ `ai003-verify.localhost:8080` | 2026-10-03 | 316c5bd + working tree | video: `tests_e2e/videos/ai003_risk_signal_e2e.webm`; screenshots `tests_e2e/screenshots/rs_01..rs_05*.png` (AR HIGH 72.73 at explicit 2026-09-26, no AR evidence button, AP BENIGN/WATCH, evidence MATCH, INCONCLUSIVE, FORBIDDEN, stale-clear, error recovery, keyboard, mobile 375px) |
| 9 | Audit round (0 CRITICAL / 4 HIGH fixed) | audit agent report 2026-10-02; fixes + regression rerun | â€” | 2026-10-02 | b4eba4d | fix applier `evidence/apply_audit_fixes.py` (kept as record) |
| 10 | Runtime image | `docker image inspect lotus-fin:ai003-local` (image NOT rebuilt in this pass; Python/JS bind via existing image + site) | Docker runtime | 2026-10-03 | 316c5bd + working tree | image id sha256:bb2fa7ce05680bb54bcbb335894ddcefe08f1cdc8aaa4683c91cc6b03383d975 |
| 11 | Wider hermetic discovery (non-AI003) | `python -m unittest discover -s lotus_fin/tests -p "test_*.py" -t .` in container | Docker backend container, NO bench site context | 2026-10-03 | 316c5bd + working tree | 164 run; 20 failed/errored are modules that need a Frappe site (import failures outside `bench`). This is an harness limitation, NOT a verified regression pass. The earlier "196 PASS AI001/AI002" claim is not re-verified here. |
| 12 | Cross-worker evidence acceptance | `python tests_e2e\\test_cross_worker_evidence.py` (2-worker Gunicorn, HTTP, unpinned) | host â†’ `ai003-verify.localhost:8080` | 2026-10-03 | 316c5bd + working tree | 20/20 MATCH, 0 false FORBIDDEN; cross-company â†’ FORBIDDEN; unknown ref â†’ FORBIDDEN (no existence leak). Expiry path covered by unit tests only. |
| 13 | Live HTTP permission revoke/regrant | `python tests_e2e\\test_security_revoke_regrant.py` | host â†’ `ai003-verify.localhost:8080` | 2026-10-03 | 316c5bd + working tree | PASS: MATCH â†’ revoke â†’ FORBIDDEN (no payload) â†’ restore â†’ MATCH |

Runtime note: after a Docker restart, `configurator` rewrites `sites/apps.txt` without `lotus_fin` (its image lacks the app), causing `Module Lotus Fin AI not found` (HTTP 404 on `getpage`). Fix applied: restore `apps.txt` (`frappe`, `erpnext`, `lotus_fin`), `bench clear-cache`, restart backend.

NOT_RUN / NOT VERIFIED: full-site `bench run-tests` (`allow_tests` disabled on the verification site by design); Docker rebuild (not performed); TTL-expiry over live HTTP (unit-level only).
