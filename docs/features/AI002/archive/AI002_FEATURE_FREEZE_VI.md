# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI-F002 — Provisional Feature Freeze

> **AI002-00B addendum / governing state:** [00B report](AI002_00B_CONTROLLED_FIXTURE_AND_GATE_CLOSURE_REPORT.md) supersedes the gate table and pre-fixture data claims below. Current fixture: synthetic transaction-backed `AI002 Fixture 2026`, opening Cash **11,550,000 VND** GL↔Trial Balance, five AR/five AP invoices and four posted payments; **zero confirmed future cash dates**. Current gates: Runtime `PARTIAL`, Contract `PARTIAL`, Data & Method `PARTIAL`, Security & Evaluation `PARTIAL`; overall `AI002_PARTIAL` and **Continue AI002-00B**. P0 technical default is strict baseline only: no due-date cash movement without approved estimated rule. Estimated due-date overlay is P1 / `DECISION_REQUIRED`; 30 calendar days remains product target, not verified future-data horizon. `SHORTFALL_CLAIMS_DISABLED_FOR_P0` is the proposed fail-safe until threshold approval. Daily points mean EOD in an owner-approved accounting timezone; intraday timing unsupported. Finance/Product must approve scope, threshold/disabled state, account/overdraft policy and timezone. Synthetic fixture never counts as real SME data. These 00B statements replace any inconsistent earlier wording.

**Ngày:** 2026-09-26 · **Trạng thái:** `AI002_PARTIAL` · **Quyết định:** discovery/contract only; chưa giao coding. Cơ sở: provisional freeze của người dùng, [runtime facts](AI002_RUNTIME_FACTS.md), [source map](AI002_DATA_SOURCE_MAP.md), [method options](AI002_METHOD_OPTIONS.md).

## 1. Bài toán và ranh giới

SME Owner và Finance Manager cần thấy số dư tiền tại một thời điểm, các dòng thu/chi đã biết trong 30 ngày tới, ngày có áp lực thanh khoản, nguyên nhân và chứng từ cần kiểm. Accountant/Finance Staff hỗ trợ đối chiếu. Forecast hỗ trợ **điều tra và lập kế hoạch**, không tự quyết định hay thực hiện thanh toán. Sai số có thể tạo cảnh báo thiếu tiền giả, bỏ sót thiếu tiền, che nghĩa vụ, hoặc lộ dữ liệu công ty khác.

Đơn vị phân tích P0: **một company, một reporting currency, một cash/bank account set và finance-book scope nhất quán**. Cho phép drilldown account/bucket khi nguồn được xác minh; không cộng các company hoặc tiền tệ tùy tiện. UI là page/workspace riêng vì cần timeline, evidence và limitations. LLM chỉ giải thích kết quả typed đã tính, diễn đạt drivers và next checks; không tạo số, quyết định quyền, đọc DB, chọn report tự do hay thay forecast. Actual ≠ forecast ≠ simulation. AI004 scenario nằm ngoài P0.

**Ngoài scope:** autonomous decision, payment execution, LLM-generated numbers, revenue forecast, loan approval, long-horizon ML. `predict_cashflow` hiện có là route deprecated AR−AP, **không được dùng làm AI002** dù vẫn trả nhãn `LOW`/`WARNING`.

## 2. Input và output contract đề xuất, version `draft-1` (AI002-00)

Input server-validated: `company`, `financial_as_of`, `forecast_start`, `forecast_end` (product target 30 calendar days), `granularity=daily`, `reporting_currency`, `cash_account_scope`, optional `finance_book`, `coverage_scope`, `include_explanation`, server-generated `correlation_id`. Reject start before/at cutoff, end before start, unsupported horizon, arbitrary source/report, company/filter mismatch, unverifiable FX and malformed date. `financial_as_of` is the accounting cutoff; `retrieved_at` and `generated_at` are separate. Site runtime currently reports `Africa/Abidjan`; daily cutoff is proposed as end of site-local accounting day, but sub-day posting and backdating behavior are **NOT_VERIFIED**. Product horizon = 30 days provisional; verified future cash-date horizon on the 2026-09-26 demo site = **none**.

Output envelope:

```yaml
status: OK|PARTIAL|INSUFFICIENT_DATA|FORBIDDEN|VALIDATION_ERROR|SOURCE_ERROR|TIMEOUT|FORECAST_UNAVAILABLE|INCONSISTENT_DATA
forecast_id: string
snapshot_id: string
method_version: string
formula_version: string
company: authorized company
financial_as_of: timestamp
forecast_start: date
forecast_end: date
granularity: daily
currency: string
rounding: currency minor-unit rule
opening_cash: {data_mode: ACTUAL, status: AVAILABLE|UNAVAILABLE, value: decimal|null, evidence_refs: []}
obligations: [{id: string, obligation_type: RECEIVABLE|PAYABLE|PAYROLL|TAX|DEBT_SERVICE|RECURRING_OPEX|CAPEX|OTHER, contractual_due_date: date|null, remaining_amount: decimal, source_kind: observed|derived|synthetic|user_entered, trust_state: raw|candidate|trusted|rejected, evidence_refs: []}]
cash_events: [{id: string, obligation_id: string|null, date: date, direction: inflow|outflow, amount: decimal, data_mode: FORECAST, forecast_class: CONFIRMED_CASH_DATE|ESTIMATED_CASH_TIMING, timing_basis: CONFIRMED_CASH_DATE|VERIFIED_SCHEDULE|CONTRACTUAL_DUE_DATE|HISTORICAL_ESTIMATE|EXPLICIT_ASSUMPTION, assumption_id: string|null, evidence_refs: []}]
forecast_points: [{date: date, modeled_cash: decimal|null, status: AVAILABLE|UNAVAILABLE|ESTIMATED, included_event_ids: []}]
shortfall_events: [] # only after threshold approval; otherwise unavailable
shortfall_threshold: {status: NOT_FROZEN|FROZEN, rule: null|BELOW_ZERO|BUFFER|OPERATIONAL_MINIMUM, value: decimal|null}
assumptions: []
coverage: {scope: TRADE_ONLY|OPERATING_CORE|COMPREHENSIVE, completeness: VERIFIED|PARTIAL|UNKNOWN, included_sources: [], missing_sources: [], unverified_sources: [], excluded_categories: [], verified_data_horizon_days: integer|null}
limitations: []
explanation: {status: AVAILABLE|UNAVAILABLE, error_code: null|string, facts: [], interpretations: [], next_checks: []}
correlation_id: string
```

An obligation is not a dated cash event. A due date alone remains in `obligations`; it enters `cash_events` only under a named, approved timing rule and is then `ESTIMATED_CASH_TIMING` with `CONTRACTUAL_DUE_DATE`, never confirmed cash. A verified schedule still needs source semantics: invoice Payment Schedule on this site retains original positive amounts after settlement, so it cannot be used as remaining cash schedule without reconciliation. `CONFIRMED_CASH_DATE` requires separate evidence of committed cash timing. `data_mode`, `forecast_class`, `timing_basis`, `trust_state` and `source_kind` are independent fields. Posted history is `ACTUAL`; AI004 overlays are `SIMULATION` and excluded from the baseline. Each material number carries snapshot/method/formula versions, evidence, currency, rounding and cutoff. A combined line must reveal its components.

`coverage.completeness=VERIFIED` means all required feeds **within its named scope** were read, authorized and reconciled; it never means all business obligations exist in ERPNext. `TRADE_ONLY` includes opening cash plus trade AR/AP only and must say “scheduled cash path based on trade receivables/payables only.” `OPERATING_CORE` additionally requires payroll, tax and recurring OPEX coverage; `COMPREHENSIVE` also requires debt service, CAPEX and other material commitments. Missing or unverified categories are named even when scope is `TRADE_ONLY`. Current site cannot claim verified 30-day coverage for any scope.

## 3. Failure, thresholds and edge behavior

`OK` requires verified opening cash, authorized successful mandatory source reads, reconciled currency/book/account scope, and `coverage.completeness=VERIFIED` **for the declared scope**; it must not imply complete SME liquidity when scope is `TRADE_ONLY`. `PARTIAL` can show a bounded modeled path with prominent omissions; it must not say liquidity is safe. Missing opening cash or mandatory timing source yields `INSUFFICIENT_DATA`/`FORECAST_UNAVAILABLE`; source failure yields `SOURCE_ERROR` or `TIMEOUT`; inconsistent reconciliation yields `INCONSISTENT_DATA`. **Model timeout/malformed output/grounding failure affects only `explanation.status=UNAVAILABLE`**, with `error_code`; valid deterministic `status` remains `OK` or `PARTIAL`. `FORBIDDEN` returns no financial payload and no existence hint. Successful empty authorized report can be verified zero only after schema/coverage checks.

Negative or zero opening cash is a valid value, not an error. `SHORTFALL_THRESHOLD=NOT_FROZEN`. Candidate A: `modeled_cash < 0`; B: `modeled_cash < configured liquidity buffer`; C: available cash below approved operating minimum. Finance/Product must choose scope, threshold and overdraft treatment. Until then, no shortfall event, “LOW RISK,” “SAFE” or “HEALTHY” badge. Missing AR/AP due date, partial/advance payments, credit notes, draft/cancelled/future invoices, overdue invoices, same-day entries, duplicate/summary/mixed rows, company-specific chart, multicurrency/missing FX, period boundaries and source timeout all need explicit fixtures and runtime checks. Settlement date must never be inferred silently from posting or due date.

## 4. Security and observability

Server flow: authenticate → authorize company → authorize each allowlisted report/DocType → validate filters/date/horizon/account scope → read company-scoped sources → normalize/reconcile → deterministic forecast → optional minimized LLM explanation → numeric and evidence grounding validation → audit. Recheck authorization at evidence open; reject cross-company filter/report tampering and arbitrary resources. Escape UI/model text, treat source text as untrusted, bind cache keys to user/company/cutoff/scope/version, and discard stale responses after company switch. Do not send raw financial rows or PII to model or logs.

Emit correlation-linked events: request start, auth result, source read/result, input built, forecast computed/unavailable, assumption applied, model call/grounding result, completion. Metrics: request/status, auth denial, source failure, missing-obligation rate, latency, model latency/tokens/cost, and later forecast error. Log source identifiers/status/counts/version only; never raw rows, names, account numbers, secrets or chain-of-thought.

Current AI001 `observability.log_event` supports correlation/status, but is AI001-specific and accepts unrestricted `details`. Current invoice/payment hooks in `api/ai_insights.py` log party/customer names and amounts. AI002 must use a validated metadata allowlist and redact these hooks before claiming zero-PII telemetry; this discovery task does not alter production code.

## 4.1. Failure matrix draft

| Source result | Normalized state | Forecast status | Explanation | UX |
| --- | --- | --- | --- | --- |
| Authorized successful empty result, schema and coverage verified | `VERIFIED_ZERO` | `OK` only if all other mandatory inputs valid | Optional | Show 0 with evidence |
| Empty company without verified opening/account setup | `MISSING` | `INSUFFICIENT_DATA` | Unavailable | Missing-input checklist, no path |
| Missing due date or mandatory source | `MISSING` | `PARTIAL` for optional component; otherwise `INSUFFICIENT_DATA` | Bounded only | Omission and scope warning |
| Source exception or timeout | `SOURCE_ERROR` / `TIMEOUT` | Same typed status if mandatory | Unavailable for affected claims | Retry/source check, no invented 0 |
| Permission denied or tampered company/filter/resource | `FORBIDDEN` | `FORBIDDEN` | Unavailable | Generic denial, clear old company data |
| Duplicate/summary/mixed row unresolved, reconciliation mismatch | `INCONSISTENT_DATA` | `INCONSISTENT_DATA` | Unavailable for affected claim | No affected path |
| Currency mismatch or missing FX | `UNAVAILABLE` | `INSUFFICIENT_DATA` if needed for combined amount | Bounded only | Currency limitation, no converted total |
| Stale source or partial obligation coverage | `STALE` / `PARTIAL` | `PARTIAL` or `FORECAST_UNAVAILABLE` if no usable future dates | Bounded only | Show source age and coverage warning |
| Model timeout, malformed output or grounding failure | Deterministic result unchanged | `OK` or `PARTIAL` as computed | `UNAVAILABLE` with error code | Keep valid path, hide bad narrative |

Backdated entries require as-of replay/versioning; a later correction cannot be silently treated as data known at an earlier forecast origin. Same-day event order and site-local cutoff are pending runtime verification.

## 5. Four gates and decision

| Gate | Status | Reason to clear |
| --- | --- | --- |
| 1 Runtime | `BLOCKED` | Historical cash/AR/AP, schedule, inventory and one controlled permission case verified; present-day cash and future cash dates absent, lower-privilege matrix/cutoff precision incomplete |
| 2 Contract | `PARTIAL` | Timing and coverage semantics hardened; threshold, P0 scope, cash-account policy and verified horizon still need Finance/Product decision |
| 3 Data & Method | `BLOCKED` | Deterministic method retained; 2026 ledger opening is stale and not bank-reconciled, with no verified future cash schedule or business obligation coverage |
| 4 Security & Evaluation | `PARTIAL` | Controlled non-admin company/filter test passed; lower-privilege/evidence/cache tests, independent gold and acceptance criteria pending |

**Overall: `AI002_PARTIAL`, not `READY_FOR_AI002_IMPLEMENTATION`.** Owner next actions: Finance Product/Accounting to approve threshold and required obligation coverage; ERP runtime owner to collect sanitized live facts; Security/QA to run role and point-in-time tests; engineering to freeze contract only after those results.


