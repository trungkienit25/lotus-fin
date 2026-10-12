# LOTUS FIN — P2-A Backend Integration Report

12/10/2026 · Asia/Saigon · Direct targeted correction + self-verification.

**P2A_OFFLINE_APPLICATION_PASS — self-verified trong phạm vi typed offline core.**

**P2A_TARGET_INTEGRATION = BLOCKED. P2A_LIVE_PERMISSION = NOT_RUN.** Không có canonical private target/fixtures được approve; image hiện tại chưa chứa code host. Không triển khai/enable ERP adapter, không nối production invoice reads. Search/open API và controller vẫn unconditional disabled. G10 vẫn independently BLOCKED; không dispatch P2-B.

Đây không phải independent acceptance của mã do tôi vừa sửa. Inspection trước sửa được thực hiện trực tiếp trên source Antigravity; kết quả sau sửa là builder/self-audit. Offline PASS không chứng minh quyền Company/document/field, revocation, CSRF, SQL bounds hay hard cancellation trên ERP thật.

## 1. Authority và actual source

Đã đối chiếu [Target Preflight](CHATBOT_P2A_TARGET_PREFLIGHT.md), [Test Oracle](CHATBOT_P2A_TEST_ORACLE.md), [Implementation Handoff](CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md), root `CHATBOT_P2A_OFFLINE_IMPLEMENTATION_AND_EVIDENCE.md`, P1 MASTER/final independent acceptance, AGENTS, ADR001/Security Code V3. Builder report nằm ở workspace root, không phải review directory. Historical builder report và preflight/oracle/handoff được giữ nguyên; packet hiện tại được cập nhật, bản cũ lưu trong evidence.

Branch `develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; staged rỗng. Source P1/P2-A untracked; hai tracked dirty Panel/Drawer có trước không đổi. Before inventory:747 fingerprints. [SOURCE_BEFORE.json](../evidence/chatbot-p2a-backend-integration-2026-10-12/SOURCE_BEFORE.json) và [SOURCE_AFTER_CODE.json](../evidence/chatbot-p2a-backend-integration-2026-10-12/SOURCE_AFTER_CODE.json) khóa chính xác file bytes. Không gọi HEAD là release artifact. Host Python `C:/Python313/python.exe`3.13.7, pytest9.0.2, Pydantic2.12.5; không install.

## 2. Findings được tái hiện và trực tiếp sửa

|Finding|Trước sửa / probe|Correction và scope|
|---|---|---|
|F2-01 Provider trust/denial|Search nhận missing/foreign source, null page, count/duplicate/over-page rows, invalid reason; incomplete OK vẫn OK. Open failure giữ source; wrong doc/company/navigation/partial source vẫn được chấp nhận.|Closed typed outcome/reason, source scope/mode/version/timezone match, revalidation/count/filter/projection, null data/source mọi terminal failure. Recognized denial thắng outer success; incomplete thành PARTIAL/INCOMPLETE không ref/cursor; không sửa P1 enum.|
|F2-02 Exact selected observation|Open chỉ so record_version, không exact invoice/company; exception có thể thoát raw usecase.|MAC/binding trước lookup; fresh port invocation mỗi lần open, exact returned identity/company + minimum descriptor, current version, safe error/timeout classification; denied wins stale. Permission implementation thật vẫn chưa có.|
|F2-03 Reference/query/cursor|Selection thiếu query/contract; forged cursor forwarded port; v2 signed claims thiếu defaulted purpose/binding/doc_type được repair.|Purpose-specific strict v2 bindings/query digest/window/page/size; authenticated duplicate/missing/noncanonical claims reject; scope deny trước expiry; equality-expiry reject. Không dùng v1 token làm P2 selection.|
|F2-04 Input/deadline/resource|True/float/string page size, JSON date/enum decoding, NFC, expired context, late return và port failures không đủ guarded. Response count bỏ envelope.|Strict DTO/filter normalization/site-local90days/future rejection; request budget được port nhận và phải consume trước mỗi I/O. Counts/full envelope bytes, logical caps, deadline trước/sau call. Conservative maximum UTF-8 message reservation; không claim hard DB/audit interrupt.|
|F2-05 Clean architecture/ADR|Application imports infrastructure codec; codec230lines, vượt ADR001.|Application-owned reference Protocol; cohesive v2 codec + shared validator + budget value object. P1 v1 methods giữ nguyên AST; tất cả17 touched code/test files<200lines.|
|F2-06 Minimum open DTO|Existing wire outer `authorized_company_label`, nested document chứa company_label/navigation lần nữa; không khớp MASTER.|Exact document five-field projection, outer company_label + fixed navigation; reject extras; typed factory from validated read observation. Private core→DTO→required-stream checks.|

Primary RED:31fail/2positive controls; GREEN33/33. Expanded authenticated malformed-claims review thêm3real failures; một privacy check false positive do actor `synthetic` trùng public key-id `synthetic-key`, đổi riêng actor canary ở test để không đổi requirement. Exact denial precedence RED1→GREEN; DTO wire assertion RED và factory/delivery RED3→GREEN; full-envelope byte assertion RED1→GREEN. Raw outputs được giữ, không sửa failing assertions để làm PASS.

## 3. Exact modified/new implementation files

Paths dưới `lotus_fin/lotus_fin/`; exact before/after SHA-256 và source snapshots nằm trong SOURCE_AFTER_CODE.json và evidence `source/`. [Allowlist](../evidence/chatbot-p2a-backend-integration-2026-10-12/ALLOWLIST.md) ghi amendments cụ thể, không “supporting files as needed”.

|Kind|Path|
|---|---|
|EDIT|application/service/search_invoices.py|
|EDIT|application/service/open_authorized_invoice.py|
|EDIT|application/port/i_authorized_invoice_read.py|
|EDIT|domain/schema/invoice_read.py|
|EDIT|infrastructure/security/action_reference_codec.py|
|EDIT|infrastructure/security/invoice_reference_claims.py|
|EDIT|presentation/dto/invoice_action_response.py|
|EDIT fixtures only|tests/test_search_invoices.py|
|EDIT fixtures only|tests/test_open_authorized_invoice.py|
|NEW|application/port/i_invoice_references.py|
|NEW|application/service/invoice_read_validation.py|
|NEW|domain/model/invoice_read_budget.py|
|NEW|infrastructure/security/invoice_reference_codec.py|
|NEW TEST|tests/test_invoice_read_security.py|
|NEW TEST|tests/test_invoice_read_budgets.py|
|NEW TEST|tests/test_invoice_read_references.py|
|NEW TEST|tests/test_invoice_read_delivery.py|

9 edited/8new files. Existing test assertions/pytest.raises AST giữ nguyên. Fixture-only changes: dynamic valid UTC deadline thay fixed expired timestamp, search row date thuộc default90-day scope, optional budget argument ở private doubles. No dropped positive/negative cases. Schema-only19 original tests vẫn PASS.

Không sửa API/controller, Frappe Company authorizer, config, P1 outcome/DTO/serializer/terminal helper/A16 sink, frontend/B1-S, legacy/finance/hooks/framework/Docker/dependencies. Read adapter suggested `infrastructure/erpnext/authorized_invoice_read_adapter.py` **chưa tạo/instantiate** vì conditional integration gate không đạt; không fake production adapter/permission fallback.

Git diff chỉ thấy hai tracked frontend files có trước; P2 untracked nên không tạo fake “full source diff from HEAD”. Đã lưu full final source, before/after hash cho mọi touched file; exact before→after text diffs cho hai fixture files và Open DTO đã snapshot trước sửa. Không có complete before-content snapshot cho các untracked service files đã sửa; manifest hashes/probe ledgers/source snapshots là evidence, không tuyên bố có một full untracked before/after patch.

## 4. Tests và preservation

[Security Test Evidence](CHATBOT_P2A_SECURITY_TEST_EVIDENCE.md) có commands/ledgers và phạm vi từng run. Một combined run270/270=173P1+19P2original+78new. Sau DTO/full-envelope corrections, affected P2-only final103/103=19original+84new. Không cộng overlapping runs; tổng distinct cases covered276, không phải một fresh276-case run. P1 foundation source/security methods không đổi sau combined run, nên không lặp lại173 khi chỉ DTO/new-helper bị ảnh hưởng. V1 codec methods identical AST với independent P1 artifact; A16/B03 implementation nguyên hash. 138independent/A16/B03 historical dedicated probes không rerun và không bị diễn giải thành live ERP acceptance.

Guarded tests: network connect/bind/DNS denied trước import; real Frappe/ERP/LLM/legacy modules blocked; no cache/bytecode, no conftest/site fixture bootstrapping; private logger streams/handlers cleanup. Final P2 tests102→103 chỉ vì thêm một envelope-byte negative; 103PASS exit0. No ERP business reads/writes thực thi; synthetic port gọi/permissions double không là ERP SQL observation. Static compile/import audit: all17touched files<200(max197), application/domain no Frappe/ERP/infrastructure imports. Outside allowlist source fingerprints/staged/tracked diff giữ nguyên.

## 5. Graph impact, risk và limitations

Bound repo/workspace `lotus-fin / E:/lotus-fin`. Pre-edit graph trên old index trả UNKNOWN cho source P2; xác nhận callers/imports bằng bounded source search, không coi empty là LOW. Index-only refresh chạy qua cached GitNexus1.6.12, không install/AGENTS/skills edits. First native-worker startup failed; retry pool1/ready timeout30s thành công, index HEAD07f7251… dated2026-10-12T04:36:11.858Z,11531files/165192nodes/195013edges/541flows. Initial sandbox analyzer bị dừng; completed retry process exit0.

Current graph impacts: Search/Open1caller mỗi cái (disabled controller), LOW; InvoiceReadFilters6affected (port/services/request/response DTO/controller), MEDIUM; terminal2execute callers, LOW; v2codec3affected, LOW; ActionReferenceCodec name ambiguous với26historical copies, **--uid** exact current source resolves1caller/LOW. --file alone vẫn ambiguous; không dùng truncated candidates làm clean check. OpenResponseDataDTO0callers/UNKNOWN: text search confirms synthetic delivery tests, chưa có production composition, không kết luận unused/safe từ zero.

Process indexing warning: skipped entry points/callees/flows, nên zero affected processes không là proof no flows. Graph refreshed trong khi correction đang diễn ra, trước final envelope helper/DTO snapshot; current SOURCE_AFTER_CODE/source snapshots là final byte identity, không claim graph là fully immutable final-source certification. Fresh impact đã chạy trước last service edits. `detect-changes --scope all --limit500` cho9symbols/6flows/**HIGH** ở hai **pre-existing tracked frontend files**, không sửa. Output không bao phủ untracked backend delta; không gọi nó clean release check. HIGH đã được báo cho người dùng; preserve tracked diff. Không commit nên chưa thực hiện commit gate; future authorized commit cần graph final-artifact scan + complete untracked-aware review, không rely git-only zero.

## 6. Actual runtime và Gate2 decision

Read-only Docker check: backend `frappe_docker-backend-1`, image`lotus-fin:ai003-local`, immutable ID`sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`, sites/logs volume mounts, không app-source bind. [RUNTIME_READONLY.json](../evidence/chatbot-p2a-backend-integration-2026-10-12/RUNTIME_READONLY.json): all10selected P1/P2 paths **MISSING**. Python3.14.7 khác host3.13.7; source versions Frappe16.34.0/ERPNext16.35.0/Lotus0.0.1. Bench apps.txt không chứng minh site DB installed apps/hook order. Existing folders frontend/ai003-verify không selected approved P2 private target.

Không initialize/connect site, không HTTP/DB/business query, credentials/SID/environment dump, permission change/outage injection. Chưa canonical artifact với exact P1/P2 source và import/version lineage, ordinary-user sessions/map/key/sink/private fixtures/lifecycle authorization. Vì thế integration **BLOCKED**, live permissions/actual HTTP/CSRF/no-write DB delta **NOT_RUN**, không dùng simulated PASS để thay.

P2 offline profile:20/50page,100scan,51search doc checks/1open,10metadata,2list,0search detail/1open detail,64KiB full response/256KiB provider,5s cooperative end-to-end usecase budget,300s default token TTL,5pages,90/365date window,0automatic retry/LLM/report. Port must instrument every physical metadata/permission/hydration/source/SQL call; it can currently only be tested as a cooperative contract. App soft deadline/byte accounting không prove Frappe query bytes, hard SQL/audit timeout, distributed admission, collation, current-principal/user/company/field/mask/role/cache-revocation semantics. Production values,7day audit retention/key custody/admission/SLO still awaiting designated owner approval; no production configuration silently created.

## 7. Conditional real qualification plan, rollback và next gate

ERP/Ops owner cần cung cấp named approved private site/snapshot+lifecycle/cleanup; Backend immutable image containing exact source/apps/imports; ERP security ordinary allowed/denied users,2companies/site2 map, exact denied document, field/mask/query hooks và revocable roles; independent QA owns fixture gold outside tested implementation. Không actual names/credentials requested trong report.

Sau authorization riêng: inspect installed API/hook metadata trước adapter; implement current-principal Company/DocType-list/exact-doc/field-mask/no full Form/source projection, instrument budget trước I/O. Test real search→select→open, cross-company/site/config/session, valid-MAC wrong scope/stale/tampered selections, complete/incomplete keyset, source/deadline/audit outage, role/field revocation across workers, DB business/seen/view/queue delta0. Test actual cookie-auth POST, Guest/GET/CSRF/origin, single Frappe message/http_status_code/response_headers/CID/no-store, safe framework pre-handler failures. SQL/resource/hard cancellation/admission/cold-warm cache benchmarks phải actual, không fake-clock PASS. No shared frontend/competition data/ai003 site/ERPNext test-helper imports.

Enablement sau full independent real gate + release approval riêng; until then defaults và endpoints stay disabled. Rollback disabled composition/flag, retire key/bump approved scope version, verify no source call/ref; no data/schema migration rollback. Không use legacy permissive fallback. Existing byte observation không thu hồi được; UI fence/reader/P2-B là task riêng.

**Stop:** offline code corrected, retained inert; three requested outputs prepared. Không deployment, commit/push, finance automation, P2-B dispatch hoặc G10 PASS.
