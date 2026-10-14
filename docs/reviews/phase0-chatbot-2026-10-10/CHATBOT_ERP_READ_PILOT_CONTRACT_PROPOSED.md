# Chatbot ERP read pilot — candidate contract

10/10/2026 · **PROPOSED / NOT_FROZEN / NO_IMPLEMENTATION_BATCH_READY**. Product: Lotus Fin, for FinTechathon Shenzhen. Selected slice **V1: find and open overdue Sales Invoices**. This document proposes an application boundary; it does not add a feature ID, replace a frozen contract, implement a route or authorize ERP writes.

The owner asks for the most reasonable deployment and reaffirms separate Lotus Fin/ERPNext identity. [Architecture evidence/decision](PHASE0_ARCHITECTURE_DECISION_RECORD.md) supports the existing Lotus backend with an in-process ERP adapter as initial candidate. ERP target/site/principal configuration still needs verification; product identity and co-deployment are separate facts.

## Scope and user flow

1. User selects an authorized company/connection in Lotus Fin and asks to find overdue invoices, optionally naming a customer or invoice.
2. Server authenticates, resolves authorized product/site/company/connection and current ERP observation time. LLM supplies candidate intent/filters only.
3. Application searches permission-filtered candidates under the approved overdue definition and explicit budgets. Return a bounded list with source status, currency, cutoff/observation time and coverage.
4. Multiple matches require user selection from authorized results; never guess an entity from an ambiguous name or disclose forbidden matches.
5. Detail/open request rechecks current permission, scope and target version. Application returns a validated navigation descriptor; UI builds its encoded route to the verified product/site.
6. Changing company/connection clears prior candidates/references and fences late responses. No financial defaults on failure.

No create/update/submit/cancel/delete/send, ERP draft/comment/task save, payment, scheduler action, report refresh/updater execution or frontend DB queries. V2 what-if and V3 follow-up are later capabilities. Invoice/customer text is untrusted data; it cannot select another tool, endpoint, company or recipient.

## Server context and typed interfaces

The following are **new proposed application types**, not claims of existing SDK/ERP fields or implemented endpoints.

| Type | Fields and rules |
|---|---|
| RequestContext | authenticated `actor_id`; server-resolved `product_id`, `erp_connection_id`, `site_id`, `company_id`, effective ERP principal; correlation_id; request_id; approved capability/contract version; server deadline; scope binding. No credentials in DTO/log/model. |
| SearchOverdueRequest | bounded optional exact invoice/customer selection or search text; opaque cursor; requested page size capped by server. No arbitrary doctype/URL/report/SQL/filter expression, principal or client-declared verified data. Historical as_of is unsupported for this candidate. |
| InvoiceCandidate | server-issued opaque reference; permitted invoice identifier/display label; permitted customer label if needed; ERP current status; due information under approved semantics; outstanding Decimal string and **outstanding currency**; invoice currency separately if authorized/useful; source version; observed_at; availability/reasons. Fields omitted when field permission denies; if financial semantics cannot be supported, fail closed for that capability. |
| SearchOverdueResult | typed status; candidates; source/provenance; approved definition_version; coverage; scanned/returned bounds; has_more/next_cursor; safe error+CID; echoed request/scope binding for race rejection. Never invented total. |
| OpenInvoiceRequest/Result | opaque reference; application validates binding/expiry and re-reads authorized target; result is allowlisted doctype + authorized name + approved navigation scope/version, not arbitrary model URL. Permission revoked/stale target clears old candidate data. |

Public application interfaces, names still PROPOSED:

```text
SearchOverdueInvoices.execute(context, request) -> SearchOverdueResult
ResolveInvoiceNavigation.execute(context, reference) -> NavigationResult

AuthorizedInvoiceReadPort.search(context, approved_query, page_budget) -> AuthorizedPage
AuthorizedInvoiceReadPort.read(context, invoice_identity) -> AuthorizedInvoiceFacts
OverduePolicy.evaluate(authorized_current_facts, observation_date, definition_version)
```

Normal UI and chatbot call these same use cases. Adapters only implement the port; domain policy never imports API/controller/client modules. Infrastructure can use permission-aware Frappe list/doc APIs locally, or reviewed target resource/allowlisted business API remotely. Child payment-term facts require parent document/field authorization, never an unguarded child-table query. Public ERP methods must be validated for side effects before use, even if labelled read.

Existing source routes remain compatibility inputs: React dynamic invoice list/detail; `frappe.client.get_list`; encoded GET resource; React Copilot `copilot_api.chat_copilot`; Desk ai_insights alias. New public route naming is not frozen. Existing CRUD provider is not a reusable agent tool, and no generic `execute_method`/SDK-object tool is exposed. Existing stateful chat cannot be assumed safe because this invoice use case is stateless.

## Financial/source contract that blocks G2/G3

Installed ERPNext16.35 source verifies `Sales Invoice.outstanding_amount` currency options=`party_account_currency`, distinct from invoice `currency`; `set_due_date` uses the maximum term due date. Daily `update_invoice_status` compares due-term payable amounts against paid amount and writes statuses. See [installed schema](../evidence/phase0-chatbot-2026-10-10/INSTALLED_INVOICE_SCHEMA.txt) and [semantics](../evidence/phase0-chatbot-2026-10-10/INSTALLED_OVERDUE_SEMANTICS.txt). This updater was never run.

**PROPOSED default:** term-aware, current-observation overdue, with a permission-aware qualified source. Exact ERP report/business read method is **NOT_VERIFIED** for the selected site. ERP stored `status=Overdue` alone is not proven fresh; strict invoice `due_date < today` alone misses some installment overdue. Chat must choose one policy before freeze:

- Term-aware overdue with verified source/allocation/current freshness and independent oracle; or
- Explicit limited “invoices past final due date with positive current outstanding”, labelled as that narrower scope. This must not be presented as a complete installment-overdue answer.

No client-side workaround or unguarded SQL if the approved API cannot supply required facts: return NOT_AVAILABLE/SOURCE_CONTRACT_UNVERIFIED. Parent document facts may be read under permissions, but amounts/term allocation need target qualification before a local policy implementation.

Proposed eligibility starts with submitted documents and positive current outstanding; treatment of returns/credits/write-offs/POS/discounted invoices and missing due dates must match selected source policy. These are pending decisions, not silently excluded rows. Payment dates/history cannot be reconstructed from current outstanding. `as_of_date` supplied by the LLM cannot backdate this source. Site timezone/current observation date, precision and cutoff definition require verification.

Monetary fields are finite Decimal strings; preserve authoritative amount/unit and target scale, no arbitrary two-decimal rounding or FX conversion. Round only under approved target monetary convention; no aggregate across currencies. Label total current outstanding separately from overdue installment amount. Verified zero differs from absent field, incomplete scope or source failure. No ledger/Income/growth formula is required for V1; F102 obligations stay at its [SSOT](../../features/F102/F102_MASTER_SSOT.md).

## Status, provenance, evidence and errors

Proposed application statuses: `OK`, `NO_MATCH`, `PARTIAL`, `AMBIGUOUS`, `VALIDATION_ERROR`, `FORBIDDEN`, `SOURCE_ERROR`, `TIMEOUT`, `NOT_AVAILABLE`, `STALE_REFERENCE`. Availability: `AVAILABLE`, `PARTIAL`, `NOT_AVAILABLE`, `NOT_VERIFIED`. Values and status survive adapter→use case→tool→API→UI; HTTP200 is not business success. Empty provider output is a provider error, not “analysis completed”.

`NO_MATCH` means a complete authorized search scope returned no eligible match; it says nothing about forbidden invoices. Page/scan/deadline truncation yields explicit PARTIAL/INCOMPLETE, not zero total. A source error never becomes NO_MATCH. Authentication/authorization errors expose no old financial payload or existence of hidden targets.

Source provenance: `ERP_VERIFIED` only after a reviewed adapter and target source contract qualify facts, with target/contract/source identity, scope, observation time and coverage. `USER_ENTERED` remains manual; `DEMO_ONLY` only under explicit isolated server policy. Neither is a verified invoice balance. Do not mark current production path ERP_VERIFIED from this proposal.

Reference/evidence is server-issued and bound to actor/product/site/company/connection/contract/target version/expiry. Client text/checksum/data_mode is not authority. Reference lookup must read and reauthorize the actual ERP target; embedded client amounts are never reused. Proposed implementation may use protected opaque identity references and authoritative re-read, avoiding a shared chat-session store. If a manifest/cache store is introduced, its expiry, isolation, corruption/outage and concurrency behavior require their own qualification. Cursor similarly binds scope/query/contract and cannot turn into arbitrary filters or reveal unauthorized totals. Offset pagination lacks snapshot consistency; coverage must disclose observation drift or detect/restart it.

Safe failures carry allowlisted code/message and one server correlation_id, without raw ERP/provider exceptions in reply/widget/LLM context/nested payload/log. Structured minimal audit: actor, product, site, company, target/action/version/status/duration/correlation_id. Do not log tokens, sensitive invoice text or full financial payload. Log user work outcome, not chain-of-thought.

## Bounds and observation

Unqualified candidates: pageSize≤50, maxPages≤5, tools≤3 per request, total deadline≤5s, output≤256KiB. These are proposed limits **without latency/performance PASS**. Chat freeze depends on measurement.

Enforce separate fetched/returned rows, child rows, scan pages, fetched bytes, output bytes, tool calls, requests/retries and deadline. Parent+term reads must fit the declared budget; do not silently fetch N child documents per result without accounting. At any cap return explicit incomplete coverage. Never send the complete invoice set to LLM. Cancellation/deadline propagates to adapter; completion after deadline or scope switch cannot render as current result. Bounded safe read retry only within remaining deadline, no permission/validation retries.

Count UI→Lotus API calls, ERP HTTP calls (zero HTTP for an in-process adapter), in-process methods, report callbacks, permission/metadata calls, SQL statements/rows and payload separately. V1 does not require four AI001 reports per search. Proposed bounded workload:100/10k/100k invoices,1/5 authorized companies, concurrency1/5/20, cold/warm, revoked/switch/timeout and installment/currency cases; declared hardware/artifact/workers, at least100samples/cell after warmup plus failure tests. Measure p95/throughput/peakRSS/error/timeout/SQL/calls. Current qualification NOT_RUN.

## Future mutation boundary — disabled design

Saving an ERP draft is mutation. Future enabled writes require immutable server proposal binding exact operation/args/targets/recipient/version, actor/product/site/company/connection, evidence and expiry; authenticated UI one-use approval; immediate reauthorization/version check; allowlisted ERP business method and lifecycle/hooks; durable operation ledger/idempotency/audit. Chat “yes”, LLM “confirmed”, history or ERP text is not approval.

Same operation key with different args denies. Timeout after remote commit yields UNKNOWN_OUTCOME and reconciliation before retry; never promise exactly-once without atomic target deduplication evidence. Rollback after ERP submit/send may be impossible and compensation is a distinct reviewed action. Company switch/revocation/stale version expires/re-previews proposal. None of these writes or tests was executed.

## Minimum acceptance and ownership

Designed tests, all current live **NOT_RUN**: allowed/denied/field-restricted principals; crossuser/company/site/product/connection; revoked list→detail/reference; forged/replayed cursor/evidence; ambiguity; missing/zero/error; schedule due before final due, partial allocations/returns/credits/write-offs; correct party-account currency/noFX; independent source oracle; source timeout/cancellation/partial paging; late company-switch result; invoice-text injection; no raw nested errors; same status through UI; no mutation calls; fresh immutable worker and browser proof. Session race/outage acceptance additionally required if selected AI007 retains shared sessions.

Chat owns business/G2 and scope decisions. Work supplies target/source/isolation/evaluation evidence. Antigravity implements only a later approved packet with exact source/allowed edits/impact/rollback; Work verifies G4B, Chat closes. No current eligible implementation batch.
