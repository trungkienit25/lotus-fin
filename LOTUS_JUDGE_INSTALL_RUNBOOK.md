# Judge install runbook — Lotus core

13 October 2026, Asia/Saigon. Evidence: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314`. No commit, push or production deployment.

Use the exact `rc-auth/LOTUS_CORE_SOURCE.tar.gz` candidate and its manifest,
not a clean clone of HEAD. Verify archive SHA256
`aea9751864ea8ff88a222014b4768be38a7906207db4cfdb418cae9aa4b84639` before extraction into a new directory.
Docker Desktop/Linux Docker, Linux amd64, Python 3 and access to the pinned
public build dependencies are required. ERPNext and shared frappe_docker are not.

From the extracted candidate, choose a NEW isolated suffix; `judge-demo` below
is an example, not authorization to mutate an existing project. The matching site
is `core-judge-demo.localhost`. Default port is 8097; choose a free `--port` and
repeat it on every command. Standard commands are identical through
`python docker/lotus-core/manage.py`, `./run.sh`, and `.\run.ps1`.

```text
python docker/lotus-core/manage.py help
python docker/lotus-core/manage.py build --project lotus-core-judge-demo
python docker/lotus-core/manage.py setup --project lotus-core-judge-demo --authorize-isolated lotus-core-judge-demo
python docker/lotus-core/manage.py status --project lotus-core-judge-demo
python docker/lotus-core/manage.py health --project lotus-core-judge-demo
python docker/lotus-core/manage.py smoke --project lotus-core-judge-demo
python docker/lotus-core/manage.py logs --project lotus-core-judge-demo
python docker/lotus-core/manage.py cleanup --project lotus-core-judge-demo --authorize-isolated lotus-core-judge-demo
```

Build has no DB/site mutation. Setup creates only a new owned project and framework
site, refusing existing unowned project/volume collisions. The helper binds exact
site/port/recipe ownership, clears ambient Compose/Lotus selection overrides, and
generates private random bootstrap passwords. It never chooses the shared
`frontend` site, clones shared frappe_docker, imports demo ERP data or switches
business requests to Administrator. Keep `.runtime` credentials private.

`http://127.0.0.1:<port>/api/method/ping` is framework liveness. Authenticated
`/api/method/lotus_fin.runtime.health.readiness` checks DB/cache/app readiness.
Native invoice POST APIs require a framework session and its CSRF header, then
return explicit CAPABILITY_DISABLED until an approved native adapter is composed.
React assets exist under `/assets/lotus_fin/core/`; no production native action
mount or complete financial UI is claimed. Legacy shared commands `sync/demo/up`
are deliberately unavailable through the default helpers.

Cleanup retains all volumes and requires the exact-project authorization argument.
No volume-erasure command is provided. Rollback: stop the owned test project with
the guarded cleanup command, retain its state, and replay a previously verified
source/image in a NEW isolated project/port. Do not point older code at an upgraded
DB without a separately tested backup/restore plan. No production rollback is qualified.

The original ERP-based recipes and source bytes remain available for separately
authorized legacy work. They are not required or used for this judge path.
