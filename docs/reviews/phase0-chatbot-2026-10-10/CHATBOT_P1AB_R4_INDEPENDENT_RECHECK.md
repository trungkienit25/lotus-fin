# P1-A/P1-B Round 4 — independent acceptance

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026 · Independent Application Security / Backend QA.

**P1A_CHANGES_REQUIRED. P1B_CHANGES_REQUIRED. Combined offline closure chưa đạt.** A16 race và suppression theo level đã sửa, nhưng filter suppression/acknowledgment còn sai. B03 exact Company và missing/throwing permission method đã sửa khi framework hiện diện, nhưng absent-framework branch vẫn bỏ qua quyền khi identity được cung cấp qua constructor. Chỉ hai blocker A16/B03 được xét; không mở architecture audit hay financial implementation.

Authority: [R3 independent report](CHATBOT_P1AB_R3_INDEPENDENT_RECHECK.md), [P1-A current implementation report](E:/lotus-fin/CHATBOT_P1A_IMPLEMENTATION_AND_EVIDENCE.md), [P1-B current implementation report](E:/lotus-fin/CHATBOT_P1B_IMPLEMENTATION_AND_EVIDENCE.md), [P1 MASTER §3/4/6](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md), [AGENTS](E:/lotus-fin/AGENTS.md), [ADR001](E:/lotus-fin/docs/adr/001-clean-architecture-core-first-adr.md), [Security Code V3 §11–12](E:/lotus-fin/docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md).

## 1. Exact source identity, diff và scope

**develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2**, staged empty. Existing tracked dirty chỉ Panel/Drawer,74 insertions/267 deletions; binary diff unchanged versus R3. Selected modules/tests vẫn untracked, nên HEAD không đủ định danh artifact.

[Current manifest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/SOURCE_BEFORE.json): full dirty inventory,22 selected source/report hashes,authority/runtime,641 tracked fingerprints và2.656 pre-existing review files. [Current source content](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/SOURCE_CONTENT.json). [Exact complete R3→R4 diff](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/EXACT_R3_TO_R4_DIFF.patch.txt) dùng actual saved R3 bytes/fingerprints, không builder summary. Không còn gap exact diff của lượt R3→R4 này.

|Changed artifact|Lines including blanks|Current SHA256|
|---|---:|---|
|lotus_fin/lotus_fin/infrastructure/observability/action_events.py|96|187dbc6fc5abc739ccc3f065ce6872f08fe21b9ded160611fb7a72fc930ddb5e|
|lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py|195|25f7d34a8b0358eed9d191631136739c3e187a0b9692c76f186271c4bda562d6|
|lotus_fin/lotus_fin/tests/test_invoice_context.py|193|6dec781f8b182f39216bd34c519ad65ffba4077a2c283d48664dca790eefdf26|
|CHATBOT_P1A_IMPLEMENTATION_AND_EVIDENCE.md|374|2c19706c84eb6b4f599aaa57c9dc98ad090deddfc2feb433d25f0754c4ced41d|
|CHATBOT_P1B_IMPLEMENTATION_AND_EVIDENCE.md|235|3945ae888da202adb609050e8b5b04fce1b2d2d3df3c2fd71bd433556ee4dbf2|

Code delta đúng two modules/one test;17 selected artifacts khác unchanged. Hai report giữ nguyên prefix344/196 lines và append correction. Hashes match builder. All20 code files<200 lines, AST/compile20/20. All50 prior test functions giữ nguyên AST/assertions; one new Company/outage test added, focused parameterized total60. [Syntax/assertion comparison](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/SYNTAX_AND_ASSERTION_IDENTITY.json). No removed/weakened original assertion.

641/641 tracked fingerprints unchanged versus R3, gồm tracked financial/legacy/package paths. P1-B API,controller,codec/config/DTO, P1-A domain/response/port và five other test files byte-identical. R7 B1-S13/13 source hashes unchanged. No dependency/session/ERP modification detected in protected baseline. Unrelated pre-existing untracked non-review files lacked prior comprehensive fingerprints; universal attribution of their contents is not claimed. No newly detected application source delta outside selected correction files.

GitNexus installed cached1.6.12: context calls for both changed classes exit1/not found; current index316c5bd…61 commits behind HEAD. Relevant graph UNKNOWN, not unused/safe. Bounded static caller trace: controller→resolve service→authorizer and event port→sink adapter; current public API remains disabled. No index install/download/refresh; no application/test edit or commit.

## 2. Historical evidence integrity exception

**Old B1-S history and both immutable R3 reports are preserved**, but two R3 raw ledgers changed between reviews:

|R3 evidence file|Recorded independent R3 result|Current contents before this review|
|---|---|---|
|A16_REAL_DEFAULT_AND_CONCURRENCY.json|6 PASS/2 FAIL|8 PASS/0 FAIL|
|TRACK_B_PROBES.json|13 PASS/1 FAIL|14 PASS/0 FAIL|

The rewritten ledgers still carry R3 source-manifest event hash `f70b52…`/84 lines despite apparent new execution against changed implementation. R3 `.INITIAL.txt` preserves A16 original6/2; immutable R3 report and prior executed results preserve previous verdict/counts. This is mixed historical/runtime lineage, **not accepted as independent R4 evidence**. We cannot infer who wrote it from contents alone.

[Lineage warning](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/HISTORICAL_LINEAGE_WARNING.json); current overwritten files copied into fresh R4 evidence as `R3_OVERWRITTEN_*.json`. Không restore/rewrite R3 files. R3's2.632 pre-existing protected files remain unchanged; its own subsequently created raw artifacts were outside that earlier fingerprint list. Both R3 report hashes exactly match previous final values. This review uses fresh R4 outputs only. Evidence hygiene correction: builder reruns must use their own current-round directory, never write previous independent output paths or reuse old manifest identity. This exception is separate from the two production contract blockers below.

## 3. Actual independent execution

Installed C:/Python313/python.exe3.13.7 / Pydantic2.12.5 / pytest9.0.2 / pluggy1.6.0 / Windows11 build26200. No installation/Docker use. Guard denies socket connect/connect_ex/bind/getaddrinfo and real ERP/LLM/legacy imports before application imports. `python -B -` stdin, bytecode disabled; pytest autoload/cache disabled and no conftest.

|Execution|Actual result / exit|
|---|---|
|Six focused existing files|**60/60 PASS**, exit0,0.90s: P1-A41 + P1-B19. Warnings0.|
|Previous independent N01–N12|12/12 PASS, intended fields/invariants.|
|Previous A13–A15|3/3 PASS.|
|Previous A16 direct/default ancestor sequential|PASS subcases.|
|Previous C01–C06|6/6 PASS: literal matrix24 allowed/120 rejected, CID/header/request, logger privacy/source/import controls.|
|Track A prior battery|**22/22 PASS**, exit0.|
|Current A16 qualification|**11 PASS/3 FAIL**, exit1; precise breakdown below.|
|Previous B01–B14 battery|**14/14 PASS**, exit0.|
|Current B03 public-controller qualification|**7 PASS/1 FAIL**, exit1; absent framework with fixed constructor identity fails.|
|Syntax/import isolation|20 AST/compile checks; actual5 Track A/14 Track B production import paths/hash identities match current tree.|

These ledgers overlap; no additive unique coverage claim. Fourteen A16 and eight B03 entries are variants of the existing requirements. Matrix pairs are subchecks. Failing executions have no ERROR/setup failure and fail intended assertions. Actual failing stream/outage barriers triggered; positive source/sink/reference controls reached success. Existing pure N01–N12/A13–A15 and B01–B14 were rerun, not inherited.

Raw [focused ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/FOCUSED_PYTEST.json), [focused output](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/FOCUSED_PYTEST.txt), [Track A](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/TRACK_A_PROBES.json), [A16](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/A16_CURRENT_QUALIFICATION.json), [Track B](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/TRACK_B_PROBES.json), [B03](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/B03_PUBLIC_QUALIFICATION.json). Matching `*_REPRODUCTION.txt` files contain actual stdin; no executable script or application/test source created. [Command/exit ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/EXECUTION_COMMANDS.json).

## 4. A16 findings and qualification

**A16 remains CHANGES_REQUIRED — HIGH contract blocker: filter policy bypass and false required-delivery count.** [Stream write:82](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:82), [ignored handler return:90](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:90), [count increment:96](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:96).

|Variant|Observed current behavior|Result|
|---|---|---|
|Healthy/failing direct/ancestor/root ×2|Actual default adapter, real streams. Healthy one emitted record/count1; OSError typed delivery failure/count0/no diagnostic canary.|6 PASS|
|Two default adapters concurrent, shared root stream|A enters controlled write; B actual OSError, A succeeds. Counts A1/B0, callback equivalent, both threads complete.|PASS|
|Effective logger WARNING|Typed failure, emitted0,count0.|PASS|
|All handlers WARNING|Typed failure, emitted0,count0.|PASS|
|Missing sink / NullHandler only|Default adapter fails closed,count0.|2 PASS|
|Logger filter returns False|Filter calls0; emits274 bytes and increments1, no error.|FAIL|
|StreamHandler filter returns False|Filter calls0; emits274 bytes and increments1, no error.|FAIL|
|Non-stream Handler filter returns False|Filter called once/rejects; emit not reached, but adapter returns normally/count1.|FAIL|

Root cause: manual `format→stream.write→flush` skips logger/handler filtering; fallback `h.handle(record)` rejection is ignored. Qualified-handler presence and no exception are still not delivery acknowledgment. Filter suppression is explicitly in Round4 acceptance; these are not speculative new scenarios. Unsupported/default configurations may fail closed; no requirement to force default propagation to succeed.

Previous callback interception/race removed. No stale intercepted callback or per-instance-lock false safety found in current tested concurrent path. Code still executes redundant `h.handleError=h.handleError` and sets named global logger INFO at import; do not describe it as wholly free of shared state changes. These observations are not additional speculative gate blockers. Per-call tested semantic callbacks remain equivalent. Actual privacy/redaction N08–N11/C05 PASS; raw stream-outage canary absent from captured logger stderr. No durable financial audit/throughput claim from these tests.

Smallest correction: one explicit supported required-sink path respecting logger/handler filter decisions, rejecting suppression as approved delivery failure/count0, and acknowledging actual writes. Honor the shared handler's supported synchronization; do not patch callbacks. Unsupported generic handlers without acknowledgment must fail closed rather than infer delivery from `handle` returning. Preserve successful/failed/default/concurrent/level/no-sink controls and add exactly three filter qualifications. Keep ADR line limits; no generic logging platform/refactor.

## 5. B03 findings and qualification

**B03 partially corrected; P1B_CHANGES_REQUIRED — MEDIUM, contract-blocking absent permission seam path.** [Conditional framework check:110](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:110), [context construction after skipped branch:135](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:135).

|Variant through actual controller + healthy real sink|Serializer result / evidence|Result|
|---|---|---|
|Trusted allowed control|200/CONTEXT_READY/ref, exactly Company/read/doc=Company A/user=alice, one actual log event.|PASS|
|Company type allowed, exact Company A denied|403/COMPANY_DENIED/null, exact actor/company passed.|PASS|
|Explicit DocType denial|403/COMPANY_DENIED/null.|PASS|
|Missing permission method|503/TARGET_UNQUALIFIED/null, no permission call.|PASS|
|Permission exception|503/TARGET_UNQUALIFIED/null, no raw error canary.|PASS|
|Guest / missing SID|401/AUTH_REQUIRED/null, no permission call.|2 PASS|
|Absent framework, supported constructor supplies trusted user/SID/site|No permission seam exists, yet200/CONTEXT_READY/ref.|FAIL|

All seven normal cases preserve request-ID echo/CID equality and one safe real audit event; no invoice/business reads. Document check now passes exact invoice ID/user and remains disabled, not DOCUMENT_READY. All B01–B14 present-framework negatives/reference/config/API checks PASS.

Remaining source guard only executes permission validation if `"frappe" in sys.modules`; no else-denial. Independent reproduction fixes identity using the adapter's existing constructor parameters and removes only the required framework/permission seam. Actual production class/controller still issues authorized context/ref. Those values are supplied by reviewer composition, **not forged client request identity**. This demonstrates a supported-composition fail-open path; it does not establish a remotely exploitable live HTTP bypass. Ordinary default adapter without framework also lacks principal and is denied, as B01 correctly shows. Constructor identity injection is not proof of Company permission, nor an explicitly isolated alternate authorizer implementation.

P1 MASTER §4 requires missing framework/permission seam fail closed; unit/test-only convenience cannot authorize the production Frappe adapter without that seam. Smallest correction: require available validated permission interface before context construction regardless of identity source; absent import/module/method or exception returns approved unavailable/denied outcome. Keep identity fixtures at explicit test composition but supply an affirmative independent permission double for genuine positive tests. Preserve existing assertions, updating their fixture setup where necessary; no fallback authorization/mock/Admin, invoice reads or new enabled path.

## 6. Cleanup, scope and gate matrix

Network attempts0 across executions. Focused suite blocks11 real Frappe import attempts; never successful real framework imports. Track B uses an explicit private synthetic module then removes it; no ERP/db read spies triggered. All owned foreground Python processes exited, no services/listeners/background helpers or process termination. Both controlled threads joined. Review logging topology handlers/levels/propagation/disabled/filters restored, owned handlers closed; state confined to private process. No bytecode/cache, application/test edits, dependencies, Docker/shared data/permission changes, commits or deployment.

[Final integrity](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-independent-2026-10-11/SOURCE_AFTER.json) verifies22 selected source/report files,641 tracked files,2.656 pre-existing review files and authority unchanged during this review. Pre-existing inaccessible pytest-cache inventory warnings are not test failures. Old R3 ledger overwrites were already present at start and were not repaired or further overwritten.

|Gate|Independent decision|
|---|---|
|Source/current identity|Verified HEAD/dirty/hash/exact diff/imports/runtime; historical raw-lineage exception disclosed.|
|P1-A prior outcome/CID/provenance/privacy|PASS current independent execution.|
|P1-A A16 required delivery|**CHANGES_REQUIRED**: three filter variants fail.|
|P1A_INDEPENDENT_PASS|Not earned: **P1A_CHANGES_REQUIRED**.|
|P1-B prior B01–B14 present-framework contracts|PASS current execution; not live rights.|
|P1-B B03 unavailable seam|**CHANGES_REQUIRED**: absent module + supplied identity still admits.|
|P1B_OFFLINE_CONTRACT_PASS|Not earned: **P1B_CHANGES_REQUIRED**; also depends on accepted P1-A.|
|P1B_LIVE_AUTHORIZATION|**NOT_RUN**, separate qualified target required.|
|Invoice search/open|**Disabled**, current direct API/controller tests; zero business reads.|
|B1-S historical PASS|Preserved R7 source/history; not rerun or promoted to new runtime PASS.|
|G3 finance / G01–G03 backend/session|Unqualified; unchanged gates.|
|G10 judge deployment|**BLOCKED independently**.|

Live HTTP/CSRF/ERP rights/revocation/envelope/image lineage NOT_RUN. Unrelated financial/browser suites and performance workloads NOT_RUN by explicit scope; no throughput/p95/RSS claims. Chat cannot close either batch offline yet. Eligible next step: only bounded A16 filter/acknowledgment and B03 absent-seam corrections, preserve history and assertions, then independent recheck. After both offline PASS, recommend separately approved target qualification preflight; no automatic P2-A implementation or financial automation enablement.

## 7. Tái xác nhận theo yêu cầu lặp lại — cùng artifact, 11/10/2026

Không có correction mới:22/22 selected source/report fingerprints, HEAD/branch và hai report R4 trước append khớp lượt acceptance ở trên. Chạy lại độc lập theo yêu cầu user trong [fresh repeat evidence](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-repeat1-independent-2026-10-11/SOURCE_BEFORE.json), không ghi đè output R3/R4.

|Repeated execution|Current actual / exit|
|---|---|
|Focused six files|60/60 PASS,1.80s,exit0.|
|Previous Track A N01–N12/A13–A15/C01–C06 + sequential A16|22/22 PASS,exit0.|
|Previous B01–B14|14/14 PASS,exit0.|
|Actual-current A16|11 PASS/3 FAIL,exit1; same three filter defects.|
|Actual-current B03 controller|7 PASS/1 FAIL,exit1; same absent-framework/supplied-identity admission.|

Repeated coverage không cộng thêm unique tests. Controlled concurrent stream/outage triggered, callbacks equivalent/threads finished; failing assertions đúng nguyên nhân đã nêu. All executions network attempts0/business reads0; focused warnings0,11 Frappe imports blocked. [Repeat command ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-repeat1-independent-2026-10-11/EXECUTION_COMMANDS.json) và [final integrity](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r4-repeat1-independent-2026-10-11/SOURCE_AFTER.json) ghi actual runtime/source/cleanup. **Verdicts unchanged: P1A_CHANGES_REQUIRED, P1B_CHANGES_REQUIRED.** Live authorization NOT_RUN, invoice search/open disabled, B1-S historical PASS preserved và G10 BLOCKED independently. Next eligible action vẫn chỉ scoped corrections trước target preflight, không P2-A implementation.
