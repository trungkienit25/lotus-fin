# AI003 Risk Signal Agent — Runtime + Data Discovery

## 1. Document control

- **OBSERVED — 2026-10-01:** discovery tại HEAD `8941cfb075d91a137686bb6b666bf2bb1f7432c5`, parent `cdb99334c7e9a13986afa24facfe88d8f95ad296`. Phạm vi duy nhất: `AR_OVERDUE_SPIKE`, `AP_DUE_CLUSTER`. Không có AI003 implementation/scaffold, production edit hay ledger mutation trong task này.
- **OBSERVED:** §1–15 là authority discovery; §16–19 giữ contract reviews; **§20 là runtime recovery + METHOD GOLD mới nhất: 66/66 PASS; §21 là policy approval package hiện hành**. V2.2 được validated tại §19; numeric policy vẫn pending, contract NOT_FROZEN. Phần lịch sử bên dưới được giữ nguyên để trace; các verdict foundation BLOCKED cũ không còn là trạng thái hiện tại.
- Classification: **OBSERVED** = runtime/source/test đã đọc hoặc thực thi; **DERIVED** = kết luận có căn cứ từ evidence; **PROPOSED** = đề nghị cần Chat/Finance/Product chọn; **NOT_VERIFIED** = chưa có bằng chứng. Availability là trục riêng: AVAILABLE / PARTIAL / NOT_AVAILABLE / NOT_VERIFIED.
- Evidence chính **E1**: [sanitized runtime aggregates/schema/source excerpts](evidence/runtime_data_discovery_2026-10-01.json); collector **E2**: [read-only discovery script](evidence/runtime_data_discovery_2026-10-01.py); **E3**: [backend file alignment](evidence/runtime_backend_alignment_2026-10-01.json).
- **OBSERVED — command:** disposable `docker run --rm --read-only`, network `frappe_docker_frappe_network`, site-volume và workspace mount readonly, `PYTHONPATH=/review/lotus_fin`, Python `/home/frappe/frappe-bench/env/bin/python`, E2; output E1. Chỉ query metadata/report và public API; `frappe.db.rollback()` rồi destroy. Không xuất raw invoice/customer/supplier/account names hoặc business rows.
- **OBSERVED:** GitNexus `list`, concept `query`, `context get_ai002_cash_forecast` bind repo `lotus-fin`; index `86208f4`, 6 commits behind. Graph chỉ định hướng public path, không là safety evidence; đối chiếu trực tiếp mã hiện tại. Không chỉnh symbol production, không commit/reindex toàn graph.

## 2. Foundation baseline

**OBSERVED — inherited independent acceptance:** `FOUNDATION_VERIFIED`, `AI003_TECHNICAL_SCAFFOLD_READY` tại `8941cfb`; [51 focused tests](../../reviews/evidence/final-8941cfb-2026-10-01/focused-tests.txt), [unchanged 51-case live probe](../../reviews/evidence/final-8941cfb-2026-10-01/live-foundation-probe.json), [datetime parser/public snapshot](../../reviews/evidence/final-8941cfb-2026-10-01/due-date-types-docker.json). Không reopen các PB/R1–R5 đã đóng. Foundation acceptance không chọn business method, threshold hoặc freeze AI003.

## 3. P0 scope

**PROPOSED — semantics cần Chat chốt:** AR_OVERDUE_SPIKE phát hiện tăng mức/tỷ trọng AR quá hạn so với baseline được duyệt; AP_DUE_CLUSTER mô tả concentration nghĩa vụ AP theo contractual due-date window. Due date không phải dự báo settlement date. Chỉ hai signal này; không suy thành vỡ nợ, fraud hay cash shortfall. LLM không tính financial truth, baseline, threshold, trigger hoặc authorization.

## 4. Runtime facts

| Item | Finding / classification | Evidence |
|---|---|---|
| Declared runtime | OBSERVED: isolated `ai003-verify.localhost`; discovery chạy app source workspace readonly, không shared frontend | E1 `site`, `app_path` |
| Versions/installation | OBSERVED: Frappe 16.34.0, ERPNext 16.35.0, Lotus Fin 0.0.1; installed frappe/erpnext/lotus_fin | E1 `versions`, `installed_apps` |
| Backend alignment | OBSERVED: baked backend AR extractor hash `f04783ef…`, access guard `f419fb6f…` khớp workspace. Chỉ hai file được kiểm riêng; full-image source attestation NOT_VERIFIED | E3; discovery mounted current app code |
| Company/currency/timezone | OBSERVED: 3 companies, tất cả VND; timezone Asia/Ho_Chi_Minh, runtime date 2026-10-01 | E1 `companies`, `timezone`, `runtime_today` |
| Reports | OBSERVED AVAILABLE: standard Script Reports Accounts Receivable→Sales Invoice; Accounts Payable→Purchase Invoice; enabled | E1 `reports` |
| DocTypes | OBSERVED AVAILABLE: Sales/Purchase Invoice, Payment Schedule, Payment Ledger Entry, GL Entry, Company, Version | E1 `metadata` |
| API flags | OBSERVED: in_test=false, ai002_use_fixture_source=false; ERP reports chạy trên fixture companies, không synthetic future-event provider | E1 `test_flags` |

**OBSERVED — reusable public boundaries:**

1. `lotus_fin.api.ai_insights.get_financial_snapshot(company, period_start, period_end, currency, as_of, comparison, ...)` / public facade `ai.financial_snapshot.build_financial_snapshot`. Envelope AI001 1.0.0, formula 2026.1. Dùng typed metric status và evidence; không gọi extractors/coordinator/assembler.
2. `lotus_fin.api.ai_insights.get_ai002_cash_forecast` (re-export từ `api.cashflow_api`), `get_ai002_cash_account_scope`, `get_ai002_evidence`. JSON forecast AI002 1.2.1, STRICT_BASELINE_V1; obligations chứa type, party_type, party_hash, remaining_amount, due_date nullable, source_ref, currency. Không phụ thuộc private F002 adapters hoặc DTO nội bộ.
3. `lotus_fin.api.key_reports.extract_key_report_data` là public whitelisted report envelope: status, report_key/name, verified company, filters_applied, columns, data, total_rows, footer metadata. E1 `public_api.report_contracts` xác nhận AR 4 / AP 8 clean transaction rows. **PROPOSED, chưa approved AI003 dependency:** nếu cần fields mà AI001/AI002 không expose, Chat phải phê duyệt boundary report này với key/filter allowlist AR/AP hoặc một public typed observation boundary do foundation owner cung cấp. Không expose generic report selector cho Agent; không đọc registry private maps.

**DERIVED:** public endpoints đủ cho metric discovery; chưa có public AI003-ready normalized observation/history API với stable allocation identity. ERP report `data` là report schema theo ERPNext version, không tự coi là versioned AI003 input contract.

## 5. AR_OVERDUE_SPIKE data finding

| Required input | Availability / classification | Exact source / limit |
|---|---|---|
| Voucher/invoice identity | AVAILABLE, OBSERVED | report voucher_type + voucher_no/name; DocType name. AI001 metric envelope không expose từng invoice |
| posting_date | AVAILABLE, OBSERVED | mọi Gold AR row có; Sales Invoice Date field; AI002 obligations không expose |
| due_date | AVAILABLE, OBSERVED | Gold report 4/4 valid tại 26/09; DocType và Payment Schedule Date. Missing/malformed foundation behavior đã verified, không fabricate zero |
| outstanding_amount | AVAILABLE, OBSERVED | report field `outstanding`, current DocType `outstanding_amount`; khác semantics current vs historical report |
| currency | AVAILABLE, OBSERVED | report currency/account_currency, Company default_currency, Invoice currency; VND-only fixture |
| company | PARTIAL, OBSERVED | public report envelope/authorized filter và invoice.company có; transaction row không có company key. Phải dùng server-verified envelope, không đoán row field |
| party | AVAILABLE, OBSERVED | report party/party_type; Sales Invoice customer; AI002 chỉ party_hash |
| status | PARTIAL, OBSERVED | DocType status/docstatus có; report rows không có status. Invoice.status là current, không chứng minh historical status tại cutoff |
| as_of | AVAILABLE, OBSERVED | report_date trong filters; public AI001 as_of/period; tách observation capture time |
| Historical observations | PARTIAL, OBSERVED/DERIVED | report rerun ở 6 cutoff thành công; posting-date reconstruction theo state hiện tại. Không có chứng cứ immutable AS_KNOWN_AT snapshot series |

**OBSERVED:** E1 public AI001 tại 26/09: `ar_outstanding=565000`, `overdue_ar_ratio=0.115`, cả hai AVAILABLE; overall PARTIAL do COGS/near_term_ap không available. Không loại AR chỉ vì envelope PARTIAL; kiểm đúng metric/source coverage.

**OBSERVED:** public AI002 AR obligations 3, tổng positive remaining 575000; report có 4 rows, net 565000, một negative credit −10000. Oracle nền tảng có overdue net 65000 / positive-only 75000. **DERIVED:** AI001 net ratio và AI002 positive-only exposure không thay thế nhau. AI001 không expose exact overdue amount metric; ratio đã quantize 4 decimals. `0.115 × 565000 = 64975`, không phải exact overdue 65000; không reconstruct exact amount bằng nhân ratio.

**OBSERVED/source:** ERP report dựa Payment Ledger Entry, cutoff posting_date<=report_date, delinked=0 (E1 source context lines 844–881); invoice current outstanding không là historical balance oracle. Credits/return_against có handling riêng. **NOT_VERIFIED:** generalized cancellation/amendment replay sau backdated edits; Gold hiện có 4 cancelled SI, 2 submitted returns mỗi leg, 0 submitted amendments. Không tạo mutation mới để chứng minh.

**OBSERVED/source:** report defaults `age_as_on=Today` nếu bỏ filter; report_date controls balance, không tự đảm bảo age buckets theo cutoff (lines 57–61). **PROPOSED:** typed report boundary phải pin ageing basis Due Date + age_as_on Report Date nếu dùng buckets, show_future_payments=false; hoặc sử dụng verified due_date với accounting cutoff. Không dùng age/range buckets thiếu filter làm historical overdue facts. AI001 ratio dùng due-date/reference cutoff đã verified, không phải kết luận lỗi foundation mới.

## 6. AP_DUE_CLUSTER data finding

| Required input | Availability / classification | Exact source / limit |
|---|---|---|
| Voucher identity / supplier | AVAILABLE, OBSERVED | report voucher_type/no, party/party_type; Purchase Invoice supplier. Public AI002 source_ref + party_hash, không supplier raw |
| Due date / amount | AVAILABLE, OBSERVED | Gold AP 8/8 report dates valid; positive public obligations 7, tổng 2775000; report net 2765000 có −10000 credit |
| Currency / company | AVAILABLE envelope, OBSERVED | VND + verified company; company không nằm trong report row |
| Payment-term/schedule identity | PARTIAL schema; runtime NOT_VERIFIED | Payment Schedule child name/idx/parent tồn tại qua query, due_date/payment_amount required trong schema. ERP term SQL select invoice name, due_date, term/description; không select ps.name (lines 565–630). Public AI002 source_ref chỉ document identity |
| as_of / current obligations | AVAILABLE, OBSERVED | forecast financial_as_of 26/09; source report cutoff; dates đến 27/10 kể cả ngoài forecast_end. Window phải filter theo policy riêng |
| Historical obligations | PARTIAL, OBSERVED/DERIVED | reports tại historical cutoffs có thể rerun; không có persisted historical obligation series / known-at proof |

**DERIVED — feasible conditional computations:** với validated positive AP observations và window policy W, `due_amount(W)=sum(amount where due_date∈W)`; `share(W)=due_amount(W)/approved_AP_denominator`. Cần denominator cùng company/currency/cutoff và rule credits/overdue/today; mẫu số 0 làm undefined. Có thể thống kê monetary concentration và distinct invoice count; chưa gọi row count là installment count. Chưa chọn N, horizon, threshold hoặc floor.

**OBSERVED:** AI002 FORECAST_UNAVAILABLE / NO_CONFIRMED_SETTLEMENT_EVENTS vẫn trả authorized obligations, không có verified cash prediction. **DERIVED:** P0 AP contractual concentration không cần settlement-event source; Chat phải approve tiêu chí partial-source consumption (`obligations` validated/coverage, errors deny), không biến unavailable forecast thành BENIGN signal. Tái sử dụng AI002 endpoint đòi approved cash-account scope và opening reconciliation vốn không thiết yếu cho AP-only; scope-less typed AP boundary chỉ là PROPOSED, chưa build.

### Signal feasibility matrix

| Item | AR_OVERDUE_SPIKE | AP_DUE_CLUSTER |
|---|---|---|
| Primary source | OBSERVED: ERP AR report / PLE; SI + schedule bổ sung metadata | OBSERVED: ERP AP report / PLE; PI + schedule bổ sung metadata |
| Public contract/service usable | OBSERVED: AI001 typed AR ratio/net total; report API nếu Chat approve | OBSERVED: AI002 JSON obligations, hoặc report API nếu Chat approve |
| Required fields available | PARTIAL: exact overdue amount/row status/history không trọn vẹn trong AI001 | PARTIAL: allocation ID/status không có trong AI002 obligations |
| Historical depth | OBSERVED: non-empty records chỉ tháng 9/2026 | OBSERVED: non-empty records chỉ tháng 9/2026 |
| Identity rule | PROPOSED: company+voucher type/no+account+verified allocation identity; voucher vs installment count cần quyết định | PROPOSED: như AR; source_ref không đủ phân biệt 2 terms cùng invoice |
| Currency handling | OBSERVED: VND; NOT_VERIFIED foreign-currency scenarios | OBSERVED: VND guard; NOT_VERIFIED FX allocation scenarios |
| Missing-data risk | DERIVED: nullable due basis → INCONCLUSIVE affected evaluation, total có thể available | DERIVED: amount có mà due_date null → incomplete numerator/window coverage |
| Duplicate risk | OBSERVED regression: exact dup dedupe/conflict typed; real split identity NOT_VERIFIED | OBSERVED regression: same; không dedupe theo amount hoặc voucher-only |
| External data needed | DERIVED: NOT_REQUIRED_FOR_P0 | DERIVED: NOT_REQUIRED_FOR_P0 |
| Deterministic computation feasible | DERIVED: conditional on metric semantics/baseline policy | DERIVED: conditional on window/denominator/identity policy |
| Main blocker | PROPOSED decision required: ratio vs amount, net vs positive, comparable baseline/history | PROPOSED decision required: window/denominator/count + real allocation evidence |

## 7. Live data readiness

**OBSERVED — local fixture data, không real-business calibration evidence:**

| Company scope | Submitted SI / PI | Posting-date coverage SI / PI | Cancelled SI / PI | Multi-row invoice schedules |
|---|---|---|---|---|
| AI002 Fixture 2026 | 5 / 5 | 05–12/09 / 05–13/09/2026 | 0 / 0 | 0 / 0 |
| AI003 Gold 2026 | 6 / 10 | 01–24/09 / 01–24/09/2026 | 4 / 0 | 0 / 0 |
| AI003 Empty 2026 | 0 / 0 | no records | 0 / 0 | 0 / 0 |

**OBSERVED:** submitted invoice due-date valid rate 100% (non-empty company/leg); missing/malformed 0 in these fixtures. Gold AR/AP report at 26/09 also 4/4 and 8/8 valid dates, all VND, duplicate voucher groups=0 and exact duplicate rows=0. Gold schedule child counts AR4/AP8, Fixture AR5/AP5; none has multiple child rows per invoice. Terms-enabled reports still same totals/counts; no distinct split identity is proved. Current conflict absence chỉ là sample observation, không proof toàn bộ ERP dữ liệu sạch.

**OBSERVED:** AR/AP reports ở 31/01, 30/06, 31/08 all success-empty cho các companies; non-empty từ cutoff 20/09. Gold 20/09→26/09: net AR 650000→565000; net AP 2850000→2765000. Cutoff 30/09 có cùng net totals như 26/09. Có history kỹ thuật theo posting date, chưa có nhiều chu kỳ economic activity để đánh giá seasonality/false positives. Version track_changes metadata không chứng minh complete historical accounting snapshots.

**PROPOSED controlled fixture request — chưa thực hiện:** sau Chat chốt semantics, cần paired current/prior observations; N historical points theo baseline được duyệt; two schedules cùng invoice (different dates và same date/amount nhưng distinct child IDs), account allocation, allocated/unallocated credit, due-today/past/future boundary, missing date, duplicate/conflict, cancellation/amendment/backdated restatement, currency rejection và empty scope. Fixture phải có independent ledger oracle, giữ tổng reconciliation; không dùng synthetic results làm production calibration.

## 8. External/realtime research

**DERIVED:** REALTIME_EXTERNAL_DATA = NOT_REQUIRED_FOR_P0. Cả hai signal dùng accounting balance/due dates và approved internal baseline; thị trường, news, FX realtime hoặc peer company data không cung cấp missing internal history/permission/allocation identity. External data không thay ERPNext làm accounting truth.

| Source / retrieval 2026-10-01 | What it supports / classification | License/access; cadence; fields; integration value |
|---|---|---|
| [Official AR/AP docs](https://docs.frappe.io/erpnext/accounts-receivable-and-payable) | OBSERVED documentation: invoice/payment allocation, ageing and payment-term view; OPTIONAL_CONTEXT | Public web; page reuse license NOT_VERIFIED; refresh khi upgrade/semantics change, không realtime. Fields/concepts: voucher, due date, schedule, currency. Design reference only |
| [Official Payment Ledger docs](https://docs.frappe.io/erpnext/payment_ledger) | OBSERVED documentation: balances depend on invoice/payment matching; OPTIONAL_CONTEXT | Public web; reuse license NOT_VERIFIED; version/change-driven review. Concepts: voucher/against-voucher, account/date, allocations. No ingestion |
| [Official Immutable Ledger docs](https://docs.frappe.io/erpnext/immutable-ledger-in-erpnext) | OBSERVED documentation: cancellation uses reversals; DERIVED: ledger immutability alone does not establish known-at report replay; OPTIONAL_CONTEXT | Public web; reuse license NOT_VERIFIED; version-driven. Concepts: reversal/cancellation/backdated correction. No ingestion |
| Installed ERPNext 16.35.0 source, E1 source_excerpts | OBSERVED version-pinned report semantics, REQUIRED internal implementation evidence | Local installed source; AP header GPLv3; refresh per runtime upgrade. report_date, posting_date, delinked, currencies, terms. No copied external dataset |
| Realtime external datasets | DERIVED: NOT_NEEDED for current P0 | No crawl/credential/license/integration required; no refresh job or external fields proposed |

Documentation không thay evidence runtime phiên bản đang chạy. Không cần academic anomaly model để quyết định deterministic rule trước khi biết metric và baseline policy; chưa chọn statistical winner hoặc tạo ngưỡng.

## 9. Baseline feasibility

**PROPOSED — options cho từng signal, không chọn winner:** availability bên dưới chỉ là feasibility từ E1; không là approved rule. `N` và comparable period chưa có giá trị business.

| Option | AR data required / availability | AP data required / availability | Pros; failure modes | Minimum history / cold start |
|---|---|---|---|---|
| Previous comparable period | PARTIAL: current/prior cùng AR definition/cutoff; AI001 comparison có nhưng sampled prior 2025 success-empty, previous=0, relative_change=null | PARTIAL: same W/denominator tại 2 cutoffs; report rerun possible, không public AP historical series | Transparent; mismatch calendar/seasonality, changes/restatement, zero denominator | At least one comparable prior plus current; none/undefined prior → INCONCLUSIVE baseline, không zero-fill |
| Rolling N-period mean | PARTIAL technical reconstruction; NOT_AVAILABLE populated N-cycle sample trong inspected site | Same, cần derived AP share/amount series với consistent W | Smooth noise; sensitive outliers, autocorrelation, missing periods, zero/history drift | N complete prior comparable points theo approved cadence; dưới N → HISTORY_INSUFFICIENT |
| Rolling median | Như mean | Như mean | Less outlier-sensitive; tied/small samples, can ignore persistent shift; no automatic severity | N approved prior points; N/cadence/minimum robustness NOT_VERIFIED; không tự chọn N |
| Recent-window baseline | PARTIAL: daily/date observations reconstructed; no immutable captured series | PARTIAL: choose whether rolling date-cutoff concentration or intra-current window; distinct meanings | Responsive; weekday/payment-cycle effects, overlapping dependent observations | Full selected history window/cadence; partial history explicitly unavailable |
| Absolute threshold | AVAILABLE numeric input sau metric chọn; exact overdue amount cần public source khác ratio | AVAILABLE: due_amount(W) từ validated AP observations | No historical calculation required; company scale/materiality, credit treatment matter | 0 historical points for arithmetic; threshold approval/calibration absent → POLICY_PENDING, không trigger |
| Relative percentage change | PARTIAL: current+baseline positive/nonzero; ratio percentage-point delta là lựa chọn khác | PARTIAL: historical due_amount/share, không cùng nghĩa current intra-window share | Comparable scale; prior zero/negative/near-zero undefined/unstable; quantized ratios | At least current+valid prior; invalid denominator → typed INCONCLUSIVE/NOT_APPLICABLE theo policy |

**OBSERVED caution:** public comparison envelope AVAILABLE không bảo đảm mọi metric/relative_change available; sampled AR previous=0 và relative_change=null. Comparison ratio absolute_change đã rounding (0.12 trong sample), không nên mặc định đó là full-precision approved percentage-point input. **PROPOSED:** derive approved delta từ typed current/prior public values với explicit precision policy, hoặc request approved public exact observation boundary. Không sửa AI001 formula/contract trong task này.

**DERIVED:** AP concentration theo window tại một cutoff có thể tính không cần historical baseline; muốn đánh giá bất thường so với lịch sử thì cần thêm series và policy. Dữ liệu fixture đủ kiểm số học/failure boundaries, không đủ chọn sensitivity/threshold/false-positive targets.

## 10. Proposed typed contract

**PROPOSED ONLY — chưa freeze, chưa code:** typed SignalObservation là schema riêng AI003, không generic core/F002 DTO. Không bắt buộc LLM gửi raw filters/threshold hoặc financial values.

```yaml
SignalRequest:
  company: server_verified_requested_scope
  as_of_date: accounting_date_YYYY_MM_DD
  signal_id: AR_OVERDUE_SPIKE | AP_DUE_CLUSTER
  currency_scope: VND  # proposed supported scope, no automatic FX
  policy_version: server_resolved_approved_version
  baseline_spec: approved_type_and_dates_or_NONE
  correlation_id: tracing_only

SignalObservation:
  source_kind: AI001_METRIC | AI002_OBLIGATION | APPROVED_REPORT_OBSERVATION
  source_contract_version: required
  company: verified_envelope_scope
  currency: verified_source_currency
  as_of_date: accounting_cutoff
  captured_at: UTC_timestamp
  temporal_basis: CURRENT_STATE_RECONSTRUCTED_BY_POSTING_DATE
  voucher_type: nullable_when_aggregate
  source_id: voucher_or_report_snapshot_ref
  posting_date: nullable_with_coverage_reason
  due_date: nullable_with_coverage_reason
  outstanding_amount: decimal_string_or_null
  party_ref: authorized_opaque_ref_or_null
  source_status: typed_coverage_status
  allocation_id: verified_schedule_or_account_ref_or_null
  observation_identity: versioned_scoped_identity
  payload_hash: scope_filters_method_bound_hash
  limitations: []

SignalResult:
  signal_id: request_signal_id
  status: OK | INCONCLUSIVE | FORBIDDEN | VALIDATION_ERROR | SOURCE_ERROR | POLICY_PENDING
  finding: TRIGGERED | BENIGN | null
  observed_value: decimal_string_or_null
  unit: VND | ratio | percentage_points | count
  baseline_value: decimal_string_or_null
  baseline_spec: resolved_type_periods_comparability
  delta: decimal_string_or_null
  threshold: approved_value_unit_comparator_or_null
  triggered: boolean_or_null
  severity: approved_rule_output_or_null
  denominator: value_and_definition_or_null
  count_basis: distinct_voucher | verified_installment | null
  policy_version: approved_version_or_null
  evidence: discriminated_REPORT_SNAPSHOT_or_DOCUMENT_refs
  coverage: missing_inputs_history_identity_precision
  limitations: []
  as_of_date: accounting_date
  accounting_timezone: Asia/Ho_Chi_Minh
  generated_at: UTC_timestamp
  data_mode: LIVE | CONTROLLED_FIXTURE
```

**PROPOSED invariants:** money Decimal/decimal-string, no arbitrary float reconstruction of exact overdue amount; unknown/unauthorized ≠ benign; zero denominator explicit. Aggregate AI001 source may omit invoice fields only for aggregate method that genuinely does not need them. If installments are unsupported, make coverage/scope explicit; never fabricate allocation_id from amount/date or silently collapse allocations. AS_KNOWN_AT not offered until immutable capture/version semantics independently verified. Policy/financial values/baseline/threshold/trigger/company/auth resolved deterministically server-side; LLM cannot override.

## 11. Agent boundary

**DERIVED feasible; PROPOSED architecture, not implemented:** User → Intent Agent → Policy Gate → Typed Signal Tool → Deterministic Signal Engine → Evidence → Grounded Explanation. Reuse public AI001/AI002 envelopes with strict coverage; raw report data and descriptions remain untrusted data.

**PROPOSED minimal tools:**

- `risk_signal_evaluate`: one signal from fixed P0 allowlist, server-verified company/date/policy; deterministic output + evidence; no raw report/filter/SQL/URL or write tool.
- `risk_signal_evidence_get`: authorized discriminated evidence replay/drilldown; delegate existing public AI002 document evidence API when appropriate. AI001 report replay production endpoint remains NOT_AVAILABLE in inspected public APIs; dynamic authorized replay/hash comparison is existing harness evidence, not built service.

Optional signal list can be a fixed UI enum; separate threshold/history/admin tools are not needed for P0 intent/explanation. Explanation only cites authorized result fields/evidence, approved next checks; never upgrades INCONCLUSIVE to BENIGN or modifies trigger/severity.

## 12. Security/failure findings

| Constraint | Classification / finding | AI003 boundary implication (PROPOSED) |
|---|---|---|
| Company isolation | OBSERVED inherited live foundation pass; public key report overwrites authorized filter; current discovery Administrator proves availability only | Resolve company before query/cache; no existence/financial payload for denied scope |
| Report/DocType permission | OBSERVED authoritative checked-user Report.is_permitted; revoke cached/fresh pass in accepted live probe | Gate report and requested invoice/evidence permissions independently; never authorize target via ambient Administrator |
| Evidence reauthorization | OBSERVED public AI002 document API checks company/ref/doc permission each call; AI001 report replay endpoint NOT_AVAILABLE | Report IDs/hashes are not auth tokens; scope-bound dynamic replay can be proposed, not claimed implemented |
| Cache scope | OBSERVED F002 key user/company/cutoff/horizon/account scope/coverage/source mode+version/method+contract, TTL300, revoked entry eviction verified | AI003 cache design NOT_VERIFIED; additionally needs signal, policy, baseline, currency, identity/precision version; reauthorize before serving |
| Cross-company IDs | OBSERVED inherited live doc/evidence company denial | Reject provided foreign IDs and keep financial payload empty |
| Unsupported currency | OBSERVED F002 VND validation, invoice/report fixtures VND only; foreign-currency live semantics NOT_VERIFIED | No FX/sum mixed currency; typed unsupported currency or explicit covered-scope limitation |
| Future as_of / timezone | OBSERVED accounting timezone/date metadata; DERIVED inspected public date validators do not establish an AI003 future-date gate | Define date-only EOD/accounting cutoff, reject future as_of by policy; do not silently convert offset timestamps by local assumptions |
| Missing history | OBSERVED historical reports reconstruct; meaningful populated prior cycles absent | HISTORY_INSUFFICIENT, nullable baseline/delta/trigger; no fabricated prior=0 |
| Duplicate/conflict/allocation | OBSERVED foundation synthetic regressions pass; actual multi-term/account reconciliation NOT_VERIFIED | Use only approved public identity contract; invalid/conflict fail typed, legitimate split preserves amounts/count basis |
| Prompt injection | DERIVED report remarks/descriptions/party data untrusted; AI003 enforcement NOT_VERIFIED until implemented | Do not execute instructions in data; tool schema/allowlist/auth/policy outside model; explanation grounding/output validation |
| Partial overall response | OBSERVED AI001 PARTIAL with valid AR, AI002 FORECAST_UNAVAILABLE with obligations | Per-input/source validity, not envelope-success shortcut; denied/source-error responses must never be consumed as observations |
| Finance Book | OBSERVED F002 explicitly rejects supplied finance_book; approved APIs do not provide scoped AI003 book input | P0 scope must state unsupported Finance Book; no silently ignored filter |

These are discovery/design findings; no new foundation regression reproduced, no AI003 security implementation claimed.

## 13. Open business-policy decisions

**PROPOSED — Chat + Finance/Product must decide; existing [business policy sheet](AI003_BUSINESS_POLICY_DECISION_SHEET.md) remains PENDING:**

1. AR observed measure: net ratio vs positive-only ratio vs exact overdue amount; credit allocation/unallocated treatment and exact precision. Do not mix AI001 and AI002 denominators.
2. Comparable baseline: explicit prior date, comparable previous period, rolling mean/median/recent-window; cadence, N, minimum complete history and restatement handling.
3. AP window: N, start/end inclusion, due-today/overdue context; denominator all positive AP vs approved larger window; credit treatment.
4. Count basis: economic vouchers or verified installments; public allocation identity and source boundary approval. Unsupported schedule scope must be explicit.
5. Zero/negative denominator, floors, materiality, count minimum, threshold unit/comparator, severity and POLICY_PENDING/INCONCLUSIVE precedence; no numeric thresholds invented here.
6. Public inputs: existing aggregate/public JSON vs allowlisted report boundary vs foundation-owned public observations service; partial response acceptance, cash-scope coupling, status enrichment/replay ownership.
7. Date-only company timezone, future cutoff, currency/Finance Book scope, historical current-state vs immutable known-at, multi-source capture consistency.
8. Calibration/demo-only scope and permitted representative history; real split/credit/cancellation controlled fixture verification before asserting those input modes.

## 14. Gate status

| Gate | Verdict / classification | Rationale |
|---|---|---|
| G1 Runtime | PASS — OBSERVED, isolated declared runtime only | Current mounted source, versions/apps/timezone, AR/AP reports and public services work; backend two-file alignment confirmed |
| G2 Contract input readiness | PARTIAL — DERIVED | Public aggregate/obligation inputs work; exact amount/credit basis, historical baseline and allocation identity/public boundary approvals pending |
| G3 Data/method feasibility | PARTIAL — DERIVED | Both deterministic P0 calculations feasible conditionally; fixtures lack multi-cycle calibration and true split examples; policy not chosen |
| Foundation | VERIFIED — inherited independent acceptance | No new regression reproduced; no foundation reopen |
| AI003 contract freeze | NOT_FROZEN — OBSERVED process state | Discovery completed, Chat/Finance/Product decisions remain pending |

## 15. Recommended next action

**PROPOSED:** ChatGPT Chat chooses signal semantics and public input boundary from this evidence, resolves §13, issues the proposed typed contract with explicit supported data modes and cold-start behavior. Commission only the missing controlled fixtures/history evidence for the selected method. No AI003 code/scaffold or production threshold until the appropriate contract/policy gate is approved.

```text
G1 RUNTIME: PASS
G2 CONTRACT INPUT READINESS: PARTIAL
G3 DATA/METHOD FEASIBILITY: PARTIAL

REALTIME_EXTERNAL_DATA: NOT_REQUIRED_FOR_P0

OPEN DECISIONS:
- AR measure/credits/precision and baseline/cold-start policy.
- AP window/denominator/count and allocation identity evidence.
- Approved public observation/history/evidence boundary.
- Materiality/threshold/severity, date/currency scope and calibration policy.

CURRENT VERDICT: DISCOVERY_COMPLETE_CONTRACT_DECISIONS_PENDING
NEXT OWNER: ChatGPT Chat
NEXT ACTION: finalize AI003 signal semantics + contract
```

---

## 16. Independent contract validation — 2026-10-01

### 16.1 Review decision and scope

**OBSERVED:** reviewed toàn bộ attachment `1e13c416-96a6-4842-aab5-62d24ff7a5be/Pasted text.txt` (“AI003 — CONTRACT DRAFT DECISION”), HEAD vẫn `8941cfb`. User authorize validate + freeze; không yêu cầu foundation reopen hoặc production implementation. Không sửa production, không gán threshold/cadence/window thay Finance/Product.

**DERIVED verdict:** direction đúng và public source feasibility PASS; **draft không thể freeze nguyên trạng** vì execution/schema/identity chưa nhất quán, policy resolver còn thiếu nghĩa xác định, và G3 trong chính draft vẫn PARTIAL. Bản technical correction candidate tại §16.4–16.8 là nội dung reviewable cụ thể; không tự đổi trạng thái thành AI003_CONTRACT_FROZEN hoặc giả lập policy approval.

**OBSERVED process requirement:** [workflow v3 Phase 9](../LOTUS_FIN_AI_FEATURE_BUILD_WORKFLOW_3_TOOLS_V3_VI.md) ghi “Chỉ freeze khi” G1 Runtime PASS, G2 Contract PASS, G3 Data/Method PASS, G4A Pre-build Security/Eval PASS. User yêu cầu freeze trao quyền thực hiện freeze khi đạt điều kiện, không cung cấp các giá trị policy hoặc evidence chưa có. Có thể freeze schema tham số hóa với POLICY_PENDING theo một phạm vi technical-only được xác định riêng; đó không tự động là full contract freeze theo bốn gate này.

### 16.2 Fresh public-boundary verification

**OBSERVED — read-only isolated runtime:** [collector](evidence/contract_boundary_validation_2026-10-01.py), [sanitized results](evidence/contract_boundary_validation_2026-10-01.json). Cùng Docker/read-only setup §1; rollback cuối probe. Chỉ public AI001 snapshots, public key report và authorized DocType metadata reads; không AI003 engine/internal source dependency.

| Check | Result / evidence |
|---|---|
| AR current + explicit prior cutoff | PASS: AI001 1.0.0 / formula 2026.1; 20/09 total 650000, ratio 0; 26/09 total 565000, ratio .115; cả hai metrics AVAILABLE |
| AR PP arithmetic | DERIVED independent oracle: (.115−0)×100 = **11.500 percentage points**; không dùng rounded comparison.absolute_change, không tái tính AR financial formula |
| Baseline ratio zero | PASS for this input: prior denominator 650000>0 nên ratio zero là valid observation, không tự coi HISTORY_INSUFFICIENT |
| AP fixed report | PASS literal `accounts_payable`, 8 clean rows, 7 positive observations, positive total 2775000, 7 distinct vouchers; exact filter recipe §16.5 |
| Company provenance | OBSERVED: 8/8 AP transaction rows không có company; envelope/authorized filter là nguồn company |
| AP account key | OBSERVED: report field `party_account`; draft `account` cần explicit normalization, không assume raw key tồn tại |
| Schedule metadata read | OBSERVED: positive invoice docs readable under Administrator; no multi-schedule vouchers in sample. Restricted-user access for new AI003 metadata bridge NOT_VERIFIED; must fail FORBIDDEN on denial |
| Policy/gold closure | NOT_VERIFIED: no approved W/cadence/threshold/floors; fixture pair demonstrates arithmetic/input feasibility, not complete AI003 gold acceptance or production calibration |

Snapshot envelope PARTIAL do unrelated metrics không ngăn dùng AR typed metrics AVAILABLE. Public input approval trong Chat draft giải quyết discovery boundary choice cho AR/AP; không cho phép AI003 đọc private extractors/assembler/coordinator/registry maps/F002 adapters.

### 16.3 Exact draft findings

| ID | Priority | Finding / consequence | Smallest closure |
|---|---|---|---|
| CV-01 | P1 | Trigger pseudo-code checks policy before data. Missing policy can mask malformed data/history as POLICY_PENDING; auth precedence not explicit. Conflicts with typed failures and no-payload security requirement | Use one ordered state machine §16.4; authorization/request/source validity precede policy |
| CV-02 | P1 | Failure table relies on reason codes absent from SignalResult; LLM failure relies on explanation absent from schema; unsupported allocation cannot be represented specifically; draft version/method literals not final | Add reason_code/explanation/strict nullability, complete result-state invariants and stable version IDs before freeze |
| CV-03 | P1 | PREVIOUS_COMPARABLE_CUTOFF has no specified deterministic resolution; comparison_policy empty; input omits baseline date | Require immutable approved resolver specification, cutoff strictly before current, same definition/scope/version; no hidden fallback or default year |
| CV-04 | P1 | Report key shown as ACCOUNTS_PAYABLE differs from actual literal `accounts_payable`; unspecified filters can permit currency/ageing/payment-term drift | Literal and exact server filters §16.5; unknown client keys rejected |
| CV-05 | P1 | `based_on_payment_terms=0` report alone cannot prove invoice has only one payment schedule. Disabling installment claim does not stop assigning multi-term balance to one header due_date | Approved read-permission-gated invoice/schedule metadata bridge; >1 schedule or ambiguous scope → UNSUPPORTED_ALLOCATION_SCOPE; prove guard with controlled fixture before PASS |
| CV-06 | P1 | Canonical identity includes account/currency but count is DISTINCT_VOUCHER; two accounts can inflate count. Duplicate schema has no full-content equivalence/reconciliation rule | Separate observation identity from economic voucher identity; do not sum conflicts or collapse proven allocations silently |
| CV-07 | P1 | FORBIDDEN financial-payload shape, evidence-get signature/storage/replay/hash behavior, and unknown policy/source-state nullability are not defined | Explicit minimal denial envelope; define evidence protocol §16.7 and result schema §16.6 |
| CV-08 | P2 | Inclusive [as_of, as_of+W] spans W+1 accounting dates; may be interpreted as W-day window. HIGH>=WATCH allows WATCH unreachable at equality; precision/range rules incomplete | Define W as calendar-day offset, not length; explicit policy constraints/precedence, decimal precision and boundary tests |
| CV-09 | P1 freeze gate | Policy numbers and cadence unapproved; draft lists gold cases but no execution/source manifest for complete selected AI003 method. Calibration alone cannot confer Finance/Product approval | Resolve policy approval/scope and complete method-specific independent gold; do not record G3 PASS from foundation counts |

Materiality definition itself is accepted as a draft business choice: AR M_AR gates **current net total AR**, not exact overdue amount; AP M_AP_DUE gates due_amount_W. Rename/label accordingly to avoid UI claiming an overdue-money materiality floor for AR. AR net ratio may be negative or outside 0..1 because of credits; never clamp/rewrite AI001 facts. AP positive-only ratio must be within 0..1 after valid aggregation.

### 16.4 Technical correction candidate — ordered evaluation

**PROPOSED complete candidate, no policy value chosen:**

1. Authenticate → server verify requested company → authorize approved reports/current+baseline resources and requested document metadata/evidence. Any denied/unknown scope → FORBIDDEN with generic reason, no financial/identity payload.
2. Validate strict date-only request, future-date rejection in company accounting timezone, fixed signal enum, extra-key rejection. Client cannot supply currency/Finance Book/policy/baseline/filters/financial values; explicitly supplied unsupported keys are rejected, not ignored.
3. Read current sources; validate envelope success, verified company/currency/cutoff/version and required typed fields. Error/timeout/malformed/conflict → SOURCE_ERROR with sanitized reason; missing due-date or unsupported allocation coverage → INCONCLUSIVE. Exact duplicate validation/dedupe precedes monetary aggregation. No zero-fill.
4. Resolve applicable policy metadata server-side. If absent/pending and valid current inputs exist, POLICY_PENDING; missing comparison/W is reported as pending policy, not fabricated history/window. A failure already established in steps 1–3 is never replaced by POLICY_PENDING.
5. With approved complete policy, resolve baseline or AP window. AR verify baseline source, comparability and denominator; missing valid history → HISTORY_INSUFFICIENT; explicit zero/nonpositive denominator → INVALID_DENOMINATOR. A prior ratio 0 with valid positive denominator is allowed. AP positive total=0 → ZERO_DENOMINATOR even if due numerator is zero. Missing/invalid inputs never become BENIGN.
6. Apply declared current-AR-total or AP-due-amount materiality floor with strict `<`; exactly equal floor remains eligible. Then HIGH first with `>=`, WATCH next with `>=`, else BENIGN. Only successful deterministic evaluation has status OK; triggered true for TRIGGERED, false for BENIGN.
7. Optional grounded explanation; provider failure/invalid output changes explanation only, never numeric/result state. Audit source/method/policy versions and correlation, then serialize strict envelope.

Policy validity: immutable approved record includes version, effective scope/date/data_mode, approver/date, validation evidence, finite decimal constants, comparator, precision, baseline resolver or W. Calibration supports approval; it does **not** automatically approve policy. HIGH>WATCH recommended when both bands must be reachable; equality may only be explicitly approved as HIGH-only effective behavior. AP thresholds in [0,1], AR PP thresholds nonnegative, materiality>=0; W integer>=0 with approved maximum. No default/unapproved constants, bool-as-int, NaN/Infinity, implicit FX or model-supplied overrides. Invalid active configuration → SOURCE_ERROR/INVALID_POLICY_CONFIG rather than silently POLICY_PENDING.

AR baseline resolver must be a total deterministic policy specification (calendar/cadence/alignment/leap/end-of-month rules) yielding baseline_cutoff<as_of or HISTORY_INSUFFICIENT; contract cannot freeze the phrase “comparable” without that definition. Adapter invokes public AI001 **twice with explicit dates/periods**, extracts typed values with `Decimal(str(public_value))`, requires contract1.0.0/formula2026.1 and same company/VND/evidence cutoff. Do not use public endpoint defaults 2020 or comparison rounded delta. PP output computed from published 4-decimal ratio precision, convention documented; no extra precision or exact-overdue-amount claim.

### 16.5 Technical correction candidate — AP scope and identity

**PROPOSED fixed public recipe (fresh probe PASS):**

```yaml
boundary: lotus_fin.api.key_reports.extract_key_report_data
report_key: accounts_payable
filters:
  company: server_verified_company
  report_date: as_of_date
  based_on_payment_terms: 0
  in_party_currency: 0
  show_future_payments: 0
  ageing_based_on: Due Date
  age_as_on: Report Date
```

Adapter validates response status/company/filters/transaction shape, footer separation, allowed voucher/party legs, finite parseable amounts and currency/account provenance before selecting amount>0. Negative credits excluded from numerator and denominator but their source scope/identity cannot bypass source validation; ignored-credit totals/counts are limitations/context, not netted into exposure. Valid nonpositive rows do not require future due-date coverage to evaluate positive AP. For every positive row, due_date must be valid date and belongs to verified observation cutoff.

Identity candidate:

```text
economic_voucher_identity = (company, voucher_type, voucher_no)
observation_identity = (economic_voucher_identity, party_account, currency)
count_basis = cardinality of economic_voucher_identity in eligible observations
```

Canonicalization must preserve original typed fields/sign/date/IDs; no whitespace/case folding that merges distinct IDs. Exact duplicate means same normalized economic/account/currency identity and all relevant content; malformed rows rejected before dedupe. Same observation identity with conflicting amount/due/party/type → SOURCE_ERROR/INCONSISTENT_DATA. Multiple account observations may contribute only with verified account allocation provenance; otherwise INCONCLUSIVE/UNSUPPORTED_ALLOCATION_SCOPE, not voucher-only dedupe.

**Additional source approval required for the candidate:** permission-checked ERPNext invoice/schedule metadata via stable Frappe DocType read interfaces, fixed allowed DocTypes, no generic selector. Need voucher company/party/account/currency, submitted state, payment_schedule cardinality. Report-access grant alone cannot grant invoice read permission; deny metadata read → FORBIDDEN. Positive invoice with >1 schedule is unsupported P0 even if the report flattened it into one row. Empty schedule with validated invoice-level due-date may be supported only under explicitly approved fallback; one schedule/header-date discrepancy must be resolved or coverage inconclusive. Non-invoice payable vouchers require their own approved contractual-date provenance or explicit unsupported-scope result. No invented allocation ID from amount/date, no installment claims.

Window candidate stays Chat's `[as_of, as_of+W]` inclusive; W is an offset, W=0 means due-today only. Already overdue is excluded from numerator but remains in **all-positive AP** denominator. Same for positive AP after window-end. Count published with explicit whether all-positive or in-window; return both count_positive_vouchers and count_due_vouchers if counts are exposed. Payment term/account splits never inflate distinct voucher count.

### 16.6 Technical correction candidate — minimum wire schema additions

Keep Chat's SignalRequest/Result shape, add these normative fields/constraints before freeze; actual version IDs must be chosen explicitly, not `draft` wire values:

```yaml
SignalRequest:
  additional_properties: false
  company: nonempty_string
  signal_id: AR_OVERDUE_SPIKE | AP_DUE_CLUSTER
  as_of_date: strict_YYYY_MM_DD
  correlation_id: optional_bounded_string  # metadata only; tool may omit

SignalResult_additions:
  reason_code: typed_enum_or_null
  source_refs:
    - kind: AI001_METRIC | ERP_AP_REPORT | ERP_DOCUMENT_METADATA
      contract_version: string_or_null
      formula_version: string_or_null
      source_schema_version: string_or_null
      cutoff: date
      captured_at: UTC_timestamp
  baseline:
    type: PREVIOUS_COMPARABLE_CUTOFF | NONE
    value: decimal_string_or_null
    denominator: decimal_string_or_null
    cutoff: date_or_null
    status: AVAILABLE | HISTORY_INSUFFICIENT | NOT_APPLICABLE | UNAVAILABLE
    resolver_version: string_or_null
  observed:
    value: decimal_string_or_null  # current AR ratio or AP due_share
    unit: ratio
    supporting_amount: decimal_string_or_null  # AR net total / AP due_amount_W
    supporting_amount_definition: CURRENT_NET_AR_TOTAL | AP_DUE_WINDOW_AMOUNT
  rule_additions:
    threshold_unit: percentage_points | ratio
    materiality_unit: VND
    materiality_definition: CURRENT_NET_AR_TOTAL | AP_DUE_WINDOW_AMOUNT
    window_start: date_or_null
    window_end: date_or_null
  explanation:
    status: NOT_REQUESTED | AVAILABLE | UNAVAILABLE
    text: string_or_null
    reason_code: sanitized_string_or_null
  temporal_basis: CURRENT_STATE_RECONSTRUCTED_BY_POSTING_DATE
```

Reason-code set must include at least UNAUTHORIZED_ACCESS, INVALID_REQUEST, FUTURE_AS_OF, UNSUPPORTED_CURRENCY, FINANCE_BOOK_NOT_SUPPORTED, HISTORY_INSUFFICIENT, INVALID_DENOMINATOR, ZERO_DENOMINATOR, INCOMPLETE_DUE_DATE_COVERAGE, UNSUPPORTED_ALLOCATION_SCOPE, INCONSISTENT_DATA, SOURCE_UNAVAILABLE, SOURCE_TIMEOUT, POLICY_UNAVAILABLE, INVALID_POLICY_CONFIG, UNSUPPORTED_SOURCE_VERSION. `INCONSISTENT_DATA` is a reason under SOURCE_ERROR, not an extra status accidentally outside enum. AP baseline NONE→value/cutoff null, NOT_APPLICABLE; delta null. AR baseline invalid→all dependent delta/trigger values null. No denominator=0 ratio fabricated.

Serialization invariants: status!=OK → finding/triggered/severity null; OK+TRIGGERED→true+WATCH/HIGH; OK+BENIGN→false+null. FORBIDDEN returns only generic status/reason/request correlation/generated_at/contract metadata; omit verified company, numeric fields, source/evidence/ref/hash/coverage resource IDs and explanation text. Auth failure has precedence over any source/policy/history outcome. Partial valid metrics may be returned for non-auth failure only with explicit coverage and null evaluation; no exposed raw exceptions/remarks/PII.

`data_mode` distinguishes real ERP storage from fixture business scope. Calling actual ERP reports on known controlled fixture companies remains CONTROLLED_FIXTURE for AI003 evidence; it is not production calibration merely because Frappe test flags are false. Mode is server-controlled, never a user-selectable bypass.

### 16.7 Technical correction candidate — evidence, cache and Agent

Two tool signatures must be fully explicit: evaluate(company, signal_id, as_of_date; optional correlation metadata), evidence_get(company, opaque_ref; optional correlation metadata). Client company is a requested scope, never authoritative; server derives authorization. Allowlisted DocTypes/reports only; policy/threshold/baseline/financial fields cannot be passed by model.

Evidence record must bind verified company, owner/access scope, accounting date, source filters/version/method and captured_at/hash; report refs must be resolvable by the proposed evidence service, not arbitrary generated IDs with no backing record. Current public AI001 report evidence has no completed evidence replay endpoint: AI003 must specify authorized report reconstruction with saved scope/hash comparison and MATCH/RESTATED/UNAVAILABLE/FORBIDDEN behavior or another approved resolvable design. No immutable known-at claim. Report and current document permissions rechecked on access; cross-company/denied result generic, ref/hash not an auth token. Evidence retrieval does not retroactively change deterministic result or pretend a changed report hash MATCH.

If caching is enabled later, Chat's key axes retained; add policy effective scope/version and all normalization/window/resolver/source schema versions, authorization before cache use, revoked/invalid scope evicted. Fresh permission does not establish data freshness: declare TTL/source-restatement policy; no indefinite cache. Simplest candidate is cache disabled until that policy is explicit. No chosen TTL invented.

Prompt injection: descriptions/remarks/raw business strings are data only; don't place them into tool/system instructions. Tools read-only, schema allowlisted, deterministic engine and policy gate outside model. Grounded explanation validates cited evidence/values and approved next-check IDs. LLM failure or unsupported claims only suppress explanation. Observability requires lifecycle/request/auth/source/evaluation/evidence/explanation outcomes, correlation/source/method/policy versions, no sensitive rows or raw exception text.

### 16.8 Gold closure checklist and freeze decision

**PROPOSED minimum missing independent gold beyond inherited foundation evidence:**

- AR: the freshly observed 0→.115 pair with positive denominators and PP11.5; current/prior AR denominator zero separately; ratio zero valid with positive prior total; prior missing vs empty; precision at WATCH/HIGH ±one declared quantum; both materiality equality/below; net credit semantics; identical company/currency/formula cutoff proof; future/backdated/restated coverage.
- AP: due-today, due-end, day-after-end, overdue excluded numerator but included denominator; negative-credit exclusion, zero all-positive total; missing due on positive vs nonpositive row; exact duplicate/conflict; two accounts same voucher count=1 with unsupported/proven provenance cases; multi-schedule invoice flattened in default report still rejected; schedule/header disagreement; currency/party/cross-leg/company guards.
- Security/failure: unauth/company/report/doc/evidence denial **with policy missing**; source error/missing date **with policy missing**; missing/invalid/expired/wrong-data-mode policy; cache revoke/freshness if cache used; evidence RESTATED/UNAVAILABLE; unexpected client fields; timezone midnight/future-date; LLM failures/injection leave evaluated result unchanged.

No arbitrary numerical production thresholds/W are selected. Fixture tests may use explicitly TEST_ONLY symbolic/boundary policies but need independent manifest (source hashes, dates/currency, exact decimals, policy identity, expected status/finding/severity/evidence). Calibration evidence supports Finance/Product review; does not itself record business approval. Mock schema/guard tests must be labelled and not replace live-source or restricted-user evidence. New ledger fixtures are not created during this contract review.

| Gate | Independent result now | What remains |
|---|---|---|
| G1 Runtime | PASS, inherited + fresh public reads | Isolated declared runtime only |
| G2 Contract | PARTIAL for supplied draft | Integrate/approve precise corrections §16.4–16.7, stable wire versions, baseline resolver and additional metadata boundary |
| G3 Data/Method | PARTIAL | Approved policy/cadence/W/scope, method-specific independent gold; no false claim from fixture arithmetic alone |
| G4A Pre-build Security/Eval | PARTIAL for supplied draft | Ordered failures/output/schema/evidence protocol corrections + selected guard/evaluation evidence; no AI003 implementation PASS claimed |
| Foundation | VERIFIED | No new foundation blocker found |
| Full AI003 contract freeze | **NOT_FROZEN** | Four mandatory gates are not all PASS |

**CURRENT VERDICT: AI003_CONTRACT_REVIEWED_CHANGES_REQUIRED.** Bản sửa technical candidate đã cụ thể; không chỉ trả lại một lời yêu cầu approval. Next owner ChatGPT Chat + Finance/Product: integrate technical corrections, choose/version/approve the pending comparison/window/policy scope and values, authorize missing controlled gold/metadata guard validation. Work verifies those exact closures; then records AI003_CONTRACT_FROZEN when the requested full freeze is justified. Technical-only schema freeze with all evaluation disabled POLICY_PENDING needs its scope stated explicitly and cannot be advertised as production full freeze.

## 17. Contract Draft V2 / candidate v0.3 — targeted validation

### 17.1 Authority, evidence and scope

**OBSERVED:** reviewed toàn bộ attachment `8e1bfb92-c3e2-498a-8fe3-42d32df9bd2f/Pasted text.txt`, including §§25–32/schema/registry riêng để tránh truncation. Không discovery/retest repo/runtime, không AI003 code, không production edit, không chọn thresholds. Dùng lại [public-boundary evidence](evidence/contract_boundary_validation_2026-10-01.json), [collector thể hiện permission check](evidence/contract_boundary_validation_2026-10-01.py), [runtime report/DocType metadata](evidence/runtime_data_discovery_2026-10-01.json) và foundation acceptance §2. V1 full-freeze conditions không được áp nhầm lên V2 **design-only** verdict.

**DERIVED:** baseline previous-month same-day + month-end clamp và AP D0..D30/future-positive denominator là CONTRACT_DECISION mới, không cần numeric risk thresholds để validate feasibility. Numeric policy pending và gold chưa chạy không tự làm design FAIL. Chỉ các inconsistency/precision gap dưới đây ngăn unconditional V2 design acceptance.

### 17.2 Delta verdicts

| Area | Verdict | Evidence / exact limit |
|---|---|---|
| V2 schema | CHANGES_REQUIRED, narrowly | Reason registry/status/result nullability/finding/trigger/severity/explanation generally consistent. Currency-conflict predicate §22 contradicts currency being in observation identity §19; see V2-01 |
| V2 precedence | PASS design | §§10/24/32: syntax→auth/company→scope→permission/read→integrity/identity→method prerequisites→policy→rule→explanation. No history/invalid source/coverage failure may become POLICY_PENDING |
| AR method | IMPLEMENTABLE / READY_FOR_GOLD | Approved public AI001 twice with explicit dates, typed statuses/company/currency/version; own Decimal PP arithmetic, no rounded comparison block. New same-month cadence still needs its own fixture; old 20/09→26/09 oracle is not monthly-baseline proof |
| AP method | IMPLEMENTABLE; precision closure required | Public report has voucher_type/no, party_account, outstanding, due_date, currency and authorized company envelope. New numerator/denominator filters implementable; six pending constants unchanged. AP ratio rounding/rule-comparison semantics not specified; see V2-02 |
| Multi-schedule boundary | PASS implementability; gold NOT_RUN | Stable Frappe parent-document read + explicit checked-user permission, company check, payment_schedule length; no allocation IDs needed. Prior metadata read evidence is Administrator-only; restricted-user/new >1-schedule guard still needs gold/security proof |
| Method gold plan | FEASIBLE; READY_TO_PREPARE after V2-02 precision rule | Transaction-backed fixtures + independent ledger/report oracle can prove methods without AI003 engine import; minimum additions §17.5 |
| G4A design | CHANGES_REQUIRED, evaluation-plan consistency only | Security boundary is implementable: no dedicated cache, scope/currency/date gates, resource reauthorization, LLM cannot change result. Policy gold requires between-WATCH/HIGH cases while invariants allow equal thresholds; see V2-03 |

### 17.3 Only exact changes required

**V2-01 — identity/conflict contradiction (§19 vs §22).** Observation identity contains currency. Two rows with different currencies therefore cannot have the same observation identity; §22 cannot detect that difference by its stated same-identity predicate. P0 VND gate prevents mixed-currency evaluation if consistently enforced, so this is not evidence of a runtime leak. Smallest change: state currency mismatch is validated/rejected **before** full identity/dedup; reserve same-identity conflict for amount/date/party/other payload fields not in that key. If same voucher/account has incompatible financial currency semantics, reject rather than treating it as a second legitimate allocation. Keep count_key separate; no amount/date-derived identity.

**V2-02 — AP precision and threshold comparison unspecified (§15/25).** `due_share=N/D` can be repeating; declaring Decimal and saying method_version controls precision does not define a wire value/rounding or the value evaluated by GTE. Different legal Decimal contexts or output quantization can give different boundary decisions. Smallest change: specify ratio output precision/rounding and whether evaluation uses rounded or exact underlying share. A safe candidate is exact comparison `N >= T × D` (finite Decimal money/thresholds) with separately rounded display share; alternatively choose one explicit quantization/rounding before both evaluation and serialization. This is method precision, **not** choosing any of the six thresholds. Independent gold must retain exact N/D and test a non-terminating share plus boundary behavior. AR use `Decimal(str(published_AI001_ratio))`; PP from published 4-decimal ratio precision, not reconstructed exact ledger precision.

**V2-03 — policy-gold reachability contradiction (§11/24 vs §51).** V2 allows HIGH==WATCH and evaluates HIGH first, but requires a between-WATCH/HIGH policy-gold case. There is no between interval or reachable WATCH band at equality. Similarly materiality floor0 has no valid below-floor nonnegative AP due amount / positive AR denominator; AP WATCH0 has no valid below-WATCH nonnegative share. Smallest change preserving selected invariants: make gold cases conditional on mathematical reachability under the approved policy/input domain; record impossible cases NOT_APPLICABLE with rationale, never manufacture invalid financial values. Explicitly test equality→HIGH and absent WATCH band when HIGH==WATCH. Do not force strict inequality/positive floors or select actual values on Finance's behalf. If Chat instead intends both severity bands always reachable, tighten both policy invariants to HIGH>WATCH explicitly.

These are the only gate changes requested here; do not reopen resolved V1 findings or redesign valid V2 source/state/security choices. Implementation bindings below make the existing conceptual boundaries concrete, not new signals/methods.

### 17.4 Exact safe public call and metadata paths

**AR — DERIVED implementable path:**

1. Resolve checked user from authenticated server session; authorize requested company and Accounts Receivable resource. Derive baseline month via calendar arithmetic, clamp to last day; include January→previous December and leap-year cases.
2. For each cutoff C (current or baseline), call `lotus_fin.api.ai_insights.get_financial_snapshot(company=verified_company, period_start=C.year+'-01-01', period_end=C.isoformat(), as_of=C.isoformat(), currency='VND', comparison=None, include_explanation=False)` in checked-user context. Explicit periods avoid endpoint's 2020 defaults. Dates/version parameters are server-controlled.
3. Extract only ar_outstanding + overdue_ar_ratio and their statuses/evidence. Require same verified company/VND, AI0011.0.0/formula2026.1, evidence cutoff C, finite values. Global PARTIAL may be acceptable when these inputs are AVAILABLE; FORBIDDEN/SOURCE_ERROR never become partial financial facts.
4. Convert published values through decimal text, compute `(current_ratio−baseline_ratio)*100`. Never use comparison.absolute_change/relative_change, raw_sources injection, internal extractor/assembler/coordinator or private maps.
5. Success-empty prior with verified denominator0 is BASELINE_DENOMINATOR_INVALID; absence of a valid prior observation is HISTORY_INSUFFICIENT; genuine source error remains SOURCE_ERROR. Prior ratio0 with positive denominator is valid. Negative/out-of-range net ratio is not automatically clamped; inherit AI001 semantics.

**AP — DERIVED implementable path:** use literal `accounts_payable` (map conceptual ACCOUNTS_PAYABLE to this exact public key), server-owned filters already verified in §16.5: company, report_date, based_on_payment_terms=0, in_party_currency=0, show_future_payments=0, Due Date ageing, Report Date age_as_on. Normalize raw `outstanding`→outstanding_amount and `party_account`→verified account scope. Company comes from authorized envelope, not absent row company field. Validate source before positive/future selection. Once normalized: eligible amount>0 with valid due_date>=as_of; numerator eligible due<=as_of+30. D31/long-dated positive included in denominator only; past-due and credits excluded from both/count. The old observed total2775000 is **all positive AP**, not asserted as V2 future-eligible denominator; recompute oracle under new definition.

**Mandatory schedule preflight — DERIVED safe design, no new runtime PASS claimed:** fixed supported DocType map, never `get_doc(untrusted_voucher_type, ...)` with arbitrary source type. For every unique voucher required by the report result (not only the numerator window), use parent `frappe.get_doc('Purchase Invoice', voucher_no)` for the supported PI type in trusted checked-user context; explicitly `doc.has_permission('read', user=checked_user)` or equivalent checked-user document permission gate. `get_doc` alone is not authorization. After authorization verify doc.company==verified company and report/header/single-child date consistency; derive count from `doc.payment_schedule`. Parent-authorized child metadata only, no `get_all('Payment Schedule')` permission bypass and no child-ID-as-token.

0/1 schedule potentially supported subject to date/source consistency; >1 → INCONCLUSIVE/UNSUPPORTED_MULTI_SCHEDULE, all finding/trigger/severity null. Metadata permission denial → FORBIDDEN/result null. Non-Purchase-Invoice source voucher must be rejected as unsupported P0 allocation scope unless separately approved; do not assume its nonexistent schedule table means a supported zero-schedule invoice. Zero-schedule fallback uses verified invoice/report due date, never fabricated due today. Any ambient-user switching, if required, is server-only try/finally restore; never accept client user.

The metadata bridge needs no stable installment identity because P0 rejects multiple schedules. Observation and count keys remain distinct; multiple account observations without proved supported allocation remain INCONCLUSIVE, not summed or collapsed by voucher count_key.

### 17.5 Smallest method-gold additions

**PROPOSED plan only; no fixtures created:** reuse foundation gold/guards, preserve existing protected Gold company/source hashes. Add a separate controlled scope for the new method, and source perturbation harness where malformed ledger records cannot legitimately be created. Oracle cannot import AI003 engine/provider normalization being tested.

- **AR monthly pair:** populated baseline and current cutoffs separated by the V2 exact calendar-month rule; the existing 20/09→26/09 pair is insufficient. Lock voucher/PLE facts and credit semantics; independently calculate exact net totals/overdue and AI001-published 4-decimal ratio quantization, then PP. Include positive/zero/negative change by controlled variants, prior success-empty/zero denominator vs unavailable observation, current zero, future posting and documented restatement. Calendar-only cases: March31→February28/29, January→December. Failure/corrupt/conflict/missing-baseline responses can use labelled source-envelope perturbations; not fabricated transaction truth.
- **AP boundaries:** same authorized fixture cutoff with positive PI vouchers due D0, D30, D31 (also long-dated), one past-due, one negative credit. Oracle independently stores future-positive denominator, D0..D30 numerator, exact fraction, both distinct voucher counts and exclusions. Include a non-terminating share to verify V2-02; no risk threshold is selected.
- **AP schedule guard:** one parent with two Payment Schedule children, exercised with default report terms-disabled so a flattened single row cannot evade preflight; include 0/1 supported cases and one-child/report due-date disagreement. Repeat metadata access under allowed/denied checked user and cross-company reference. No invented allocation IDs.
- **AP source perturbations:** exact duplicate, same identity conflicting amount/date, missing/malformed positive due date, same voucher multiple unproved account observations, currency/identity mismatch. Label controlled row mutation distinct from real ERP output. Cases verify source/method failure wins even when policy absent.

Independent manifest: fixture scope, locked source hashes, cutoff/baseline, company/currency, upstream+method/identity versions, exact monetary/ratio operands and precision, expected status/reason/nullability, evidence provenance. Method gold expects POLICY_PENDING only when all method prerequisites pass; risk finding/severity remain null until approved policy. Policy gold is later, includes V2-03 degenerate-threshold behavior. No six risk values invented for method gold.

### 17.6 Design gates and handoff

```yaml
V2 SCHEMA: CHANGES_REQUIRED # V2-01
V2 PRECEDENCE: PASS
AR METHOD: READY_FOR_GOLD
AP METHOD: CHANGES_REQUIRED # precision only, source boundary implementable
MULTI-SCHEDULE BOUNDARY: PASS_IMPLEMENTABILITY # live guard proof pending gold
METHOD GOLD PLAN: FEASIBLE
G4A DESIGN: CHANGES_REQUIRED # V2-03 policy-gold consistency

G2 CONTRACT: CHANGES_REQUIRED
G3 METHOD DESIGN: CHANGES_REQUIRED
G4A SECURITY/EVAL DESIGN: CHANGES_REQUIRED

POLICY VALUES STILL PENDING:
  - AR_MATERIALITY_FLOOR_VND
  - AR_WATCH_DELTA_PP
  - AR_HIGH_DELTA_PP
  - AP_DUE_MATERIALITY_FLOOR_VND
  - AP_WATCH_DUE_SHARE
  - AP_HIGH_DUE_SHARE

CURRENT VERDICT: CONTRACT_V2_CHANGES_REQUIRED
CONTRACT FREEZE: NOT_FROZEN
NEXT OWNER: ChatGPT Chat
```

No foundation regression claimed. Three narrow document clarifications precede unconditional design PASS; numeric policy pending and unexecuted gold are tracked separately from those design corrections.

## 18. Contract Draft V2.1 / candidate v0.3.1 — three-area targeted review

### 18.1 Scope and accepted closures

**OBSERVED:** read complete contract attachment `f6acac08-bc28-4f39-b99e-e96ee505a5c1/Pasted text.txt` and validation mandate `7ccabaed-bc43-4aff-8893-8a85783f2eb1/Pasted text.txt`. No repo/runtime discovery, foundation re-test, production code, ledger mutation or six-policy-value selection. Prior public-boundary/schema/permission evidence reused from §17. Only standalone Python Decimal arithmetic executed; it is not transaction-backed METHOD GOLD or implementation verification.

| Delta | Result | Evidence / interpretation |
|---|---|---|
| Currency/identity | PASS design | V2.1 §§1–4: auth/source permission→currency validation→normalization→identity→dedupe; incompatible currency never CONFLICTING_OBSERVATION. Logical key excludes amount/due-date; count_key separate. Unsupported company/source scope vs internally corrupted source metadata use distinct existing reasons and no result payload |
| AP precision | PASS design | §§7–9: D>0, exact finite Decimal N>=T×D, no binary-float authority; output quantize(.0001, HALF_UP) only. Native Decimal localcontext supports this; sufficient operand-derived precision and Inexact checking needed for authoritative sums/products, not blind reliance on default context28 |
| HIGH/WATCH equality | PASS design | §8 HIGH first; at common threshold HIGH, no WATCH-only state. V2 reason/finding/trigger/severity invariants remain compatible |
| Gold applicability system | CHANGES_REQUIRED, reachability detail | Reasoned REQUIRED/N/A taxonomy fixes equality/floor0, but §14's unconditional H>W→reachable WATCH cases and F>0→positive below-floor case omit actual representable input precision; V2.1-01 |
| AR method gold feasibility | READY_FOR_METHOD_GOLD | Prior-month calendar resolver, clamp/leap/year and explicit public AI001 calls already implementable. Need a populated real monthly pair; old within-September delta11.5 is arithmetic evidence only, not monthly-method gold |
| AP method gold feasibility | READY_FOR_METHOD_GOLD | Existing fixed public report and permission-checked PI metadata can supply fields/count. Separate controlled PI with two schedules mandatory, terms-disabled/flattened row must still reject. No fixture created/executed here |
| Exact-fraction proof | PASS standalone arithmetic; fixture proof pending | §18.2 shows unchanged exact rule while display ratio rounds differently; TEST_ONLY operand, no production policy approval |
| G4A consistency | CHANGES_REQUIRED, specification only | No new auth/nullability/model flaw found; two narrow declarative consistency issues remain (§18.3). No full pentest/security runtime acceptance claimed |

### 18.2 Exact-fraction feasibility evidence

**OBSERVED standalone stdlib Python:** N=Decimal('1'), D=Decimal('3'); **TEST_ONLY arithmetic operand T=Decimal('0.33332')**, explicitly not any AI003 policy constant/configuration. T×D=.99996 exactly; N>=T×D is True. HALF_UP display at4dp=.3333, at2dp=.33; naive 4dp-share>=T is False. Both display choices leave exact comparison True. `localcontext(prec=50)` and `Inexact` trap on the product confirm native support for this finite demonstration; precision50 is a test context, not a general monetary limit or required production constant.

**DERIVED implementation feasibility:** use ordinary Decimal values from validated decimal text, sufficient context derived from finite operand sizes for exact summation/product and exact comparison; use separate presentation division/quantize. Default Decimal context precision is finite, so “Decimal” by itself does not guarantee no rounding for arbitrarily large operands. No custom numeric type is required. Independent oracle can retain N/D as integer/decimal fraction and exact T×D, with division rounding confined to display. Method gold can use explicitly TEST_ONLY comparison operands without selecting risk-policy values; end-to-end response finding remains POLICY_PENDING until an approved policy exists.

### 18.3 Exact remaining contract changes

**V2.1-01 — applicability must use representable method inputs, not only H>W/F>0.** V2.1 §14 says H>W yields reachable exact-WATCH/between-WATCH outputs and F>0 requires a valid positive below-floor case. AI001 publishes overdue_ar_ratio at4dp; AR delta_pp therefore lies on the .01PP grid. H>W alone does not guarantee a grid point in [W,H); exact WATCH may not be representable at all. For q=.01PP, a WATCH-band candidate exists only if ceil(W/q)×q < H, subject to other prerequisites. Similarly current ar_outstanding is a positive amount at AI001 .01 monetary quantum; F>0 alone does not ensure an allowed positive amount below F (minimum positive .01). No pending threshold/floor is restricted to these quanta in V2.1.

Smallest change: make §14/15's simplified applicability rules subordinate to §21's actual logical-reachability rule including precision, domain and prerequisite gates. Retain equality→NO_SEPARATE_WATCH_BAND and floor0→ZERO_MATERIALITY_FLOOR. Add a reason such as NO_REPRESENTABLE_METHOD_INPUT for other mathematically impossible boundary cases. Exact WATCH/HIGH requires a representable operand; otherwise verify the reachable neighboring GTE cases and declare only the exact-equality case N/A. N/A never excuses absent policy/fixture, failure or unexpectedly unsupported runtime. Do not force aligned threshold values or stricter inequalities unless Chat/Finance deliberately changes policy invariants.

**V2.1-02 — first-failed-stage ordering vs unconditional rank (§11).** Request syntax is first, authentication second, but the new unconditional rank says FORBIDDEN>VALIDATION_ERROR. For malformed syntax plus unauthenticated request, these imply different primary responses. V2's safe syntax-first behavior was valid; the new rank needs its scope clarified. Smallest change: state the numbered first-failed-stage order is normative, safe syntactic INVALID_REQUEST can be returned before auth, and FORBIDDEN precedence applies after syntactic acceptance/resource authorization rather than overriding earlier safe syntax. Alternatively move authentication first explicitly; do not leave both meanings normative. Keep source/coverage/method failures before POLICY_PENDING; no financial payload or resource-existence disclosure from syntax checks.

These are direct consistency effects of the revised applicability/precedence text, not a foundation reopen or a redesign of valid signal methods. Currency-before-identity, exact AP comparison and HIGH-first equality are accepted.

### 18.4 Method-gold work still required

**PROPOSED, feasible plan only:**

- AR: separate controlled populated previous-month/current cutoffs, clamp31→30/28/29 and Jan→Dec calendar cases; unavailable baseline vs baseline/current denominator0; net credits; positive/negative/zero PP; future-posting isolation. Public AI001 snapshots with explicit server-owned cutoff/period, Decimal(str(published ratio)), no comparison.display delta or private class. Oracle independently derives locked voucher/PLE facts and published ratio precision; imports no AI003 engine.
- AP: transaction-backed D0/D30/D31/long-dated positive PI, past-due and negative-credit exclusions; exact future-positive D, window N, counts; repeating fraction and separate display/exact comparison; 0/1/2 schedules. At least one **real controlled PI with two child schedules**, report payment-terms disabled/flattened, permission-checked authoritative parent preflight still yields UNSUPPORTED_MULTI_SCHEDULE.
- Labelled source perturbations for duplicate/conflict, missing due date and currency failure-before-identity; prove reconciliation not invoked on currency failure. Fixed supported DocType map; explicit checked-user parent read permission and company verification, no get_all permission bypass, no invented child/allocation identity. Allowed/denied checked-user and cross-company metadata cases must be executed in gold/security work.
- Independent manifest records source hashes, versions, dates/currency/data mode, exact N/D and comparison operands, response nullability/reason, applicability/reason and expected output. All mandatory METHOD/SECURITY/MODEL cases remain required; POLICY_NOT_APPLICABLE only for approved-method/policy logical impossibility, excluded from both pass-rate numerator and denominator.

**METHOD GOLD BLOCKERS:** none to creating controlled method gold; its execution/real-two-schedule proof is still outstanding, not already PASS. Correct V2.1-01/02 before treating applicability/primary failure expectations as the final acceptance oracle. No numeric production thresholds needed to prepare method gold.

### 18.5 Targeted gate result

```yaml
CURRENCY/IDENTITY: PASS
AP PRECISION: PASS
HIGH/WATCH EQUALITY: PASS
GOLD APPLICABILITY: CHANGES_REQUIRED
AR METHOD GOLD FEASIBILITY: READY_FOR_METHOD_GOLD
AP METHOD GOLD FEASIBILITY: READY_FOR_METHOD_GOLD
EXACT-FRACTION PROOF: PASS_STANDALONE_ARITHMETIC_FIXTURE_PENDING
G4A CONSISTENCY: CHANGES_REQUIRED

G2 CONTRACT: CHANGES_REQUIRED
G3 METHOD DESIGN: READY_FOR_METHOD_GOLD
G4A SECURITY/EVAL DESIGN: CHANGES_REQUIRED

EXACT REMAINING CONTRACT CHANGES:
  - Applicability must include representable method precision/domain.
  - Clarify syntax-first order versus unconditional FORBIDDEN ranking.
METHOD GOLD BLOCKERS: NONE_TO_PREPARATION_EXECUTION_PENDING
POLICY VALUES: PENDING_APPROVAL
CURRENT VERDICT: CONTRACT_V2_1_CHANGES_REQUIRED
CONTRACT FREEZE: NOT_FROZEN
NEXT OWNER: ChatGPT Chat
```

All six named numeric constants from V2/V2.1 remain pending; no policy registry or production value was created/approved. Existing result/reason-code/nullability/LLM-independence/company-resource auth behavior is otherwise retained unchanged.

## 19. V2.2 targeted contract validation — 2026-10-02

### 19.1 Scope and evidence

**OBSERVED:** reviewed the normative V2.2 rules supplied in attachment `3ddb943f-7990-41e0-957a-a856857cc024/Pasted text.txt`. This attachment is a validation mandate containing the revised rules, not a separate complete V2.2 contract document. The verdict below covers those supplied deltas and their consistency with the previously reviewed V2/V2.1 schema. No full-document freeze or implemented AI003 acceptance is claimed.

Existing §17–18 public-boundary, method and schema evidence reused. No foundation re-test, runtime rediscovery, ledger mutation, production edit, policy selection or broad security audit. Following workflow V3, this result is recorded in the existing feature SSOT. A narrowly scoped Docker source read records current framework transport parsing and ERPNext monetary normalization in [V2.2 source evidence](evidence/contract_v2_2_targeted_source_2026-10-02.json).

**OBSERVED execution limitation:** the supplemental live precision query could not resolve the site's configured database hostname: `MySQLdb.OperationalError (2005): Unknown server host 'db' (-2)`. Earlier probe attempts also encountered a logger working-directory error; running from the sites directory removed that error and exposed the DB connection failure. No live precision value or HTTP end-to-end result was obtained. No transaction was established, and no business data was written. Docker availability alone does not establish site DB availability; no stack reconfiguration was attempted.

### 19.2 Targeted conclusions

| Area | Result | Evidence / required interpretation |
|---|---|---|
| AR representability | PASS design | Published AI001 ratio scale4 implies delta grid .01PP. `x_watch=ceil(WATCH/.01)×.01`; WATCH-only requires `x_watch<HIGH` **and a valid representable witness satisfying all remaining method/materiality prerequisites**. H>W alone is insufficient. Exact equality is REQUIRED only on the valid method grid; otherwise EXACT_BOUNDARY_NOT_REPRESENTABLE. Valid neighboring boundary cases remain REQUIRED; lack of a valid neighbor must itself be proved against the domain, never inferred from unsuccessful fixture search |
| Money quantum / floor | PASS design; live AP quantum NOT_VERIFIED | §18 establishes AI001 monetary normalization at .01. Current ERPNext report source uses `get_currency_precision() or 2` and rounds outstanding with that precision. The helper reads backend currency_precision, with backend number_format fallback; this is actual source normalization, not an inference from rendered VND formatting. METHOD GOLD can pin effective precision/source versions and verify controlled amounts without modifying production contracts. Pin the quantum for each consumed boundary; do not assume AP inherits AI001's quantum. Positive below-floor needs an actual positive representable amount <F, not merely F>0 |
| AP reachability | PASS design | Use exact finite-decimal N>=T×D, D>0, 0<=N<=D, N>=F, N>=WATCH×D, N<HIGH×D. For a pinned money grid, an independent oracle can express N=nQ and D=dQ with integer n,d, plus actual domain bounds and prerequisites. A concrete valid witness proves reachability; N/A needs a mathematical/domain impossibility proof. Failed search, absent fixture, unavailable runtime or missing implementation is not such a proof. No policy-specific reachability result is asserted before policy approval |
| Gold applicability | PASS design | REQUIRED pairs only with NOT_RUN/PASS/FAIL; NOT_APPLICABLE pairs with NOT_APPLICABLE. N/A needs domain/method/policy versions, the case predicate, one of the four supplied proof codes and an explanatory proof. A reason label alone is not proof. Pending policy or unknown precision retains NOT_RUN/unresolved applicability, never N/A. This resolves V2.1-01 |
| Gate accounting | PASS design | Keep a complete versioned case registry. Every REQUIRED case must PASS; FAIL or NOT_RUN prevents gate PASS. N/A is excluded from both numerator and denominator and retained in the manifest with proof. Required cases cannot be dropped or silently reclassified. Design readiness here does not mean execution gates have passed |
| Transport split | PASS design / source compatibility | Current `make_form_dict(request)` catches orjson JSONDecodeError and throws Frappe DataError before a business response. Thus malformed transport can remain outside RiskSignalResponse. TRANSPORT_ERROR is the contract's category, not a claim that Frappe emits that literal status or a particular HTTP envelope. A parseable request object reaches the application boundary; auth must run before business enum/type/semantic validation there. Safe adapter behavior is implementable; no whitelisted endpoint or HTTP integration was executed |
| First-failed-stage | PASS design | Sole normative A1→A11 ordering replaces the independent global status rank. Cases A/B/C/D/E/F yield FORBIDDEN / VALIDATION_ERROR / FORBIDDEN / SOURCE_ERROR / INCONCLUSIVE / POLICY_PENDING respectively. A2 is structural only and performs no company lookup; A4 future-date/scope semantics follow A3 company authorization. Source defects at A6/A7 and method failures at A8 cannot be hidden by A9 policy absence. This resolves V2.1-02 |
| Security consistency | PASS design | Retain generic ACCESS_DENIED for denied/nonexistent company or resource, no company/resource-specific disclosure before authorization, and null financial/evidence result on FORBIDDEN/VALIDATION_ERROR/SOURCE_ERROR. Authenticated structural errors may disclose only safe shape/format requirements. Partial INCONCLUSIVE/POLICY_PENDING results contain only independently valid authorized values. Evidence authorization and explanation/LLM isolation remain required. These are design conclusions, not runtime security acceptance |

The allowed applicability proof codes are exactly `NO_SEPARATE_WATCH_BAND`, `EXACT_BOUNDARY_NOT_REPRESENTABLE`, `NO_POSITIVE_REPRESENTABLE_VALUE_BELOW_FLOOR`, and `LOGICALLY_UNREACHABLE_BY_METHOD`. They describe eval-case applicability, not new RiskSignalResponse reason codes. No source failure is converted into a benign finding or N/A.

Unaffected V2.1 decisions remain accepted: currency validation before identity; exact AP comparison; 4dp HALF_UP display only; HIGH before WATCH; prior-month same-day/clamped AR baseline; positive-future AP denominator and inclusive D0–D30 numerator; multi-schedule fail-closed; separate observation identity/count_key; existing reason/nullability/explanation rules; no dedicated AI003 cache; VND only; Finance Book unsupported.

### 19.3 Verdict and next work

```yaml
G2 CONTRACT: PASS
G3 METHOD DESIGN: READY_FOR_METHOD_GOLD
G4A SECURITY/EVAL DESIGN: PASS
EXACT REMAINING CONTRACT CHANGES: NONE_FOR_REVIEWED_DELTAS
METHOD GOLD BLOCKERS:
  - Execution environment: site DB hostname db is not resolvable; restore connectivity before pinning live precision and executing transaction-backed gold.
POLICY VALUES: PENDING_APPROVAL
CURRENT VERDICT: CONTRACT_V2_2_VALIDATED
CONTRACT FREEZE: NOT_FROZEN
NEXT OWNER: ChatGPT Chat
```

**NO FURTHER CONTRACT DESIGN ROUND REQUIRED. NEXT PHASE = METHOD GOLD EXECUTION.** There is no method-design blocker. The execution limitation does not justify another contract round or N/A. §18.4's independent AR two-month/baseline-failure and AP boundary/dedupe/conflict/missing-date/real-two-schedule fixtures remain outstanding; their oracle must not import an AI003 engine. Pin money precision, method/domain versions and evidence hashes during controlled setup. Required method/security cases must execute, and policy-specific cases remain NOT_RUN until the six existing values are approved. No numeric policy value has been selected or approved and no AI003 contract is frozen.

## 20. Runtime recovery + METHOD GOLD — 2026-10-02

**OBSERVED authority:** [METHOD GOLD evidence](AI003_METHOD_GOLD_EVIDENCE.md), [66-case manifest](AI003_METHOD_GOLD_MANIFEST.yaml), [independent stdlib-only transaction oracle](AI003_METHOD_GOLD_ORACLE.py), [test-only runner](evidence/method_gold_runner.py). User mandate `a3a51885-b468-447c-b915-fd77d4405bdd/Pasted text.txt` authorizes runtime recovery and new controlled transactions on the isolated verification site; no production AI003 or numeric policy selection.

Root cause of §19's DB blocker was stopped DB/Redis containers, not missing network/alias configuration. `docker start` restored the three original services without recreating/resetting DB/site volumes. Site `ai003-verify.localhost` now resolves db, connects, has frappe/erpnext/lotus_fin installed and timezone Asia/Ho_Chi_Minh. Current workspace revision8941cfb app source is mounted read-only for the disposable probe process; public-boundary hashes/app path recorded. Source app tree is unchanged.

**OBSERVED numeric domain:** VND; report and AI001 money scale2/Q=.01, supported by source precision and real submitted .01 SI/PI; published overdue ratio scale4/HALF_UP; AR delta grid.01PP. Default ERP invoice rounding explains why some gross rates differ from posted balances; oracle follows posted PLE attribution. No contract precision assumption changed and no oracle/production formula was altered to match output.

AR monthly/clamp/leap/year cases reconcile current and baseline totals, overdue amounts, published ratios and PP against posted transactions/public reports. Positive72.73PP, negative−4.35PP and zero published-method delta pass. Missing baseline, verified zero denominators, net credits, future posting, source failure and real report denial pass. Source-baseline corruption precedes current-zero method failure and missing policy.

AP future-positive denominator9, D0–D30 numerator3, exact fraction1/3, 4dp display.3333, distinct voucher counts2/4 pass. D31/long dated remain denominator-only; past due/credits excluded. Real zero/one schedules, controlled rolled-back positive-parent zero-schedule metadata, and **real submitted PI with two children despite one flattened report row** pass; the latter yields INCONCLUSIVE/UNSUPPORTED_MULTI_SCHEDULE. Duplicate/conflict/missing/malformed date, unproved account scope, currency-before-identity, actual checked-user metadata denial and cross-company/nonexistent-parent generic suppression pass.

Test-only T=.33332 proves exact N>=T×D (true) versus rounded display comparison(false), with independent Fraction agreement. It is confined to method evidence, not a production policy/configuration. Application ordering is exercised only by a document-side harness using real existing public providers/guards; no AI003 endpoint/engine or full G4B audit is claimed.

Hygiene independently rechecked: zero temporary users/User Permissions/AR Custom Role restrictions; restored positive-parent schedule count1, retained multi-parent count2; protected prior non-MG voucher/PLE hashes and final MG hashes unchanged after probes. Intentionally retained five new controlled companies, seven SI, eight PI, one PE, supporting account/master/fiscal coverage. No shared frontend/site mutation or AI004/AI005 logic work.

Operational limitation retained in evidence: Standard Template Company creation triggers missing `lotus_fin.lotus_fin` during ERP template resync. Fixture creation uses the supported native Existing Company COA-copy path; no production patch/bypass. This unused path is not asserted fixed and does not block the verified method boundaries. Earlier setup/harness diagnostics retained; final counts have no omitted required cases, FAIL or NOT_RUN.

| Area | PASS | FAIL | NOT_RUN |
|---|---:|---:|---:|
| Runtime | 2 | 0 | 0 |
| Precision/fraction/currency ordering | 6 | 0 | 0 |
| AR | 15 | 0 | 0 |
| AP | 21 | 0 | 0 |
| First-failed-stage | 7 | 0 | 0 |
| Security | 12 | 0 | 0 |
| Hygiene | 3 | 0 | 0 |
| Total | 66 | 0 | 0 |

```yaml
G2 CONTRACT: PASS
G3 METHOD GOLD: PASS
G4A PRE-BUILD RUNTIME/EVAL: PASS
METHOD GOLD BLOCKERS: NONE
POLICY VALUES: PENDING_APPROVAL
CURRENT VERDICT: METHOD_GOLD_VERIFIED
CONTRACT FREEZE: NOT_FROZEN
NEXT OWNER: ChatGPT Chat
```

**METHOD DESIGN + METHOD GOLD CLOSED. NEXT PHASE = POLICY APPROVAL + POLICY GOLD.** Six existing numeric policy constants still await approval; no calibration/threshold or contract freeze is inferred from synthetic fixtures. Foundation acceptance remains inherited without broad re-audit.

## 21. Policy approval package — 2026-10-02

**OWNER-APPROVED DEMO_ONLY policy:** [current decision sheet](AI003_BUSINESS_POLICY_DECISION_SHEET.md) binds `AI003_DEMO_POLICY_V1`: AR floor 0 VND / WATCH 5.00pp / HIGH 15.00pp; AP floor 0 VND / WATCH .50 / HIGH .75; Project Owner, 2026-10-02; `production_calibrated=false`. **NOT APPROVED FOR PRODUCTION** and no automatic promotion path. Production calibration/approval remains pending; synthetic fixtures are not calibration evidence.

**POLICY GOLD verified:** [manifest](AI003_POLICY_GOLD_MANIFEST.yaml) and [evidence](AI003_POLICY_GOLD_EVIDENCE.md) record 17 REQUIRED PASS, 0 FAIL/NOT_RUN/errors and 4 V2.2-proved N/A. AR used public typed snapshots; AP used authorized public report/parent metadata and exact `N>=T*D`; both display-rounding traps passed. METHOD GOLD was not rerun; its 66/66 manifest, oracle, source and fixture fingerprints remained unchanged. Temporary policy transactions/companies were fully rolled back. No production AI003 code/config was created.

```yaml
G2 CONTRACT: PASS
G3 METHOD GOLD: PASS
G4A PRE-BUILD RUNTIME/EVAL: PASS
METHOD GOLD: 66 PASS / 0 FAIL / 0 NOT_RUN
DEMO POLICY: AI003_DEMO_POLICY_V1 / DEMO_ONLY / OWNER_APPROVED
PRODUCTION POLICY: PENDING_APPROVAL
POLICY GOLD: 17 REQUIRED PASS / 4 NOT_APPLICABLE / 0 FAIL / 0 NOT_RUN
CURRENT VERDICT: POLICY_GOLD_VERIFIED
CONTRACT FREEZE: NOT_FROZEN
NEXT OWNER: ChatGPT Chat
```

# Historical investigation — retained, superseded by current §1–21 above

# AI-F003 Risk Signal Agent — pre-build investigation (draft, chưa freeze)

## 1. Document control

- Ngày điều tra: 2026-09-29; cập nhật xác thực 2026-09-30 tại §29–35. Trạng thái: **PRE-BUILD FINDING / NOT CONTRACT FROZEN**. Chủ đích: evidence collector; không có AI003 production code.
- Workspace hiện tại: `E:\lotus-fin`, revision `86208f49e05122531c1cbe8b11d066092244dd4c`; production source vẫn bằng `c6f4cd1` (commit mới documentation/harness only). §4–34 là lịch sử; **§35 là Work final foundation/pre-build evaluation mới nhất**. Runtime là isolated site `ai003-verify.localhost`; không suy kết quả sang site `frontend`.
- Thứ tự chứng cứ: runtime hiện tại > test hiện tại > đọc mã hiện tại > báo cáo cũ > giả định. `NOT_VERIFIED` nghĩa là chưa có chứng cứ, không nghĩa là âm tính.
- GitNexus index lúc bắt đầu trỏ tới `f743acf...` (sau HEAD 9 commit), thiếu FTS; truy vấn `snapshot`/`forecast` trả rỗng. `impact build_financial_snapshot` thấy caller `get_financial_snapshot`, risk LOW; `impact extract_key_report_data` thấy AI001 fetcher, `predict_cashflow`, `get_ai_training_dataset`, risk LOW; `impact get_verified_company` thấy 7 caller, risk MEDIUM. `impact get_cash_forecast` trả `UNKNOWN`/target not found. Các verdict này **không** xác nhận blast radius của workspace hiện tại; đã đối chiếu bằng mã nguồn. Không chỉnh sửa hàm/lớp nào. `node .gitnexus/run.cjs analyze --index-only` thất bại ở parse phase vì toàn bộ worker khởi động lỗi; index vẫn stale, không được coi là graph check sạch.

## 2. Problem

Người chủ SME, quản lý tài chính hoặc người được cấp quyền cần biết dấu hiệu nào đáng kiểm tra, bằng chứng nào hỗ trợ, và nên kiểm tra tiếp ở đâu. `RiskSignal` chỉ là ưu tiên rà soát; không kết luận gian lận, vỡ nợ hay ra quyết định tín dụng.

## 3. Scope

- Chỉ đọc; rule và evidence đi trước. Rule quyết định severity; LLM chỉ giải thích số liệu có sẵn và đề nghị bước kiểm tra thuộc allowlist.
- Không có điểm rủi ro hộp đen, payment, bank submission, ghi sổ hoặc thay đổi threshold từ prompt.
- Đánh giá 10 candidate, không giả định candidate nào có thể triển khai. `READY` đòi hỏi nguồn, ngữ nghĩa, cutoff, permission, evidence, rule và gold đều được xác minh. **Hiện chưa có signal READY.**

## 4. Runtime và bản đồ thành phần

| Hạng mục | Hiện trạng / mức chứng cứ |
| --- | --- |
| Site | `frontend`, container `frappe_docker-backend-1`, runtime command `bench --site frontend list-apps`. |
| Version / app | Frappe `16.34.0`, ERPNext `16.35.0`, `lotus_fin 0.0.1`; installed `frappe`, `erpnext`, `lotus_fin` (runtime 2026-09-29). |
| Company / currency | `Name (Demo)` trả `default_currency=VND` qua `frappe.db.get_value` (runtime); `AI002 Fixture 2026` chỉ được nêu trong AI002 SSOT cũ, chưa xác minh lại dữ liệu hôm nay. |
| Timezone | Site `Africa/Abidjan` qua `frappe.utils.get_system_timezone`; AI002 response/contract ghi `Asia/Ho_Chi_Minh` (`cashflow/models.py`, `service.py`). Chưa giải quyết lệch ngày kế toán. |
| Finance Book | `ForecastRequest.finance_book` có field nhưng API AI002 không nhận/truyền, adapter hiện không lọc Finance Book; AI001 P&L/AR/AP/TB cũng không đưa Finance Book vào filters. **NOT_VERIFIED** cho scope book. |
| AI001 | API `api/ai_insights.py:get_financial_snapshot` → `ai/financial_snapshot.py:build_financial_snapshot` → `api/key_reports.py:extract_key_report_data` → ERPNext reports. Snapshot contract `1.0.0`, formula `2026.1`; 4 nguồn P&L, AR, AP, TB; có 7 core metrics, `near_term_ap` cố ý UNAVAILABLE. `ai/financial_health.py` so kỳ trước; `ai/explanation.py` giải thích; `ai/observability.py` log. UI `lotus_fin_ai/page/financial_health`. |
| AI002 | API `api/ai_insights.py:get_ai002_cash_forecast` → `cashflow/service.py:get_cash_forecast` → `adapters.py`/`engine.py`; models contract `1.2.1`, method/formula `STRICT_BASELINE_V1`. `cashflow/cache.py` TTL 300 giây; `agent.py`/`tools.py`/`grounding.py` có bounded explanation. UI `lotus_fin_ai/page/cash_forecast`. |
| Test/fixture | AI001 tests `test_financial_snapshot`, `test_financial_health`, `test_explanation`; AI002 `test_cashflow_engine`, `test_cashflow_security`, `test_cashflow_failclosed`; AI002 fixture và gold ở `docs/features/AI002`. Workspace `python -m unittest -q` trên sáu module: **127 tests OK**. Container cũ thiếu `test_cashflow_failclosed`: cùng lệnh chạy 54 tests rồi lỗi import; không được dùng làm bằng chứng cho workspace. |

AI001 metric có thể dùng làm **candidate input**: `revenue`, `cogs`, `gross_margin`, `ar_outstanding`, `overdue_ar_ratio`, `ap_outstanding`. Chưa được công nhận là authoritative cho AI003 vì các lỗi trust/cutoff dưới đây. AI002 có `shortfall_events`, `opening_cash`, `obligations`, `coverage`, `evidence_refs`, nhưng production `FailClosedSource` không có confirmed future event; `FORECAST_UNAVAILABLE` không phải shortfall âm tính.

## 5. Data và trust findings

1. AI001 parser AR/AP bỏ qua row thiếu/không đọc được amount rồi trả zero nếu không còn row hợp lệ (`financial_snapshot.py:236-350`). Controlled replay: `parse_ar_data([{"party":"X"}], date(2026,9,26))` trả `(0,0,0, ["No active receivables found in period."])`; `parse_ap_data` cũng trả `0`. Đây là **invalid row → apparent zero**, blocker cho AR/AP signal. Một report `status` khác `error`, `data` thiếu mặc định thành `[]` tại snapshot processing; cần phân biệt success-empty và malformed/unknown status.
2. AI001 `as_of` được cắt 10 ký tự và lấy `min(period_end, as_of)`; không validate ISO đầy đủ hay `as_of >= period_start`. `comparison=PREVIOUS_PERIOD` tạo previous snapshot với `as_of=None` (`financial_snapshot.py:578-588, 1007-1022`), nhưng report kỳ trước vẫn lọc theo `prev_end`. Chưa chứng minh replay theo thời điểm đã biết trước các bút toán backdated/cancelled; period comparison cũng được tính từ khoảng kỳ gốc ngay cả khi current bị cắt sớm. Cần test future posting, backdated edit, cancellation cho cả current/previous.
3. AI001 `build_comparison_block` ghi chú kiểm tra currency nhưng chỉ so `company` (`financial_health.py:149-160`), và `relative_change` với previous zero là `None` dù block metric status vẫn `AVAILABLE`. Không biến status AVAILABLE thành change khả dụng.
4. AI001 `currency` là tham số client và được gắn nhãn vào metric; chưa thấy đối chiếu với company/report currency hoặc FX. P&L parse dựa tên tài khoản (`financial_snapshot.py:108-233`), COGS chưa xác thực theo chart của từng tenant. Expense, party concentration, inventory không có metric riêng.
5. AI001 EvidenceRef là report metadata + `checksum_or_version`, không phải doc ref `DocType:docname`; checksum tạo từ payload nhưng không giữ immutable payload hay API kiểm chứng lại cùng version (`financial_snapshot.py:75-105`). AI002 evidence là doc refs, được reauthorize qua `get_ai002_evidence`/`verify_evidence_access` (`api/ai_insights.py:446-474`, `security/access.py:105-157`). Hai loại không thể gọi chung một drilldown không có discriminated type.
6. AI002 AR/AP adapter bắt `status=success`, list dict, amount hợp lệ, company/currency, voucher và due date (`cashflow/adapters.py:250-435`); có `ObligationSourceError`/`ObligationPermissionError`. Đây là nguồn candidate tốt hơn AI001 cho due-date obligation, nhưng không suy due date thành ngày tiền về/ra. Opening cash cần GL↔TB reconciliation, approved account scope. Theo `service.py:299-340`, không có confirmed future events thì response `FORECAST_UNAVAILABLE`, không có point hay shortfall.
7. Không có sample distribution, số quan sát tối thiểu, denominator policy hoặc peer baseline được xác minh cho AI003. Số liệu fixture AI002 là kỹ thuật, không là business truth.

## 6. Signal feasibility matrix

Ký hiệu: `Y/P/N` = YES/PARTIAL/NO; `NV` = NOT_VERIFIED. Coverage `fixture` chỉ là dữ liệu AI002 cũ; không chứng minh live AI003. `P0` là đề nghị điều tra sau gate, không là quyền build.

| signal_type | business_meaning / required_metric | authoritative_source; actual_source_path | required_fields (đã thấy, không giả lập) | fields / baseline / as_of | currency_semantics | permission_verified / evidence_supported | current_data_coverage | status / P0 / blocking_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AR_OVERDUE_SPIKE` | Tỷ trọng AR quá hạn tăng; `overdue_ar_ratio` hiện/kỳ trước | AI001 candidate; `ai/financial_snapshot.py:parse_ar_data`, `ai/financial_health.py:build_comparison_block`, AR report | `outstanding` hoặc alias, `overdue_amount`/`overdue` hoặc `due_date`; report `report_date` | P/P/P | VND label chưa reconcile FX | P / report checksum P | demo history NV | PARTIAL / CONDITIONAL / malformed→zero, baseline cutoff, denominator và threshold chưa chốt |
| `AP_DUE_CLUSTER` | Nghĩa vụ AP tập trung vào cửa sổ hạn; sum/count by `due_date` | AI002 obligation candidate; `cashflow/adapters.py:get_trade_obligations`, AP report | `outstanding`, voucher ref, `due_date`, currency | P/N/P | AI002 VND-only gate | P / doc ref P | fixture cũ; live NV | PARTIAL / CONDITIONAL / due date có thể null; định nghĩa window/materiality chưa chốt; không gọi là cash shortfall |
| `CUSTOMER_CONCENTRATION` | AR hoặc doanh thu lệ thuộc khách hàng; share/HHI cần scope | AI002 obligation party hash candidate, không có authoritative aggregate; `cashflow/models.py:Obligation`, AR report | `party_hash`, `remaining_amount`; revenue by customer chưa có | P/N/P | AI002 VND-only | P / doc ref P | live NV | NOT_READY / NO / lựa chọn AR vs sales, party identity và denominator chưa chuẩn |
| `SUPPLIER_CONCENTRATION` | AP/mua hàng lệ thuộc nhà cung cấp | AI002 AP obligation candidate; `cashflow/adapters.py:get_trade_obligations`; Purchase Analytics chưa map | `party_hash`, `remaining_amount`; spend per supplier chưa có | P/N/P | AI002 VND-only | P / doc ref P | live NV | NOT_READY / NO / phải chọn AP exposure vs procurement spend và xác minh nguồn |
| `MARGIN_DROP` | Gross margin kỳ này giảm; `gross_margin` comparison | AI001 candidate; `ai/financial_snapshot.py:parse_pnl_data`, `financial_health.py` | P&L `account_name`/`account`, amount aliases, COGS row | P/P/P | ratio, underlying currency cần reconcile | P / report checksum P | demo history NV | PARTIAL / CONDITIONAL / COGS mapping tên tài khoản, as_of kỳ trước, denominator và threshold |
| `EXPENSE_SPIKE` | Chi phí vận hành tăng bất thường | unavailable authoritative metric; P&L report `api/key_reports.py` mới là raw data | expense account mapping và period totals chưa xác minh | N/N/P | currency/FX NV | report permission P / evidence N | NV | NOT_READY / NO / không có AI001 expense metric; tránh dựng engine P&L thứ ba |
| `SALES_DECLINE` | Doanh thu kỳ này giảm; `revenue` comparison | AI001 candidate; `ai/financial_snapshot.py:parse_pnl_data`, `financial_health.py` | P&L revenue row/amount | P/P/P | client currency label chưa reconcile | P / report checksum P | demo history NV | PARTIAL / CONDITIONAL / parser tài khoản, historical cutoff, baseline & threshold |
| `INVENTORY_CASH_LOCK` | Tiền bị giữ trong tồn kho | `Stock Balance` có trong `api/key_reports.py`, nhưng ratio/valuation + cash scope chưa có | stock value, turnover/cash mapping chưa xác minh | N/N/N | valuation/currency NV | report permission P / evidence N | NV | NOT_READY / NO / chưa có định nghĩa metric/cutoff/gold |
| `CASH_SHORTFALL` | Modeled 30-day cash < 0; `shortfall_events` | AI002; `cashflow/service.py:get_cash_forecast`, `engine.py:compute_forecast` | reconciled opening, eligible confirmed cash events, `forecast_points`, `shortfall_events` | P/N/P | VND-only; timezone site mismatch | P / doc ref P | future source fixture-only | BLOCKED / NO live; CONDITIONAL fixture / production FailClosedSource, no live confirmed settlements, timezone |
| `COLLECTION_DELAY` | Thời gian thu tiền dài hơn baseline | unavailable; AI002 obligations only due date, AI001 AR balance | actual allocation/receipt timing, invoice date, due date, partial payments chưa có unified source | N/N/N | NV | NV / N | NV | NOT_READY / NO / không được suy actual collection từ contractual due date |

Không signal nào được gắn `READY`: permission `P` nghĩa là có guard/code/unit evidence, chưa có AI003 cross-role E2E; evidence `P` nghĩa là ref tồn tại nhưng chưa có lineage/drilldown thống nhất. `as_of=P` chỉ là filter code, không phải temporal leakage test đã pass.

Checklist dưới đây giữ riêng **toàn bộ field bắt buộc** để có thể chuyển sang machine-readable contract sau này. `PARTIAL` về permission/evidence không là authorization PASS.

| signal_type | business_meaning | required_metric | authoritative_source | actual_source_path | required_fields | field_semantics_verified | historical_baseline_available | as_of_supported | currency_semantics | permission_verified | evidence_supported | current_data_coverage | status | recommended_P0 | blocking_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AR_OVERDUE_SPIKE | AR quá hạn tăng | overdue_ar_ratio delta | AI001 candidate / AR report | `financial_snapshot.py:parse_ar_data` | outstanding, overdue/due_date | PARTIAL | PARTIAL | PARTIAL | label VND, FX NV | PARTIAL | PARTIAL | NV | PARTIAL | CONDITIONAL | malformed→zero, denominator/cutoff/rule |
| AP_DUE_CLUSTER | hạn AP dồn cụm | AP amount/count by due date | AI002 obligation / AP report | `adapters.py:get_trade_obligations` | outstanding, voucher, due_date | PARTIAL | NO | PARTIAL | VND-only | PARTIAL | PARTIAL | old fixture only | PARTIAL | CONDITIONAL | null due date, window/rule |
| CUSTOMER_CONCENTRATION | AR/sales tập trung | party share | AI002 obligation candidate | `models.py:Obligation` | party_hash, remaining_amount | PARTIAL | NO | PARTIAL | VND-only | PARTIAL | PARTIAL | NV | NOT_READY | NO | AR-vs-sales denominator, identity |
| SUPPLIER_CONCENTRATION | AP/spend tập trung | party share | AI002 obligation candidate | `models.py:Obligation` | party_hash, remaining_amount | PARTIAL | NO | PARTIAL | VND-only | PARTIAL | PARTIAL | NV | NOT_READY | NO | AP-vs-spend denominator |
| MARGIN_DROP | biên gộp giảm | gross_margin delta | AI001 candidate / P&L | `financial_snapshot.py:parse_pnl_data` | revenue, COGS report rows | PARTIAL | PARTIAL | PARTIAL | ratio; underlying FX NV | PARTIAL | PARTIAL | NV | PARTIAL | CONDITIONAL | COGS mapping, prior cutoff/rule |
| EXPENSE_SPIKE | chi phí tăng | expense delta | unavailable metric / P&L candidate | `key_reports.py:profit_and_loss` | expense account mapping | NO | NO | PARTIAL | FX NV | PARTIAL | NO | NV | NOT_READY | NO | chưa có metric authoritative |
| SALES_DECLINE | doanh thu giảm | revenue delta | AI001 candidate / P&L | `financial_snapshot.py:parse_pnl_data` | revenue report row | PARTIAL | PARTIAL | PARTIAL | label VND, FX NV | PARTIAL | PARTIAL | NV | PARTIAL | CONDITIONAL | account mapping, prior cutoff/rule |
| INVENTORY_CASH_LOCK | tồn kho giữ tiền | inventory value/cash ratio | Stock Balance candidate | `key_reports.py:stock_balance` | valuation, turnover, cash | NO | NO | NO | valuation FX NV | PARTIAL | NO | NV | NOT_READY | NO | metric/cutoff/gold chưa có |
| CASH_SHORTFALL | modeled EOD cash âm | shortfall_events | AI002 | `service.py:get_cash_forecast` | reconciled opening, confirmed events | PARTIAL | NO | PARTIAL | VND-only, timezone lệch | PARTIAL | PARTIAL | fixture only | BLOCKED | NO live | thiếu production settlement source |
| COLLECTION_DELAY | actual thu tiền chậm | actual collection lag | unavailable | `adapters.py:get_trade_obligations` chỉ due date | payment allocation, invoice/receipt dates | NO | NO | NO | NV | NO | NO | NV | NOT_READY | NO | due date không là collection date |

## 7. Method, source map và threshold feasibility

| Signal candidate | Source map (kind/service/DocType; runtime) | Scope / semantics | Missing, zero, exception, evidence | Threshold khả thi (chưa chọn giá trị) |
| --- | --- | --- | --- | --- |
| AR overdue | ERP report → AI001 snapshot; Accounts Receivable; runtime AI001 cũ có, current call NV | company, `report_date=min(period_end,as_of)`, VND label; overdue if `due_date < cutoff`; finance book NV | Missing row hiện có thể thành zero: **block**. Success-empty chỉ zero khi source status/shape đúng; permission/source error tách riêng. Report checksum ref. | absolute ratio và prior-period delta lý thuyết; rolling/peer/distribution NV; min AR denominator/count policy NV. |
| AP due cluster | ERP report → AI002 obligations; Purchase Invoice doc refs; current live call NV | company, `report_date=financial_as_of`; due date là contractual, window phải versioned; VND only; book NV | Null due date → inconclusive cho cluster; zero confirmed obligations ≠ source error; typed exception; doc refs. | absolute amount/count hoặc relative concentration lý thuyết; prior/rolling/peer NV; min count/denominator NV. |
| Customer/supplier concentration | AI002 AR/AP obligations, Sales/Purchase Analytics chưa chứng minh; document refs; live NV | company/cutoff VND; share theo party hash chỉ nếu identity stable; AR/AP exposure khác sales/spend | Missing party/amount, zero total → inconclusive; source denial/error typed; no released aggregate evidence | share/HHI lý thuyết; prior/rolling/peer/distribution NV; total exposure >0 và min parties cần quyết định. |
| Sales decline/margin drop | ERP P&L → AI001 snapshot + comparison; report checksum; current live call NV | period start/end + effective cutoff; previous snapshot hiện `as_of=None` (block); gross margin `(revenue−COGS)/revenue` khi revenue >0; currency label chưa reconcile | Missing P&L/COGS/revenue và zero denominator phải inconclusive; source exception riêng; report ref thiếu immutable replay | absolute/prior-relative lý thuyết; rolling/peer/distribution NV; min revenue/count policy NV. |
| Cash shortfall | AI002 `ForecastResponse.shortfall_events` (GL/TB, AR/AP, synthetic future source); fixture/unit runtime only | company, EOD 30 ngày từ `financial_as_of+1`; zero threshold là AI002 technical breach, không là AI003 severity; VND, book NV | `FORECAST_UNAVAILABLE` = unknown, không benign; verified zero modeled cash không breach; typed source/reconciliation failures; doc refs cần auth | `modeled_cash<0` đã có ở AI002; severity magnitude/duration chưa có rule; historical distribution/peer NV. |

Source map chi tiết cho các signal có đường dữ liệu candidate (không đồng nghĩa production usable):

```yaml
AR_OVERDUE_SPIKE:
  source: {source_kind: ERP_NEXT_REPORT, service_or_report: AI001 FinancialSnapshot / Accounts Receivable, DocType_if_any: null, runtime_verified: NO_CURRENT_CHECKOUT}
  scope: {company: server_verified_required, as_of: report_date, period: current_and_previous_required, currency: VND_label_unreconciled, finance_book: NOT_SUPPORTED}
  semantics: {sign: positive_outstanding, cutoff: effective_end_date, date_field: due_date_or_report_overdue, missing_behavior: CURRENTLY_CAN_COLLAPSE_TO_ZERO_BLOCK, zero_behavior: accept_only_success_empty_and_valid_denominator}
  trust: {state: PARTIAL}
  evidence: {supported: PARTIAL, evidence_ref_type: AI001_REPORT_CHECKSUM}
AP_DUE_CLUSTER:
  source: {source_kind: ERP_NEXT_REPORT, service_or_report: AI002 get_trade_obligations / Accounts Payable, DocType_if_any: Purchase Invoice, runtime_verified: NO_CURRENT_CHECKOUT}
  scope: {company: server_verified_required, as_of: financial_as_of, period: versioned_due_window_required, currency: VND_ONLY, finance_book: NOT_SUPPORTED}
  semantics: {sign: positive_remaining_amount, cutoff: report_date, date_field: due_date_contractual, missing_behavior: INCONCLUSIVE_FOR_NULL_DUE_DATE, zero_behavior: success_empty_is_verified_zero}
  trust: {state: PARTIAL}
  evidence: {supported: PARTIAL, evidence_ref_type: AI002_DOCUMENT_REF}
SALES_DECLINE:
  source: {source_kind: ERP_NEXT_REPORT, service_or_report: AI001 FinancialSnapshot / Profit and Loss Statement, DocType_if_any: null, runtime_verified: NO_CURRENT_CHECKOUT}
  scope: {company: server_verified_required, as_of: effective_end_date, period: current_and_equal_length_previous, currency: VND_label_unreconciled, finance_book: NOT_SUPPORTED}
  semantics: {sign: revenue_report_amount, cutoff: effective_end_date, date_field: report_period_end_date, missing_behavior: INCONCLUSIVE, zero_behavior: prior_zero_disables_relative_rule}
  trust: {state: PARTIAL_ACCOUNT_MAPPING}
  evidence: {supported: PARTIAL, evidence_ref_type: AI001_REPORT_CHECKSUM}
MARGIN_DROP:
  source: {source_kind: ERP_NEXT_REPORT, service_or_report: AI001 FinancialSnapshot / Profit and Loss Statement, DocType_if_any: null, runtime_verified: NO_CURRENT_CHECKOUT}
  scope: {company: server_verified_required, as_of: effective_end_date, period: current_and_equal_length_previous, currency: ratio_on_unreconciled_amounts, finance_book: NOT_SUPPORTED}
  semantics: {sign: gross_margin_ratio, cutoff: effective_end_date, date_field: report_period_end_date, missing_behavior: INCONCLUSIVE_IF_REVENUE_OR_COGS_MISSING, zero_behavior: revenue_zero_disables_ratio}
  trust: {state: PARTIAL_COGS_MAPPING}
  evidence: {supported: PARTIAL, evidence_ref_type: AI001_REPORT_CHECKSUM}
CASH_SHORTFALL:
  source: {source_kind: DERIVED_SERVICE, service_or_report: AI002 get_cash_forecast, DocType_if_any: GL Entry / Purchase Invoice / Sales Invoice, runtime_verified: UNIT_AND_OLD_FIXTURE_ONLY}
  scope: {company: server_verified_required, as_of: financial_as_of_EOD, period: following_30_calendar_days, currency: VND_ONLY, finance_book: NOT_SUPPORTED}
  semantics: {sign: modeled_cash_below_zero, cutoff: opening_GL_posting_date_and_event_eligibility, date_field: posting_date_and_confirmed_settlement_date, missing_behavior: FORECAST_UNAVAILABLE_IS_INCONCLUSIVE, zero_behavior: modeled_cash_zero_is_no_breach}
  trust: {state: BLOCKED_LIVE_FUTURE_SOURCE}
  evidence: {supported: PARTIAL, evidence_ref_type: AI002_DOCUMENT_REF}
```

Sign: AR/AP `remaining_amount` dương là exposure, revenue/COGS theo P&L parser, margin là ratio, modeled cash âm là breach. Với mọi source, `verified zero`, legitimate success-empty, missing mandatory field, permission denial, timeout, source exception và inconsistent/corrupt rows là các state khác nhau. Không chuyển một state sang state khác trong rule/UI.

## 8. Contract review (candidate envelope, chưa implement)

| Field | Verdict | Required change / evidence |
| --- | --- | --- |
| `signal_id` | NEEDS_CHANGE | Stable deterministic ID từ company scope + signal type + cutoff + rule version; không dùng random ID làm idempotency. |
| `signal_type` | SUPPORTED | Candidate vocabulary; chỉ publish type đã có source/rule. |
| `company` | SUPPORTED | Chỉ từ server-verified company; FORBIDDEN không trả company. |
| `as_of` | NEEDS_CHANGE | Tách accounting date, generated_at UTC, timezone; validate và replay test. |
| `snapshot_id` | NEEDS_CHANGE | AI001 và AI002 tự tạo ID riêng; thêm `source_snapshot_refs[]` có feature/contract/method/as_of; không tự nhận shared ID. |
| `status` | NEEDS_CHANGE | Tách signal finding (`TRIGGERED`/`BENIGN`/`INCONCLUSIVE`) khỏi source/coverage/error state; enum chưa freeze. |
| `severity` | NEEDS_CHANGE | Chỉ deterministic, nullable khi inconclusive; enum/rule severity chưa có. |
| `metric.metric_id` | SUPPORTED | AI001 IDs và AI002 shortfall type có sẵn; cần mapping versioned. |
| `metric.current_value` | NEEDS_CHANGE | Giá trị từ typed metric only; không float tùy ý, giữ decimal/string và status. |
| `metric.unit` | SUPPORTED | `currency_or_unit` AI001, `currency` AI002; phải validate nguồn. |
| `baseline.type/period/value` | NEEDS_CHANGE | AI001 PREVIOUS_PERIOD có, nhưng as_of/currency chưa đủ; hỗ trợ `NONE` và unavailable reason. |
| `rule.threshold` | NOT_SUPPORTED | Chưa có threshold business; AI002 zero breach không quyết định severity. |
| `rule.rule_version` | NOT_SUPPORTED | Chưa có AI003 rule registry/version. |
| `coverage.status/missing_inputs[]` | NEEDS_CHANGE | AI001 missing_inputs + AI002 coverage khác semantics; schema typed source states. |
| `evidence_refs[]` | NEEDS_CHANGE | Discriminated `REPORT_SNAPSHOT` vs `DOCUMENT`; auth mỗi lần truy cập, nguồn/bộ lọc/checksum. |
| `limitations[]` | SUPPORTED | Cả hai có, nhưng không đưa exception text nhạy cảm ra client. |
| `explanation.status/text` | NEEDS_CHANGE | AI001/AI002 shape khác; model fallback phải giữ signal; grounding/schema/version. |
| `next_checks[]` | NEEDS_CHANGE | AI002 có allowlist; AI003 cần action IDs + server permission, không arbitrary URL. |

Envelope còn cần `feature_id`, `contract_version`, `formula_version`/`method_version`, `correlation_id`, `data_mode`, `source_status`, `generated_at`, `accounting_timezone`, `finance_book`/scope (khi hỗ trợ), `comparison_snapshot_id`, `rule_inputs`/denominator/count. Chưa freeze tên enum.

## 9. Security investigation

| Boundary | Finding / gap |
| --- | --- |
| Authentication & company | Frappe `@frappe.whitelist()` mặc định yêu cầu login; `get_verified_company` kiểm tồn tại và Company read permission (`security/access.py:26-67`). Cần AI003 E2E với user hạn chế; không dùng `Administrator` làm chứng cứ phân quyền. |
| Report/resource | AI001 adapter có key registry và `check_report_permission`, nhưng nhận client `filters` gần như tự do (`api/key_reports.py:80-140`); AI003 không được expose generic extractor. AI002 `check_ai002_report_permission` dùng allowlist. |
| Tampering | AI003 phải resolve company server-side trước scope, allowlist signal/filter; từ chối report/DocType/URL tuỳ ý và cross-company evidence. Test filter `company`, ngày, Finance Book, account set, `signal_filter`. |
| Evidence | AI002 `get_ai002_evidence` gọi `get_verified_company` + `verify_evidence_access`; ref ngoài allowlist/khác company trả FORBIDDEN. AI001 report checksum chưa có authorized replay/drilldown. Không để FORBIDDEN lộ tên công ty/resource hoặc existence. |
| Cache/isolation | AI002 key chứa user/company/as_of/horizon/account scope/coverage/source mode/version (`cashflow/cache.py`), TTL 300s; `get_cash_forecast` validate trước cache. Chưa test AI003 cross-user/role, fixture/live, permission changes trong TTL; snapshot AI001 không cache. Không dùng shared cache thiếu auth. |
| Fixture/live | AI002 endpoint không nhận fixture flag; server test flags có thể chọn `SyntheticFixtureSource` (`api/ai_insights.py:390-413`). Cần xác minh flags không bật ở production và container checkout đồng bộ. |
| Logging | `key_reports.py:134` log `str(e)` từ source; AI001 snapshot limitations có error string; kiểm tra PII/error redaction trước AI003 reuse. |

Security verdict: guard primitives tồn tại, **AI003 boundary NOT_VERIFIED**. Không thực hiện pentest hay role-based live test trên shared site. Đây là G4A PARTIAL, không PASS.

## 10. Agent boundary

Candidate `get_risk_signals(company_scope_resolved_server_side, as_of, optional_signal_filter)` phải là một tool allowlisted, read-only, typed. Server xác thực user/company/resource, tính metric/rule, và chỉ trả authorized facts/evidence. Agent có thể hiểu ý định, gọi tool, sắp ưu tiên theo severity đã có, diễn giải và đưa next-check ID trong allowlist. Không raw SQL, generic report/DocType/URL, lấy company chỉ từ prompt, đổi severity/threshold, tạo số/signal, kết luận fraud/default/bankruptcy hoặc ghi transaction. AI001 `explanation.py` và AI002 `agent.py`/`tools.py`/`grounding.py` là framework sẵn có; chưa cần thêm framework. Model timeout/malformed/grounding fail chỉ làm `explanation=UNAVAILABLE`.

## 11. Evaluation, failure và temporal plan

| Source result / case | Metric state → signal state | Explanation → UI |
| --- | --- | --- |
| Valid positive | AVAILABLE → TRIGGERED theo versioned rule | Grounded hoặc unavailable → signal/evidence vẫn hiện. |
| Valid benign | AVAILABLE → BENIGN | Không hiện alert; có thể ghi trạng thái kiểm tra. |
| Success-empty xác thực / verified zero | ZERO_VERIFIED → BENIGN **chỉ nếu rule có denominator hợp lệ**; zero denominator → INCONCLUSIVE | Giải thích rõ zero và coverage; không bịa tỷ lệ. |
| Mandatory field missing / malformed rows | SOURCE_INVALID → INCONCLUSIVE | Data-quality banner; không alert và không “an toàn”. |
| No previous period / zero prior denominator | BASELINE_UNAVAILABLE → INCONCLUSIVE với rule delta | Không tính relative change. |
| Source timeout / exception | TIMEOUT/SOURCE_ERROR → INCONCLUSIVE | Generic error, retry; không gán zero. |
| Inconsistent rows / GL↔TB mismatch | INCONSISTENT_DATA → INCONCLUSIVE | Không forecast/signal giả. |
| Unauthorized company/resource / tampered filter | FORBIDDEN → không có signal payload | Generic FORBIDDEN, clear stale UI, không leak existence. |
| Historical `as_of` unsupported | UNSUPPORTED_CUTOFF → INCONCLUSIVE | Chặn replay, không dùng hiện tại thay quá khứ. |
| Model unavailable/timeout/malformed/grounding fail | Giữ nguyên deterministic metric/signal/severity | `explanation=UNAVAILABLE`, dùng approved static next checks; không xoá signal. |

Temporal oracle bắt buộc: tạo mỗi source một giao dịch có posting/date **sau** cutoff, tính lại signal cùng cutoff và so byte-level metric/rule input/evidence fingerprint (bỏ generated_at); không thay đổi. Áp dụng AR, AP, P&L sales/expense/margin, concentration, inventory và forecast nếu được chọn. Riêng backdated correction/cancellation: cần policy `as_known_at`/ledger snapshot, vì `posting_date <= as_of` đơn độc không khôi phục trạng thái “đã biết tại thời điểm cũ”. Chưa có live replay test: **NOT_VERIFIED**.

Fixture/gold đề nghị: transaction-backed fixture trên isolated site, `AI003_GOLD_MANIFEST.yaml` độc lập, với POSITIVE, BENIGN, INCONCLUSIVE cho từng signal chọn. Oracle tính tay hoặc script riêng từ vouchers/report rows đã khóa, không import AI003 engine; giữ `source_payload_hash`, period/cutoff/timezone, company/book/currency, expected metric/baseline/rule status/evidence IDs. Case bắt buộc: true trigger, gần threshold nhưng benign, missing, corrupt, zero denominator, future posting, cross-company, report denial, model failure. False positive theo từng signal = false alerts / verified benign cases; đo theo fixture và sau này adjudicated production labels, không invent statistical target. Chưa tạo gold manifest vì chưa có source/rule threshold được freeze.

Per-signal false-positive oracle (dùng ký hiệu `T_rule` cho threshold sẽ được phê duyệt, không gán trị số):

| Signal được đề nghị | True trigger | Benign gần ngưỡng | Missing / inconsistent | Historical cutoff | Cross-company |
| --- | --- | --- | --- | --- | --- |
| SALES_DECLINE | Current/prior revenue reconciled, delta vượt `T_rule` | Delta sát phía không-trigger của `T_rule` | Thiếu revenue row hoặc P&L totals không reconcile → inconclusive | Sales Invoice/GL sau cutoff không đổi metric; backdated edit được đánh dấu unsupported nếu không có as-known-at | Company B không vào P&L/report ref A |
| AR_OVERDUE_SPIKE | AR overdue/total hợp lệ hai kỳ và delta vượt `T_rule` | Delta sát phía không-trigger | Missing outstanding/due date, zero denominator hoặc summary/detail mismatch → inconclusive | Invoice/payment sau cutoff không đổi AR A tại cutoff | B row/ref hoặc unauthorized AR report → FORBIDDEN/inconclusive, không payload |
| AP_DUE_CLUSTER | Đủ AP rows due dates trong approved window, measure vượt `T_rule` | Cluster sát phía không-trigger | Null due date, malformed amount/voucher, conflicting rows → inconclusive | Future-posted AP không vào cutoff; due date sau cutoff chỉ là nghĩa vụ | B voucher không xuất hiện ở A; evidence drilldown bị từ chối |
| MARGIN_DROP (optional) | Revenue/COGS reconciled hai kỳ, margin delta vượt `T_rule` | Delta sát phía không-trigger | COGS mapping mơ hồ, revenue zero, P&L inconsistent → inconclusive | Future COGS/credit note không đổi historical margin | Không dùng P&L cross-company |

## 12. UX

Hai Frappe pages riêng hiện có: `financial-health` chứa KPI, comparison, explanation, evidence; `cash-forecast` chứa 30-day table, obligations, coverage và bounded copilot. AI003 nhiều signals phù hợp một page/workspace read-only riêng, link từ Financial Health/Cash Forecast; modal đơn giản khó chứa evidence, limitations và next checks. Dùng cùng company/as_of picker, badge trung tính cho inconclusive, severity badge chỉ từ server. Chuyển company phải clear data ngay và bỏ response cũ theo generation token như `cash_forecast.js:212-289`. UI không tính metric, threshold, severity, permission hay financial value. UI thực tế AI003 chưa có: NOT_VERIFIED.

## 13. Observability

`ai/observability.py:43-151` allowlist metadata, hash user/company, correlation ID; `log_ai002_event` có source status, coverage, model status, error class, count, latency. `log_event` feature allowlist chỉ AI001/AI002 nên AI003 cần mở rộng có kiểm soát. Chỉ log `correlation_id`, feature/contract/rule version, snapshot reference token nếu safe, signal type/status, source/coverage/model status, latency, allowlisted error class; không log raw rows, party/name, bank data, invoice text, prompt, secret, chain-of-thought. `snapshot_id`/rule version chưa được allowlist tại logger. Sink và retention chưa xác minh. AI001 `EVENT_METRIC_COMPUTED` truyền `value` vào `details` nhưng `_safe_details` drop; cần test end-to-end sink để chứng minh.

## 14. Performance và known risks

- AI001 một snapshot đọc 4 reports, PREVIOUS_PERIOD gọi lại 4 reports = tối đa 8 report calls theo code (`financial_snapshot.py:593-649,1007-1022`), chưa có latency measurement. AI002 thêm GL SQL + TB + AR + AP + scope, và cache riêng. Nếu gọi 10 signal độc lập sẽ nhân report reads. Đề nghị một authorized request context, một AI001 snapshot, một AI002 response khi cần, nhiều rule; không tuyên bố có shared snapshot hiện tại.
- AI001/AI002 `snapshot_id` được sinh độc lập. EvidenceRef không tương thích; formula/version phải propagate theo từng nguồn. Cache AI002 có TTL và không biết AI001 snapshot; nguy cơ stale/mixed cutoff.
- `cashflow/cache.py` single-flight key theo company/cutoff/source mode, không theo user/account scope, dù cache key có. Khi lock không acquire, service vẫn thực hiện computation; performance guarantee chưa có. Cache in-process; không đo hit/latency runtime.
- Container cũ hơn workspace, site timezone mismatch, approved cash scope fixture/migration hiện tại chưa xác minh, finance book/FX unsupported. Đây là blocker cho live P0.

## 15. Gate status và evidence ledger

| Gate | Status | Vì sao |
| --- | --- | --- |
| G1 Runtime | PARTIAL | Version/site/currency/timezone verified; container không khớp workspace, chưa có current endpoint/role runtime result. |
| G2 Contract | PARTIAL | AI001/AI002 shape có, nhưng AI003 severity/rule/baseline/evidence/as_of còn gap. |
| G3 Data & Method | BLOCKED | Chưa có threshold, temporal oracle, live future source; AI001 malformed→zero và P&L semantics cần xử lý. |
| G4A Pre-build Security/Evaluation | PARTIAL | Guards/unit tests và test design có; AI003 authorization, gold/role/cross-company/temporal E2E chưa chạy. |
| G4B | NOT_APPLICABLE_YET | Chưa build AI003. |

Evidence records cho các claim đã xác minh (mọi claim khác ở trên là code inspection hoặc NOT_VERIFIED):

| claim | code_path | test_file / test_name | environment | command | result | artifact |
| --- | --- | --- | --- | --- | --- | --- |
| Runtime version/app | `lotus_fin/hooks.py` | N/A (runtime inventory) | Docker site `frontend`, 2026-09-29 | `docker exec frappe_docker-backend-1 bench --site frontend list-apps` | 3 versions/app như §4 | terminal result; §4 |
| Timezone | `cashflow/models.py:ForecastResponse` | N/A (runtime inventory) | Docker site `frontend` | `bench --site frontend execute frappe.utils.get_system_timezone` | `Africa/Abidjan` | terminal result; §4 |
| Demo currency | `api/ai_insights.py` | N/A (runtime inventory) | Docker site `frontend` | `bench --site frontend execute frappe.db.get_value --args '["Company", "Name (Demo)", "default_currency"]'` | `VND` | terminal result; §4 |
| Current unit behavior | `ai/financial_snapshot.py`, `cashflow/service.py` | six test modules in §4 / unittest suite | Windows Python 3.13.7, workspace HEAD + dirty AI002 | `python -m unittest -q` on six named modules | 127 tests OK | terminal result; §4 (unit only) |
| AI001 malformed AR/AP→zero | `ai/financial_snapshot.py:parse_ar_data/parse_ap_data` | no existing dedicated test; controlled replay | Windows Python 3.13.7 | `python -c` calling both parsers with `[{"party":"X"}]` | AR `(0,0,0, limitation)`, AP `(0, limitation)` | terminal result; §5.1 |

## 16. Recommended P0 scope

**Không có production-ready signal hôm nay.** Sau khi giải quyết blockers, mục tiêu demo nhỏ nhất là: (1) `SALES_DECLINE` từ AI001 current/prior P&L đã reconcile; (2) `AR_OVERDUE_SPIKE` từ AR được fail-close và historical replay; (3) `AP_DUE_CLUSTER` từ AI002 obligation due dates, gắn nhãn contractual. Chỉ thêm `MARGIN_DROP` nếu COGS mapping theo chart được chứng minh và gold độc lập. `CASH_SHORTFALL` chỉ trong fixture demo ghi rõ synthetic; không đưa vào live P0 tới khi có verified confirmed settlement source và timezone đúng. Không mock sáu signal còn lại như production.

## 17. Open questions / blockers before contract freeze

1. Current container và workspace sẽ đồng bộ/migrate trên isolated site nào? Site đó có accounting timezone và approved cash account scope đúng không?
2. Chính sách company/Finance Book/currency/FX và so sánh kỳ nào được chủ sản phẩm/phòng tài chính phê duyệt? `as_of` nghĩa posting cutoff hay as-known-at time?
3. AI001 AR/AP malformed→zero và P&L account-name mapping được sửa/verified tại boundary nào? Ai sở hữu authoritative metric sau đó?
4. Threshold/severity (absolute/relative, denominator, observation count, close-to-threshold tolerance) được duyệt với SME user nào? Chưa thể gán severity từ sample.
5. Có source nào chứng minh confirmed future settlement để bật live `CASH_SHORTFALL`? Nếu không, giữ `FORECAST_UNAVAILABLE`.
6. Evidence report checksum được lưu/replay và reauthorize thế nào? AI003 `evidence_refs` phân biệt report/doc ra sao?
7. AI003 role/cross-company/filter/cache/stale-UI E2E và temporal future-posting test chạy trên isolated site khi nào?

## 18. Next action

Giữ contract ở draft. Đồng bộ isolated Frappe site với workspace, chạy migration/test AI002 hiện tại, khắc phục AI001 malformed source và cutoff/currency issues, thu thập chỉ số current/prior cùng oracle độc lập, rồi review thresholds và rule version với finance owner. Sau đó chạy role/temporal/fixture evaluation trước khi ChatGPT Chat quyết định freeze và giao build.

## Historical finding summary — SUPERSEDED by v2 reassessment below

VERIFIED
- Runtime version/app/site, timezone mismatch, demo VND; 127 local unit tests; AI001 malformed AR/AP row thành zero qua controlled replay.

NOT VERIFIED
- Current workspace trên live container, AI003 role/permission/cross-company E2E, historical replay, Finance Book/FX, rule threshold/severity, real SME baseline.

READY SIGNALS
- Không có.

CONDITIONAL SIGNALS
- `SALES_DECLINE`, `AR_OVERDUE_SPIKE`, `AP_DUE_CLUSTER`, `MARGIN_DROP` sau các gate riêng.

BLOCKED / P1 SIGNALS
- `CASH_SHORTFALL` live blocked; `CUSTOMER_CONCENTRATION`, `SUPPLIER_CONCENTRATION`, `EXPENSE_SPIKE`, `INVENTORY_CASH_LOCK`, `COLLECTION_DELAY` P1/not ready.

REUSED AI001 COMPONENTS
- Candidate `revenue`, `gross_margin`, `overdue_ar_ratio`, comparison và report EvidenceRef; chưa approved authoritative cho AI003.

REUSED AI002 COMPONENTS
- Candidate `obligations`, `shortfall_events`, coverage, typed errors, evidence authorization, cache isolation; future source live chưa có.

SECURITY FINDINGS
- Company/report/doc guards tồn tại; AI003 boundary và generic filter/cache/role isolation chưa được verify; AI001 raw source error text cần redaction review.

DATA FINDINGS
- AR/AP malformed→zero; P&L tên tài khoản, currency/Finance Book và historical distribution chưa được chứng minh.

TEMPORAL / AS_OF FINDINGS
- AI001 previous snapshot gọi với `as_of=None` nhưng lọc `prev_end`; future/backdated/cancelled transaction tests chưa có; site timezone lệch contract.

FIXTURE / GOLD FINDINGS
- AI002 fixture/gold chỉ là kỹ thuật; AI003 independent oracle và 3 trạng thái cho mỗi signal chưa xây vì rule/source chưa freeze.

UX FINDINGS
- Nên dùng page riêng với evidence/coverage và server-generated severity; tận dụng stale-response guard của cash forecast.

OBSERVABILITY FINDINGS
- Structured log allowlist hiện chỉ AI001/AI002; AI003 metadata/sink/retention chưa verify.

G1: PARTIAL
G2: PARTIAL
G3: BLOCKED
G4A: PARTIAL
G4B: NOT_APPLICABLE_YET

BLOCKERS BEFORE CONTRACT FREEZE
1. Source trust và historical cutoff (AI001 malformed→zero, P&L mapping, previous `as_of`).
2. Threshold/severity/denominator được phê duyệt và independent gold.
3. Isolated runtime đồng bộ, timezone, Finance Book/currency, role/security/temporal tests.
4. Live future settlement source nếu muốn `CASH_SHORTFALL` production.

RECOMMENDED P0
- Sau gates: `SALES_DECLINE`, `AR_OVERDUE_SPIKE`, `AP_DUE_CLUSTER`; `MARGIN_DROP` chỉ nếu COGS verified.

RECOMMENDED NEXT ACTION
- Chạy remediation + isolated fixture oracle, rồi trình evidence cho ChatGPT Chat quyết định contract freeze; chưa giao implement AI003.

## 19. Historical v2 reassessment control and exact delta — superseded by §29

Evidence labels trong §19–28: **OBSERVED** = phép chạy hiện tại; **DERIVED** = suy từ mã/contract hiện tại, chưa phải runtime PASS; **PROPOSED** = thiết kế chưa phê duyệt; **NOT_VERIFIED** = chưa đủ chứng cứ. Feature spec v2 là yêu cầu sản phẩm, không là bằng chứng implementation.

| SPEC CHANGE v1 → v2 | CURRENT CODE SUPPORT | RUNTIME SUPPORT | AI003 IMPACT | STATUS |
| --- | --- | --- | --- | --- |
| AI001 từ vài candidate metrics thành 22 KPI thuộc profitability, liquidity, working capital, cash flow, leverage | 7 core metric cũ + `near_term_ap` UNAVAILABLE; chỉ 5 KPI v2 có một phần code; không có standardized KPI registry | AI001 demo hiện trả current `revenue/cogs/gross_margin/AR/AP/cash` AVAILABLE, nhưng previous revenue/COGS/margin UNAVAILABLE | Không được map KPI v2 chưa implemented sang signal hoặc coi `status=AVAILABLE` là trustworthy | OBSERVED + DERIVED; v2 specification PROPOSED |
| Metric envelope AI001 thêm `metric_name/category`, `unit`, `currency`, `comparison_period`, `data_source`, `data_quality_status` | Chỉ có `metric_id/value/currency_or_unit/period/formula_version/snapshot_id/evidence_refs/limitations`; comparison nằm block riêng | Runtime contract `1.0.0` vẫn là schema cũ | AI003 cần adapter versioned hoặc AI001 v2 contract; không tự gắn nhãn category/quality từ prompt | OBSERVED |
| AI002 thêm 7 `cash_metrics[]` | `ForecastResponse` có `forecast_points`/`shortfall_events`, không có `cash_metrics`; 3 KPI có thể suy một phần từ series/event nhưng chưa là metric contract | Container AI002 khác checksum commit và thiếu migration, nên current code runtime NOT_VERIFIED | Không gọi AI002 KPI layer là authoritative; chỉ dùng typed forecast output có gate | DERIVED + OBSERVED runtime mismatch |
| AI003 thêm `metric_id/category`, `change_value/pct`, `threshold_type`, `unit`, `comparison_period`; bỏ `as_of` khỏi candidate list | Không có AI003 service; AI001/AI002 có 2 snapshot IDs độc lập và evidence khác dạng | Không có AI003 runtime | Phải **giữ `as_of`/timezone** trong production contract dù v2 list bỏ; đổi field cần provenance và validation | PROPOSED |
| V2 AI-F102 thêm revenue CAGR/concentration, AI-F104 thêm turnover/DIO | Chưa có các KPI này trong current AI001/AI002 code | NOT_VERIFIED | `CUSTOMER_CONCENTRATION`, `INVENTORY_CASH_LOCK` vẫn P1 | DERIVED |

## 20. Runtime alignment after commit `030ccc3`

| Claim | Evidence hiện tại | Kết luận |
| --- | --- | --- |
| Git | `git rev-parse HEAD` = `030ccc3c46bd6e22443c1a008818954829a6ec3b`; `git status` không có tracked modification, chỉ tài liệu/video untracked | OBSERVED; nhận biết commit mới của user. |
| Container versions/site | `docker exec frappe_docker-backend-1 bench --site frontend list-apps`: Frappe 16.34.0, ERPNext 16.35.0, Lotus Fin 0.0.1; site `frontend` | OBSERVED. |
| Container checkout | Container app không có `.git`; SHA256 `ai/financial_snapshot.py` khớp workspace (`fa9d62...`), nhưng `cashflow/service.py` và `api/ai_insights.py` khác; `test_cashflow_failclosed.py` không tồn tại trong container | OBSERVED. Không dùng container AI002 để claim current commit runtime PASS. |
| Migration | Read-only `frappe.db.has_column('Company','ai002_approved_cash_accounts')` trả false; control check `Company.name` trả true. `AI002 Fixture 2026` còn tồn tại. | OBSERVED; approved cash-scope config từ commit chưa migrate trên site. Không chạy migrate trên shared site. |
| Timezone / Finance Book | `frappe.utils.get_system_timezone` = `Africa/Abidjan`; `Company.default_finance_book` field tồn tại nhưng `Finance Book` count = 0; API/filter code không truyền Finance Book | OBSERVED schema/site; book semantics NOT_VERIFIED. AI002 contract timezone `Asia/Ho_Chi_Minh` chưa được triển khai ở site. |
| Company/currency | `Name (Demo).default_currency=VND`. AI001 live request `currency=USD` trả response/`revenue` AVAILABLE gắn `USD`; source filters không có FX conversion hoặc requested currency validation | OBSERVED label mismatch; không được coi money KPI là đúng currency cho AI003. Không in financial amount trong phép thử. |
| Fixture flags | Endpoint hiện tại chỉ bật SyntheticFixtureSource theo server test flags; fresh CLI context không chứng minh trạng thái web workers | DERIVED + NOT_VERIFIED. Cần kiểm tra deployed flags trên isolated site. |
| Graph | `impact build_financial_snapshot`: 1 caller `get_financial_snapshot`, risk LOW; `impact get_verified_company`: 7 callers, risk MEDIUM; `get_cash_forecast`: UNKNOWN/not indexed. Index sau HEAD 10 commit và lần rebuild trước lỗi worker startup. | OBSERVED nhưng stale: không coi UNKNOWN/LOW là current all-clear; code text đối chiếu. |

Sanitized AI001 live call (Administrator, demo company, 2020-01-01..2020-12-31, `as_of=2020-12-31`, rollback sau gọi): top status `OK`; current `revenue`, `cogs`, `gross_margin`, `ar_outstanding`, `overdue_ar_ratio`, `ap_outstanding`, `cash_balance` đều AVAILABLE; `near_term_ap` UNAVAILABLE. `comparison.status=AVAILABLE`, nhưng previous `revenue/cogs/gross_margin/cash_balance` UNAVAILABLE, AR/AP và overdue ratio AVAILABLE. **OBSERVED**: comparison block AVAILABLE không bảo đảm từng KPI so sánh có baseline. Không có live role-limited/AI003 call.

Local current commit test: `python -m unittest -q lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_financial_health lotus_fin.tests.test_explanation lotus_fin.tests.test_cashflow_engine lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed` → **127 tests OK** (Python 3.13.7; unit/mocks, không là site E2E). Test hiện tại chưa cover v2 KPI registry, currency-label attack, AI003 temporal/role/gold.

## 21. V2 KPI implementation reality

Code states `IMPLEMENTED` nói có phép tính và output hiện tại, **không** nói trustworthy. `PARTIALLY_IMPLEMENTED` là chỉ có comparison/series/event hoặc thiếu named KPI contract. `NOT_IMPLEMENTED` là không có formula service/output. Mọi KPI dưới đây đều `DEFINED_IN_SPEC`; v2 chỉ nêu tên cho vài KPI mà chưa chốt công thức chi tiết.

Reusable source profiles cho bảng KPI:

| Profile | code_path / service/API / formula | source + fields + period/as_of | currency/book/evidence/permission/tests/runtime |
| --- | --- | --- | --- |
| P&L | `ai/financial_snapshot.py:parse_pnl_data/build_financial_snapshot`, `ai/financial_health.py:compute_metric_change`; `api/ai_insights.py:get_financial_snapshot`; gross margin `(revenue−COGS)/revenue` khi revenue>0 | ERPNext Profit and Loss Statement; `account_name/account`, `total/amount/balance/net_amount`; current `period_start..min(period_end,as_of)`; previous equal-length period từ original period, `as_of=None` nhưng report cutoff `prev_end`. Account-name heuristic, không có operating expense/net income extraction. | Currency do request gắn nhãn, USD-on-VND đã observed; Finance Book filter absent; report checksum metadata; Company+Report check; `test_financial_snapshot`, `test_financial_health`; live current P&L available, previous P&L unavailable. |
| AR | `financial_snapshot.py:parse_ar_data`; AR outstanding=sum, overdue ratio=overdue/total hoặc 0 khi total<=0 | Accounts Receivable report; `outstanding` aliases, `overdue_amount/overdue` hoặc `due_date`; point-in-time `report_date=effective_end`; previous separate report. Malformed/missing amount bị bỏ qua thành apparent zero. | Cùng currency/book/evidence/permission như P&L; live current/previous AVAILABLE nhưng numeric trust BLOCKED; `test_financial_snapshot` không phát hiện malformed→zero. |
| AP | `financial_snapshot.py:parse_ap_data`; AP outstanding=sum | Accounts Payable report; `outstanding` aliases; `report_date=effective_end`; previous separate report. Missing amount có thể thành zero. `near_term_ap` UNAVAILABLE. | Cùng currency/book/evidence/permission như P&L; live current/previous AVAILABLE nhưng numeric trust BLOCKED. |
| Forecast | `cashflow/engine.py:compute_forecast`, `cashflow/service.py:get_cash_forecast`, API `get_ai002_cash_forecast`; EOD cash=opening+eligible inflows−outflows; technical breach `<0` | GL opening + Trial Balance reconcile, AR/AP obligations, confirmed future events; `financial_as_of` EOD and following 30 dates; `forecast_points`/`shortfall_events`, no named `cash_metrics`. | VND-only validation; `finance_book` model-only; doc ref path, top-level `ForecastResponse.evidence_refs` mặc định `[]` và service không populate; Company/Account/report guards; `test_cashflow_*` unit 127-suite; current runtime NOT_VERIFIED vì container/migration mismatch. |

| AI001 KPI v2 | Code state | Formula/source profile | Runtime support | Trust / AI003 usage |
| --- | --- | --- | --- | --- |
| Revenue Growth Rate | PARTIALLY_IMPLEMENTED | P&L comparison `relative_change=(current−prior)/abs(prior)`; **khác** spec `(current−prior)/prior` khi prior âm | Previous revenue UNAVAILABLE on demo | BLOCKED; baseline/formula semantics phải thống nhất |
| Gross Profit Margin | IMPLEMENTED | P&L `gross_margin` ratio; v2 unit `%` nhưng code unit `ratio` | Current AVAILABLE, previous UNAVAILABLE | PARTIAL; account mapping/currency/cutoff |
| Operating Profit Margin | NOT_IMPLEMENTED | Chưa có operating profit/expense metric; spec nêu tên | No output | NOT_READY |
| Net Profit Margin | NOT_IMPLEMENTED | Chưa có net income metric | No output | NOT_READY |
| Current Ratio | NOT_IMPLEMENTED | Current assets/liabilities chưa có typed metric | No output | NOT_READY |
| Quick Ratio | NOT_IMPLEMENTED | Cash/AR/investments/current liabilities chưa có cùng scope | No output | NOT_READY |
| Cash Ratio | NOT_IMPLEMENTED | Cash/current liabilities chưa có verified denominator | No output | NOT_READY |
| AR Outstanding | IMPLEMENTED | AR profile, `ar_outstanding` | Current+previous AVAILABLE | BLOCKED malformed→zero/currency |
| Overdue AR Ratio | IMPLEMENTED | AR profile, `overdue_ar_ratio` | Current+previous AVAILABLE | BLOCKED malformed→zero/zero denominator |
| DSO | NOT_IMPLEMENTED | Average AR + net credit sales absent | No output | NOT_READY |
| AP Outstanding | IMPLEMENTED | AP profile, `ap_outstanding` | Current+previous AVAILABLE | BLOCKED malformed→zero/currency |
| DPO | NOT_IMPLEMENTED | Average AP + credit purchases absent | No output | NOT_READY |
| DIO | NOT_IMPLEMENTED | Average inventory + verified COGS absent | No output | NOT_READY |
| CCC | NOT_IMPLEMENTED | DIO+DSO−DPO unavailable | No output | NOT_READY |
| Operating Cash Flow | NOT_IMPLEMENTED | Cash Flow report trong registry, nhưng không có KPI parser/output | No output | NOT_READY |
| Operating Cash Flow Ratio | NOT_IMPLEMENTED | OCF/current liabilities unavailable | No output | NOT_READY |
| Free Cash Flow | NOT_IMPLEMENTED | OCF−CapEx unavailable | No output | NOT_READY |
| Net Cash Burn | NOT_IMPLEMENTED | Không có period cash burn metric | No output | NOT_READY |
| Cash Runway | NOT_IMPLEMENTED | Cash/burn inputs và denominator policy chưa có | No output | NOT_READY |
| Debt-to-Equity | NOT_IMPLEMENTED | Debt/equity typed metrics absent | No output | NOT_READY |
| Debt Ratio | NOT_IMPLEMENTED | Debt/asset typed metrics absent | No output | NOT_READY |
| Interest Coverage | NOT_IMPLEMENTED | EBIT/interest expense typed metrics absent | No output | NOT_READY |

| AI002 KPI v2 | Code state | Formula/source profile | Runtime support | Trust / AI003 usage |
| --- | --- | --- | --- | --- |
| Projected Ending Cash | PARTIALLY_IMPLEMENTED | Forecast profile; last `forecast_points[].modeled_cash`, no `cash_metrics` ID | Current commit NOT_VERIFIED; old container not aligned | BLOCKED live future source/deployment |
| Minimum Cash Balance | PARTIALLY_IMPLEMENTED | Forecast profile; min series/`minimum_modeled_cash` only in shortfall event; opening vs horizon semantics need contract | NOT_VERIFIED | BLOCKED; no named KPI/evidence |
| Cash Shortfall Amount | PARTIALLY_IMPLEMENTED | Forecast profile; negative `minimum_modeled_cash` in technical event, no positive amount KPI | NOT_VERIFIED | BLOCKED; amount sign/coverage chưa chuẩn |
| Net Cash Burn | NOT_IMPLEMENTED | No period burn calculation | No output | NOT_READY |
| Cash Runway | NOT_IMPLEMENTED | No burn/runway rule | No output | NOT_READY |
| Operating Cash Flow | NOT_IMPLEMENTED | No OCF calculation | No output | NOT_READY |
| Free Cash Flow | NOT_IMPLEMENTED | No OCF/CapEx calculation | No output | NOT_READY |

Controlled replay trên current code: `compute_metric_change(-50,-100)` trả `relative_change=+0.5`; công thức v2 `(−50−(−100))/(−100)` là `−0.5`. `compute_metric_change(20,0)` trả `status=AVAILABLE` nhưng `relative_change=None` + limitation. **OBSERVED** unit diagnostic; cần quyết định sign/zero policy trước khi chuẩn hóa Revenue Growth Rate.

## 22. KPI trust matrix for AI003

Legend `Y` có bằng chứng phù hợp; `P` mới có một phần; `N` thiếu/không đúng; `NV` chưa kiểm chứng. `formula_defined` xét v2 hoặc code; `source_verified` là current source path có runtime, không đồng nghĩa field semantics. `permission_verified=P` nghĩa có code/unit guard nhưng chỉ live Administrator; `gold_verified=N` nghĩa chưa có oracle độc lập cho standardized KPI v2. **Không có `AI003_authoritative_input=YES`.**

| metric_id | metric_category | formula_defined | code_implemented | source_verified | field_semantics_verified | as_of_verified | comparison_verified | currency_verified | Finance_Book_verified | permission_verified | evidence_verified | gold_verified | status | AI003_authoritative_input |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| revenue_growth_rate | profitability | Y | P | P | P | P | N | N | N | P | P | N | BLOCKED | NO |
| gross_profit_margin | profitability | Y | Y | P | P | P | N | N | N | P | P | N | BLOCKED | NO |
| operating_profit_margin | profitability | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| net_profit_margin | profitability | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| current_ratio | liquidity | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| quick_ratio | liquidity | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| cash_ratio | liquidity | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| ar_outstanding | working_capital | Y | Y | P | N | P | P | N | N | P | P | N | BLOCKED | NO |
| overdue_ar_ratio | working_capital | Y | Y | P | N | P | P | N | N | P | P | N | BLOCKED | NO |
| dso | working_capital | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| ap_outstanding | working_capital | Y | Y | P | N | P | P | N | N | P | P | N | BLOCKED | NO |
| dpo | working_capital | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| dio | working_capital | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| ccc | working_capital | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| operating_cash_flow_ai001 | cash_flow | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| operating_cash_flow_ratio | cash_flow | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| free_cash_flow_ai001 | cash_flow | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| net_cash_burn_ai001 | cash_flow | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| cash_runway_ai001 | cash_flow | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| debt_to_equity | leverage | Y | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| debt_ratio | leverage | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| interest_coverage | leverage | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| projected_ending_cash | forecast | Y | P | N | P | P | N | P | N | P | N | N | BLOCKED | NO |
| minimum_cash_balance | forecast | P | P | N | P | P | N | P | N | P | N | N | BLOCKED | NO |
| cash_shortfall_amount | forecast | P | P | N | P | P | N | P | N | P | N | N | BLOCKED | NO |
| net_cash_burn_ai002 | forecast | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| cash_runway_ai002 | forecast | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| operating_cash_flow_ai002 | forecast | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |
| free_cash_flow_ai002 | forecast | P | N | N | N | N | N | N | N | N | N | N | NOT_READY | NO |

Metric IDs trong matrix là **proposed mapping names**, trừ các ID trùng current output (`ar_outstanding`, `overdue_ar_ratio`, `ap_outstanding`). Chưa có registry chuẩn hóa các ID v2. Duplicate OCF/FCF/runway entries ghi rõ feature owner vì hai feature cùng liệt kê nhưng đều chưa implement; không tạo hai financial truth engines.

## 23. Old blockers revisited: reproduction and remediation target

| Previous finding → v2 reassessment | Current evidence | Affected KPI/signal | Verdict / remediation proposal |
| --- | --- | --- | --- |
| Malformed AR/AP row → zero | **OBSERVED** current commit controlled replay: `status=success,data=[{"party":"X"}]` → `ar_outstanding`, `overdue_ar_ratio`, `ap_outstanding` đều `AVAILABLE=0`. | AR Outstanding, Overdue AR Ratio, AP Outstanding; `AR_OVERDUE_SPIKE`, `AP_DUE_CLUSTER` nếu reuse AI001 AP. | STILL OPEN. AI001 adapter cần typed validation trước parser; malformed row làm source INVALID, không zero. |
| Unknown report status, missing `data` → zero | **OBSERVED** `status=mystery,data=[]` và `status=success` không có `data` đều → cùng `AVAILABLE=0`; legitimate `status=success,data=[]` cũng → zero. Diagnostic thêm P&L/TB hợp lệ cùng AR/AP `status=mystery` + malformed row → top snapshot `OK`, AR/AP `AVAILABLE=0`. | Cùng KPI AR/AP | STILL OPEN. Chỉ `success` + `data` list hợp lệ + company/currency/cutoff confirmed mới cho zero. AI002 adapter đã có strict parser riêng nhưng chưa là AI001 authoritative output. |
| Historical current/previous | **OBSERVED** stub fetcher: `as_of=2026-09-15` current P&L `2026-09-01..15`, prior P&L `2026-08-02..31`; AR report dates `09-15`, `08-31`. **OBSERVED** `as_of=2026-08-15` trước period start vẫn trả PARTIAL và tạo P&L `2026-09-01..2026-08-15`; invalid `2026-13-01` bị bỏ qua, dùng `2026-09-30`. | Revenue Growth, margin, AR/AP deltas; sales/margin/AR signals | STILL OPEN. Validate full date, `period_start <= as_of <= period_end` theo policy; align prior window với effective current window; reject unsupported historical semantics. |
| Future posting / backdated / cancelled | Filter code dùng posting/report date; chưa tạo giao dịch đối chứng tại site hiện tại. `as_of` là posting-date cutoff, không có `as_known_at` snapshot state để replay backdated edit. | Tất cả signal historical | NOT_VERIFIED. Isolated transaction-backed test: future posting không đổi historical output; backdated/cancelled được policy rõ (restate vs as-known-at). Không claim temporal PASS từ stub. |
| P&L mapping | **DERIVED** `parse_pnl_data` tìm `income/revenue/sales`, `cost of goods sold/cogs/giá vốn` bằng account-name heuristic (`financial_snapshot.py:108-233`); không dùng `root_type/account_type`/chart mapping để xác nhận revenue/COGS; không extract operating expense/profit/net income. Live current AVAILABLE nhưng không chứng minh đúng mapping; prior revenue/COGS/margin UNAVAILABLE. | Gross Profit Margin, Revenue Growth, Operating/Net Margin; `SALES_DECLINE`, `MARGIN_DROP`, `EXPENSE_SPIKE` | STILL OPEN. Reconcile ERPNext account semantics per company/chart, define sign and report row hierarchy, independent numeric gold. |
| Currency / FX | **OBSERVED** demo company VND, request USD nhưng AI001 revenue AVAILABLE unit USD. **DERIVED** AI001 filters không có FX step; `currency` được gắn lên metric. | Money KPI AI001 và signal derived | STILL OPEN, stronger evidence than old report. Server-enforce company/report currency or verified FX conversion with rate/date/version, then regression test mismatch. |
| Finance Book | **OBSERVED** Company có `default_finance_book` field nhưng site Finance Book count 0. **DERIVED** AI001 report filters không truyền Finance Book; AI002 request dataclass có `finance_book`, API/adapter không dùng. | Mọi accounting KPI/signal | STILL OPEN. Scope explicit/default policy + end-to-end filter/gold test; không suy no books trên demo thành universally safe. |
| Container alignment / migration | **OBSERVED** AI002 checksums khác commit; approved cash-scope column absent. | AI002 projected cash/shortfall, AP obligations, `CASH_SHORTFALL`, `AP_DUE_CLUSTER` | STILL OPEN. Đồng bộ code/migrate chỉ trên isolated site; không lấy old container test làm current proof. |

No old blocker được đánh dấu RESOLVED cho AI003. AI002 **code-level** fail-closed AR/AP và per-account TB là tiến bộ đã commit, nhưng deployment, source completeness và security E2E của AI003 chưa xác minh.

## 24. Standardized KPI → all 10 AI003 signals; P0 challenge

`primary_metric_id` và supporting IDs ở đây là mapping **PROPOSED**; chỉ `ar_outstanding`, `overdue_ar_ratio`, `ap_outstanding`, `revenue`, `gross_margin`, `cogs` là current AI001 output IDs. `authoritative_input=NO` cho toàn bộ vì trust matrix §22.

| signal_type | primary_metric_id | supporting_metric_ids[] | source_feature | authoritative_input | baseline_supported | threshold_ready | gold_ready | recommended | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AR_OVERDUE_SPIKE | overdue_ar_ratio | ar_outstanding | AI001 | NO | PARTIAL | NO | NO | CONDITIONAL | Current/prior available runtime, nhưng malformed→zero, currency/cutoff/gold chưa đạt. |
| AP_DUE_CLUSTER | ap_due_window_amount (new, not implemented) | ap_outstanding | AI002 | NO | NO | NO | NO | CONDITIONAL | AI002 strict obligations có due_date code, nhưng current container/migration không aligned; window baseline/rule chưa có. |
| CUSTOMER_CONCENTRATION | customer_exposure_share (new) | ar_outstanding, revenue | P1 | NO | NO | NO | NO | P1 | Party denominator/identity và AR-vs-sales meaning chưa frozen. |
| SUPPLIER_CONCENTRATION | supplier_exposure_share (new) | ap_outstanding | P1 | NO | NO | NO | NO | P1 | AP exposure khác spend; no aggregate contract. |
| MARGIN_DROP | gross_profit_margin (mapped to current gross_margin) | revenue, cogs | AI001 | NO | NO | NO | NO | P1 | Prior P&L metrics UNAVAILABLE live; COGS heuristic/currency. **Demoted from old conditional P0.** |
| EXPENSE_SPIKE | operating_expense (new) | operating_profit_margin | unavailable | NO | NO | NO | NO | P1 | Không có OPEX/operating profit KPI; raw P&L report không đủ. |
| SALES_DECLINE | revenue_growth_rate (comparison only) | revenue | AI001 | NO | NO | NO | NO | P1 | Prior revenue UNAVAILABLE live; negative prior denominator formula conflict/currency. **Demoted from old conditional P0.** |
| INVENTORY_CASH_LOCK | dio (not implemented) | inventory_turnover, cash_balance | P1 | NO | NO | NO | NO | P1 | v2 nêu DIO nhưng inventory average/COGS mapping/cutoff chưa có. |
| CASH_SHORTFALL | cash_shortfall_amount (event only) | projected_ending_cash, minimum_cash_balance | AI002 | NO | NO | NO | NO | BLOCKED | Confirmed future event production source chưa có; deployment/timezone/evidence gaps. |
| COLLECTION_DELAY | actual_collection_lag (not implemented) | dso | unavailable | NO | NO | NO | NO | P1 | DSO là receivables/sales proxy, **không bằng** actual payment delay. |

**Smallest credible P0 today: zero READY signals; không freeze.** Sau remediation, thử nghiệm đầu tiên nên giới hạn tối đa `AR_OVERDUE_SPIKE` và `AP_DUE_CLUSTER` để có hai chiều receivable/payable. Đây là **CONDITIONAL** và có thể giảm còn một hoặc không nếu oracle/source không đạt. Không có KPI v2 mới nào hiện đủ evidence để thay thế. `SALES_DECLINE`/`MARGIN_DROP` chỉ quay lại P0 khi prior P&L numeric gold, currency và account mapping được xác minh; không giữ vì danh sách cũ.

Threshold/severity readiness cho bốn hypothesis cũ (không đặt giá trị):

| Signal | Absolute | Relative/prior | Rolling | Minimum denominator/count | Zero denominator / near-threshold | Result |
| --- | --- | --- | --- | --- | --- | --- |
| AR_OVERDUE_SPIKE | Có thể trên overdue ratio nhưng business basis NV | Prior runtime AVAILABLE nhưng historical/trust chưa đạt | NV | Total AR >0; minimum row count NV | Total AR=0 → inconclusive cho ratio; tolerance NV | Threshold và severity NOT_VERIFIED |
| AP_DUE_CLUSTER | Có thể trên amount/count trong window | Prior chưa có | NV | Total eligible AP, count và missing due-date policy NV | Empty success có thể verified zero; tỷ lệ với total AP=0 undefined; tolerance NV | Threshold và severity NOT_VERIFIED |
| SALES_DECLINE | Có thể trên absolute revenue change | Prior live UNAVAILABLE; negative/zero prior formula conflict | NV | Prior revenue/observation count NV | Prior=0 → relative undefined; tolerance NV | Demoted, NOT_VERIFIED |
| MARGIN_DROP | Có thể trên margin-point change | Prior live UNAVAILABLE | NV | Revenue>0 và COGS mapping verified; count NV | Revenue=0 → margin undefined; tolerance NV | Demoted, NOT_VERIFIED |

Metric formula ≠ signal trigger threshold ≠ severity threshold. AI002 technical `<0` breach không tự định nghĩa AI003 severity. Chưa có approved finance-owner basis, near-threshold tolerance hay distribution dataset.

## 25. Candidate AI003 contract v2 review (không freeze)

| Field | Verdict | Reason/change |
| --- | --- | --- |
| `signal_id` | NEEDS_CHANGE | Stable deterministic ID, idempotency + rule/source version; current code không có. |
| `company` | SUPPORTED_IN_PRIMITIVE | Resolve/authorize server-side; FORBIDDEN payload omit company. AI003 endpoint chưa có. |
| `signal_type` | NEEDS_CHANGE | Allowlist chỉ cho implemented/trusted signals; unknown filter generic deny. |
| `severity` | NOT_SUPPORTED | Rule/severity policy chưa frozen; nullable cho inconclusive, LLM không quyết định. |
| `status` | NEEDS_CHANGE | Tách finding state khỏi source/coverage/model state; không dùng KPI AVAILABLE làm signal TRIGGERED. |
| `metric_id` | PARTIAL | AI001 legacy IDs, AI002 no cash_metrics; v2 registry missing. |
| `metric_name` | NOT_SUPPORTED | Legacy metric không có; approved localization/name map cần version. |
| `metric_category` | NOT_SUPPORTED | Legacy metric không có; v2 taxonomy chưa code. |
| `baseline_value` | PARTIAL | AI001 comparison có previous value theo metric, nhưng live P&L unavailable và temporal chưa verify. |
| `current_value` | PARTIAL | AI001 numeric output có; trust/currency blockers; decimal serialization cần thống nhất. |
| `change_value` | PARTIAL | AI001 comparison `absolute_change` có, không cùng schema. |
| `change_pct` | PARTIAL | AI001 `relative_change` ratio, v2 `%` conversion/sign/zero policy chưa chốt. |
| `threshold` | NOT_SUPPORTED | Business rule threshold chưa có. |
| `threshold_type` | NOT_SUPPORTED | Absolute/relative/window semantics chưa versioned. |
| `unit` | NEEDS_CHANGE | AI001 `currency_or_unit`, AI002 `currency`; USD label mismatch. |
| `comparison_period` | PARTIAL | AI001 `comparison.previous_period`, không per-metric và không valid cho mọi metric. |
| `rule_version` | NOT_SUPPORTED | AI003 rule registry chưa có. |
| `evidence_refs` | NEEDS_CHANGE | AI001 report checksum vs AI002 doc refs/empty top-level; type/authorization required. |
| `as_of` (v2 list omitted) | REQUIRED_ADDITION | Accounting cutoff + timezone bắt buộc; không được bỏ khỏi production schema. |
| `feature_id`, `contract_version`, `correlation_id` | REQUIRED_ADDITION | Provenance/API evolution; AI001/AI002 có các dạng này. |
| `source_snapshot_refs`, `source_status`, `coverage_status`, `missing_inputs` | REQUIRED_ADDITION | Separate source lineage, quality/failure, no false benign. |
| `limitations`, `generated_at`, `accounting_timezone`, `data_mode` | REQUIRED_ADDITION | Explain trust/temporal/fixture; versions & timestamps riêng. |

Enum cho severity/status/threshold_type là PROPOSED/NOT_VERIFIED; không freeze theo text v2. Contract phải có `formula_version`/`method_version`, denominator/count khi dùng ratio, và scope của currency/Finance Book để so current/baseline nhất quán.

## 26. Source snapshot reuse and evidence compatibility

**PROPOSED** request context: authenticate → verify company/role + exact KPI/signal allowlist → normalize cutoff/currency/book → get one authorized AI001 KPI snapshot and only when needed one AI002 forecast/obligation response → validate status/lineage → deterministic AI003 rules. AI003 không chạy riêng lại P&L/AR/AP formula. **Current reality:** AI001 generates `SNAP-...` per call; previous comparison has `previous_snapshot_id`; AI002 independently generates its own `SNAP-...` plus `forecast_id`. Không có shared snapshot ID, immutable snapshot storage hoặc atomic cross-feature read. Same company/cutoff/currency/book chưa thể bảo đảm vì AI001 accepts arbitrary currency, AI002 VND-only, book unhandled. Cache AI002 300s tạo thêm mixed-freshness risk.

| Evidence kind proposed | Existing support | Authorization + scope/version gap | AI003 treatment |
| --- | --- | --- | --- |
| `REPORT_SNAPSHOT` | AI001 `generate_evidence_ref`: source_name, company, filters, as_of, retrieved_at, 16-hex checksum; metric links checksum | Report permission checked khi đọc; không có persistent payload/replay hoặc dedicated reauthorize checksum drilldown; version không bao gồm immutable report data | PARTIAL; chỉ reference metadata, không invent drilldown. |
| `DOCUMENT_REF` | AI002 obligation `source_ref=DocType:name`; `get_ai002_evidence` + `verify_evidence_access` allowlist/read/company check | Top-level `ForecastResponse.evidence_refs` mặc định `[]`, `service.py` không populate; nguồn ref trong obligations/events chưa có lineage mapping thống nhất sang RiskSignal | PARTIAL; reauthorize mỗi lần mở, không copy ref chỉ từ UI. |
| `DERIVED_METRIC` | AI001 metric carries formula_version, snapshot_id, report checksums; AI002 event method/formula version | Không có standardized KPI v2 quality/denominator/derived ref ID; không lưu oracle provenance | PROPOSED wrapper trỏ source metric + formula/method + report/doc refs; chưa claim implemented. |
| `FORECAST_REF` | AI002 `forecast_id` + `snapshot_id` in response | IDs random/ephemeral, không có retrieval endpoint/versioned immutable snapshot; evidence_refs top-level empty | NOT_SUPPORTED as durable evidence; dùng inline typed output only under authorized request. |

Version propagation tối thiểu: mỗi `source_snapshot_refs[]` phải giữ source feature, contract/formula/method version, company, cutoff, period, currency, book, source status, generation time và evidence kind/ref; AI003 rule_version riêng. Không gộp 2 snapshot IDs thành một giả. Nếu source/error/permission/coverage không đạt, AI003 signal INCONCLUSIVE/FORBIDDEN theo contract, không dùng giá trị cũ.

## 27. Security, temporal and independent gold re-check

| Boundary | Current fact → AI003 requirement | State |
| --- | --- | --- |
| Company + filter | `get_verified_company` và AI002 `resolve_request_scope` là primitives; AI003 chưa có endpoint. Allowlist signal + metric IDs và server-selected company; không nhận arbitrary report/DocType/URL/filter từ prompt. | DERIVED / AI003 NOT_VERIFIED |
| Resource + evidence | AI001 report permission ở fetch; AI002 doc evidence reauthorize API. AI003 phải reauthorize mỗi view và suppress unauthorized company/resource existence. | PARTIAL; role/cross-company runtime chưa test |
| Cache role change | **DERIVED** `get_cash_forecast`: `validate_forecast_request` → cache lookup/return → source AR/AP report checks chỉ trên miss (`service.py:145-205`). Same user giữ Company/Account nhưng mất Report permission trong TTL có thể vẫn nhận cached response. Controlled mock route: cache hit returned, `get_trade_obligations` not called; **không** là live exploit proof. | SECURITY BLOCKER; recheck report/resource auth before cache hit hoặc invalidate on permission changes, test role revoke/regrant. |
| Cache isolation | Key includes user/company/cutoff/horizon/scope/source mode/version; helpful for cross-user, nhưng no permission epoch and source snapshot freshness. | PARTIAL; TTL/stale data E2E pending |
| Stale UI | AI002 page uses generation token/clear on company switch. AI003 page absent; must carry over and test out-of-order responses with role/company change. | DERIVED / NOT_VERIFIED |
| Fixture/live | API fixture source only under server test flags. Current web-worker flags and deployed source not inspected; container lacks new code and approved-scope migration. | NOT_VERIFIED |
| Agent | AI001/AI002 LLM explanations exist; AI003 must receive immutable, authorized facts and can neither calculate/alter KPI, threshold or severity nor invent signal. | PROPOSED |

Temporal test matrix for every future selected signal: current cutoff, previous cutoff, transaction posted after cutoff, backdated transaction created later, cancellation/reversal, fiscal boundary, timezone midnight boundary. Current code has posting-date filters for AI001 and AI002; **as-known-at** replay is not implemented/verified. Stub filter capture proves only filter construction, not ERPNext point-in-time correctness. `as_of` invalid and earlier-than-period are accepted by AI001 diagnostic (§23); these requests must fail validation rather than silently shift periods. AI002 site timezone mismatch blocks Vietnam date-boundary acceptance.

Independent gold plan for first conditional candidates:

| Candidate | POSITIVE | BENIGN near threshold | INCONCLUSIVE + security/temporal/model cases |
| --- | --- | --- | --- |
| AR_OVERDUE_SPIKE | Transaction-backed AR at two cutoffs; independent oracle sums outstanding/overdue from locked vouchers and computes ratio/delta with approved rule | Same denominator/observation count, just non-trigger side of symbolic `T_rule`; verified zero only with legitimate empty report | Missing/malformed amount; unknown status/missing data; zero denominator; future posting; backdated/cancelled case under approved policy; cross-company/report denial; source exception; model timeout leaves deterministic status. |
| AP_DUE_CLUSTER | Transaction-backed AP vouchers with contractual due dates in approved window; oracle sums/counts from voucher residuals, never cash-settlement claim | Valid AP dates just outside rule boundary or non-trigger side of `T_rule` | Null/malformed due date, malformed amount/voucher, empty success, future posting, cross-company/document denial, source exception, model failure; partial-payment residual reconciled. |

Gold manifest (chưa tạo) phải lưu source voucher IDs/hashes, independent expected KPI numeric values, period/cutoff/timezone/book/currency, source state, denominator/count, expected signal state, rule/threshold version, evidence IDs. Gold oracle không import AI003 engine hay AI001/AI002 metric function để tính expected KPI. Sai lệch live report↔oracle phải được điều tra; không chỉnh formula chỉ để test xanh. Mọi threshold/tolerance vẫn NOT_VERIFIED tới khi finance owner phê duyệt. False-positive tracking: adjudicated benign gần ngưỡng, malformed/zero misclassification, delayed corrections; không phát minh precision target khi chưa có dataset.

## 28. Historical v2 gates, evidence ledger and next action — superseded by §29

| Gate | Status | Evidence / blocker |
| --- | --- | --- |
| G1 Runtime | PARTIAL | AI001 same checksum + live sanitized call; AI002 checksum mismatch, migration absent, timezone mismatch; no isolated current deployment. |
| G2 Contract | PARTIAL | v2 KPI/risk fields specified nhưng standardized KPI IDs/envelope/evidence/severity chưa code/freeze. |
| G3 Data & Method | BLOCKED | Malformed→zero, USD label mismatch, historical/P&L baseline/Finance Book gaps, no thresholds/independent gold. |
| G4A Security/Evaluation | BLOCKED | Potential same-user role-change cache bypass, AI003 permission/E2E/gold missing; guard primitives alone insufficient. |
| G4B | NOT_APPLICABLE_YET | Chưa build AI003. |

| claim | code_path | test_file / test_name | environment | command | result | artifact |
| --- | --- | --- | --- | --- | --- | --- |
| Commit/test alignment | AI002 files in §20 | Six current unit modules / suite | Windows Python 3.13.7, HEAD `030ccc3` | `git rev-parse HEAD`; `python -m unittest -q ...` | 127 OK; no tracked dirty code | Tool transcript 2026-09-29; §20 |
| Container mismatch/migration | `service.py`, `api/ai_insights.py`, `fixtures/custom_field.json` | N/A (runtime schema) | Docker `frontend` | `Get-FileHash`; `docker exec sha256sum`; `frappe.db.has_column` read-only | AI002 hashes differ; approved cash column false | §20 sanitized hashes/booleans |
| AI001 live KPI availability | `api/ai_insights.py:get_financial_snapshot`, `financial_snapshot.py` | `test_financial_snapshot.py` supports unit only | Docker `frontend`, Administrator demo, rollback | `docker exec -i ... python -` sanitized snapshot call | current 7 core AVAILABLE; prior P&L trio unavailable | §20 statuses only |
| Currency label mismatch | `financial_snapshot.py:build_financial_snapshot` | no current dedicated test | Same Docker demo, rollback | sanitized AI001 call request USD + company currency read | company VND, revenue AVAILABLE labeled USD | §20 metadata only |
| Malformed/unknown/empty split | `financial_snapshot.py:parse_ar_data/parse_ap_data/build_financial_snapshot` | no current dedicated test | Windows Python 3.13.7 | controlled inline Python cases (§23) | malformed, unknown, missing data, legitimate empty all AVAILABLE 0; with valid P&L/TB top snapshot can be `OK` | §23 output |
| Prior period/as_of validation | `financial_snapshot.py`, `financial_health.py` | `test_financial_health.py` covers arithmetic, not full replay | Windows Python 3.13.7 | controlled fetcher capture and invalid-cutoff calls | current/prior filters as §23; early/invalid cutoff accepted | §23 output |
| Cached report reauthorization gap | `cashflow/service.py:validate→cache→source` | no role-change test | Windows Python 3.13.7, mock only | patch validation/cache and observe report-read call | cache returned, source read skipped | §27; live exploit NOT_VERIFIED |

No gate is PASS. Không sửa production code, không tạo AI003 engine hoặc threshold. Next action: đồng bộ commit `030ccc3` trên **isolated** Frappe site và migrate scope; khắc phục AI001 source validation/currency/as_of, xác minh P&L historical mapping, bảo vệ cache role-change; sau đó tạo independent KPI+signal gold và role/temporal E2E. ChatGPT Chat review evidence và quyết định freeze; tài liệu này không tự freeze.

## Historical v2 finding summary — superseded by §29

V2 DELTA
- 22 AI001 KPI, 7 AI002 cash KPI và RiskSignal fields mới được nêu trong spec; code chưa có standardized KPI layer/cash_metrics.

VERIFIED KPI INPUTS
- Không có KPI v2 đủ toàn bộ source, historical, currency/book, permission, evidence và independent gold để AI003 dùng authoritative.

PARTIAL KPI INPUTS
- AI001 revenue comparison, gross_margin, AR outstanding/overdue ratio, AP outstanding; AI002 forecast series/shortfall event chỉ ở current code/unit level.

BLOCKED KPI INPUTS
- AR/AP malformed→zero; P&L prior unavailable/mapping; USD label mismatch; AI002 cash KPIs current runtime chưa deploy/migrate; KPI v2 còn lại chưa implement.

AI003 P0 SIGNALS
- Hiện không có READY signal; smallest credible scope để freeze hôm nay là rỗng.

CONDITIONAL SIGNALS
- Chỉ thử `AR_OVERDUE_SPIKE` và `AP_DUE_CLUSTER` sau source/security/threshold/gold gates.

P1 / BLOCKED SIGNALS
- `SALES_DECLINE`, `MARGIN_DROP` demoted P1; `CUSTOMER_CONCENTRATION`, `SUPPLIER_CONCENTRATION`, `EXPENSE_SPIKE`, `INVENTORY_CASH_LOCK`, `COLLECTION_DELAY` P1; `CASH_SHORTFALL` blocked live.

OLD BLOCKERS RESOLVED
- Không có blocker AI003 được xác nhận resolved; AI002 code-level fail-closed/TB gate đã commit nhưng chưa deployed verified.

OLD BLOCKERS STILL OPEN
- Malformed/unknown AR/AP→zero, historical/as_of policy, P&L mapping, currency/Finance Book, timezone, runtime alignment, thresholds, gold.

NEW BLOCKERS
- V2 KPI contract/cash_metrics gap; observed USD label mismatch; potential AI002 same-user role-change cache bypass.

SOURCE / SNAPSHOT REUSE
- AI001 7 core metrics và AI002 typed forecast/obligations là candidate; snapshot IDs độc lập, không shared atomic snapshot.

EVIDENCE FINDINGS
- AI001 report checksum không có authorized replay; AI002 doc refs có reauth API nhưng top-level forecast evidence_refs không populated; FORECAST_REF chưa durable.

SECURITY FINDINGS
- Server company/report/doc guards tồn tại; cache hit trước AR/AP report reauth là derived risk, AI003 role/cross-company E2E chưa chạy.

TEMPORAL FINDINGS
- Current/prior report filters observed bằng stub; invalid/early as_of accepted; future/backdated/cancelled actual transaction replay NOT_VERIFIED.

GOLD / FIXTURE FINDINGS
- AI003 independent KPI/signal oracle chưa có; symbolic POSITIVE/BENIGN/INCONCLUSIVE plan đã định, threshold chưa approved.

G1: PARTIAL
G2: PARTIAL
G3: BLOCKED
G4A: BLOCKED
G4B: NOT_APPLICABLE_YET

CONTRACT FREEZE: NOT_READY

TOP 3 BLOCKERS
1. Authoritative KPI correctness: fail-closed AR/AP, currency/Finance Book, P&L historical/cutoff + independent numeric gold.
2. Isolated current runtime: align AI002 commit/migrate/timezone and verify source/evidence/security including cache role changes.
3. Approved AI003 thresholds/severity/denominator and transaction-backed temporal/false-positive oracle.

RECOMMENDED NEXT ACTION
- Remediate and verify the three blockers, then submit updated evidence to ChatGPT Chat for freeze decision; do not implement AI003 yet.

## 29. Foundation verification and initial gate — 2026-09-30 (see §30 for Work result)

The remediation in `AI003_FOUNDATION_REMEDIATION_REPORT.md` corrected the AI001 malformed-source, cutoff, and currency paths and the AI002 cache-hit report authorization path. The current `lotus_fin` working tree was packaged into local Docker image `lotus-fin:ai003-local`; backend, frontend, scheduler, websocket, and both queues now use that image. SHA256 checks matched workspace and backend for representative AI001/AI002 code and test files. The local workspace and Docker backend each ran the same 159 unit tests (127 existing + 32 remediation): **159 passed, 0 failed**. Four existing cash-scope tests were isolated from real Company authorization when Frappe is installed; no production authorization logic was changed for that test correction. These are unit results, not a live financial oracle.

Read-only site checks after the image update: `frappe.db.has_column("Company", "ai002_approved_cash_accounts") = False`; `frappe.utils.get_system_timezone() = Africa/Abidjan`. The site data and DB volumes were preserved, so image alignment did not apply migration or change site settings. The remediation code is also uncommitted at this revision; the image is a local working-tree snapshot. GitNexus remains 10 commits behind HEAD: `build_financial_snapshot` impact reports one direct caller (`get_financial_snapshot`, LOW on stale graph); `get_cash_forecast` is UNKNOWN/not indexed. Text search confirms `get_cash_forecast` is called by `api/ai_insights.py` and tests; UNKNOWN is not treated as safe.

| Gate | Current status | Evidence / remaining condition |
| --- | --- | --- |
| Foundation code + unit verification | **PASS** | 159/159 in workspace and Docker; current app files packaged in local image. |
| Ready for next Work verification | **YES** | The verification phase can start; this is not contract freeze. |
| G1 Runtime | PARTIAL | Image aligned, but approved cash-scope column absent, timezone differs from the AI002 contract, and live report/permission behavior is not replayed on an isolated current site. |
| G2 Contract | PARTIAL | AI003 standardized KPI envelope, evidence IDs, scope, and rule/severity semantics remain draft. |
| G3 Data & Method | BLOCKED | AI001 remediation has unit evidence, but historical P&L mapping, numeric oracle, thresholds, denominators, and transaction-backed AI003 signal gold are not verified. |
| G4A Pre-build Security/Eval | BLOCKED | Cache reauthorization has unit evidence; AI003 role/cross-company, temporal, source-failure, and adversarial evaluation on an isolated site remain. |
| G4B Post-build Verification | NOT_APPLICABLE_YET | AI003 has not been implemented. |
| Contract freeze | **NOT_READY** | Workflow v3 Phase 9 requires G1, G2, G3, and G4A all PASS. |

**Next workflow step:** Chat has drafted the candidate contract; Work now completes runtime discovery and the workflow v3 step 4 (`fixture + independent gold + security facts`). First align an isolated Frappe site by applying the required migration and checking timezone, then replay real AR/AP and P&L report outputs, permissions, cutoff/temporal cases, and cache revocation. Build a transaction-backed fixture and an oracle independent of AI001/AI002/AI003 calculations for at most `AR_OVERDUE_SPIKE` and `AP_DUE_CLUSTER`, subject to source evidence. Chat then reviews thresholds, severity, and the full gate evidence before Phase 9 contract freeze. Antigravity implementation is Phase 10, after freeze.

## 30. Work verification on isolated site — 2026-09-30 (see §31 for latest Work recheck)

Full reproducible findings: [`evidence/AI003_WORK_VERIFICATION_2026-09-30.md`](evidence/AI003_WORK_VERIFICATION_2026-09-30.md). Site `ai003-verify.localhost` was created separately from `frontend`; app installation and migration succeeded, approved-cash column is present, timezone is `Asia/Ho_Chi_Minh`, and synthetic submitted vouchers provide an independent source oracle. `frontend` retains its old schema/timezone.

Live source oracle at 2026-09-26: AR outstanding 6,9 triệu VND, overdue AR 2 triệu, AP outstanding 7,95 triệu, cash from GL 11,55 triệu, revenue 8 triệu. AI001 returns revenue/cash correctly but AR/AP `UNAVAILABLE`; AI002 returns typed `SOURCE_ERROR` with no financial payload. ERPNext/Frappe report output has four valid dict rows plus a documented total footer of type `list` (`add_total_row=true`), which both strict parsers currently treat as malformed. **WV-01 blocks usable AR/AP runtime.**

An independent preflight finding, **WV-02**, shows that an uninitialized ERPNext Party Type master makes both AR/AP reports contain Customer and Supplier rows. A controlled adapter probe demonstrates that `_collect_obligations` can label a Supplier/Purchase Invoice row as AR/Sales Invoice. Proper Party Type mapping restored correct report totals on the isolated site, but the adapter does not validate row semantics; a footer-only patch must not turn this into a silent wrong result. Validations for invalid cutoff, currency mismatch, Finance Book, Guest/cross-company denial and posting-date cutoff passed live. COGS mapping, `as_known_at`, signal thresholds/gold and live cache role revocation remain unverified.

| Gate | Current result |
| --- | --- |
| Foundation code/unit | PASS (159/159 workspace and Docker). |
| Ready for Work verification | YES; Work verification has started. |
| Work verification | **BLOCKED by WV-01/WV-02; remediation and re-test required.** |
| G1 Runtime | PARTIAL (isolated site aligned; `frontend` remains unmigrated/wrong timezone; AR/AP source unavailable). |
| G2 Contract | PARTIAL. |
| G3 Data & Method | BLOCKED (AR/AP runtime and independent signal gold/thresholds). |
| G4A Security/Eval | BLOCKED (cross-leg semantic validation and live cache/temporal evaluation). |
| G4B | NOT_APPLICABLE_YET. |
| Contract freeze | NOT_READY. |

**Next action per workflow v3:** Zcode/Antigravity repairs WV-01 and WV-02 in AI001/AI002 source boundaries, with tests for real Frappe v16 footer, malformed rows, missing Party Type and cross-leg data. Work then re-runs unit and isolated-site oracle/security/temporal checks. Chat reviews the resulting evidence, rule thresholds and candidate scope before contract freeze; AI003 implementation remains later.

## 31. Work recheck after Antigravity remediation — 2026-09-30 (see §32 for latest authority)

See [`evidence/AI003_WORK_RECHECK_2026-09-30.md`](evidence/AI003_WORK_RECHECK_2026-09-30.md). Work independently re-ran 182 local and 218 Docker tests; all passed. Isolated-site AI001 AR/AP/revenue/cash and AI002 AR/AP obligations now match the independent 2026-09-26 voucher/GL oracle. The Frappe list footer and normal Party Type path are working.

Two fail-closed gaps remain: **WR-01** allows unverified dict summary markers to be silently skipped, including an all-summary payload that becomes verified zero; **WR-02** lets AI001 count a positive AR/AP row with no voucher/provenance. The Antigravity report's `REMEDIATED & DEEPLY VERIFIED` describes its checks but is not a Work gate PASS. Work verification remains **NOT_PASS**; G1 `PARTIAL`, G2 `PARTIAL`, G3/G4A `BLOCKED`, G4B `NOT_APPLICABLE_YET`, contract freeze `NOT_READY`. Antigravity/Zcode fixes WR-01/02, then Work re-tests before Chat considers contract authority.

## 32. Work verifies Zcode WR-01/WR-02 — 2026-09-30 (see §33 for candidate v0.2 evaluation)

Evidence: [`evidence/AI003_WR01_WR02_WORK_VERIFIED_2026-09-30.md`](evidence/AI003_WR01_WR02_WORK_VERIFIED_2026-09-30.md). Work independently ran **197 local tests and 233 Docker tests**, all passed. Live poisoned AR probes reject fake summaries and voucher-less positive rows. Two-cutoff AI001 numeric and AI002 obligation replay matches the independent voucher/GL oracle. **WR-01 and WR-02 are VERIFIED FIXED; foundation remediation PASS within this checked scope.**

Work rebuilt the local image from `c6f4cd1` and aligned all six application services; tests and live replay still passed after container recreation. Database/site volumes were preserved. COGS and verified future settlement remain unavailable as intended. AI003 source-contract/gold/threshold/security evidence is still incomplete: G1 `PARTIAL`, G2 `PARTIAL`, G3/G4A `BLOCKED`, G4B `NOT_APPLICABLE_YET`, **contract freeze NOT_READY**.

**Next owner: ChatGPT Chat**, to complete the candidate contract for at most `AR_OVERDUE_SPIKE` and `AP_DUE_CLUSTER`, with explicit baseline/window/denominator/severity and financial approval requirements. Work then verifies gold and remaining security/temporal cases against that contract; Chat decides freeze only after all pre-build gates pass. No current finding requires another WR-01/WR-02 remediation loop.

## 33. Independent pre-build evaluation of candidate v0.2 — 2026-09-30 (latest authority)

Authority supplied by Chat: [`AI003_CANDIDATE_CONTRACT_v0.2.md`](AI003_CANDIDATE_CONTRACT_v0.2.md) and [`AI003_WORK_PREBUILD_EVALUATION_PROMPT_v0.2.md`](AI003_WORK_PREBUILD_EVALUATION_PROMPT_v0.2.md). Full evidence: [`evidence/AI003_PREBUILD_EVALUATION_2026-09-30.md`](evidence/AI003_PREBUILD_EVALUATION_2026-09-30.md); per-field feasibility: [`AI003_CONTRACT_FEASIBILITY_v0.2.md`](AI003_CONTRACT_FEASIBILITY_v0.2.md); independent source/symbolic gold: [`AI003_GOLD_MANIFEST.yaml`](AI003_GOLD_MANIFEST.yaml).

On unchanged revision `c6f4cd13c677e167ac645d4d0c48d236383c4fac`, Work created synthetic Gold/Empty companies only on `ai003-verify.localhost` and recorded 70 distinct cases: 53 live source/reusable-primitive probes, 17 specification-only cases. Six checks remain unmet; these are not six independent bugs. No production code or AI003 implementation was changed. WR-01/WR-02 retain their scoped VERIFIED FIXED status.

AR and AP source arithmetic, partial/paid invoices, allocated/unallocated credits and inclusive AP +1/+7/+8/+30/+31 boundaries are independently verified. AR due-exact is not overdue. Future-posted AR/AP leaves historical input unchanged; backdate/cancel/amend restates input and changes evidence checksum. Document evidence reauthorization, cross-company denial and bounded explanation fallback passed. Unallocated credits are not automatically allocations merely because return_against is set; credit/netting policy remains open.

**New concrete findings:** PB-SEC-01 (HIGH) — actual AR report is denied by Frappe Custom Role, but reusable report guard still permits it and AI002 cache returns the same cached financial payload; PB-DATA-01 — AR missing due-date/overdue information still produces AVAILABLE ratio; PB-DATA-02 — exact duplicate AR/AP row can double-count input. AP null due date and durable report/derived evidence replay need explicit candidate design/coverage rules; business policy/threshold approval remains pending. These are candidate-created verification findings, not a reversal of the earlier scoped WR fix.

| Gate | Latest assessment |
| --- | --- |
| G1 Runtime | PASS for the isolated verification runtime; no production-site deployment claim. |
| G2 Contract | PARTIAL — field mapping, netting/identity/zero/precision/status/replay and financial approvals open. |
| G3 Data & Method | BLOCKED — source quality defects and unapproved rule policy; numeric source gold exists. |
| G4A Security/Evaluation | BLOCKED — reproduced report/cache authorization defect; absence of an AI003 endpoint is not the blocker. |
| G4B | NOT_APPLICABLE_YET. |
| Contract freeze | NOT_READY. |

**Next owner: ChatGPT Chat**, as explicitly required by the supplied Work prompt: review concrete reproductions and contract decisions first, then approve focused foundation remediation for Antigravity/Zcode. Work re-tests approved changes and affected gold; only Chat decides freeze after all pre-build gates pass.

## 34. Independent Verification Lead round — 2026-09-30 (historical; latest §35)

IVL re-verified the foundation remediation and the three open pre-build defects at unchanged revision `c6f4cd1` on `ai003-verify.localhost`. Evidence: [`AI003_IVL_REMEDIATION_VERIFICATION_2026-09-30.md`](AI003_IVL_REMEDIATION_VERIFICATION_2026-09-30.md) (focused remediation verification), [`evidence/AI003_IVL_GOLD_CLOSURE_2026-09-30.md`](evidence/AI003_IVL_GOLD_CLOSURE_2026-09-30.md) (gold closure), [`AI003_IVL_CONTRACT_SEMANTICS_REVIEW_v0.2.md`](AI003_IVL_CONTRACT_SEMANTICS_REVIEW_v0.2.md) (contract semantics + conflicts), [`AI003_BUSINESS_POLICY_DECISION_SHEET.md`](AI003_BUSINESS_POLICY_DECISION_SHEET.md) (approval surface), [`AI003_CONTRACT_FREEZE_DECISION_PACKAGE.md`](AI003_CONTRACT_FREEZE_DECISION_PACKAGE.md) (decision package for Chat).

Independently confirmed this round:

- Runtime/source/migration sync: image `sha256:220e4f5d…` matches §32 rebuild; container source hashes equal HEAD `c6f4cd1`; scope column and `Asia/Ho_Chi_Minh` verified. Impact analysis: 67 passing §33 cases remain valid (unchanged revision); only the three defects, regression suites and gold oracle were re-run.
- **PB-SEC-01 reproduced independently** (own probe, not Work's script): Custom Role `Accounts Receivable → Accounts Manager` makes `Report.is_permitted()` deny and direct report run refuse, while `check_ai002_report_permission` passes and the AI002 cache returns the identical forecast ID with 10 obligations and opening cash. Regrant restores. Root cause confirmed at `security/access.py:check_report_permission` (generic `query_report.has_permission` instead of report-specific permission).
- **PB-DATA-01 reproduced**: missing due-date/overdue fields on a positive AR row leave the ratio AVAILABLE at −0.0177 (overdue basis collapses to the credit row).
- **PB-DATA-02 reproduced both legs**: exact duplicate AR row → 640,000 vs 565,000; exact duplicate AP row → 8 vs 7 obligations with repeated `source_ref`.
- **Gold closure**: independent voucher/Payment-Ledger oracle re-run matches the manifest at both cutoffs (650,000/0; 565,000/65,000; AP 1,400,000/1,950,000 and 275,000/975,000) and was re-verified after probe cleanup. Numeric gold is stable; policy artifacts stay PENDING_APPROVAL.
- **Evidence replay design**: isolated harness proved `DYNAMIC_AUTHORIZED_REPLAY + SAVED_HASH_COMPARISON` produces MATCH / RESTATED / UNAVAILABLE / FORBIDDEN correctly, using the authoritative report permission primitive; snapshot ID/hash never acts as an authorization token. No production replay endpoint was built; durable REPORT_SNAPSHOT storage remains a Chat design choice.
- Probe hygiene: probe users/roles/permissions removed and asserted absent; four cancelled transient invoices and one temp Customer remain as documented residue with zero numeric impact (gold re-run proven); Work may purge them in the next fixture pass.
- Version conflict recorded: the verification mandate references candidate contract **v0.3**, but only **v0.2** exists. Nothing invented; Chat must issue the authoritative next contract version.

Gate assessment re-confirmed: G1 `PASS` for the isolated verification runtime only; G2 `PARTIAL`; G3 `BLOCKED` (PB-DATA-01/02 + unapproved policy); G4A `BLOCKED` (PB-SEC-01, independently reproduced); G4B `NOT_APPLICABLE_YET`; **CONTRACT FREEZE NOT_READY**. Next owner: **ChatGPT Chat** — decide the seven contract conflicts, approve the focused remediation scope for PB-SEC-01/PB-DATA-01/PB-DATA-02, and process the eight-row Business Policy Decision Sheet; then Antigravity/Zcode implements approved changes, Work re-tests, and only Chat decides freeze.

## 35. Final foundation verification / pre-build decision — 2026-09-30 (latest authority)

Authority: user's Master Prompt “Final Foundation Verification, Independent Evaluation & Contract Closure”. Current HEAD `86208f49e05122531c1cbe8b11d066092244dd4c`, branch `feature/risk-signal-agent`. Production diff from `c6f4cd1` is empty; latest commit adds docs/harness only. **No new production remediation for PB-SEC-01/PB-DATA-01/PB-DATA-02 exists. Candidate v0.3 and Chat-approved decisions were not found.** Do not infer either from builder report or prompt assumptions.

Full current authority: [Final Pre-build Decision Package](AI003_FINAL_PREBUILD_DECISION_PACKAGE.md), [focused Work verification](evidence/AI003_FINAL_FOUNDATION_VERIFICATION_2026-09-30.md), [business policy sheet](AI003_BUSINESS_POLICY_DECISION_SHEET.md), [scaffold/integration plan](AI003_TECHNICAL_SCAFFOLD_IMPLEMENTATION_PLAN.md).

- VERIFIED_RUNTIME alignment: isolated `ai003-verify.localhost`, image `220e4f5d…` across six app services, Frappe16.34.0/ERPNext16.35.0/Lotus Fin0.0.1; relevant source hashes match workspace and reference production; installed apps/scope column/Ho_Chi_Minh/VND/cash scope verified. No source/migration change means no rebuild/migration needed; no frontend mutation or Git reset/rebase/commit.
- VERIFIED_TEST: **152/152 focused unit tests OK**, command/output in focused report. **51 current probe checks, 39 PASS / 12 FAIL / zero harness errors**: mixed real-runtime/live-row-mutation/harness cases labelled; 12 unmet checks belong to three open PB defects. **25 TEST_ONLY_POLICY specification assertions PASS**, not engine/approval proof. Never add overlapping suite/probe/historical counts.
- PB-SEC-01 HIGH reproduced: actual report Custom Role revoke/direct denial but active and trusted explicit-user guard passes; populated cache returns same forecast `FC-6CDB4EB5`, 10 obligations and opening cash. Fresh uncached request returns SOURCE_ERROR instead of required generic FORBIDDEN; no fresh financial payload leak observed. Regrant works. Company/Account/document isolation and doc-regrant pass. F0 must repair report-specific auth, cache eviction and fresh error typing.
- PB-DATA-01 reproduced with missing and malformed date/basis: total valid 565k but overdue −10k/ratio −0.0177 remains available; explicit/date valid cases retain gold. F0 must invalidate affected overdue metric without changing legacy financial formula or forcing valid total unavailable.
- PB-DATA-02 reproduced in both AI001/AI002 AR/AP; exact/conflicting copies double-count. Missing voucher identity still failclosed. Simulated term split preserves amount but actual distinct multi-term/account split reconciliation remains NOT_VERIFIED; do not blanket dedup by voucher.
- Independent oracle dual AR bases/AP windows/credits at 20/09 and 26/09 still match original fingerprints; expected gold unchanged. 70 original cases retained, revalidation metadata added. **Correction to §34: original 70 cases − 6 unmet = 64 passing (including specification-only), not 67.** Gold never implies approved business policy.
- Temporal VERIFIED_RUNTIME evidence §33 reused because relevant production code/site/oracle fingerprints unchanged; posting-date/restatement only, no AS_KNOWN_AT. Current replay harness shows live MATCH and real revoked FORBIDDEN with authoritative guard; synthetic changed-hash RESTATED/forced UNAVAILABLE labelled harness-only. Production dynamic replay remains CONDITIONAL, foundation auth blocked; scope/schema/method-bound canonical hash and non-atomic multi-source limitations must be explicit.
- Probe changes rolled back; User/Custom Role absent, Gold fingerprint unchanged. Four cancelled historical IVL vouchers remain, no new voucher writes and no destructive fixture cleanup.
- GitNexus 12 commits stale; guard/AR parser LOW from old graph, adapter UNKNOWN; detect compare says changed docs but no indexed symbol overlap, not clean. Actual source/diff supplements unresolved graph; no production symbol edited.

| Gate / readiness | Current conclusion | Exact next condition / owner |
| --- | --- | --- |
| Foundation | PARTIAL; three PB defects FAIL | Chat technical handoff → one Builder F0 → independent Work acceptance live PASS. |
| G1 | PASS isolated declared runtime | Re-align only when production source/migration changes; Work/DevOps. |
| G2 | PARTIAL | Chat issues v0.3/approved technical decisions; Finance/Product policy scope defined. |
| G3 | BLOCKED | F0 data/identity/coverage PASS + selected-method gold/real split reconciliation + approved policy for production freeze. |
| G4A | BLOCKED | F0 real report revoke/regrant cached/fresh/explicit-user FORBIDDEN, no payload, evict; Work. |
| G4B | NOT_APPLICABLE_YET | Endpoint-specific tests after implementation; absence is not G4A defect. |
| Technical scaffold | CONDITIONAL | Offline draft schemas/mocks SAFE_TO_SCAFFOLD; real-data adapters MUST_WAIT F0 and technical contract readiness. |
| Business policy | PENDING | Vietnamese B1–B9 proposal/approver sheet; no synthetic production thresholds or fake approval. |
| Contract freeze | NOT_READY | Mandatory gates and genuine in-scope approvals; only Chat reviews freeze. |

**Outcome C — NOT READY. Next owner ChatGPT Chat:** [current prompt](AI003_CHAT_PREBUILD_FINDINGS_REVIEW_PROMPT.md) issues technical decisions and focused F0 handoff; Product/Finance can review policies in parallel. Then Antigravity/Zcode implements, Work verifies. Plans S1–S5 and integration ownership/rebase commands are documented, not implemented; no AI003 build in this turn.
