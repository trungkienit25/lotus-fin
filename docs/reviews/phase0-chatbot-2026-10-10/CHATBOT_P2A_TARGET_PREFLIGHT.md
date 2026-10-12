# LOTUS FIN — P2-A Target Qualification Preflight

12/10/2026 · Asia/Saigon · Inspection read-only · Không triển khai P2-A.

**P2A_OFFLINE_BUILD_READY = YES**: nền P1 đã được nghiệm thu; đủ thiết kế để chuẩn bị một build offline, capability mặc định tắt. Đây không phải phê duyệt các quyết định sản phẩm/cấu hình còn chờ trong handoff, hoặc quyền bắt đầu coding từ phiên này.

**P2A_TARGET_READY = BLOCKED. P2A_LIVE_PERMISSION_QUALIFIED = NO.** Container đang chạy thiếu toàn bộ 15 file nền P1 đã kiểm tra. Chưa có target riêng được phê duyệt, mapping và ordinary-user fixtures; live quyền/HTTP/CSRF là **NOT_RUN**. G10 vẫn **BLOCKED độc lập**.

## 1. Authority, lineage và evidence reuse

Đã đọc [P1 final independent acceptance](CHATBOT_P1_FINAL_INDEPENDENT_RECHECK.md), [P1 final work-to-chat](CHATBOT_P1_FINAL_WORK_TO_CHAT.md), [P1 MASTER](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md) §3–9, [Action Executor Decision](CHATBOT_ERP_SDK_ACTION_ARCHITECTURE_DECISION.md), hai root implementation reports, AGENTS.md, ADR001 và Security Code V3. MASTER/architecture vẫn mang trạng thái PROPOSED/NOT_FROZEN trong tài liệu lịch sử; preflight không tự đổi trạng thái hoặc ghi đè SSOT. Verdict closure cũ CHANGES_REQUIRED được supersede bởi independent recheck trên source mới, không bị xóa.

Nguồn baseline: `docs/reviews/evidence/chatbot-p1-final-independent-recheck-2026-10-12/`:

|Evidence được giữ lại|Kết quả đã thực thi trước phiên này|Kiểm tra hiện tại|
|---|---|---|
|FOCUSED_RESULTS.json|173/173 PASS, exit 0|Đọc ledger; source fingerprints khớp|
|NEGATIVE_RESULTS.json|138/138 PASS, exit 0, network/business reads 0|Đọc 138 checks; không nhầm với key `cases`|
|A16_CURRENT/A16_CURRENT_QUALIFICATION.json|14/14 PASS, exit 0|Hash adapter giữ nguyên|
|B03_CURRENT/B03_PUBLIC_QUALIFICATION.json|8/8 PASS, exit 0|Hash authorizer giữ nguyên; permission double không phải live ERP|

Đối chiếu `SOURCE_BEFORE.json`: **4.244 manifest entries / 4.215 đường dẫn duy nhất, 0 mismatch**, gồm 29 source/report entries. Không chạy lại suites/probes: **NOT_RERUN — fingerprint-qualified evidence reuse**, không báo đây là PASS mới. Host Python 3.13.7, pytest 9.0.2, Pydantic 2.12.5 vẫn khớp baseline. Không lặp discovery P1 hay so sánh SDK.

`develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; staged rỗng. Tracked dirty: `frontend/src/components/copilot/LotusCopilotDrawer.tsx`, `frontend/src/pages/copilot/components/VercelChatPanel.tsx`; nhiều file P1/evidence/docs chưa tracked. SHA-256 tracked binary diff: `09344d31c5b694e62eb399cc6461a6388ea77c330fbf1943b127b4f3c56fd3eb`; staged diff: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. HEAD không đủ định danh artifact.

## 2. Host source fingerprints

Các đường dẫn dưới `lotus_fin/lotus_fin/`. Bảng là SHA-256 bytes hiện tại; toàn bộ code/test fingerprints còn lại được đối chiếu với manifest independent phía trên.

|File|SHA-256 host|Backend Docker|
|---|---|---|
|api/invoice_actions_api.py|90ea0be717f55100d53f71fc308c166f4b0955c932bc57d68342b76dfdc1f23f|MISSING|
|application/port/i_action_events.py|9573fd752755e463ecb0cf24d9e6e01941865561c2e8dbd744b633950423876e|MISSING|
|application/port/i_read_authorizer.py|81114c6bd2e81500e779f10f2b4af40607b97334043002f6cd33b167513a1583|MISSING|
|application/service/resolve_read_context.py|0def479f8c61488958128e2dd80cda3822ffa8bb0db2bba9457b97bcde2568a1|MISSING|
|domain/model/authorized_read_context.py|495b2ca9c91a4b077743d5a277d7f23a919c56d8be91cbd16e6ba39b6b21cd70|MISSING|
|domain/schema/action_outcome.py|bf90ca6b85743b7152a9b749528240c9c48d48a39e4682c18e674adf78fc2bb9|MISSING|
|infrastructure/config/invoice_actions_config.py|ae56b57f9123fa449a7c07da1a96ceca04a961f7c659404d5f6c61fe4a32ac91|MISSING|
|infrastructure/observability/action_events.py|990ee5243e2f50264b5664d2360e60fa0eb422547bd93412f7f1ee3ee045b198|MISSING|
|infrastructure/security/action_reference_codec.py|9270cd467ca795185db8b5f5c8df7fa0158d977e32aa78b8fca54cbfaf2bd009|MISSING|
|infrastructure/security/frappe_invoice_authorizer.py|84c6d1dee0075abbfc9c3326bf5e3faaf5caaa19422f01ef118543659b5e22f9|MISSING|
|presentation/controller/invoice_actions_controller.py|bbfe06b870d7b5f67621f89f4101e128d8ed6b2190595fef7f9ed51a5a603d3a|MISSING|
|presentation/dto/action_outcome.py|2c89b0c5ea422972cd6855230bb99c594630134956d5e901b54cd25e5833796f|MISSING|
|presentation/dto/invoice_action_request.py|2e3dc6263427582df068894664812481325f5b4345e0fefc9a02ebc25933278c|MISSING|
|presentation/response/action_response.py|599f7afd0e0a1dd79671f0796a87cdd16e26fb2d3ad66a670889ae01a42521bb|MISSING|
|presentation/response/invoice_action_delivery.py|0bfdd70dfb485b3f415bcf3da54b80d531b41f0e35a0f5cdd4d05cd131ed8c84|MISSING|

MASTER SHA-256 `751ed14eff6dec6e6aa832150ee022551b56a43b23dc5699839e747cd9e9e640`; architecture decision `e8a5806517065906e0892c94acb9ee1ff8a645d64feb6f45bf60379ddcbfe5de`. `hooks.py` host/container khớp `8cf19213cfea71a16f40317d514fe0f1d1bd81142ad5851fe2826c20ca773ec7`; một file khớp không khắc phục 15 file thiếu.

## 3. Serving environment đã quan sát

Đọc Docker metadata và source filesystem bằng Python stdin `-B`, `PYTHONDONTWRITEBYTECODE=1`; không import Frappe/ERPNext/Lotus, không init/connect site, không DB/HTTP request. Lệnh Docker đầu trong sandbox bị permission denied; read-only escalation được chấp nhận và các lần inspection sau exit 0. Không bị automatic approval rejection.

|Hạng mục|Quan sát actual|Giới hạn|
|---|---|---|
|Backend/frontend|`frappe_docker-backend-1`, `frappe_docker-frontend-1`; frontend port 8080|Tên/tag không là canonical release approval|
|Image|`lotus-fin:ai003-local`; ID/digest `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`; created 2026-10-03T15:45:15.535651656Z|Không rebuild/restart/replace|
|Code mount|Backend chỉ mounts sites/logs volumes; không bind host app source|Sửa host không tự deploy vào image|
|Topology|Queue long/short, scheduler, websocket cùng tag; redis cache/queue 6.2-alpine; DB tag mariadb:11.8|Chỉ tags/status, không claim phiên bản DB thực thi hoặc concurrency PASS|
|Framework source version|Frappe 16.34.0; ERPNext 16.35.0; Lotus 0.0.1|Đọc `__version__` từ file, không gọi runtime import|
|Python backend|3.14.7; Pydantic 2.12.5, Werkzeug 3.1.6, PyMySQL 1.1.2|Khác host Python 3.13.7; cần compatibility tests trên build mới|
|Bench app inventory|sites/apps.txt: erpnext, frappe, lotus_fin|Không chứng minh apps đã install trong DB của từng site|
|Version manifest|sites/apps.json có frappe/erpnext, thiếu lotus_fin; ERPNext commit `12cd563fb9a79731f75ae2a45b1446a0a2dd9e74`; Frappe commit null|Lineage/mapping site-app-product còn PARTIAL|
|Site folders|`frontend`, `ai003-verify.localhost`|Không chọn các site này làm P2 fixture|
|Nginx routing|Host default → frontend; Host khớp `^ai003-verify` → ai003-verify.localhost; proxy đặt X-Frappe-Site-Name|Đã đọc config; runtime routing/header isolation test NOT_RUN|
|Identity map|Chưa có approved product/site/connection/version/company mapping P2|Lotus product và ERP site là hai danh tính khác nhau|
|Current Frappe principal|NOT_RESOLVED / NOT_RUN|Shell/container user không là HTTP actor; không có authorized ordinary-user session cho fixture|
|Live session/permission cache|NOT_RUN|Không đọc cookie/SID/token hoặc giả user; không đổi global user|

Không có initialized P2 target trong phiên này. P1 policy không cho dùng shared `frontend` hoặc tái sử dụng `ai003-verify` làm acceptance site. Cần owner chỉ định private site/snapshot, exact artifact và lifecycle được duyệt ở task riêng.

## 4. APIs/quyền thật từ source đã cài

File runtime dưới `/home/frappe/frappe-bench/apps/frappe/frappe/`. Đây là **STATIC_VERIFIED**, không phải live permission PASS.

|Source/API|Quan sát|Điều kiện adapter P2-A|
|---|---|---|
|`__init__.py:1360` get_list|Delegates `model.qb_query.DatabaseQuery.execute`|Dùng fixed Sales Invoice + explicit fields/company/typed filters/limit; không get_all/direct QB mặc định|
|`model/qb_query.py:26,195` execute|ignore_permissions mặc định False, query kwargs chuyển sang `frappe.qb.get_query`; có option save_user_settings|Không bật save_user_settings/comments/children/joins/update; calls/SQL đếm riêng|
|`database/query.py:215` get_query|Direct QB mặc định ignore_permissions=True|Không thay get_list bằng unrestricted query builder|
|`database/query.py:1619,1665`|Query hooks/server-script conditions; distinction select-only|Chặn select-only bằng DocType read gate độc lập trước query|
|`permissions.py:81,138` has_permission|Exact doc string sử dụng get_lazy_doc; rồi get_doc_permissions|Exact Company read và Sales Invoice read riêng; boolean True; seam absent/error không cho phép|
|`permissions.py:229,483`|Role/if_owner/user permission/share/controller hooks có semantics riêng; hooks có thể deny|Một list result chưa chứng minh exact doc hook cho phép read|
|`model/document.py:165,2137` lazy doc|Lazy child tables, nhưng parent loader SELECT *; child getter/hook có thể tải thêm|Không giả partial dict là đầy đủ permission doc; qualifying lazy path, parent bytes/metadata/SQL phải tính. Full parent auth load không được gọi là minimal projection read|
|`model/__init__.py:218` get_permitted_fields|Field-level permitted projection API|Kiểm required fields và predicate fields trước query; role/field/mask policy mới nhất|
|`query_builder/utils.py:82,148`|Query results masking; `document.py:957` cũng loại permlevel/mask|Required denied/masked → PROJECTION_UNAVAILABLE; optional customer_name bị loại; không suy ra quyền từ read_only/hidden|
|`desk/form/load.py:47,53,416`|Field permission application, add_seen, run onload|Không native getdoc/Form open; fixed Lotus read descriptor|

Không dùng `get_all`, `ignore_permissions`, raw SQL business query, user impersonation hoặc unrestricted RPC trong P2 implementation. Framework source bên trong có SQL/get_all không là cho phép adapter gọi chúng. Parent-row permission hydration/extra authorization metadata chỉ được dùng sau target review, với bounds riêng; nếu custom hook cần unbounded children/PII/financial hydration không thể đáp ứng budget, target/capability giữ BLOCKED. Chưa chứng minh cách tối thiểu đó chạy được trên target.

Required permission gates: (1) authenticated actor/current session; (2) server site/product/connection/company mapping; (3) exact Company read; (4) Sales Invoice DocType **read**, không select; (5) effective allowed filter/projection fields và masking; (6) list/query conditions; (7) exact document read/company match cho từng result trước exposure; (8) fresh gates lại tại open, rồi version check. Company allowlist không là quyền người dùng. Share/owner grant không được vượt policy Company/DocType/projection đã chốt cho pilot.

Standard ERPNext `sales_invoice.json` có Accounts Manager/Accounts User read và permlevel-1 rules; các field company/posting_date/customer_name được đọc từ schema file. Đây không phải roles/perms của người dùng hay Custom DocPerm/Property Setter trong site DB. Company metadata live, User Permission, DocShare, custom fields/masks, enabled/disabled user, server scripts, installed-app hook order và cache revocation coherence đều **NOT_RUN**.

Đọc hooks của ba app trên disk: không có Sales Invoice/Company-specific `has_permission`/`permission_query_conditions` declarations trong mappings đã đọc. Lotus có Sales Invoice on_submit và Payment Entry on_submit; không đọc/business-trigger chúng. Không kết luận “không custom hooks”: DB Server Script, site app installation/order và dynamic extensions chưa được inspect bằng live metadata session.

## 5. POST/Guest/CSRF/wrapping và audit/key

Host API đã declare `allow_guest=False, methods=[POST]`; hiện cả ba exports chỉ gọi disabled helper, **chưa compose controller/usecases/events/config**. Controller search/open cũng unconditional CAPABILITY_DISABLED. Offline P1 PASS không chứng minh endpoint thật đang phục vụ.

`get_context` controller hiện thiếu `default_posting_from/default_posting_to` và gán `expires_at` từ request deadline, khác token TTL. P2 wiring phải trả date defaults đã approved và actual context-token expiry; không dùng deadline 5s như reference expiry 300s. Đây là contract-completion gap khi mở P2, không đổi nghiệm thu foundation disabled P1.

Source Frappe whitelist `__init__.py:439`, handler `handler.py:46,65`, RPC `api/v1.py:35`: whitelist/method check trước handler; handler đặt return value vào `frappe.response[message]`. Host helper hiện trả `{message: body}`: khi nối thẳng sẽ tạo **double message**, là integration gap cần sửa trong allowlist. `utils/response.py:146` dùng `http_status_code`; `app.py:307` dùng `frappe.local.response_headers`. Host helper dùng `frappe.response.status_code`/`frappe.response.headers` rồi swallow exceptions: **chưa chứng minh HTTP status/header**. P2 API phải return bare Outcome một lần, set `http_status_code`/response_headers theo source này, nối required delivery boundary và không nuốt audit failure.

`auth.py:81` kiểm CSRF của unsafe requests nhưng có early-return cho ignore_csrf, session/token missing hoặc allowed referrer. Common/site config đã đọc không có ignore_csrf/allow_cors và giá trị flag effective từ các file đó là false; **không chứng minh toàn bộ CSRF/origin protection**. Không inspect cookie/session, allowed_referrers cache, API-key principal hay middleware behavior live. Cần cookie-auth POST tests với valid/missing/invalid token, hostile Origin/Referer, no token/no session và exact reject-before-query counters. Không đổi framework security policy hoặc dùng API key để né pilot session contract.

Config presence inspection chỉ kiểm tên `invoice_actions`, `invoice_actions_enabled`, `invoice_actions_signing_key_id`, `invoice_actions_signing_secret`, `invoice_actions_connections` trong common/site JSON; đều absent. Các tên là probe candidates, **chưa có production config loader được nối**, không suy ra mọi environment/secret-store đều không có key. Không in secrets, environment, SID hay credentials. Key custody/rotation/approved map loader: **NOT_VERIFIED**.

P1 `SafeStructuredActionEvents` yêu cầu mọi effective non-Null sink, INFO policy, full stream write count + normal flush; acknowledgment không là disk persistence/durable audit guarantee. Missing sink không admission; failing sink ném safe ActionEventDeliveryError, 0 acknowledgment; không retry/ERP Error Log fallback. Healthy terminal boundary đúng 1 event/CID/RID. Production logger binding, restricted sink/ACL, retention/rotation/health/admission và HTTP safe exception mapping chưa được nối/qualified; dedicated key tối thiểu config length 32 chars không chứng minh entropy/custody. TTL/rotation/log retention cần approval riêng.

## 6. GitNexus và giới hạn thay đổi

Skill đã áp dụng: `.claude/skills/gitnexus-exploring/SKILL.md`, `.claude/skills/gitnexus-impact-analysis/SKILL.md`, guide. Repo bound **lotus-fin / E:/lotus-fin**, không worktree khác. Cached CLI 1.6.12 dùng trực tiếp, không install. Index `316c5bd32197b35f01873f8ae463051f88b37ee5`, 61 commits behind HEAD. List trả 1 repo; stats actual khác banner AGENTS lịch sử: 8.086 files/141.018 symbols/160.525 edges/558 flows.

Concept query trả các skill/evidence flows không liên quan P1. Context InvoiceActionsController not found; upstream impacts InvoiceActionsController, FrappeInvoiceAuthorizer, ActionReferenceCodec, InvoiceActionsConfig exit 1, `risk=UNKNOWN`, impactedCount null. **Callers/processes không resolvable, không phải zero affected hoặc LOW.** Bounded text confirmation sau graph: controller → resolver/codec/config/InvoiceActionDelivery; resolver → authorizer port; delivery → serializer/events; API disabled helper là đường riêng, không caller controller. Các P1 tests gọi trực tiếp foundation.

Wrapper help bị pnpm EPERM; direct cached CLI hoạt động. Direct `status` không hoàn tất trong phiên, đã dừng process riêng; index freshness lấy từ meta, list, query staleness và git count. Không analyze/reindex vì phiên read-only. Không application edit/commit; UNKNOWN không dùng để cấp quyền sửa. Task coding sau phải refresh bằng runner có sẵn, impact lại exact symbols/files, cảnh báo HIGH/CRITICAL nếu có; không substitute text search cho graph edit gate. Không có graph HIGH/CRITICAL được báo trong lần này; security significance vẫn cần review độc lập. Không commit nên detect-changes pre-commit không áp dụng phiên này.

## 7. Blockers và điều kiện đóng

|ID|Blocker được xác định|Owner cần nhận / bằng chứng để đóng|
|---|---|---|
|T01|Serving image thiếu 15 P1 files; Python host/runtime khác|Release/Backend owner: build immutable artifact trong task riêng, import/source hashes và runtime regression của exact image|
|T02|Chưa approved private site/lifecycle; apps.json không có Lotus lineage; site DB installed apps unknown|ERP/Ops owner: named private snapshot/site, apps/schema/hooks/config versions, baseline/cleanup; không dùng hai site đang có|
|T03|Chưa principal/session, Company/doc/list/field/mask/custom rights fixtures|ERP security owner + independent QA: ordinary users, permissions ledger độc lập, I01/I02 từ oracle|
|T04|Chưa server identity/company mapping, key custody và version policy|Product/security + Backend owner: approved opaque map, loader, key lifecycle không lộ secret|
|T05|Required audit production binding/HTTP failure mapping chưa qualified|Security/Ops + Backend owner: healthy/outage/suppression/ACL/retention và exactly-one event acceptance|
|T06|HTTP composition, wrapper/status/header/CSRF chưa qualified|Backend + independent QA: exact deployed POST/Guest/GET/token/origin/CID tests; no request performed hiện tại|
|T07|Permission lazy hydration/field policy, collation/deadline/admission/SQL budgets chưa qualified|ERP/Backend + QA: actual instrumented resource/no-write/revocation tests trong site riêng|
|T08|GitNexus thiếu current symbols, exact future patch chưa impact được|Coding owner: refresh sẵn có + complete fresh impact trước source edit; không install tự động|

Không gán owner danh tính cụ thể khi người dùng chưa chỉ định. T01–T07 chặn target/live enablement; T08 là edit prerequisite, không mở lại offline acceptance P1.

## 8. Phạm vi đã thực thi và điểm dừng

Đã chạy: read-only git inventory/diff/hash/ledger checks; cached graph list/query/context/impact; Docker list/image/mount metadata; Python AST/source/version/config-presence reads trên backend; nginx file read. Không chạy ERP HTTP/DB request, fixture/test initialization, business read/write, permission revocation, outage injection, package install, source edits, commit/push/deploy/restart. Python inspection processes đã exit; không bytecode/cache hoặc helper files được tạo. Không đọc business invoice hay request credentials.

Chỉ tạo bốn tài liệu P2-A. [Test oracle](CHATBOT_P2A_TEST_ORACLE.md) là DESIGNED/NOT_RUN cho P2; [handoff](CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md) ghi contract/allowlist và approval-pending values; [one-page packet](CHATBOT_P2A_WORK_TO_CHAT.md) cho Chat. **Dừng ở target blockers + implementation contract. Không dispatch implementation.**
