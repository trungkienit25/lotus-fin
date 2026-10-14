# Work → Chat — B1-S Round6 F07 closure decision

11/10/2026 · FinTechathon Shenzhen · `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + dirty artifact.

**Recommended verdict: `B1S_G4B_CHANGES_REQUIRED`. Chat chưa nên đóng B1-S.** Hai exact Round5 blockers đã CLOSED; còn một query classification violation được reproduce trên nhánh cache asset hiện hữu, cùng approved F07 trust boundary. Không mở broad audit/ERP implementation.

|Current independent execution|Result|
|---|---|
|Static-root exact probe|PASS: abort/UNDECLARED_ASSET, native pytest1|
|Forged-HMR exact probe|PASS: callback/token mismatch/WS ledger, pytest1/no upstream|
|Legitimate positive controls|Native4/4 PASS; owned bootstrap token matches four WS callbacks; actual static/cache resources boot|
|Frozen Q1–Q8|8/8 qualification PASS, intended native failure +clean lifecycle|
|Original F07 requirements|PASS; eight overlapping ownership/lifecycle requirements|
|Application gold|52/52 PASS;32 exact-message checks overlap, oracle unchanged|
|Typecheck/build/targeted lint|exit0; existing warnings separately recorded|
|Source/history/cleanup|Current13 source hashes unchanged during review;333 protected/847 historical checks unchanged; owned resources0, private TEMP removed|

**One material blocker — R6-F07-C, P2/MEDIUM:** `copilot_test_harness.py::is_allowed_static_asset`70–71 allows cache query by raw `startswith("v=")`. Current legitimate `/.vite/deps/react.js?v=780a8cd6` is observed200; append only `&reviewer_undeclared=1` and still get **JavaScript200, native ledger empty, selected pytest0**. Qualification FAIL; owned PID/listener/cleanup PASS. This directly tests Round6's supported-query contract, not a hypothetical future concern. R5's exact outside-root and forged-token probes remain closed.

**Smallest eligible correction:** parse query fields for generated cache resources; allow empty or sole declared `v`, deny undeclared/additional/duplicate keys before continuation. Preserve legitimate virtual/generated cache assets. Existing urllib.parse support suffices; no new dependency, production code or broader refactor. Exact negative must abort/record/pytest1 with clean owned lifecycle; legitimate boot, frozen Q1–Q8/original/native4/gold52 stay green.

Only helper/report changed Round5→6; native286≤320 unchanged, helper160≤200, five production files/fixtures/package/lock unchanged. Report history retained except trailing whitespace at append. Current private root does not contain “lotus-fin”; positives no longer depend on product-name substring. Exact HMR token is read from owned Vite bootstrap with PID proof, not first incoming WS; token values redacted. No new framework/dependency or application/test edits in review.

|Gate|Decision|
|---|---|
|G1/G2|PASS narrow identity/UI safety|
|G3|Unqualified financial context; live NOT_RUN/outside scope|
|G4A/G4B|FAIL / CHANGES_REQUIRED for cache query predicate only|
|G10|BLOCKED independently; judge delivery NOT_RUN|
|G01–G03|NOT_CLOSED; backend/session NOT_RUN|

Finance shortcuts/widgets/unqualified remote requests remain disabled; company selector is no authorization evidence. No ERP/LLM/provider/public/shared8080/Docker operation, installs, commits or deployments. Independent transport clamps and exact owned cleanup protect the review; no unrelated process kill. Stale GitNexus remains UNKNOWN; future fixer follows AGENTS impact before editing. Warnings, unused LifecycleGuard and hypothetical platform/lifetime hardening are nonblocking.

**Next owner:** Chat controls tiny correction scope/closure decision; Antigravity builder repairs helper predicate and factual report; independent Work reviewer verifies exact query probe and frozen set. No automatic dispatch here. After B1-S PASS, separately scope outcome/CID +server-owned authorized read, then invoice search/select/open. Lotus Fin and ERPNext boundaries remain distinct; synthetic UI acceptance grants no permission to enable financial automation.

[Review](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R6_INDEPENDENT_RECHECK.md) · [Actual ledger](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R6_TEST_RESULTS.json).
