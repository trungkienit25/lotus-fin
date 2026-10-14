# Work → Chat — Chatbot Assisted Actions P1

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026.

**Verdict: `P1_READY_FOR_CHAT_APPROVAL`. Contract PROPOSED/NOT_FROZEN; chưa implemented, chưa dispatch Antigravity.** B1-S giữ `B1S_G4B_PASS`; R7 gold52/52/native4/4 là evidence lịch sử được giữ, không chạy lại trong P1. G10 vẫn BLOCKED riêng. Không bật financial widgets/unqualified Copilot POST.

**Hướng đề xuất: Option A — typed/stateless authorized read API trong backend Lotus hiện có**, strict Frappe adapter ở infrastructure, React làm pilot. Lotus Fin và ERPNext là hai sản phẩm riêng; không cần suy ra microservice hoặc “ERPNext SDK”. Chatbot giúp chọn intent/tiêu chí, server nắm quyền và source; zero LLM calls cho pilot đầu tiên. Ordinary UI dùng lại cùng use case.

## Facts hiện tại và năm finding quyết định thiết kế

Actual `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + dirty Panel/Drawer có trước; staged empty.60 architecture fingerprints unchanged; current routes/source đọc lại. Docker29.1.3 connected; local Frappe16.34.0/ERPNext16.35.0/Lotus0.0.1, image `ed6e02f…`; backend no host source mount, **controller/DTO container khác host**, resident import/site permissions chưa qualified. GitNexus stale61/notfound; bounded static caller trace, không graph all-clear.

|Priority|Source fact/root cause|Minimum implication|
|---|---|---|
|1 C06 HIGH|Existing principal/tool args thiếu strict scope/validation; no-framework Admin/mock/True fallbacks|NEW server principal/site/product/connection/company/context authorizer; fresh read/doc/field checks, no privileged fallback.|
|2 C05 MED|Old ChatResponseDTO/service mất status/reason/CID, raw errors/fallback che outcome|NEW versioned six-status envelope/CID/event chain; bypass old DTO/controller fallback.|
|3 C01/C03 HIGH|Runner có last-tool/data mismatch; global session không owner/site/product/retention guarantee|Stateless typed invoice use cases, không AgentRunner/chat session; old fixes deferred tới capability phụ thuộc.|
|4 C04 HIGH|Desk widget field/scope callbacks khác React safety; two UI routes|React only; Desk chatbot chưa safety-qualified, không cho B1 closure đại diện Desk.|
|5 navigation/deployment|React generic form editable; native v16 `/desk/...` load có conditional seen/view/onload writes; host ≠ serving source|**NEW minimum read-only Lotus invoice reader**, no generic form/native loader fallback; qualify canonical isolated artifact trước enable.|

C02 finance adapter drift chỉ chặn respective future financial tools. C07 read-specific budgets bắt buộc trong new path; C08 selected target/config reproducibility cần qualify, old LLM/cache fixes deferred. C09 full UI refactor deferred; tiny Panel binding variance phải duyệt. Không fix cả chín finding. Missing solution-design reference: **REFERENCE_NOT_FOUND** sau bounded project search.

## Contract và quyết định Chat phải duyệt

First workflow: **generic Sales Invoice search → user select (kể cả một kết quả) → fresh exact-document reauthorization/version check → minimum read-only reader**. Chỉ ID/date/docstatus + optional permitted customer label; không amount/overdue/unpaid, no ERP write/send. “Cần xử lý” phải chọn tiêu chí. V1 overdue source remains blocked; stored Overdue status không đủ financial oracle. Đọc tối thiểu không phải full invoice form.

|Decision|Proposed approval|
|---|---|
|D1 scope|React, Sales Invoice generic L1/L2; no financial semantics/customer-search/Purchase expansion.|
|D2 open UX|Minimum Lotus reader; native/full ERP form cần contract amendment về side effects/identity/route.|
|D3 topology/auth|Existing backend + current-user in-process adapter; chỉ định platform/Work cung cấp canonical fresh isolated target/image/site/map/roles; remote delegation chưa approved.|
|D4 outcome/security|Six statuses, closed reasons, serverCID, source AUTHORIZED_READ (không financial verification); strict projection/opaque purpose-bound signed refs/cursors, fresh permission mỗi lần.|
|D5 limits|Duyệt hoặc thay values trong master: page20/max50, scan100/request,5pages/window, date90/max365, total5s, bytes64KiB, retries0/LLM0/report0; audit/key/TTL và workload/SLO riêng.|
|D6 edits/owners|Duyệt proposed exact NEW paths và tiny binding variance, reviewed fixture lifecycle; Chat owns scope/freeze, Antigravity builds, Work independently qualifies.|

Runtime blockers before enable: canonical source/image/imported module identity; per-site apps/custom hooks/doc/field/mask/read-vs-select rights/revocation; CSRF/cookie/routing/CID delivery; bounded permission query/hard deadline/no-write evidence. SDK compatibility/delegation not proven, no dependency installation. Contract-design PASS không đóng các blockers bằng synthetic test.

## Small batch order và acceptance

|Batch / owner|Scope; dependencies|Required evidence before next enable|
|---|---|---|
|P1-A / Antigravity backend → Work|NEW safe outcome/CID serializer + redacted events, bypass old DTO; D1–D4|Strict outcome/denial/nested errors/HTTP-CID/log sentinel tests, actual hashes/diff/line caps.|
|P1-B / security/backend → Work|NEW context/authorizer/typed requests/ref codec/config/API; P1-A, approved auth/target/key policy|Forged/cross-scope/expired refs, no Admin/mock fallback, delivery auth/CSRF, no invoice read while disabled; real permission tests pending.|
|P2-A / backend → Work|NEW bounded search/open/read port/strict adapter; P1-B + qualified target/API rights|Actual authorized/denied principals/projection/pagination/revocation/caps/no ERP writes, independent oracle, source/runtime/image +cleanup.|
|P2-B / frontend → Work|NEW action client/results/read-only reader, tiny approved Panel binding; P2-A|Isolated search/select/reauth/open/cancel/switch/XSS/CID DOM evidence; existing52 gold +relevant build/type/lint after edits; no old financial transport enable.|
|P2-C / independent Work → Chat|Fresh canonical isolated integration/delivery/performance qualification|Real permission/field/revocation/no-write/outage/cache/worker tests; frozen representative benchmark; exact nonoverlapping PASS/FAIL/NOT_RUN and fixture cleanup. G10 separate.|

Each batch exact proposed paths/tests/exclusions/rollback are in master §9; NEW paths are not existing implementation. No ad-hoc scripts, source<200lines/file, fresh GitNexus impact before edit. Rollback disables new capability/UI only, no ERP migrations/data changes. Không dispatch một prompt sửa all-feature/session/SDK.

**P1 gates:** G0/G1/G2/G3/G4 PASS **contract/discovery**; G5 PARTIAL pending D1–D6. New feature/runtime tests NOT_RUN. G3 financial/G01–G03 legacy session not closed; G10 BLOCKED. Next owner **Chat**: approve/amend selected contract, assign isolated target qualification owner, then issue only P1-A approved batch. Không freeze, triển khai hoặc bật automation từ packet này.

[Source discovery + current hashes](CHATBOT_P1_SOURCE_DISCOVERY_AND_GAP_REPORT.md) · [Principal MASTER_SSOT/schema/budgets/exact batch allowlists](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md).
