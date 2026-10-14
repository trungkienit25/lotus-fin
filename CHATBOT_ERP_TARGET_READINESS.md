# Lotus Fin P2-A/P2-B ERP target readiness

12 October 2026 · Asia/Saigon · read-only discovery and approval gate.

**PRIVATE_TARGET_READY = BLOCKED.** No complete, explicitly approved isolated target for this task was found. Stop before target mutation, build, site provisioning, credentials, fixtures, deployment or feature enablement. The authorized work completed here is discovery and a concrete qualification handoff.

| Required verdict | Result | Exact scope |
|---|---|---|
| PRIVATE_TARGET_READY | BLOCKED | Mandatory owner, named private target, fixtures and lifecycle approval absent. |
| ADAPTER_IMPLEMENTATION | BLOCKED | Conditional phase not entered; abstract read port exists, concrete ERP adapter not implemented here. |
| REAL_HTTP_ACCEPTANCE | NOT_RUN | No actual route/session/auth/CSRF requests executed. |
| ERP_PERMISSION_ACCEPTANCE | NOT_RUN | No installed-site or ordinary-user Company/DocType/document/field/custom-hook tests. |
| ERP_NO_WRITE | NOT_RUN | No private fixture before/after business and framework side-effect snapshots. |
| P2AB_LIVE_ACCEPTANCE | BLOCKED | Target/source/adapter/HTTP/permission/resource/no-write gates outstanding. |
| G10 | BLOCKED | Judge packaging/entrypoint and independent qualification unresolved. |

Fresh source-to-serving-runtime comparison: **FAIL, 17/17 selected files absent**, separate from the blocked private-target verdict. Existing writable-layer app drift also prevents the image digest from identifying the live source; see runtime qualification. Historical offline acceptance is not a new live PASS.

## Evidence identity and authority

Repository/worktree: `lotus-fin / E:/lotus-fin`; branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Twelve tracked paths were already modified; numerous untracked documents, deployment inputs, frontend modules and correction tests were already present. HEAD is insufficient to identify the artifact.

Unique evidence: [discovery directory](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/), [identity](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/IDENTITY.json), [580-file pre-write manifest](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/SOURCE_BEFORE.json), [commands and outputs](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/COMMANDS.json), [17-path comparison](docs/reviews/evidence/chatbot-private-erp-discovery-2026-10-12-1655-a12f82/HOST_RUNTIME_COMPARISON.json). The manifest covers current application/frontend/build/primary authority documents, not every historical evidence file or the large `my-skills` tree. Original byte hashes, captured tracked diff and status are retained. The initial empty staged-diff pipeline created no file; the current explicit staged-state check is empty, and no baseline staged hash comparison is claimed. Text diff capture uses PowerShell UTF-8; it is not a raw Git blob hash.

Authority read: [AGENTS](AGENTS.md); [P1 MASTER](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md); [Security Code V3](docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md); [ADR001](docs/adr/001-clean-architecture-core-first-adr.md); [frozen P2-B wire](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2B_WIRE_CONTRACT.md); P1 final fix/evidence and later P2-A correction/independent acceptance; [P2AB independent recheck](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2AB_INDEPENDENT_RECHECK.md); [prior target qualification](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2A_LIVE_TARGET_QUALIFICATION.md); [judge reconciliation](docs/reviews/phase0-chatbot-2026-10-10/JUDGE_RELEASE_RECONCILIATION_PLAN.md); current Docker/runner/README/fixture instructions. P1 MASTER retains its historical proposed header; use the subsequent frozen wire and current accepted implementation evidence for the qualified offline shapes. No contract freeze/amendment made here.

## Approval search and boundary

Searches covered current `docs` excluding historical evidence copies, primary phase0 reports, specs, runtime, Docker, CI and README, using private-target/site approval, owner, ordinary-user/oracle, snapshot/restore and key/sink lifecycle terms. Exact commands and candidate files are recorded. No complete P2 approval record was found in inspected project material; this does not assert that no approval exists outside the repository.

Historical AI002 fixture instructions authorize `frontend` only for AI002 on 26 September. AI003 cleanup scripts target `ai003-verify.localhost` and commit deletes/cancellations. Judge reconciliation explicitly remains a proposed release plan. None authorizes this task. Shared `frontend`, `ai003-verify`, production, judge and unrelated containers are excluded.

| ID | Mandatory missing approval/evidence | Responsible role to be named | Closure artifact |
|---|---|---|---|
| A01 | Named human target owner and isolation boundary | ERP/Ops owner | Signed/dated task-scoped approval naming host, Compose project, site, image, network, containers and owned volumes; exclusions explicit. |
| A02 | Authorized source/build/deployment scope | Release + backend owner | Commit plus dirty/untracked file manifest, reviewed recipe/base/platform, private tag/digest and precise allowed edits/build/start operations. |
| A03 | Approved ordinary accounts and authentication lifecycle | ERP security owner | Allowed and denied ordinary principals; authorized login/logout/disable/revoke operations; secure credential provisioning reference, no secrets in reports. |
| A04 | Companies and document fixtures | ERP owner + independent QA | Approved synthetic Company A/B, exact allowed/denied/shared/deleted/stale invoices and row/date/version ledger; fixture creation/removal scope. |
| A05 | Independent field/custom permission oracle | ERP security + QA | Effective roles, User Permissions, shares/owner rules, DocPerm/Custom DocPerm, field permlevels/masks and query/controller hooks with expected results derived independently. |
| A06 | Snapshot, restore, cleanup and rollback | Ops owner | Baseline ID/hash, DB/files/config/cache scope, restore rehearsal and verification, exact owned resources eligible for cleanup; failure procedure. |
| A07 | Site/company/connection/projection/timezone ownership | Backend + ERP owner | Exact server map and version, allowed site routing and companies, actual System Settings timezone, required schema/projection and change invalidation policy. |
| A08 | Signing-key lifecycle | Security/Ops owner | Custody/provisioning reference, key ID and rotation/retirement policy, token TTL/config-version invalidation, disposal; no key values exported. |
| A09 | Required audit sink lifecycle | Security/Ops owner | Sink acknowledgement/availability contract, access/retention/rotation/disposal, private failure injection/restore; required app events separated from ERP writes. |
| A10 | Mutation and outage-test boundary | Target owner + QA | Explicit permission for fixture/revocation/schema/session/key/sink/timeout tests, migrations if needed, queue/scheduler/email/provider containment and cleanup. |

All role names above are proposed responsibilities; no human approval or owner has been invented. Existing config DTOs, apps.txt, running containers or Admin credentials do not satisfy these rows.

## Readiness checklist

- [ ] A01–A10 approved together against the same task, target and artifact; operator verifies no resource overlaps an excluded project.
- [ ] Materialized source bytes match an approved manifest including required dirty/untracked code; reviewed exclusions and dependencies are complete.
- [ ] Pinned base/platform/dependency inputs and resulting immutable image identified; all serving workers use it and import expected modules.
- [ ] Installed-site ERPNext/Lotus app versions/order, hooks/customizations, schema and timezone verified on the approved target.
- [ ] Ordinary principals and independently owned fixture permission oracle installed only under the approved mutation scope.
- [ ] Config/key/sink composition is qualified, fail-closed and owned; no Administrator substitution or frontend authority.
- [ ] Snapshot restoration and cleanup rehearsed, including framework caches/files/queues and temporary permission changes.
- [ ] Concrete bounded adapter and actual HTTP middleware pass the matrix in the adapter report.
- [ ] Business and relevant lifecycle side-effect deltas reviewed; physical SQL/rows/bytes/deadlines measured.
- [ ] React transport is connected only after live acceptance and separate enablement approval; judge gate executed separately.

## Safe sequence after operator authorization

1. Resolve A01–A10 in a dated approval packet. Approve exact new private names and operations; do not reuse existing sites by inference.
2. Review/materialize the source and dependency manifest, private build recipe and platform; build using the conditional commands in [runtime qualification](CHATBOT_PRIVATE_RUNTIME_QUALIFICATION.md). No shared tag overwrite.
3. Provision only the approved private target, verify installed-site metadata, bootstrap ordinary-user fixtures and rehearse snapshot restore. Provision keys through the approved secret channel and bind the required sink.
4. Perform fresh graph impact on the exact modules to be edited; implement the narrow in-process adapter and HTTP composition. Preserve accepted P1/P2-A outcomes, references, projection and disabled rollout policy.
5. Execute real permission/HTTP/resource/no-write tests and restoration/cleanup; retain negative outcomes rather than replacing them with synthetic evidence.
6. Review the artifact and live evidence before enabling UI/API. G10 requires its own approved source/entrypoint and independent judge run.

## Graph checks and edit scope

GitNexus 1.6.12 binds exactly `E:/lotus-fin`, indexed HEAD above at `2026-10-12T07:02:27.060Z`, 166057 symbols/547 processes. A current dirty-tree freshness certification was not obtained: the read-only `status` command stalled and was interrupted. Concept query returned empty with FTS disabled. Named controller lookup was ambiguous across 26 historical/current copies; exact current UID resolved its four test importers and methods. Upstream controller impact returned **UNKNOWN**, zero resolved callers/processes, with its explicit warning; text confirmation shows test consumers and no public API/controller composition. This is unresolved operational risk, not unused code or LOW.

All four requested report names received pre-write impact attempts: not indexed / **UNKNOWN**. File existence and text checks confirmed they were absent and had no current references. Only new documentation/evidence was added; no function/class/method, existing deployment input or authority report was edited. No commit/push, so the pre-commit change-analysis gate was not invoked as a commit approval. A future implementation/commit requires fresh complete graph checks.

**Next operator authorization:** provide a dated A01–A10 packet naming the private target, owner, ordinary accounts, companies/documents, independent field/custom-hook oracle, source/image scope, allowed mutations, key/sink ownership, tested snapshot/restore/cleanup and rollback. Phase 3–6 work remains blocked until that packet exists.
