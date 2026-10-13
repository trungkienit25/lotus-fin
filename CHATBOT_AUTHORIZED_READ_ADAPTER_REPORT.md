# Lotus Fin authorized read adapter report

12 October 2026 · Asia/Saigon. **ADAPTER_IMPLEMENTATION = BLOCKED.** Concrete adapter implementation and live testing are conditional on [target approval](CHATBOT_ERP_TARGET_READINESS.md). No implementation change, mock permission substitute or live test was made here.

## Current boundary and exact routes

Approved architecture: React UI → typed Lotus backend API → server-owned authentication/context → typed search/open use cases → `IAuthorizedInvoiceReadPort` → in-process current-principal Frappe adapter → ERPNext. No second Node backend, generic executor, CRUD/RPC catalog, direct frontend ERP SDK or Administrator fallback.

| Component | Actual source observation |
|---|---|
| `api/invoice_actions_api.py` | Three decorated POST declarations, all routed to unconditional disabled helper; no controller/config/sink/read-port composition. |
| `InvoiceActionsController` | get_context private composition exists; public controller search/open always disabled despite optional use-case constructor arguments. |
| `IAuthorizedInvoiceReadPort` | Abstract bounded search/open interface. Actual consumers are SearchInvoicesService and OpenAuthorizedInvoiceService; test implementations are mocks. |
| `FrappeInvoiceAuthorizer` | Resolves session/site/Company/config/timezone seam; Company check is not invoice document/field authority. Its document method remains disabled. |
| `InvoiceActionsConfig` | Strict DTO, enabled defaults false; not a connected approved production config/key loader. |
| `InvoiceActionDelivery` | Required sink admission and safe one-terminal-event boundary exist privately; not connected by the current HTTP helper. |
| React client | createProductionTransport returns synthetic disabled503 with no network even when UI flag is on. |
| Serving app | All 17 selected P1/P2 paths absent; actual route registration/imports NOT_RUN. |

Capability names differ from concrete Python method names. The exact three approved family routes to qualify are:

| Capability | POST route |
|---|---|
| invoice.context / get_context | `/api/method/lotus_fin.api.invoice_actions_api.get_context` |
| invoice.search | `/api/method/lotus_fin.api.invoice_actions_api.search_invoices` |
| invoice.open | `/api/method/lotus_fin.api.invoice_actions_api.open_invoice` |

Do not create routes literally named `invoice.search` or `invoice.open`, or aliases to unchecked core calls. Whitelist only these transport methods; use cases and read port must remain internal.

## Fresh static Frappe findings

[Framework evidence](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/FRAPPE_STATIC_FRESH.json) contains original file hashes, signatures, line positions and bounded source excerpts read from the serving filesystem without importing app/site code. Some functions exceed the reader's 100-line excerpt cap; `source_truncated=true` is an explicit static-review limitation. No complete behavior proof is inferred.

- `frappe.get_list` delegates to qb_query.DatabaseQuery.execute. Permission-aware list semantics need actual target tests; they do not replace per-document custom-hook authorization.
- Direct database/query.get_query defaults `ignore_permissions=True`. Any use must explicitly establish permission enforcement; no raw-QB shortcut selected here.
- permissions.has_permission with a document name uses get_lazy_doc; exact document authorization can hydrate parent data and invoke custom/controller and user permission rules. Administrator has a shortcut; ordinary users are mandatory.
- get_permitted_fields may choose select permission if read is not specified; required read/filter/order/identity/version fields must be checked explicitly, including actual mask/custom permission behavior.
- Document.load_from_db contains `SELECT *` and child loading. Field-level read filtering/masking is a separate function. Generic get_doc followed by projection is not evidence of minimum physical reads.
- auth.validate_csrf_token has early returns for missing request/session/saved token, ignore_csrf, matching token and allowed referrer. Actual session/origin/proxy configuration must be tested; the decorator is not CSRF acceptance.
- handler.handle wraps returned data in response.message. The host helper already returns `{message: body}`: **static double-envelope risk** when composed with that handler. No actual double-envelope HTTP failure claimed because it was not executed.
- utils.response.as_json reads response.http_status_code; app.process_response applies frappe.local.response_headers. The host helper writes response.status_code and response.headers inside broad exception handling: **unqualified status/header delivery**. Disabled503/no-store/CID from private serialization cannot be claimed on HTTP.
- application dispatch calls sync_database and after-request hooks; serializer calls make_logs. Session/cookie/monitor/seen/view/log/queue side effects require measurement, not an assertion from read-only business intent.

## Conditional implementation plan

Before editing, run exact-UID GitNexus impact for each source target after checking dirty-tree freshness; warn on HIGH/CRITICAL, resolve UNKNOWN with source confirmation, and retain callers/processes/risk. Current controller graph reports UNKNOWN despite test importers; no operational all-clear.

1. Qualify approved installed-site schema, effective hook order, ordinary principal, map/company/timezone, masks and required fields. If authorization requires unbounded/full-parent hydration, stop and document the conflict instead of bypassing hooks.
2. Implement the proposed cohesive `infrastructure/erpnext/authorized_invoice_read_adapter.py` and, only if needed, a separate invoice query responsibility. Maintain ADR001 core/ports and <200-line source modules. Keep source, configuration and tests in a reviewed exact allowlist.
3. Search uses exact authorized company, fixed Sales Invoice DocType, allowlisted filters/order, bounded keyset and lookahead. Check every exposed candidate's fresh read/document/company/field/custom policy; unauthorized fields cannot be predicates. Required masked/missing fields fail closed. No total/unbounded fetch/native-form read.
4. Open verifies signed purpose/scope/config/query/version before lookup, freshly reauthorizes current actor/session/site/company/DocType/document/fields/custom hooks, then performs exact minimum read. Denial wins stale/missing/source details; a signature grants no permission. Record version change requires re-search.
5. Wire fresh context resolver, v1 context codec, v2 selection/cursor codec, typed use cases and required delivery sink into the explicit HTTP boundary. Use actual framework status/header APIs and one envelope, with strict body parsing/admission controls. No altered frozen outcome semantics to accommodate transport defects.
6. Account for every metadata/permission/lazy hydration/query/payload operation in the request budget before I/O. Compare source identity/schema/projection and fail closed on unknown outcomes or unavailable authorization. Measure cancellation limitations rather than claiming hard DB cancellation from cooperative checks.
7. Keep UI/API defaults disabled until private evidence passes. Any actual contract conflict returns a separately documented correction proposal; accepted P1/P2-A semantics cannot change silently.

## Real HTTP acceptance matrix — all NOT_RUN

Execute against approved private serving routes through the real proxy/session middleware, using ordinary account sessions provisioned securely. Capture redacted request shape, exact transport status/envelope/headers, CID/worker identity and expected/actual result for each case.

| ID | Actual route test | Required result/evidence |
|---|---|---|
| H01 | Authenticated POST for all three methods | Correct capability; one allowed envelope and exact status mapping. |
| H02 | GET/HEAD and unsupported method | No invoice read/side effect; framework rejection recorded, UI handles any untyped error safely. |
| H03 | Guest, expired/logged-out/disabled actor | No data/read; actual401/403 and framework body behavior recorded. |
| H04 | Missing/wrong CSRF, foreign origin/referrer, Host/site manipulation | Denial through actual middleware; no ignore_csrf/CORS bypass. |
| H05 | Strict body/extra/nested keys, duplicate JSON keys, invalid UUID/types/dates/filters, oversized body | Rejected before read; actual422/413/framework mapping verified, no generic RPC fields. |
| H06 | Outcome mapping | OK/PARTIAL200; AUTH_REQUIRED401; other denial403; stale409; document unavailable404; invalid/projection422; source502; disabled/unqualified503; timeout504, per frozen wire. |
| H07 | Correlation/confidentiality | Server CID header=body=event; no-store survives proxy/errors; no response secrets/tracebacks/unauthorized fields. |
| H08 | Envelope/serialization | Exact `{message: Outcome}` or approved root Outcome; no message.message, tuple leakage or double JSON. |
| H09 | get_context→search→explicit select→open | Stable read-family version and source anchors, same ordinary session/company/site, fresh authorization. |
| H10 | Revoke after search | Open denies/clears data; no stale permission cache grant across workers. |
| H11 | Alternate RPC/legacy/direct core route | No callable bypass of context, signing, fresh policy, budget or terminal sink. |
| H12 | Sink absent/write/flush/ack failure | No protected success, one attempt/no false ack, safe transport failure; no recursive fallback logging. |
| H13 | Reference/cursor tamper, wrong purpose/scope/key, retired key, replay/expiry/config change | Reject or freshly reauthorize valid same-scope read replay; never cached authority. |
| H14 | Framework pre-handler errors | Actual401/403/405/413/CSRF error bytes/headers tested; untyped errors remain safe transport failures. No invented429 policy. |

## Live ordinary-user permission/business oracle — all NOT_RUN

Independent QA owns expected fixture rights/values; do not compute gold through the adapter under test. Every case records fixture version, actor class, site/company, expected authorized fields, actual outcome, source identifiers, counters and side-effect interval.

| ID | Negative case |
|---|---|
| N01 | Cross-company invoice; no unauthorized row/label/count/ref exposure. |
| N02 | Unpermitted document, owner/share/query-permission distinctions. |
| N03 | Unpermitted required or optional field; no denied-field filter inference. |
| N04 | Custom document/controller/query hook denial. |
| N05 | Company access revoked between search and open; multiworker cache coherence. |
| N06 | Logout/expired session/disabled actor; no signed-token authority. |
| N07 | Site/connection/product/version mismatch. |
| N08 | Record version changed after selection; fresh denial precedence. |
| N09 | Missing/masked field or missing schema; no synthetic repaired value. |
| N10 | Search result deleted before open; safe nonexistence/denial precedence. |
| N11 | Invalid filters/unknown keys/types/prefix/date bounds. |
| N12 | Key rotation/retirement/config mismatch and expiry boundary. |
| N13 | Concurrent requests/tabs and stale selection/context. |
| N14 | Unauthorized pagination/cursor replay/query/window/page binding. |
| N15 | Missing/unhealthy audit sink and delivery failure. |
| N16 | DB/read-port timeout, interrupted read, late return and cancellation. |

| ID | Positive case |
|---|---|
| P01 | Exact permitted five-field document plus authorized outer company label/fixed reader descriptor. |
| P02 | Complete empty search yields EMPTY_RESULT; selection_required false. |
| P03 | Partial/incomplete search, including zero rows; no selection refs/open/cursor success. |
| P04 | Multirow bounded search and authorized next page with deterministic ordering. |
| P05 | Explicit selection even for one row; no automatic open. |
| P06 | Fresh authorized open with unchanged current principal/version. |
| P07 | Same-context get_context→search→open through real routes/UI. |
| P08 | Exact serialization, date/docstatus/version and opaque source identifiers; no financial verification claim. |

Historical P2-B independent report found empty/context/source-binding UI defects; this task does not repair or rerun them. Their current closure needs source fingerprint plus regression evidence before live UI acceptance. Synthetic DOM/network interception is not ERP permission proof.

## Resource qualification — all NOT_RUN

Preserve current offline profile as the starting contract: default/max page20/50; scan100; list calls2; search document checks51/open1; metadata10; search detail0/open detail1; provider256KiB; full response64KiB; cooperative5-second budget; five-page window;90/365-day dates; reference defaultTTL300s; automatic retries/LLM/reports0. These logical caps are not SQL counts or measured production SLOs.

Instrument actual SQL count/time/shape, rows examined where DB exposes it, returned/hydrated candidates and parents/children, wire/provider/full-envelope bytes, metadata/cache hits/misses and denied candidates. SQL text/parameters containing protected values stay in the approved restricted evidence channel; public reports use bounded aggregates. Record query deadlines, supported cancellation mechanism and unavoidable continuation. Test0/20/21/50/51/100/101 rows, lookahead, oversized fields, unauthorized background rows, page/query/cursor limits, collation/ties, cold/warm cache and concurrency. Stable ordering must match cursor comparison and actual database collation. Error budgets and admission/performance thresholds need explicit owner approval; no guessed p95/throughput PASS.

## ERP no-write protocol — all NOT_RUN

1. Restore the approved synthetic baseline and record image/site/schema/permissions/fixture hashes. Separate fixture setup/revocation/restore intervals from measured business-read intervals.
2. Before each read family, snapshot applicable Sales Invoice parents/children/version/_seen, related ledgers, permissions and relevant seen/view logs, queues, notifications/email, lifecycle/audit/error logs and files/cache/session state. Define exact tables/hooks with the approved target owner; do not assume a transaction rollback covers sessions, files or background work.
3. Execute positive/negative HTTP flows and capture database write/commit/queue/lifecycle instrumentation plus required application RESPONSE_DELIVERY events in the approved external sink.
4. Compare before/after business and side-effect fingerprints, investigate every delta and asynchronous settling window, and report framework session/access/log writes explicitly. Required app audit events are allowed only under declared sink policy; they do not excuse ERP business mutations.
5. Restore approved permission/key/sink changes and rehearse cleanup/rollback. Retain restoration verification and residual object counts. ERP_NO_WRITE_PASS requires the actual target evidence and stated scope; mocks, internal controller calls or no observed writes in this filesystem discovery cannot supply it.

No ERP HTTP/DB/business query, site initialization, credential configuration, fixture mutation or source function edit was executed. **REAL_HTTP_ACCEPTANCE NOT_RUN; ERP_PERMISSION_ACCEPTANCE NOT_RUN; ERP_NO_WRITE NOT_RUN; P2AB_LIVE_ACCEPTANCE BLOCKED; G10 BLOCKED.**
