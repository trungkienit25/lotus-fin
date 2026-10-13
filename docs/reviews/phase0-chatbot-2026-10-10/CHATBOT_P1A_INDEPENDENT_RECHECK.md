# P1-A independent recheck — outcome, CID, safe delivery và observability

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026 · Independent Backend QA/Security Reviewer.

**Verdict: `P1A_CHANGES_REQUIRED`.** Current focused suite18/18 PASS, nhưng independent checks6 PASS/12 FAIL tái hiện các vi phạm contract ngay trên source P1-A. Không đóng P1-A hoặc dispatch P1-B. Các lỗi được gom thành bốn nhóm functional/security và một scope/evidence correction; không yêu cầu broad architecture/SDK/legacy refactor.

Authority: [P1 MASTER SSOT §3/6/9](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md), [architecture decision](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_ERP_SDK_ACTION_ARCHITECTURE_DECISION.md), [action packet](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_ACTION_EXECUTOR_WORK_TO_CHAT.md), [builder report](E:/lotus-fin/CHATBOT_P1A_IMPLEMENTATION_AND_EVIDENCE.md), [AGENTS](E:/lotus-fin/AGENTS.md), [ADR001](E:/lotus-fin/docs/adr/001-clean-architecture-core-first-adr.md), [Security V3 §11–12](E:/lotus-fin/docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md). Contract decisions/runtime enablement ngoài P1-A không được tự freeze ở đây.

## 1. Current artifact và scope

`develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`. Staged empty; existing tracked dirty chỉ Copilot Panel/Drawer,74 insertions/267 deletions. Exact unstaged binary diff và641 tracked-file hashes bằng lượt architecture review trước; không quy dirty B1-S cho builder P1-A.

P1-A additions: **5 production modules +2 test files +1 root implementation report**, tất cả untracked. Untracked total9,741 gồm9,730 pre-existing inventory +3 review docs ở lượt trước +8 P1-A additions. 80 unique prior selected source/authority files và13 R7 fingerprints independently rehashed: không đổi. Không dependency/SDK/service/old Copilot/session/frontend/financial source change được phát hiện trong protected scope. Đây không phải chứng nhận mọi untracked file chưa từng bị người khác sửa; không có global historical hash baseline cho chúng.

Exact P1-A diff là ADD-only của bảy source/tests dưới đây; current content/hashes định danh artifact, không HEAD hoặc builder summary. [Raw source/environment manifest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-independent-2026-10-11/SOURCE_BEFORE.json).

|Path dưới `lotus_fin/lotus_fin/`|Actual lines including blanks|SHA256|
|---|---:|---|
|domain/schema/action_outcome.py|170|`a45a0c3393052970a5bb0aeb742c80dc138eb3cfa07441ca436929c20b15d2ce`|
|presentation/dto/action_outcome.py|83|`fe327a272d20180c04182795d398b00b5ba324011e609ddaff685d2daf4ca609`|
|presentation/response/action_response.py|140|`1aab845ac2b52d86a33507c93c42af0aec84489584ee423e8d4a9b18d6ae3c8e`|
|application/port/i_action_events.py|34|`102320200ae7bb67d81c6b3a30173bd9ff46047c35b0a3382240a46729dd6485`|
|infrastructure/observability/action_events.py|63|`9834f9d440e01c6cafaf41b83872a3f8b3c4167848a9931d84f266556685c796`|
|tests/test_action_outcome.py|177|`e3df2bb265c40959e0b2e3edda5b9107e4d6b0b17722c11e1ee27353df82294f`|
|tests/test_action_delivery.py|231|`ed7830d3f520138efe900e38cc3d3de7baa968feb05bafd98e37c7b652529d03`|

Builder report SHA `ff1b4f4a5a20e69614314637d2c1872bed1170263281d59070d48a77a3d2a2ca`. Its seven SHA values match; test line counts158/196 do **not** match actual177/231. Five production files meet limit; delivery test231 violates <200-line ADR/no approved variance found. Không thay test oracle/source để làm suite xanh.

Host execution: Windows, `C:/Python313/python.exe`, Python3.13.7, Pydantic2.12.5, pytest9.0.2, pluggy1.6.0. Dependencies reused; no install. Docker **NOT_USED** in this review; different deployed controller/DTO artifact previously observed không là current tested P1-A module. Không infer site/imports/ERP permission acceptance từ host tests.

GitNexus graph-first query `action outcome correlation serialization observability` exit0, stale61 commits; context `ActionOutcome` notfound/exit1. No relevant current flow resolved: UNKNOWN, bounded static tracing allowed by request. Source imports searched only after graph result: new modules reference each other, no production caller wiring outside them. No index download/graph-safe assertion. Code correction sau phải fresh impact before edit; Work không sửa functions.

## 2. Tests actually executed

|Execution|Actual|Scope|
|---|---|---|
|Existing focused test_action_outcome +test_action_delivery|**18/18 PASS**, pytest exit0,0.64s|9 domain +9 delivery/log tests. [Actual pytest output](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-independent-2026-10-11/FOCUSED_PYTEST.txt).|
|Independent current-contract probes N01–N12 +C01–C06|**6 PASS /12 FAIL**, process exit1|Pure/serializer/actual in-memory logger/synthetic sink outage, no ERP. [Machine ledger with source/runtime](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-independent-2026-10-11/INDEPENDENT_PROBES.json).|
|Status/reason exhaustive literal oracle, C03|24 valid pairs +120 rejected pairs,0 mismatches|Subchecks of one probe; không cộng144 vào unique test count. Oracle copied from SSOT literal allowlist, not STATUS_REASON_MATRIX under test.|
|New five-module import/isolation, C06 and pytest guard|PASS; forbidden imports/network attempts0|No frappe/erpnext/financial modules/AgentRunner/old controller/provider imported. Package compatibility resolver import is pre-existing and site-free.|
|B1-S native/gold and old clean-architecture/F002 regression|**NOT_RUN** here|No changed caller/legacy source:13 R7 and80 prior hashes unchanged. Broad29-test builder result không được inherit làm current execution.|
|Live HTTP/Frappe decoder/ERP permissions/performance|**NOT_RUN**, outside P1-A inert boundary|Serializer tuple is not actual HTTP; no route/site/business data/SDK call or benchmark. P1-B/P2 qualification riêng.|

No app/test source edits or persistent runtime scripts. Python runs via stdin, bytecode/cache/plugin autoload disabled; imports/network guarded before application import. `--noconftest` avoids unrelated site fixtures; current focused tests have no conftest dependency. Guard attempts were recorded, none occurred. No spawned listener/process/service requires cleanup.

Actual focused invocation inside the offline guard:

```python
sys.path.insert(0, str(pathlib.Path.cwd() / "lotus_fin"))
pytest.main([
    "-p", "no:cacheprovider", "--noconftest", "-v",
    "lotus_fin/lotus_fin/tests/test_action_outcome.py",
    "lotus_fin/lotus_fin/tests/test_action_delivery.py",
], plugins=[r])
```

Shell environment: `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; executable `python -B -`. Recorder `r` records each call outcome. Python audit hook rejects `socket.connect`, `socket.connect_ex`, `socket.bind`, `socket.getaddrinfo`; MetaPathFinder rejects Frappe/ERPNext/OpenAI/financial modules/legacy runner-controller-service/provider imports. Independent probes use same path/bytecode/network containment and direct imports of the five P1-A modules, not test helper/oracle imports.

## 3. Independent negative outcomes

These are **failed safety assertions**, not successful negative qualifications. Current code accepted/emitted the prohibited result. Canaries are synthetic; no real credentials/data were used.

|Probe / required assertion|Actual current behavior|Finding|
|---|---|---|
|N01 OK cannot claim complete success with INCOMPLETE source|serialize returns200/OK with INCOMPLETE|F02|
|N02 malformed observation timestamp/timezone rejected|`not-a-date` /`invalid/timezone` accepted,200/OK|F02; no actual source identity claim|
|N03 PARTIAL cannot authorize open|Non-null selection_ref retained in PARTIAL body,200|F02|
|N04 nested declared denial cannot remain outer success|Outer OK/200 contains nested FORBIDDEN/ACCESS_DENIED and protected canary|F02; no valid capability payload validation|
|N05 denied/error data null at final delivery|Valid FORBIDDEN model subsequently assigned data; serializer returns403 with protected data|F01|
|N06 terminal message fixed safe template|SOURCE_ERROR body contains raw `OperationalError sid=P1A_CANARY_7428`,502|F01|
|N07 direct DTO rejects unapproved version/status/reason/capability|`unapproved.v99`/BOGUS/`unrestricted.rpc` accepted and model_dump succeeds|F01/F02|
|N08 raw auth-session value absent from actual logger|`context_ref='sid=P1A_CANARY_7428'` appears in StringIO logger|F03|
|N09 raw actor email absent from logger|`actor_ref='P1A_CANARY_7428@example.invalid'` appears|F03|
|N10 stage fixed, not provider free text|`stage='OperationalError P1A_CANARY_7428'` appears|F03|
|N11 event IDs/capability/status-reason validate|Non-UUID CID/request, arbitrary RPC capability, OK+ACCESS_DENIED accepted|F03|
|N12 sink outage explicitly surfaced|Logger raises OSError; adapter returns normally, recorded_events contains one event|F04|

Positive controls: C01 actual generated CID.version4/RFC variant +body/header equality +403 PASS; C02 UUID1/UUID5/malformed IDs rejected PASS (validator's canonical equality matters); C03 matrix PASS; C04 declared FORBIDDEN stays403 despite invalid request ID, canary absent PASS; C05 keyword Bearer redaction reaches **actual logger**, PASS; C06 import/network isolation PASS. Những positives không bù các failing assertions.

## 4. Reproduction và smallest bounded correction

Common constructors below reproduce N01–N07 on current actual modules. Valid UUIDs ensure failures are not incidental CID checks; no live source read.

```python
import uuid
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome, SourceEvidence, ActionStatus as S, ActionReasonCode as R,
)
from lotus_fin.presentation.dto.action_outcome import ActionOutcomeDTO
from lotus_fin.presentation.response.action_response import ActionResponseBuilder as B

def source(**changes):
    values = dict(mode="ERP_READ", product_ref="prod_p1a", site_ref="site_p1a",
        connection_ref="conn_p1a", connection_version="v1",
        observed_at="2026-10-11T09:00:00Z", timezone="Asia/Ho_Chi_Minh",
        coverage="PAGE_COMPLETE")
    values.update(changes)
    return SourceEvidence(**values)

def outcome(**changes):
    values = dict(status=S.OK, reason_code=R.RESULTS_FOUND,
        correlation_id=str(uuid.uuid4()), request_id=str(uuid.uuid4()),
        capability="invoice.search", source=source(), context_version="ctx_p1a",
        data={"items": []}, user_message="Tìm thấy danh sách hóa đơn phù hợp.")
    values.update(changes)
    return ActionOutcome(**values)
```

|Finding / severity / exact symbols|Reproduction assertions and root cause|Smallest correction within P1-A|
|---|---|---|
|**F01 HIGH — unsafe final delivery** [serialize_response:128](E:/lotus-fin/lotus_fin/lotus_fin/presentation/response/action_response.py:128), [DTO:26](E:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/action_outcome.py:26)|N05: `o=outcome(status=S.FORBIDDEN,reason_code=R.ACCESS_DENIED,source=None,data=None); o.data={'private':'P1A_CANARY_7428'}; body=B.serialize_response(o)[2]; assert body['data'] is None` **fails**. N06: use SOURCE_ERROR/SOURCE_FAILURE, source/data None, raw user_message; `assert canary not in body` fails. Domain model mutable; from_domain copies fields, DTO validates only UUID; serializer neither revalidates nor derives fixed message.|Final boundary must enforce closed domain/DTO invariants even after mutation, deny/error data/source null and fixed code-derived message; invalid outcomes fail safely. Immutability/validated construction is useful, but not substitute for final validation of nested mutable payload. No old fallback/controller edits.|
|**F02 HIGH — incomplete outcome/provenance/action safety** [ActionOutcome:119–168](E:/lotus-fin/lotus_fin/lotus_fin/domain/schema/action_outcome.py:119), [SourceEvidence:94](E:/lotus-fin/lotus_fin/lotus_fin/domain/schema/action_outcome.py:94), [DTO:29](E:/lotus-fin/lotus_fin/lotus_fin/presentation/dto/action_outcome.py:29)|N01: `B.serialize_response(outcome(source=source(coverage='INCOMPLETE')))` emits OK. N02 malformed date/tz passes. N03 PARTIAL source INCOMPLETE with `data={'items':[{'invoice_id':'SINV-P1A-SYNTHETIC','selection_ref':'p1a_synthetic_ref'}]}` emits actionable ref. N04 data nested FORBIDDEN/private passes. N07 instantiate DTO with valid UUIDs but version/status/reason/capability bogus; model_dump succeeds. Root: source presence not semantic validity, data Any, DTO free strings/domain check only optional to_domain.|Enforce strict shared version/enums/matrix/source validity at construction **and delivery**; OK requires complete authorized evidence; PARTIAL disallows action refs/open; reject raw nested outcome/provider payloads or normalize declared denial before success. Constrain success payload contract without building invoice search/ERP logic now; concrete P2 projections remain later. No competing outcome schema, generic recursive dispatcher or invented source proof.|
|**F03 HIGH — actual log privacy/contract leakage** [ActionEvent:13](E:/lotus-fin/lotus_fin/lotus_fin/application/port/i_action_events.py:13), [record_event:47](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:47)|N08–10 attach logging.StreamHandler(StringIO) to private logging.Logger; record_event with valid UUIDs and one raw context_ref/actor_ref/stage from table; `assert 'P1A_CANARY_7428' not in stream.getvalue()` fails. N11 construct ActionEvent with invalid IDs/capability/pair; accepted. Root: bounded free strings + keyword regex is not controlled metadata/pseudonymization. Current builder tests inspect retained dict and only values containing sensitive keywords.|Validate UUIDs/capability/closed stage/status-reason, permit only approved opaque scope refs/counters. Until trusted pseudonymous context formatting exists, omit/null scope fields rather than accepting raw sid/email/token. Validate/reject inappropriate values before logging; retain fixed stage/code. Test actual logger/output and ValidationError handling with keyword-free canaries, not only adapter memory. No secret-key/platform rollout in P1-A.|
|**F04 MEDIUM — audit sink failure silently treated as recorded** [record_event:54–63](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:54)|N12 injected logger `.info` raises OSError; `record_event` returns None and recorded_events length1. Root: append-before-delivery + catch/pass, no observable failure result for future caller. SSOT §6 requires reliable security events/default capability disable on required-sink outage.|Surface explicit typed delivery failure/result under one documented sink policy; do not report failed delivery as recorded. No capability enabled here, so not a reproduced financial transaction omission. P1-B can enforce future admission only if the port communicates failure. Remove/bound test-only event retention from production path without adding a general audit framework.|
|**F05 MEDIUM — scope/ADR and factual evidence** [delivery test](E:/lotus-fin/lotus_fin/lotus_fin/tests/test_action_delivery.py), builder report25–35|Actual231 lines vs reported196; no approved variance. Outcome test177 vs158. SHA values match; not source drift.|Keep tests cohesive/table-driven within approved cap, preserve current assertions and add missing independent regressions; update factual line counts/current evidence. If an extra test/helper file genuinely needed, obtain narrow allowlist amendment instead of adding it silently. No additional production module/framework demanded.|

For N08–N12 use `ActionEvent(correlation_id=str(uuid.uuid4()),request_id=str(uuid.uuid4()),capability='invoice.search',stage='AUTH_CHECK',**field_changes)` and `SafeStructuredActionEvents(private_logger).record_event(event)`. N11 overrides IDs/capability/status/reason as table. N12 private logger stub only implements info and raises synthetic OSError. Probes execute via `python -B -` under stated containment; ledger stores actual acceptance/emission/outage behavior and process exit1. Corrections must test intended rejection/typed failure, not merely exception of any kind. No proposed live exploit or dependency install.

## 5. Gate decision và P1-B checkpoint

|Gate|Verdict|Evidence|
|---|---|---|
|P1A-G1 CONTRACT|FAIL|N01–04/N07: incomplete success/PARTIAL action/nested failure/strict DTO gaps. Six statuses and matrix already PASS.|
|P1A-G2 FAIL-CLOSED SECURITY|FAIL|N05/06 and F02: final denied data/raw message leakage. No live HTTP/user exploit claim.|
|P1A-G3 CID/OBSERVABILITY|FAIL|CID generation/UUID/header tuple tests PASS; N08–12 privacy/event validation/sink behavior FAIL. Actual HTTP chain NOT_RUN.|
|P1A-G4 LEGACY ISOLATION|PASS within host scope|Guarded imports/network0 +static wiring +protected legacy/source fingerprints unchanged; no enabled action endpoint.|
|P1A-G5 TEST/EVIDENCE REPRODUCIBILITY|PARTIAL|Current hashes/commands/results reproducible, seven builder SHA match; inadequate safety assertions/report line counts and ADR cap require bounded correction.|

Chat **cannot close P1-A yet**. Recommended next eligible work: P1-A correction F01–F05 in same five modules/two tests/report only, fresh impact per AGENTS, no P1-B/API/permissions/dependencies. One independent recheck of corrected focused assertions, no renewed broad architecture or historical F07 cycle.

After closure, P1-B prerequisites remain decisions/fixtures, not functionality tested here: canonical fresh isolated Frappe target/image/import/site/version/apps with reviewed baseline/lifecycle/cleanup; trusted actor/auth-session/site/product/connection/company mapping; exact doc/field/query authorization semantics; key ownership/storage/rotation/expiry for context/ref signing; disabled-by-default explicit routes/admission/CSRF; real ordinary allowed/denied-user multi-company/field/revocation fixtures; approved P1-B §9 paths and §7 budgets/keys/log policy. No shared ai003-verify site, ERPNext helper imports, shared8080 or mutation needed for P1-A closure. Runtime absence does not itself block this foundation; reproduced foundation violations do.

B1-S prior PASS preserved, no current rerun. G3 financial context/G01–G03 backend-session not closed; G10 remains separate BLOCKED/NOT_RUN. P1-A correction does not authorize ERP actions, P2 invoice reads or financial automation.

## 6. Preservation

Before and after tests/reporting:641 tracked aggregate `c751a0b4a1b1f8e48cf47aae91dfe1afb76022b08ad2258bc21c9b3a537a8d84`;2,597 pre-existing review files `e4776aa06b24ec1bc8df48aa128c01f2f9610fa532603a47230e7d14458317a8`; unstaged diff `09344d31c5b694e62eb399cc6461a6388ea77c330fbf1943b127b4f3c56fd3eb`; staged empty. Sorted path/lowercase-file-hash compact UTF-8 JSON aggregate format same previous review. **Preservation PASS**: all eight P1-A artifact hashes, protected aggregates, HEAD/branch/diff unchanged; local report links resolve/fences balanced; packet398 words. [Actual final integrity ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1a-independent-2026-10-11/SOURCE_AFTER.json). Only two review documents and four raw non-executable evidence files created. No application/test/permission/package/data edit, install, site initialization, ERP/provider/network access, Docker mutation, process termination, commit or deploy.
