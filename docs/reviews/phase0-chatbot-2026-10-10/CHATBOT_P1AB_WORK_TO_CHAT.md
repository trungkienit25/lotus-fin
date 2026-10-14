# Work → Chat: combined P1-A/P1-B independent recheck

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026.

**P1A_CHANGES_REQUIRED. P1B_CHANGES_REQUIRED. Combined acceptance BLOCKED.**
Chat **chưa đóng P1-A**, không grant P1B_OFFLINE_CONTRACT_PASS hoặc P1B_LIVE_AUTHORIZATION_PASS. P1-B chưa sẵn sàng acceptance trên target. **Invoice search/open/action vẫn NO; không enable hoặc dispatch P2-A.**

[Full review](CHATBOT_P1AB_INDEPENDENT_RECHECK.md) · [actual machine ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/INDEPENDENT_PROBES.json).

## Current evidence

develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2; staged empty; tracked dirty Panel/Drawer có sẵn, không đổi.20 current source/tests +2 reports được SHA256 định danh; all source/tests35–189 lines. [Manifest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/SOURCE_BEFORE.json) và [final integrity](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-independent-2026-10-11/SOURCE_AFTER.json).

P1-A report có stale response hash: actual2e7878d8ce709662e95f3ac72545be2ac8400454dfb0e94e6efd160e2b5214c2, đúng P1-B report. Exact one-line condition delta thay cách xử lý missing request ID đã verified; cần factual scope explanation, không rollback rộng.

Host Python3.13.7/Pydantic2.12.5/pytest9.0.2; installed dependencies reused. No source/test edits, installs, live ERP/LLM, Docker mutation, data/permissions change, commit/deploy. GitNexus61 commits stale/current symbol missing; bounded static trace, không graph-safe claim.

|Current execution|Result|
|---|---|
|Six existing focused modules|**55/55 PASS**, exit0:37 P1-A +18 P1-B.|
|Original independent N01–N12|**12/12 PASS**.|
|Remaining P1-A A13–A16|**4 FAIL**.|
|P1-B B01–B14|**7 PASS /7 FAIL**.|
|Controls C01–C06|**6 PASS**, matrix24/120 subchecks0 mismatch.|
|Independent total|**36 check groups:25 PASS /11 FAIL**; probe exits1. Không cộng vào55 thành unique coverage.|

## Material blockers and smallest correction

1. **P1-A final delivery/denial:** DTO không revalidate full provenance; mutated invalid source vẫn200/OK. PARTIAL chứa recognized FORBIDDEN vẫn xuất protected canary. OK message không enforce fixed safe template. Close F01/F02 tại shared final boundary; giữ coverage/selection-ref/null-data rules, không build invoice logic.
2. **P1-A actual sink reliability:** throwing logger fake PASS nhưng real StreamHandler write outage không propagate; adapter falsely records1 event. Required sink phải observable/acknowledge delivery, failed event không được recorded. F04 còn open.
3. **P1-B principal/permission:** missing SID trở thành auth_session_default; configured company/user equality thay current rights. Denied fake permissions vẫn authorized, document method DOCUMENT_READY với zero permission checks. Strict trusted session + current permission seam; chưa qualified phải unavailable/denied, không add invoice reads ở foundation.
4. **P1-B references:** product/connection claims chưa verify đầy đủ, actual connection-version switch vẫn nhận old ref. Raw SID decode được từ public signed token. Full scope/config/version binding + keyed/opaque session/actor references; MAC không che credentials.
5. **P1-B admission/API:** optional missing audit sink vẫn context200/ref. Plain API functions không authenticated POST whitelist declarations, không controller/audit composition, không echo valid client ID. Wire one disabled boundary theo P1-A; actual HTTP envelope/header/CSRF/status vẫn cần target qualification.

Forged MAC/wrong purpose/expired/key/actor/company/session/site negatives, Guest/missing framework rejection, unknown/missing config, forged request identity và disabled actions có positive offline evidence. Chúng không bù các blockers, không qualify live permissions.

## Gates and next owner

B1-S **prior R7 PASS preserved**,13/13 source hashes unchanged; native/gold không rerun. G3 finance/G01–G03 session/backend không được đóng. **G10 independently BLOCKED.** Không build B0/AI007/F101/F102 hoặc invoice finance automation.

**Recommended next batch — Antigravity Backend/Security:** bounded correction P1-A F01/F02/F04 trước, rồi five P1-B root causes; exact file allowlist/necessary small variance phải được duyệt, GitNexus impact trước edit. Preserve55 current assertions, thêm exact independent failing cases, real logging-handler failure và declaration checks. **Owner Work:** independent recheck theo fresh SHA/actual exits; không builder-self-PASS.

**Real ERP prerequisites — Chat/product + target/security owner:** canonical Lotus/backend/image/module/app/custom-hook lineage; approved ERP site/product/connection-version map; actual authenticated principal/Company/doc/field/revocation oracle; purpose/key policy, required sink; fresh private fixture/snapshot reviewed baseline/lifecycle/cleanup. Verify authenticated POST/Guest/GET/CSRF/decoder/CID/single-envelope/no-store và denial-before-read. No shared frontend/ai003 bootstrap baseline.

**Recommended P2-A action sau closure:** approve and qualify one bounded Sales Invoice minimal authorized read slice, explicit search→select→exact-document reauthorization/open contract. Keep amount/overdue/write/send/SDK/LLM/legacy migration out of scope. Chưa dispatch implementation hay bật action tự động.

