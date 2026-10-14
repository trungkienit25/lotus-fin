# Real HTTP evidence boundary

**LOTUS_REAL_HTTP = BLOCKED / NOT_RUN**, 12 October 2026. Bound source: [manifest](docs/reviews/evidence/chatbot-native-integration-2026-10-12-01a13088/SOURCE_CANDIDATE_MANIFEST.json), SHA-256 `46ede75ac9c27dc935a60629556e6c0d19d3e085c078c41628d2213b678ff05a`. `invoice_actions_api.py` SHA-256 `90ea0be717f55100d53f71fc308c166f4b0955c932bc57d68342b76dfdc1f23f`; controller SHA-256 `ab218965c93a31dfa467a85350768425ad6e9f4a3e4194be272a9c0e27c808d3`.

Three source declarations are marked authenticated POST (`get_context`, `search_invoices`, `open_invoice`). Their handler currently returns `NOT_AVAILABLE/CAPABILITY_DISABLED`; search/open in the controller also do so. The code sets a response status/header and returns `{message: body}`, but no serving Frappe session, CSRF middleware, exact one-envelope serialization, correlation header or terminal audit acknowledgement was observed. A successful fixture route is not this endpoint.

| Evidence item | Status | Actual execution or missing prerequisite |
| --- | --- | --- |
| Real authenticated ordinary-user POST, positive context → search → explicit open | **NOT_RUN** | No approved native source, policy, site or ordinary-user accounts. |
| Guest, disabled/revoked session, wrong tenant, document/field denial | **NOT_RUN** | Requires owned policy and live session/permission fixtures. |
| GET/POST/CSRF, invalid JSON/schema, duplicate keys, unexpected fields, framework 401/403/404/409/422/429/500 | **NOT_RUN** | Requires selected HTTP stack and real middleware trace. |
| CID body/header/event, no-store, bounded response, source errors, timeout, required audit failure | **NOT_RUN** | Requires serving worker, source, configured sink and controlled faults. |
| Local browser fixture | **PASS on host for P2-B/B1-S; PASS for candidate L3; candidate P2-B FAIL and B1-S TIMEOUT** | Host P2-B exit **0**, 3 passed; host B1-S exit **0**, 4 passed ([commands](docs/reviews/evidence/chatbot-native-integration-2026-10-12-01a13088/HOST_FIXTURE_COMMANDS.json)). Candidate L3 exit **0**, 1 passed. Candidate P2-B exit **1**, 3 failed because its network guard rejected host-resolved Vite `env.mjs` through a dependency junction. Candidate B1-S exit **124**, 150 s timeout after three failures; owned fixture process was stopped and port released ([candidate commands](docs/reviews/evidence/chatbot-native-integration-2026-10-12-01a13088/E2E_COMMANDS.json)). All are synthetic browser evidence only. |

Live test requirements: a named isolated Lotus core target, approved ordinary users/records, session and CSRF policy, fixture snapshot/restore, audit sink, source/image identity, cleanup and rollback owner. Record raw method/status/header/body shape with sanitized IDs, server/worker hashes, effective app list, permission/source/audit traces and before/after business snapshots. No shared, production or judge endpoint was contacted.
