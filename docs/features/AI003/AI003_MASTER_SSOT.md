# AI-F003 Risk Signal Agent — pre-build investigation (draft, chưa freeze)

## 1. Document control

- Ngày điều tra: 2026-09-29; cập nhật xác thực 2026-09-30 tại §29–33. Trạng thái: **PRE-BUILD FINDING / NOT CONTRACT FROZEN**. Chủ đích: evidence collector; không có AI003 production code.
- Workspace hiện tại: `E:\lotus-fin`, revision `c6f4cd1`; foundation remediation và tài liệu trước đó đã commit. Các mục §4–18 là điều tra lịch sử trên commit `70bd6e8`; §19–28 là v2 reassessment lịch sử; §29–31 là các vòng verification trước; §32 là vòng foundation verification; §33 là kết quả Work pre-build evaluation mới nhất. Runtime kiểm chứng là isolated site `ai003-verify.localhost`; không suy từ kết quả này rằng site `frontend` đã được migrate.
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

## 34. Independent Verification Lead round — 2026-09-30 (latest authority)

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
