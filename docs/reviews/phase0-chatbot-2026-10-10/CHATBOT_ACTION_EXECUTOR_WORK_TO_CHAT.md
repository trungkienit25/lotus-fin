# Work → Chat — Assisted Actions / SDK decision

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026 · `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + current dirty hashes.

**`ACTION_ARCHITECTURE_READY_FOR_CHAT_DECISION`**. Current Python backend hỗ trợ model typed action execution. SDK-backed adapter khả thi nhưng chưa nên thêm SDK/service cho pilot. **Chọn A: backend Lotus hiện có → strict stateless use cases → in-process Frappe adapter**, qualified current-user context. Lotus Fin/ERPNext là hai sản phẩm riêng; cùng deployment không đổi identity.

## Đối chiếu proposal người dùng

|Phần|Trạng thái có evidence|
|---|---|
|B1-S UI safety/harness|Đã triển khai, R7 independent PASS:52 gold/native4/Q1–Q8. Current13/13 fingerprints unchanged; lượt này không rerun.|
|P1 outcome/context/ref/search-open contracts|Draft PROPOSED/NOT_FROZEN; chưa implementation.|
|Chatbot tìm/chọn/mở invoice; V1 overdue|Chưa có typed API/use cases/UI. P1 generic search khác PastFinalDue.|
|Local prefill/ERP Draft/confirm-write|Chưa có assisted-action workflow; writes disabled. Generic manual CRUD không là chatbot executor.|
|B0/judge deployment|Chưa qualify; G10 BLOCKED riêng.|

Proposal Round3 còn mô tả React fallback/HTML risk và3 synthetic cases đã lạc hậu. Không rewrite proposal/history hoặc chạy lại B1. SDK names/diagram không chứng minh automation đã có.

## Năm findings quyết định

1. ToolInvoker gọi sáu finance commands, raw args; schema published không runtime validation. Chưa invoice action catalog/authorized read port.
2. AgentRunner/legacy fallback có false-success risk; old reproduced defects trên source không đổi. Bypass cho pilot, không rewrite runner.
3. Shared chat sessions thiếu ownership isolation; stateless pilot tránh dependency này, vẫn test auth-session.
4. Current DTO thiếu P1 status/source/CID/context. Cần endpoint/serializer mới, giữ một outcome contract.
5. Docker kết nối được nhưng host/container controller/DTO khác nhau. Serving imports/site rights chưa verify; phải qualify canonical isolated artifact trước bật.

Reuse clean architecture seams, deterministic domain logic và B1 safe text/CID/lifecycle; không reuse Admin/mock fallback, raw generic CRUD/RPC, full editable form hoặc old finance wrappers như permission boundary.

## Adapter và extensibility

A ưu tiên hiện tại. B typed Python REST dành cho target remote được xác nhận. C SDK sau cùng port nếu pinned client/target/auth tests đủ; D service riêng chỉ khi runtime/target/operator/SLO justify. Không cần NestJS chỉ vì muốn dùng SDK.

JS `frappe-js-sdk` là third-party, không installed; v16 compatibility NOT_VERIFIED. Python `frappe/frappe-client` đã archive31/03/2026, không installed. [Primary archive evidence](https://github.com/frappe/frappe-client). SDK credentials chạy bằng ERP principal tương ứng; **không tự inherit quyền người dùng Lotus**. Remote delegation/scoped service account phải explicit; reject unrestricted Administrator + frontend filters.

READ đầu tiên: clarify → authorized bounded search → user select → fresh doc/field/version checks → minimum Lotus reader. No amounts/overdue/reports/LLM/ERP writes. PREPARE tương lai là local UNSAVED preview, khác saved ERP Draft. WRITE cần separate immutable exact-args proposal/explicit one-use confirm/reauth/durable idempotency/audit/reconciliation; timeout-after-commit UNKNOWN_OUTCOME không blind retry. Submit/cancel/send/payment/autonomous actions disabled.

## Quyết định và thứ tự batch

Chat approve P1 D1–D6: (1) React generic Sales Invoice, (2) minimum read-only reader, (3) A/current-user target + isolated qualification owner, (4) P1 six outcomes/projection/signed refs, (5) budgets/key/CSRF/log/workload, (6) exact allowlists/owners/tiny Panel variance. Accept typed use cases as executor responsibility; **P1-C không thêm competing registry**. Remote/native-form/financial/LLM/write scope cần amendment riêng.

|Order / owner|Acceptance trước enable|
|---|---|
|P1-A outcome/CID; Antigravity BE → Work|Strict delivery/schema/denial/source/redaction, no old DTO fallback|
|P1-B context/auth/ref; security BE → Work|Forged/cross-scope/expiry/CSRF/current principal; endpoints disabled|
|P1-C; Chat+Work checkpoint|Chốt catalog→explicit use cases; không executor framework mới|
|P2-A bounded read; BE → Work|Permission/field/source/version/caps/deadline/bytes/no-write|
|P2-B UI; frontend → Work|Clarify/results/select/reader/race/XSS/cancel +52 gold preserved|
|P2-C; independent Work → Chat|Fresh canonical private target: ordinary allowed/denied users, revocation/company/site/masks/outage; real API-vs-SQL counts and workload; cleanup|
|P3; Chat+Work design first|PREPARE contract then separate WRITE protocol; no current implementation dispatch|

Exact proposed paths/dependencies/rollback ở decision §9 và P1 §9. Application/SDK/ERP/performance tests **NOT_RUN** trong lượt inspect; no clean qualified baseline, no synthetic permission PASS. G3/G01–G03 chưa đóng; G10 vẫn riêng. Chat có thể approve kiến trúc để bắt đầu batch nhỏ, chưa thể đóng assisted-action feature hoặc bật financial automation.

[Source/proposal comparison + hashes](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_ACTION_EXECUTOR_CODEBASE_INSPECTION.md) · [PROPOSED architecture decision](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_ERP_SDK_ACTION_ARCHITECTURE_DECISION.md) · [Existing P1 SSOT](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md).

Chỉ tạo ba review Markdown; preserve source/P1/proposal/history. Không freeze, install, sửa permissions/data, commit/deploy hoặc dispatch Antigravity.
