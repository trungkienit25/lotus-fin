# Round 2 — V1 overdue source and contract closure

10/10/2026 · FinTechathon Shenzhen · T3 · **V1_SOURCE_BLOCKED**. Recommend **Option B: PAST_FINAL_DUE_INVOICES** as the smallest candidate, labelled “Hóa đơn đã qua hạn cuối còn dư nợ”. It is not a complete installment-overdue search and is not yet source-qualified/frozen. Standalone V1 needs neither F101 nor F102. No invoice/term report executed, source records read, fixture created, updater called or implementation dispatched.

## Current installed source, separated from site qualification

Observed local installed Frappe16.34.0 / ERPNext16.35.0 / Lotus0.0.1, existing backend image ID `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`. This proves installed **disk source**, not site customizations, effective-user permissions, resident worker identity or a remote product's compatibility. [Source index/hashes](../evidence/phase0-round2-2026-10-10/INSTALLED_AR_AND_PERMISSIONS_INDEX.txt), [AR source](../evidence/phase0-round2-2026-10-10/AR_SEMANTICS_SOURCE.txt).

| Installed path below `/home/frappe/frappe-bench/apps/` | Exact fingerprint / evidence |
|---|---|
| erpnext/erpnext/accounts/report/accounts_receivable/accounts_receivable.py | SHA256 `2ee6a9bbdb58852f0fe61f30fa5f1f7c2fbf3f7272820ddc1eda21b61a6621eb` |
| erpnext/erpnext/accounts/report/accounts_receivable/accounts_receivable.json | SHA256 `aae418f91979b3faa8d98c813252d3d45cddcbe2bfe4a11f8a3c81aa0a325a0c` |
| frappe/frappe/model/qb_query.py | SHA256 `e42f930ceb1f6277a5435c9ef8123715f9499221fe8be75d8de264ba080cdf0f` |
| frappe/frappe/database/query.py | SHA256 `ea7f6e9815d5b91e3e93a48cecf5c65f472a0fe1a29a6e0387b3ae9afb3a320c` |
| frappe/frappe/model/document.py | SHA256 `902e8330128a8d541069355e9c66689c548fca749a9d05ccc69cdd952ac44937` |
| frappe/frappe/desk/query_report.py | SHA256 `79df274daceef5c4eb0721497f9efb6ae5b57c4d819a57fdd5924ecf76fb3bff` |
| frappe/frappe/utils/data.py | SHA256 `432faeec793c21a62085e311979ac6201b31b1cc0cee9e7310b6d75053063d24` |

Report `Accounts Receivable` exists; shipped JSON is enabled Script Report, ref_doctype Sales Invoice, roles Accounts Manager/User, prepared_report=0. Those are shipped metadata, not current site Report settings. `execute → ReceivablePayableReport.run` reads Payment Ledger Entries, invoice details, returns and exchange revaluations. `report_date` defaults to `nowdate`; age_as_on may separately choose Today or report date. Company default fallback exists, so V1 must supply authorized company explicitly.

**Semantics observed now:**

- Invoice-level report balance aggregates invoiced minus paid minus credit_note at configured precision, with company-currency or party-account-currency modes. This is a report balance at its filter context, not interchangeable with every invoice field or historical settlement event.
- `based_on_payment_terms` fetches non-return invoice Payment Schedule rows; term allocation uses schedule paid/discounted values, advance handling and further allocation of parent paid/credit amounts across terms. It exposes computed term outstanding; the implementation contains FIFO-style allocation, not evidence of an authoritative actual payment-to-installment mapping.
- Current installed invoice source says outstanding_amount uses party_account_currency and due_date can be the latest contractual installment date. A positive invoice balance past final due supports Option B's restricted predicate; it must not be renamed “overdue installment amount”. Fully settled balances do not inherit positive original schedule obligations.
- Returns/credit notes participate in report reconciliation; the term query excludes is_return invoices. Discounts affect term paid amounts. Write-offs, POS, credit reversals, advance/discount rounding and currency modes require an independent site oracle before enabled coverage; source presence is not a universal correctness PASS. In particular, schedule/base/party currency conversions must be reconciled before term amounts are exposed.
- Stored invoice Overdue status is maintained by write-shaped updater logic and may lag observation. No status updater/refresh was invoked. V1 should use qualified fields/date, not trust stored status as current truth.

AI002 [MASTER §4 Amendment A1](../../features/AI002/AI002_MASTER_SSOT_V1_2_1_REFINED.md) disallows inferred FIFO **as verified cash/installment allocation** absent a verified mapping. This is relevant reuse boundary, not a blanket ban on ERP report presentation. Option A needs explicit business approval to represent ERP-policy computed allocation, plus independent oracle; it cannot silently become AI002 verified cash timing. No feature contract changed.

## Permission/read lifecycle evidence

Newly traced **actual installed list path**: `frappe.client.get_list → frappe.get_list → model.qb_query.DatabaseQuery.execute → frappe.qb.get_query → database.query.Engine`. The older `model/db_query.py` alone is insufficient evidence for this installed target. Active list wrapper passes `ignore_permissions=False`, `ignore_user_permissions=False`, user/context and parent_doctype; save_user_settings defaults False. Direct query-builder `get_query` defaults **ignore_permissions=True**, so it is not a safe substitute. [Active list](../evidence/phase0-round2-2026-10-10/ACTIVE_LIST_REPORT_CLOCK_SOURCE.txt), [exact permission code](../evidence/phase0-round2-2026-10-10/ACTIVE_QB_PERMISSION_EXACT.txt).

Active query engine checks read/select authority, owner/user/share/query conditions, field selection/filter/order permissions, linked and child-field permissions and masking. “Select” alone is not financial read permission; V1 must require read, required unmasked financial fields and non-bypass context. If required fields are removed/masked, return unavailable/forbidden per agreed policy, never infer zero. No ignored-permission/user flag or dynamic caller-supplied field/filter expression permitted.

`frappe.client.get` loads a document, checks permission and applies field-level read permissions before returning it. `Document.apply_fieldlevel_read_permissions` strips unauthorized parent and child fields and masks values; Administrator bypasses this path. In-process adapter must explicitly do the equivalent after `get_doc`, then project its allowlist; `get_doc` alone is not authorization. Do not expose all parent/child data as returned by generic get.

Report delivery validates report access, reference report permission and filter permissions, and `generate_report_result` is read-only decorated; `get_filtered_data` applies linked user/share/owner filtering and some masking. Raw AR internals use SQL/get_all/QB reads, so direct `execute` bypassing the report wrapper is not equivalent to authorized public report delivery. No complete field-level permission proof for derived report/child amounts established. Prepared-report mode/site overrides may create background/cache/state effects: do not call refresh/prepared branches as discovery acceptance.

Read source inspection found no need to invoke invoice status updater for proposed B. A business-read path can still touch framework metadata/cache/audit; custom hooks/effective settings and full execution side effects remain NOT_VERIFIED. “Zero ERP mutations” must distinguish accounting/document writes from explicitly reviewed observability metadata. No current live read-only assertion was run.

Site date source: `now_datetime` uses `ZoneInfo(get_system_timezone())`; get_system_timezone reads System Settings.time_zone or defaults Asia/Kolkata; nowdate derives that date. Host Asia/Saigon and previous-site historical timezone are not current target facts. Freeze one server observation instant/date/timezone per query, test local-midnight boundaries; no browser “today” or fixed2026 cutoff.

## Options and selection

| Axis | A — TERM_AWARE_OVERDUE | B — PAST_FINAL_DUE_INVOICES |
|---|---|---|
| User/demo value | Finds earlier missed installments; strongest broad promise | Smaller truthful find/open task, credible if limitation shown |
| Source correctness | Report exists; term allocation policy/mapping/currency still unqualified | Positive current invoice residual and authoritative final due needed; cannot prove installment overdue amount |
| Permission | Authorized report plus derived/child-field checks and detail reauthorization | Authorized parent list/read plus field checks; fewer dependencies |
| Currency/precision | Report/term/base/party modes need oracle | Preserve decimal residual in party_account_currency; no FX/totals across currencies |
| Coverage | Returns/credits/advances/discount allocation and terms | Proposed submitted, non-return, positive current residual, final due < observed local date; abnormal/missing data disclosed |
| Dependency/blast radius | Ledger/report/child allocation orchestration; wider | Shared narrow parent read/navigation port; no term reads or financial engine dependency |
| Testability | Independent installment ledger policy oracle required | Independent approved invoice/voucher fixtures and field/date permission oracle required |
| Verdict | BLOCKED; no qualified actual allocation | **Recommended candidate, still BLOCKED** on site/field/balance/date oracle and contract approval |

Chat must approve the submitted/non-return policy, treatment of linked credits/write-offs/POS/missing due and label. If unsupported data occurs, suppress unverifiable amount and report PARTIAL/NOT_AVAILABLE; never claim comprehensive overdue coverage. Negative balances are credits, not zero or payable overdue. Future-posted records and reversals also need an explicit inclusion policy before G2/G3.

## Proposed application boundary, status and evidence

Existing architecture reused: ordinary UI or future chat → `SearchOverdueInvoices` / `ResolveInvoiceNavigation` → `AuthorizedInvoiceReadPort.search/read` → in-process Frappe adapter. These named invoice use cases/port are **proposed, not existing verified symbols**. Remote ERP requires separately qualified typed HTTP/client adapter; SDK cannot supply delegation or permission proof. No new dependency proposed here.

Server-only `ExecutionContext`: authenticated actor, product, site, connection/version, authorized company, observation instant/local date/timezone, deadline, contract version, correlation_id. Client input: bounded customer/invoice candidate text or opaque reference/cursor; never actor, arbitrary endpoint/doctype/SQL, company authority or source-mode claims. Resolve customer/IDs only within authorized company and record scope; ambiguity returns authorized choices without existence leakage.

Candidate parent allowlist: `name, company, docstatus, is_return, customer, due_date, outstanding_amount, party_account_currency, currency, modified`; add posting_date only if approved inclusion rule requires it. Optional customer display name needs separately authorized field access. Missing required/masked fields fail closed. Terms/PLE not fetched for B. Backend reads candidate predicate/date fields; no frontend database query/computation. Detail rechecks actor/company/document and financial-field permissions immediately before navigation; reject stale source version or repreview, not cached permission reuse.

Proposed output:

```text
InvoiceReadOutcome {
  status: OK|NO_MATCH|AMBIGUOUS|PARTIAL|FORBIDDEN|SOURCE_ERROR|
          TIMEOUT|NOT_AVAILABLE|STALE_REFERENCE,
  capability: PAST_FINAL_DUE_INVOICES, contract_version,
  observed_at, local_date, timezone, authorized_scope, correlation_id,
  items: [reference, final_due_date, current_outstanding_decimal,
          party_account_currency, source_modified, evidence_ref],
  coverage: {complete, fetched_rows, scanned_rows, returned_rows,
             missing_required_data, truncated, reason},
  next_cursor?, safe_navigation?, limitations[], explanation_status
}
```

Financial Decimal strings must be finite, correctly rounded to qualified field/currency precision; retain unit, never replace nonfinite/missing with zero. Only qualified amounts/evidence can carry ERP_VERIFIED. Source availability, coverage, reference availability and optional explanation availability remain separate. No LLM explanation needed for finding/opening records.

| Proposed status | Existing convention compatibility, not a global enum change |
|---|---|
| OK | Existing success/SUCCESS transport variants normalize only after qualified data; ERP docstatus1 is unrelated. |
| NO_MATCH | New invoice-use-case outcome; complete authorized valid scope with no candidates. Not empty-page/outage/hidden-fields/truncated-scan inference. |
| AMBIGUOUS | Selection required, not financial/source failure; choices stay authorized. |
| PARTIAL | Existing financial partial concept preserved with explicit unavailable fields/coverage. |
| FORBIDDEN | Existing permission concept; HTTP401/403 or typed failure may accompany it; no target existence leak. |
| SOURCE_ERROR / TIMEOUT | Existing source-error convention / explicit deadline outcome; safe text and CID; no zero substitution. |
| NOT_AVAILABLE | Missing capability/qualified source/data; not no-match. |
| STALE_REFERENCE | New scoped-reference outcome; re-search/reauthorize, not automatic navigation. |

Reference/cursor must be server-authenticated opaque token, purpose-bound to actor/product/site/connection/company/query/contract/version/expiry. Signing prevents forgery, not revocation; reauthorize each request. Never return an LLM URL. Adapter returns allowlisted product route descriptor/encoded authorized invoice identifier after current read; Desk versus React target must first be selected under T1. On company/connection switch, invalidate references/cursors/results and fence late responses. Prompt injection in customer/invoice text has no authority to add tools/scopes/routes. No generic ERP CRUD or arbitrary RPC exposed.

Stable order proposed `name` keyset for bounded eligibility scans; due-date sorting may happen within qualified returned subset. Mutable rows/inserts/revocation mean a signed cursor is not a snapshot. Coverage is PARTIAL across unstable/truncated windows until a qualified query-consistency policy is established. Scan eligible authorized positive invoices and detect missing due fields rather than treating a filtered empty due-date page as complete. NO_MATCH requires completed scope/data checks under declared consistency; do not promise full snapshot coverage from offset pagination. Contract consistency remains a G2/G3 decision.

## Independent acceptance design and bounds

All following **DESIGNED / NOT_RUN**. Gold must be independently prepared from approved isolated vouchers/source fields and permission matrix, not the new use-case output or report's own computed totals. No invented live fixture values in this packet.

| Approved fixture condition | Required assertion |
|---|---|
| Two authorized submitted non-return invoices, final due before observed date, residual positive | B returns both exact authorized identities/current residuals/units/evidence; detail reauthorization allows expected target. |
| Cross-company inaccessible invoice | Absent from candidates/counts and denied detail/reference without existence leakage. |
| Permission revoked between search and open | Open denied, prior facts/reference not treated as current authority. |
| Multiple terms: one unpaid term past due, final due in future | B excludes and displays restricted capability label. A includes only after independently verified term-residual oracle; no parent residual called installment overdue. |
| Partial payment; full settlement | Past-final positive parent residual retained with correct unit; settled invoice excluded even if original schedule rows remain positive. |
| Return/credit/reversal/write-off | Approved policy distinguishes non-return parent residual and credit records; reconciled <=0 excluded; no negative→zero/payable conversion; unavailable reconciliation disclosed. |
| Missing final date/terms | B requires final date; required missing data disclosed PARTIAL/NOT_AVAILABLE, not false NO_MATCH. A needs required term mapping. |
| Mixed invoice/party-account currencies; POS/discount | Exact residual unit/precision matches independent oracle; no invoice-currency relabelling/FX aggregate; unsupported cases unavailable. |
| Local-midnight boundary | Frozen server instant maps to approved site-local date; due-today not past-final under strict `<` rule. |
| Error/timeout | Safe typed outcome/CID, no cached or synthetic success/zero. |
| Forged/expired/wrong-context cursor/reference | Denied before target query/navigation; permission still checked for valid signed token. |
| Late switch/pagination boundary | Old facts cannot reappear; no duplicates within declared stable window; row/page cap yields explicit incomplete coverage, never NO_MATCH. |
| Prompt injection/unsafe navigation | Text displayed as data; cannot add action/endpoint/recipient; encoded allowlisted route only. |
| Mutation absence | Instrument actual SQL/document writes/queues/email/provider calls; invoice/status/ledger/company/permission state unchanged. Explicit observability writes separately declared. |

**Candidate enforceable bounds, unmeasured and not release SLOs:** internal page50, max5pages/**250 scanned parent rows per invocation**, returned candidates≤50; child-term reads0 for B; tool invocations≤1 per search or resolve, no autonomous loop; adapter source calls≤5 search pages plus explicitly capped metadata/authorization overhead recorded separately, detail≤1 parent read plus authorization/metadata calls. Fetched/scanned/returned rows and source bytes each accounted; proposed fetched-byte cap1MiB and final output256KiB; total deadline5s with cancellation/deadline checks between calls and qualified DB/transport timeout. No blind retries; default0, at most1 documented safe transient read retry only within the same deadline/call budget. Bounds include lookahead; no uncounted N+1 page. In-process hard cancellation is not proven by a UI abort. Reference TTL and query consistency must be approved, not guessed as an acceptance threshold.

Future G4B workload: declared canonical image/hardware/database size, empty/50/51/250/251 candidate windows, large authorized nonmatches/missing dates, partial payments/multicurrency/permission restrictions, warm/cold runs and declared concurrent users/workers; measure actual API/report/adapter calls **separately** from SQL statements/rows, bytes, p95 latency and peak RSS. No p95/throughput/RSS PASS from one request/mock. Current performance **NOT_RUN**.

One server CID must follow UI/chat → use case → adapter → outcome/audit; redacted structured audit actor/product/site/company/target/action/version/status/duration/CID. No credentials/raw financial documents/tool payloads/model reasoning logged. Session-free public use case: G01–G03 NOT_APPLICABLE. Calling it through existing stateful AI007 requires separate session gates, currently BLOCKED.

## Ownership, minimal future plan and remaining qualification

Chat owns business/source/status/coverage/reference contract; Work qualifies target/oracle; Antigravity implements only approved exact edits. Source revision and hashes above plus [host manifest](../evidence/phase0-round2-2026-10-10/SELECTED_SOURCE_MANIFEST.json). Existing candidate boundaries are `lotus_fin/lotus_fin/application/service/`, `application/port/`, `infrastructure/erpnext/`, `presentation/controller/`, `presentation/dto/`, `api/` and `lotus_fin/lotus_fin/tests/`. **No exact new implementation file set established or approved:** name the actual use-case/port/adapter/DTO/API/test files only after G2/G3 selects B and route. Do not invent current symbols or reuse generic invoice SQL as an approved port.

Future smallest plan: approve B predicate/units/coverage → qualify required parent fields and authorized list/detail on isolated target → independent oracle tests → typed read/search/resolve boundary reused by ordinary UI → selected safe navigation delivery → later chatbot integration. Impact touches selected invoice route and callers; permission/source adapter tests required before shipping; no engine/F102/session overhaul. Rollback disables the new read/navigation entry and reverts only approved files; no ERP changes to undo. Preconditions: T1 canonical isolated target, effective principals/metadata, independent current invoice reconciliation/date/field oracle, contract approval, bounded executable tests. **Next verification is targeted:** metadata+authorized list/detail/masking/revocation and B semantics on the reviewed clean baseline. No live execution here and no contract freeze.
