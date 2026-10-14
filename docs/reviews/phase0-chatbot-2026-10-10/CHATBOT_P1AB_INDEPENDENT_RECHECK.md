# P1-A/P1-B combined independent recheck

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026 · Independent Security QA / Senior Backend Reviewer.

**P1-A: P1A_CHANGES_REQUIRED. P1-B: P1B_CHANGES_REQUIRED. Combined acceptance: BLOCKED.** N01–N12 nay đều PASS, nhưng F01/F02/F04 chưa đóng hoàn toàn. P1-B có các vi phạm security được tái hiện độc lập; không đạt P1B_OFFLINE_CONTRACT_PASS, không suy ra P1B_LIVE_AUTHORIZATION_PASS. Chat chưa thể đóng P1-A hoặc chấp nhận P1-B target readiness. **Không invoice search/open/action nào được bật.**

Review đúng hai batch source/offline; không broad ERP audit, sửa source/test, freeze SSOT hoặc dispatch P2-A. Lotus Fin là sản phẩm riêng; ERPNext là target/platform tích hợp, chưa được qualification ở lượt này.

Authority: [P1 MASTER §3–6/9](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md), [prior independent review](CHATBOT_P1A_INDEPENDENT_RECHECK.md), current [P1-A report](E:/lotus-fin/CHATBOT_P1A_IMPLEMENTATION_AND_EVIDENCE.md), [P1-B report](E:/lotus-fin/CHATBOT_P1B_IMPLEMENTATION_AND_EVIDENCE.md), [ADR001](E:/lotus-fin/docs/adr/001-clean-architecture-core-first-adr.md), [Security Code V3](E:/lotus-fin/docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md), [AGENTS](E:/lotus-fin/AGENTS.md). P1 MASTER vẫn PROPOSED/NOT_FROZEN; review không thay trạng thái đó.

## 1. Artifact, dirty tree và scope

**develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2**, staged empty. Existing tracked dirty chỉ Copilot Panel/Drawer,74 insertions/267 deletions. 641 tracked fingerprints và exact unstaged binary-diff hash bằng independent P1-A baseline trước: aggregate SHA256 c751a0b4a1b1f8e48cf47aae91dfe1afb76022b08ad2258bc21c9b3a537a8d84; diff SHA256 09344d31c5b694e62eb399cc6461a6388ea77c330fbf1943b127b4f3c56fd3eb.

Relevant current additions đều untracked: P1-A5 production/3 tests, P1-B9 production/3 tests, hai root reports. Prior seven P1-A source/tests có hash thay đổi so với prior review; security regression test mới. P1-B9+3 source/test additions đúng paths §9. Không quy9,761 untracked lúc bắt đầu cho Antigravity; phần lớn inventory có sẵn.

[SOURCE_BEFORE.json](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/SOURCE_BEFORE.json) chứa status, từng path/SHA256/line count của20 source/tests +2 reports,641 tracked và2,603 historical review files. [TRACKED_DIFF.patch.txt](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/TRACKED_DIFF.patch.txt) giữ diff thực tế.

All20 source/test files **35–189 lines including blanks**, đạt ADR cap. Không phát hiện package/lock/dependency/shared security/legacy financial change trong tracked scope đã bảo vệ. Không có historical hash baseline cho mọi unrelated untracked file; không chứng nhận chúng chưa từng được sửa.

Current P1-A response SHA256 **2e7878d8ce709662e95f3ac72545be2ac8400454dfb0e94e6efd160e2b5214c2** khác correction report P1-A 178fd44…. Đảo riêng điều kiện line109 từ “client_request_id is not None and was_replaced” về “was_replaced” khớp chính xác hash cũ: một-line delta đã xác minh. P1-B report ghi hash hiện tại nhưng không giải thích scope/rationale của P1-A delta. Missing ID nay có thể giữ CAPABILITY_DISABLED thay INVALID_REQUEST; API cũng chưa echo ID.

P1-A report nói new regression file có “approved Chat exception”; review xác nhận file/cap nhưng không có approval artifact riêng trong evidence đã đọc. Latest user explicitly yêu cầu kiểm correction hiện tại; không dùng gap này làm blocker độc lập.

Old18 regression intents còn representation: null data/source, matrix/version/extra fields, UUID/header/status, fixed failure message và event recording; parametrization tăng coverage. Tuy nhiên test mang tên sentinel tokens/cookies/passwords nay chỉ dùng benign enum values, không giữ nguyên literal redaction assertions. Closed-stage/privacy N08–N10 kiểm actual logger bù confidentiality; không tuyên bố byte-for-byte preservation của old untracked tests vì snapshot cũ chỉ giữ hashes/results.

[Source verification](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/SOURCE_VERIFICATION.json):20 AST/compile checks PASS;14 actual imported production module paths/hashes khớp workspace source;22 source/report hashes không đổi trong execution. [After manifest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/SOURCE_AFTER.json) bảo vệ historical evidence và R7.

GitNexus graph-first query/context dùng installed cached1.6.12 runner: query exit0, graph **61 commits stale**, context InvoiceActionsController notfound/exit1. New flows UNKNOWN; query output tool-truncated, không là clean graph proof. Bounded static tracing tiếp tục theo user authorization; không refresh/download tooling. Local wrapper bị EPERM trước khi cached runner thành công. [Graph evidence](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/GRAPH_EVIDENCE.json). No function edit/commit; correction sau cần fresh impact trước sửa.

## 2. Execution và counts thực tế

Host C:/Python313/python.exe, Windows11 build26200, Python3.13.7/Pydantic2.12.5/pytest9.0.2/pluggy1.6.0. Không install. Docker NOT_USED; không lấy container/site cũ làm tested runtime.

|Execution|Actual result / exit|Boundary|
|---|---|---|
|Existing six focused pytest modules|**55/55 PASS**, exit0,0.96s: P1-A12+15+10=37, P1-B6+6+6=18|Current source only; no ERP conftest.|
|Independent original N01–N12|**12/12 PASS**|Rejection, safe final delivery, actual logger privacy, injected throwing sink.|
|Remaining P1-A A13–A16|**0 PASS /4 FAIL**|Final provenance, PARTIAL denial, success message, actual stdlib sink outage.|
|P1-B independent B01–B14|**7 PASS /7 FAIL**|Context, MAC/binding, credentials, audit, disabled admission, declarations.|
|Controls C01–C06|**6/6 PASS**|UUID/header, ID replacement, literal matrix, denial precedence, actual logger positive event, isolation.|
|Independent ledger total|**36 check groups:25 PASS /11 FAIL /0 ERROR**; main probes exit1, real-sink follow-up exit1|Không cộng55+36 thành unique coverage; nhiều checks overlap existing tests.|
|Literal matrix C03|24 allowed +120 rejected pairs;0 mismatches|Subchecks của một control, không144 additional tests.|
|20 syntax /14 import identity checks|PASS, exit0|Không phải functional cases hoặc runtime permission proof.|

Raw [pytest text](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/FOCUSED_PYTEST.txt), [pytest cases/invocation/exits](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/FOCUSED_PYTEST.json), [independent assertions/actuals/hashes/runtime](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/INDEPENDENT_PROBES.json).

Reproduction: [pytest stdin](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/FOCUSED_PYTEST_REPRODUCTION.txt), [probe stdin](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/INDEPENDENT_PROBES_REPRODUCTION.txt), [real sink stdin](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/REAL_SINK_REPRODUCTION.txt). Raw non-executable evidence, không tạo runtime script.

Actual invocation: python -B - via PowerShell stdin; PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; prepend root/lotus_fin to sys.path; pytest.main với -p no:cacheprovider --noconftest -v, sáu explicit paths và Recorder. Probe scripts cùng source path, independent guards trước import. Source/tests/oracles không sửa.

Containment: Python audit hook denies socket connect/connect_ex/bind/getaddrinfo; MetaPath denies real Frappe/ERPNext/provider/legacy imports. Successfully loaded real framework imports0, network attempts0. Nine framework import attempts bị deny trong pytest và three trong main probes; caught imports được ghi nhận. Controlled fake frappe chỉ trong process memory cho permission/admission spies, removed trong finally. Fake invoice get_doc/get_list/get_all tripwires measured0 ở disabled paths. Không listener/Node/service được spawn; không cleanup process/file ngoài review artifacts.

Pytest warnings/assertion failures: none. Manifest preparation ban đầu UnicodeDecodeError trên unrelated binary rồi thành công bằng manifest reader sửa decoding; không đổi source. Capture combined command evidence gặp Windows command-length limit, sau đó lưu raw qua patch tool. Git status cảnh báo inaccessible existing pytest-cache directories; không claim inspect ignored contents. Actual StreamHandler outage có captured stderr “Logging error”, là failed security delivery assertion A16, không pytest warning hay PASS.

## 3. Track A — closure của original counterexamples

|Probe|Current actual|Status|
|---|---|---|
|N01|OK with INCOMPLETE rejected|PASS|
|N02|Malformed date và invalid IANA timezone independently rejected|PASS|
|N03|PARTIAL with actionable selection_ref rejected|PASS|
|N04|OK chứa declared FORBIDDEN/ACCESS_DENIED rejected|PASS|
|N05|Mutated failure data/source stripped;403, no canary|PASS|
|N06|SOURCE_ERROR raw message replaced;502 safe template|PASS|
|N07|Direct DTO rejects version/status/reason/capability separately|PASS|
|N08–N10|Raw session/email/provider-stage rejected before actual StringIO logger; zero leaked/recorded events|PASS each|
|N11|Invalid event CID/request/capability/matrix independently rejected|PASS|
|N12|Injected logger.info throws OSError → typed error, recorded_events0|PASS|

N01–N12 không hoàn tất broader F01/F02/F04. Bốn bounded checks dưới đây cùng invariants đã yêu cầu, không mở scope architecture/scale:

|Finding / severity / exact source|Reproduction và actual violation|Smallest correction|
|---|---|---|
|**A-F01 HIGH — final provenance/message chưa closed** [DTO:38](E:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/action_outcome.py:38), [serializer:138](E:/lotus-fin/lotus_fin/lotus_fin/presentation/response/action_response.py:138)|A13: valid source sau đó assigned observed_at=not-a-date, verification=FORGED →200/OK forwards both. Direct DTO nhận source chỉ có coverage=PAGE_COMPLETE. Coverage được check nhưng full SourceEvidence không được validate tại delivery. A15: OK user_message chứa OperationalError/session canary →200 exposes raw text; template enforcement chỉ failures.|Một authoritative full source validator tại final boundary kể cả model mutation; mọi terminal message bounded/fixed theo code. Invalid source reject/map safely, không fabricate success; không build invoice logic.|
|**A-F02 HIGH — PARTIAL che denial** [domain:184](E:/lotus-fin/lotus_fin/lotus_fin/domain/schema/action_outcome.py:184), [DTO:79](E:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/action_outcome.py:79)|A14: PARTIAL/INCOMPLETE data chứa nested FORBIDDEN/ACCESS_DENIED/private canary; construction/serializer200/PARTIAL với protected data. Denial scan chỉ chạy cho OK, trái §3 aggregate precedence.|Reject/normalize recognized denial trước cả hai success branches; không protected PARTIAL sau denial. Giữ source/selection-ref checks; không generic business dispatcher.|
|**A-F04 HIGH — actual sink outage falsely recorded** [record_event:36](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:36)|A16: actual logging.Logger + StreamHandler stream.write throws OSError. Standard handler handles exception internally; logger.info returns, adapter records1 event, không typed error. Captured stderr Logging error. Throwing fake N12 không qualify supported actual logger path.|Required sink phải communicate failure/acknowledgment; logger.info return không chứng minh delivery. Thêm real failing-handler/no-false-record qualification, một sink policy, không general audit platform/financial ledger.|

F03 privacy/closed metadata current PASS ở construction/logger boundary đã chạy. F05 line-cap correction current PASS; scope/history caveats ở §1. F01/F02/F04 **partially corrected, materially open**, không blanket inherit old FAIL.

## 4. Track B — independent security outcomes

|Probe|Actual|Status|
|---|---|---|
|B01|Guest denied; absent framework/principal denied|PASS offline|
|B02|Missing SID → authorized context dùng auth_session_default|FAIL|
|B03|Fake Company/doc permission denies, resolver vẫn authorized, document method DOCUMENT_READY; permission checks0/invoice reads0|FAIL|
|B04|Tampered MAC/wrong purpose/expired ref/wrong key rejected|PASS|
|B05|Actor/session/site/company/context-version changes rejected; product/connection-ID/connection-version changes accepted với same context_version|FAIL|
|B06|Actual config v1→v2 giữ context_version; old signed token vẫn verifies|FAIL|
|B07|Public context_ref base64 exposes exact synthetic raw session binding; signing key absent|FAIL|
|B08|events_port=None + enabled context →200/OK/ref, không required sink|FAIL|
|B09|Provided throwing sink → typed error, history0, no successful return|PASS cho fake; A16 chặn general delivery claim|
|B10|Unknown config/missing key rejected; default disabled, unmapped site denied|PASS|
|B11|Forged actor/site/session fields →422/INVALID_REQUEST/null data|PASS|
|B12|Search/open CAPABILITY_DISABLED, disabled context503/null; measured fake invoice reads0|PASS|
|B13|Whitelist-registration spy không ghi methods; supplied valid request_id không echoed|FAIL|
|B14|Direct fake Guest POST/actor GET không protected data; status_code attribute401/405|PASS direct-call, không live HTTP/CSRF/status proof|

|Finding / severity / exact source|Root cause và bounded correction|
|---|---|
|**B-F01 HIGH — permissive auth/synthetic session** [SID:86](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:86), [Company:100](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:100), [document:139](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:139)|Missing SID thành default authority. Connection allowlist + non-Guest thay current actor Company/capability rights. Document method chỉ equality actor, bỏ document/company/site/session/rights. Bỏ synthetic binding; fresh trusted binding required. Config không phải permission proof. Strict unavailable/denied cho seam chưa qualified, không placeholder DOCUMENT_READY. Không thêm invoice reads vào P1-B; test injection chỉ explicit test composition, không Admin/global impersonation.|
|**B-F02 HIGH — ref/config binding thiếu** [fingerprint:109](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:109), [verify:123](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/action_reference_codec.py:123)|Claims có product/connection nhưng verifier không compare; connection_version thiếu trong claims/fingerprint. B06 chứng minh actual config-switch bypass, hơn altered-model case. Bind/verify full trusted product/site/connection/config/projection/contract; canonical fingerprint. Giữ MAC/purpose/key/expiry, fresh permission checks; signature không cấp quyền.|
|**B-F03 HIGH — signed ref lộ session credential** [claims:23](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/action_reference_codec.py:23), [sign:55](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/action_reference_codec.py:55)|HMAC đảm bảo integrity, không confidentiality. Raw SID copied vào public base64 claims; decode controller response lấy synthetic SID. Không dùng/output live credential. Dùng trusted purpose-bound keyed/opaque actor/session refs; không raw cookie/SID/email trong claims/logs; không cần session store mới.|
|**B-F04 HIGH — required sink optional** [constructor:34](E:/lotus-fin/lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py:34), [record:50](E:/lotus-fin/lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py:50)|events_port=None bỏ mọi event nhưng enabled context vẫn issues ref. Missing/unhealthy sink phải fail admission safely trước success/ref, áp dụng corrected P1-A sink policy. Disabled/invalid paths cần bounded compatible observability; không broad infrastructure expansion.|
|**B-F05 MEDIUM — API declaration/compatibility gap** [helper:12](E:/lotus-fin/lotus_fin/lotus_fin/api/invoice_actions_api.py:12), [exports:45](E:/lotus-fin/lotus_fin/lotus_fin/api/invoice_actions_api.py:45)|Ba plain functions không whitelist/allow_guest=False/method metadata; bounded hooks/API search không thấy registration khác. AST/spy xác nhận no registration. API không compose controller/audit/config, bỏ valid request ID; manual denial untyped/no CID, auth/header exceptions catch/pass. Return tự bọc message cần actual framework qualification. Thêm một disabled authenticated POST composition/decoder theo P1-A CID/outcome/audit; search/open inert. Không claim actual double-envelope/HTTP status failure từ fakes.|

Typed frozen context và strict extra-forbid request DTOs có sẵn. Không implicit Administrator/set_user/ignore_permissions/get_all call, AgentRunner/global chat session/old ChatResponseDTO/legacy fallback wiring trong new source. Static/actual host imports xác nhận isolation, không runtime authorization. Codec purpose checks PASS; không reference nào bật invoice execution. Không missing-provider/config demo rows; no real invoice read/write.

## 5. Gate matrix và NOT_RUN

|Gate|Independent current decision|
|---|---|
|P1-A outcome/security/CID/logging|**CHANGES_REQUIRED**: N01–12/CID/privacy positives; A13–16 material failures.|
|P1-B typed context/authorization|**CHANGES_REQUIRED**: B02/B03; frozen model không phải authority.|
|P1-B reference integrity/privacy|**CHANGES_REQUIRED**: B05/B06/B07 dù MAC/purpose rejection đúng.|
|P1-B disabled API/admission/compatibility|**CHANGES_REQUIRED**: B08/B13/A16; search/open disabled.|
|P1-B source isolation/ADR|PASS trong protected scope đã xem;20 files dưới cap. P1-A one-line delta/approval-history caveats ở §1.|
|Combined acceptance|**BLOCKED** do P1-A prerequisite và P1-B violations.|
|P1B_OFFLINE_CONTRACT_PASS|**NOT_EARNED — P1B_CHANGES_REQUIRED**.|
|P1B_LIVE_AUTHORIZATION_PASS / ERP target|**NOT_RUN / BLOCKED**, không infer từ fakes.|
|B1-S R7 prior PASS|**Preserved**,13/13 R7 source hashes match; không rerun/current-runtime requalification.|
|G3 financial context|Unqualified/BLOCKED; invoice identity contracts không qualify finance.|
|G01–G03 backend/session|Không closed bởi offline tests; unchanged scope.|
|G10 judge deployment|**BLOCKED independently**; không deployment/site/browser acceptance.|

Native B1-S/gold, unrelated financial suites, broad SDK/architecture, live auth/CSRF/decoder/status/headers, actual ERP Company/doc/field/revocation, cache coherence, concurrency/p95/throughput/RSS và serving image lineage **NOT_RUN**. Bounded source impact; chưa isolated qualified target baseline; không bật invoice reads. Không runtime/performance PASS từ0.96s unit suite.

Target prerequisites: sửa/recheck material defects trước; approve exact trusted Lotus→ERP site/product/connection-version map, installed image/module/app/custom-hook lineage, real principal/Company/invoice/field/revocation oracle, purpose/key policy (withheld secrets), required observable sink và fresh private fixture/snapshot baseline/lifecycle/cleanup. Actual qualification phải kiểm authenticated POST/Guest/GET/CSRF, decoding limits/duplicate keys, single envelope/CID/no-store/error delivery và deny-before-read. Không dùng ai003-verify/shared frontend, Docker mutation hoặc ERPNext test helpers.

## 6. Handoff

Chat **không đóng P1-A**, **không chấp nhận P1-B offline/target readiness** ở revision này. Batch kế tiếp đề xuất: bounded A-F01/A-F02/A-F04 corrections, rồi B-F01–B-F05, exact allowlist/minimal supporting-boundary variance được duyệt trước sửa, fresh graph impact. Giữ55 assertions và independent failing cases; qualify actual sink/declarations, không chỉ throwing fakes.

Sau independent offline closure và riêng target prerequisites, Chat mới xét P2-A authorized Sales Invoice search/select/open: bounded permission-aware minimal projection, fresh exact-document auth, signed selection/version/source. Không amounts/overdue/write/SDK/LLM/legacy migration; không automatic implementation dispatch. [Work→Chat packet](CHATBOT_P1AB_WORK_TO_CHAT.md).

