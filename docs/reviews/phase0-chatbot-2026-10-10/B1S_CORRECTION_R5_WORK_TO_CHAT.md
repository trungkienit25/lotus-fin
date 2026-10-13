# Work → Chat — B1-S Round5 F07 final verification

11/10/2026 · Lotus Fin · FinTechathon Shenzhen · `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + dirty tree.

**Verdict: `B1S_G4B_CHANGES_REQUIRED`. Chat chưa nên đóng B1-S.** Eight Round4 critical qualifications đều PASS; application chưa có regression. Hai ngoại lệ static/HMR vẫn cho undeclared requests tạo false PASS, vi phạm F07 exact/bounded allowlist. Không dùng backend findings hoặc lint warnings để giữ gate mở.

|Current independent execution|Result|
|---|---|
|Q1–Q8 METHOD/QUERY/ENCODED/ASSET/localWS/readiness race/late ledger/stale sync|8/8 PASS; actual native pytest1 đúng lý do +clean owned lifecycle|
|Original F07 requirements|8 requirements PASS; lifecycle observations overlap runs|
|Normal native|4/4 PASS, pytest0|
|Existing application gold|52/52 PASS;32 exact-text checks overlap, không cộng thêm|
|Static/HMR precision variants|2 FAIL qualification: selected native pytest0 sai kỳ vọng|
|TypeScript/build/targeted lint|exit0; five existing lint warnings và build/config warnings riêng|
|Cleanup|Owned Nodes/listeners0, reviewer fallback kills0, unrelated kills0; private TEMP removed|

Final executions use independent HTTP-origin clamp and all-WS-upstream denial outside native policy. Native server lifecycle/assertions unchanged; gold oracle unchanged. No ERP/LLM/public/shared frontend/Docker requests, installs, commits or deployments. Source test286≤320/helper133≤200; five production files, fixtures, package/lock unchanged versus Round4.333 protected fingerprints +558 historical raw hashes/18 historical deliverables preserved. HEAD alone is not artifact identity; see manifest/ledger.

**Only remaining blockers (P2/MEDIUM test infrastructure):**

1. `copilot_test_harness.py::is_allowed_static_asset`54–57 uses `"lotus-fin" in norm`. Probe `/@fs/E:/lotus-fin/reviewer-undeclared-static-probe.js` outside private TEMP returns **200 fixture HTML**, ledger does not fail, pytest0. Bind canonical module/assets to verified private roots and reject unknown before Vite fallback; declare supported query variants.
2. `is_allowed_vite_ws`60–66 accepts arbitrary token value. `ws://127.0.0.1:5188/?token=reviewer-forged-token` reaches native callback but pytest0. Bind HMR exception to actual owned fixture-generated URL/token, or eliminate fixture WS and deny all. No upstream connection occurred; defect is accounting false PASS.

These reproduce existing approved static/HMR precision requirements; no speculative broad audit. Builder report's “internal repo”/“valid token” wording is inaccurate at these branches. PID readiness, settled ledger and missing-current-request synchronization now pass their demonstrated invariants. Q6 secondary occupied-port error preserves original PID mismatch; controlled sentinel is untouched and later reviewer-cleaned.

|Gate|Decision|
|---|---|
|G1/G2|PASS narrow identity/UI|
|G3|BLOCKED/unqualified production financial context; live NOT_RUN|
|G4A/G4B|FAIL / CHANGES_REQUIRED|
|G10|BLOCKED independently; deployment acceptance NOT_RUN|
|G01–G03|NOT_CLOSED; backend/session NOT_RUN|

**Next eligible small batch:** Antigravity builder repairs only these two test-policy exceptions within approved test/fixture/helper paths/caps; factual report append. Chat owns scope/acceptance; independent Work reviewer executes exact two repros +eight/original/native4/gold52 with owned cleanup. Each invalid attempt must abort/intercept, enter native ledger, yield intended pytest1; normal suite and gold remain green. Follow AGENTS impact requirement before source edit; stale graph UNKNOWN is unresolved. No new dependency or production/backend change, no automatic dispatch in this packet.

Finance shortcuts/widgets/unqualified remote Copilot requests remain disabled; selected company is no authorization evidence. Real ERP/LLM, principal/site/company delegation, G10 delivery and backend/session gates remain outside UI acceptance. After B1-S PASS, propose a **separate** milestone from existing chatbot architecture audit: outcome/CID and server-owned authorized read contract, then invoice search/select/open. Lotus Fin and ERPNext remain separate products/technology boundaries. This review grants no permission to enable ERP financial automation.

[Independent review](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R5_INDEPENDENT_RECHECK.md) · [Ledger](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R5_TEST_RESULTS.json) · [Raw reproduction](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/REPRODUCTION.md).
