# V1 PastFinalDue source contract — proposed v0.1

12 October 2026 · Lotus Fin · implementation **NOT_IMPLEMENTED**; contract **PROPOSED / NOT_FROZEN**; live capability **BLOCKED**. This packet defines decisions for approval; it grants none. The task authorizes design, not live reads, fixture creation, feature enablement or mutation. No domain implementation was made because V1-specific business semantics and safe fixture approval are absent.

## 1. Authority and boundary

Read together with the [authority register and next steps](CHATBOT_PROPOSAL_COMPLETION_PLAN_UPDATED.md), [independent gold](CHATBOT_V1_INDEPENDENT_GOLD_SPEC.md), [Round2 source closure](../phase0-chatbot-2026-10-10/V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md), [Round3 packet](../phase0-chatbot-2026-10-10/PHASE0_WORK_TO_CHAT_PACKET.md), and [P1 MASTER](../phase0-chatbot-2026-10-10/CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md). Accepted P1/P2 offline foundations remain intact. P1's current five-field reader and `AUTHORIZED_READ` provenance do not qualify financial facts.

Exact capability: `invoice.search_past_final_due`; proposed version `v1.past-final-due.v0.1`; projection `invoice.past-final-due.v0.1`. Label: **Hóa đơn đã qua hạn cuối còn dư nợ** / **Invoices past final due date with current residual**. Sales Invoice only. No customer lookup, Purchase Invoice, installment allocation, ranking, FX conversion, aggregated debt, historical balance or LLM explanation in this batch.

## 2. Predicate, precision and units

For an individually authorized parent observation `r`, at a frozen server instant `T`:

```text
D := calendar date of T in the qualified site's IANA timezone Z
eligible(r) := r.company = authorized_company
            AND r.docstatus = integer 1
            AND r.is_return = integer 0
            AND r.posting_date <= D
            AND r.final_due_date < D
            AND Decimal(r.current_outstanding_decimal) > Decimal("0")
            AND r.source_policy_qualified = true
            AND all required fields readable, unmasked, valid and current
```

All additional policies in this section are **proposals requiring G2 approval**. Do not evaluate an unqualified row as false and call coverage complete.

* `final_due_date` maps to authorized `Sales Invoice.due_date` only after installed field semantics and multi-term maximum-date behavior are independently qualified. No missing-date fallback to posting date. Dates must be canonical real `YYYY-MM-DD`; impossible dates and timestamps are invalid. Due today is excluded. A future posting date is explicitly excluded, even if due date is earlier; inconsistent chronology (`due_date < posting_date`) is unsupported data, not a positive match.
* Residual is the **current** parent `outstanding_amount`, after ERP's actual allocations and reconciliation at the read time. Unit is **`party_account_currency`**, never invoice `currency` or company default currency. Payment made after invoice creation changes the residual. A date filter does not reconstruct settlement at that past date.
* The proposed inclusion threshold is exact **strictly positive**, epsilon **0**, with no materiality/collection threshold. Parse a bounded finite Decimal from a lossless canonical decimal string, never a binary float, boolean, missing/null, NaN or Infinity. Source DB decimal extraction and every serialization hop must retain precision; converting an already rounded float to a string does not recover truth.
* Require source storage scale `s`, approved presentation scale `p`, rounding mode `ROUND_HALF_UP`, and precision-policy version from qualified field/currency metadata. Proposed supported `0 <= p <= s <= 9`, at most 30 integer digits; these bounds require metadata proof and G2 approval. Decimal operations use sufficient precision (at least 50 digits here) and fail on overflow; no default VND/2 decimals. Currency codes are an installed allowlist, not a guessed ISO rule.
* Predicate operates on the **exact stored residual** before display rounding. Emit `current_outstanding_decimal` in canonical fixed-point notation (no exponent, no unnecessary trailing zeros, normalize negative zero), plus `display_outstanding_decimal` with exactly `p` fractional digits. For a positive value displaying as zero, show **“positive residual below display precision”**, expose the exact permitted value, and never show “settled”. This avoids silently discarding tiny positives. If approved policy instead chooses quantized eligibility, it needs a new predicate version and changed gold; it is not this proposal.
* No totals across currencies. No frontend financial arithmetic. Formula version is `past-final-due.exact-positive.v0.1`; numeric `as_of` is the row read instant, not `D` at end of day. Qualification attestation and per-row observation are separate from financial-source approval.

## 3. Credit, settlement and exceptional data policy

|Case|Proposed policy|Required proof / outcome if unknown|
|---|---|---|
|Return / credit-note invoice (`is_return=1`)|Exclude as a candidate; never convert negative balance into collectible debt|Parent credit/return reconciliation still qualified; no company-level credit netting|
|Allocated credit / payment / advance|Use the resulting parent residual once; no local subtraction|Independent voucher/allocation oracle must match; unsupported reconciliation → PARTIAL|
|Unallocated credit, including `return_against` without allocation|No invented netting against another invoice|Disclose invoice-level scope, not net party indebtedness; G2 approval needed|
|Writeoff / reversed payment / cancelled credit / amendment|Use current reconciled eligible parent version; old cancelled parent excluded|Each lineage/settlement behavior requires oracle; no assumption based on status string|
|POS and cash-discount transactions|Support only after explicit G2 inclusion and G3 reconciliation qualification|Until qualified, detect as unsupported and return PARTIAL, including zero matches; do not silently omit|
|Missing, masked or malformed required data|No zero/date/currency substitution|Missing or unsupported source data → PARTIAL; missing global qualification → NOT_AVAILABLE; rights denial → FORBIDDEN|
|Duplicate same identity/version|Suppress the duplicate and mark integrity/coverage incomplete|No sum/count inflation; conflicting versions invalidate that identity; repeated source integrity failures → SOURCE_ERROR|

The adapter needs a trustworthy **policy coverage attestation** for settlement variants. `is_pos` is a mandatory internal permission-bound classification field; other writeoff/discount/credit flags must be frozen from actual installed metadata. If their safe detection or source-wide coverage cannot be established, V1 remains blocked; parent fields alone cannot prove those cases qualified. No hidden report/ledger reads may be added to “repair” an invoice.

## 4. Actual source map and permission contract

|Requirement|Observed source / evidence|Proposed V1 use and limitation|
|---|---|---|
|Parent invoice read|Round2 recorded installed ERPNext16.35/Frappe16.34; [source index](../evidence/phase0-round2-2026-10-10/INSTALLED_AR_AND_PERMISSIONS_INDEX.txt)|New narrow parent adapter; recorded source is historical disk evidence, not current target/source qualification|
|Permission-aware list|`frappe.client.get_list → frappe.get_list → model.qb_query → database.query.Engine`; [active permission source](../evidence/phase0-round2-2026-10-10/ACTIVE_QB_PERMISSION_EXACT.txt)|Explicit current user, `ignore_permissions=False`, `ignore_user_permissions=False`; no `get_all`, bare SQL or QB default permission bypass|
|Exact detail|`frappe.client.get`; [framework source](../evidence/phase0-round2-2026-10-10/FRAMEWORK_READ_AND_IMPORT_SOURCE.txt)|Check document read, company, field-level read stripping/masking; `get_doc` alone is insufficient. No full Form/onload/seen/view side effects|
|Current settlement and unit|Round2 invoice/source observations; AI002 MASTER §4 Amendment A1|Parent residual in party-account currency; independent fixture proof still required for this V1 target|
|Report accounting balance|[AR source](../evidence/phase0-round2-2026-10-10/AR_SEMANTICS_SOURCE.txt): PLE/credit/revaluation/term allocation|Not used for B at runtime. Raw AR execution is not permission-qualified delivery; historical/term modes are not substitutes|
|Clock|Qualified System Settings timezone + one server UTC instant|No host/browser date or AI002 shared-site timezone inheritance; reject missing/invalid target timezone|
|Existing ordinary frontend provider|`frontend/src/providers/dataProvider.ts`: `fields=*`, offsets, estimated totals, generic create/update/delete|Read for architecture facts only. Not reused as V1 adapter, completeness proof or mutation executor|
|Existing report gateway|`infrastructure/erpnext/erpnext_gateway.py`; core facade re-exports it|Company/report seam, not parent financial projection. Its company-currency/VND fallback cannot supply party currency|

**Required internal fields:** `name`, `company`, `docstatus`, `is_return`, `posting_date`, `due_date`, `outstanding_amount`, `party_account_currency`, `currency`, `modified`, `is_pos`, and qualified precision/policy classification metadata. `currency` is validation metadata only; do not expose it as the residual unit. Customer/party/name/address/email and Payment Schedule/PLE children are excluded from the runtime projection. Any future customer filter requires a separate field/linked-record contract.

Every field used in selection, filtering, ordering, classification or display must be readable **and unmasked** for the ordinary user; queryability/select-only authority is insufficient. Check Company and Sales Invoice read, user/owner/share/query constraints, field permlevels, filter/order rights and current document rights. Restricted finance fields must disable financial filtering; hiding the output while applying a secret predicate still leaks information. Never expose inaccessible-record counts or existence. Revoke before list → no protected response; revoke before open → generic FORBIDDEN with data/source/handles cleared. Fresh checks cannot guarantee instantaneous revocation after bytes have been delivered; declare that observation boundary.

## 5. Exact proposed delivery contract

Separate typed API; do not widen `p1.invoice.v1` enums/DTO in place. Its current context Literal supports only three generic read capabilities and `invoice.min.v1`. Reuse designs, not an unsupported cast.

```text
Request = {contract_version:"v1.past-final-due.v0.1",
 request_id:UUIDv4, context_ref:opaque, filters:{posting_from:date,posting_to:date,
 invoice_name_prefix?:NFC text<=128}, page_size?:integer[1,50], cursor?:opaque}
```

Explicit inclusive posting interval, at most 365 days; no omitted date default hiding older debt. Response visibly repeats the interval and says “within this posting interval”. No client actor/site/currency/date-of-evaluation/source policy/fields/order/DocType/SQL/URL arguments; reject extras and explicit nulls. Server resolves current principal/session/product/site/connection/company/policy. Prefix is literal prefix with database wildcard escaping, not SQL syntax. A future whole-history contract must revisit coverage and budget.

```text
Outcome = {contract_version, capability:"invoice.search_past_final_due",
 status:OK|PARTIAL|FORBIDDEN|SOURCE_ERROR|TIMEOUT|NOT_AVAILABLE,
 reason_code, request_id, correlation_id, context_version, source|null, data|null,
 user_message:fixed-safe-text}
source = {mode:ERP_READ|SYNTHETIC_TEST_ONLY, source_revision, projection_version,
 product_ref,site_ref,connection_ref,connection_version, observed_at_utc,
 evaluation_local_date,timezone,formula_version,precision_policy_version,
 qualification_ref, consistency:"LIVE_KEYSET", verification:"AUTHORIZED_READ"}
data = {filters,items:[{invoice_id,record_version,final_due_date,
 current_outstanding_decimal,display_outstanding_decimal,party_account_currency,
 storage_scale,presentation_scale,row_observed_at_utc,evidence_ref,selection_ref?}],
 coverage:{page_complete,scope_complete,reason_codes:[]},
 has_more:boolean|null,next_cursor:opaque|null,selection_required:boolean,
 total_count:null, limitations:[]}
```

No `ERP_VERIFIED` badge is authorized here. Future numeric qualification must bind reviewed source revision/policy/oracle, not just a successful response. Evidence refs are opaque metadata, not permission or immutable historical replay. Selection references bind record **and settlement** fingerprint: `modified` alone may not change when ledger settlement changes. If no qualified settlement revision exists, compare the exact due/residual/currency/precision/policy fingerprint on open. Do not put raw finance/actor/SID in decodable signed payloads; use a server-held opaque handle or authenticated encrypted token with independently reviewed lifecycle.

Proposed reason/status pairs: OK `MATCHES_FOUND`, `PAGE_READY`, `EMPTY_RESULT`; PARTIAL `COVERAGE_INCOMPLETE`, `UNSUPPORTED_POLICY`, `SOURCE_DATA_INVALID`, `SOURCE_INTEGRITY`; FORBIDDEN `AUTH_REQUIRED`, `ACCESS_DENIED`, `REFERENCE_DENIED`, `CSRF_OR_ORIGIN_DENIED`; SOURCE_ERROR `PROVIDER_ERROR`; TIMEOUT `DEADLINE_EXCEEDED`; NOT_AVAILABLE `TARGET_UNQUALIFIED`, `CAPABILITY_DISABLED`, `STALE_REFERENCE`. Denial/source error/timeouts/unavailability have null data/source. PARTIAL may show individually valid observed rows but **no selection handles/cursor/action**, `has_more=null`; zero-row PARTIAL is valid. Explicit selection required iff items are nonempty; one row never auto-opens. EMPTY_RESULT only when qualified authorized scope was exhausted under declared consistency with no data gaps. HTTP proposed 200/200/403 (401 auth)/502/504/503 (409 stale); invalid request → safe 422 NOT_AVAILABLE/INVALID_REQUEST, method →405. Freeze full reason matrix before delivery implementation. Server CID equals response header; one Frappe envelope, no-store, fixed safe messages; terminal audit required for every outcome.

## 6. Pagination, source coverage and physical limits

Freeze `D`, timezone, normalized query, scope, policy and precision version across the signed bounded search window; re-resolve authority every page. Expiry or local-date rollover forces fresh search. Proposed handle TTL 300s, maximum five pages/window. `name ASC` keyset using qualified database collation; row-order and duplicate checks are mandatory. No offset totals. A cursor is not a snapshot: mutable rows/inserts can alter membership. Label rows “observed during this search”; never promise an as-known-at company snapshot. Whole-scope completeness means only the declared live traversal interval/query, not a historical guarantee. Revalidation/instability or unexplained gaps → PARTIAL.

Page complete differs from scope complete: a correctly filled page with more candidates is OK/PAGE_READY and `scope_complete=false`, visibly bounded. A physical scan/data failure is PARTIAL with no continuation authority. Do not filter missing due/balance data away before classifying it; otherwise false EMPTY_RESULT is possible. Qualify authorized broad parent scanning or an equivalent invalid-data detection query; count every query. Signed continuation includes lookahead/resume state so no row is dropped. Count repeated fetched lookahead too.

|Proposed V1 bound|Enforcement and proof|
|---|---|
|Internal fetch page <=50; scanned/fetched parent rows <=250 per invocation; returned <= requested<=50|Include duplicates, nonmatches and lookahead; fifth full page cannot issue an uncounted sixth probe. At250 without proven exhaustion → PARTIAL|
|Search source page calls <=5; open parent read <=1; auth/metadata calls <=10 separately|Permission checks <=250 search /1 open, separately instrumented. Calls are not SQL statements; no uncapped per-row hydration|
|Source fetched bytes <=1MiB; response UTF-8 bytes <=256KiB|Account lower-layer materialization before allocation when possible; capped bounded projection, never corrupt JSON truncation|
|End-to-end deadline 5000ms; auto retries0; LLM/report/child-term/provider calls0|Remaining deadline reaches every source/auth/audit stage; actual DB timeout/cancel plus physical query/rows/RSS qualification required|
|Window <=5 pages; UI current generation1; actor/site admission proposal2|Distributed server admission, not browser abort or in-memory limiter proof|

These are proposed V1 values from source closure, **not** generic P1's100scan/64KiB. No benchmark/SLO PASS claimed. If actual permission checks/full-parent hydration cannot meet physical bounds, block adapter; do not skip authorization. Audit records redacted CID/status/version/counters and opaque scoped bindings; no tokens, query text, row values, personal financial data or exception dumps.

## 7. Open, settlement races and smallest implementation batches

Proposed V1 companion `invoice.open_past_final_due` uses the selected reference under this same new financial contract; it is not an enabled generic `invoice.open`. Reauthorize all source/field/document rights, reread current parent, recompute eligibility and compare settlement fingerprint. Settlement or version changed → STALE_REFERENCE, no old amount/handle, explicit new search. Forbidden wins over stale; no hidden existence. Approved minimum financial reader only, no native Form navigation.

All paths below are **NEW proposals** under `lotus_fin/lotus_fin/`, except existing source listed as read-only. No implementation permission implied:

1. **V1-D1, after G2 approval:** `domain/schema/past_final_due.py`, `domain/policy/past_final_due_policy.py`, `tests/test_past_final_due_policy.py`. Exact Decimal/date/policy evaluator with synthetic gold only; no Frappe/import/provider/context/API. Each cohesive source <200 lines. First executable batch remains blocked until the decision sheet below is approved.
2. **V1-S1, after G3 target/fixture approval:** `application/port/i_past_final_due_read.py`, `infrastructure/erpnext/past_final_due_read_adapter.py`, `infrastructure/erpnext/past_final_due_query.py`, `tests/test_past_final_due_source.py`. Real permission, metadata, settlement, lossless numeric and physical budget qualification; no financial-engine/report reuse.
3. **V1-A1, separate approved delivery batch:** `application/service/search_past_final_due.py`, `application/service/open_past_final_due.py`, `domain/model/past_final_due_context.py`, `infrastructure/security/past_final_due_handles.py`, `presentation/dto/past_final_due.py`, `presentation/controller/past_final_due_controller.py`, `api/past_final_due_api.py`, focused integration/authorization tests. Own typed contract/configuration; no widening P1 or enabling flags here.
4. UI financial projection/mount is a later allowlist after Antigravity's P2-B ownership clears and scope pinning is accepted. Keep current action/UI files untouched. Generic backend offline PASS remains distinct from V1 source qualification.

Demo now: document/gold examples labelled synthetic only. Release blockers: G2 decisions, G3 real oracle/permissions, qualified artifact/site/sink/handles/physical costs, V1 delivery/UI acceptance and separate release authorization. Rollback future V1 entrypoint/handles only; no ERP data changed by this read capability.

## 8. Concrete approvals still required

|ID / owner|Decision to record|Current state|
|---|---|---|
|G2-V1-01 Product + Finance|Option B label, Sales/submitted/nonreturn, future posting/invalid chronology, exact-zero threshold|PROPOSED / NOT_FROZEN|
|G2-V1-02 Finance|Parent residual unit, precision metadata/scales/rounding, tiny-positive presentation|PROPOSED / NOT_FROZEN|
|G2-V1-03 Finance|Allocated/unallocated credits, returns/writeoffs/reversals/POS/discount eligibility and unsupported coverage|PROPOSED / NOT_FROZEN|
|G2-V1-04 Product + Security|Posting interval limits, live consistency/page completeness, stale open, field denial, reason matrix, TTL/budgets/UI|PROPOSED / NOT_FROZEN|
|G3-V1-01 Work/platform owner|Named isolated target, canonical source/image/worker/site/schema/timezone and approved fixture baseline/cleanup|BLOCKED|
|G3-V1-02 Financial verifier|Independent parent/voucher/allocations reconciliation including multcurrency/terms/settlement fingerprint|BLOCKED; historic AI001/AI002/AI003 gold is not a V1 approval|
|G3-V1-03 Security verifier|Non-Administrator document + every predicate/financial field permission, masked/filter inference/revoke and no-write|BLOCKED|
|G3-V1-04 Engineering verifier|Lossless decimal transport, metadata policy classification, ordering/consistency/SQL/calls/bytes/deadline|BLOCKED|

Each decision needs approver, timestamp, exact document digest/revision, allowed scope and explicit conditions. Blank fields and agent recommendations are not approvals.
