# Isolated startup and smoke

13 October 2026, Asia/Saigon. Evidence: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314`. No commit, push or production deployment.

User explicitly approved project `lotus-core-01a13314`, site
`core-01a13314.localhost`, localhost port 8097 and private volumes. Selection was
never inferred from the shared frappe_docker environment.

Actual commands (all final operations exit 0; exact full argv/log hashes in RUNTIME_COMMANDS.json):

```text
python docker/lotus-core/manage.py setup --project lotus-core-01a13314 --site core-01a13314.localhost --port 8097 --authorize-isolated lotus-core-01a13314
python docker/lotus-core/manage.py smoke --project lotus-core-01a13314 --site core-01a13314.localhost --port 8097
python docker/lotus-core/http_qualification.py --base http://127.0.0.1:8097 --credentials .runtime/lotus-core-01a13314/qa.json --output <evidence>/HTTP_1.json
python docker/lotus-core/manage.py cleanup --project lotus-core-01a13314 --site core-01a13314.localhost --port 8097 --authorize-isolated lotus-core-01a13314
```

Setup/smoke/HTTP/cleanup were repeated for a second cold launch, retaining the
same isolated DB/site volumes. First creation installed the framework and Lotus
on empty private volumes; repaired/hardened replays used that isolated site.
This is two cold process starts, not two independent fresh databases.

Read-only site smoke asserted exactly two installed apps; no erpnext module;
no Company/Sales Invoice DocTypes; valid native imports and hook registrations;
DB SELECT 1; Redis ping; React inclusion. Real nginx/backend ping returned pong.
Fresh short/long workers, websocket and scheduler were running in both final
status captures; backend/database/Redis health checks passed. This proves process
startup, not successful native business jobs or financial data readiness.

HTTP cases: guest core/legacy/v2 denial; ordinary login and identity; ordinary
readiness; legacy/v2/form-cmd denial; missing CSRF denial; authenticated Desk
session/token; valid-CSRF native capability disabled (503, private/no-store);
logout and session denial afterward. No successful financial read was asserted.

QA provisioning is explicit isolated setup support, separate from read-only smoke.
It creates only framework User/Role records, no business schema/data. Actual
passwords/tokens are omitted from evidence; configuration remains ignored/private.
Final cleanup removed only this project's containers/network and retained volumes.
Production/native business rollback was not performed.
