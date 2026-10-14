# Work → Chat: P1-A/P1-B Round 4 acceptance

11/10/2026 · Lotus Fin / FinTechathon Shenzhen 2026.

**P1A_CHANGES_REQUIRED. P1B_CHANGES_REQUIRED. Không đóng hai batch offline tại revision này.** Review chỉ A16/B03; không mở architecture/financial scope.

Source develop@`07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, staged empty. Exact saved-R3→current-R4 diff: two modules/one test/two report appends. Event adapter96 lines/hash`187dbc6…`,authorizer195/hash`25f7d34…`,context test193/hash`6dec781…`; full SHA256/dirty/import manifest trong [recheck](CHATBOT_P1AB_R4_INDEPENDENT_RECHECK.md). All20 code files<200; all50 prior test-function ASTs/assertions unchanged, one test added. API/legacy/protected tests and641 tracked fingerprints unchanged; B1-S R7 sources13/13 unchanged. Relevant GitNexus stale61/not found, bounded static tracing.

|Current independently executed evidence|Result|
|---|---|
|Focused existing P1-A/P1-B|60/60 PASS:41+19,exit0,0.90s.|
|Previous Track A including N01–N12/A13–A15/CID/privacy|22/22 PASS,exit0.|
|Current A16 qualification|11 PASS/3 FAIL,exit1.|
|Previous B01–B14|14/14 PASS,exit0.|
|Current B03 controller qualification|7 PASS/1 FAIL,exit1.|

Counts overlap; variants not additive unique coverage. Network attempts0, real ERP/LLM imports0, business reads0. No source/test/data/dependency/Docker changes; controlled threads/processes finished and review logger state cleaned.

Only remaining material repairs:

1. **A16 — backend builder:** direct stream writes bypass logger/handler filters; generic handler rejection still increments delivered. Real False filters reproduce either unauthorized emission/count1 or no emission/count1. Require explicit acknowledged sink, respect suppression/fail closed/count0, no callback patch. Acceptance: three filter cases plus preserved direct/ancestor/root/default, actual outage, concurrent A1/B0, logger/handler-level and missing/Null sink controls. Previous callback race and level-suppression failures now PASS.
2. **B03 — authorization builder:** exact Company/user calls and missing/throwing method cases now PASS. But `if frappe in sys.modules` skips authorization when module absent and supported constructor supplies identity; actual controller issues200/ref. Require validated permission seam regardless of identity source; unavailable framework denied before context/ref. Positive tests must explicitly supply affirmative permission double without weakening assertions. This is offline composition-contract evidence, not claimed live request impersonation.

**Historical evidence warning:** R3 raw A16 ledger changed from6/2 to8/0 and Track B from13/1 to14/0 before this review, while R3 reports/source manifest remain old. New PASS entries carry stale R3 source hash. Original report verdicts and B1-S remain preserved; current overwritten copies and lineage warning saved separately, no restoration performed. Builder must stop rerunning into old independent output paths. R4 verdict uses freshly executed R4 evidence only.

Next eligible batch: narrowly correct A16 filter/acknowledgment and B03 absent permission seam, preserve assertions/history, then independent recheck. Chat cannot close P1-A/P1-B offline yet. After both PASS, recommend **target qualification preflight**, not automatic P2-A: exact trusted Lotus Fin→ERP product/site/config map, installed app/custom-hook lineage, real principal/company/doc/field/revocation oracle, approved key/required sink, isolated baseline/lifecycle/cleanup and real HTTP/CSRF delivery evidence.

`P1B_LIVE_AUTHORIZATION=NOT_RUN`; invoice search/open disabled; financial automation not authorized. G3/G01–G03 not closed. **G10 BLOCKED independently. B1-S historical PASS preserved.** No automatic implementation dispatch or enable/release permission.

### Tái xác nhận cùng artifact — yêu cầu lặp lại 11/10/2026

22 source/report hashes unchanged; no new correction. Fresh execution: focused60/60 PASS(1.80s), Track A22/22 PASS, B01–B14 14/14 PASS; A16 vẫn11 PASS/3 FAIL(filter), B03 vẫn7 PASS/1 FAIL(absent framework with constructor identity). Không cộng repeat thành coverage mới. Evidence riêng tại [repeat manifest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-repeat1-independent-2026-10-11/SOURCE_BEFORE.json); previous outputs/verdicts không ghi đè.

**P1A_CHANGES_REQUIRED / P1B_CHANGES_REQUIRED giữ nguyên.** Chưa đủ điều kiện offline closure hay target qualification preflight. Sửa đúng A16/B03 trước; các giới hạn live auth, disabled invoice actions, historical B1-S và G10 ở trên vẫn áp dụng.
