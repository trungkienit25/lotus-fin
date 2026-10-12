# P1 — Kiểm tra chấp nhận độc lập cuối cùng

12/10/2026 · Asia/Saigon · Backend QA / Application Security · Kiểm tra source offline.

**P1-A: P1A_OFFLINE_PASS. P1-B: P1B_OFFLINE_PASS.** F01–F04 được đóng trên working tree hiện tại bằng thực thi độc lập; không dùng builder verdict làm bằng chứng PASS. **Đề nghị chuyển sang P2-A target qualification preflight.** Không bắt đầu triển khai P2-A.

## Danh tính và phạm vi

`develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; staged rỗng. P1 backend chưa được Git theo dõi; HEAD không đủ định danh. Dirty Panel/Drawer và exact tracked binary diff được giữ nguyên. [Manifest trước](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/SOURCE_BEFORE.json), [snapshot source](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/SOURCE_CONTENT.json), [diff độc lập từ closure](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/INDEPENDENT_SOURCE_DIFF.patch.txt) khóa artifact bằng SHA-256. Đây là source trong workspace, chưa xác minh artifact đang phục vụ production.

Đã đọc closure decision, hai final-fix reports, hai root implementation reports, MASTER SSOT §3–6, AGENTS, ADR001 và Security Code V3. Không sửa authority/hợp đồng hoặc lịch sử verdict.

|Source dưới `lotus_fin/lotus_fin/`|Dòng|SHA-256 hiện tại|
|---|---:|---|
|domain/schema/action_outcome.py|198|`bf90ca6b85743b7152a9b749528240c9c48d48a39e4682c18e674adf78fc2bb9`|
|infrastructure/security/action_reference_codec.py|147|`9270cd467ca795185db8b5f5c8df7fa0158d977e32aa78b8fca54cbfaf2bd009`|
|presentation/controller/invoice_actions_controller.py|117|`bbfe06b870d7b5f67621f89f4101e128d8ed6b2190595fef7f9ed51a5a603d3a`|
|presentation/response/invoice_action_delivery.py|56|`0bfdd70dfb485b3f415bcf3da54b80d531b41f0e35a0f5cdd4d05cd131ed8c84`|

Production/test hashes khớp artifact builder; hai root reports có append sau manifest builder, đã xác minh prefix cũ giữ nguyên. [Static audit](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/INDEPENDENT_STATIC_AUDIT.json) chứa toàn bộ hashes còn lại.

## Thực thi và kết quả

Python `C:/Python313/python.exe` 3.13.7; pytest 9.0.2; Pydantic 2.12.5. Env: `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. [Lệnh/exits](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/COMMANDS.json) lưu đầy đủ tham số và cảnh báo.

|Lệnh đã chạy từ workspace|Kết quả / exit|
|---|---|
|`git rev-parse HEAD`, `git status --porcelain=v1 --untracked-files=all`, `git diff --cached --binary`, `git diff --binary`|exit 0; hai cache cũ không đọc được, không dùng cache trong tests|
|`Get-Content -Raw …/FOCUSED_REPRODUCTION.txt \| C:/Python313/python.exe -B -`|173/173 PASS, exit 0; 12 explicit test modules, `pytest.main` với `-p no:cacheprovider --noconftest -v`|
|`Get-Content -Raw …/NEGATIVE_REPRODUCTION.txt \| C:/Python313/python.exe -B -`|138/138 PASS, exit 0; probe mới, không nhập builder fixture|
|`C:/Python313/python.exe -B -` với stdin đã kiểm tra trong `A16_CURRENT/REPRODUCTION.txt`, `B03_CURRENT/REPRODUCTION.txt`|14/14 và 8/8 PASS; cả hai exit 0|

Dấu `…/` ở bảng là `docs/reviews/evidence/chatbot-p1-final-independent-recheck-2026-10-12/`; exact stdin và raw outputs nằm tại đó. [Focused ledger](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/FOCUSED_RESULTS.json) xác minh đường dẫn/hash các module nhập thật. Các bộ có overlap, không cộng thành unique coverage.

|Finding|Bằng chứng độc lập trên mã hiện tại|Quyết định|
|---|---|---|
|F04|22 probe: đủ 5 forbidden reasons × OK/PARTIAL × dict/list; domain, DTO, serializer đều từ chối nested denial. Outcome bị mutate đi qua terminal helper trả 403/FORBIDDEN/ACCESS_DENIED, data/source null, 1 ack. Hai benign controls vẫn 200. Không lộ protected canary.|CLOSED_VERIFIED; P1-A|
|F01|58 probe: giải mã ref từ controller thật; raw actor/email, SID và secret key không xuất hiện trong claims/body/log. Matching actor hợp lệ. Sai actor/session/site/product/company/connection/config/context/projection/purpose/key/expiry/wire hoặc binding version đều bị từ chối; cả payload có MAC hợp lệ nhưng schema/actor cũ. `key_id` là metadata công khai, không phải secret.|CLOSED_VERIFIED; P1-B|
|F02|42 probe trên 7 terminal paths. Healthy required StreamHandler: đúng 1 attempt = 1 acknowledged event = 1 log line, RESPONSE_DELIVERY khớp body/CID/RID. Missing sink: 503/null, 0 ack. Write/flush/short-write/suppression: safe ActionEventDeliveryError, 1 attempt/0 ack, không trả protected success, không retry.|CLOSED_VERIFIED; P1-B|
|F03|12 probe search/open: UUID4 hợp lệ, kể cả uppercase, echo nguyên. Missing/malformed/wrong type/UUID1 thay UUID4 với 422/INVALID_REQUEST. CID/header/event đồng nhất; raw ID không vào log. Denial precedence được giữ trong focused tests.|CLOSED_VERIFIED; P1-B|
|A16 / B03|A16 14/14 kiểm tra default/direct/ancestor/root, outage, suppression, shared-handler concurrency, callback giữ nguyên. B03 8/8 kiểm tra exact Company/actor, denied/unavailable seam/Guest/SID; thêm 4 probe absent/throws/False/truthy. Không cấp ref khi denied.|CLOSED_VERIFIED; không hồi quy|

[Negative ledger](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/NEGATIVE_RESULTS.json) chứa từng case/quan sát. Success permission controls chỉ dùng qualified doubles tại Company seam; source evidence của pure schema controls là synthetic. **Không phải ERP authorization acceptance hoặc bằng chứng dữ liệu ERP thật.**

## Integrity và giới hạn

27 code/test files compile, tất cả <200 dòng (tối đa 199). Tám historical test files giữ mọi assertion/`pytest.raises`; bảy file giữ nguyên, một file chỉ thêm UUID4 vào hai disabled-test inputs, giữ nguyên assertions 503. Missing/invalid IDs có negatives riêng. Diff gồm ba production sửa, một cohesive delivery helper mới, bốn test modules mới và hai test inputs; không có generic framework, fake production module hoặc permission bypass.

Đối chiếu builder-before: 676 protected files không có thay đổi ngoài fix; 3.484 historical review files nguyên hash. B1-S R7: 13/13 source/package/harness/report snapshots khớp hiện tại. A16 adapter/B03 authorizer nguyên byte. [After integrity](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/SOURCE_AFTER.json): toàn bộ 4.215 fingerprints trước phiên này không đổi, HEAD/staged/diff giữ nguyên.

GitNexus cached 1.6.12: index cũ 61 commits; query trả flows không liên quan, context/impact current symbols exit 1/UNKNOWN. Wrapper `status` ban đầu exit 1 do pnpm EPERM; chuyển CLI cache sẵn, không install/refresh. [Graph evidence](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/GRAPH.json). UNKNOWN vẫn unresolved bằng graph; đối chiếu source xác nhận scanner→domain/DTO/delivery, codec→controller, delivery→controller. Không coi zero callers là all-clear. Không sửa source/commit nên không dùng graph để cấp quyền sửa.

Network attempts 0; ERP business reads 0; handlers/threads riêng được dọn, framework doubles được gỡ, Python processes kết thúc. Không implementation edit, install, live ERP call, Docker change, commit hoặc deployment.

**Gate tiếp theo được đề nghị: P2-A target qualification preflight.** Live ERP/document/field/revocation permissions và HTTP/auth/CSRF: **NOT_RUN / NOT_VERIFIED**. Invoice search/open vẫn disabled; B1-S historical PASS được bảo toàn, browser không rerun. **G10 tiếp tục independently BLOCKED.** Không có material offline blocker tái hiện; không tự động triển khai P2-A hoặc bật invoice actions.
