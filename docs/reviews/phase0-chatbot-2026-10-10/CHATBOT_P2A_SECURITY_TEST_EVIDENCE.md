# LOTUS FIN — P2-A Security Test Evidence

12/10/2026 · Asia/Saigon · Builder/self-verification, **không independent acceptance** của correction.

Gate1 **P2A_OFFLINE_APPLICATION_PASS**, chỉ typed core/synthetic port/delivery. Gate2 **P2A_TARGET_INTEGRATION=BLOCKED**; **P2A_LIVE_PERMISSION=NOT_RUN**. Không ERP qualification hoặc deployment thực thi. Report/limitations/allowlist: [Backend Integration Report](CHATBOT_P2A_BACKEND_INTEGRATION_REPORT.md).

## 1. Reproduction và scope

Evidence root `docs/reviews/evidence/chatbot-p2a-backend-integration-2026-10-12/`. Runners lưu dưới `*_REPRODUCTION.txt` là reviewed Python stdin evidence, không ad-hoc application scripts. Execute từ `E:/lotus-fin`, installed Python3.13.7/pytest9.0.2/Pydantic2.12.5, không install:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
Get-Content -Raw docs/reviews/evidence/chatbot-p2a-backend-integration-2026-10-12/APPLICATION_GREEN_REPRODUCTION.txt | C:/Python313/python.exe -B -
```

Tương tự thay tên runner trong matrix. Exact pytest args nằm trong mỗi RESULTS.json: `pytest.main(['-p','no:cacheprovider','--noconftest','-v', ...explicit test module paths...], plugins=[Recorder()])`. Guards trước app import chặn socket connect/connect_ex/bind/getaddrinfo và real Frappe/ERP/LLM/legacy imports. Module identity ledger chứa actual imported file paths/hashes, không chạy file harness hoặc conftest/site setup. Stdout đầy đủ lưu trước khi terminal hiển thị tail; tail truncation không mất raw evidence.

## 2. Executed runs và RED→GREEN

|Runner prefix / raw ledger|PASS|FAIL|Exit|Ý nghĩa|
|---|---:|---:|---:|---|
|RED_REPRODUCTION / RED_RESULTS|2|31|1|Reproduced current application boundary defects, không setup ERROR|
|GREEN_REPRODUCTION / GREEN_RESULTS|33|0|0|Same primary33checks after correction|
|EXPANDED_REPRODUCTION / EXPANDED_RESULTS|92|4|1|3missing authenticated claims bugs +1privacy-canary false positive|
|EXPANDED_GREEN_REPRODUCTION / EXPANDED_GREEN_RESULTS|96|0|0|Strict required claims; unique actor privacy canary; original19retained|
|DENIAL_RED_REPRODUCTION / DENIAL_RED_RESULTS|24|1|1|Known ACCESS_DENIED reason trong outerOK trả sai classification|
|DENIAL_GREEN_REPRODUCTION / DENIAL_GREEN_RESULTS|25|0|0|Recognized denial wins, null source/data|
|FINAL_REPRODUCTION / FINAL_RESULTS|270|0|0|173P1 +19P2original +78new then-current cases|
|DTO_RED_REPRODUCTION / DTO_RED_RESULTS|2|3|1|Missing minimum DTO factory +open delivery route mismatch; private search delivery controls PASS|
|APPLICATION_FINAL_REPRODUCTION / APPLICATION_FINAL_RESULTS|102|0|0|After minimum Open DTO correction; P2-only affected suite|
|BYTES_RED_REPRODUCTION / BYTES_RED_RESULTS|25|1|1|Response budget counts data/source but misses envelope|
|APPLICATION_GREEN_REPRODUCTION / APPLICATION_GREEN_RESULTS|103|0|0|Latest exact affected P2 source, full envelope guard|

`DTO_WIRE_RED.json` lưu direct construction/serialization của actual old DTO: outer `document,authorized_company_label,navigation`, nested redundant company_label/navigation; direct expected MASTER key assertion exit1. Đây là bounded wire defect riêng, không lấy missing-method error làm bằng chứng duy nhất.

Không cộng runs overlapping. Latest P2 suite103=19original+84new (security33, budget26, reference20, delivery5). P1 suite173 được chạy trong270run; không sửa P1 protected semantics sau đó nên reuse173regression, không claim một fresh276-case execution. Tổng distinct coverage từ relevant runs276. Bộ138independent/P1 A16 14/B03 8 dedicated historical probes không rerun; qualified reuse khi respective source không đổi, không cộng unique coverage và không coi actual ERP permission PASS.

Expanded privacy false positive: actor fixture `synthetic` trùng public metadata key_id`synthetic-key`. Đổi riêng actor ở privacy test thành unique email canary, giữ “raw actor/SID/key absent” assertions. Không sửa crypto để conceal legitimate key_id. Initial failure/raw ledger bảo tồn. Một diagnostic manifest read ban đầu dùng host default encoding bị UnicodeDecodeError; chạy lại explicit UTF-8 thành công, không application test failure. Apply-patch delete/add same target bị tool reject trước mutation; corrective patches đã áp dụng, không có partial source edit từ lần đó.

## 3. Oracle/observation mapping

|Security area|Actually executed offline checks|Live classification|
|---|---|---|
|Provider/source|Missing/foreign scope/source, null page, invalid status/reason, count/duplicate/over-page/malformed rows, projected dates/docstatus/filter, exact doc/company/source version, fixed descriptor|ERP source/field-mask/query hooks NOT_RUN|
|Denial precedence|Failure null source/data; recognized denial wins outerOK; revoked private port grant wins stale/retained doc; exception/timeout typed safe result|Actual ordinary roles/UserPermission/DocShare/cache/revocation NOT_RUN|
|Complete/PARTIAL|Incomplete outerOK normalized PARTIAL, coverageINCOMPLETE, no ref/cursor/has_more; complete empty selection_required false; page5 window limit no actionable handle|Actual collation/keyset/window/lookahead/authorized bound NOT_RUN|
|References|MAC/purpose/retired key/equality expiry; separate scope axes with expiry; contract/query/record binding; authenticated missing/defaulted/duplicate claims; canonical wire; forged/stale query/page cursor denied before port|Actual cross-site/current session/config lineage NOT_RUN|
|Input|Strict ints/no bool, NFC/controls/length/closed filter/date pair, JSON ISO dates/enum, site-local normalized defaults/future-date validation|Actual Frappe request decoder/duplicate body keys/16KiB enforcement NOT_RUN|
|Budgets|Exact cap/+1 per list/doc/meta/scan/provider bytes/response bytes/detail; negative/bool/float/string counts reject; absent/expired deadline no port; monotonic equality; late port success dropped; full-envelope conservativeUTF8 bytes|Physical SQL/I/O accounting, DB/audit interrupt/cold-warm/concurrency/admission NOT_RUN|
|Audit/CID|Core→DTO→ActionOutcome→existing InvoiceActionDelivery +private real StreamHandler:1ack/1line/CID header/body/RID; write failure throws accepted safe audit error/0ack; handlers cleaned|Production sink binding/retention/ACL/durable persistence/actualHTTP header/wrapper/CSRF NOT_RUN|
|No writes|No real ERP import/network/source business reads; port doubles only. Static no application/domain Frappe imports, immutable source scope; endpoints kept disabled|ERP DB business/seen/view/onload/queue before-after proof NOT_RUN|

Offline role/document permission double proves protocol re-invocation/null-data deny, không quyền Frappe. Logical budget class không preempt blocking call; actual source adapter phải consume every I/O và enforce target deadlines. Source row observation đưa qua trusted authorized read port; application validation không tự chứng minh list/document/field rights. No unrestricted full-document hydration/SQL test được thực thi vì actual adapter chưa được phép triển khai.

## 4. Source/runtime/graph identity

`SOURCE_BEFORE.json`:747protected current file hashes +HEAD/branch/staged/tracked diff. `SOURCE_AFTER_CODE.json`:17 touched code/test hashes/lines và final snapshots `source/`; all<200, max197. `STATIC_AUDIT.json`: compile/import checks, preserved source boundaries. `P1_CODEC_AST_PRESERVATION.json`: exact original5v1methods (`__init__`, actor/session derive, sign_reference, verify_reference) identical AST. Both original P2 test modules retain assertions/raises; fixture diffs và pre-edit content lưu riêng. Full untracked before-content diff không available cho mọi service; không dùng git diff empty như no-change proof.

API/controller/A16/Company authorizer/config/P1 domain/DTO/serializer/delivery/finance/frontend source không sửa; tracked binary diff và staged hash trước/sau không đổi. Existing test callbacks/private sinks cleanup; no script/bytecode/cache installed. Inspection source subprocesses exit; completed GitNexus retry exit0.

`RUNTIME_READONLY.json`: backend Python3.14.7, source Frappe16.34.0/ERPNext16.35.0/Lotus0.0.1, same old image digest `ed6e02f…`, all10inspected integration source paths missing; bench apps/site folders chỉ metadata. Docker exec dùng Python`-B`/no bytecode để đọc file/AST/version, không import site/app, không DB/HTTP/secret read. Actual principal/session/installed-site apps và config mapping chưa established.

Graph cached1.6.12: pre-edit UNKNOWN on old index+source confirmation. Initial full refresh worker crash; pool1/ready30s retry successful. Fresh graph impacts/search/open LOW, filtersMEDIUM, exactuidcodecLOW; DTOUNKNOWN cần source confirmation. `GRAPH_*` raw artifacts gồm context, exactuid disambiguation và detect_changes. Whole-tree detect_changesHIGH liên quan pre-existing frontend9symbols/6flows, không modified bởi task. Process enumeration có truncation và graph refresh trước final helper/DTO changes; untracked backend không nằm trong git-only diff report. Không tuyên bố final graph all-clear hoặc commit gate PASS; không commit.

## 5. Gate2 execution plan và NOT_RUN prerequisites

1. Named ERP/Ops owner approve private site/snapshot, exact immutable P1/P2 image/app/import/schema/custom-hook/connection-map versions và provision/cleanup lifecycle; không dùng shared frontend/ai003-verify/judge data.
2. ERP security owner chuẩn bị allowed ordinary user, denied ordinary user/Company/DocType/select-only/exact doc, CompanyA/B/siteA/B, owner/share/link/query hooks, field denied/masked, revocable user/role. Independent QA lập gold ledger ngoài tested service; credentials/session keys không export.
3. Backend qualify installed get_list/qb permission APIs, exact document lazy auth/full-parent cost, field/mask/projection/filters and no onload/seen/view mutations. Không get_all/ignore_permissions/Admin/set_user/arbitrary SQL/RPC; source adapter only after target authorization.
4. Actual HTTP sessions test authenticated POST/Guest/GET/CSRF/origin/CID/status/single message/no-store/pre-handler failures; source/required audit outages và actual cancellation/budgets. Instrument SQL versus API counts/bytes/deadlines/cache revocation cross workers.
5. Before/after private fixture invoices/children/GL/payment/permissions/seen/ViewLog/queues unchanged during read requests; provisioning/revocation/outage lifecycle mutations tách scope và timestamp. Owner restores baseline/closes owned resources. Only independent real qualification +release approval permits enablement.

Tất cả5steps hiện **NOT_RUN**, Gate2 **BLOCKED** bởi missing target/source/approval/fixtures. Không tạo private ERP site, không request invoices thật, không deployment/permissions changes. Independent acceptance sau correction và G10 closure là separate work; không tự dispatch.
