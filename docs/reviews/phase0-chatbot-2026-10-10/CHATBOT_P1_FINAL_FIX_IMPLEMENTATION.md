# P1 Final Direct Fix — Implementation, 2026-10-12

**P1_FINAL_FIX_LOCAL_PASS; P1A_LOCAL_PASS; P1B_LOCAL_PASS.** Đây là builder/local verification sau khi trực tiếp sửa, không phải independent acceptance. Không còn material blocker tái hiện trong approved offline matrix. Đã thực hiện tuần tự F04 → F01 → F02/F03, mỗi phase có RED trước source edit và GREEN trước phase tiếp theo.

## Source và authority

`develop` @ `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; HEAD/branch không đổi, staged rỗng, không commit/push. P1 source vốn untracked trước đợt này: HEAD không đủ định danh artifact. Evidence root: `docs/reviews/evidence/chatbot-p1-final-direct-fix-2026-10-12/`. `SOURCE_BEFORE.json`, `SOURCE_CONTENT_BEFORE.json`, `SOURCE_AFTER.json`, `ACTUAL_SOURCE_DIFF.patch.txt` chứa actual working-tree identity và exact diff. Dirty Panel/Drawer giữ nguyên.

Áp dụng P1 MASTER SSOT §3/§5/§6, ADR001, Security Code V3, closure decision/final audit hiện hữu; kỹ năng đọc từ `my-skills`: systematic-debugging, test-driven-development, clean-code, verification-before-completion. Không freeze/update hợp đồng.

GitNexus cached1.6.12, index `316c5bd32197b35f01873f8ae463051f88b37ee5` stale61commits. Upstream impact của scanner/codec/controller trả exit1/UNKNOWN, không chứng minh unaffected. Đã cảnh báo boundary authorization/delivery nhạy cảm trước edit và corroborate static caller theo ngoại lệ user cho phép. Impact test fixture cũ cũng UNKNOWN, text tracing chỉ thấy pytest entrypoint. `GRAPH_IMPACT.json` giữ limitation; không tải tooling/index hoặc commit.

## F04 — denial policy đóng và có giới hạn

`scan_for_nested_denial` lấy đủ năm reason từ `STATUS_REASON_MATRIX[FORBIDDEN]`, duyệt dict/list bằng stack, max depth16 và budget4096node; kiểm tra container trước expansion. Recognized denial thắng OK/PARTIAL. Unsupported shape/status/reason, non-finite float và vượt budget fail closed. Domain/final DTO tái dùng policy, không dispatcher mới.

Construction/DTO từ chối denial bằng validation. Terminal boundary controller revalidate mutated outcome trước serialize: nested denial thành403/FORBIDDEN/ACCESS_DENIED, data/source null; invalid success thành502/SOURCE_ERROR/INVALID_PROVIDER_RESPONSE, safe allowlist message. Benign OK/PARTIAL vẫn200, PARTIAL không cấp selection_ref.

RED16FAIL/14PASS; GREEN71/71. Lần GREEN đầu domain204dòng bị ADR check phát hiện: đã rút header/spacing, giữ container bound và chạy GREEN-ADR71/71, source198dòng trước khi chuyển F01. Shared DTO/response không sửa.

## F01 — public actor binding kín

Codec dùng keyed HMAC-SHA256 với domain prefix `actor_binding:v1:` và `aref_` full digest, constant-time actor comparison; opaque session cũ giữ nguyên. MAC bảo vệ required `binding_version=opaque-actor.v1`, `projection_version=invoice.min.v1`, purpose/key/expiry cùng actor/session/site/product/company/connection/config/context/projection/document binding.

Wire prefix `ref.v1` giữ nguyên; payload schema mới bắt buộc version/projection. Signed legacy payload raw actor/thiếu field bị từ chối, không migration/fallback. Signature không thay fresh authorization. Synthetic codec tests open/cursor không bật use case.

RED6FAIL/8PASS; GREEN42/42: public decode qua actual qualified offline controller không raw actor/email/SID/key, log không token; wrong actor/company/config/projection, tamper/expiry/purpose/key và legacy claims fail closed.

## F02/F03 — terminal boundary duy nhất

Thêm đúng một helper `presentation/response/invoice_action_delivery.py`56dòng, caller production duy nhất `InvoiceActionsController`. Helper sanitize server CID, build typed failure, revalidate/serialize và ghi required terminal event. Controller117dòng; không generic framework hoặc owner audit thứ hai.

Invalid context, disabled search/open, Guest/Company denial, authorized context và disabled config đi cùng boundary. Valid UUID4 request_id echo nguyên; missing/malformed ID thay UUID4, NOT_AVAILABLE thành INVALID_REQUEST; root FORBIDDEN giữ denial. CID là tham số nội bộ server, không lấy request body; bad internal CID thay UUID4, header/body/event đồng nhất.

Healthy admitted terminal response: đúng1 RESPONSE_DELIVERY event acknowledged, chỉ safe metadata. Missing sink: không admission,503/CAPABILITY_DISABLED/null, không claim recorded event. Unhealthy/unqualified sink: safe ActionEventDeliveryError propagate,1attempt/0ack, không retry/recursive logging/protected OK. Chưa hứa HTTP status cho exception khi chưa live HTTP qualification.

A16 adapter và B03 exact Company authorizer giữ nguyên byte/hash. Search/open vẫn disabled, zero business reads, không legacy fallback.

RED-valid-CID21FAIL/6PASS; GREEN27/27. RED đầu có bad-CID fixture gây nhiễu positive case: giữ raw evidence nhưng tách CID case và chạy lại RED trước production edit. Hồi quy gặp1failure do test disabled cũ gửi thiếu ID; chỉ thêm valid UUID4 cho hai input, giữ nguyên hai assertion503/CAPABILITY_DISABLED. Missing/sai ID được kiểm tra422 riêng. Affected regression cuối102/102.

## Scope, self-audit và giới hạn

Sửa3primary production modules; thêm1cohesive helper và4focused test modules; thay2input trong1test cũ. AST mọi original assert/pytest.raises trong8historical test files giữ nguyên. Đối chiếu676protected files, ngoài approved source không đổi;3484historical review artifacts giữ nguyên. Hai root implementation reports chỉ append factual local results. API/legacy/financial/B1-S và SSOT không sửa.

Final focused173/173 PASS =86historical+87new. Separate probe reruns: Track A22/22, B14/14, A16 14/14, B03 8/8, F01–F04 findings8+controls3=11/11. Không cộng overlapping probes vào unique coverage. Actual logger/ack/redaction, source-evidence mutation, CID/header, import/syntax, ADR<200, preservation đều đạt.

Không ERP/LLM/public network, process/service/Docker/site/data/permission mutation, installs, ad-hoc runtime .py hoặc deploy. Private Python processes exit; fixtures close handlers/owned threads, restore shared logger state và gỡ framework double.

`P1B_LIVE_AUTHORIZATION=NOT_RUN`; `G10=BLOCKED` riêng. Live HTTP/auth/CSRF/ERP document rights không suy ra từ doubles. B1-S historical PASS preserved, browser NOT_RUN. Lotus Fin là sản phẩm riêng với ERPNext target. Dừng tại local contract GREEN, không P2-A hay invoice enable. Independent acceptance còn pending.


## Exact source SHA256 (under lotus_fin/lotus_fin)

| File | Lines | Before | After |
|---|---:|---|---|
| domain/schema/action_outcome.py | 198 | 0fa95bc9fba8073350c3189c7e055bdae56f579b39d780f508d2e94baf9f147d | bf90ca6b85743b7152a9b749528240c9c48d48a39e4682c18e674adf78fc2bb9 |
| infrastructure/security/action_reference_codec.py | 147 | e5297a037017852afaae1afea9223ead30be328ee4808e0adf2a68d357c8e3dd | 9270cd467ca795185db8b5f5c8df7fa0158d977e32aa78b8fca54cbfaf2bd009 |
| presentation/controller/invoice_actions_controller.py | 117 | 88dd38b38529200d47e6bbaff047373b1d3dc34c374331d3ce9095be8f75ce31 | bbfe06b870d7b5f67621f89f4101e128d8ed6b2190595fef7f9ed51a5a603d3a |
| presentation/response/invoice_action_delivery.py | 56 | NEW | 0bfdd70dfb485b3f415bcf3da54b80d531b41f0e35a0f5cdd4d05cd131ed8c84 |
| tests/test_action_denial_policy.py | 72 | NEW | daf02b869f337d092854222782000cadda3f0aaffb559fed9f612a15a52a3c37 |
| tests/test_action_reference_privacy.py | 112 | NEW | 53269b85217f6db43736e66d2c4cf3e6c5285a465c1a9eb88bffaea1a65c46a1 |
| tests/test_invoice_auth_delivery.py | 116 | 42989a2e826dccc0e2c29b7333f9407222d137b9de076989c1f9799e7a2f533a | 8bc29f6f40bfaffcd786535f44c902c197629c9fba4b6423230acdd2d26ac114 |
| tests/test_invoice_delivery_boundary.py | 66 | NEW | 42d509429010e36a114a064d8a3f491675e8dad6a84bad73e5168649b90d73fe |
| tests/test_invoice_terminal_delivery.py | 144 | NEW | 6de1d7adb9a84ed831deee25a79abeb3fb36cd2e4e67007339e9f309085ee1b8 |
