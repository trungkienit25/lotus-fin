# Lotus Fin — architecture work-to-agents handoff

13 October 2026 · Asia/Saigon · `E:/lotus-fin` · **REVIEW HANDOFF ONLY — NOT A DISPATCH OR APPROVAL**.

Read in order:

1. [N0 approval sheet](LOTUS_FINAL_N0_APPROVAL_SHEET.md): exact human decisions, pending owners and five verdicts.
2. [Full dependency inventory](LOTUS_FULL_ERP_DEPENDENCY_INVENTORY.md): current file/caller/profile evidence, graph results, hashes and concurrent source drift.
3. [Native architecture proposal](LOTUS_NATIVE_ARCHITECTURE_FROZEN_PROPOSAL.md): owned metadata architecture and finance limitations. “Frozen proposal” is not approved contract freeze.
4. [Token/permission migration](LOTUS_TOKEN_PERMISSION_MIGRATION_PLAN.md): proposed native version/source/claims, old-token rejection and fresh grants.
5. [Full execution plan](LOTUS_FULL_INDEPENDENCE_EXECUTION_PLAN.md): dependency order, exclusive ownership, acceptance and stop boundaries.

## Non-negotiable constraints

The **entire Lotus Fin release** must work without ERPNext application installation, schemas, roles, reports or credentials. Frappe Framework is allowed. Do not copy/rename Sales Invoice, Company, GL Entry or Accounts Payable as native authority. Do not quietly disable advertised finance and claim full independence. A Product-approved reduced pilot remains a reduced pilot; the full-product gate remains open.

No native invoice/tenant source is approved. Do not build a tabSales Invoice “native adapter,” relabel ERP_READ or treat synthetic fixtures/DTOs/hardcoded profiles as operational data. Recommendations here are PROPOSED. Human source/policy/wire/target decisions must be recorded before dependent implementation. This document does not authorize site/user/secret creation, migrations, commit/push or deployment.

## Current source reconciliation required before future work

Repository branch `codex/p2a-invoice-read-backend`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`; newest subject is working source including untracked files. Root [AGENTS](AGENTS.md) requires graph-first exploration, exact upstream impact before edits, UNKNOWN confirmation and change analysis before a separately authorized commit. Use exact production UIDs because the index contains old evidence copies; FTS-disabled empty results are not proof of no callers.

Actual current [controller](lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py) calls injected Search/Open services. [HTTP API](lotus_fin/lotus_fin/api/invoice_actions_api.py) preserves strict Request/Response disabled admission; [production frontend transport](frontend/src/pages/copilot/actions/invoiceActionClient.ts) remains disabled. No production concrete native read port was found. Avoid repeating historical unconditional-controller and double-wrap findings as current defects.

Concurrent work outside this decision task added [Frappe-only Dockerfile](docker/lotus-core/Dockerfile), [compose](docker/compose.lotus-core.yml), [guarded helper](docker/lotus-core/manage.py), [runtime request boundary](lotus_fin/lotus_fin/runtime/boundary.py), cleared ERP hooks/fixtures, removed the Company custom-field fixture, declared dependencies and changed default `run.ps1`/`run.sh`. Reassess these exact bytes and any newer evidence before P0 editing. Do not overwrite them from old reports. Their existence does not prove native finance, React route independence or release acceptance. Source is moving; recapture a stable candidate.

The final reread also confirms hooks no longer include legacy JS, app_home is `/app`, the Desk workspace is hidden/empty, and core DB/Redis image digests are pinned. New HTTP qualification/provisioning/packaging scripts are source only in this review; they were not run here. FollowupPreview.tsx changed concurrently, so inherited L3 acceptance does not certify its current bytes. The inventory's final verification section records these observations and their hashes.

Final inspection also found [integrations/lotus_erpnext](integrations/lotus_erpnext/README.md), a separate prototype requiring ERPNext/Lotus and an explicit qualification flag, excluded from the core app copy. Its own README records no business/security acceptance. Reassess its current hooks/install/events/fixture files; do not describe it as absent or approved. Whole-product native source migration remains required; prototype separation alone does not prove optionality of advertised financial behavior.

The [latest N0 packet](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/N0_PRODUCT_DATA_SECURITY_DECISION_PACKET.md), [execution](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/LOTUS_CHATBOT_FINAL_INTEGRATION_EXECUTION.md), [work-to-chat](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/LOTUS_CHATBOT_FINAL_WORK_TO_CHAT.md) and [manifest](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/SOURCE_MANIFEST.json) are dated13 October. They report improved offline coverage and N0/live blockage. Later source changes invalidate using that manifest as today's complete acceptance identity. Inherited backend438/UI fixtures/finance393+7 are scoped and overlapping, not current full-product PASS.

## Future assignments — owners not yet named

| Slot | Assignment and disjoint ownership | Admission / output |
| --- | --- | --- |
| Human Product/Data/Security | Close exact N0 IDs; choose existing owned service or approve independently authored metadata source and separate financial authorities | Signed names/date/decision/version hashes, schema/update/grants/lifecycle and numeric SLA/audit answers. Do not delegate human approval to an agent. |
| P0 Platform | Runtime/images/helpers/hooks/package/install/contained legacy boundary | Separately authorized source/artifact work; qualified Frappe-only shell with source→image→worker evidence. Native data approval is not needed to review packaging. No full finance claim. |
| P1 Data + Security | Data owns native storage/update/migration design; Security owns principal/grants/context/source/claims/config interfaces. No overlapping file writes | Wait for signed N0; one native authority/policy and successor contract; ordinary-user/row/field/revocation oracle. |
| P2 Backend Read | Existing typed read services/ports, approved adapter, DTO/controller/API/delivery | Wait for P1/P0/sink/target; genuine native Search/Open+HTTP. Preserve current HMAC/config/response/delivery fixes. |
| P3 Frontend | All React behavior/routes/providers/catalog/bundle tests | Wait for wire/HTTP/product route approval before transport/mount; ordinary native browser journey and no required ERP selectors/routes. |
| P4 Financial | Native finance sources, composition/engines/API/tool/plugin/legacy agent migration | Wait for per-source N0-13; preserve formulas, coverage and DEMO_ONLY constraints; all included AI/report features work without ERP. |
| P5 Independent QA/Security | New cohesive native acceptance tests/CI/evidence, read-only production inspection | Wait for immutable artifact and approved lifecycle; independent native security/no-write/finance/rollback evidence; human G10 acceptance separate. |

Exact file ownership is in the execution plan. Shared contract edits require sequential transfer. Do not spawn or message agents merely because this handoff exists; implementation dispatch needs a later authorized task and applicable delegation instructions. No agents were dispatched by this decision package.

## Handoff exit and open decisions

Current verdicts: **N0_DATA_AUTHORITY BLOCKED; CORE_INDEPENDENCE_READINESS CHANGES_REQUIRED/NOT_VERIFIED; FULL_PRODUCT_INDEPENDENCE_READINESS FAIL/CHANGES_REQUIRED; NATIVE_SECURITY_CONTRACT PROPOSED/NOT_APPROVED; IMPLEMENTATION_READY NO for native/full-product implementation.** P0 review/preparation is separable from native implementation approval.

Open: all N0-01…N0-15 decisions, named human owners, stable source/artifact, source/tenant/grant schemas, authority/update/reconciliation, source/reference versions, numeric freshness/revocation/audit policies, native financial feeds, complete product scope and independent release qualification. Optional ERP integration remains deferred; L3/V1/F101/F102/L4/L5 are not automatically approved. Security V3 bank-write denial remains.

**STOP after the six decision documents. No source modification, migration, commit, push or deployment by this task.**
