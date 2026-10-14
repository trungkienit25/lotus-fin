# LOTUS FIN — P2-A Independent Backend Acceptance

12/10/2026 · Asia/Saigon · Independent Backend Security QA / Frappe Integration Review.

**Offline: CHANGES_REQUIRED. Live integration: BLOCKED; live permission/HTTP/DB qualification: NOT_RUN. P2-B: NOT_READY. G10: independently BLOCKED, không được đóng bởi quyết định này.**

Bộ source test hiện có chạy mới **276/276 PASS**; oracle bổ sung độc lập **72 PASS / 12 FAIL / 0 ERROR** trên 84 ca. Ba nhóm lỗi contract bên dưới chặn nghiệm thu offline và độ ổn định backend để xây UI. Không phát hiện unauthorized exposure trong các ca offline đã thực thi; đây không phải chứng minh quyền ERP thật. Không sửa implementation để làm test PASS.

## Authority và phạm vi quyết định

Đã đọc bản hiện tại của [Target Preflight](CHATBOT_P2A_TARGET_PREFLIGHT.md), [Implementation Handoff](CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md), [Test Oracle](CHATBOT_P2A_TEST_ORACLE.md), [Backend Integration Report](CHATBOT_P2A_BACKEND_INTEGRATION_REPORT.md), [Security Test Evidence](CHATBOT_P2A_SECURITY_TEST_EVIDENCE.md), packet P2-A, root [offline implementation report](E:/lotus-fin/CHATBOT_P2A_OFFLINE_IMPLEMENTATION_AND_EVIDENCE.md), [P1 MASTER](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md) và [P1 final independent acceptance](CHATBOT_P1_FINAL_INDEPENDENT_RECHECK.md). Latest integration report là self-verification của correction, không thay independent acceptance. Root report 19-test là lịch sử trước correction; không lấy verdict đó làm PASS hiện tại.

Outcome authority giữ `p1.invoice.v1`, sáu statuses và closed reason mapping hiện có. MASTER vẫn PROPOSED/NOT_FROZEN; phiên này không freeze SSOT, phê duyệt production config, mở production ERP hoặc đánh giá deployment. P2-B readiness chỉ xét backend contract đủ ổn định để xây UI; vẫn NOT_READY vì lỗi offline, không chỉ vì thiếu live target.

Áp dụng GitNexus exploring/impact-analysis theo AGENTS. Chỉ đọc source, chạy focused tests/probes offline, inspect Docker metadata/filesystem và tạo báo cáo/evidence. Không package install, ERP/site initialization, HTTP/DB request, shared ERP call, Docker mutation, permission/config mutation, commit hoặc deployment.

## Source, dirty tree, changed paths và artifact identity

Workspace/repo `lotus-fin / E:/lotus-fin`, branch `develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`. Staged rỗng. Hai tracked dirty paths có trước:

- `frontend/src/components/copilot/LotusCopilotDrawer.tsx`
- `frontend/src/pages/copilot/components/VercelChatPanel.tsx`

Tracked binary diff SHA-256 `09344d31c5b694e62eb399cc6461a6388ea77c330fbf1943b127b4f3c56fd3eb`; staged diff SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Inventory `--untracked-files=all` trước phiên có 10.870 dirty/untracked paths, phần lớn evidence/docs/source có trước; không gọi đây là delta P2-A. Backend P1/P2 chưa tracked, nên HEAD/git diff không đủ định danh release.

[SOURCE_BEFORE.json](../evidence/chatbot-p2a-independent-2026-10-12/SOURCE_BEFORE.json) khóa 409 file code/config/review hiện tại; [GIT_STATUS_BEFORE.txt](../evidence/chatbot-p2a-independent-2026-10-12/GIT_STATUS_BEFORE.txt) giữ full path inventory. Manifest này là inventory có phạm vi, không phải mọi file trong workspace. [BUILDER_HASH_COMPARISON.json](../evidence/chatbot-p2a-independent-2026-10-12/BUILDER_HASH_COMPARISON.json): **17/17 final code/test hashes khớp, 0 mismatch** với SOURCE_AFTER_CODE của builder; hashes các module import thật cũng khớp. Không suy luận serving identity từ host test.

Exact correction paths của builder, dưới `lotus_fin/lotus_fin/`:

|Kind|Path|
|---|---|
|EDIT|application/service/search_invoices.py|
|EDIT|application/service/open_authorized_invoice.py|
|EDIT|application/port/i_authorized_invoice_read.py|
|EDIT|domain/schema/invoice_read.py|
|EDIT|infrastructure/security/action_reference_codec.py|
|EDIT|infrastructure/security/invoice_reference_claims.py|
|EDIT|presentation/dto/invoice_action_response.py|
|EDIT fixtures|tests/test_search_invoices.py|
|EDIT fixtures|tests/test_open_authorized_invoice.py|
|NEW|application/port/i_invoice_references.py|
|NEW|application/service/invoice_read_validation.py|
|NEW|domain/model/invoice_read_budget.py|
|NEW|infrastructure/security/invoice_reference_codec.py|
|NEW TEST|tests/test_invoice_read_security.py|
|NEW TEST|tests/test_invoice_read_budgets.py|
|NEW TEST|tests/test_invoice_read_references.py|
|NEW TEST|tests/test_invoice_read_delivery.py|

So với builder SOURCE_BEFORE 747 entries, có 9 existing code/test paths đổi và packet P2-A đổi; 8 new paths ở bảng không có trong baseline. [P1_AST_AND_BUILDER_DELTA.json](../evidence/chatbot-p2a-independent-2026-10-12/P1_AST_AND_BUILDER_DELTA.json) giữ exact before/current hashes. Không có full before-content của mọi untracked service; không tuyên bố có complete Git patch cho backend.

|Current source / authority|SHA-256|
|---|---|
|search_invoices.py|324d83d315028183749cf3fa9c8d773701fbb66b1061b8572a3df950a7f2b313|
|open_authorized_invoice.py|53c9219b8d57861e853ce2ec2ee5ca1fa5d4ca50ce8ab05b98ca83934aaec040|
|invoice_read.py|70c5406b0703a6218e4d3cc8739e86d80cfac9d6efb7357fe45ba6249ba8f419|
|invoice_actions_controller.py|6e3989e78b7a8d717e4e3c561835dbff70742d1c0df4b8c0216d210e042d6755|
|frappe_invoice_authorizer.py|84c6d1dee0075abbfc9c3326bf5e3faaf5caaa19422f01ef118543659b5e22f9|
|invoice_action_request.py|23db89ddbfcc2349d24c4847567d07fc350c632a8b57b47d2964ef3cf58954dc|
|P1 MASTER|751ed14eff6dec6e6aa832150ee022551b56a43b23dc5699839e747cd9e9e640|

Full SHA-256 của 17 correction paths và API/config/audit/P1/report authority nằm trong linked manifests.

## Findings chặn offline / P2-B

### P2A-F01 — Scope version đổi theo capability, phá fresh search → open [P1]

[Authorizer:131](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:131) đưa `capability` vào fingerprint. Với cùng ordinary actor/session/site/company/connection policy, gọi resolver thật ba lần nhận ba context_version khác nhau. Context token không verify với fresh search context; selection token do SearchInvoicesService thật phát hành bị OpenAuthorizedInvoiceService thật trả `FORBIDDEN/ACCESS_DENIED`, document port calls=0 khi dùng fresh open context.

Independent C05/C06/C08 **FAIL**; C01/C07 **PASS** chứng minh setup context/search đã thành công. C09 **PASS** khi test ép giữ version bằng `model_copy` rồi đổi capability: positive control này giải thích vì sao các test dùng chung context có thể che lỗi. Không dùng forced version như production solution. Quyền Company chỉ là synthetic exact-document double; không có live ERP session.

Vi phạm Oracle Q13 và Handoff §3: same read-family scope phải ổn định qua context/search/open; capability vẫn fresh authorize riêng. Đây là prerequisite P2 chưa hoàn tất trên source được nghiệm thu, không phải P1 regression mới. Cần correction nhỏ có scope review, giữ mọi binding actor/session/company/site/policy/contract/projection và deny khi scope thật đổi; không bỏ context-version check để làm positive PASS.

### P2A-F02 — get_context chưa thực hiện ContextData cho UI [P2]

[Controller:74](E:/lotus-fin/lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py:74) thiếu `default_posting_from/default_posting_to`; [line 78](E:/lotus-fin/lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py:78) trả request deadline làm `expires_at`. Independent C02/C03 **FAIL**: reported expiry còn khoảng **4,98s**, authenticated context token thực tế còn **299,47s**. C01/C04 **PASS**: context response OK và terminal/RID/CID hoạt động trong private stream, không phải disabled/setup error.

Vi phạm MASTER §5 D1 và Handoff §2, đã được preflight nhận diện. UI không có server date defaults như contract và có thể coi token 5 phút đã hết hạn sau 5 giây. Cần trả approved site-local inclusive 90-day defaults và actual signed context-token expiry, tách TTL khỏi deadline. Không thay đổi P1 v1 crypto semantics ngầm.

### P2A-F03 — Null/missing input được repair thành default thay strict reject [P2]

[Request DTO:44](E:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/invoice_action_request.py:44) nhận `filters:null`, missing required filters và `page_size:null`. [Filters:31](E:/lotus-fin/lotus_fin/lotus_fin/domain/schema/invoice_read.py:31) nhận explicit null dates; [normalization:55](E:/lotus-fin/lotus_fin/lotus_fin/domain/schema/invoice_read.py:55) biến chúng thành omitted date pair. **7 FAIL** I03/I04/I05: sáu schema negatives cùng một application reproduction. `posting_from:null` thực sự tới port một lần và trả `OK/RESULTS_FOUND`, thay expected `INVALID_REQUEST` trước source call.

MASTER SearchRequest có required filters object; page_size optional nghĩa là omitted dùng 20, không phải nullable. Handoff §2 yêu cầu explicit empty/wrong-type date fields bị reject; chỉ date pair thực sự omitted mới được default. `{filters:{}}`/omitted page_size positive PASS; bool/string/0/51 sizes và các extra arbitrary scope/RPC/field inputs bị reject. Không có bằng chứng unauthorized ERP exposure; lỗi nằm ở schema/query semantics chưa ổn định. Cần phân biệt omitted với explicit null, bổ sung negative tests và giữ valid default/NFC/date-bound controls.

Ba findings trên được tái hiện trực tiếp bằng runner độc lập, không lấy builder verdict hay giả lập HTTP làm chứng cứ. F01/F02 đã là các P2 completion gaps trong handoff; báo cáo integration giới hạn PASS vào private typed core nhưng chưa đóng chúng. Không chấp nhận đầy đủ P2-A/P2-B readiness bằng cách loại bỏ các contract đang được SSOT yêu cầu.

## Thực thi test và containment

Host `C:/Python313/python.exe`, Python 3.13.7, pytest 9.0.2, Pydantic 2.12.5. Từ `E:/lotus-fin`:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
Get-Content -Raw docs/reviews/evidence/chatbot-p2a-independent-2026-10-12/FOCUSED_REPRODUCTION.txt | C:/Python313/python.exe -B -
Get-Content -Raw docs/reviews/evidence/chatbot-p2a-independent-2026-10-12/NEGATIVE_REPRODUCTION.txt | C:/Python313/python.exe -B -
```

|Run|Actual result|Evidence|
|---|---|---|
|19 focused source modules; explicit pytest paths, `-p no:cacheprovider --noconftest -v`|276 PASS / 0 FAIL / 0 SKIP, exit 0; **173 P1 +103 P2**, fresh combined run|[FOCUSED_RESULTS](../evidence/chatbot-p2a-independent-2026-10-12/FOCUSED_RESULTS.json), [raw stdout](../evidence/chatbot-p2a-independent-2026-10-12/FOCUSED_STDOUT.txt)|
|Independent inputs/negative oracle, tự tạo synthetic fixtures, không nhập builder fixture|84 cases: **72 PASS /12 FAIL /0 ERROR**, exit 1|[NEGATIVE_RESULTS](../evidence/chatbot-p2a-independent-2026-10-12/NEGATIVE_RESULTS.json), [raw stdout](../evidence/chatbot-p2a-independent-2026-10-12/NEGATIVE_STDOUT.txt)|
|Independent P1 v1 codec AST comparison|5/5 original methods identical với accepted P1 source|[AST/delta ledger](../evidence/chatbot-p2a-independent-2026-10-12/P1_AST_AND_BUILDER_DELTA.json)|

Không cộng các lần chạy overlapping, không coi 84 ca là toàn bộ live oracle. Dedicated historical P1 138/A16 14/B03 8 probes **NOT_RERUN**; không biến thành mới hoặc ERP permission PASS. [TEST_SUMMARY](../evidence/chatbot-p2a-independent-2026-10-12/TEST_SUMMARY.json) phân loại counts, cleanup và hashes module.

Guards đặt trước application import, chặn socket connect/connect_ex/bind/DNS và real Frappe/ERP/provider imports; plugin autoload/conftest/cache/bytecode disabled. Network attempts **0**. Focused run có **11 blocked Frappe import attempts**, independent run có **1 blocked attempt** từ package initialization; không real Frappe import được cho qua. Company seam dùng ModuleType synthetic riêng; source identities được kiểm đường dẫn/hash. Private streams/handlers được tháo, synthetic Frappe được gỡ, process test kết thúc. Không credentials/token/SID/business rows thật trong evidence.

## Kết luận theo 12 yêu cầu

|Yêu cầu|Offline source/probe conclusion|Live limit|
|---|---|---|
|1 Typed search/open + strict P1 mapping|Closed rows/five-field open DTO, fixed navigation, status/reason/HTTP mappings và denial precedence PASS; **F02/F03 contract FAIL**|Real request decoder/wrapping NOT_RUN|
|2 Server principal/company/site context|DTO không cho client overrides; Company exact read/server session/site/map seam fail closed; **F01 stable family scope FAIL**|Actual principal, trusted routing, disabled user/site policy NOT_RUN|
|3 Permission-aware bounded search|Read port contract + strict returned-count/duplicate/filter/source checks; page-size, logical call/row/byte caps PASS|Concrete Frappe read adapter **ABSENT**; list/DocType read/select-only/doc hooks/authorized bounds/masks/SQL/collation NOT_RUN|
|4 Exact doc/field reauthorization on open|Fresh port invocation, exact identity/company/version/fixed descriptor và typed doc/field denial PASS; real resolver pipeline **F01 FAIL**|Field/doc rights implementation và actual revocation NOT_RUN|
|5 Signed refs, expiry/revocation|v2 MAC/purpose/schema/scope/query/version/current key/equality-expiry checks PASS; v1 methods preserved; **context expiry metadata F02 FAIL**|Key custody/current policy/ordinary-user revocation across workers NOT_RUN|
|6 Complete/PARTIAL|Valid incomplete observation→PARTIAL, coverage INCOMPLETE; zero-row incomplete không EMPTY_RESULT; refs/cursor/has_more null PASS|Authorized upper bound/lookahead/page completeness thật NOT_RUN|
|7 Terminal audit/request/CID|Private real StreamHandler single ack/line/IDs; missing sink no admission, outage no protected success/no retry PASS|Public API còn disabled helper riêng; production composition/audit/status/header/single wrapper/CSRF NOT_RUN|
|8 No arbitrary RPC/full doc/field access|Explicit endpoints, extra method/url/doctype/sql/fields overrides rejected, minimal fixed projections PASS trong code paths đã đọc|Lazy parent/child hydration/custom hooks/no-full-form property trên target NOT_RUN|
|9 Source outage/timeouts|Typed source/timeout failures null data/source, no demo/legacy retry; logical caps và late-return suppression PASS|Physical SQL/provider-byte/hard DB/audit interruption/admission NOT_RUN|
|10 No ERP business mutation|Core/ports không có business write/form/onload path; test ERP reads/writes=0 bởi containment|ERP no-write before/after proof **NOT_RUN**, không PASS từ zero requests|
|11 P1 regressions|**173/173 fresh PASS** và 5/5 v1 method AST preserved; không reopen P1/B1-S từ lỗi prerequisite P2|B1 browser/other unrelated suites NOT_RERUN|
|12 Disabled until qualified|Config default False; API/helper và controller search/open unconditional disabled, kể cả synthetic enabled config PASS|Không có qualification/enablement/release approval; giữ disabled|

API source hiện vẫn helper disabled, chưa nối required terminal boundary, trả `{message: body}` và đặt `response.status_code/headers`. Preflight đã chỉ ra nguy cơ double-message/status-header mismatch khi đi qua Frappe wrapper. Đây là **known unqualified transport/composition blocker**, không claim actual HTTP FAIL/PASS từ source hay controller calls. Context→search→open probes ở đây là offline direct composition, không HTTP.

## Serving artifact và integration gate

[RUNTIME_IDENTITY.json](../evidence/chatbot-p2a-independent-2026-10-12/RUNTIME_IDENTITY.json) là quan sát độc lập mới qua read-only Docker inspect và Python stdin `-B` đọc file/version, không import app/init site/connect DB:

|Observation|Actual|
|---|---|
|Backend|frappe_docker-backend-1; container `a857658a101bbe5304d16160d65c5669878e9b5eada9b3d288666236c84f0b55`|
|Immutable image ID|`sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`; tag lotus-fin:ai003-local|
|Mounts|sites/logs volumes, **không bind host app source**|
|Selected source files|**10/10 MISSING**, gồm API/controller/search/open/port/schema/codec/authorizer/audit|
|Runtime/source versions|Python 3.14.7; source Frappe16.34.0/ERPNext16.35.0/Lotus0.0.1; Python khác host|

Sandbox Docker read ban đầu bị permission denied; read-only escalation được auto-review chấp nhận, hai inspection exits 0. Không có approval rejection còn pending. Metadata/source presence không là imported runtime/app-site identity; không dump config/environment/secrets. Không selected hoặc gọi shared frontend/ai003-verify.

**Không có approved isolated target đã được kiểm thử** trong packet hiện tại: không ordinary-user sessions, independent real permission gold ledger, exact deployed P1/P2 source/import lineage, approved map/key/sink/fixtures/lifecycle. Vì vậy real requests, permission oracle inspection, Company/DocType/doc/field/mask/revocation, HTTP/CSRF, actual resource/outage, ERP before/after no-write và fixture cleanup đều **NOT_RUN**. Không fixture được tạo/sửa nên không có cleanup lifecycle để chứng minh. Offline fake permission output không sinh live expected results và không được dùng để đóng integration.

Gate classification: **P2A_LIVE_INTEGRATION = BLOCKED** bởi known missing artifact/target/authorization/fixtures; execution status của live permission/integration tests là **NOT_RUN**. Hai trạng thái khác nhau: gate bị chặn và không có live execution. Không suy luận PASS từ mocks hoặc tag/apps inventory.

## GitNexus, integrity và điểm dừng

Repo bound lotus-fin/E:/lotus-fin; cached GitNexus1.6.12, không install/reindex. Index HEAD khớp `07f7251…`, indexed `2026-10-12T04:36:11.858Z`, 11.531 files/165.192 nodes/195.013 edges/541 flows. HEAD freshness không chứng minh final dirty/untracked source fully indexed; index có trước final helper/DTO correction.

Fresh concept query trả port definitions, không execution flow; fresh context/impact Search/Open exact paths mỗi cái 1 upstream controller importer, **LOW**; filters 5 direct/6 total, **MEDIUM**; exact UID codec 1 controller importer, **LOW**. Controller name ambiguous với historical copies, đã đọc lại exact current UID; authorizer exact UID context đã đọc. Không dùng ambiguous/zero flow làm all-clear. Raw graph files ở evidence root; text/source reading dùng để kiểm implementation sau graph, không thay graph analysis.

Fresh `detect-changes --scope all --limit 500` exit 0 báo **HIGH: 2 pre-existing tracked frontend files, 9 symbols, 6 flows**. Đã cảnh báo; phiên này không sửa chúng. Git-only detect_changes không bao phủ untracked backend/report delta và không là clean release/commit check. No application edits/commit; future correction cần fresh pre-edit impact, warning HIGH/CRITICAL và UNKNOWN confirmation theo AGENTS. Wrapper ban đầu EPERM do pnpm; direct cached CLI hoạt động, không cài package để khắc phục.

[SOURCE_AFTER.json](../evidence/chatbot-p2a-independent-2026-10-12/SOURCE_AFTER.json) xác nhận **409/409 protected fingerprints nguyên**, HEAD/staged/tracked diff nguyên; chỉ thêm hai báo cáo yêu cầu và evidence của review này. Module identity hashes nguyên. Không broad architecture audit hoặc unrelated regression suite.

**Final gates:**

- `P2A_OFFLINE_INDEPENDENT = CHANGES_REQUIRED`
- `P2A_LIVE_INTEGRATION = BLOCKED` — live permission/integration execution `NOT_RUN`
- `P2A_P2B_READINESS = NOT_READY`
- `G10 = BLOCKED` độc lập, không kiểm/đóng trong P2-A.

Điều kiện recheck offline: sửa F01–F03 trong batch được duyệt, giữ enabled=False/unconditional search-open disabled; positive fresh-context pipeline và strict-null/context-data negatives PASS; affected P1/P2 checks cùng source/graph identity được xác minh lại. Live gate cần task qualification riêng với approved private target, immutable artifact, independently owned permission oracle, real requests/resource/audit/no-write evidence và cleanup. **Dừng tại quyết định gate; không dispatch sửa lỗi, P2-B, integration, commit hoặc deployment.**
