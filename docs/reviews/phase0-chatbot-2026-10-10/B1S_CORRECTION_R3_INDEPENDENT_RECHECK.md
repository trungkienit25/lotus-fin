# B1-S Correction Round 3 — Independent G4B recheck

**Verdict: `B1S_G4B_CHANGES_REQUIRED`; implementation closure `B1S_CORRECTION_R3_PARTIAL`.** F05 đã đóng trong scope: body FORBIDDEN được giữ trước transport timeout. **52/52 case ứng dụng PASS**, gồm nguyên 48 gold, case thất bại Round2 và ba case F05 bổ sung. F07 sửa được direct Node ownership/normal teardown và unknown API, nhưng còn **bốn FAIL native qualification**; chưa đủ đóng G4B.

Revision ngày 2026-10-10, nối tiếp [Round2](B1S_CORRECTION_R2_INDEPENDENT_RECHECK.md), không thay lịch sử bằng current facts. Review một agent, chỉ inspect/audit/E2E cô lập và ghi evidence; không sửa application/native test, backend, permission, commit, dispatch hay deploy.

## Scope, revision và lineage

Branch `develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; implementation uncommitted. [SOURCE_BEFORE](../evidence/b1s-g4b-correction-r3-2026-10-10/SOURCE_BEFORE.json) mới là identity của artifact được test. So Round2, hook và Python test đổi, builder report append; normalizer, renderer, Panel, Drawer, fixture/package/lock giữ nguyên. [Revision diff](../evidence/b1s-g4b-correction-r3-2026-10-10/R2_TO_R3_DIFF.patch).

Full-file lines: hook173, normalizer149, renderer57, Panel545, Drawer55, Python test257, fixture main169/config29/html12, report326. New production dưới200; Panel variance giữ nguyên; test dưới cap320 đã được user duyệt. Current report đã đính chính preserved hashes/line counts. Hook SHA256 `97365EA11F0CB06BE0C3A15435453DF99F1C5FD50AB31FCCC5AAB8E77584BE76`; test `59B2640EF767225605DFAE0ED9FABE15EE9167B7F56CDDA4268C783E07782609`.

333 protected paths khớp Round2. 189 historical raw hashes và chín historical deliverables không đổi. Reviewer giữ nguyên 12 selected fingerprints và tracked diff trước/sau. Unrelated dirty/untracked work không bị quy cho Antigravity hoặc sửa. Không cập nhật F102 vì không có fact/gate F102 mới.

GitNexus context hook dùng exact cached CLI, bounded10s, trả notfound. Index `316c5bd…` từ2026-10-02, chậm HEAD61 commits; stale/UNKNOWN vẫn unresolved. Dùng static fallback trong scope được user cho phép, không refresh/download; không kết luận symbol dead hoặc graph safe. Không edit symbol/commit; người sửa sau vẫn phải impact trước edit theo AGENTS.

## Actual tests

Private frontend/fixture copy dưới TEMP, 11 source/package/lock hashes khớp; copy dependencies sẵn có, không install. Node22.19.0/npm11.7.0, Python3.13.7/pytest9.0.2/Playwright1.58.0/Chromium1208. [Environment](../evidence/b1s-g4b-correction-r3-2026-10-10/ENVIRONMENT.json), [nine build hashes](../evidence/b1s-g4b-correction-r3-2026-10-10/BUILD_ARTIFACT_MANIFEST.json). Đây là source/private browser lineage, không immutable image/site/worker/HTTP lineage.

| Kiểm tra đã chạy | Actual |
|---|---|
| Typecheck; Vite build sau typecheck | PASS/exit0 cả hai; chạy một lần |
| Targeted Oxlint, năm production files | Exit0, 5 warnings; không clean-code PASS |
| Current supplied suite + reviewed lifecycle wrapper | 4 PASS/pytest0 |
| Current suite + native server fixture không override | 4 PASS/pytest0 |
| Byte-exact original golden suite | 3 PASS/pytest0 |
| Independent application DOM/hook | 52 PASS/0 FAIL; original48 giữ expected |
| Exact fixed-message assertions trên evidence đã capture | 32 PASS; không thêm case/request |
| Native qualification records | 13 PASS/4 FAIL/0 BLOCKED; tính riêng |

Suites có overlap, không cộng thành total application cases. Actual Page/router/Company A→B, Drawer, pending success/failure/loading races, reset/unmount, CID/XSS và production zero Copilot POST đều được kiểm tra bằng actual production imports với synthetic transport. Không suy ra backend/financial authority từ các PASS này. [Ledger](B1S_CORRECTION_R3_TEST_RESULTS.json), [DOM](../evidence/b1s-g4b-correction-r3-2026-10-10/DOM_RESULTS.json).

F05 reuse normalizer trong catch trước timeout branch, sau stale/intentional cancellation fencing. `ETIMEDOUT + HTTP500 + nested FORBIDDEN` → FORBIDDEN thật qua hook; timeout-only, HTTP403, generic network, intentional cancel và CID giữ PASS. Native fixture case cùng tên chỉ inject HTTP500/body, không Axios ETIMEDOUT; independent reproduction mới chứng minh precedence.

## Remaining F07 findings — test infrastructure, priority MEDIUM

| Finding/root cause | Reproduction và actual | Acceptance cần đạt |
|---|---|---|
| F07-N1: chỉ route `**/api/**`, không fail unexpected non-API outbound | OUTBOUND: reviewer abort `https://reviewer.invalid/outbound-probe` trước connect, native pytest vẫn0 | Native tự record/deny và pytest1 |
| F07-N2: không observe/fail unexpected WS | WS: reviewer intercept `wss://reviewer.invalid/ws-probe` không upstream; native pytest0 | Native record/deny và pytest1; phân biệt local HMR |
| F07-N3: substring endpoint allowlist | ALIAS: local `/api/method/not_declared_chat_copilot` nhận200, pytest0 | Exact origin/path/method fixture registry; unknown alias abort/pytest1 |
| F07-N4: readiness trước `try/finally` | SETUP fault sau actual Popen: owned Node6812 còn LISTENING5188 | Spawn/readiness/timeout/yield đều trong owned cleanup; wait exit + released port |

[NATIVE raw/reproduction](../evidence/b1s-g4b-correction-r3-2026-10-10/REPRODUCTION.md). Không external traffic từ probes: containment do reviewer cung cấp, không ghi nhận thành native PASS. Setup case là controlled readiness exception với actual owned process, không natural outage. Reviewer xác minh command line/PID6812 rồi dừng đúng process đó; không kill shared PID.

Native unknown API đã abort và pytest1 vì unexpected-request assertion: negative qualification PASS. Native NORMAL listener PID11656 đúng direct owned Node; normal completion và assertion-failure retry PID15080 cleanup/port release PASS. Foreign-listener refusal trước spawn PASS, sentinel untouched. Service workers block được giữ trên native pages. Source vẫn thiếu native listener-PID/poll assertion; status-only wait có thể đọc case cũ; native chưa cover actual Page/races/actual timeout như independent gold. Đây là static coverage gaps, không phát minh thêm application FAIL.

Initial API qualification đạt native negative assertions/cleanup nhưng reviewer redundant Browser.close gặp closed event loop trước serialize. Giữ stdout/stderr/JUnit/partial; một API-only retry sửa wrapper close handling, không đổi native source/assertions, [API_RETRY](../evidence/b1s-g4b-correction-r3-2026-10-10/API_RETRY_RESULTS.json) thành evidence cuối. Không tính lỗi wrapper này thành product finding.

## Gate matrix và handoff

| Gate | Current scope |
|---|---|
| G1 | PASS narrow source/environment identity |
| G2 | PASS tested B1S application contract; financial authority/budget NOT_RUN |
| G3 | PARTIAL: production0POST/no verified numeric widget; financial qualification NOT_RUN |
| G4A | FAIL: bốn native F07 records |
| G4B | CHANGES_REQUIRED |
| G10 | BLOCKED riêng, unchanged |
| G01–G03 | NOT_CLOSED |

NOT_RUN: real ERP/LLM/financial truth; backend permission/session/cross-user/site/product; deployment/image; payload-size, SQL counts, p95/throughput/RSS; real ERP timeout-after-commit/UNKNOWN_OUTCOME. Không dùng Docker/shared frontend/shared site, không gọi business mutation. Lotus Fin và ERPNext là hai product identities riêng; Round3 không mở lại SDK/topology/B0/V1. FinTechathon Shenzhen demo chưa được chứng nhận financial chatbot automation.

Đề xuất một batch test-only F07: exact fixture/network/WS accounting; cleanup bao trùm setup với verified owned PID; generation-specific waits và giữ golden assertions. Recheck native negatives +52 gold +targeted checks. Không sửa hook/normalizer/UI đang PASS nếu không có regression mới. Nếu vượt approved paths/cap320, báo SCOPE_CHANGE_REQUIRED. Chat quyết định batch; reviewer không freeze hoặc dispatch. [Short packet](B1S_CORRECTION_R3_WORK_TO_CHAT.md).

[Cleanup](../evidence/b1s-g4b-correction-r3-2026-10-10/WORKSPACE_CLEANUP.json): private copy removed, owned Node0, port5188 released, known Playwright Chromium0. [Raw hashes](../evidence/b1s-g4b-correction-r3-2026-10-10/RAW_EVIDENCE_HASHES.json) và [deliverable hashes](../evidence/b1s-g4b-correction-r3-2026-10-10/DELIVERABLE_HASHES.json) đóng evidence của lượt này.
