# Lotus Fin — final N0 approval sheet

13 October 2026 · Asia/Saigon · Repository `E:/lotus-fin` · **PROPOSED / NOT APPROVED**.

This is a human decision package, not implementation authorization. The user's requirement is authoritative: the entire Lotus Fin release must work without the ERPNext application, installation, schemas, roles, reports or credentials. Frappe Framework is permitted. No approval of a native invoice/tenant authority has been supplied. No source changes, migrations, provisioning, deployment, commit or push are authorized in this task.

## Verdicts

| Verdict | Decision | Evidence / remaining condition |
| --- | --- | --- |
| N0_DATA_AUTHORITY | **BLOCKED — PROPOSED, NOT APPROVED** | No operational Lotus-owned tenant/membership/invoice implementation found. Product/Data must choose and sign the source and update authority. |
| CORE_INDEPENDENCE_READINESS | **CHANGES_REQUIRED / NOT_VERIFIED** | New concurrent Frappe-only runtime files are present; source intent is credible, but this review did not build/start/qualify them. Current API reads remain disabled. |
| FULL_PRODUCT_INDEPENDENCE_READINESS | **FAIL / CHANGES_REQUIRED** | Financial providers, Desk page role declarations, Company selectors, reports and dynamic React routes still encode required ERP dependencies. Quarantining them does not migrate their advertised capabilities. |
| NATIVE_SECURITY_CONTRACT | **PROPOSED / NOT_APPROVED** | HMAC, typed services and audit delivery are reusable. Native membership, grants, identity, source mode and successor reference semantics remain unsigned. |
| IMPLEMENTATION_READY | **NO for native/full-product implementation** | P0 analysis and packaging review can proceed in a separately authorized task. P1–P4 require the approvals below; P5 needs a qualified artifact and fixture lifecycle. This task ends with documents. |

## Current evidence and precedence

Assess the working tree, including untracked files, on branch `codex/p2a-invoice-read-backend`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. HEAD alone is not the candidate. See the [full inventory and source observation ledger](LOTUS_FULL_ERP_DEPENDENCY_INVENTORY.md).

Read authorities: actual [AGENTS.md](AGENTS.md); accepted [ADR001](docs/adr/001-clean-architecture-core-first-adr.md); [Security Code V3](docs/security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md); [P1 MASTER](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md); [P2-A handoff](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md); [frozen P2-B wire](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2B_WIRE_CONTRACT.md). The earlier [product audit](LOTUS_FIN_PRODUCT_INDEPENDENCE_AUDIT.md), [dependency matrix](LOTUS_FIN_ARCHITECTURE_DEPENDENCY_MATRIX.md), [authority map](LOTUS_FIN_NATIVE_DATA_AUTHORITY_MAP.md), and [native integration design](LOTUS_FIN_CHATBOT_NATIVE_INTEGRATION_DESIGN.md) are inputs, not proof of today's source.

The latest located [N0 packet](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/N0_PRODUCT_DATA_SECURITY_DECISION_PACKET.md), [execution report](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/LOTUS_CHATBOT_FINAL_INTEGRATION_EXECUTION.md), [work-to-chat](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/LOTUS_CHATBOT_FINAL_WORK_TO_CHAT.md), [source manifest](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/SOURCE_MANIFEST.json), and [gate ledger](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/GATE_VERDICTS.json) report offline readiness and live/N0 blockage. They do not record native authority approval.

Current corrections supersede old structural claims: [controller](lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py) executes injected Search/Open services; [API](lotus_fin/lotus_fin/api/invoice_actions_api.py) uses Werkzeug Response and strict admission but still returns disabled; [transport](frontend/src/pages/copilot/actions/invoiceActionClient.ts) still does no network I/O. Concurrent [core Dockerfile](docker/lotus-core/Dockerfile), [compose](docker/compose.lotus-core.yml), [hooks](lotus_fin/lotus_fin/hooks.py), and [boundary](lotus_fin/lotus_fin/runtime/boundary.py) were inspected, not implemented or accepted by this review. The old Company fixture was removed concurrently. No current stable full-product candidate is certified.

Final reread: default helpers now target Frappe-only core; hooks unload legacy JS and use `/app`; Workspace is hidden/empty; a separate [ERP integration prototype](integrations/lotus_erpnext/README.md) contains gated hooks/fixture installation but explicitly lacks business/security acceptance. These source improvements do not approve N0 or migrate financial authority. Exact observation and drift limits are in the inventory's final verification section.

## Recommendation requiring human choice

Choose **B** if no existing owned source can be identified: a minimal, independently designed Lotus metadata authority on the permitted Frappe/MariaDB stack. Four domain records plus an explicit versioned grant policy suffice for the first read slice: Tenant, Company, Membership, Invoice Metadata. This is not a renamed Sales Invoice, an ERP Company clone, an accounting ledger, or an authoritative AR/AP balance source.

Choose **A** only if Product/Data identifies an actual existing Lotus-owned source, its operational write owner, schema/API version, tenant keys, grants, update/reconciliation process and deployment custody. No such source was found in this repository. An external service's existence remains UNKNOWN until supplied and verified. Synthetic ports, DTOs, report gateways, public datasets and ERP mirrors do not establish native authority.

| ID | Human decision to record | Concrete proposed answer / required detail | Approver | Status |
| --- | --- | --- | --- | --- |
| N0-01 | Release scope and source option | B for metadata first; retain a separate full-product completion obligation for all enabled finance/UI capabilities. A needs named operational evidence. | Product + Data | PENDING |
| N0-02 | Tenant/company topology and owner | Opaque immutable tenant/company keys; one company belongs to one tenant; Frappe site is deployment identity, not tenant authority. Choose single/multi-tenant site policy and named domain owner. | Product + Data + Security | PENDING |
| N0-03 | Native schema and update authority | Approve four independently authored records, constraints, schema version/hash and sanctioned operator/API/import process. Read capabilities never write. No initial data importer is implicitly approved. | Product + Data | PENDING |
| N0-04 | Invoice identity, dates and lifecycle | Immutable native record ID separate from display label; company-local posting date; DRAFT/POSTED/VOID proposed; no payment/overdue interpretation. Decide transitions, corrections, deletion and duplicate-label rules. | Product + Data | PENDING |
| N0-05 | Native authorization | Active Frappe user/session plus owned membership, capability, row/document rules and closed field/filter grants; deny by default; no Administrator/System Manager/ERP-role business bypass. Sign policy and adversarial oracle. | Security + Product | PENDING |
| N0-06 | Wire/source/reference succession | Proposed `p1.invoice.v2`, `invoice.min.v2`, `LOTUS_NATIVE_READ`, `ref.v3`, resource `lotus.invoice.metadata.v1`; native tenant/source bindings and strict old-token rejection. Exact labels and semantics require sign-off. | Security + Product + Data | PENDING |
| N0-07 | Timezone/currency/version/order | IANA company timezone, UTC observation, company base currency, opaque record version, binary stable ID order. Explicitly revise the old site-timezone/default-window and `name ASC` contracts. VND-only finance scope retained pending separate approval. | Data + Product + Security | PENDING |
| N0-08 | Freshness/completeness | Name source custodian; approve numeric maximum age/lag, health and reconciliation SLA, page coverage, outage/partial behavior and schema/source revision policy. No invented SLA is signed here. | Data + Product | PENDING |
| N0-09 | Audit, revocation and key custody | Approve membership/policy epochs, in-flight delivery fence, durable sink owner/ACL/retention, acknowledgement guarantees and rotation/revocation operations. Numeric retention/SLA must be filled in. | Security + Platform | PENDING |
| N0-10 | Storage and data migration | Frappe-owned DocTypes are recommended, independently defined; approve actual names/permissions/indexes/migration and backups in a subsequent task. Default new site has no ERP import. Existing sites need explicit mapping/reconciliation. | Data + Security + Platform | PENDING |
| N0-11 | Frappe-only artifact and isolated target | Review the new `docker/lotus-core` recipe; approve source/framework/dependency digests, dedicated site/project/volumes, synthetic ordinary users, two tenants, provisioning/cleanup and rollback. No shared runtime mutation. | Platform + Security | PENDING |
| N0-12 | Production route and capability catalog | `/copilot` through existing React composition proposed; native membership selector; only accepted capabilities exposed. Generic ERP routes and Desk links must leave the core catalog. A reduced pilot must be named as such. | Product + Security | PENDING |
| N0-13 | Native finance source authority | Separately approve normalized P&L/AR/AP/cash/obligation/schedule/credit/history inputs, account scope and update/reconciliation authority for AI001–006. Metadata approval does not cover these. | Product + Data + Security | PENDING |
| N0-14 | Optional ERP integration | Defer. If later requested, approve a separate connector profile, delegated identity, mappings, custody and revocation. It is never core bootstrap, fallback or a data-authority shortcut. | Product + Data + Security | PENDING |
| N0-15 | L3 / future capabilities | L3 fact-free local template/TTL/clipboard approval separate. V1 overdue, F101/F102 and L4/L5 writes remain outside this metadata decision. MVP bank R4/R5 remain denied. | Product + Security | PENDING |

## Signature and acceptance record

Each approver must supply: **human name and role; date/time; APPROVE / CHANGES_REQUESTED / REJECT; decision IDs; exact proposal/schema/policy/version hashes; filled SLA/retention/custody values; exclusions and unresolved conditions**. No signatures or approvals are inferred from test PASS, document titles, role names, or this recommendation.

Product reviewer: UNASSIGNED / PENDING. Data authority owner and reviewer: UNASSIGNED / PENDING. Security reviewer: UNASSIGNED / PENDING. Platform target/artifact reviewer: UNASSIGNED / PENDING. Independent QA/release reviewer: UNASSIGNED / PENDING.

N0 closes only when N0-01 through N0-13 have mutually consistent signed answers for the selected scope; N0-14 may be explicitly deferred and N0-15 explicitly excluded. This authorizes a later scoped implementation proposal, not automatic enablement. Full product acceptance also requires migrated finance and UI, ordinary-user ERP-free end-to-end evidence, independent security acceptance and separate G10 approval.

Open decisions are the PENDING rows. Detailed specification: [architecture proposal](LOTUS_NATIVE_ARCHITECTURE_FROZEN_PROPOSAL.md), [token/permission plan](LOTUS_TOKEN_PERMISSION_MIGRATION_PLAN.md), [execution plan](LOTUS_FULL_INDEPENDENCE_EXECUTION_PLAN.md), [agent handoff](LOTUS_ARCHITECTURE_WORK_TO_AGENTS.md). **STOP after this package.**
