# Work → Chat — B1-S Correction Round 3

2026-10-10 / independent audit + isolated E2E / FinTechathon Shenzhen. **B1S_G4B_CHANGES_REQUIRED; B1S_CORRECTION_R3_PARTIAL.** Không freeze/dispatch implementation.

`develop` HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, uncommitted; [current SHA256](../evidence/b1s-g4b-correction-r3-2026-10-10/SOURCE_BEFORE.json) là artifact identity. Round2→3 chỉ hook/test/report đổi. Reviewer không sửa application/test/backend/permissions; 333 protected paths và lịch sử giữ nguyên. Graph stale61 commits/context notfound; UNKNOWN unresolved, static fallback scope-approved. Impact trước edit vẫn bắt buộc.

**F05 CLOSED trong scope.** Catch reuse normalizer trước timeout; actual ETIMEDOUT + HTTP500 + nested FORBIDDEN trả FORBIDDEN. **52/52 independent application cases PASS**, gồm nguyên48 gold và four additional cases; actual Page/Drawer0POST, scope races/unmount/CID/XSS giữ PASS. Typecheck/build PASS; lint exit0 còn5 warnings. Current wrapped4/native4/original3 tests đều PASS, coverage overlap. 32 exact-message checks trên captured evidence PASS, không thêm case/request.

**F07 PARTIAL**, native qualification13PASS/4FAIL. Direct Node ownership, normal/assertion teardown, foreign-listener refusal, unknown API abort +pytest1 đã PASS. Bốn root causes còn lại:

- Native không fail unexpected non-API outbound; reviewer deny nhưng pytest0.
- Native không observe/fail foreign WS; reviewer block upstream nhưng pytest0.
- Endpoint substring nhận alias `not_declared_chat_copilot` thành200/pytest0.
- Readiness ngoài finally; setup exception để owned Node sống/listen. Reviewer đã dừng đúng PID, cleanup hiện sạch.

Đây là test-infrastructure findings, không production permission leak. Native service-worker block có; source thiếu listener-PID/poll verification và response/generation-specific wait. Native fixture timeout case không inject actual Axios timeout; independent hook reproduction có.

| Gate | Current |
|---|---|
| G1/G2 | PASS narrow identity/tested UI contract |
| G3 | PARTIAL; financial qualification NOT_RUN |
| G4A/G4B | FAIL / CHANGES_REQUIRED |
| G10 | BLOCKED riêng, unchanged |
| G01–G03 | NOT_CLOSED |

**Minimal next batch:** sửa F07 trong test/fixture approved paths, cap320: exact origin/path/method fixtures + all unexpected channel accounting; owned cleanup từ spawn tới readiness/yield, wait exit/verify released port; case-specific waits và giữ assertions. Recheck: unknown API/alias/outbound/WS đều denied +pytest1; normal/assertion/setup cleanup PASS, foreign PID untouched; actualPage/Drawer0POST và52gold vẫnPASS. Không mở lại hook/UI PASS. Vượt scope/cap thì SCOPE_CHANGE_REQUIRED; không thêm dependencies.

Lotus Fin riêng ERPNext; không suy diễn SDK/deployment compatibility ở lượt này. Real ERP/LLM/financial truth, session permissions, immutable deployment và performance/payload budgets NOT_RUN; không claim financial automation demo acceptance. F102 unchanged. Chat quyết định batch, Work recheck sau authorization; G10 xử lý riêng.

[Review](B1S_CORRECTION_R3_INDEPENDENT_RECHECK.md) · [Ledger](B1S_CORRECTION_R3_TEST_RESULTS.json) · [Reproduction](../evidence/b1s-g4b-correction-r3-2026-10-10/REPRODUCTION.md). Evidence có source/build hashes, actual PIDs/JUnit/probe outcomes, cleanup và preserved history; initial API wrapper diagnostic được lưu và API-only retry supersede rõ ràng.
