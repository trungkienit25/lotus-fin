# B1-S Correction Round 5 — Independent F07 recheck

**Verdict: `B1S_G4B_CHANGES_REQUIRED`.** 11/10/2026 · FinTechathon Shenzhen · independent QA/security/test-infrastructure review. **Q1–Q8 của Round4: 8/8 PASS; original eight requirements PASS; normal native4/4 PASS; application gold52/52 PASS.** Hai ngoại lệ static/HMR vẫn cho undeclared attempts thoát ledger và tạo pytest0. Đây là vi phạm F07 đã reproduce, không phải blocker backend hoặc đề xuất mở rộng coverage vô hạn. Chưa đề nghị Chat đóng B1-S.

## 1. Current artifact, diff và authority

`develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, implementation còn uncommitted. Staged empty. Hai tracked dirty files Panel/Drawer có từ baseline; exact tracked diff không đổi trong lượt review. Các unrelated untracked files được preserve, không quy kết cho Antigravity chỉ vì untracked.

| Current B1-S artifact | Lines | SHA256 |
|---|---:|---|
| Native test |286≤320|`4075D799EC2A1D7F89E3ACCF82671797E2E96ED03E44EC2DD38C4E128D2DCC09`|
| Conditional helper |133≤200|`ADAAC78773A05C668990D5DCFDA33CAECA1C34D06755F3649A00D1D9E2BF180B`|
| Implementation report |526|`647B09F49DDEC93A1910365319A07A09C2B715FB22096DF8A6D5213CC965E3B8`|

[All13 source/report/package fingerprints](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/SOURCE_BEFORE.json), [exact Round4→5 diff](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/R4_TO_R5_DIFF.patch). Delta: native test refactor, helper added, report append. Five production files, three fixture files, package/lock unchanged versus selected Round4 baseline; backend/permissions/dependency/protected fingerprints333/333 unchanged. Report preserves substantive historical content; two trailing blank lines replaced by separator/new section, so strict byte-prefix check is false. This whitespace delta is nonblocking.

558 historical raw hashes +18 current historical deliverable hashes =576/576 preserved. R4 recheck's earlier quality-audit append is verified through its immutable before-append snapshot and current quality manifest; not rewritten here. Original assert AST22/22 retained; request-increment assertion added. Existing 26-case native table/oracle preserved. [Scope/history](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/HISTORY_INTEGRITY.json), [assert preservation](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/ASSERTION_PRESERVATION.json).

AGENTS/GitNexus, ADR001, existing B1-S contracts and current user Round5 scope apply. Explicit native≤320/helper≤200 allowance overrides generic ADR file cap for these test artifacts; historical Panel variance is unchanged. No new business script/helper/dependency. GitNexus cached context `install_network_guard` returns notfound; index2026-10-02/316c5bd… is stale. UNKNOWN unresolved; scope-authorized bounded static tracing used, no tooling download or graph all-clear. Future fixer must perform required impact analysis.

## 2. Actual environment and execution

Python3.13.7, pytest9.0.2, Playwright1.58.0/Chromium1208, Node22.19.0, Vite8.3.3, React19.3.0, TypeScript6.0.3, Axios1.20.0, Oxlint1.87.0. Fresh private TEMP with existing dependencies copied; root node_modules junction points into that same private copy. Twelve copied test/production/fixture/package hashes match source; all13 workspace hashes unchanged after execution.

Actual helper import: `tests_e2e.copilot_test_harness`; four existing pytest entrypoints unchanged. Native server fixture runs its direct Node spawn/readiness/finalizer, without `ServerOverride`. Reviewer only pins existing browser binary, enforces10s probe waits, observes callbacks/PIDs and injects controlled faults. Application gold separately reuses existing immutable review oracle with synthetic transport and reviewer server lifecycle; its wrapped four-test aggregate overlaps native4 and is not additional coverage.

Final18 invocations all run with independent transport containment installed **before native imports**: `Route.continue_` may reach only exact `http://127.0.0.1:5188`; any WS `connect_to_server` denied. Native outbound probes must still fail through native ledger; reviewer fallback alone cannot qualify them. All18 containment ledgers have0 fallback upstream attempts. First execution/proof refinement retained separately; repeats are not new cases. No ERP/LLM/public/shared8080 requests, dependency install, Docker mutation or paid provider. [Commands, reproduction and boundaries](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/REPRODUCTION.md).

## 3. Eight required negative qualifications

Each row uses actual native pytest, triggered probe, intended failure and clean owned lifecycle. Expected negative pytest exit1 is qualification PASS; reviewer executor exit0. Full responses/assertions/PIDs/command lines/JUnit are in matching raw `*_RESULTS.json`, `*_JUNIT.xml`, stdout/stderr and containment ledgers.

| ID | Actual result | pytest | Qualification |
|---|---|---:|---|
|Q1 METHOD|GET exact POST-only Copilot aborted; METHOD_QUERY ledger; no200|1|PASS|
|Q2 QUERY|Company GET undeclared query aborted; no synthetic success; METHOD_QUERY|1|PASS|
|Q3 ENCODED|`/%61pi/method/reviewer_undeclared_probe` aborted as UNDECLARED_API; no HTML success|1|PASS|
|Q4 ASSET|`/reviewer-undeclared-static-probe` aborted as UNDECLARED_ASSET|1|PASS|
|Q5 LOCAL_WS|Undeclared localhost WS path reaches guard, records WS; no upstream|1|PASS|
|Q6 READINESS|Controlled post-spawn foreign sentinel rejected by exact PID mismatch; owned Node stopped; sentinel untouched until reviewer closes it|1 setup error|PASS|
|Q7 LATE|Unexpected request during `browser.close` aborted/recorded; post-close final ledger fails|1|PASS|
|Q8 SYNC|22nd send suppressed: prior FORBIDDEN/text/IDLE still present, only21 requests; current response wait times out|1|PASS|

Q6 finalizer also raises “port remained occupied” while the foreign sentinel intentionally remains. Original PID mismatch survives in exception chain; native owned process already exited, foreign sentinel remains open, final port free after reviewer cleanup. Diagnostic masking is nonblocking here, not a leak or foreign kill.

## 4. Demonstrated remaining contract violations

**R5-F07-A — P2/MEDIUM, static allowlist not bound to actual private roots.** `tests_e2e/copilot_test_harness.py::is_allowed_static_asset`, lines54–57 accepts any `/@fs/` path containing `lotus-fin` and a listed extension, ignoring `query`. Independently fetch `http://127.0.0.1:5188/@fs/E:/lotus-fin/reviewer-undeclared-static-probe.js` while server runs from private TEMP. Native continues the outside-private-root, undeclared path; **HTTP200 fixture HTML, selected native pytest0, no unexpected-event failure**. Reviewer qualification FAIL/exit1; owned Node/listener cleanup PASS. No real file or ERP read was performed. [Actual response and evidence](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/POLICY_ASSET_RESULTS.json).

Smallest correction: replace product-name substring with canonical, verified private root/path bounds; declare existing module/assets and supported query variants so unknown paths are rejected before Vite fallback. Preserve boot assets and one central policy. Required recheck: this exact probe aborts, records native event, pytest1, cleanup clean, normal4/gold52 remain green. Query-ignorance is static observation, not separately executed additional finding.

**R5-F07-B — P2/MEDIUM, HMR exception checks token shape, not identity.** Same helper `is_allowed_vite_ws`, lines60–66 accepts any token value, also no query. Synthetic `ws://127.0.0.1:5188/?token=reviewer-forged-token` **actually enters native callback**, is treated as allowed, no unexpected-event assertion, selected native pytest0. Qualification FAIL/exit1; cleanup PASS. Routed WS has no upstream by installed Playwright default and independent clamp: this is false-green accounting, not demonstrated data exfiltration. [Callback proof](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/POLICY_LOCAL_WS_RESULTS.json).

Installed Vite8.3.3 generates a specific random `config.webSocketToken`, injects it into client URL and compares it on server; merely having key `token` does not mean valid token. [Installed primary source excerpts/hashes](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r5-2026-10-11/INSTALLED_PRIMARY_SOURCE.json). Smallest correction: bind exception to exact owned fixture-generated URL/token, or remove fixture WS attempt and deny all WS. Do not trust the first arbitrary page request. Preserve no-upstream behavior; forged token must record violation and pytest1. These two probes verify the already-approved static/HMR precision requirements, without expanding into new application features.

Round5 implementation report's eight scenarios are now independently verified, but its “internal repo”/“valid token” claims exceed actual code. Its positive native runner result does not establish those two contracts. No production/financial regression found in this scope.

## 5. Original regressions, application and engineering

Original eight requirements PASS: unknown API alias (`ALIAS`, plus overlapping `API`), foreign HTTP (`OUTBOUND`), foreign WS (`WS`), pre-existing listener refusal (`PREFLIGHT`), normal teardown (`NORMAL`), assertion-failure teardown (`API`), readiness exception cleanup (`SETUP` direct actual fixture), exact owned PID/listener identity. SETUP/PREFLIGHT directly execute native fixture rather than pytest; their RuntimeErrors and cleanup are recorded as such, not invented pytest exits. Lifecycle/owner observations overlap scenario runs and are not extra unique tests.

**Native4/4 PASS, application52/52 PASS, 32/32 exact-text checks PASS on those same records.** Current executions cover root/nested denial precedence, Axios timeout distinctions, safe normalization, unqualified provenance/widgets/actions, XSS text rendering, CID validity/redaction, actual Page/Drawer0 Copilot POST, company/context reset, delayed success/failure, unmount fencing/cancellation and disabled finance shortcuts. F05 remains CLOSED for this UI contract. No historical PASS substituted for current gold.

TypeScript/build/targeted lint all exit0 in private frontend. Separate warnings: five existing React/unused-variable lint warnings;757.04kB JS chunk warning; Vite config-loader future-compatibility warning. No failed assertion hidden as warning; none of these holds B1-S open.

## 6. Engineering and cleanup assessment

One active network guard in helper; one native process owner. API method/origin/path/query checks, decoded unknown API handling, post-spawn HTTP title/PID readiness, browser-close-before-ledger and response/count synchronization now handle all eight demonstrated failures. Helper boundaries are small; no additional SDK, framework, dependencies or business layer.

Nonblocking: unused `LifecycleGuard` is imported but not used by four entrypoints, duplicates a lifecycle abstraction and swallows page-close exceptions; four live tests retain explicit finalizers. Do not declare it universally dead from stale graph. Broad HTTP readiness exceptions cause bounded retry/fail, not PASS; listener lookup errors return empty then timeout. Netstat parsing is Windows-specific; Linux/macOS NOT_RUN. Case URL substring synchronization remains protected by active endpoint policy for these executed tests; no speculative alternate race introduced.

Every native run records direct owned Node PID/arguments, independent listener and command-line observation, then0 owned Nodes/0 listeners before reviewer fallback cleanup; fallback owned kills0, unrelated kills0. Q6/PREFLIGHT preserve their controlled foreign sentinel until reviewer cleanup. DOM reviewer-owned server exits and port5188 is free. Private TEMP/junction deletion and final known-browser/Node/listener inventory are recorded in WORKSPACE_CLEANUP.json. All contexts use `service_workers=block`; actual SW-install negative probe NOT_RUN. Cleanup PASS does not imply universal network escape-proof while policy exceptions remain.

## 7. Gate verdict and limits

|Gate|Current decision|
|---|---|
|G1|PASS — working tree, hashes, private copy/environment and scope identity|
|G2|PASS — current synthetic UI contract;52gold +native4|
|G3|BLOCKED / current production financial context unqualified; live acceptance NOT_RUN|
|G4A|FAIL — two remaining static/HMR false-green exceptions|
|G4B|**B1S_G4B_CHANGES_REQUIRED** — demonstrated material F07 violations|
|G10|BLOCKED independently; judge artifact/site/HTTP acceptance NOT_RUN|
|G01–G03|NOT_CLOSED; backend/session acceptance NOT_RUN|

Source lineage: actual working tree/fingerprints; runtime lineage: private Vite/installed Chromium/synthetic transport; Docker/ERP image lineage NOT_USED/NOT_VERIFIED. No authorization, tenant/principal, financial truth or performance PASS inferred. Timing records are execution durations, not p95/throughput/RSS acceptance.

Chat should authorize/track only a small test-only closure of R5-F07-A/B inside current allowlist/caps, followed by exact probe +eight/original/native/gold recheck. No freeze or implementation dispatch here. After B1-S achieves PASS, separately scoped outcome/CID and server-owned authorized-read milestone can precede invoice search/select/open. Lotus Fin product identity remains separate from ERPNext technology. UI safety does not authorize ERP financial automation.

[Machine ledger](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R5_TEST_RESULTS.json) · [Work→Chat](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R5_WORK_TO_CHAT.md).
