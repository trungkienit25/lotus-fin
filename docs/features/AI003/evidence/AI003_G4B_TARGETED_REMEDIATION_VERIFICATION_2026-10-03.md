# AI003 — G4B Targeted Remediation Verification (2026-10-03)

Implementation-owner verification record for the targeted remediation pass on
branch `feature/ai003-risk-signal`. This is BUILDER evidence, not independent
verification. Scope: (1) evidence-store Redis error boundary + structured
diagnostics, (2) Docker configurator/app registry, (3) docs alignment.
Frozen items untouched: Contract V2.2, AI003_DEMO_POLICY_V1, DEMO_ONLY /
COMPETITION scope, production_calibrated=false.

## Baseline

- Reviewed commit: `117d7e5c787dfdc2caf1febb33f84bba41c746c1` (HEAD at start, no drift)
- Branch: `feature/ai003-risk-signal`
- Host: Windows 11, Docker Desktop, Python 3.13 (host) / 3.14 (container)
- Stack: `E:\frappe_docker\pwd.yml` + `E:\lotus-fin\docker\ai003-local\compose.override.yml`,
  site `ai003-verify.localhost` (verification stack only)

## Root causes fixed

1. **Redis boundary swallow (evidence store).** `frappe.cache().set_value()`
   suppresses Redis `ConnectionError` and `get_value()` catches it and returns
   `None`, so on the real wrapper a PUT returned an evidence ref while GET
   returned None (0 diagnostic events), and a process-local dict fallback
   produced same-worker MATCH / other-worker FORBIDDEN. Fix
   (`lotus_fin/lotus_fin/risk_signal/evidence.py`): raw Redis commands
   (`setex`/`get`/`delete`) on the existing Frappe cache client, site-namespaced
   keys via `make_key()` under `ai003:evidence:` (prefix and TTL 3600s kept),
   any init/SET/GET/DELETE failure logged once as structured
   `ai003_evidence_storage_error` (correlation id, sanitized exception type,
   allowlisted fields only) and raised as typed `EvidenceStorageUnavailable`;
   the process-local fallback dict, FIFO eviction and `__len__` were removed.
   A failed SET never emits a ref; the AP evaluation path
   (`service._ap_evidence`) drops evidence refs and the deterministic result
   keeps frozen-contract behavior. Replay maps the typed storage failure to
   `UNAVAILABLE` with null payload; missing/expired/cross-company/unknown stay
   generic `FORBIDDEN`. JSON serialization with Decimal/date round-trip keeps
   canonical hash semantics. Cache initialization failure is fail-closed (no
   silent fallback). Correlation ids now propagate into store boundary events
   (`create_evidence_record(..., correlation_id=...)`, `_STORE.get(..., correlation_id=...)`).
2. **Configurator image mismatch.** `configurator` ran `frappe/erpnext:v16.35.0`
   and rewrote `sites/apps.txt` from its own `apps/` (no lotus_fin) on every
   compose up → `Module Lotus Fin AI not found`. Fix
   (`docker/ai003-local/compose.override.yml`): `configurator.image:
   lotus-fin:ai003-local` (the custom image contains frappe, erpnext,
   lotus_fin). Resolved with `docker compose ... config` before running.
3. **Harness defect found during re-verification.**
   `tests_e2e/test_security_revoke_regrant.py` blanket-deleted ALL Custom Role
   docs with `report='Accounts Payable'` during setup and cleanup. Hardened:
   pre-existing AP Custom Roles are snapshotted and never deleted; revoke
   creates its own role only when none pre-exists (otherwise the harness
   aborts without mutating state); cleanup deletes only the created role and
   test user. Current site state preserved (no pre-existing AP Custom Role on
   `ai003-verify.localhost`; verified before and after).

## Commands and results (actual)

| Check | Command (shell) | Result |
|---|---|---|
| Evidence unit suite (host) | `python -m pytest lotus_fin/tests/test_risk_signal_evidence.py -q` (PowerShell, host, PYTHONPATH=repo app) | 27 passed (8 new storage-boundary tests: ConnectionError injection, timeout, SET-failure emits no ref, GET-failure vs missing key, cross-worker, no local fallback, TTL+Decimal/date round-trip, correlation-id diagnostics with zero sensitive error text) |
| Hermetic suite (host) | `python -m pytest lotus_fin/tests/ --ignore=...test_workspace_ui.py --ignore=...test_access_and_reports.py --ignore=...test_security_hardening.py` | 405 passed; the 3 ignored files fail collection with `ModuleNotFoundError: No module named 'frappe'` (pre-existing host-env limitation, unchanged by this pass) |
| AI003 suite (Docker) | `docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -q lotus_fin.tests.test_risk_signal_contract ... test_cashflow_failclosed` | 291 tests OK |
| Frozen AR/AP gold smoke (incl. AP display-rounding traps) | `docker cp docker/ai003-local/ai003_smoke_probe.py frappe_docker-backend-1:/tmp/` then `docker exec ... python /tmp/ai003_smoke_probe.py` | `"pass": true`, 7/7 cases — artifact `evidence/ai003_smoke_results_2026-10-03.json` |
| Cross-worker HTTP replay | `python tests_e2e/test_cross_worker_evidence.py` (host → ai003-verify.localhost:8080) | 20/20 MATCH, 0 false FORBIDDEN; cross-company → FORBIDDEN (payload null); unknown ref → FORBIDDEN (no existence leak) |
| Revoke/regrant (hardened harness) | `python tests_e2e/test_security_revoke_regrant.py` | PASS: MATCH → revoke (Custom Role → Accounts Manager) → FORBIDDEN, payload null → restore → MATCH; snapshot printed; site state preserved |
| TTL over HTTP (expiry mechanism) | `python tests_e2e/test_ttl_expiry_http.py` (new dedicated probe) | PASS: dedicated short-TTL record (4s) → fresh replay MATCH → post-expiry replay FORBIDDEN with null payload. This verifies the TTL EXPIRY MECHANISM over live HTTP; it is NOT a 3600-second wall-clock verification (production TTL value pinned by unit test: SETEX time=3600) |
| Live Playwright E2E | `python tests_e2e/test_risk_signal_workspace.py` (host Chromium → ai003-verify.localhost:8080) | PASS 16/16; video `tests_e2e/videos/ai003_risk_signal_e2e.webm`, screenshots `tests_e2e/screenshots/rs_*.png` |

## Registry durability

- Resolved config: `docker compose -f E:\frappe_docker\pwd.yml -f E:\lotus-fin\docker\ai003-local\compose.override.yml config`
  → `configurator image: lotus-fin:ai003-local`.
- Image rebuilt and recreated: image id
  `sha256:b9e70762321fea732299b547c68acc03a6d3b0c24a501fe94d0b91f9153953a4`;
  configurator exit code 0.
- After TWO consecutive recreate/start cycles that ran configurator:
  `sites/apps.txt` = `erpnext`, `frappe`, `lotus_fin` (written by configurator,
  not hand-edited).
- Runtime code parity: sha256 of `lotus_fin/risk_signal/evidence.py`
  (`cfdd2c2c35149a71f595335e50bf89bb0251c15d48c2903060758255b56d5700`) and
  `risk_signal/service.py`
  (`0fc8da0109b11a8cfae47f7715a7fb2738b63283dc636266667a8d910aa0aaa4`) identical
  inside container and working tree.
- `bench --site ai003-verify.localhost migrate` and `clear-cache` run after
  rebuild; module mapping resolves (E2E page loads; smoke 7/7).

## Failure-mode matrix actually exercised

| Mode | Path | Observed |
|---|---|---|
| Redis healthy | HTTP replay | MATCH |
| Missing / expired key | unit (`test_4_get_failure_distinct_from_missing_key`), HTTP TTL probe post-expiry | generic FORBIDDEN, payload null |
| Redis outage / timeout | unit fault injection at raw command boundary (ConnectionError/TimeoutError) | typed `EvidenceStorageUnavailable`; replay → UNAVAILABLE payload null; store path emits no ref; no local fallback |
| Permission revoked | live HTTP | FORBIDDEN, payload null; regrant → MATCH |
| Unknown / cross-company ref | live HTTP | generic FORBIDDEN, no existence disclosure |

## Remaining findings (NOT closed by this pass)

1. **Stale-response UI defect** (independent-reviewer finding, outside this
   patch's authorized scope): recorded as an open finding; G4B must not be
   declared PASS while it remains open.
2. `frappe` import required for 3 host test modules (container-only suites) —
   environmental, pre-existing.
3. Full-site `bench run-tests` remains not run (allow_tests disabled on the
   verification site by design).
4. 3600-second TTL wall-clock behavior not waited out (mechanism verified
   instead; see TTL row above).
