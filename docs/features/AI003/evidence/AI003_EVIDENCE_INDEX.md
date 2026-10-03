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
| 4 | Evidence/observability tests (34) | `â€¦ test_risk_signal_evidence` | same | 2026-10-03 | fix-4 round (storage-boundary + decode-boundary tests: parent pickle bytes, invalid UTF-8/JSON, malformed records) | `tests/test_risk_signal_evidence.py` |
| 5 | Service + security matrix tests (32) | `â€¦ test_risk_signal_service` | same | 2026-10-03 | current | `tests/test_risk_signal_service.py` |
| 6 | In-container AI003 suite (298) | `docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -q lotus_fin.tests.test_risk_signal_contract lotus_fin.tests.test_risk_signal_sources lotus_fin.tests.test_risk_signal_policy lotus_fin.tests.test_risk_signal_evidence lotus_fin.tests.test_risk_signal_service lotus_fin.tests.test_ai003_foundation_remediation lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed` | Docker backend container (rebuilt image) | 2026-10-03 | fix-4 round | 298/298 OK (evidence suite also passes in isolation: 34 OK). Earlier 291/285/280/134 counts are superseded. |
| 7 | Live API smoke (gold-number assertions) | `docker cp docker/ai003-local/ai003_smoke_probe.py frappe_docker-backend-1:/tmp/` then `docker exec -w /home/frappe/frappe-bench/sites â€¦ python /tmp/ai003_smoke_probe.py` | backend container, site `ai003-verify.localhost` | 2026-10-03 | G4B targeted remediation pass | `"pass": true` 7/7 — `evidence/ai003_smoke_results_2026-10-03.json` (supersedes `ai003_smoke_results_2026-10-02.json`, kept as historical artifact) |
| 8 | E2E Playwright, live (22/22 PASS) | `python -u tests_e2e\\test_risk_signal_workspace.py` | host Chromium â†’ `ai003-verify.localhost:8080` | 2026-10-03 | fix-4 round (stale-response scenarios with real held-request delivery control; keyboard test asserts real result) | video: `tests_e2e/videos/ai003_risk_signal_e2e.webm`; screenshots `tests_e2e/screenshots/rs_*.png` |
| 9 | Audit round (0 CRITICAL / 4 HIGH fixed) | audit agent report 2026-10-02; fixes + regression rerun | â€” | 2026-10-02 | b4eba4d | fix applier `evidence/apply_audit_fixes.py` (kept as record) |
| 10 | Runtime image (rebuilt this round) | `docker build -f docker/ai003-local/Dockerfile -t lotus-fin:ai003-local E:\\lotus-fin` | Docker runtime | 2026-10-03 | fix-4 round | image id sha256:4eeb7dd024de1645099f74940742b4b6c6eccccc51d1438988d2d6e7c6080cc2; container/working-tree code hashes match (evidence.py d25c4578â€¦, ai_insights.py 1d2b45b8â€¦, risk_signal.js 16ff6b9aâ€¦). Supersedes sha256:b9e70762â€¦ and bb2fa7ceâ€¦ (kept as historical). |
| 11 | Wider hermetic discovery (non-AI003) | `python -m pytest lotus_fin/tests/` (host; 3 frappe-import modules excluded) | host, no frappe installed | 2026-10-03 | fix-4 round | 412 passed + 7 subtests. The 3 excluded modules need a Frappe site (import failure outside `bench`) — harness limitation, NOT a verified regression pass. The earlier "196 PASS AI001/AI002" claim is not re-verified here. |
| 12 | Cross-worker evidence acceptance | `python tests_e2e\\test_cross_worker_evidence.py` (2-worker Gunicorn, HTTP, unpinned) | host â†’ `ai003-verify.localhost:8080` | 2026-10-03 | fix-4 round | 20/20 MATCH, 0 false FORBIDDEN; cross-company â†’ FORBIDDEN (payload null); unknown ref â†’ FORBIDDEN (no existence leak) |
| 13 | Live HTTP permission revoke/regrant (hardened) | `python tests_e2e\\test_security_revoke_regrant.py` | host â†’ `ai003-verify.localhost:8080` | 2026-10-03 | fix-4 round | PASS: per-run unique user (no pre-existing user ever touched); pre-state snapshotted, conflict aborts exit 2 BEFORE any mutation (verified with a seeded foreign AP Custom Role) â†’ MATCH â†’ revoke â†’ FORBIDDEN (no payload) â†’ restore â†’ MATCH; MATCH → revoke → FORBIDDEN (no payload) → restore → MATCH; cleanup in finally removes only run-created artifacts; pre-existing AP Custom Roles before == after |
| 14 | TTL expiry mechanism over live HTTP (isolated probe key) | `python tests_e2e\\test_ttl_expiry_http.py` (unique probe ref AI003-EV-probe-<uuid>, collision-checked, short TTL 4s, via production EvidenceStore boundary) | host â†’ `ai003-verify.localhost:8080` + backend site context | 2026-10-03 | G4B targeted remediation pass | PASS: probe fresh MATCH â†’ post-expiry FORBIDDEN (payload null); existing production record untouched (same value hash, TTL 3599→3587 natural decay, still MATCH). Expiry MECHANISM only — NOT a 3600s wall-clock verification; production TTL (3600) pinned by unit test (SETEX time=3600) |
| 15 | Installed-Frappe raw Redis fault probe | `python tests_e2e\\test_raw_redis_fault_probe.py` (live `frappe.cache()` raw get/setex/delete patched in a site-context process, evidence keys only, restored in finally) | backend container, site context | 2026-10-03 | fix-4 round | 5/5 PASS: GET ConnectionError/TimeoutError â†’ endpoint UNAVAILABLE (payload null); SETEX/DELETE ConnectionError â†’ typed EvidenceStorageUnavailable; healthy MATCH after unpatch |
| 16 | Decode boundary public-endpoint probe | `python tests_e2e\\test_decode_boundary_endpoint.py` (public `get_risk_signal_evidence` in a separate site-context process; corrupt payloads injected into installed Redis under unique collision-checked probe refs) | backend container, site context | 2026-10-03 | fix-4 round | 5/5 PASS: parent pickle bytes / invalid UTF-8 / invalid JSON / valid-JSON-wrong-structure â†’ typed UNAVAILABLE, payload null, no unhandled exception, no pickle.loads; healthy JSON record â†’ MATCH unchanged |
| 17 | G4B targeted remediation verification record (round 1) | implementation-owner verification summary | Windows host + Docker Desktop | 2026-10-03 | commit 27fe965 (historical) | `evidence/AI003_G4B_TARGETED_REMEDIATION_VERIFICATION_2026-10-03.md` |
| 18 | Fix-4 verification record (this round) | implementation-owner verification summary (4 findings: decode boundary, harness state preservation, TTL key isolation, stale-response UI) | Windows host + Docker Desktop | 2026-10-03 | fix-4 round | `evidence/AI003_FIX4_VERIFICATION_2026-10-03.md` |

Runtime note (FIXED durably in this pass): `configurator` previously ran
`frappe/erpnext:v16.35.0` and rewrote `sites/apps.txt` without `lotus_fin`
after any Docker restart, causing `Module Lotus Fin AI not found` (HTTP 404 on
`getpage`). The temporary manual `apps.txt` restore + `bench clear-cache`
workaround of the 2026-10-02 round is superseded by the compose override
`configurator.image: lotus-fin:ai003-local`
(`docker/ai003-local/compose.override.yml`); after two consecutive
recreate/start cycles that run configurator, `sites/apps.txt` lists `erpnext`,
`frappe`, `lotus_fin`. The 2026-10-02 note above is kept as the historical
record of that round.

NOT_RUN / NOT VERIFIED: full-site `bench run-tests` (`allow_tests` disabled on
the verification site by design); 3600-second TTL wall-clock wait (expiry
mechanism verified instead, see row 14); independent verification of this round
(builder evidence only — see row 18 for its limitation).
