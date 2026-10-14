# Phase 0 — gates and evidence

**Current targeted follow-up:** [Round 2 matrix below](#round-2--targeted-readiness-10102026) supersedes only T1/B1-S/V1 readiness. The original Phase 0 ledger remains dated history; it does not prove judge-image or current UI acceptance.

10/10/2026 · **CHANGES_REQUIRED / NO_IMPLEMENTATION_BATCH_READY**. [Reproduction/current manifest](../evidence/phase0-chatbot-2026-10-10/REPRODUCTION.md). Branch develop/HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; application/authority fingerprints recorded separately from runtime/image. None of the following inherits a historical PASS across deployment or scope.

## Gate matrix for selected V1

| Gate | Result | Verified now / exact missing acceptance |
|---|---|---|
| G1 runtime/source/topology/capability | **PARTIAL** | Docker/package/process/routing/current hashes read successfully. Clean target acceptance **BLOCKED**: no reviewed isolated site/snapshot lifecycle/cleanup; per-site apps/custom fields/roles/effective principal/connection/company and resident modules NOT_VERIFIED. Host/runtime fork remains. |
| G2 business + typed contract | **PARTIAL** | V1 selected independently; typed boundary PROPOSED. Chat must decide term-aware versus limited final-due overdue, cutoff/precision/currency/credit policy, target/identity binding and status/bounds. No frozen contract. |
| G3 data/method + authoritative source | **BLOCKED** | Installed permission-aware APIs/schema/source inspected. Current overdue source/term allocation/status freshness/field permissions not qualified on selected site. No authority from current outstanding for historical settlement. |
| G4A pre-build security/evaluation | **PARTIAL** | Threats/minimum assertions designed, existing source defects documented; executable pilot evaluation and allowed/forbidden clean source oracle **NOT_RUN/BLOCKED**. Schema/error/status/transport/URI/injection/bounds assertions still required. |
| G4B postimplementation delivery | **NOT_RUN** | Pilot not implemented; no current live HTTP/browser or fresh-worker acceptance. Historical unit green is not G4B. |
| G10 deployment/image lineage | **BLOCKED** | Offline exact image missing3Copilot/session files, financing differs; current runtime patches differ from host. Reader cleanup PASS only. Need approved canonical artifact/revision, fresh new-worker/site smoke and resident app identity proof. |
| G01 session ownership | **NOT_APPLICABLE** to proposed stateless V1 use case; **BLOCKED** if existing stateful AI007 selected | Host save ownership gap; runtime-only fixes not sufficient. Require crossbinding/revocation/atomic ownership tests for selected session path. |
| G02 shared storage/lifecycle | **NOT_APPLICABLE** to stateless V1; **BLOCKED** for stateful AI007 | Runtime cache adapter does not establish distributed storage semantics/outage/corrupt-vs-missing tests. No memory fallback qualification. |
| G03 concurrency/lease/commit | **NOT_APPLICABLE** to stateless V1; **BLOCKED** for stateful AI007 | Real multiworker create/race/lease-expiry/stale-writer/CAS-fencing/outage tests NOT_RUN. Merely calling a stateless invoice tool from the existing stateful chat does not waive these gates. |

F102 scope/facts/gates remain solely [MASTER_SSOT §7/§7.7](../../features/F102/F102_MASTER_SSOT.md), PROPOSED/CHANGES_REQUIRED; no new F102 probes/build in this follow-up. F101 discovery. V1 invoice reads do not require full Income/COGS remediation. Security CodeV3 bankR4/R5 DENY and separate mutation scope remain.

## Actual evidence ledger

| Check | Actual outcome | Boundary |
|---|---|---|
| Git revision/diffs/fingerprints | PASS metadata;333/333 host hashes match previous final snapshot | Many pre-existing untracked files; not a clean checkout, not deployed identity |
| Docker actual connectivity | PASS server29.1.3 | Before Docker use; no site/business acceptance |
| Runtime package/process/topology/routing | PASS read-only inventory | Frappe16.34/ERPNext16.35/Lotus0.0.1; no per-site DB/schema/permission runtime assertions |
|15 runtime files | PASS capture;15 unchanged previous runtime; host/runtime alignment **FAIL** (4byte-match) | Prior normalized comparison:10content-different,1line-ending; source file read is not resident import proof |
| Offline baked image read | Exit1: missing files, alignment **FAIL**; cleanup PASS0remaining | No network/mount/site/import/server, not new-worker acceptance; error is artifact gap, not executed financial assertion |
| GitNexus freshness/refresh | Stale61commits; TIMEOUT45s | Repo runner entered package manager; stopped. Offline cached CLI correction used; no package compatibility or safety PASS from graph |
| Cached query/context/impact | Copilot query TIMEOUT10s; controller notfound; invoice historical fixture flows; audit impact UNKNOWN | No actual current read path resolved; bounded static trace follows. Missing/UNKNOWN not safe/dead. |
| Current source inspection | VERIFIED static observations | Numbered source + hashes; no attack/revocation HTTP reproduction |
| Installed ERP methods/schema/overdue source | PASS file capture | updater is mutation code inspected only, never called; no target metadata override or business fact verification |
| Official REST/client review | Primary docs/source inspected | API shape, wrapper sync/pagination/error surface; target compatibility/maintained guarantee NOT_VERIFIED; no SDK installed |
| New unit suites/probes this follow-up | **NOT_RUN** | No source/test changes; no need to repeat prior arithmetic. No145test total claimed as new execution |
| 09/10 hermetic tests, historical |145PASS across8suite processes; architecture module LOADER_ERROR0assertions | Historical source snapshot now matches selected hashes, but mock/fake/source boundary unchanged; not current live acceptance |
| Real ERP permission/data/Redis/session HTTP/browser/provider | **NOT_RUN**; clean baseline prerequisite BLOCKED | Shared frontend/contaminated ai003 site excluded; no Administrator-only shortcut |
| Representative calls/latency/p95/throughput/RSS/SQL | **NOT_RUN** | Static4report callbacks/snapshot ≠4SQL/HTTPcalls; suite elapsed time not latency acceptance |
| Mutation/create/update/submit/cancel/send | **NOT_RUN / disabled** | Zero discovery ERP action calls; no shared data/perms/deploy/Redis flush |

Historical [test ledger](../evidence/existing-features-discovery-2026-10-09/RESULTS.json) retains exact commands/exits and mocked boundaries. Loader/import failures and inspection invocation errors are separate from assertion FAIL. No actually-run live threat case or pilot gold is manufactured.

## Designed acceptance, not executed

| Risk | Required assertion | Gate/dependency |
|---|---|---|
| Crossuser/company/site/product/connection | Bind server context; deny list/detail/reference/cursor under wrong scope, no payload/existence leak | G1/G3/G4A/B |
| Revocation/field permission | Reauthorize every lookup and cache reuse; clear stale financial facts | G3/G4A/B |
| Forged reference/cursor/proposal | Reject altered/expired/binding mismatch; client checksum/claims never elevate trust | G4A/B; proposal only future writes |
| Source semantics | Independent installment/final-due/partial/return/credit/write-off/POS/currency oracle; missing vs verified zero vs outage | G2/G3 |
| Prompt injection/unsafe URL | ERP/customer text cannot add tool/endpoint/recipient/scope; navigation encoded and bound to approved UI | G4A/B |
| Status/raw errors/provider empty | Same typed outcome source→tool→API→UI; recursive marker absent in response/widget/model/log; oneCID | G4A/B |
| Deadline/retry/paging | Cap atN+1, cancellation, explicit PARTIAL/coverage; no false NO_MATCH/total; measure calls/bytes separately | G2/G4A/B + qualification |
| Company switch/session race | Fence late response and clear old data; qualify actual shared session ownership/atomic commit if used | G4B/G01–G03 conditional |
| Future write duplicate/timeout-after-commit | Approval exact args/version/recipient/actor/expiry; revoked/stale deny; mismatched key deny; UNKNOWN_OUTCOME reconcile without blind retry | Disabled mutation scope, NOT_RUN |

## Batch readiness

| Batch | Current disposition | Minimal next work |
|---|---|---|
| B0 canonical deployment/isolation | **Verification next, not an implementation dispatch** | Identify exact judge target/canonical artifact, review fresh baseline lifecycle+cleanup and per-site metadata/principals; no shared bootstrap |
| B1 existing correctness/security | Candidate, not eligible | P0-01 fake UI truth and selected authority/error/source paths; approved narrow contract + impact/regressions, avoid system-wide rewrite |
| B2 public UI/use-case alignment | Candidate, not eligible | Chosen capability contract; distinguish F004/F005, typed status/provenance; no frontend financial fallback |
| B3 invoice read/navigation | First vertical slice, not eligible | Close relevant G1–G4A target/source/semantics/evaluation; exact files/public names/allowed edits/rollback packet |
| B4 Copilot integration | Conditional candidate | Selected orchestration/schema/budget/status route; qualify session gates if retained |
| B5 ERP mutation | Disabled design only | Separate approved business/lifecycle/approval/idempotency/unknown-outcome scope |

**NO_IMPLEMENTATION_BATCH_READY.** Chat scope/contract arbitration → Work bounded missing verification → approved implementation packet for at most one batch → Antigravity → Work G4B → Chat closure. No freeze or dispatch here.

## Round 2 — targeted readiness, 10/10/2026

**B1S_CHANGES_REQUIRED · V1_SOURCE_BLOCKED · DEPLOYMENT_BLOCKED · NO_IMPLEMENTATION_BATCH_READY.** Only T1/T2/T3 reviewed; no broad AI feature retest, application edits, new packages, site/bootstrap or business reads. [Canonical artifact](CANONICAL_ARTIFACT_AND_TARGET_VERIFICATION.md), [B1-S packet](B1S_COPILOT_UI_FAILCLOSED_PACKET.md), [V1 source closure](V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md), [current raw outcomes](../evidence/phase0-round2-2026-10-10/RESULTS.json).

| Gate | B1-S UI safety | V1 read/navigation |
|---|---|---|
| G1 canonical source/route/test target | **BLOCKED**: exact host source/two callers verified; locked isolated React build/runner unavailable, scope-context integration unresolved | **BLOCKED**: installed source verified; canonical release/site/apps/fields/principals/current permissions not qualified |
| G2 selected behavior contract | **PARTIAL**: proposed typed compatibility/failure/race policy; cutoff/server-context and ADR/file-set approval missing | **PARTIAL**: restricted B recommended, not approved; currency/credit/POS/missing-date/coverage policy and query consistency open |
| G3 provenance/source | **PARTIAL**: current DTO lacks authoritative root provenance/CID/context; neutral legacy rendering and badge suppression proposed, qualified source envelope not verified | **BLOCKED**: current final-date/residual/currency/precision/field authorization and reconciliation oracle NOT_RUN; A term allocation unqualified |
| G4A pre-build evaluation/security | **PARTIAL**: exact negative/positive DOM assertions designed; runnable isolated frontend fixtures/context prerequisites missing, tests NOT_RUN | **PARTIAL**: permission/reference/cursor/injection/date/coverage oracle assertions designed, executable isolated source qualification missing |
| G4B post-build delivery | **NOT_RUN**: no implementation or actual browser acceptance | **NOT_RUN**: use case absent; no source HTTP/UI/mutation-absence acceptance |
| G10 immutable deployment | **BLOCKED**, separate gate: current judge image missing route dependencies/React delivery; no fresh worker/site | **BLOCKED**, separate gate: manifest/recipe/target conflict; no fresh worker/site |
| G01–G03 session gates | **NOT_APPLICABLE** to the proposed local presentation patch; does not qualify existing stateful backend | **NOT_APPLICABLE** to stateless use case; **BLOCKED** for stateful AI007 integration |

| Actually-run Round 2 check | Result | Boundary |
|---|---|---|
| Revision/333 protected host hashes | **PASS**: 333/333 match previous snapshot; tracked/staged diff empty | Many pre-existing untracked inputs; canonical release not selected |
| Docker connectivity/source/config reads | **PASS**: server29.1.3, installed versions/source captured | No site/business/API execution |
| Exact cached graph fingerprint | **PASS** | No package manager/download/refresh used |
| Current graph route/impact resolution | **NOT_RUN** current-flow qualification; bounded CLI completed with notfound/UNKNOWN, historical query only | Stale61commits; no “no callers” or safe blast-radius conclusion |
| Host/runtime/image alignment | **FAIL** selected alignment: host/runtime4byte-match of15; old judge missing7 selected files and differing API | Installed disk is not resident-worker proof; runtime fixes remain candidates |
| Judge offline package resolution | **PASS** root import/API spec lookup only | presentation/application specs absent; no API dependency import/new worker/HTTP |
| Offline reader/layout file probes | Missing-file exits1/2, **FAIL** completeness | Artifact inspection, not financial assertion failures; cleanup PASS0remaining |
| Selected UI and active ERP query source | **PASS** capture/trace | Two panel callers; actual installed get_list uses qb_query→database.query, not just old db_query |
| B1-S DOM/ERP permission/source oracle/session/load | **NOT_RUN** | Frontend prerequisites absent; no reviewed clean baseline; no historical PASS inherited |
| ERP mutations/provider calls/shared-bootstrap | **NOT_RUN / disabled** | Zero discovery ERP business RPC/read/write calls; no paid LLM/outbound documents |

Inspector invocation errors (wrong preliminary filenames, PowerShell parse/rg wildcard mistakes) are recorded separately; successful captures use corrected actual paths. No product assertion is inferred from those errors. B1-S and V1 bounds remain designed, not measured SLOs. F101/F102 authority unchanged and neither gates standalone invoice V1.

**Targeted next work:** Chat decides the narrow B1-S context/cutoff/ADR policy; provide the locked isolated React test target and run deterministic DOM cases. Separately reconcile judge recipe/entrypoint and approve fresh baseline; then qualify B's invoice fields/permissions/current residual/date oracle. No additional broad architecture discovery, contract freeze or implementation dispatch.
