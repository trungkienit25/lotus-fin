# LOTUS FIN — P2-A Final Independent Work → Chat

12/10/2026 · Asia/Saigon · Backend Security QA / Frappe Review · Read-only source + offline reproduction.

**CHANGES_REQUIRED · P2A_LIVE_INTEGRATION=BLOCKED · P2B=NOT_READY.** Live permission/HTTP/resource/ERP no-write/cleanup execution **NOT_RUN**. **G10 tiếp tục BLOCKED độc lập.** Không authorization production access, deployment hoặc enablement từ packet này.

Source test chạy mới **276/276 PASS =173 P1 +103 P2-A**. Oracle độc lập mới **84 ca:72 PASS /12 FAIL /0 ERROR**, exit1; ba nhóm lỗi contract chặn backend readiness:

|Finding|Actual reproduction|Cần đóng trước P2-B readiness|
|---|---|---|
|F01, P1 priority|Resolver cùng principal/session/company/policy sinh version khác theo capability. Context→fresh search verify thất bại; search selection→fresh open trả FORBIDDEN/ACCESS_DENIED, doc calls0. Positive search và manually-preserved-version open đều PASS.|Stable read-family scope, fresh capability authorization riêng; không bỏ binding check. Thực thi positive pipeline không ép giữ context_version.|
|F02, P2 priority|get_context thiếu default_posting_from/to; advertised expiry khoảng5s nhưng token còn gần300s.|ContextData đúng MASTER: approved site-local date defaults, expires_at là actual token expiry.|
|F03, P2 priority|DTO nhận missing/null filters/page_size và explicit null date pair. posting_from:null được default thành query90days, gọi port1 và trả OK/RESULTS_FOUND.|Reject explicit null/wrong schema trước read; chỉ omitted date pair/page_size có approved defaults.|

F01/F02 là P2 prerequisites đã ghi trong handoff, còn tồn tại sau self-verification của private core; không coi là P1 regression mới. **P1 173/173 preserved**, original5v1codec methods identical AST. Không reopen B1-S hoặc sửa historical verdict/SSOT.

Actual workspace `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; backend untracked, hai tracked dirty frontend files có trước. **17/17 final builder hashes khớp**; 409 protected source/config/review hashes nguyên sau review. HEAD không đủ định danh source artifact. GitNexus fresh Search/Open/codec LOW, filtersMEDIUM; whole tracked-tree scan **HIGH** tại frontend có trước, không bao phủ untracked backend và không là release all-clear.

Independent read-only serving inspection: image ID `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`, không host source bind, **10/10 selected P1/P2 paths MISSING**. Runtime Python3.14.7 khác host3.13.7. Chưa approved private target/current principal/map/key/audit sink/ordinary-user real permission oracle/lifecycle. Adapter ERP thật chưa tạo/nối; không dùng shared frontend/ai003-verify. Gate live **BLOCKED**, execution **NOT_RUN**, không mock-as-live PASS.

Đã kiểm offline refs/scope/purpose/expiry/retired-key, strict closed projection/extra-RPC fields, complete/PARTIAL nonactionability, exact doc/version/null failure, source/timeout caps, required stream audit/RID/CID và disabled defaults. Actual DocType/document/field/mask/query-hook rights, revocation coherence, HTTP/CSRF/single-message/status/headers, hard SQL/audit deadlines và ERP before/after no-write vẫn **NOT_RUN**. No-write không được báo PASS chỉ vì không gọi ERP.

Chi tiết và reproduction: [Independent Recheck](CHATBOT_P2A_INDEPENDENT_RECHECK.md), [test summary](../evidence/chatbot-p2a-independent-2026-10-12/TEST_SUMMARY.json), [negative ledger](../evidence/chatbot-p2a-independent-2026-10-12/NEGATIVE_RESULTS.json), [source manifest](../evidence/chatbot-p2a-independent-2026-10-12/SOURCE_BEFORE.json), [runtime identity](../evidence/chatbot-p2a-independent-2026-10-12/RUNTIME_IDENTITY.json).

**Return:** `P2A_OFFLINE_INDEPENDENT: CHANGES_REQUIRED`; `P2A_LIVE_INTEGRATION: BLOCKED`; `P2A_READY_FOR_P2B: NOT_READY`.

Đề nghị Chat nhận batch correction F01–F03 và independent offline recheck tiếp theo. Live qualification cần approved immutable private target/permission gold/real request/resource/audit/no-write/cleanup task riêng. Đây là điều kiện đóng gate, không dispatch/authorization. Search/open giữ disabled; không source edit, ERP call/mutation, package install, Docker mutation, commit, deployment hoặc P2-B dispatch trong phiên này. **Dừng sau gate decision.**
