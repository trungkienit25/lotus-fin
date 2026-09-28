# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI002-00B — Controlled fixture, runtime closure and gate decision

**Date:** 2026-09-26. **Decision:** `AI002_PARTIAL`. **Next action:** Continue AI002-00B. This report supersedes the gate table in [AI002-00 discovery](AI002_RUNTIME_DATA_DISCOVERY_REPORT.md); that report remains historical evidence. `OBSERVED` means direct site/code output; `DERIVED` is a calculation or inference; `PROPOSED` needs approval. The fixture is **synthetic test data posted through real ERPNext transactions**, never actual SME financial data.

## 1. Executive verdict

`PARTIAL / DERIVED`: a current-dated, isolated, transaction-backed company and independent opening-cash gold now exist. The strict baseline has **zero confirmed future cash-date events**. It cannot support a meaningful 30-day cash trajectory or a shortfall claim. Product scope/threshold/account/timezone decisions, source completeness and evidence/cache/security closure remain open. No AI002 engine, UI or LLM pipeline was implemented.

## 2. Revision/environment

`OBSERVED / VERIFIED`: repository revision `ed8bb2bf706a5813aee0902946ae42a946eb9ef9`, local Docker site `frontend`, Frappe `16.34.0`, ERPNext `16.35.0`, Lotus Fin `0.0.1`, MariaDB client `11.8.9`. Installed apps: `frappe`, `erpnext`, `lotus_fin`. Site system timezone `Africa/Abidjan`, workspace/user timezone Asia/Saigon. All fixture mutations occurred only in the local test site. GitNexus `impact extract_key_report_data --direction upstream` found three direct callers (`frappe_report_fetcher`, `predict_cashflow`, `get_ai_training_dataset`), one process group and `LOW` indexed risk; index was five commits behind. Prior `predict_cashflow` impact returned `UNKNOWN`; text search found tests but no Lotus UI caller. Neither result proves external whitelisted callers absent.

## 3. Source inventory

`OBSERVED`: submitted GL, Trial Balance, Sales/Purchase Invoice, Payment Entry, Payment Entry Reference, Payment Ledger Entry and Payment Schedule have current fixture records. ERP Payment Request, Auto Repeat, Subscription and related future sources have no verified fixture cash commitment. Payroll/Loan DocTypes were absent in the installed app set in AI002-00. `NOT_VERIFIED`: off-ERP payroll, tax, debt, recurring OPEX, CAPEX, manual commitments and bank statement truth. Source details are in [data source map](AI002_DATA_SOURCE_MAP.md). Zero ERP records never means zero business obligations.

## 4. Controlled fixture design

`OBSERVED / VERIFIED`: dedicated company `AI002 Fixture 2026`, abbreviation `A2F`, country Vietnam, default currency VND, Standard chart, fiscal year 2026. Created apart from `Name (Demo)` 2020 history. One non-stock test service item and existing demo master parties were used. Values and dates are plausible **invented test scenario values**; no 2026 SME source or public dataset was represented as real. `Cash - A2F` is the only posted Cash/Bank leaf account in this fixture. No bank statement reconciliation. The original due-date-before-posting validation failure was rolled back; setting explicit invoice posting dates allowed valid submission.

## 5. Transactions created

`OBSERVED / VERIFIED`: one submitted Journal Entry `ACC-JV-2026-00001` on 2026-09-01 debits Cash and credits Opening Balance Equity 12,000,000 VND. Five submitted Sales Invoices: `AR_IN` 3,000,000 due 10-02; `AR_OVERDUE` 2,000,000 due 09-20; `AR_BEYOND` 1,000,000 due 11-15; `AR_PARTIAL` 1,500,000 due 10-10; `AR_SETTLED` 500,000 due 10-06. Five submitted Purchase Invoices: `AP_IN` 4,000,000 due 10-04; `AP_OVERDUE` 1,250,000 due 09-19; `AP_BEYOND` 1,500,000 due 11-18; `AP_PARTIAL` 2,000,000 due 10-12; `AP_SETTLED` 750,000 due 10-08. Four submitted Payment Entries on 09-22: Receive 600,000 and 500,000; Pay 800,000 and 750,000, all allocated against their named invoices. IDs and exact expected amounts are in [gold manifest](../AI002_GOLD_FIXTURE_MANIFEST.yaml). No Internal Transfer, advance, credit note, cancellation, future-posted invoice or confirmed future payment was created; those cases remain `NOT_VERIFIED`.

## 6. Opening cash reconciliation

`OBSERVED / VERIFIED` as ERP ledger balance at financial as-of 2026-09-26: five Cash GL rows; debit 13,100,000, credit 1,550,000, net **11,550,000 VND**. Trial Balance Cash leaf for 2026-09-01 to 2026-09-26 returns the same debit/credit. `DERIVED`: independent transaction arithmetic = 12,000,000 + 600,000 + 500,000 − 800,000 − 750,000 = **11,550,000**. Group accounts were excluded. This is `ERP_LEDGER_RECONCILED`, not bank statement or real business cash reconciliation. Balance Sheet cross-check and restricted/bank/overdraft account policy remain `NOT_VERIFIED`.

## 7. AR runtime findings

`OBSERVED / VERIFIED`: at cutoff, outstanding is `AR_IN` 3,000,000; `AR_OVERDUE` 2,000,000; `AR_BEYOND` 1,000,000; `AR_PARTIAL` **900,000** after 600,000 received; `AR_SETTLED` **0** after 500,000 received. `DERIVED`: total fixture AR 6,900,000. The due date is a contractual due date, not a confirmed collection date. Report adapter returned five AR rows for the authorized finance test user. Credit/return, multiple installment and missing due-date cases remain `NOT_VERIFIED`.

## 8. AP runtime findings

`OBSERVED / VERIFIED`: at cutoff, outstanding is `AP_IN` 4,000,000; `AP_OVERDUE` 1,250,000; `AP_BEYOND` 1,500,000; `AP_PARTIAL` **1,200,000** after 800,000 paid; `AP_SETTLED` **0** after 750,000 paid. `DERIVED`: total fixture AP 7,950,000. Due date does not prove bank execution date. Credit/return and multi-installment cases remain `NOT_VERIFIED`.

## 9. Payment/allocation findings

`OBSERVED / VERIFIED`: four submitted fixture Payment Entries have Receive/Pay directions and allocations. The two fully settled invoices still each have a positive original Payment Schedule row (`500,000` AR, `750,000` AP); partially settled schedules still show originals (`1,500,000` AR, `2,000,000` AP). `DERIVED`: raw Payment Schedule `outstanding` is unsafe as residual cash schedule. Payment Entry postings on/before cutoff already affect opening cash and must be excluded from future events. Internal transfer netting, advances/reversals, cancellation and Payment Ledger point-in-time replay remain `NOT_VERIFIED`.

## 10. Future commitment findings

`OBSERVED`: invoice contractual due dates occur within and beyond the 30-day horizon. `DERIVED / VERIFIED` classification: they prove obligation/due timing, **not confirmed future cash date**. No tested ERP source establishes a confirmed cash date after cutoff. No source has been promoted solely because it contains a date. Future-date horizon for strict baseline remains **none**. Payroll/tax/debt/OPEX/CAPEX and off-system obligations remain `NOT_VERIFIED`, regardless of named ERP source counts.

| Category | ERP candidate / presence | Business/date semantics | Company, permission, currency and coverage state |
| --- | --- | --- | --- |
| Trade AR/AP | Ten fixture invoices and ten schedules | Verified obligation and contractual due date; cash settlement date unproved | Fixture company, authorized Accounts User sampled, VND; `PARTIAL` for cash timing |
| Payment Request | DocType exists; zero records in earlier inventory | Request is not proof of bank settlement | Record-level role/date/currency semantics `NOT_VERIFIED` |
| Auto Repeat / Subscription | DocTypes exist; zero records in earlier inventory | Recurrence can describe planned document generation, not automatically payment | Company/permission/currency and business coverage `NOT_VERIFIED` |
| Purchase/Sales Order | Historical demo records and schedules | Order commitment can overlap invoice; no automatic cash settlement | Company and deduction chain `PARTIAL`; current fixture orders absent |
| Payroll | Named payroll DocTypes absent in installed apps | Business payroll may exist outside ERP | ERP feed `NOT_AVAILABLE`; business coverage `NOT_VERIFIED` |
| Tax | Tax Withholding Category had zero records | Category is not a dated tax-payment schedule | Named feed `VERIFIED_ZERO_RECORDS`; business coverage `NOT_VERIFIED` |
| Debt service | Named Loan DocType absent | External loan obligations unknown | ERP feed `NOT_AVAILABLE`; business coverage `NOT_VERIFIED` |
| Recurring OPEX, expense, CAPEX | Expense Claim named feed absent in earlier inventory; other valid source not established | Planned spending is distinct from posted expense and cash | `NOT_VERIFIED` |
| Journal Entry | One posted fixture opening transaction | Actual accounting entry, not a future commitment feed | VND fixture `VERIFIED` as historical cash only |
| Manual/off-ERP | No authorized feed provided | Could contain material future obligations | `NOT_VERIFIED`; never infer zero |

## 11. Daily EOD semantics

`PROPOSED`: for dates 2026-09-27 through 2026-10-26, a daily point means end-of-day modeled cash after eligible events dated that day, using the approved accounting timezone. Date-only invoice/GL fields do not prove 9 AM versus 4 PM liquidity. Intraday claims are disabled. The manifest lists the flat 11,550,000 arithmetic result for all 30 days, **internal gold only**; UX must not plot it as a meaningful forecast while no future cash event is verified. Source backdating/cancel-after-origin replay is `NOT_VERIFIED`.

## 12. P0 baseline vs estimated-layer decision

`PROPOSED` technical default: **Option A strict baseline** = reconciled opening cash + future events with separately proven confirmed cash date or verified schedule settlement semantics. Invoice due dates remain obligations and contribute **zero** to strict baseline. An estimated due-date layer is `P1 / DECISION_REQUIRED`, separately labeled and only after Finance/Product approves its rule, evaluation and UX. Option B may offer product value but requires approval; C must never be named confirmed scheduling. This same rule is now repeated in Method Options and Feature Freeze. No statistical/ML timing justified by this fixture.

## 13. Cash-event provenance contract

`PROPOSED`: every cash event must have either `obligation_id` or complete direct provenance (`source_kind`, `trust_state`, `source_ref`, `evidence_refs`, `timing_basis`, `assumption_id`). In both paths require authorized company, cutoff, signed direction/amount, currency, date, method/formula version and reconciliation state. Reject orphan event. For direct manually entered commitments, unverified/estimated status is explicit; never silently promote to ERP actual.

## 14. Coverage-scope decision

`PROPOSED / DECISION_REQUIRED`: retain `TRADE_ONLY`, `OPERATING_CORE`, `COMPREHENSIVE` as named scopes; Finance/Product must approve P0 scope. `TRADE_ONLY` requires opening cash plus verified AR/AP and discloses excluded/unverified payroll, tax, debt, recurring OPEX, CAPEX and off-system obligations. `OPERATING_CORE` additionally requires payroll, tax, recurring OPEX; `COMPREHENSIVE` adds debt/CAPEX/other material commitments. `coverage.completeness=VERIFIED` applies only inside the declared scope and never proves no off-system liability. Current fixture proves trade documents and cash arithmetic, not full business coverage.

## 15. Threshold decision

`DECISION_REQUIRED`: below zero, configured buffer and operational minimum remain candidates; overdraft treatment is unapproved. `PROPOSED` fail-safe: `SHORTFALL_CLAIMS_DISABLED_FOR_P0` until Finance/Product approves a rule. Then no shortfall event, first-shortfall date, safe/risk badge or inferred zero threshold. This disabling rule is a gate-safe contract proposal, not an owner-approved final threshold.

## 16. Cash-account policy

`OBSERVED`: fixture has posted leaf `Cash - A2F`; no tested Bank leaf balance. `PROPOSED / DECISION_REQUIRED`: include only active authorized leaf Cash/Bank accounts selected by explicit scope; exclude group accounts and restricted cash unless Finance approves; reconcile account currency and book, define overdraft/negative balances and inactive/frozen behavior. Never hard-code `Cash - A2F` in product code. A one-account fixture cannot verify multi-account policy.

## 17. Timezone/cutoff decision

`OBSERVED`: installed site reports `Africa/Abidjan`; company is configured Vietnam and user locale is Asia/Saigon. `PROPOSED`: `financial_as_of` and daily boundary use a single configured accounting timezone; `retrieved_at`/`generated_at` use UTC instants; UI displays timezone explicitly. Browser midnight never changes accounting cutoff. `TIMEZONE_CONFIG_REQUIRES_OWNER_CONFIRMATION`: which timezone defines Vietnam business accounting day is unresolved. API/UI serialization and same-day order are `NOT_VERIFIED`.

## 18. Currency/FX decision

`OBSERVED`: test company and sampled transactions are VND. `PROPOSED`: P0 accepts one verified reporting currency; reject unsupported conversions with typed unavailable status. FX requires approved rate source/date/pair/rounding/evidence, none verified. Multi-currency, non-default Finance Book and Accounting Dimension behavior remain `NOT_VERIFIED`.

## 19. Least-privilege security results

`OBSERVED / PARTIAL`: rollback-only test users with `Accounts User` role and Company User Permission were used. Authorized `ai002.finance@test.invalid` could resolve fixture company and extract five AR report rows, and had GL/AR/AP report permission plus Sales Invoice, Payment Entry and Payment Ledger record read. Denied `ai002.denied@test.invalid` could not resolve/extract fixture company or read fixture invoice/payment/ledger records. Company filter tampering to `Name (Demo)` raised `CompanyAccessError`; arbitrary report key raised `ValidationError`. Temporary users/permissions were rolled back. `CODE_RISK`: `get_verified_company` names the requested company in forbidden and missing-company exceptions, allowing existence distinction. Report permission alone was allowed for the denied user; the combined extractor's company guard prevented the read. Generic `FORBIDDEN` normalization needs implementation and test.

## 20. Evidence/cache/company-switch results

`NOT_VERIFIED`: no AI002 evidence drawer, AI002 cache or company-switch UI exists to test. Record-level invoice/payment/ledger `has_permission` was sampled, but a future evidence API must reauthorize on open. Required acceptance: cache key binds user/company/cutoff/scope/versions; clear old data and discard late response after switch; denied response carries no prior-company payload. Direct arbitrary DocType endpoint behavior beyond sampled records is `NOT_VERIFIED`.

## 21. PII/observability review

`OBSERVED / PARTIAL`: AI001 `observability.log_event` returns unrestricted `details` and includes company; some callers log raw error strings or snippets; existing invoice/payment hooks log party names and amounts. A runtime canary using **fake sentinel data only** returned both `CANARY_AI002_PERSON` and `987654321` unchanged in `details` (`sentinel_party_returned=true`, `sentinel_amount_returned=true`). The asserted zero-PII guarantee is therefore not enforced by the logger. `PROPOSED`: AI002 allowlist only correlation ID, feature/contract/method/formula versions, status, source type/status/count, coverage, latency, model status, error class; test the actual logging sink and hooks after remediation. No production logger was changed here.

## 22. Gold fixture and deterministic evaluation

`OBSERVED`: [machine-readable gold](../AI002_GOLD_FIXTURE_MANIFEST.yaml) independently calculates opening from submitted transactions; it lists 30 daily strict arithmetic points and explicit excluded invoices/payments. `DERIVED`: expected service status is `FORECAST_UNAVAILABLE` with no rendered path and no shortfall events because no confirmed future cash dates and no approved estimated rule exist. The manifest is **not a passing engine test**: no AI002 forecast service exists. Runtime verified partial/full allocation and stale Payment Schedule amounts; credit, transfer, negative/zero opening, year boundary, source timeout, FX and model fallback remain test gaps. Statistical rolling-origin/MAE/RMSE/intervals are conditional on an enabled estimated/statistical layer; MAPE near zero is not mandatory.

## 23. External research used

None. No public data were crawled or imported. Current-day 2026 values were invented for an explicitly labeled test scenario and posted through ERPNext. External macro datasets in the workspace do not establish SME accounting truth. No external research notes file is warranted.

## 24. Remaining blockers

`DECISION_REQUIRED`: Finance/Product P0 coverage scope, threshold or formal disabled state, overdraft/account inclusion, estimated timing P0 versus P1, accepted timezone and 30-day product target. `NOT_VERIFIED`: confirmed future cash source, full business obligation inventory, current bank statement truth, internal transfer/credit/advance/cancel/backdated/FX cases, evidence/cache/company-switch E2E, generic denial, logging canary and live provider fallback. No real 2026 SME financial dataset was supplied; `REAL_BUSINESS_DATA_READY=false`.

## 25. Four-Gate reassessment

| Gate | Status | Evidence and reason |
| --- | --- | --- |
| 1 Runtime | `PARTIAL` | Current valid fixture, GL/TB/AR/AP/payment semantics and limited role matrix; future cash-date source, account/timezone and point-in-time edge cases missing |
| 2 Contract | `PARTIAL` | Strict baseline, daily EOD, provenance, safe failure proposals aligned; owner scope/threshold/account/timezone/estimated-layer choices open |
| 3 Data & Method | `PARTIAL` | `IMPLEMENTATION_DATA_READY=false`: transaction-backed gold/opening exist, but no eligible future cash-date case. `REAL_BUSINESS_DATA_READY=false` |
| 4 Security & Evaluation | `PARTIAL` | Least-privilege allow/deny and filter tamper observed; generic denial fails, evidence/cache/E2E and full gold/failure matrix remain |

## 26. Final recommendation

**`AI002_PARTIAL` — Continue AI002-00B.** The current fixture removes the stale-2020 opening-cash blocker for engineering study, but cannot be called real business data or a validated cash forecast. Finance/Product must sign off the product claims; Security/QA must close the identified access and evidence gaps; ERP data owner must verify a legitimate future cash timing feed or accept a deliberately sparse strict baseline. Only then reassess readiness for **AI002-01 Contract Freeze**. Keep deprecated whitelisted `predict_cashflow` out of UI and agent tools; inventory callers, emit deprecation warning, then plan a typed tombstone/removal with compatibility review. No implementation authorization is implied.


