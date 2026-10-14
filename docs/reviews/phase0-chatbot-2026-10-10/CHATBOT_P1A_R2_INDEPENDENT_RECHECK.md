# P1-A Round 2 — independent A13–A16 closure recheck

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026 · Independent Backend Security QA.

**Verdict: P1A_CHANGES_REQUIRED.** A13/A14/A15 và original N01–N12 PASS trên current source. A16 direct-handler case PASS, nhưng **default adapter với real failing StreamHandler ở logger cha vẫn falsely records một event**, không surface typed failure. P1-A chưa thể đóng. Đây là demonstrated P1-A sink defect; không giữ gate vì prerequisite P1-B/ERP.

Authority: [prior combined recheck](CHATBOT_P1AB_INDEPENDENT_RECHECK.md), [current P1-A implementation report](E:/lotus-fin/CHATBOT_P1A_IMPLEMENTATION_AND_EVIDENCE.md), [P1 MASTER §3/6/9](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md), [AGENTS](E:/lotus-fin/AGENTS.md), [ADR001](E:/lotus-fin/docs/adr/001-clean-architecture-core-first-adr.md), [Security Code V3 §11–12](E:/lotus-fin/docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md). Không thay SSOT/history hoặc review P1-B implementation ở lượt này.

## 1. Current artifact và exact scope

**develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2.** Staged empty. Existing tracked dirty chỉ Copilot Panel/Drawer,74 insertions/267 deletions; exact binary diff bằng baseline combined review. P1-A source/tests vẫn untracked; HEAD không định danh đầy đủ artifact.

[Before manifest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/SOURCE_BEFORE.json) ghi full dirty inventory,22 current selected source/report hashes,641 tracked files và pre-existing review hashes. [Current content snapshot](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/SOURCE_CONTENT.json) chỉ chứa P1-A eight files/report, không executable scripts.

|P1-A path dưới lotus_fin/lotus_fin/|Lines including blanks|Current SHA256|
|---|---:|---|
|domain/schema/action_outcome.py|191|0fa95bc9fba8073350c3189c7e055bdae56f579b39d780f508d2e94baf9f147d|
|presentation/dto/action_outcome.py|121|2c89b0c5ea422972cd6855230bb99c594630134956d5e901b54cd25e5833796f|
|presentation/response/action_response.py|155|599f7afd0e0a1dd79671f0796a87cdd16e26fb2d3ad66a670889ae01a42521bb|
|application/port/i_action_events.py|91|9573fd752755e463ecb0cf24d9e6e01941865561c2e8dbd744b633950423876e|
|infrastructure/observability/action_events.py|66|8f9f9c60c59563b314e52c223224bf71926026e327d9f8ced81c1c1d316bda11|
|tests/test_action_outcome.py|177|1f681972a3e1c68bd3b3332d72f326882df024ca1ec8f6ff59751e51e562a99b|
|tests/test_action_delivery.py|174|e902a6721bb4df4d3ed5eef463d19ee0e87f6f5d4d9afbf6d47c420ad70a9516|
|tests/test_action_security_regressions.py|188|b60996f7fae400cb04f7b2961499defaf2478bf054b47cc88ea2070f4f8f3249|

All8 dưới200 lines. Actual delta: **four production modules changed**, events port và two original test files unchanged, regression test changed, root report appended. Builder “5 production modified” statement overcounts unchanged port, không functional blocker. Root report287 lines, SHA256731b66954e4d9ed8afd41e151e044a09ce21dad3713b8a47572c9f36983d5966.

Exact previous bytes của four changed production modules và regression test được reconstructed rồi **matched independently to prior SHA256** trước dùng làm diff, không giả định builder diff đúng. [Verified exact diff](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/VERIFIED_PRODUCTION_DIFF.patch.txt), [inverse/hash verification](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/DIFF_VERIFICATION.json). Prior206-line root-report prefix vẫn exact-hash unchanged; history không bị rewrite. Unchanged files được hash comparison riêng.

Diff confirms: full SourceEvidence reconstruction ở DTO/serializer; PARTIAL denial guard ở domain/DTO; message template now unconditional; sink adapter wraps only directly attached handlers' handleError callbacks. No capability or financial source behavior enabled.

**P1-B9 modules +3 tests +report =13/13 fingerprints unchanged**, chỉ hash comparison, không import/test/review implementation. **B1-S R7 source13/13 unchanged**; prior evidence preserved, native/browser/gold không rerun. Không package/lock/tracked legacy change; không quy pre-existing untracked inventory cho builder.

GitNexus installed cached1.6.12 context SafeStructuredActionEvents exit1/notfound; index commit316c5bd…61 commits behind current HEAD. Relevant graph UNKNOWN; bounded static source/import tracing, không index refresh/download hoặc “safe” inference. Graph-first conceptual query đã unresolved trong prior combined review; current context rechecked. Không code edit/commit; correction phase sau vẫn cần fresh impact.

## 2. Actual execution, controls và isolation

Host C:/Python313/python.exe; Windows11 build26200; Python3.13.7/Pydantic2.12.5/pytest9.0.2/pluggy1.6.0. Installed environment reused; Docker NOT_USED.

|Execution|Actual / exit|
|---|---|
|Three existing focused P1-A files|**41/41 PASS**, exit0,0.73s:12 outcome +15 delivery +14 regression functions/cases.|
|Independent original N01–N12|**12/12 PASS**.|
|Independent A13–A16|**3 PASS /1 FAIL**; A16 includes direct and default propagated subcases.|
|Independent C01–C06|**6/6 PASS**.|
|Independent total|**22 check groups:21 PASS /1 FAIL /0 ERROR**, process exit1 for intended A16 violation.|
|Literal matrix C03|24 allowed +120 rejected pairs;0 mismatches. Subchecks, không144 additional tests.|
|P1-A syntax/import identity|8 AST/compile checks PASS;5 actual imported module paths/hashes match current workspace.|

Không cộng41+22 thành unique coverage; original negative tests overlap independent probes. Builder cumulative52 và previous combined55 không inherited như execution ở lượt này.

[Pytest text](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/FOCUSED_PYTEST.txt), [case ledger/args/exit](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/FOCUSED_PYTEST.json), [independent exact assertions/actuals/hashes/runtime](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/INDEPENDENT_PROBES.json), [commands/exits](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/EXECUTION_COMMANDS.json). Reproducible stdin: [pytest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/FOCUSED_PYTEST_REPRODUCTION.txt), [independent probes](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/INDEPENDENT_PROBES_REPRODUCTION.txt).

Executed via PowerShell stdin → python -B -; PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1. Explicit root/lotus_fin sys.path; pytest.main with -p no:cacheprovider --noconftest -v and three paths, Recorder. Independent probes import actual production modules, no builder fixture/oracle imports.

Before imports, Python audit hook rejects socket connect/connect_ex/bind/getaddrinfo; MetaPath rejects real ERP/Frappe/LLM/provider/legacy agent/controller imports. Both executions: **network attempts0, forbidden import attempts0**. Actual module identities recorded in C06. No source/test edits, cache/plugin fixture writes, installs, shared service requests, Docker/data/permissions changes, commits or deployment.

Every command completed; no background helper/listener or service spawned, no process termination/deletion required. Controlled logging changes stay in private foreground Python process; ancestor handlers/levels/propagation restored in finally, owned handlers closed. [Final integrity](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-r2-independent-2026-10-11/SOURCE_AFTER.json) verifies protected source/history unchanged during review.

Pytest warnings0. StreamHandler outage diagnostics were captured on private stderr; not counted as successful adapter delivery. Preparation first manifest read hit Windows default JSON-encoding error, retried UTF-8-SIG; P1-B test-name classification narrowed before execution. Existing inaccessible pytest-cache inventory warnings recorded; no changes to those directories.

## 3. Intended negative assertions

|ID|Independent result|
|---|---|
|N01|OK/INCOMPLETE rejected for coverage invariant. PASS.|
|N02|Malformed timestamp and timezone individually rejected for intended fields. PASS.|
|N03|PARTIAL actionable selection_ref rejected. PASS.|
|N04|Nested FORBIDDEN rejected from OK. PASS.|
|N05|Post-construction failure data/source mutation stripped,403/null/no canary. PASS.|
|N06|SOURCE_ERROR message equals approved literal and excludes canary,502. PASS.|
|N07|Unknown version/status/reason/capability tested individually with otherwise valid DTO. PASS.|
|N08/N09/N10|Session/email/free-text stage rejected before real StringIO logger; zero leaked/recorded events. PASS each.|
|N11|Invalid event CID/request/capability/status-reason individually rejected. PASS.|
|N12|Throwing sink emits typed error; recorded_events0. PASS.|
|A13|observed_at and verification mutations independently rejected at serializer for intended field; direct DTO with only coverage rejected for missing source fields. PASS.|
|A14|PARTIAL nested FORBIDDEN rejected both at construction and after data mutation at final DTO; no success body emitted. PASS.|
|A15|Valid OK and PARTIAL retain200, exact approved literal message replaces raw OperationalError/session canary. PASS.|
|A16 direct|Real local StreamHandler write outage → ActionEventDeliveryError, recorded_events0, callback restored. PASS subcase.|
|A16 default/propagated|Same real failing stream on ancestor/root handler; default adapter has direct handlers0 → no typed failure, recorded_events1. **FAIL subcase; A16 overall FAIL.**|

ValidationError accepted only where field/invariant matches intended oracle. A13/A14 do not pass merely because a bad UUID/import error occurred. They prove serializer rejection/no public success, **not live HTTP safe-error delivery**.

Controls: generated genuine UUID4/body-header CID/no-store/client-ID echo; malformed/UUID1/UUID5 replacement; literal independent24/120 matrix; denial precedes bad ID; actual successful logger emits one approved event with no canaries; actual five-module/import/network isolation. All PASS.

Assertion review: two original test files byte-identical to prior combined snapshot. Regression refactors retain N01–12 intents, but N06 removed its exact safe-message equality assertion, and builder A15 only checks no-canary. Independent N06/A15 explicitly assert approved literals and PASS, so this weakening is documented without inventing another production blocker. Restore the equality assertion in the next scoped regression correction. Builder direct A16 omits default ancestor path, which explains false closure.

## 4. Only material remaining finding

**F04/A16 — HIGH contract blocker: default propagated logging outage falsely counted as delivered.**

Exact source: [default logger:17](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:17), [record_event direct handler selection:40](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:40), [false append:66](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:66).

Root cause: adapter inspects self._logger.handlers only. Its default named logger can have zero direct handlers and propagate to ancestor/root handlers. Standard StreamHandler handles write-level OSError internally. Ancestor handleError is never intercepted; handler_errors remains empty and adapter appends event despite failed sink. Captured stderr confirms probe triggered, but caller gets normal return and delivered-history contains one event. No live ERP incident or deployment configuration is claimed.

Minimal reproduction, private process only:

    root_handler = logging.StreamHandler(BrokenStream())  # write raises OSError
    logging.getLogger().addHandler(root_handler)
    eventmod.logger.setLevel(logging.INFO)
    eventmod.logger.propagate = True
    eventmod.logger.handlers = []
    adapter = SafeStructuredActionEvents()  # actual default composition
    adapter.record_event(valid_event)
    assert len(adapter.recorded_events) == 0  # FAIL: actual 1

Full reproduction preserves/restores logger configuration and verifies direct healthy/failing controls. Intentional independent process exit1 qualifies the demonstrated failing safety assertion; it is not a successful negative qualification or incidental test setup failure.

**Smallest scoped correction:** make supported required-sink acknowledgment/failure explicit for actual default delivery, including effective ancestor handlers, or fail closed before logging/counting if that composition cannot be qualified. Preserve logger state and avoid per-request shared callback mutation causing interference. Retain direct-handler/throwing-sink semantics and no-false-record invariant. Extend existing focused regression via bounded parameterization/fixture within <200 lines; restore exact-message assertion. Only adapter/current regression/report need targeted correction unless a cohesive boundary variance is explicitly approved; no P1-B/ERP/legacy refactor.

## 5. Closure decision and NOT_RUN

P1-A **cannot close** until A16 default-path invariant independently passes with reliable failure and zero false-delivered events. A13–A15 and original N01–12 are current verified positives, not blanket accepted P1-A.

P1-B was only fingerprint-protected; no new P1-B verdict, permission test or implementation audit here. Existing P1-B corrections must not treat this review as a closed P1-A dependency.

Live Frappe HTTP decoder/status/header/envelope/CSRF and **ERP target authorization remain NOT_RUN**; no actual invoice read/write, SDK/LLM or action enablement. Unrelated legacy clean-architecture AgentRunner/F002 import suites inspected for scope but NOT_RUN: they enter old tool/financial paths and are not dependencies changed by P1-A. Current five-module isolation is directly executed instead. B1-S/browser/gold and performance NOT_RUN, protected fingerprints unaffected. G10 remains independently BLOCKED, not reevaluated.

No P2 dispatch, broad architecture review, source fix or contract freeze. [Concise Work→Chat](CHATBOT_P1A_R2_WORK_TO_CHAT.md).

