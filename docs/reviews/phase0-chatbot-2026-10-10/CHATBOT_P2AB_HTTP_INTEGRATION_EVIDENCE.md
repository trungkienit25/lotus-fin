# LOTUS FIN — P2-A/P2-B HTTP Integration Evidence

12/10/2026 · Asia/Saigon · **P2AB_HTTP_INTEGRATION=BLOCKED; live execution NOT_RUN.**

Không thực hiện real invoice HTTP, permission/fixture DB reads/writes hoặc UI→ERP flow. Current image thiếu17selected backendfiles và chưa approved private target/lifecycle. Evidence này ghi static readiness cùng exact NOT_RUN matrix; không simulated PASS.

## 1. Fresh facts và scope

[Live target qualification](CHATBOT_P2A_LIVE_TARGET_QUALIFICATION.md) ghi fresh Docker/source/hash observations. Docker available sau user note; actual image vẫn `ed6e02f…`, no app-source bind,17/17missing. Host correction+protected/doc hashes25/25match. No new backend/frontend edits hoặc transport enablement.

Host methods đã declare authenticated POST/allow_guest=False:

- `/api/method/lotus_fin.api.invoice_actions_api.get_context`
- `/api/method/lotus_fin.api.invoice_actions_api.search_invoices`
- `/api/method/lotus_fin.api.invoice_actions_api.open_invoice`

Declarations không chứng minh methods registered/loaded trong serving workers; current runtime source files absent. API helper vẫn unconditional disabled, không compose resolver/usecases/key/audit. Controller search/open unconditional disabled. Actual responses/status/headers/CSRF trên endpoints **NOT_RUN**.

## 2. Static transport mismatch phải xử lý sau approved target

Fresh installed framework source:

|Observation|Current host integration gap|
|---|---|
|`handler.py:handle`46 places returned data in `frappe.response['message']`|Host helper returns `{message: body}`; direct composition risks double-message envelope.|
|`utils/response.py:as_json`146 uses `http_status_code`|Host helper sets `response.status_code`; actual status not qualified.|
|`app.py:process_response`286 merges `frappe.local.response_headers`|Host helper writes `response.headers` and swallows failures; CID/no-store delivery not qualified.|
|`auth.py:validate_csrf_token`81 has no-token/referrer/config early returns|Cookie-session/missing/invalid token/hostile origin negatives required; no default CSRF PASS.|
|Whitelist439/handler execute_cmd65 check registration and methods|Guest/GET behavior needs actual request, not direct handler tuple.|

[Actual framework source excerpts/hashes](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/FRAPPE_STATIC_SOURCE.json). This is source evidence, not observed HTTP failure. No API patch before target approval/readiness; no framework policy change/API-key workaround. After readiness, scope-specific implementation must return one bare Outcome for Frappe wrapper, set actual response keys, compose required terminal delivery and qualify safe audit-error transport.

## 3. Real qualification matrix — every row NOT_RUN

|Test / independently arranged scenario|Expected evidence after target approval|Current execution|
|---|---|---|
|Authenticated ordinary-user POST + valid CSRF|Exact current actor/site/context; get_context→search→explicit select→fresh open; source/minimum DTOs match|NOT_RUN|
|Guest|Real401/403/framework denial before business reads, safe body/CID limitations recorded|NOT_RUN|
|GET/other method|Framework method deny, zero protected reads; actual405/envelope limits recorded|NOT_RUN|
|Missing/invalid CSRF; hostile Origin/Referer; session has no saved token|Reject before business query under approved session/origin policy; no bypass/referrer fallback|NOT_RUN|
|Valid/uppercase/missing/malformed request_id|Valid UUID4 echo verbatim; invalid typed boundary422/replacement; no raw input logging|NOT_RUN|
|CID client spoof/header/body/terminal consistency|Server-owned CID, header=body=terminal; single current RID/generation/capability|NOT_RUN|
|Response wrapping/status/no-store|Exactly approved single envelope; real401/403/422/503/status+CID/no-store, no recursive double unwrap|NOT_RUN|
|Allowed/denied Company; cross-company/site|Independent fixture gold; server exact Company/current scope, no hidden data|NOT_RUN|
|DocType read denied/select-only; exact doc denied|Deny before list/exposure or selected document; permissions are not inferred from list/select|NOT_RUN|
|Required field denied/masked/custom query/doc hooks|PROJECTION_UNAVAILABLE/denial; no predicate/count inference/raw masked data|NOT_RUN|
|Fresh open after role/share/Company/field revoke, cold/warm workers|Denied after approved revocation boundary; signed ref does not grant|NOT_RUN|
|Modified/deleted known selected doc; denial+stale|Correct stale/unavailable classification; denial wins, no unrestricted existence probe|NOT_RUN|
|Forged/wrong-purpose/wrong-scope/key/expired refs|Zero requested-document reads before valid binding, safe typed terminal|NOT_RUN|
|Healthy/missing/outage required audit|Healthy exactly1attempt=ack=terminal; missing no admission; outage no protected success/retry|NOT_RUN|
|Source outage/late return/SQL blocking/audit timeout|Safe real classification and enforced physical bounds, no late success/mock-as-hard-cancel|NOT_RUN|
|Rows/list/doc/metadata/hydration/provider/response bytes|Instrument actual calls/SQL/bytes, approved limits and PARTIAL nonactionability; no global count|NOT_RUN|
|ERP business/seen/view/queue state before/after|Independent scoped fixture baseline/delta and lifecycle separation|NOT_RUN|
|P2-B current DTO/scope/generation lifecycle against real transport|Approved isolated client, actual click→open, denied/stale/revoked clearing, no late prior-context data|NOT_RUN|

Missing target does not turn these into SKIP/PASS. No real authenticated session inspected, no credentials requested/dumped, no mocks used for this matrix.

## 4. P2-B current output

Đã đọc [UI implementation](CHATBOT_P2B_UI_IMPLEMENTATION.md), [UI evidence](CHATBOT_P2B_UI_TEST_EVIDENCE.md), [handoff](CHATBOT_P2B_WORK_TO_CHAT.md) và actual `invoiceActionClient.ts` sau graph context. Builder report claims fixture60unit/3E2E/4B1regression; **NOT_RERUN / không independent UI acceptance** trong task này.

Actual client `createProductionTransport` returns synthetic disabled503/CAPABILITY_DISABLED with no network I/O even if flag on; flag predicate chỉ exact `VITE_LOTUS_INVOICE_ACTIONS='on'`. No approved auth/CSRF transport connected. This is an inert local client, **not a observed live HTTP503**. No replacement of React safeguards.

Frozen [wire contract](CHATBOT_P2B_WIRE_CONTRACT.md) byte hash `a4fb42f0bd5fcec7dcf3fad95ae72ae20601b72a05f02d3015445dc9955843c1`. Full exact DTO compatibility/real UI transport flow deferred until backend private HTTP target qualified, as request §7 requires. Không connect shared frontend/AI003/judge để có success.

## 5. Real no-write/resource gate

**ERP_NO_WRITE=NOT_RUN.** Task chỉ đọc Docker metadata và source/config-key-presence files; không query invoices/children/GL/payment/DocShare/User Permission/seen/ViewLog/queues. Không infer whole running stack zero writes from agent zero requests; existing scheduler/workers outside this qualification vẫn running.

Required approved synthetic baseline: Sales Invoice+children, relevant GL/payment, seen/view/log/queue side effects, permission roles/shares/user links. Record stable primary keys/counts/checksums/allowed fields before/after each read request, auth/session/cache operations separately, and fixture provision/revoke/cleanup outside measured business-read window. Independent gold owner must supply expected rights and records; do not generate expected ledger from tested adapter.

Actual list/document/metadata SQL calls, auth hydration cost, rows/provider/response bytes, hard DB/audit interruption, collation/keyset/cache coherence/concurrency/admission remain NOT_RUN. P2 application counters/soft deadlines cannot certify physical SQL/cancellation. No benchmark/SLO invented.

## 6. Commands, containment và cleanup

New evidence root `docs/reviews/evidence/chatbot-p2ab-runtime-readiness-2026-10-12/`. [Commands/exits](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/COMMANDS.json), [source baseline](../evidence/chatbot-p2ab-runtime-readiness-2026-10-12/SOURCE_BEFORE.json). Docker reads approved through automatic review; no automatic approval rejection outstanding.

Executed source readers:

```powershell
Get-Content -Raw docs/reviews/evidence/chatbot-p2ab-runtime-readiness-2026-10-12/RUNTIME_SOURCE_READER.txt | docker exec -i frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -B -
Get-Content -Raw docs/reviews/evidence/chatbot-p2ab-runtime-readiness-2026-10-12/FRAPPE_STATIC_READER.txt | docker exec -i frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -B -
```

Both exits0; no app import/site init/DB/HTTP, no bytecode. Readers record metadata/hashes/signatures only; candidate config keys exposed as presence booleans, not secret values. Readers/processes complete; no persistent helper/service created in container. No owned fixture/volume/session to clean, and no cleanup of shared objects. Host source/UI/Docker/config/evidence preserve checks recorded after task.

**Stop:** actual source mismatch+private target blockers. No adapter/HTTP/client implementation or live acceptance claimed.
