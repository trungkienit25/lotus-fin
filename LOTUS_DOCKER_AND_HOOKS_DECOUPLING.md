# Docker and hooks decoupling

13 October 2026, Asia/Saigon. Evidence: `docs/reviews/evidence/frappe-only-2026-10-13-01a13314`. No commit, push or production deployment.

Default startup now uses `docker/compose.lotus-core.yml` and a verified official
Frappe build/base pair. The recipe initializes only Frappe and installs only
Lotus. It includes the actual React build and judge support scripts, and retains
database, cache/queue Redis, nginx, backend, websocket, workers and scheduler.
No ERPNext image, install-app command, report bootstrap or ERP credentials are
required by this profile. Framework DB/site-administrator bootstrap credentials
are freshly generated in ignored `.runtime/<project>/core.env`.

Legacy `docker/ai003-local/Dockerfile`, `docker/compose.judge.yml`, and
`docker/judge/init.sh` remain preserved historical ERP recipes. They are not the
new default and were not executed. Original `run.ps1`/`run.sh` bytes are preserved
in `before/`; default entry scripts now dispatch to the guarded core helper.

| Boundary | Registration/bootstrap | Default status |
| --- | --- | --- |
| Native core | before_request admission, authenticated readiness and three typed invoice declarations | Enabled framework; financial capability disabled |
| Optional ERP integration | Sales Invoice/Payment Entry events, financial schedules, Company custom field | Separate `lotus_erpnext` app, excluded from core image |
| Legacy ERP customization | Old Desk JS, ERP workspace links, report/data/setup routes | No core JS include; workspace hidden and ERP links removed; RPC denied |

Core has empty `doc_events`, `scheduler_events`, `fixtures`, and financial
persistent cache hooks. The Company fixture was transferred byte-for-byte to
the optional app. Original workspace JSON was preserved outside core bootstrap.
Core has its own logo and opens the framework Desk.

Optional integration requires ERPNext plus the explicit boolean
`lotus_erpnext_integration_qualified` site setting. Installation and every optional
event/scheduled job recheck qualification. This flag does not grant user/company
permissions, and the optional integration has not received business/security acceptance.

`before_request` denies every non-allowlisted Lotus RPC before legacy module
resolution, including old guest-whitelisted APIs and v2/form-cmd variants. All
Lotus RPCs require an authenticated principal. Native POST APIs additionally
require an initialized matching framework session CSRF header; missing-token
sessions cannot bypass admission before Desk initialization. No required native
import is hidden by a new fallback.

GitNexus was bound to E:/lotus-fin at HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`.
Hooks/packaging/new code returned UNKNOWN; dynamic framework consumers and helper
switches were confirmed by text after graph analysis. FollowupPreview was also
unindexed; its fixture consumer was confirmed before removing two logically
redundant comparisons that prevented TypeScript build. Numerical code was untouched.
Full dirty-worktree graph review reports HIGH aggregate risk (65 symbols/eight
flows), includes prior work, and caps its listing even after an expanded limit.
The index does not cover all new source; no clean graph/commit claim is made.
