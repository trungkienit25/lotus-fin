# AI003 — Reproduction Guide

Verified on: Windows 10/11 host, Docker Desktop, Python 3.13 (host) / 3.14
(container), Chromium via Playwright 1.58. Shell per step is named; PowerShell
is the primary documented shell (paths `E:\lotus-fin`).

Assumptions: repo at `E:\lotus-fin`; compose project lives at `E:\frappe_docker`
(discover step 1 — do not trust hardcoded paths; `run.ps1`'s compose path is
broken on this machine); sites volume `frappe_docker_sites` persists.

## 0. Preflight gate (Git Bash or PowerShell)

```powershell
docker inspect frappe_docker-backend-1 --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'
docker ps --format '{{.Names}}\t{{.Status}}' | Select-String frappe_docker
```
Expected: 6 app services Up (queue-short/queue-long may be Exited(0) — the
AI003 path is synchronous; start them if desired: `docker start
frappe_docker-queue-short-1 frappe_docker-queue-long-1`); db healthy; redis up.

## 1. Backend unit tests (host, hermetic — PowerShell)

```powershell
$env:PYTHONPATH='E:\lotus-fin\lotus_fin'
python -m unittest -q lotus_fin.tests.test_risk_signal_contract lotus_fin.tests.test_risk_signal_sources lotus_fin.tests.test_risk_signal_policy lotus_fin.tests.test_risk_signal_evidence lotus_fin.tests.test_risk_signal_service
python -m unittest -q lotus_fin.tests.test_ai001_foundation_blockers lotus_fin.tests.test_ai002_foundation_blockers lotus_fin.tests.test_ai003_foundation_remediation lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed
```
Expected: 146 PASS for AI003 (current evidence index); 196 combined foundation PASS is historical, not rerun during documentation cleanup. (Order-dependence is NOT claimed between suites;
`test_access_and_reports` is container-only.)

## 2. Docker rebuild + recreate (Git Bash; absolute paths required)

```bash
docker build -f "E:\lotus-fin\docker\ai003-local\Dockerfile" -t lotus-fin:ai003-local "E:\lotus-fin"
docker compose -f "E:\frappe_docker\pwd.yml" -f "E:\lotus-fin\docker\ai003-local\compose.override.yml" up -d --force-recreate backend frontend websocket scheduler queue-short queue-long
docker image inspect lotus-fin:ai003-local --format '{{.Id}}'   # record digest
```
Named volumes are preserved. Any `docker cp`-style code sync invalidates
evidence until the image is rebuilt (no bind mounts).

## 3. Site migration + cache (PowerShell)

```powershell
docker exec frappe_docker-backend-1 bench --site ai003-verify.localhost migrate
docker exec frappe_docker-backend-1 bench --site ai003-verify.localhost clear-cache
```
Required after image rebuild when the Page/workspace records changed.
`sites/apps.txt` must list `lotus_fin` (the configurator image in the committed compose override supplies it; investigate image alignment if missing) — otherwise the desk
throws "Module Lotus Fin AI not found" and app assets are not linked.

## 4. In-container verification set (Git Bash)

```bash
MSYS_NO_PATHCONV=1 docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -q lotus_fin.tests.test_risk_signal_contract lotus_fin.tests.test_risk_signal_sources lotus_fin.tests.test_risk_signal_policy lotus_fin.tests.test_risk_signal_evidence lotus_fin.tests.test_risk_signal_service lotus_fin.tests.test_ai003_foundation_remediation lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed
```
Recorded builder result: 298 PASS (fix-4 round, see evidence index; not rerun during documentation cleanup). (Full discovery historically shows pre-existing order
pollution among site-connected suites — see AI003 tech doc §19.)

## 5. API smoke (gold numbers) — Git Bash

```bash
docker cp "E:\lotus-fin\docker\ai003-local\ai003_smoke_probe.py" frappe_docker-backend-1:/tmp/ai003_smoke_probe.py
MSYS_NO_PATHCONV=1 docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/ai003_smoke_probe.py
```
Expected: `"pass": true` — 7/7 cases (UNAUTH FORBIDDEN, unknown-company
FORBIDDEN, AR gold HIGH 72.73pp, AP gold BENIGN 0.3333 counts 4/2, evidence
MATCH, multi-schedule INCONCLUSIVE, DEMO disclosure). Read-only; no cleanup
needed.

## 6. Playwright E2E (PowerShell) — verified 34/34 at 3eb8207

```powershell
python tests_e2e\test_risk_signal_workspace.py
```
Target: `http://ai003-verify.localhost:8080` only (Chromium resolves
*.localhost; other browsers need a hosts entry; smoke curl uses `--resolve
ai003-verify.localhost:8080:127.0.0.1`). Read-only; screenshots land in
`tests_e2e\screenshots\rs_*.png`. The earlier E2E blocker note is historical. Live E2E passed 34/34 at `3eb8207`; see the evidence index and `docs/reviews/AI003_FINAL_INDEPENDENT_REVERIFY_3eb8207_2026-10-03.md`. The shared
`frontend` site is never used as an E2E target (site-cleanliness invariant).

## Environment fixes applied during this build (for reruns on this machine)

1. `sites/apps.txt`: appended `lotus_fin` (was missing → module-not-found +
   missing asset links).
2. `bench --site ai003-verify.localhost set-admin-password admin` (stack
   standard credential on the isolated verify site).
3. `System Settings.setup_complete = 1` (DB) on the verify site; the earlier
   bootinfo cache blocker was resolved before the verified E2E run.
4. nginx Host-map conf mounted read-only via compose override
   (`docker/ai003-local/nginx/frappe.conf`) — default site behavior unchanged.
5. Dockerfile bakes `/assets/lotus_fin/{js,css}` include assets.
