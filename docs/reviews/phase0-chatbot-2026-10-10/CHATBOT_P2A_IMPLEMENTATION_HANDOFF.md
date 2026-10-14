# LOTUS FIN — P2-A Implementation Handoff

12/10/2026 · Asia/Saigon · Contract/handoff only, không coding hoặc dispatch.

**P2A_OFFLINE_BUILD_READY = YES; P2A_TARGET_READY = BLOCKED; P2A_LIVE_PERMISSION_QUALIFIED = NO.** READY nghĩa là có nền P1 và contract tối thiểu để chuẩn bị build disabled offline. Trước coding cần quyết định §7, nhận allowlist mở rộng §5 và fresh graph impact; trước live cần đóng T01–T07 trong [preflight](CHATBOT_P2A_TARGET_PREFLIGHT.md). Không có release approval trong tài liệu này.

Authority: [P1 MASTER](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md) §3–9, [Action Executor Decision](CHATBOT_ERP_SDK_ACTION_ARCHITECTURE_DECISION.md), [latest independent P1 PASS](CHATBOT_P1_FINAL_INDEPENDENT_RECHECK.md), ADR001/Security V3. Không thêm SSOT/outcome enum hoặc executor registry mới. Hợp đồng semantic dưới đây được xác định cho bàn giao; production values vẫn **DECISION_PENDING**.

## 1. Vertical slice tối thiểu

`invoice.search` → user chọn một result → `invoice.open`. `invoice.context` là endpoint nền sẵn có để lấy scope server. Backend typed use cases + in-process Frappe adapter. Không SDK/dependency/service mới, LLM/planner, financial math, report, overdue/customer lookup, native editable Form, onload/seen/view log, child/items/taxes/payment/attachment reads hoặc ERP writes. P2-A trả descriptor; React reader và explicit-selection UI thực thi thuộc P2-B, không đưa vào allowlist P2-A.

Mọi request lấy actor/SID từ authenticated Frappe request, site từ trusted routing + approved mapping. Client company chỉ là candidate lúc get_context; search/open không nhận company/site/product/connection/user/fields/method/url overrides. Không constructor identity injection trong production composition; không global set_user/Administrator fallback. Không có production session hiện tại đã được qualified.

Fresh authorize Company + capability + DocType read + fields/masks; document gate lại cho mỗi candidate/open. List/query permissions và document permissions là hai phép kiểm khác nhau. Approved field predicates cũng phải readable/unmasked trước query để ngăn inference. Share/owner/custom hook không được vượt Company/DocType policy của pilot. Không đáp ứng target API/hook/bounds → TARGET_UNQUALIFIED hoặc PROJECTION_UNAVAILABLE, không bỏ check.

## 2. Request, result và pagination contract

|Endpoint|Input exact|Output data khi OK|
|---|---|---|
|get_context|`request_id: UUID4`, `company_candidate: string`|context_ref/version, authorized company_label, allowed_filters, server date defaults, expires_at|
|search_invoices|`request_id`, `context_ref`, `expected_context_version`, `invoice_type: SALES`, typed `filters`, bounded `page_size`, optional signed cursor|items, returned_count, total_count:null, page_complete, has_more, next_cursor, selection_required, limitations|
|open_invoice|`request_id`, `context_ref`, `expected_context_version`, `selection_ref`|document minimum row without selection_ref, authorized company_label, fixed navigation descriptor|

Filters chỉ có `invoice_name_prefix`, `posting_from`, `posting_to`, `docstatus=DRAFT|SUBMITTED|BOTH`. Thiếu cả date pair → server site-local last 90 calendar days including today; chỉ thiếu một date → INVALID_REQUEST. Window inclusive `(to-from).days+1`; future/reversed/over-max dates bị reject, không clamp. Docstatus BOTH map 0/1, luôn loại cancelled 2; không invoice business status/overdue filter. Explicit empty date fields/wrong types/extra keys bị reject. Prefix NFC ≤128 chars, nonempty nếu supplied; reject NUL/control; `%`/`_` phải literal escaped, query parameterized; không substring/arbitrary SQL.

P2 get_context phải bổ sung approved date defaults và lấy `expires_at` từ actual signed token expiry. Current controller dùng deadline_at_utc thay TTL expiry và chưa trả date defaults; sửa trong allowlisted controller, không tái diễn field semantics sai khi wiring.

Current SearchRequestDTO `filters: Dict[str,str]` là placeholder P1, chưa closed nested schema. Thay bằng strict typed filter model; boolean không là int/page/docstatus; JSON duplicate keys/oversized bodies bị reject trước DTO business processing. Tên/length maxima đã có không chứng minh toàn bộ transport decoding. Default projection proposed **không customer_label**; optional customer_name chỉ được thêm sau phê duyệt field/mask oracle riêng, không linked Customer read.

Internal projected business fields: `name, company, posting_date, docstatus, modified`. Public row: `invoice_type=SALES, invoice_id, posting_date, docstatus=0|1, record_version, selection_ref`. Company internal exact match; modified tạo opaque record_version, không gửi raw modified. Field masked/denied thuộc required identity/predicate/version → NOT_AVAILABLE/PROJECTION_UNAVAILABLE, không leak count/inferred filter. Optional customer_name nếu được approved và masked/denied thì omit property hoàn toàn.

Authorized result phải đủ required fields, không duplicate IDs, đúng company/date/docstatus và exact read permission. Không repair source bằng demo/zero/default. returned_count=items.length là số đã được phép trả, total_count luôn null. Một result cũng selection_required=true; user không chọn → không open call. Backend không thể chứng minh click bằng signed ref; ref chỉ chứng minh result đã được server phát hành và fresh authorization, UI interaction là P2-B oracle riêng.

Fixed name ASC keyset, same target DB collation/comparison semantics; không client order/offset. First search tạo permission-aware **authorized** upper-name bound, cursor gắn window bound/last-name/page-index/normalized query/page size/current scope. Không expose tên bound/last-name của doc chưa authorized trong signed-but-readable claims. Nếu không thể tìm authorized bound/extra lookahead trong budget → incomplete. Không dùng global MAX/name/count query để suy ra hidden invoices.

Upper-bound/list lookahead/candidate permission work đều đếm budget. Có next_cursor chỉ khi page hoàn tất, còn page allowance và có thêm một **authorized** row. LIVE_KEYSET không là snapshot; inserts/changes/revocation có thể đổi window. Same query/page size bắt buộc ở next page; mismatch → STALE_CURSOR. Page_complete chỉ là bounded page, không toàn bộ công ty. Trang 5 mà cần vượt window cap → PARTIAL/COVERAGE_INCOMPLETE, no cursor/selection refs; user refine/restart explicit, không broaden tự động.

PARTIAL chỉ trả subset độc lập authorized với source.coverage=INCOMPLETE, page_complete=false, has_more=null, next_cursor=null, **mọi selection_ref=null**. Zero items nhưng scan chưa hoàn tất vẫn PARTIAL, không EMPTY_RESULT. Nếu không có source observation hợp lệ thì dùng SOURCE_ERROR/TIMEOUT, không fabricate PARTIAL. Explicit provider/auth denial theo P1 precedence → FORBIDDEN/null toàn bộ; normal candidate không eligible có thể loại trước exposure, không forward nested denial payload trong partial items.

## 3. Scope, signed reference, open và delivery

Các P1 primitives reuse nguyên privacy/denial/audit semantics. Current codec chỉ có doc_id, không record_version/query/window; không dùng token P1 hiện tại để tuyên bố selection/cursor P2 hợp lệ. Proposed extension:

|Binding|Contract cần thực hiện|
|---|---|
|Context|Actor/SID opaque keyed binding, site/product/connection/version/company, contract_version/projection, approved policy revision, expiry; fresh principal/scope mỗi request|
|Context fingerprint|Ổn định qua context→search→open cho cùng scope/policy. Current authorizer fingerprint có capability, nên không so fresh search context trực tiếp với context token v1 mà bỏ binding check. Refactor fingerprint thành read-family scope; capability vẫn fresh authorize riêng, không coi context capability là grant|
|Policy version|Approved connection_version phải bump khi đổi mapping/key/projection/budget/filter/timezone/permission policy config; fingerprint bao gồm contract/projection. Per-user rights vẫn recheck, không dựa version như permission snapshot|
|Selection|Purpose invoice.open; exact doc_type Sales Invoice/doc_id/opaque record_version/query fingerprint cùng scope/context/contract/projection/key/time bounds. Chỉ mint từ complete authorized search|
|Cursor|Purpose invoice.cursor; exact normalized filters/page size/order/authorized upper bound/last key/page index/window identity + same scope/version/expiry|
|Wire/schema|Giữ approved P1 context `ref.v1` semantics và opaque-actor.v1 privacy tests; proposed P2 selection/cursor `ref.v2` strict purpose-specific claims. P2 read usecases reject v1 selection/cursor thiếu bindings, không fallback. Schema/wire decision phải được Chat nhận trước coding; không tự đổi outcome `p1.invoice.v1`|
|Key|Dedicated HMAC-SHA256/current key-id, constant-time verify, canonical strict JSON; no raw actor/SID/key; retired key invalidates old handles. Missing/unqualified key/map → TARGET_UNQUALIFIED|

Decode bounded token shape → authenticate MAC/schema/purpose/key → fresh request context → verify all bindings/expiry → exact document authority. Không document lookup theo body invoice_id; không unrestricted existence probe khi MAC/scope sai. Untrusted payload claims chỉ được dùng để resolve company candidate sau signature validation và approved map check; rồi exact Company authority quyết định. Expiry semantics proposed **reject now >= expires_at**, equality boundary phải test; P1 codec currently `now > expires_at`, đây là P2 extension boundary, không silently reinterpret historical P1 acceptance.

Open reauthorizes current Company/DocType/document/projection before revealing changed/deleted details. Fresh authorized projected read + matching company, then compare record_version; changed → STALE_SELECTION. Unauthorized wins version/staleness; wrong/forged scope → ACCESS_DENIED. Known formerly authorized unavailable fixture → DOCUMENT_UNAVAILABLE without unrestricted global existence check. Race during permission/version/projection observation → fail closed/research; no atomic/snapshot guarantee claimed until target transaction/cache behavior is qualified.

Open response `navigation={kind:LOTUS_READ_VIEW,view:sales-invoice-minimal-v1}` only; no URL/doctype native form route/run_method/html. Source evidence: ERP_READ, AUTHORIZED_READ, server product/site/connection/version, invoice.min.v1, observed_at UTC/site timezone, PAGE_COMPLETE/LIVE_KEYSET. Không financial VERIFIED. Reader chỉ display bytes đã authorized tại observation; không thể thu hồi bytes đã thấy, nhưng mọi refresh/open mới phải reauthorize.

Outcome giữ sáu status và closed reasons P1. HTTP mappings **reuse current ActionResponseBuilder**: OK/PARTIAL 200; auth 401; access/company/CSRF 403; INVALID_REQUEST/PROJECTION_UNAVAILABLE 422; context/selection/cursor stale 409; unavailable authorized doc 404; SOURCE_FAILURE/INVALID_PROVIDER_RESPONSE 502; deadline 504; target/disabled 503. Không tự đổi source outage thành 503 (MASTER có candidate 502/503 nhưng serializer hiện tại 502). Framework pre-handler errors/405/413 có thể không typed envelope: decoder fail closed, không recursively unwrap hoặc bắt raw error làm success.

API lấy bounded request body, tạo server UUID4 CID, giữ valid request UUID4 verbatim; invalid/missing ID → replacement + INVALID_REQUEST, deny precedence vẫn giữ. Return bare Outcome để Frappe wrap **một** message. Set actual http_status_code và local.response_headers gồm matching X-Correlation-ID/Cache-Control:no-store; không swallow audit errors. Existing InvoiceActionDelivery revalidate outcome, đúng 1 terminal event healthy. Absent required sink → no admission; failing acknowledgment → no protected response, safe transport failure mapping, one attempt/0 ack/no retry. Child stages cùng CID, không coi child logs là duplicate terminal.

POST-only/Guest forbidden bằng real whitelist, session/CSRF/origin qualification của target. Không sửa middleware/auth policy, không API-key/Admin workaround. Error envelope/CID trước handler nếu framework không hỗ trợ hiện tại phải ghi limitation và không claim full transport gate PASS; out-of-allowlist middleware amendment cần task khác.

## 4. Budget register — tất cả production values chờ duyệt

Các proposal lấy P1 MASTER §7, không tự invent SLO/config đang dùng. Test profile có thể dùng proposals dưới tên explicit synthetic fixture; production loader phải validated/fail closed, không auto-enable bằng default.

|Budget/config|P1 proposal / existing bound|Tình trạng/điều kiện|
|---|---|---|
|page_size_default/max|20/50|Config hiện có; reject >max, không clamp|
|scan_rows_max/request|100|Tính upper-bound/candidates/lookahead, duplicate hoặc denied cũng count|
|pages/window|max 5|Signed page index; vượt → no actionable partial|
|date default/max|90/365 inclusive days|Site timezone phải approved; authorizer hiện hardcodes Asia/Ho_Chi_Minh, không coi là site truth|
|prefix/company/context version|128 chars /128 chars /128 chars|Existing maxima, strict control/NFC validation|
|body_max|16 KiB UTF-8 raw bytes|Nginx hiện client_max_body_size 50m, buffer16K không là16KiB cap; cần endpoint pre-parse enforcement/test|
|ref/cursor input max|2048 chars each|Existing DTO/codec; v2 worst-case payload phải fit. Bounded decode/duplicate keys/schema required; nếu không fit quay lại Chat, không tăng cap ngầm|
|deadline total|5000 ms|Existing config bounds1000–30000 không là approval để chọn30s; fresh per request, count auth→query→serialization→required audit. Hard DB/audit blocking bound chưa qualified|
|source_list_calls|max 2/request|Upper bound + bounded page/lookahead; source API count không là SQL count|
|doc permission checks|51/search;1/open|Includes bound candidate. Page50+independent bound+lookahead có thể cần52: **không nâng ngầm**, trả PARTIAL nếu51 không đủ; product quyết full50 first-page hoặc amended cap52|
|auth/metadata calls|max10/request|Lazy parent/hook/link reads count; không skip mandatory checks vì hết budget|
|invoice_detail_reads|1/open;0/search projected detail calls|Extra lazy parent authorization reads không là free: account riêng bytes/SQL/auth budget, cần qualified target |
|business child/term/report reads|0|Lazy hook cần children → unsupported target, không expand tự động|
|response/provider bytes|64 KiB/256 KiB|UTF-8 serialized output/provider fetched totals; include auth hydration. No corrupt JSON truncation; no selection ref if incomplete|
|LLM/report calls/retries|0/0/0|User retry fresh request/rights, không tự retry|
|context/selection/cursor TTL|300s|Existing config60–3600 không approve range làm production default mới; deadline và token TTL khác nhau|
|UI generation/admission|1 current request/UI; proposed2 actor+site concurrent|Server distributed limiter/coherence chưa có; no process-local assurance|
|structured audit TTL|7days candidate|Restricted storage/rotation/retention/privacy owner phê duyệt; ACK không durability|
|clock future tolerance|P1 existing60s|P2 equality/clock-skew decision và synthetic boundary tests; không tăng tolerance|
|SLO/SQL/RSS thresholds|UNSET|Cần representative baseline và approval, không chọn p95/throughput/RSS tự động|

Boundary oracle: 0/20/21/50/51/100/101 rows, unauthorized/long/masked fields; later 10k/100k background, actual workers concurrency1/5/20, cold/warm cache. Chưa tạo workloads hoặc benchmark. Deadline phải ngăn late completion success; cooperative timer không chứng minh DB/audit interrupt. Không qualified hard mechanisms → target BLOCKED, không nâng timeout để PASS.

## 5. Exact proposed P2-A implementation allowlist

Mọi source path dưới `E:/lotus-fin/lotus_fin/lotus_fin/`. Đây là **proposed expanded allowlist cần nhận trước coding**, vì original P1 §9 chỉ cho six new modules + controller/API không đủ typed filters/version claims/config/fresh document seam. Không sửa file trong phiên preflight. Nếu cần thêm path ngoài bảng, quay lại review scope trước edit.

|Kind|Exact relative path|Trách nhiệm|
|---|---|---|
|NEW|application/port/i_authorized_invoice_read.py|Typed permitted search/read observation + remaining budget|
|NEW|application/service/search_invoices.py|Bounded authorization/filter/page/selection orchestration|
|NEW|application/service/open_authorized_invoice.py|Signed selected identity/fresh rights/version/read orchestration|
|NEW|domain/schema/invoice_read.py|Closed filters/query/rows/page/read models/invariants|
|NEW|infrastructure/erpnext/authorized_invoice_read_adapter.py|Qualified Frappe permission-aware source adapter|
|NEW|infrastructure/erpnext/invoice_read_query.py|Cohesive fixed keyset/filter/projection/query budget helper; optional P1 path now explicitly included|
|NEW|presentation/dto/invoice_action_response.py|Discriminated search/open response DTO; no competing outcome|
|NEW|infrastructure/security/invoice_reference_claims.py|Purpose/version-specific typed claims, schema separation from codec; bounded parsing|
|EDIT|api/invoice_actions_api.py|Disabled real composition, strict POST decoding/single wrap/status/headers/safe audit error transport|
|EDIT|presentation/controller/invoice_actions_controller.py|Fresh context + usecases + existing terminal boundary|
|EDIT|presentation/dto/invoice_action_request.py|Closed nested filters/bounds, preserve P1 UUID semantics|
|EDIT|infrastructure/security/action_reference_codec.py|v2 selection/cursor authentication, preserve approved context/privacy behavior|
|EDIT|infrastructure/security/frappe_invoice_authorizer.py|Stable read-family fingerprint, fail-closed exact-document seam and fresh context checks|
|EDIT|infrastructure/config/invoice_actions_config.py|Explicit bounded read budgets/validated disabled target composition; no secrets committed|
|NEW TEST|tests/test_invoice_read.py|Pure contract/port/permission/filter/cap negative tests|
|NEW TEST|tests/test_invoice_read_integration.py|Actual isolated target HTTP/permission/no-write tests, skip unless approved target supplied|
|NEW TEST|tests/test_invoice_read_references.py|v2 scope/query/version/cursor/privacy tests|
|NEW TEST|tests/test_invoice_read_transport.py|Isolated real delivery/HTTP codec/disabled-wrapper tests|
|NEW TEST|tests/test_invoice_read_budgets.py|Calls/bytes/deadline/partial/admission boundary tests|

Không default add conftest/init scripts/fixture tools. Fixture helper chỉ trong cohesive allowlisted test modules, không init site tự động; import ERPNext test helpers bị cấm. Modules <200 dòng gồm blank lines; nếu table-driven tests/source không vừa thì xin exact cohesive path amendment, không arbitrary split/generic framework. Current authorizer gần cap nên replace disabled branch/cohesive query helper, không thêm dài vô hạn.

Reuse **read-only**: domain/schema/action_outcome.py (denial matrix/source), presentation/dto/action_outcome.py, presentation/response/action_response.py, presentation/response/invoice_action_delivery.py, application/port/i_action_events.py, infrastructure/observability/action_events.py, domain/model/authorized_read_context.py, application/port/i_read_authorizer.py, application/service/resolve_read_context.py. Các P1 regression tests giữ nguyên assertions/fixtures. Không sửa A16 sink/B03 Company seam để làm integration PASS.

Không allowlist frontend/B1-S, generic dataProvider/gateway, legacy Copilot/AgentRunner/session/financial modules/hooks, framework files, Docker/infra/site/permissions, migrations, packages, SSOT history. Deploy/lifecycle riêng, không mở rộng bảng bằng “supporting files as needed”.

## 6. Prerequisites, fixtures, tests và rollback

Coding owner đọc actual working tree/hashes, source graph refresh có sẵn (không package install ngầm), impact exact existing/new boundaries; UNKNOWN hoặc partial/truncated phải xử lý trước edit, warn HIGH/CRITICAL. Khi commit được authorize ở task khác phải detect_changes scope all trên đúng checkout; không zero từ wrong index/worktree làm clean check.

Fixture owner đề xuất ERP/Ops + ERP security, independent oracle owner QA; **named owners/site chưa assigned**. Private target cần canonical image có exact source/imports, installed app versions/order/schema/custom hooks/config fingerprints, ordinary users/2companies/site2 boundary, audit sink/key mapping và safe controlled permissions. QA lập permission/gold matrix ngoài tested usecase; fixture provisioning/revocation là mutation chỉ được phép task fixture riêng đã approved lifecycle. Không request hóa đơn thật, không credentials trong chat/evidence; dùng synthetic records do owner chuẩn bị.

**Có thể chạy ngay:** read-only fingerprints/ledger/source metadata; focused P1 guarded tests khi có source drift, không rerun full173 khi vẫn match. **Sau offline code được authorize/build:** pure U02–U04, synthetic transport/sink spies/budget/deadline cases trong [oracle](CHATBOT_P2A_TEST_ORACLE.md), affected P1 references/context/delivery regressions. Synthetic doubles không đóng I01–I04. **Cần private ERP:** actual permissions/masking/query hooks/cache revocation, HTTP cookie/CSRF/status/headers, no writes, collation/hard timeouts/admission và benchmark. **Cần P2-B riêng:** real explicit click/late UI lifecycle/minimum reader/XSS.

Feature flag `InvoiceActionsConfig.enabled` mặc định False; production API có disabled composition nếu target/key/sink/config thiếu. Offline test composition có thể explicit enable synthetic adapters, không fallback production giả. Không bật search/open trên shared image/site. Enablement task riêng chỉ sau independent live oracle PASS + product/security/release approval. Nếu chỉ một capability qualified không auto-enable capability còn lại; current single flag cần giữ both disabled đến cả search/open đạt gate, không thêm per-capability flags ngầm.

Rollback: capability flag off trước, remove/disable new entry composition, retire dedicated key/advance approved policy version để refs/cursors cũ bị reject, UI clears local protected state tại P2-B; independent recheck disabled/no-query behavior. Deployment revert về **known disabled immutable artifact**, không về legacy permissive endpoint. Không schema/data rollback vì không ERP business writes/migrations. In-flight authorized bytes đã trả không thu hồi được; no late protected terminal delivery sau invalidation phải qualification bằng request context/fence. Không reset permissions/cache/Redis shared.

## 7. Final decisions trước coding / trước enablement

1. Chat/Product nhận search/select/minimum Lotus descriptor, không customer_label trong first projection; full form/financial fields cần task contract khác. Chốt P2-A backend/P2-B UI scope và expanded exact allowlist §5.
2. Chat/Security nhận read-family fingerprint + versioned v2 selection/cursor claims, config-version bump policy, equality-expiry semantics; duy trì P1 outcome và complete privacy/denial regression.
3. Chốt numeric test/build profile §4 trước coding; mọi production value vẫn cần release approval. Quyết định cap51 với PARTIAL tại page50/bound/lookahead, hoặc explicit amended52. Chốt max-page exhaustion semantics, body parser16KiB và token2048 v2 feasibility.
4. ERP/Ops chỉ định owner/private target/lifecycle/app lineage/timezone/map và permission fixtures; không chọn shared frontend/ai003-verify. Đây là live prerequisite, không cần real invoices để build offline.
5. Security/Ops chốt key custody/rotation, sink ACL/health/retention/durability requirements; Backend đề xuất safe HTTP failure mapping trong allowlist. Middleware changes ngoài API phải scope approval riêng.
6. Backend/QA qualify field permissions/lazy parent hydration/hook budgets, DB collation/order, enforceable DB+audit deadlines/cancellation/admission. Chốt SLO/SQL/RSS sau baseline, không trước evidence.

Không chờ credentials hoặc real business data để hoàn tất handoff. **Không tự động giao P2-A cho agent/builder, không coding/deploy/enable trong phiên này.**
