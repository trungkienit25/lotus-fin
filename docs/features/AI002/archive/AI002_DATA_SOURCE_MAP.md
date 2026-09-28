# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI002 data source map

> **AI002-00B source update:** Historical counts and `Name (Demo)` statements below remain the pre-fixture snapshot. On the dedicated 2026 test company, valid ERPNext documents yield reconciled opening Cash **11,550,000 VND**; five Sales and five Purchase Invoices include overdue, in-horizon, beyond-horizon, partially paid and fully settled cases. Four posted Payment Entries contribute to opening, not future cash. Invoice `Payment Schedule.outstanding` remains original even when invoice `outstanding_amount=0`; use invoice residual and allocation evidence. **No tested future source proves a confirmed cash date**, so the strict path has no eligible events. Current fixture and IDs: [gold manifest](../AI002_GOLD_FIXTURE_MANIFEST.yaml); complete status: [AI002-00B report](AI002_00B_CONTROLLED_FIXTURE_AND_GATE_CLOSURE_REPORT.md). Synthetic fixture is accounting-backed test data, not actual SME business data.

**Future-source classification contract (PROPOSED):** record category, ERP source, record presence, business meaning, date meaning (`OBLIGATION`, `CONTRACTUAL_DUE_DATE`, `CONFIRMED_CASH_DATE`, `ESTIMATED_CASH_TIMING`), company scope, permission, currency, coverage and state (`VERIFIED`, `PARTIAL`, `NOT_VERIFIED`, `NOT_AVAILABLE`, `NOT_APPLICABLE`, `VERIFIED_ZERO_RECORDS`). A zero-record ERP feed does not prove zero business obligations. Any dated cash event requires obligation ID **or** direct source reference plus evidence, trust, timing basis and assumption ID; reject orphan events.

**Status:** discovery only, 2026-09-26. `PARTIAL` means historical AI001 evidence and/or live source/schema presence exists, not that the source is fit for a current forecast. `NOT_VERIFIED` means no sufficient AI002 runtime proof. `NOT_AVAILABLE` requires a live negative check; no source below is called that merely because it was not found in documents.

| Input | Candidate report/DocType and fields | Trust / mode | Date, currency, permission | Completeness, evidence, status |
| --- | --- | --- | --- | --- |
| Opening/current cash | GL submitted entries in enabled leaf `Account.account_type in (Cash, Bank)`; Trial Balance cross-check | ERP actual, derived balance | Posting date through `financial_as_of`; company/book/account currency; report and account read grants | 2020-12-31 Demo leaf bank GL debit 47,000 minus credit 164,854 = −117,854 VND, matches Trial Balance; Cash leaf has no entries. Explicit 2026-09-26 GL cutoff yields same net because no later postings. Ledger value observed but stale; current bank truth and account policy unknown. `PARTIAL` |
| AR outstanding | Accounts Receivable: voucher, outstanding, paid, credit_note | ERP actual receivable, **not cash** | `report_date` snapshot, company, VND in demo; report access | Live 2020-12-31 and 2026-09-26 reports: 3 voucher dict rows, one list summary row, 316,000 VND. Earlier as-of excludes future-posted invoices. All surviving due dates are 2020. `PARTIAL` |
| AR due date | Accounts Receivable `due_date`; Sales Invoice `due_date` (live schema: optional) / payment schedule candidate | Contractual timing, not settlement | Compare to as-of in site timezone; source currency, invoice access | AI001 rows had due dates; schedule split and missing-date frequency unknown. `PARTIAL` |
| Expected customer inflow | AR outstanding + approved collection rule or separately confirmed receipt date | Obligation stays distinct; cash event is `ESTIMATED_CASH_TIMING` or evidenced `CONFIRMED_CASH_DATE` | Forecast date must not precede cutoff; convert only with verified FX | No collection probabilities, actual commitments or delay model verified. `NOT_VERIFIED` |
| AP outstanding | Accounts Payable: voucher, outstanding, paid, credit_note | ERP actual obligation, **not cash paid** | `report_date`, company and report permission | Live 2020-12-31 and 2026-09-26 reports: 3 voucher dict rows, one list summary row, 184,293 VND. Earlier as-of excludes future-posted invoices. All due dates are 2020. `PARTIAL` |
| AP due date | Accounts Payable `due_date`; Purchase Invoice `due_date` (live schema: optional) / payment schedule candidate | Contractual timing | Compare to cutoff; verify invoice currency and permission | AI001 rows had due dates; installment/schedule behavior unknown. `PARTIAL` |
| Supplier outflow | AP outstanding with separately confirmed cash date or explicit approved timing rule | Known payable remains an obligation; cash event `ESTIMATED_CASH_TIMING` unless cash date confirmed | Avoid counting posted payments, original invoice schedules and overlapping order rows | Invoice Payment Schedule retains original amounts after settlement; no confirmed future cash date. `NOT_VERIFIED` |
| Existing payments | Payment Entry `posting_date`, `payment_type`, `paid_amount`, `received_amount`, `paid_from/to`, `references`; Payment Entry Reference `allocated_amount`, `reference_doctype/name`, `due_date`, `exchange_rate`; Payment Ledger | ERP actual when submitted/posted | Include through cutoff only, company-scoped, payment/ledger read permissions | Live: 5 submitted entries (2 Receive/3 Pay), 5 allocations totaling 211,854 VND, 16 Payment Ledger Entries. Payment Schedule still shows original positive amounts on 5 settled invoices; never sum it with AR/AP outstanding. `PARTIAL` |
| Future known obligations | Candidate payroll, tax, loan, recurring, orders and manual commitments; `Payment Request`, `Auto Repeat`, `Subscription`, `Journal Entry`, `Purchase Order` DocTypes exist | Source-specific future commitment | Due/payment date, currency, lifecycle and role permissions | Live: first four sources have 0 records, 10 Purchase Orders dated 2020 (4 open for receiving/billing), 26 Payment Schedule rows dated 2020 across invoice/order parents. No verified 2026 cash schedule. Business completeness `NOT_VERIFIED` |
| Tax/payroll/loan | Tax Withholding Category exists with 0 records; Salary Slip, Payroll Entry and Loan DocTypes absent from installed `frappe`/`erpnext`/`lotus_fin` apps | Future commitment, not actual cash | Posted vs scheduled distinction and restricted access | Named payroll/loan ERP feeds `NOT_AVAILABLE` on this site; tax category has `VERIFIED_ZERO_RECORDS` but is not itself a tax-payment schedule. Business obligations and external/manual sources `NOT_VERIFIED`; never map to zero |
| Current period actual flow | Cash Flow and GL bank/cash movements | ERP actual | Posting date through cutoff, signed inflow/outflow, currency/book | Standard Cash Flow/GL reports exist; latest GL posting is 2020-11-23, so no verified current-period data. `PARTIAL` |
| Historical flow | Historical GL cash/bank movements and settlement events | ERP actual training/evaluation | Point-in-time cutoffs; no future labels in features | Only 2020 count known; coverage too small to claim statistical readiness. `NOT_VERIFIED` |
| Currency / FX | Company default currency, account/document currencies; exchange rate source candidate | ERP configuration / conversion | Rate date, precision, missing FX must block converted total | Both companies VND; sampled invoices and cash/bank accounts VND. Multi-currency and FX behavior unverified. `PARTIAL` |
| Finance book/dimensions | Trial Balance/GL finance_book and account dimensions | ERP actual/config | Same book and scope across cash/AR/AP; authorized filters | 0 Finance Book records, all 42 GL entries have null finance_book, 0 Accounting Dimension records on demo site. Default-book sample `VERIFIED`; non-default behavior `NOT_VERIFIED` |

Evidence basis: [AI001 runtime facts](../../../runtime/AI001_DATA_SOURCE_FACTS.md), [AI001 source map](../../../data/AI001_DATA_SOURCE_MAP.md), current `security/access.py`, `api/key_reports.py`, and `ai/financial_snapshot.py`. Runtime status is deliberately weaker than source existence.

## Obligation coverage inventory, live demo site

| Category | P0 disposition | Evidence and limitation |
| --- | --- | --- |
| Trade AR/AP | `MANDATORY` for `TRADE_ONLY` | Reports return outstanding and contractual due dates; all current due dates are years overdue, so cash timing is unverified |
| Payroll | `MANDATORY` for any operating/comprehensive claim | Payroll DocTypes absent; business payroll may be external. Source `NOT_AVAILABLE`, business coverage `NOT_VERIFIED` |
| Tax | `MANDATORY` for comprehensive claim | Tax Withholding Category 0 records; no dated tax payable feed verified |
| Debt service | `MANDATORY` for comprehensive claim | Loan DocType absent; external debt unknown |
| Recurring OPEX/subscriptions | `MANDATORY` for operating/comprehensive claim | Auto Repeat and Subscription exist but 0 records; off-system obligations unknown |
| Payment requests | `OPTIONAL` only after semantics verified | 0 records; request is not proof of bank settlement |
| Purchase commitments | `OPTIONAL` / `P1` | 10 Purchase Orders, 4 still to receive/bill; all dated 2020; order schedules overlap invoices and must be deduplicated |
| Sales commitments | `P1` | 5 completed Sales Orders dated 2020; order schedule overlaps invoices, not guaranteed cash |
| Journal schedules, planned CAPEX, manual commitments | `NOT_VERIFIED` | Journal Entry has 0 records; no separate dated CAPEX/manual feed verified |

`NOT_AVAILABLE` applies to the named ERP feed on this installed site, not to the real-world obligation. `TRADE_ONLY` is a possible bounded product scope, not a complete liquidity forecast.

## Source acceptance rules

For each source, record `source_name`, report/DocType and version, exact fields/filters, row grain, `source_kind`, `trust_state`, `data_mode`, `company`, `financial_as_of`, `retrieved_at`, currency/book, `record_count`, evidence reference, permission result, and completeness claim. `[]` becomes verified zero only after a successful, authorized, correctly scoped read with a valid schema and expected coverage. Timeout, permission failure, missing field and source error never become zero. Reconcile invoice outstanding after payments/credits before scheduling; deduplicate by stable voucher + schedule/reference key. Keep actual, forecast and simulation aggregates separate.


