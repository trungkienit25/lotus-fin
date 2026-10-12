# LOTUS FIN — P2-A Adversarial Test Oracle

12/10/2026 · Asia/Saigon · **DESIGNED / NOT_RUN** cho P2-A. Không implementation hoặc fixture mutation trong phiên này.

P1 baseline giữ fingerprint-qualified PASS: focused173/173, independent138/138, A16 14/14, B03 8/8; không rerun/không cộng overlap thành unique coverage. [Preflight](CHATBOT_P2A_TARGET_PREFLIGHT.md) phân biệt host source với Docker thiếu P1. [Handoff](CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md) là contract/budget/allowlist cần nhận; outcome authority vẫn P1 MASTER §3–6.

## 1. Hai tầng bằng chứng và fixture ownership

**O = offline contract:** pure typed ports/doubles/synthetic source, no socket/real Frappe/ERP/LLM/legacy imports; real private StringIO/StreamHandler kiểm delivery acknowledgment. Chỉ chứng minh bounds/semantics/denied-before-call. Synthetic HTTP nếu dùng thật transport harness phải label synthetic; direct controller calls không là HTTP tests.

**I = isolated actual ERP:** canonical image/site/ordinary users/custom metadata/hooks và actual HTTP/DB observation. Target hiện BLOCKED, tất cả I **NOT_RUN**. Host mocks không thể đóng I. **U = UI acceptance P2-B** riêng, không nằm trong implementation P2-A.

Owner chưa assigned: ERP/Ops provision approved private site/snapshot + cleanup, ERP security lập roles/UserPermission/DocShare/custom fields/masks/hooks, QA lập gold ledger **độc lập với search/open implementation**. Không tự tạo site hoặc gọi ERPNext test helpers từ test collection. Không dùng shared frontend/ai003-verify, real business invoices, Administrator cho positive actor, không sửa global user; genuine private sessions do fixture owner cấp ngoài report.

Proposed isolated fixture ledger: ordinary `U_allowed`, `U_denied`, `U_select_only`, `U_company_denied`, `U_field_denied`, `U_revocable`; Company A/B; site A/B, approved/unapproved product/connection mappings. Synthetic invoice aliases A-draft/A-submitted/A-cancelled/B-hidden, owner/shared/query-hook-denied/doc-hook-denied, masked required/optional fields, modified/deleted variants. Aliases không là actual IDs hoặc claim fixtures đã tồn tại. `U_denied` phải được tách Company-deny và Sales-Invoice-deny để không che downstream failure bằng gate trước.

Gold ledger định nghĩa exact allowed identities/projection/date/docstatus/version theo fixture metadata do owner xác nhận, không gọi tested adapter để sinh expected rows. Fixture DB may có parent financial data nhưng oracle không export real values; server adapter còn phải đáp ứng source minimization/hydration budgets. Revocation/modification/outage injections là mutation task riêng cần approved lifecycle; không làm trên serving site này.

## 2. Assertion chung

Mọi handler terminal có `contract_version=p1.invoice.v1`, đúng capability, UUID4 server CID, valid UUID4 request_id echo verbatim, headerCID=bodyCID=terminalEventCID, bounded fixed user_message. Healthy sink: đúng1 RESPONSE_DELIVERY attempt=ack=logline; child stages cùng CID không tính thành terminal thứ hai. No secrets/raw actor/SID/tokens/queries/invoice/customer/financial canaries trong logs/errors; authorized projected invoice ID chỉ được xuất trong result/ref đã được phép.

FORBIDDEN/SOURCE_ERROR/TIMEOUT/NOT_AVAILABLE luôn data=null/source=null, không action/ref. OK/PARTIAL yêu cầu source đầy đủ AUTHORIZED_READ, server scope/version/timezone, current context_version và strict projected schema. PARTIAL coverage=INCOMPLETE, page_complete=false, has_more=null, cursor=null, **mọi selection_ref=null**. EMPTY_RESULT chỉ từ completed bounded authorized page. Không total/hidden-count leak.

Counter spies: auth/metadata, source list, exact document permissions, parent authorization hydration, detail reads, SQL, provider/response bytes, queues/provider/report/business writes đếm riêng. “No requested-document lookup” trên ref failure không cấm các metadata/Company checks cần authenticate context; spies phải phân loại, không false PASS bằng counting zero business path do setup lỗi. Explicit denial wins source/stale/version; missing source không thành empty/zero.

Expected status dưới đây giữ current serializer: 502 SOURCE_FAILURE, 422 PROJECTION_UNAVAILABLE. Không lấy candidate alternate HTTP503 trong MASTER làm replacement ngầm. Pre-handler framework rejection có thể raw transport body/CID missing: assert deny + zero protected calls, label transport qualification limitation; không claim typed single-envelope/CID PASS khi thiếu.

## 3. Permission, boundaries, selection và revocation matrix

|ID / tầng|Arrange → action|Expected exact result và probes|
|---|---|---|
|Q01 O/I|U_allowed, Company A/read DocType/read doc+required fields; search fixed date/BOTH|200 OK/RESULTS_FOUND; exact authorized gold rows only, cancelled/B-hidden absent; no amount/child data; complete source/refs. I phải actual ordinary user|
|Q02 O/I|Company allowed nhưng Sales Invoice read denied|403 FORBIDDEN/ACCESS_DENIED; null; source list/detail0. Không chứng minh bằng Company-denied user|
|Q03 O/I|U_select_only có select nhưng không read|403 ACCESS_DENIED trước list; không grant bởi get_list/select path|
|Q04 O/I|Approved mapping nhưng exact Company A permission False|403 COMPANY_DENIED; context/search/open null/no ref/invoice queries0; DocType Company permissive nhưng exact doc denied là separate variant|
|Q05 O/I|Company candidate B ngoài mapping; body company override tại search/open|get_context403 COMPANY_DENIED; extra field search/open422 INVALID_REQUEST; no B invoice lookup/data|
|Q06 O/I|Validly signed selected B doc với A scope (server synthetic adversarial token)|403 ACCESS_DENIED; no projected B read/exposure; document Company phải exact match; không coi forged-MAC-only test là đủ cross-company proof|
|Q07 O/I|List query allowed row, custom document has_permission denies|Candidate bị loại trước exposure/ref; nếu scan completes và không row permitted →200 EMPTY_RESULT; nếu còn unchecked candidates →PARTIAL. Explicit provider FORBIDDEN payload →403 null whole response|
|Q08 O/I|Query hook excludes invoice, exact doc hook would allow|Search không trả excluded row; no hidden count. Không chạy unrestricted second query để “bù”. Open vẫn cần independently qualify selected reference/target policy, không arbitrary ID|
|Q09 O/I|Owner/share fixtures + user link permissions riêng|Exact gold role/owner/share/UserPermission outcomes; denied Company/DocType/predicate gates không bypass bởi share. Hook exception/permission seam absent →503 TARGET_UNQUALIFIED, no success|
|Q10 O/I|Required name/company/posting_date/docstatus/modified predicate/version field denied hoặc masked|422 NOT_AVAILABLE/PROJECTION_UNAVAILABLE trước unsafe filter/exposure; no inference/count/raw masked data; fields.each variant|
|Q11 O/I|Optional customer_name riêng approved rồi denied/masked|Property customer_label absent, không empty string/mask sentinel/raw value; no Customer query. First default profile chưa approved optional nên luôn absent|
|Q12 O/I|User A/session S/site A token gửi từ user B/session khác/site B/product/connection khác|403 ACCESS_DENIED với cryptographic scope mismatch; requested-doc lookup0. Unmapped new target →503 TARGET_UNQUALIFIED trước read; mỗi axis riêng và positive same-scope control|
|Q13 O/I|connection/config/projection policy version đổi, same principal|Verified old token→409 CONTEXT_CHANGED (policy epoch change); no doc read/ref reuse. Same scope stable context→search→open phải succeed; capability đổi không tạo false scope mismatch|
|Q14 O/I|User logout/disabled/missing session binding|401 AUTH_REQUIRED/null/no business query. Actual middleware may reject before handler; no old success/session injected principal|
|Q15 O/I|Search allowed rồi revoke exact document role/share/UserPermission trước open|403 ACCESS_DENIED/null; token vẫn valid không grant. I dùng fresh real request qua workers + cold/warm permission caches; record revocation timestamp|
|Q16 O/I|Search allowed rồi revoke Company permission|403 COMPANY_DENIED trước document read; no stale result replay|
|Q17 O/I|Search allowed rồi revoke predicate/projection/mask permission|422 PROJECTION_UNAVAILABLE/null; không dùng cached raw field/value hay old allowed field list|
|Q18 O/I|Search allowed; source modified; rights vẫn granted|409 STALE_SELECTION, not silently latest DOCUMENT_READY; opaque record_version binding thay đổi|
|Q19 O/I|Source modified và rights revoked cùng lúc|403 ACCESS_DENIED hoặc Company deny ở preceding gate, không409 tiết lộ change; denial precedence|
|Q20 O/I|Previously authorized fixture deleted before open|404 DOCUMENT_UNAVAILABLE/null theo known-authorized scope; inaccessible unrelated alias generic403/no existence probe; raw DB exception không public|
|Q21 O/I|Fresh selected complete result, current rights/version unchanged|200 OK/DOCUMENT_READY; strict minimum document + fixed LOTUS_READ_VIEW/sales-invoice-minimal-v1; invoice ID/record version/source khớp selected alias|
|Q22 O/U|0/1/many complete rows; request no user choice|Search 0 EMPTY_RESULT;1/many selection_required=true. U: không auto open, explicit click trước open. Backend ref validity không là evidence click|
|Q23 O/I|Permission changes trong read/version check; hook cần children/unbounded parent bytes|Không claim atomically authorized snapshot. Guard rejects/target unqualified/partial theo stage, no bypass/full form; I instrument exact reads/cache/race boundary và budgets|

## 4. Reference, filters, cursor, resource/failure matrix

|ID / tầng|Arrange → action|Expected result/probes|
|---|---|---|
|R01 O/I|Tamper payload/signature/key ID; bad base64/parts; wrong purpose context/cursor làm selection|403 ACCESS_DENIED/null; no requested-document lookup. Valid MAC + wrong schema/purpose phải cũng deny, không chỉ bad signature|
|R02 O/I|Expired context/selection/cursor; times before/equal/after expires_at|Authenticated context expiry409 CONTEXT_CHANGED; selection409 STALE_SELECTION; cursor409 STALE_CURSOR; equality reject theo approved P2 decision. Forged token403. No widening/retry|
|R03 O/I|Retired key; future-issued beyond approved skew; unknown wire/binding/schema; v1 selection thiếu record/query|403 ACCESS_DENIED/null; no P2 fallback to incomplete P1 claims. Matching current keys/version positive must PASS|
|R04 O|Decode successful synthetic references/body/log|No raw actor/email/SID/secret; bound scope/version/query/selected doc only approved public/opaque metadata. Cursor last/upper bound không chứa unauthorized IDs; key_id public metadata permitted|
|R05 O/I|Missing/malformed UUID1/nonstring IDs; valid uppercase UUID4|Valid UUID4 giữ nguyên; others422 INVALID_REQUEST/new UUID4; no raw input log. Denied actor/company vẫn deny precedence, không validation thành success|
|R06 O/I|Extra filters/body keys, bool page_size, negative/0/51 limits, wrong invoice_type, unknown docstatus, duplicate JSON keys|422 INVALID_REQUEST trước source query. Raw body duplicate-key rejection phải actual transport test, Pydantic-after-json-only chưa đủ|
|R07 O/I|Date missing pair/partial pair/reversed/future/>365; leap/timezone boundary|Both missing uses approved site-local90-day inclusive default; one missing/invalid422; exact permitted date gold, no clamp/source cutoff inference|
|R08 O/I|Prefix controls/NUL/empty/>128; NFC variants; literal `%`, `_`, quotes; prompt-injection text|Invalid422; valid literals only parameterized prefix matches gold; no arbitrary SQL/method/doctype/URL/scope change. Customer/invoice strings remain data|
|R09 O/I|Body 16KiB and+1 UTF-8 byte; token2048 and+1 chars; encoded claims oversize|Within cap parses if otherwise valid; over body rejected before business parsing/query (413 transport if pre-handler, otherwise approved422); oversized typed token422; invalid authenticated ref403. Logs omit body. Nginx buffer không counted as request cap|
|R10 O/I|Cursor filters/page size/order/window/page-index tampered; cross scope|Authenticated same-scope query mismatch409 STALE_CURSOR; tampered/wrong-scope403; no offset/default changed query|
|R11 O/I|Keyset candidates at0/20/21/50/51/100/101; duplicates/long IDs|Returned≤requested, scan≤100/doc≤51/list≤2; actual collation/window consistency. Duplicate malformed provider row502 INVALID_PROVIDER_RESPONSE; không silently dedupe để giả complete|
|R12 O/I|Need extra authorized lookahead, bound count consumes last doc check|has_more true only proved by authorized extra row. Page50/bound/lookahead exceeding51→200 PARTIAL/COVERAGE_INCOMPLETE/no refs; no unapproved52nd check. Positive lower-page bound control|
|R13 O/I|0 permitted rows nhưng scan/doc/list cap exhausted before completion|200 PARTIAL with items[]/incomplete, no total/no cursor/no selection_ref; không200 EMPTY_RESULT|
|R14 O/I|Completed scope page genuinely no permitted match|200 OK/EMPTY_RESULT; PAGE_COMPLETE, items[],count0,total:null; no hidden/whole-company absence claim; positive containing-match control|
|R15 O/I|Provider incomplete but valid authorized subset; page5 window exhaustion|200 PARTIAL, all refs null/cursor null/has_more null; incomplete source. Open attempts lacking selection_ref422, no executable partial handles|
|R16 O/I|Missing source/required fields, wrong company/date/docstatus, nested business denial, invalid outcome|Source/schema failure502 INVALID_PROVIDER_RESPONSE/null; nested closed FORBIDDEN reason403 ACCESS_DENIED/null, whole response. Không synthetic financial repair|
|R17 O/I|source outage/query exception before valid observation|502 SOURCE_ERROR/SOURCE_FAILURE/null; no EMPTY_RESULT/demo/legacy/LLM fallback; zero retry, sanitized error/CID, terminal once if sink healthy|
|R18 O/I|Total deadline at boundary, slow query/hook/serialization/audit; late completion|504 TIMEOUT/DEADLINE_EXCEEDED/null nếu có safe bounded delivery; no late200/protected bytes. Blocking audit/DB mechanism unsupported →target not qualified, không report mock timer as hard timeout PASS|
|R19 O/I|provider bytes256KiB+1/response bytes64KiB+1|No cap overrun or corrupt JSON truncation. Safely bounded valid subset only may PARTIAL/no refs; otherwise502 INVALID_PROVIDER_RESPONSE/null. Include token bytes/parent auth hydration, no unbounded full invoice load|
|R20 O/I|Auth/metadata call11/doc check52/list call3/open detail read2|Stop before extra call; partial only search after valid observation/no denial; open no protected success. No omission mandatory check to fit cap; raw SQL vs API counts separately|
|R21 O/I|Same request ID duplicate; duplicate signed read; overlapping requests|Request ID không idempotency/approval; each admitted read fresh authorize/budget/new serverCID, valid clientID echoed; no cached auth/result. No write/retry; approved distributed admission behavior tested separately|
|R22 O/U|Old response after company/context/logout/unmount/late request|U discards old generation/context/RID, clears result/ref/reader. Server stale token scope/policy fails; no claim one tab company switch globally invalidates another authorized tab|
|R23 O/I|Actor+site concurrency admission over approved2; multiworker|Bounded admission, no business reads for rejected request; candidate429 safe NOT_AVAILABLE/CAPABILITY_DISABLED mapping +Retry-After only after policy approval. No process-local limiter claimed distributed|

## 5. Required audit, HTTP and no-write matrix

|ID / tầng|Arrange → action|Expected result/probes|
|---|---|---|
|D01 O/I|Healthy required sink across valid search/open, empty/partial/auth/validation/source/timeout terminals|Exactly1 terminal attempt=ack=line, header/body/event IDs/capability/status match; no canaries; failure branches also logged|
|D02 O/I|Missing sink at admission|503 CAPABILITY_DISABLED/null, no business query/signed result refs;0ack, no false delivered event. Missing vs failing sink tested independently|
|D03 O/I|Sink write/flush/short-write fails; logger/handler suppressions|Safe ActionEventDeliveryError,1attempt/0ack; no protected success or retry; HTTP layer maps safe failure without raw exception. Don't require successful delivery to unavailable sink|
|D04 O/I|Multiple effective sinks, one fails; ancestor/root/shared handler concurrency|No acknowledged terminal unless all required sinks succeed; possible physical partial write not relabeled durable delivery; no callbacks/global logging state changed; no duplicate retry|
|D05 O/I|Authenticated cookie POST valid CSRF on exact3 endpoint paths|Actual declared whitelist, same principal/context; single `{message:Outcome}`; status/header/no-store correct; no double.message/legacy body. O direct-call result not HTTP evidence|
|D06 O/I|Guest POST, GET/PUT/DELETE; unwhitelisted alias/arbitrary RPC/run_method|Framework401/403 for Guest, framework405/permission reject for wrong method per actual target; no business query/data/ref. Capture actual transport and missing-envelope/CID limitations; no universal dispatcher|
|D07 O/I|Cookie-auth missing/invalid CSRF; hostile Origin/Referer; missing saved token; allowed_referrer bypass variants|Unsafe request rejected before business query under approved session policy,403 CSRF_OR_ORIGIN_DENIED if typed boundary available. If installed framework early-return accepts prohibited variant: gate FAIL/BLOCKED, not waive by get_list permissions|
|D08 O/I|Client spoof X-Correlation-ID; invalid/mismatched returned body/header/source/context|Server CID generated, trusted internal propagation only; decoded inconsistent response rejected/cleared, never success. Full pre-handler CID chain requires evidence, missingCID limitation not PASS|
|D09 O/I|No request config/key/unknown site/product/map/retired policy|503 TARGET_UNQUALIFIED/null or disabled503 at admission; no impersonation/mock fallback; environment secret presence not proof approved config|
|D10 O/I|Search/select/open successful/failed paths with write/queue/provider spies and DB baseline|ERP business writes0: no insert/save/submit/cancel/db_set/_seen/ViewLog/onload/user-settings/queue/send/provider/report calls. Invoices/children/GL/payment/permissions unchanged after each request; no native form getdoc|
|D11 I|POST transaction/session/framework audit effects under isolated instrumentation|Separate permitted auth-session/cache operational writes + external audit from business/seen/view writes. POST automatic commit không là no-write proof. No Error Log business fallback; fixture lifecycle writes excluded with explicit before/after timing|
|D12 I|Canonical deployed file hashes/import paths/apps/schema/hooks vs gold target; pinned versions|All new/P1 files actually loaded from exact image/site; source/config/map versions align. Host173PASS/bench apps.txt/tag không substitute installed-site or import evidence|
|D13 I|Cold/warm metadata caches, parallel workers, role/user revocation|Denied after approved revocation boundary across workers; stale cached permission not grant. No Redis flush shared; collect actual coherence/TTL/invalidator evidence|
|D14 I|Controlled private DB/source/audit outage +cleanup|Actual typed/transport failures meet oracle, counters bounded; no real/shared outage; owner restores fixture/baseline and closes owned processes/handlers/session keys|

## 6. Execution gates, artifacts và acceptance

**Trong phiên preflight:** chỉ hash/metadata/source/ledger checks đã thực thi. Không Q/R/D implementation tests chạy mới. Matrix có positive và denied cases để tránh false PASS bằng always-disabled endpoint; enable synthetic profile chỉ trong guarded test composition. Từng check cần setup outcome khác ERROR; no setup exception counted security deny.

**Sau coding được authorize:** table-driven O cases trong allowlisted test modules; network/import guards trước app import, private sinks, fake clock/remaining-budget spies; no bytecode/cache/provider endpoints. Chạy affected P1 modules và exact new negatives/positive controls. Chỉ broaden regression khi changed surface/new failure yêu cầu, không lặp full173 vì metadata inspection. Integration module skip unless owner cung cấp approved private target; skip/NOT_RUN không là PASS.

**Trước live integration:** freeze image/import hashes, exact private site/map/config/timezone/app+custom hook versions, fixture oracle ledger, permission baseline, isolated sessions, approved provisioning/revocation/outage/cleanup plan. Performance proposals: cap-boundary cases rồi10k/100k background/concurrency1/5/20, cold/warm caches; representative SQL/RSS/SLO thresholds còn UNSET nên performance qualification NOT_RUN.

Per-case evidence: test ID/tier/nodeid/actual actor alias/scope versions, expected/actual status+reason+safe response keys, counters, CID consistency, sink attempts/acks, exact command/exit/setup result, code/config fingerprints, timing/clock, write baseline/delta and cleanup. Không store raw token/SID/key/query/business rows/error stack; permission ledger và synthetic IDs ở restricted fixture evidence được owner duyệt, public summary dùng aliases.

Independent reviewer đối chiếu oracle không dựa builder PASS. **P2A_OFFLINE_PASS** chỉ O suite cho exact source; **P2A_LIVE_PERMISSION_QUALIFIED=YES** cần Q01–Q21 relevant actual permission cases và D12/D13 actual artifact/cache evidence, không synthetic substitution. Target enablement còn cần full I HTTP/resource/audit/no-write gates và final approval; permission YES riêng không release. Q22/R22 UI cần P2-B task, không report từ P2-A backend là product end-to-end PASS. G10 không tự đóng bởi bất kỳ P2 matrix PASS.

Bất kỳ unauthorized exposure/business write/denial-as-success/unbounded bypass hoặc false audit acknowledgment → FAIL, feature stays disabled. Unknown/unavailable target/hooks/deadline/owner → NOT_RUN/BLOCKED với exact missing prerequisite; không báo SAFE/unused từ zero observation. **Dừng ở oracle/handoff, không tự provisioning hoặc dispatch.**
