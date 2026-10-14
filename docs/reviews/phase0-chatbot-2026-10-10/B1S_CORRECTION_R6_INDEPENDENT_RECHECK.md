# B1-S Round6 — Independent G4B closure review

**Verdict: `B1S_G4B_CHANGES_REQUIRED`.** 11/10/2026 · Lotus Fin · FinTechathon Shenzhen. **Hai exact defects Round5 CLOSED:** static-root probe và forged-HMR probe đều qualify PASS. Legitimate native4/4, application52/52, Q1–Q8 8/8 và original F07 requirements PASS. Còn **một demonstrated violation** của query allowlist trên cache asset; chưa đề nghị Chat đóng B1-S. Không mở lại architecture/backend audit.

## Source identity, scope và diff

`develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, working tree dirty/uncommitted; staged empty. Hai tracked Panel/Drawer changes có từ baseline; exact tracked diff không đổi trong lượt review. Không quy kết unrelated untracked files cho builder.

|Artifact|Lines|SHA256|
|---|---:|---|
|Native test|286≤320|`4075D799EC2A1D7F89E3ACCF82671797E2E96ED03E44EC2DD38C4E128D2DCC09`|
|Helper|160≤200|`39FDBE4018F02F64E8A349FE7C179FDD4AFDF12C538AB28AC5C63E8FB029FC8F`|
|Implementation report|578|`1290385699B7F6531ED0BAC73CE19BC584EAD2635DAF30DFCBACC1CC4D32F7EF`|

[Full13 current fingerprints](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/SOURCE_BEFORE.json) và [Round5→6 exact diff](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/R5_TO_R6_DIFF.patch). Chỉ helper và report đổi. Five production files, native test/oracle, three fixtures, package/lock giữ nguyên Round5.333 protected source/backend/session/dependency fingerprints và847 historical hash checks giữ nguyên;847 =826 historical raw files +21 historical current deliverables, không phải test coverage. R4 earlier append lineage đã verified ở Round5 và không đổi. Report substantive history retained; trailing blank lines replaced by Round6 separator, nên strict byte-prefix false nhưng không rewrite lịch sử. Native23 assert AST và26-case vector byte-preserved.

AGENTS/GitNexus, ADR001 và approved B1-S/user Round6 contract áp dụng. Explicit native≤320/helper≤200 allowance và historical Panel variance không được mở rộng. No dependency/framework, new application file, production/test edit, backend/session/ERP mutation, commit/push/deploy. Helper import vẫn `tests_e2e.copilot_test_harness`; only one active native policy/process owner. Unused LifecycleGuard không được gọi từ four native entrypoints; không xóa hoặc tuyên bố universally dead.

Cached GitNexus status timeout35s; contexts `is_allowed_static_asset`/`is_allowed_vite_ws` notfound. Index2026-10-02/316c5bd… stale/UNKNOWN; bounded static tracing dùng theo scope, no tooling download/graph-safe claim. Future source fixer vẫn phải làm AGENTS impact.

## Actual private execution and positive controls

Private TEMP `b1s-r6-review-<uuid>` **không chứa “lotus-fin”**; current frontend/dependencies/test/helper/fixtures copied, twelve copied hashes matched. Root node_modules junction points only into private frontend/node_modules. Python3.13.7, pytest9.0.2, Playwright1.58.0/Chromium1208, Node22.19.0, Vite8.3.3, React19.3.0, TypeScript6.0.3, Axios1.20.0, Oxlint1.87.0. Source/runtime/executable/installed-primary-source hashes retained.

Native fixture/assertion bodies unchanged. Reviewer observes process/listener/response/callbacks and injects controlled faults in memory, pins existing browser binary, probe waits10s. Independent HTTP continuation clamp allows only exact127.0.0.1:5188 and denies any WS upstream; Python HTTP reads likewise bound to fixture origin. All19 containment ledgers show0 fallback upstream attempts. No real ERP/LLM/public/shared8080/Docker/site/business-data interaction. These are synthetic UI/native-harness results, not financial permission acceptance.

**Normal native4/4 PASS / pytest0.** Positive bootstrap records92 local static responses/23 unique URLs across four pages, legitimate cache URLs with sole `v` query and legitimate /@fs modules. Helper ROOT derives from copied helper's realpath; normcase/realpath +root separator prevent sibling-prefix/junction escape for /@fs, extension +isfile required; /@fs queries denied. Own dependency junction resolves inside verified private root. No adversarial symlink sweep was run; canonicalization review and real positive junction behavior are distinguished.

HMR remains narrowly allowed, not eliminated. Helper reads `const wsToken` from owned `/@vite/client`; contemporaneous listenerPID17596 equals exact native-owned PID. Four normal WS callbacks match bootstrap token; values redacted/hash retained. No token learned from first incoming WS. Installed Vite generates/injects specific token; installed Playwright routed WS defaults to no upstream. [Positive/identity evidence](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/NORMAL_BOOTSTRAP_IDENTITY.json), [primary source](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/INSTALLED_PRIMARY_SOURCE.json).

## Two exact Round5 closures

|Probe|Actual native outcome|pytest|Qualification|
|---|---|---:|---|
|`/@fs/E:/lotus-fin/reviewer-undeclared-static-probe.js`|fetch aborted; UNDECLARED_ASSET ledger; rejected before Vite fallback; no external file/business read|1|PASS / R5-F07-A CLOSED|
|`ws://127.0.0.1:5188/?token=reviewer-forged-token`|actual callback; token mismatch, WS ledger; no upstream, final browser close|1|PASS / R5-F07-B CLOSED|

Both selected pytest failures match intended native “Unexpected network traffic detected”, reviewer exit0, cleanup PASS. [Static exact proof](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/POLICY_ASSET_RESULTS.json), [forged token proof](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/POLICY_LOCAL_WS_RESULTS.json). Report's hashes, chosen HMR strategy and these exact closures agree with current source/execution; positive claims were independently rerun.

## One remaining material F07 violation

**R6-F07-C — P2/MEDIUM, `copilot_test_harness.py::is_allowed_static_asset`, lines70–71.** Cache branch tests `not query or query.startswith("v=")`, so it never verifies sole declared query key. This is the existing strict request/query trust boundary explicitly inspected in Round6, not a new application capability or speculative edge case.

Reviewer obtains an actual legitimate cache URL from **current page resource entries**, adds only `&reviewer_undeclared=1` and fetches it after native goto. Positive control `/.vite/deps/react.js?v=780a8cd6` returns200. Negative `/.vite/deps/react.js?v=780a8cd6&reviewer_undeclared=1` also returns **200 `text/javascript` /135555 bytes**, no native violation, selected normalization pytest **0**; qualification **FAIL**, reviewer exit1. No fake version, wrong listener, stale result or bootstrap failure caused this. Owned NodePID14668 exactly matches private Vite listener/command line; cleanup PASS before fallback. [Actual probe](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/CACHE_ASSET_RESULTS.json), [current positive/negative resource URLs](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/CACHE_ASSET_BOOTSTRAP_IDENTITY.json), [pytest0](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/CACHE_ASSET_JUNIT.xml).

Smallest correction: parse cache query fields, permit empty query or only the declared sole `v` parameter; reject unknown/duplicate/additional keys before continuation and record native event. Preserve legitimate generated/virtual cache resources and actual Vite boot. Do not substitute a filesystem existence check for virtual cache resources blindly. Existing parse_qsl dependency is already present; no new dependency/refactor needed. Recheck this exact current-resource extra-key probe: abort +native ledger +intended pytest1 +clean lifecycle; all frozen regression remains green. Report's “only query v=…” description does not yet hold for parsed parameter sets.

## Frozen regressions and engineering

|Frozen scenario|Actual reason|pytest|Result|
|---|---|---:|---|
|Q1 METHOD|GET Copilot rejected/METHOD_QUERY|1|PASS|
|Q2 QUERY|Undeclared Company query rejected/METHOD_QUERY|1|PASS|
|Q3 ENCODED|Decoded unknown API rejected/UNDECLARED_API, no HTML success|1|PASS|
|Q4 ASSET|Unknown root asset rejected/UNDECLARED_ASSET|1|PASS|
|Q5 LOCAL_WS|Unknown local path recorded WS/no upstream|1|PASS|
|Q6 READINESS|Post-spawn sentinel wrong PID rejected; owned process exits, sentinel retained until reviewer close|1 setup|PASS|
|Q7 LATE|Request during browser.close captured; final ledger after close fails|1|PASS|
|Q8 SYNC|Suppressed22nd send; prior FORBIDDEN/IDLE retained,21 requests; current-response timeout|1|PASS|

Original eight requirements PASS: API alias rejection, foreign HTTP, foreign WS, pre-existing listener refusal, normal teardown, assertion-failure teardown, readiness-error teardown and exact ownership. SETUP/PREFLIGHT directly invoke actual native fixture, not pytest: RuntimeErrors, spawn refusal/owned cleanup recorded without invented pytest exit. Other negative runs fail for intended native assertions, not reviewer containment. Q6 secondary occupied-port error retains original PID mismatch in exception chain; foreign sentinel deliberately remains until reviewer cleanup, not an owned leak.

**Application52/52 PASS, exact-message32/32 PASS on same records; F05 CLOSED.** Current production imports: Page/Drawer0 Copilot POST, denial/timeout precedence, safe normalization/rendering/CID, source fail-closed, scope/context reset, races/delayed success/failure/unmount, disabled finance shortcuts and no fabricated output. Gold/oracle unchanged. DOM wrapped four-test aggregate overlaps actual native4 and is not eight unique native tests. Lifecycle/owner observations and32 exact strings overlap; do not sum counts as independent application coverage.

Typecheck/build/targeted lint exit0. Separate warnings: five existing React/unused variables,757.04kB chunk and Vite future config-loader warning. No gate blocker from warnings or unrelated architecture. First collector read hit Windows cp1252 UnicodeDecodeError, corrected explicit UTF-8; tests/oracle unaffected, diagnostic retained.

## Commands, cleanup and evidence lineage

Exact subprocess args/selected test names/exits/timings are in `CONTAINED_EXECUTION_REPRODUCTION.txt`, `CACHE_EXECUTION_REPRODUCTION.txt`, `CONTAINED_EXECUTIONS.json`, `CACHE_EXECUTIONS.json`, per-mode JUnit/stdout/stderr/results and ENGINEERING_RESULTS. To reproduce, rebuild a fresh private copy from hashed source snapshots/current unchanged sources and existing matching dependencies, verify twelve hashes, create only internal dependency junction and update OWNED_WORKSPACE. Then execute reviewer programs through UTF-8 Python stdin; no app/runtime business script or source edit:

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-Content -Encoding UTF8 -Raw -LiteralPath 'E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/CONTAINED_EXECUTION_REPRODUCTION.txt' | python -
Get-Content -Encoding UTF8 -Raw -LiteralPath 'E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r6-2026-10-11/CACHE_EXECUTION_REPRODUCTION.txt' | python -
```

Native fixture owns direct Node spawn and readiness/teardown; separate gold uses reviewer-owned lifecycle only. Capture module assert preservation, before/after source hashes, exact PID/listener/command lines and final empty ledger after browser close. Each run shows0 owned Nodes/listeners before fallback, fallback kills0. Foreign sockets remain until reviewer cleanup. No unrelated process termination. All contexts set service_workers=block; SW-install negative probe NOT_RUN. Verified TEMP/junction deleted and final node/browser/listener inventory in WORKSPACE_CLEANUP.json. Actual task-owned Node/browser cleanup is PASS; unrelated processes are untouched.

## Gate matrix and recommendation

|Gate|Current|
|---|---|
|G1|PASS — current source/dirty artifact, private copy/environment and integrity|
|G2|PASS — frozen synthetic UI safety only|
|G3|Financial context unqualified; live acceptance NOT_RUN/outside this batch|
|G4A|FAIL — cache extra query remains falsely green|
|G4B|**B1S_G4B_CHANGES_REQUIRED**|
|G10|BLOCKED independently; judge artifact/site/HTTP acceptance NOT_RUN|
|G01–G03|NOT_CLOSED by synthetic UI; backend/session NOT_RUN|

Nonblocking residual limits: token cache is process/module-scoped and non-Windows netstat behavior not qualified; only current one-fixture-per-review-process lifecycle is executed. No universal symlink/SW/async threat sweep or performance acceptance; durations are not p95/throughput/RSS. Source lineage actual working tree+hashes; runtime private Vite/Chromium/synthetic transport; Docker/ERP image lineage NOT_USED/NOT_VERIFIED. No financial/backend authority inferred.

Next owner: Chat scopes a tiny helper query-policy correction; Antigravity builder repairs/reports; independent reviewer reruns exact cache extra-key proof plus frozen set. No automatic dispatch or new implementation batch. Once B1-S passes, separately scoped outcome/CID and server-owned authorized read milestone precedes invoice search/select/open. Lotus Fin product and ERPNext technology remain separate; UI safety is not permission to enable unqualified financial automation.

[Machine ledger](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R6_TEST_RESULTS.json) · [Work→Chat](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R6_WORK_TO_CHAT.md).
