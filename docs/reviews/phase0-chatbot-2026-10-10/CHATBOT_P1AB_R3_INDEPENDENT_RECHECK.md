# P1-A/P1-B Round 3 — independent recheck

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026 · Independent Backend QA / Application Security.

**P1A_CHANGES_REQUIRED. P1B_CHANGES_REQUIRED. Combined offline acceptance BLOCKED.** Corrections đã đóng phần lớn counterexample trước đó, nhưng A16 còn false delivery/concurrency và B03 còn cấp context khi chưa có quyền Company hợp lệ. Đây là hai blocker đã tái hiện trên production source hiện tại, không phải prerequisite ERP hoặc giả thuyết scale.

Authority: [P1-A R2](CHATBOT_P1A_R2_INDEPENDENT_RECHECK.md), [prior combined](CHATBOT_P1AB_INDEPENDENT_RECHECK.md), [P1 MASTER §3/4/6](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md), [P1-A builder report](E:/lotus-fin/CHATBOT_P1A_IMPLEMENTATION_AND_EVIDENCE.md), [P1-B builder report](E:/lotus-fin/CHATBOT_P1B_IMPLEMENTATION_AND_EVIDENCE.md), [AGENTS](E:/lotus-fin/AGENTS.md), [ADR001](E:/lotus-fin/docs/adr/001-clean-architecture-core-first-adr.md), [Security Code V3 §11–12](E:/lotus-fin/docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md). Không sửa source/test, SSOT hoặc lịch sử.

## 1. Current source identity và scope

**develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2**, staged empty. Tracked dirty vẫn chỉ Panel/Drawer; binary diff unchanged versus prior review. Hai mươi P1 modules/tests vẫn untracked; HEAD không đủ định danh artifact. [Manifest](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/SOURCE_BEFORE.json) ghi full dirty inventory, toàn bộ 22 selected source/report SHA256, authority/runtime, 641 tracked files và 2.632 pre-existing review files. [Full current content](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/SOURCE_CONTENT.json) lưu snapshot cho lần recheck sau.

Delta từ actual P1-A R2 baseline: five production files, two tests và two report append. Tất cả nằm trong correction scopes đã nêu; 13 selected files còn lại unchanged. Không quy toàn bộ pre-existing untracked files cho builder.

|Changed code path dưới lotus_fin/lotus_fin/|Lines including blanks|Current SHA256|
|---|---:|---|
|infrastructure/observability/action_events.py|84|f70b52fda24a423e4ef670f512d353d75ff4954bc467ea81d3a5f24a6452d1c4|
|infrastructure/security/frappe_invoice_authorizer.py|181|7f0e183867cfd29212a0bcac9bf4be0dab6ed0a6b6d8fa43c8b6925d0bd00d12|
|infrastructure/security/action_reference_codec.py|137|e5297a037017852afaae1afea9223ead30be328ee4808e0adf2a68d357c8e3dd|
|presentation/controller/invoice_actions_controller.py|187|88dd38b38529200d47e6bbaff047373b1d3dc34c374331d3ce9095be8f75ce31|
|api/invoice_actions_api.py|83|90ea0be717f55100d53f71fc308c166f4b0955c932bc57d68342b76dfdc1f23f|
|tests/test_action_security_regressions.py|199|dd77f86eb31257c626fc7fc00fded85788c6a20020ce71337cba2ba983198f30|
|tests/test_invoice_context.py|151|2bceb748d01aa7508da7e193ecb7456189f6ef4b1fa4d0528ba40b46129aafc9|

Builder hashes match actual code. Both previous report prefixes remain exact SHA-matched: 287 P1-A lines and 110 P1-B lines preserved. Latest report hashes: P1-A `07ab9a4dda08447353055d5b0a8a9ed1097393096bba79edff0b2d8e7c12a813`; P1-B `05e370c42b62116fb3351cb6764e52b5264e4b12d1c30489a38ffcd896400566`. Their complete-closure claims are contradicted by executions below.

[Exact P1-A diff](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/VERIFIED_P1A_DIFF.patch.txt) uses saved R2 content. [Hash-verified partial P1-B diff](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/VERIFIED_P1B_DIFF.patch.txt) covers controller and context test, reconstructed and matched to prior hashes before comparison. **Evidence gap:** previous full authorizer/codec/API bytes were not retained and are uncommitted; their complete exact historical diffs cannot be certified from hashes/report alone. Current full contents, previous/current fingerprints and current behavior are independently verified; no unverified candidate reconstruction is presented as a diff. [Verification ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/DIFF_AND_ISOLATION.json).

All 20 code files below 200 lines; AST/compile 20/20. Original outcome/delivery/reference/auth-delivery tests unchanged. Context-test diff adds SID to two negative fixtures, preserving assertions. Regression diff retains prior test intents and restores exact N06 message equality; A16 adds ancestor/no-sink checks, but still omits default concurrent delivery and real suppressed delivery. No newly weakened assertion found in verified diffs.

641/641 previous tracked fingerprints and 2.617/2.617 R2 historical review fingerprints unchanged; current review baseline protects 2.632 files. R7 B1-S 13/13 fingerprints unchanged, including packages/lockfile. No unrelated tracked/package/session/ERP change detected. Previous manifests do not fingerprint every unrelated untracked non-review file; universal attribution outside that protected baseline is not claimed.

GitNexus installed cached 1.6.12: both named contexts `SafeStructuredActionEvents` and `FrappeInvoiceAuthorizer` exit1/not found. Current metadata indexed `316c5bd…`, 61 commits behind HEAD. Relevant graph UNKNOWN, not safe/unused. Bounded source tracing: controller → resolve service → authorizer; controller/event port → actual logging adapter; API currently returns disabled outcomes without executing controller/invoice reads. No tooling install or index refresh; no source edits/commit requiring impact/detect-changes. A future correction still needs applicable impact workflow.

## 2. Independent execution

Windows11 build26200; C:/Python313/python.exe, Python3.13.7, Pydantic2.12.5, pytest9.0.2, pluggy1.6.0. Installed runtime reused; Docker NOT_USED. Network audit/import guards installed before production imports. No ERP/LLM/provider access, dependencies, browser or background service.

|Execution|Actual current result / process exit|
|---|---|
|Six existing focused files|**59/59 PASS**, exit0, 3.48s; P1-A41 + P1-B18. Warnings0.|
|Independent N01–N12|**12/12 PASS**, intended assertions.|
|Independent A13–A15|**3/3 PASS**.|
|Prior A16 sequential direct/default ancestor|PASS subcases.|
|Independent C01–C06|**6/6 PASS**: literal matrix 24 allowed/120 rejected, CID/echo/no-store, logger/privacy/import controls.|
|Track A baseline probe ledger|**22/22 PASS**, exit0. This does not qualify all current A16 requirements.|
|Additional actual-default A16 qualification|**6 PASS /2 FAIL**, exit1: healthy/outage × direct/ancestor/root; concurrent root and suppressed required delivery fail.|
|Independent B01–B14|**13 PASS /1 FAIL /0 ERROR**, exit1; B03 fails intended Company/permission assertions.|
|B03 controller public-delivery reproduction|Two failure variants reproduce `200/OK/CONTEXT_READY` + context_ref; exit1. Confirmation of B03, not two new coverage IDs.|

Counts are separate ledgers, **not additive unique coverage**. B03 variants, A16 variants and matrix pairs are subchecks. Focused tests overlap independent requirements. Intentional failure exits correspond to demonstrated defects, not setup/import/UUID errors. ValidationError only accepted for the intended validation field/invariant. Healthy source/sink/reference controls prove probes actually reached the corrected boundaries.

Actual invocation: PowerShell stdin → `python -B -`; `PYTHONDONTWRITEBYTECODE=1`, pytest plugin autoload/cache disabled. `pytest.main` with `-p no:cacheprovider --noconftest -v` plus exactly six paths in its ledger. Raw [pytest ledger](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/FOCUSED_PYTEST.json), [pytest output](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/FOCUSED_PYTEST.txt), [Track A](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/TRACK_A_PROBES.json), [A16](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/A16_REAL_DEFAULT_AND_CONCURRENCY.json), [Track B](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/TRACK_B_PROBES.json), [B03 public delivery](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/B03_PUBLIC_DELIVERY.json). Matching `*_REPRODUCTION.txt` files record full in-memory stdin; no executable runtime/test script created.

## 3. Only material remaining corrections

### A16 — HIGH: required sink falsely acknowledged, shared callback race

[Callback replacement:70](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:70), [restoration:78](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:78), [unconditional delivery count:84](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/observability/action_events.py:84).

Six sequential tests use **actual default `SafeStructuredActionEvents()`**, real StreamHandler, healthy StringIO/failing stream, positioned at direct/ancestor/root. Healthy emits one line/count1; outage raises approved ActionEventDeliveryError/count0; callbacks restored. Previous ancestor defect is corrected.

Concurrency reproduction uses two request-local default adapters sharing one real root StreamHandler. Controlled barriers let A install callback and emit successfully; B saves A's wrapper/installs its own and waits on the handler lock. A finalizes/restores original callback. B's stream then raises OSError; original callback swallows it, B returns success/count1 and restores A's stale wrapper. **Both return success/count1; shared callback not restored.** Probe order triggered, both owned threads finished. This directly violates the requested no concurrency-unsafe callback mutation/no shared state leak invariant.

Same acknowledgment defect also occurs without concurrency: real default logger at WARNING with a healthy root handler suppresses INFO. **Emitted bytes0, no delivery error, recorded_events1.** Finding is required-delivery correctness, not future throughput speculation. A qualified handler's presence and `logger.info()` return are not acknowledgment.

Smallest scoped correction: replace per-request mutation of shared/root callbacks with one owned sink/delivery contract that reports actual success or approved failure. Honor filtering/disabled levels/no sink; increment history only after confirmed delivery. Keep redaction and sequential/default-path assertions; add the two demonstrated cases. A per-instance lock alone cannot synchronize different adapters or unrelated root logger users. No generic audit platform/backend refactor required.

### B03 — HIGH: exact Company permission not checked; unavailable checks fail open

[Company check:112](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:112), [exception swallowed:119](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:119), [authorized return:150](E:/lotus-fin/lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py:150).

The current check calls only `has_permission("Company", "read")`, omitting candidate Company/current-principal scoped proof. Explicit DocType denial now rejects Company and document access. However, a seam permitting Company type read while denying **Company A** still receives no document identity and resolver authorizes. Removing `has_permission`, or making it raise a permission-service outage, also yields authorized context because the code skips/catches the check.

Independent controller confirmation with healthy real required sink returns serializer tuple **200/OK/CONTEXT_READY**, issues context_ref and `AUTHORIZED_READ` provenance for both exact-Company denial and permission outage; log count1 and request/CID controls remain correct. This is public controller delivery evidence with a controlled framework seam, **not actual HTTP or live ERP permission qualification**. Zero invoice/database reads executed.

Smallest scoped correction: require a validated authorization seam and fresh exact principal/company permission before building context/ref. Missing interface/import/exception must produce approved denied/unavailable outcome, never authorized context. Config allowlist alone is not permission proof. Keep document method/search/open disabled without invoice reads; any not-yet-qualified document permission behavior remains unavailable. Add demonstrated Company-specific and unavailable-seam negatives with healthy positive control, preserving strict request/ref/CID contract.

## 4. Track B corrected outcomes

|ID|Current independent result|
|---|---|
|B01/B02|Guest/absent framework principal denied; missing SID AUTH_REQUIRED. PASS each.|
|B03|Explicit type denial PASS subcase; exact Company denial, permission exception, missing permission interface FAIL subcases. Overall FAIL.|
|B04|Forged MAC, wrong purpose, expiry and key rejected. PASS.|
|B05/B06|Eight binding changes rejected; valid control accepted; actual config v1→v2 changes context version and rejects old ref. PASS each.|
|B07|Actual successful public ref decoded: raw synthetic SID/signing key absent; opaque session binding, real event recorded. PASS.|
|B08/B09|Absent required sink503/null; real failing direct StreamHandler raises delivery error/count0, prevents successful return. PASS each; general concurrency remains A16-blocked.|
|B10/B11|Unknown/missing security config rejected/default off/unmapped denied; forged actor/site/session request rejected422/null. PASS each.|
|B12|Enabled-config search/open and disabled context all503/null; measured ERP/business-read spies0. PASS.|
|B13|Actual module reload registers all three exports with allow_guest=False/methods POST; all three JSON/form requests echo valid request_id, equal CID header/body and disabled/null outcome. PASS offline.|
|B14|Direct fake Guest POST / actor GET:401/405 status attributes and no protected data. PASS direct-call only.|

No Guest/Admin/mock authority fallback or legacy AgentRunner/session/DTO wiring in actual new composition was observed, **except the demonstrated unavailable-permission seam bypass**. Constructor identity injection is exercised only by existing isolated tests; actual current API remains disabled and does not compose an enabled controller. MACs confer no authority; typed/frozen model and binding tests do not establish live permissions.

## 5. Integrity, cleanup and gates

All probe runs: network attempts0; real ERP/LLM imports0. Focused pytest blocks13 attempted Frappe imports; they are caught by tested code, not successful imports. Track B only installs explicit synthetic framework objects in private process, removes them afterwards and records0 business-read attempts. Track A production imports match current paths/hashes; Track B records all14 production import identities. No bytecode/cache, source/test edits, listener/service, installation, Docker/data/permissions change or process termination. Logging chain handlers/levels/propagation/disabled flags restored; owned handlers closed and both concurrency threads joined. The production callback leak was observed before reviewer restoration in the private process. Every Python foreground command exited.

[Final integrity](E:/lotus-fin/docs/reviews/evidence/chatbot-p1ab-r3-independent-2026-10-11/SOURCE_AFTER.json) verifies protected files and pre-existing evidence unchanged during review. One preparation command initially failed Windows default text decoding; retry UTF-8 succeeded, not counted as a test. Existing inaccessible pytest-cache inventory warnings are separate from assertions.

|Gate|Current verdict|
|---|---|
|G1 current source/environment|Verified current hashes/imports/dirty inventory; exact historical diff limitation for three uncommitted B files disclosed.|
|P1-A outcome/security/CID|N01–N12/A13–A15/C01–C06 PASS; logging **CHANGES_REQUIRED A16**.|
|P1-B typed context/authorization|Model/isolation present; **CHANGES_REQUIRED B03**.|
|P1-B reference integrity/privacy|PASS offline B04–B07; not an authorization grant.|
|P1-B disabled API/admission|B08–B14 except B03 PASS offline; shared P1-A delivery prerequisite remains open.|
|P1A_INDEPENDENT_PASS|Not earned: **P1A_CHANGES_REQUIRED**.|
|P1B_OFFLINE_CONTRACT_PASS|Not earned: **P1B_CHANGES_REQUIRED**.|
|Combined closure|**BLOCKED** by demonstrated A16/B03 violations.|
|P1B_LIVE_AUTHORIZATION / ERP target|**NOT_RUN / BLOCKED pending separate qualified target**.|
|B1-S prior R7 PASS|Preserved source/evidence; no browser/harness rerun or new runtime claim.|
|G3 finance / G01–G03 session/backend|Unqualified, not closed by these tests.|
|G10 judge deployment|**BLOCKED independently**.|

Live authenticated HTTP/CSRF/status/envelope/header delivery, actual Company/doc/field/revocation permissions and serving image lineage NOT_RUN. No authorized isolated target baseline for this pass. Unrelated financial/browser suites and performance tests NOT_RUN by scope; no p95/throughput/RSS claim from unit timings.

Chat cannot close either batch offline yet. Next proposed batch is only scoped A16 and B03 correction, then independent recheck with preserved assertions. After offline closure, separately qualify trusted Lotus Fin→ERP site/product/config map, installed app/custom-hook lineage, principals/Company/doc/fields/revocation, key policy, required sink and fresh private baseline/lifecycle/cleanup plus real HTTP/CSRF. Only then consider separately approved P2-A bounded invoice search/select/open. No invoice action, financial automation, P2 implementation or G10 release authorized by this review.
