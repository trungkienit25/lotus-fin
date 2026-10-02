# AI003 — Evidence Index

Concise, navigable index. Each item: artifact, producing command, environment,
date, revision, path. No raw logs are duplicated here. Language note: the
SSOT and decision-sheet authority records are substantially Vietnamese;
section numbers/titles are cited so claims trace across languages.

Pre-build authority chain (committed baseline efd7046):
- METHOD GOLD 66/66 — `AI003_METHOD_GOLD_MANIFEST.yaml` + `AI003_METHOD_GOLD_EVIDENCE.md` + oracle `AI003_METHOD_GOLD_ORACLE.py`
- POLICY GOLD 17/17 + 4 proved N/A — `AI003_POLICY_GOLD_MANIFEST.yaml` + `AI003_POLICY_GOLD_EVIDENCE.md`
- Owner policy approval — `AI003_BUSINESS_POLICY_DECISION_SHEET.md` (top binding, 2026-10-02)
- Foundation retests — `docs/reviews/AI003_FINAL_FOUNDATION_RETEST_cdb9933_2026-10-01.md`, `docs/reviews/AI003_FOUNDATION_INDEPENDENT_RETEST_d8dd7c8_2026-10-01.md` + `docs/reviews/evidence/`

| # | Artifact | Command (shell) | Env | Date | Revision | Path |
|---|---|---|---|---|---|---|
| 1 | Contract unit tests (25) | `python -m unittest -q lotus_fin.tests.test_risk_signal_contract` | PowerShell, host, `PYTHONPATH=E:\lotus-fin\lotus_fin` | 2026-10-02 | b4eba4d | `lotus_fin/lotus_fin/tests/test_risk_signal_contract.py` |
| 2 | Source tests (37) | `… test_risk_signal_sources` | same | 2026-10-02 | b4eba4d | `tests/test_risk_signal_sources.py` |
| 3 | Policy/evaluation boundary tests (18) | `… test_risk_signal_policy` | same | 2026-10-02 | b4eba4d | `tests/test_risk_signal_policy.py` |
| 4 | Evidence/observability tests (16) | `… test_risk_signal_evidence` | same | 2026-10-02 | b4eba4d | `tests/test_risk_signal_evidence.py` |
| 5 | Service + security matrix tests (32) | `… test_risk_signal_service` | same | 2026-10-02 | b4eba4d | `tests/test_risk_signal_service.py` |
| 6 | In-container targeted verification (279) | `MSYS_NO_PATHCONV=1 docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -q lotus_fin.tests.test_risk_signal_contract lotus_fin.tests.test_risk_signal_sources lotus_fin.tests.test_risk_signal_policy lotus_fin.tests.test_risk_signal_evidence lotus_fin.tests.test_risk_signal_service lotus_fin.tests.test_ai003_foundation_remediation lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed` | Git Bash → backend container, site context | 2026-10-02 | b4eba4d | run output (this index is the record) |
| 7 | Live API smoke (gold-number assertions) | `docker cp docker/ai003-local/ai003_smoke_probe.py frappe_docker-backend-1:/tmp/` then `docker exec -w /home/frappe/frappe-bench/sites … python /tmp/ai003_smoke_probe.py` | backend container, site `ai003-verify.localhost` | 2026-10-02 | 4b22d93 | `evidence/ai003_smoke_results_2026-10-02.json` |
| 8 | E2E implementation + blocker analysis | `python tests_e2e/test_risk_signal_workspace.py` (blocked live; diagnostics in probe transcripts) | host Chromium/Firefox → ai003-verify.localhost:8080 | 2026-10-02 | 4b22d93 | `tests_e2e/test_risk_signal_workspace.py`, `evidence/AI003_E2E_BLOCKER_NOTE_2026-10-02.md`, screenshots `tests_e2e/screenshots/rs_*.png` |
| 9 | Audit round (0 CRITICAL / 4 HIGH fixed) | audit agent report 2026-10-02; fixes + regression rerun (128+196 PASS) | — | 2026-10-02 | b4eba4d | fix applier `evidence/apply_audit_fixes.py` (kept as record) |
| 10 | Image build + recreate + migrate | `docker build -f docker/ai003-local/Dockerfile -t lotus-fin:ai003-local E:\lotus-fin`; `docker compose -f E:\frappe_docker\pwd.yml -f docker/ai003-local/compose.override.yml up -d --force-recreate …`; `bench --site ai003-verify.localhost migrate/clear-cache` | Git Bash | 2026-10-02 | 4b22d93 | image digest sha256:21f61183dd3d62ed6a6c2142a933f9ef7ec100c631bb513e2fc649d7ac2be110 |
| 11 | AI001/AI002 regression (hermetic) | `python -m unittest -q lotus_fin.tests.test_ai001_foundation_blockers lotus_fin.tests.test_ai002_foundation_blockers lotus_fin.tests.test_ai003_foundation_remediation lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed` | PowerShell, host | 2026-10-02 | b4eba4d | 196 PASS |

NOT_RUN items (with reasons): live Playwright E2E pass (verify-site desk boot
loop — item 8 note); HTTP-level report revoke/regrant through the new endpoint
(same blocker; boundary-level live probes exist in METHOD GOLD). N/A items
carry proofs in POLICY GOLD (4 materiality N/As with V2.2 proof codes).
