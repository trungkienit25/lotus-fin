# Lotus Fin — token and permission migration plan

13 October 2026 · Asia/Saigon · `E:/lotus-fin` · **PROPOSED / NOT APPROVED**.

The [N0 approval sheet](LOTUS_FINAL_N0_APPROVAL_SHEET.md), [architecture proposal](LOTUS_NATIVE_ARCHITECTURE_FROZEN_PROPOSAL.md) and [current-source inventory](LOTUS_FULL_ERP_DEPENDENCY_INVENTORY.md) govern this plan. No token, permission, key, schema or source change is made here. Native source identity and grants require human Product/Data/Security approval.

## Actual contract and source evidence

| Current source location | Current behavior to preserve or migrate |
| --- | --- |
| [AuthorizedReadContext](lotus_fin/lotus_fin/domain/model/authorized_read_context.py), [SourceEvidence](lotus_fin/lotus_fin/domain/schema/action_outcome.py) | Only ERP_READ/DEMO_ISOLATED; company/product/site/connection/context/projection scope. No native tenant/source authority namespace. |
| [ActionReferenceCodec](lotus_fin/lotus_fin/infrastructure/security/action_reference_codec.py) | Context `ref.v1`, binding `opaque-actor.v1`; HMAC-SHA256, actor/session derivations, scope and purpose; historical expiry rejects `now > expires_at`. |
| [InvoiceReferenceV2Codec](lotus_fin/lotus_fin/infrastructure/security/invoice_reference_codec.py) | `ref.v2` selection/cursor; canonical strict claims and HMAC comparison; `now >= expires_at` rejection; no token becomes authorization. |
| [SelectionClaimsV2 / CursorClaimsV2](lotus_fin/lotus_fin/infrastructure/security/invoice_reference_claims.py) | `p1.invoice.v1`, `invoice.min.v1`, Sales Invoice/doc_id, name ASC, query/page/record-version/expiry bindings. |
| [FrappeInvoiceAuthorizer](lotus_fin/lotus_fin/infrastructure/security/frappe_invoice_authorizer.py) | Company permission and site timezone; config/key-material digest in stable scope fingerprint; ERP_READ emitted. Missing live permission interface denies. |
| [Configuration loader](lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config_loader.py), [config](lotus_fin/lotus_fin/infrastructure/config/invoice_actions_config.py) | Newest cache/site/key rotation/privacy behavior is part of the current candidate; preserve it, including same-key-ID secret-change invalidation. Default capability disabled. |
| [Search](lotus_fin/lotus_fin/application/service/search_invoices.py), [Open](lotus_fin/lotus_fin/application/service/open_authorized_invoice.py), [validation](lotus_fin/lotus_fin/application/service/invoice_read_validation.py), [read schemas](lotus_fin/lotus_fin/domain/schema/invoice_read.py) | Bounded typed orchestration, exact selected identity/version, fresh port authorization, denial precedence, no partial actions. Open currently equates projected invoice_id with claims.doc_id; native display label vs record key must be explicitly separated. |
| [Controller](lotus_fin/lotus_fin/presentation/controller/invoice_actions_controller.py), [HTTP API](lotus_fin/lotus_fin/api/invoice_actions_api.py), [response](lotus_fin/lotus_fin/presentation/response/action_response.py) | Injected controller services function; public route disabled. Preserve strict Request/Response admission, CID/no-store/nosniff, safe failure messages and existing reasons such as CONTEXT_CHANGED. |
| [P2-B wire](docs/reviews/phase0-chatbot-2026-10-10/CHATBOT_P2B_WIRE_CONTRACT.md), [frontend types/decoders](frontend/src/pages/copilot/actions/invoiceActionTypes.ts) | Current version and source whitelist are intentionally closed. They must reject unapproved native versions instead of accepting a widened union. UI expiry already rejects equality. |

The latest [source reconciliation](docs/reviews/evidence/chatbot-release-candidate-2026-10-13-01a132c2/SOURCE_VERSION_RECONCILIATION.json) names the historical versions above and explicitly marks native successor pending N0. Security Code V3 prohibits client/LLM-selected authority, raw chain-of-thought, invented numbers and MVP bank writes. Historical ERP choices are replaced through a reviewed successor, not silent reinterpretation.

## Smallest successor family proposed for approval

Use **one native family**, not parallel permissive ERP/native verifiers on the core routes. Proposed labels below are concrete review choices, **not approved literals**:

| Axis | Existing | Proposed successor |
| --- | --- | --- |
| Action wire | `p1.invoice.v1` | `p1.invoice.v2` |
| Projection | `invoice.min.v1`, docstatus0/1 | `invoice.min.v2`, closed DRAFT/POSTED lifecycle |
| Context/selection/cursor binding | context ref.v1, selection/cursor ref.v2 | `ref.v3` for all three purposes, version-specific closed claims |
| Source mode | ERP_READ / DEMO_ISOLATED | `LOTUS_NATIVE_READ` operational; DEMO_ISOLATED remains explicitly synthetic and never production fallback |
| Resource | `doc_type="Sales Invoice"` | `resource_type="lotus.invoice.metadata.v1"` |
| Record identity | ERP doc_id / displayed invoice_id | owned `native_record_id` + tenant/company/source tuple; display invoice label is separately projected |
| Cursor order | `name ASC` | binary native_record_id ASC inside one authorized tenant/company/source window |
| Policy authority | Company/DocType/Frappe role semantics | owned membership/capability/row/document/field policy with effective revision/epoch |
| Date authority | site timezone | approved company accounting timezone, explicitly bound to source/context |

Native claims must bind purpose; key ID; opaque actor and current session; product/site; source ID, source mode, schema/authority revision; connection ID/version; tenant ID/company ID; context fingerprint; policy/membership epoch; wire/projection/resource versions; issue/expiry. Selection additionally binds native record ID, observed record version and originating query fingerprint. Cursor additionally binds normalized predicate digest, page size/index, binary order, authorized last/upper keys and fixed window. Context includes only bindings needed to reconstruct trusted scope; no raw email, sid or secret. Site identity is not a tenant surrogate.

Source revision used for security identity means authority/schema/config revision, not every insert into a LIVE_KEYSET collection. Individual writes bump record version; policy/source rebinding invalidates context. If Data chooses to invalidate a cursor on every collection update, approve snapshot/revision semantics explicitly; do not claim LIVE_KEYSET and stable snapshot simultaneously.

Retain HMAC-SHA256, canonical serialization, constant-time MAC verification and opaque actor/session pattern. Native version/purpose/domain must be part of authenticated content and a distinct key namespace or derivation; native and optional ERP cannot share an ambiguous trust domain. Security approves actual key custody, native key ID/rotation and any retained legacy keys. HMAC gives integrity, **not encryption**: public-safe claims only, no financial/customer payload. Re-run actual maximum-length feasibility against the existing token/body/response budgets; added bindings must fit or receive an explicit versioned cap amendment. Do not remove tenant/source security fields to fit 2048 characters.

Strict decoder admission requires exact version prefix, bounded canonical base64/JSON, no duplicate/extra/missing keys, correct type/purpose/scope, nonfuture issue time and `now >= expires_at` rejection. The stronger equality rule is proposed for the new family. Historical v1 equality semantics and tests remain in their historical contract scope; do not edit them into apparent native acceptance.

## Permission migration, ordered by authority

1. Frappe supplies authenticated current enabled user, live sid and trusted site. No request-supplied user/role/source/SQL/URL and no admin fallback. Privileged maintenance does not imply operational domain access.
2. Lotus membership authoritatively resolves tenant/company. Company candidate is untrusted; a same-named ERP Company does not map automatically. `System Manager`, `Accounts User`, `Accounts Manager` and report permissions are not native grants.
3. Closed capabilities `invoice.context/search/open` have independent row/document and field/filter grants. Authorization precedes predicates and protected exposure. Hidden/denied fields cannot participate in filters/order/counts that infer data. Required projection fields denied → safe unavailable/denial, never partially repaired record.
4. Check fresh policy at each read and immediately before protected terminal delivery; revocation takes precedence over stale/version/existence information. Session/logout/disabled user, company/source changes, document grant loss and key retirement invalidate old state. Regrant creates a new effective epoch; old selections/cursors remain invalid.
5. Cache keys bind current actor/session, tenant/company/source/mode, policy/membership/source revisions, contract/projection and relevant cutoff. Reauthorization is required on hits. Never reuse Frappe Company/Report cached allow decisions as native authority.
6. Separate operator/import grants from read grants. Generic Frappe CRUD/DocType/report endpoints must enforce the signed domain policy or deny access to these records; removing links from React is insufficient. No ignore_permissions, user switching or framework-missing allow path in native production composition.

The exact row-rule representation, ownership, revocation lag, audit retention and physical request-cancellation guarantees remain N0-05/N0-08/N0-09 decisions. A signed reference is a candidate handle; authorization always comes from current authority.

## Old token rejection and client cutover

| Incoming object / request | Native core outcome | Migration allowed |
| --- | --- | --- |
| ref.v1 or ref.v2, even valid MAC and same invoice/company label | Reject before document source I/O; safe old-version/context-invalid outcome under approved reason matrix | User obtains new authenticated native context, searches again and explicitly selects. No token transcoding. |
| ERP_READ source/evidence or Sales Invoice selected resource | Reject wrong authority/resource/mode | Only an separately approved external adapter may process it in its own profile; no native rebranding. |
| Native handle from other tenant/company/site/source/actor/session/purpose | Generic denial, no protected data/source or existence detail | None. |
| Correct native identity but expired/old schema/policy/key epoch | Reject and clear protected UI state | New context and fresh query/selection, never automatic replay. |
| Still-authorized native record whose version changed | STALE_SELECTION or approved successor equivalent, null protected payload | Explicit fresh search/selection. No silent open-latest. |
| Revoked user/grant plus changed record | Generic authorization denial wins | Regrant still requires new context/selection. |

Proposed deployment cutover: keep capability disabled; install approved native schemas/data/policy; deploy backend supporting only the selected native family on existing three action routes; deploy matching React decoders/config; retire old context key namespace/config epoch; clear protected state/caches; qualify ordinary users; enable only after independent P5/G10 gates. Server selects the profile/version; body cannot request arbitrary source mode. Old clients receive a safe unsupported-version failure, never success with changed meanings. Roll back to a known disabled immutable native artifact, not an old permissive ERP fallback.

Use existing typed orchestrators and ports; make only identity/status/source/version deltas needed for the successor. `IInvoiceReferences` currently names v2 selection/cursor methods: add explicit successor methods or a reviewed version-specific implementation interface, keeping historical test composition separate. Do not alias old claim decoders into native verification. Open's typed port must receive/validate native key distinct from display label, and exact read results must expose that key internally for verification while projecting only allowed fields. No second generic executor or duplicate agent stack.

## Financial-provider and evidence migration

| Provider / source locations | Required successor change | Financial invariant |
| --- | --- | --- |
| AI001 API fetcher, SourceGatherer/SourceValidation/MetricAssembler, EvidenceRef | Owned source schema/provenance registry and native resource grants; normalize approved observations without claiming ERP reports generated them. Source contract version changes, formula version retained unless arithmetic changes. | 1.0.0/formula2026.1 calculation, period/effective cutoff, unavailable≠zero, credits/dedupe/reconciliation. |
| AI002 adapters/service/cache/evidence | Owned cash/obligation/allocation/scope providers; native reconciliation provenance replacing ERP_GL labels under approved version; source schema+policy+account/cutoff bound caches and evidence | 1.2.1/STRICT_BASELINE_V1 math, negative cash, explicit TRADE_ONLY coverage, no inferred installment settlement/FIFO; confirmed commitments need separate approval. |
| AI003 ServiceDeps/sources/contracts/evidence | Native ARProvider/APProvider/ScheduleProvider; new source-kind/identity/schema assertions and native evidence IDs; preserve old ERP evidence for legacy audit | V2.2 method, valid baseline/history, AP exact concentration, current/baseline cutoff; DEMO_ONLY policy is not production-calibrated. |
| AI004–006 and agent/plugin registries | Approved native/user scenario source binding, owned entitlement gates and truthful evidence; remove hardcoded defaults claiming operational truth | Preserve deterministic engine gold; no accidental financial-source scope inherited from invoice metadata approval. |

Do not rewrite saved ERP report hashes into native attestations. If historical data is explicitly migrated, create a signed mapping manifest from external source ID/version to native ID/version and verify reconciliation at approved cutoffs; this is data provenance, never a permission/token grant. Native and old evidence replay each requires fresh corresponding authorization. No importer, key rotation, evidence deletion or database migration is performed in this task.

## Required qualification and open decisions

Retain current HMAC/privacy/config/delivery regression assertions and add genuinely different native cases: two tenants with same display invoice ID; shared company label; wrong source/mode/resource/version; old valid v1/v2 tokens rejected with zero protected I/O; native boundary purpose replay; same key ID secret replacement; source/schema/policy/timezone changes; logout/revoke/regrant/disabled-user; query vs open grant differences; required field/filter denial; canonical parsing/tamper/expiry equality; record update; partial non-actionability; audit outage and late response fencing. Physical DB and audit cancellation, ordinary-user HTTP/middleware and browser delivery must run on the approved ERP-free target, not mocks.

Open decisions: N0-02…N0-13; exact new labels/claims/caps, status reason matrix, native schema and row rules, revocation fence/SLA, source revision semantics, finance source equivalence and staged rollout owners. **NATIVE_SECURITY_CONTRACT = PROPOSED / NOT_APPROVED; IMPLEMENTATION_READY = NO pending N0.**
