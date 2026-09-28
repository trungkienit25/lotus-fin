# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI002-00 — Runtime/Data Discovery & Contract Hardening

> **Historical snapshot, superseded for current gate status by [AI002-00B report](AI002_00B_CONTROLLED_FIXTURE_AND_GATE_CLOSURE_REPORT.md).** The 00 report below describes the site before the dedicated 2026 fixture was posted. Current local test fixture has Cash GL↔Trial Balance **11,550,000 VND**, ten invoices, four posted payments, partial/full settlement and positive original schedules on settled invoices. It is synthetic/test, not real SME data. Current four gates are all `PARTIAL`; overall `AI002_PARTIAL` and next action Continue AI002-00B. The earlier `BLOCKED` statuses and “no 2026 transactions” claims below are historical, not current site claims.

**Date:** 2026-09-26 · **Repo revision:** `ed8bb2bf706a5813aee0902946ae42a946eb9ef9` · **Environment:** local Docker site `frontend` · **Feature:** AI-F002 · **Decision:** `AI002_PARTIAL` / `HOLD_FOR_GATES`. Labels below distinguish `OBSERVED` runtime/code, `DERIVED` interpretation, and `PROPOSED` contract.

## 1. Executive verdict

`BLOCKED` for a 2026 30-day cash forecast. The site has a reconcilable **historical** 2020 cash balance and AR/AP reports, but its latest submitted GL posting is 2020-11-23; all open invoice due dates and all Payment Schedule due dates are in 2020. No future cash movement date or complete operating-obligation feed was verified. The deterministic scheduled method remains the P0 candidate. No AI002 engine, UI or model was built.

## 2. Environment inspected

`OBSERVED`: `bench --site frontend version` returned Frappe `16.34.0`, ERPNext `16.35.0`, Lotus Fin `0.0.1`; installed apps are `frappe`, `erpnext`, `lotus_fin`. MariaDB client reports `11.8.9`. `frappe.utils.now` returned `2026-09-26 11:35:35`; `frappe.utils.get_system_timezone` returned **`Africa/Abidjan`**. Companies `Name` and `Name (Demo)` both default to VND/Vietnam. Fiscal years present: 2019, 2020. Finance Book records: zero; Accounting Dimension records: zero. 42 GL entries have null `finance_book`. Container DB/Redis initially stopped; queries initially failed with unknown DB host, then succeeded after those containers were started.

## 3. Evidence boundary

Read-only `bench execute frappe.get_all` and `frappe.desk.query_report.run` on site `frontend`, current revision above, Administrator CLI context unless stated; summarized outputs below omit parties/voucher IDs. One permission test temporarily inserted a User Permission, exercised the guards and called `frappe.db.rollback()`; a subsequent query confirmed no Company User Permission remained. The only enabled non-Administrator account has broad `System Manager` and Accounts roles, so it does not prove a least-privilege role matrix. No production site or external obligations were inspected. AI001 2026-09-24 observations are historical evidence and conflict with current transaction counts (AI001: 6 SI/5 PI/8 PE; current: 5 SI/6 PI/5 PE); no silent reconciliation.

## 4. Runtime facts

`VERIFIED / OBSERVED`: standard Script Reports `Accounts Receivable`, `Accounts Payable`, `Trial Balance`, `General Ledger`, `Cash Flow` exist. Current `Sales Invoice` count 5, `Purchase Invoice` 6, `Payment Entry` 5, `Payment Ledger Entry` 16, `Payment Schedule` 26. All 42 sampled GL rows are submitted, not cancelled, with latest `posting_date=2020-11-23`. This establishes **site data age**, not present-day financial truth. See [runtime facts](AI002_RUNTIME_FACTS.md) for source-level detail.

## 5. Opening cash findings

`PARTIAL / OBSERVED`: Demo chart has two enabled leaf VND accounts typed Cash/Bank and two group accounts typed Cash/Bank. Exclude group accounts from summation; do not hard-code demo account names in product logic. For `Name (Demo)` at 2020-12-31, five submitted bank GL rows sum debit 47,000 minus credit 164,854 = **−117,854 VND**. Cash leaf has no GL rows. Trial Balance run with `company`, `fiscal_year=2020`, `from_date=2020-01-01`, `to_date=2020-12-31` returns bank closing debit 47,000 and closing credit 164,854, yielding the same net. First Trial Balance attempt without `fiscal_year` raised ValidationError; that filter is mandatory in this runtime. Explicit GL query through 2026-09-26 returns the same 42 total rows and **−117,854 VND** cash-leaf net: this is the ERP ledger-derived balance at that cutoff, but it is **stale** because no postings follow 2020-11-23 and no current bank reconciliation was observed. Negative cash is a valid ledger value. `NOT_VERIFIED`: current real-world bank cash, account inclusion/overdraft policy, Balance Sheet cross-check in this run, finance-book variation and FX. Proposed source: submitted GL through cutoff on enabled leaf Cash/Bank accounts with independent Trial Balance reconciliation; keep scope configurable and authorized.

## 6. AR findings

`PARTIAL / OBSERVED`: `Accounts Receivable` with `company=Name (Demo), report_date=2020-12-31` returned 3 voucher dict rows plus 1 list summary row, totaling outstanding **316,000 VND**. `report_date=2020-02-15` returned only the invoice already posted by then (229,000 VND); `report_date=2026-09-26` returned the same three old unpaid invoices. The report exposes `posting_date`, `due_date`, `invoiced`, `paid`, `credit_note`, `outstanding`, `currency`. Sales Invoice `posting_date` is required; `due_date` is optional and labeled **Payment Due Date**. All five current Sales Invoices have one Payment Schedule row, and all have due date = posting date in this fixture. `DERIVED`: due date is contractual obligation timing; it cannot establish actual collection day. `NOT_VERIFIED`: missing-due-date, multiple installments, credit note, partial/advance and cancelled invoice behavior because this fixture lacks those examples.

## 7. AP findings

`PARTIAL / OBSERVED`: `Accounts Payable` at 2020-12-31 returned 3 voucher dict rows plus 1 list summary row, outstanding **184,293 VND**. At 2020-01-10 only the earlier payable appeared (39,000 VND); at 2026-09-26 the same three old payables remained. Purchase Invoice has required `posting_date`, optional `due_date`, `outstanding_amount`, `currency` and `is_return`. All six current Purchase Invoices have one Payment Schedule row. `DERIVED`: known payable and contractual due date do **not** establish bank settlement date. Same missing edge cases as AR remain `NOT_VERIFIED`.

## 8. Payment/allocation findings

`VERIFIED / OBSERVED`: 5 submitted Payment Entries (2 Receive, 3 Pay); 5 Payment Entry Reference rows allocate 211,854 VND total; 16 Payment Ledger Entries. Two Sales Invoices and three Purchase Invoices have current outstanding zero, yet their Payment Schedule rows retain positive original `payment_amount` and `outstanding` values (47,000 VND sales and 164,854 VND purchase scheduled amounts). The 26 Payment Schedule rows include 5 Sales Invoice, 6 Purchase Invoice, 5 Sales Order and 10 Purchase Order parents. **Summing schedules with invoice outstanding would double count**, and treating settled schedule rows as future cash would recreate past payments. Rule `PROPOSED`: payments posted on/before `financial_as_of` are in actual/opening state; schedule only remaining, authorized obligations after reconciling Payment Ledger/allocations and deduplicating order→invoice chains. Internal Transfer must not create net company inflow/outflow. Advances, credit notes, reversals, cancellation and same-day ordering remain `NOT_VERIFIED` in fixtures.

## 9. Future obligation inventory

`OBSERVED`: Payment Request 0, Auto Repeat 0, Subscription 0, Journal Entry 0, Tax Withholding Category 0, Finance Book 0. Purchase Order 10 (6 Completed, 4 To Receive and Bill), all dated 2020. Sales Order 5, all Completed, dated 2020. Payment Schedule due-date range 2020-01-04 to 2020-11-23. Salary Slip, Payroll Entry, Loan and Expense Claim DocTypes were not installed in this app set (`NOT_AVAILABLE` **as ERP feeds here**). `DERIVED`: there is no verified 2026 ERP cash schedule, but no evidence that the business has zero payroll, tax, debt, OPEX or CAPEX. `NOT_VERIFIED`: external/manual obligations, records in other systems, record-level permissions, currency/status semantics for candidate feeds and completeness by company. Category map and proposed mandatory scope are in [source map](AI002_DATA_SOURCE_MAP.md).

## 10. Currency / Finance Book findings

`PARTIAL / OBSERVED`: both companies, sampled invoices and demo Cash/Bank leaf accounts are VND. Finance Book has zero records, all sampled GL `finance_book` fields null, and Accounting Dimension has zero records. This verifies only a single-currency/default-book example. Missing FX, account-currency variation and non-default finance book remain `NOT_VERIFIED`; no conversion may be invented.

## 11. Permission tests

`PARTIAL / OBSERVED`: named non-Administrator account can read `Name (Demo)` Company and AR Report; Guest denied. In a temporary transaction, User Permission for `Name` allowed it and caused `get_verified_company('Name (Demo)')` to raise `CompanyAccessError`. Supplying `company=Name` with modified `filters.company=Name (Demo)` to `extract_key_report_data` also raised `CompanyAccessError`. Arbitrary report key raised `ValidationError`. Rollback confirmed no Company User Permission remains. `CODE_RISK`: denial exception includes the requested company name; existing Company guard distinguishes nonexistent from forbidden. AI002 response must normalize to generic `FORBIDDEN` without existence/name leak. `NOT_VERIFIED`: lower-privilege accountant, source DocType permissions, evidence drilldown, cache isolation and stale UI response on company switch.

## 12. Temporal/as-of findings

`PARTIAL / OBSERVED`: sampled AR/AP `report_date` excludes invoices posted after that date. Current site timezone `Africa/Abidjan` conflicts with session Asia/Saigon; client-local midnight must not define financial cutoff. Report invoice `posting_date` and contractual `due_date` are separate fields; Payment Entry has its own `posting_date`. `NOT_VERIFIED`: sub-day GL ordering (posting fields observed as Date), as-of replay under backdated/cancelled corrections, same-day settlement ordering and timezone conversion across API/UI. `PROPOSED`: use site-local end-of-day cutoff, record exact timezone and retrieved/generated timestamps, replay only point-in-time visible records.

## 13. Reconciliation results

`VERIFIED` historical bank: GL `47,000 − 164,854 = −117,854 VND`, equal Trial Balance net at 2020-12-31. The 2026-09-26 GL cutoff yields the same amount because no newer GL exists; this is an observed **stale ledger balance**, not current bank reconciliation. `VERIFIED` historical AR/AP report totals at 2020-12-31: 316,000 / 184,293 VND; summary list rows excluded. `NOT_VERIFIED`: current bank truth, Balance Sheet comparison in this run, all-company/account reconciliation, current obligation completeness. These historical values cannot be presented as a reliable 2026 liquidity path.

## 14. Coverage assessment

`PROPOSED`: `TRADE_ONLY`, `OPERATING_CORE`, `COMPREHENSIVE` are explicit scopes; `coverage.completeness=VERIFIED` means all required feeds **inside that scope** were read and reconciled, never that the SME has no other liabilities. `TRADE_ONLY` must disclose excluded payroll/tax/debt/OPEX/CAPEX; operating/core and comprehensive need those sources or an approved external/manual feed. For 2026-09-26, **verified future cash-date horizon: none**. Product target 30 daily calendar days remains provisional; current data support neither a 30-day nor a 14-day dated cash path. Outstanding overdue AR/AP can be displayed as obligations, not dated cash movements.

## 15. Remaining blockers

Current bank-reconciled cash and future commitments; business inventory of payroll/tax/debt/OPEX/CAPEX; threshold and account policy approval; lower-privilege source/evidence matrix; multi-currency/finance-book and cutoff/backdating semantics; independent AI002 gold and required UI/security cases. `predict_cashflow` remains a whitelisted AR−AP stub with `LOW/WARNING` output. GitNexus impact returned `risk: UNKNOWN`, zero resolved callers and no processes on a stale index (5 commits behind); text search found Python tests, no Lotus UI call, but external API callers remain unknown. Deprecation plan `PROPOSED`: inventory API traffic, mark route unsupported in docs/tool registry, never link AI002 UI to it, then replace with a typed tombstone or remove after compatibility review and regression tests. No production rewrite in this task.

## 16. Contract changes

`draft-1` separates `obligations[]` (type, contractual due, remaining amount) from `cash_events[]` (cash date, `forecast_class`, `timing_basis`, explicit assumption/evidence). `data_mode`, `source_kind` and `trust_state` remain separate. A due date alone does not create a cash event. Coverage carries scope, completeness, included/missing/unverified/excluded sources and verified data horizon. `SHORTFALL_THRESHOLD=NOT_FROZEN`; candidates: below zero, approved liquidity buffer, or operational minimum. No `LOW RISK`/`SAFE` claim. Model failures only set `explanation.status=UNAVAILABLE` plus error code; valid top-level forecast stays `OK`/`PARTIAL`.

Observability `PROPOSED`: server-generated correlation ID, request/auth/source status and count, method/formula version, coverage, latency and explanation/model status. Existing AI001 observability has correlation/status plumbing but is feature-specific and its `details` field is unrestricted. Existing invoice/payment hooks log party/customer names and amounts (`OBSERVED` code), so AI002 cannot claim zero-PII telemetry until an allowlisted/redacted path is tested. Never log raw rows, account numbers, names, secrets, raw prompts or chain-of-thought.

## 17. Evaluation changes

P0 mandatory: independent Decimal gold, GL/Trial Balance reconciliation, cutoff replay, daily path, first-shortfall date/threshold boundary **after threshold approval**, coverage and zero/missing correctness, double-count fixtures, permission/tamper/evidence/E2E and failure matrix. Rolling-origin and confidence intervals become mandatory **only when estimated/statistical timing is enabled**; MAPE is not a mandatory cash metric near zero/negative values. No AI002 forecast-quality evaluation was run.

## 18. UX changes

`PARTIAL` view says **“Lowest modeled cash within included sources”** and shows a prominent omitted-obligation warning, never an unqualified projected lowest cash. Show actual opening, known contractual obligation, estimated cash timing and confirmed cash date distinctly. If no future cash dates are verified, show obligations/missing-data checklist without a fabricated line. No shortfall/risk badge until threshold approved. AI004 simulation remains separate. LLM failure preserves deterministic result.

## 19. Four-Gate reassessment

| Gate | Status | Evidence | Blockers |
| --- | --- | --- | --- |
| 1 Runtime | `BLOCKED` | Versions/site/timezone, historical GL/TB and AR/AP shape, payment/schedule counts, one permission transaction | Current cash/future cash dates, lower-privilege/source permission and precise cutoff |
| 2 Contract | `PARTIAL` | Timing/coverage/failure/UX `draft-1` now explicit | Product scope, shortfall threshold/disabled decision, account policy and horizon sign-off |
| 3 Data & Method | `BLOCKED` | Deterministic method chosen; historical cash reconciled and stale current-cutoff ledger value observed | No 2026 dated obligations or business coverage; current bank truth unverified |
| 4 Security & Evaluation | `PARTIAL` | Controlled company/filter guard pass, gold/security plan | Least-privilege/evidence/cache tests, independent transaction-backed gold/acceptance |

## 20. Recommendation

**`AI002_PARTIAL`; continue AI002-00 discovery.** Task packet remains `HOLD_FOR_GATES`. Next: Finance/Product chooses coverage scope and threshold behavior; ERP data owner supplies current, transaction-backed cash and dated commitments and verifies off-ERP obligations; Security/QA completes lower-privilege matrix, generic-denial policy and gold fixtures. Start AI002-01 Feature Contract Freeze only after those blockers are resolved. No AI002-02/03 implementation is authorized by this report.

## Review record

Reviewed: workflow v2, codebase-aligned AI Feature Specification, all seven prior AI002 documents, AI001 runtime/source and workspace artifacts, access/report/snapshot/observability/API code, hooks, tests inventory and Docker test site. Known limitation: Administrator CLI was used for source reads; only controlled guard/report permission checks used a named non-Administrator account. Unresolved document conflict: historical AI001 transaction counts differ from this revision's site counts. No secret or raw financial row is retained in this report.


