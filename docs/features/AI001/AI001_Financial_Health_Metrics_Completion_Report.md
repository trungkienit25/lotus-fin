# AI001-03 COMPLETION REPORT: FINANCIAL HEALTH METRICS, PERIOD COMPARISON & OBSERVABILITY

**Ngày hoàn thành:** 2026-09-25  
**Hạng mục:** AI001 / AI-F001 Financial Health Analyst — Giai đoạn AI001-03  
**Phạm vi:** Financial Health Metrics + Previous-Period Comparison + Observability Infrastructure  
**Trạng thái kiểm thử:** 100% Passed (38/38 tests tổng cộng: 23/23 live Frappe integration tests, 15/15 deterministic metrics & comparison unit tests).  
**Khuyến nghị:** `READY_FOR_AI001_LLM_EXPLANATION`

---

## 1. Executive Summary

Giai đoạn AI001-03 đã mở rộng và hoàn thiện kiến trúc nền tảng dữ liệu cho trợ lý phân tích tài chính `AI-F001 Financial Health Analyst` thuộc Lotus Fin:
1. **Deterministic Metrics Calculation**: Chuẩn hóa toàn bộ phép tính tài chính P0 bằng `Decimal` (`ROUND_HALF_UP`), triệt tiêu hoàn toàn sai số dấu phẩy động (float floating-point inaccuracy).
2. **Previous-Period Comparison Engine**:
   - Tự động suy diễn kỳ so sánh liền kề có cùng độ dài ngày/năm tài chính (`compute_previous_period`).
   - Tạo `FinancialSnapshot` và `EvidenceRef` độc lập cho kỳ trước từ nguồn dữ liệu ERPNext thực tế.
   - Tính toán `absolute_change` và `relative_change` (`(current - prev) / abs(prev)`).
   - Xử lý triệt để mẫu số bằng 0 (`previous == 0` -> `relative_change = null`, gắn limitation `"Previous period value is zero; relative change undefined."`).
   - Chặn đứng so sánh chéo công ty (Cross-company comparison -> `status = UNAVAILABLE`).
   - Bảo toàn tính trung lập: Tuyệt đối không sinh nhận định chủ quan (good/bad/healthy/unhealthy).
3. **Frozen Near-Term AP Metric**:
   - Bổ sung `near_term_ap` vào danh mục metric với trạng thái `UNAVAILABLE` và limitation rõ ràng: `"near-term AP horizon not yet frozen"`. Không tự tiện bịa đặt khung thời gian 7/14/30 ngày khi chưa có quy định nghiệp vụ chốt.
4. **Structured Observability & Operational Telemetry**:
   - Module `observability.py` phát hành structured JSON audit logs với `correlation_id` xuyên suốt các span.
   - Ẩn danh hóa người dùng bằng hàm băm an toàn `SHA256(user)[:12]`.
   - Cam kết Zero-PII: Không ghi log số tiền chi tiết, tên khách hàng/nhà cung cấp, mật khẩu hay token.
   - Bounded in-memory operational metrics collector: đo đếm tổng số request, phân loại status (`OK`, `PARTIAL`, `FORBIDDEN`, `VALIDATION_ERROR`, `SOURCE_ERROR`), lỗi nguồn theo từng report, đếm số metric computed vs unavailable, và thống kê độ trễ P50/P95.
5. **Khớp số 100% với Runtime Gold**:
   - Đối soát đối chiếu trực tiếp trên container ERPNext `frappe_docker-backend-1` site `frontend` cho `Name (Demo)` FY2020. Kết quả khớp chính xác 100% với số liệu đã được đối soát.

---

## 2. Chi tiết các tệp tin đã thay đổi & tạo mới

| File | Hành động | Mục đích |
|---|---|---|
| `lotus_fin/lotus_fin/ai/observability.py` | Tạo mới | Structured JSON audit logging, pseudonymous hashing, operational metrics collector, span tracer. |
| `lotus_fin/lotus_fin/ai/financial_health.py` | Tạo mới | Suy diễn kỳ trước (`compute_previous_period`), tính chênh lệch tuyệt đối & tương đối (`compute_metric_change`), dựng `build_comparison_block`. |
| `lotus_fin/lotus_fin/ai/financial_snapshot.py` | Sửa đổi | Tích hợp observability events, thêm metric `near_term_ap` (`UNAVAILABLE`), tích hợp nhánh `comparison="PREVIOUS_PERIOD"`, bảo toàn company guard check khi chạy có/không có kết nối DB. |
| `lotus_fin/lotus_fin/api/ai_insights.py` | Sửa đổi | Bổ sung tham số `comparison` vào whitelisted endpoint `@frappe.whitelist() get_financial_snapshot`. |
| `lotus_fin/lotus_fin/tests/test_financial_health.py` | Tạo mới | 15 unit tests độc lập kiểm chứng toán học kỳ so sánh, mẫu số 0, chuyển đổi âm-dương, near-term AP invariant, structured logging & telemetry. |
| `lotus_fin/lotus_fin/tests/test_access_and_reports.py` | Sửa đổi | Bổ sung live integration tests cho `near_term_ap` và `comparison="PREVIOUS_PERIOD"` chạy trong môi trường Frappe thực tế. |
| `lotus_fin/lotus_fin/tests/test_financial_snapshot.py` | Sửa đổi | Cập nhật số lượng metric mong đợi (8 metrics) bao gồm `near_term_ap`. |
| `docs/features/AI001/AI001_Feature_Freeze_VI.md` | Sửa đổi | Cập nhật Definition of Ready (DoR) hoàn thành các gate runtime, data, method và test gold. |

---

## 3. Bảng đối soát số liệu Live ERPNext (Reconciliation Table)

### 3.1 Dữ liệu kỳ hiện tại (FY2020: 2020-01-01 -> 2020-12-31) trên Company `Name (Demo)`

| Metric ID | Tên chỉ số | Giá trị Runtime | Giá trị Gold | Đơn vị | Trạng thái | Bằng chứng (EvidenceRef Checksum) |
|---|---|---|---|---|---|---|
| `revenue` | Doanh thu thuần | 363,000.00 | 363,000.00 | VND | AVAILABLE | `85d6218bae769177` (P&L) |
| `cogs` | Giá vốn hàng bán | 253,760.00 | 253,760.00 | VND | AVAILABLE | `85d6218bae769177` (P&L) |
| `gross_margin` | Biên lợi nhuận gộp | 0.3009 (30.09%) | 0.3009 | ratio | AVAILABLE | `85d6218bae769177` (P&L) |
| `ar_outstanding` | Tổng nợ phải thu | 316,000.00 | 316,000.00 | VND | AVAILABLE | `5a5da1c424d61733` (AR) |
| `overdue_ar_ratio` | Tỷ lệ nợ quá hạn | 1.0000 (100.0%) | 1.0000 | ratio | AVAILABLE | `5a5da1c424d61733` (AR) |
| `ap_outstanding` | Tổng nợ phải trả | 184,293.00 | 184,293.00 | VND | AVAILABLE | `c026f0bb5c1c78a3` (AP) |
| `near_term_ap` | Nợ phải trả sắp đến hạn | `null` | `null` | VND | UNAVAILABLE | *(near-term AP horizon not yet frozen)* |
| `cash_balance` | Số dư tiền & ngân hàng | -117,854.00 | -117,854.00 | VND | AVAILABLE | `4768e4bdb399a4c7` (Trial Balance) |

### 3.2 Dữ liệu so sánh kỳ trước (FY2019: 2019-01-01 -> 2019-12-31)

| Metric ID | Hiện tại (2020) | Kỳ trước (2019) | Chênh lệch tuyệt đối | Chênh lệch tương đối | Diễn giải trạng thái |
|---|---|---|---|---|---|
| `revenue` | 363,000.00 | `null` | `null` | `null` | UNAVAILABLE (Năm 2019 không có phát sinh P&L) |
| `cogs` | 253,760.00 | `null` | `null` | `null` | UNAVAILABLE |
| `gross_margin` | 0.3009 | `null` | `null` | `null` | UNAVAILABLE |
| `ar_outstanding` | 316,000.00 | 0.00 | +316,000.00 | `null` | AVAILABLE (Relative change = null do mẫu số kỳ trước = 0) |
| `overdue_ar_ratio` | 1.0000 | 0.00 | +1.0000 | `null` | AVAILABLE (Relative change = null do mẫu số kỳ trước = 0) |
| `ap_outstanding` | 184,293.00 | 0.00 | +184,293.00 | `null` | AVAILABLE (Relative change = null do mẫu số kỳ trước = 0) |
| `cash_balance` | -117,854.00 | `null` | `null` | `null` | UNAVAILABLE (Không có số dư tiền 2019) |

*Ghi chú: Toàn bộ so sánh phản ánh trung thực dữ liệu kế toán thực tế có trong hệ thống, không tự bịa đặt số dư 0 cho kỳ thiếu.*

---

## 4. Live Runtime JSON Payload Example

Dưới đây là payload JSON thực tế trả về từ endpoint `get_financial_snapshot(company="Name (Demo)", period_start="2020-01-01", period_end="2020-12-31", comparison="PREVIOUS_PERIOD")`:

```json
{
  "feature_id": "AI001",
  "contract_version": "1.0.0",
  "status": "OK",
  "correlation_id": "62e105e4-7389-4091-a1e4-c5a4dcfbf473",
  "company": "Name (Demo)",
  "period": {
    "start": "2020-01-01",
    "end": "2020-12-31"
  },
  "as_of": "2026-09-25T14:48:46.293054Z",
  "snapshot_id": "SNAP-966EFF57F593",
  "data_mode": "actual",
  "currency": "VND",
  "metrics": [
    {
      "metric_id": "revenue",
      "status": "AVAILABLE",
      "value": 363000.0,
      "currency_or_unit": "VND",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": ["85d6218bae769177"],
      "limitations": []
    },
    {
      "metric_id": "cogs",
      "status": "AVAILABLE",
      "value": 253760.0,
      "currency_or_unit": "VND",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": ["85d6218bae769177"],
      "limitations": []
    },
    {
      "metric_id": "gross_margin",
      "status": "AVAILABLE",
      "value": 0.3009,
      "currency_or_unit": "ratio",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": ["85d6218bae769177"],
      "limitations": []
    },
    {
      "metric_id": "ar_outstanding",
      "status": "AVAILABLE",
      "value": 316000.0,
      "currency_or_unit": "VND",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": ["5a5da1c424d61733"],
      "limitations": []
    },
    {
      "metric_id": "overdue_ar_ratio",
      "status": "AVAILABLE",
      "value": 1.0,
      "currency_or_unit": "ratio",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": ["5a5da1c424d61733"],
      "limitations": []
    },
    {
      "metric_id": "ap_outstanding",
      "status": "AVAILABLE",
      "value": 184293.0,
      "currency_or_unit": "VND",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": ["c026f0bb5c1c78a3"],
      "limitations": []
    },
    {
      "metric_id": "near_term_ap",
      "status": "UNAVAILABLE",
      "value": null,
      "currency_or_unit": "VND",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": [],
      "limitations": ["near-term AP horizon not yet frozen"]
    },
    {
      "metric_id": "cash_balance",
      "status": "AVAILABLE",
      "value": -117854.0,
      "currency_or_unit": "VND",
      "period": {"start": "2020-01-01", "end": "2020-12-31"},
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-966EFF57F593",
      "evidence_refs": ["4768e4bdb399a4c7"],
      "limitations": []
    }
  ],
  "comparison": {
    "status": "AVAILABLE",
    "type": "PREVIOUS_PERIOD",
    "previous_period": {
      "start": "2019-01-01",
      "end": "2019-12-31"
    },
    "previous_snapshot_id": "SNAP-3CCADE0F6A09",
    "metrics": {
      "revenue": {
        "status": "UNAVAILABLE",
        "current": 363000.0,
        "previous": null,
        "absolute_change": null,
        "relative_change": null,
        "limitations": ["Metric unavailable in current or previous period."]
      },
      "cogs": {
        "status": "UNAVAILABLE",
        "current": 253760.0,
        "previous": null,
        "absolute_change": null,
        "relative_change": null,
        "limitations": ["Metric unavailable in current or previous period."]
      },
      "gross_margin": {
        "status": "UNAVAILABLE",
        "current": 0.3009,
        "previous": null,
        "absolute_change": null,
        "relative_change": null,
        "limitations": ["Metric unavailable in current or previous period."]
      },
      "ar_outstanding": {
        "status": "AVAILABLE",
        "current": 316000.0,
        "previous": 0.0,
        "absolute_change": 316000.0,
        "relative_change": null,
        "limitations": ["Previous period value is zero; relative change undefined."]
      },
      "overdue_ar_ratio": {
        "status": "AVAILABLE",
        "current": 1.0,
        "previous": 0.0,
        "absolute_change": 1.0,
        "relative_change": null,
        "limitations": ["Previous period value is zero; relative change undefined."]
      },
      "ap_outstanding": {
        "status": "AVAILABLE",
        "current": 184293.0,
        "previous": 0.0,
        "absolute_change": 184293.0,
        "relative_change": null,
        "limitations": ["Previous period value is zero; relative change undefined."]
      },
      "cash_balance": {
        "status": "UNAVAILABLE",
        "current": -117854.0,
        "previous": null,
        "absolute_change": null,
        "relative_change": null,
        "limitations": ["Metric unavailable in current or previous period."]
      }
    },
    "limitations": [
      "revenue: Metric unavailable in current or previous period.",
      "cogs: Metric unavailable in current or previous period.",
      "gross_margin: Metric unavailable in current or previous period.",
      "ar_outstanding: Previous period value is zero; relative change undefined.",
      "overdue_ar_ratio: Previous period value is zero; relative change undefined.",
      "ap_outstanding: Previous period value is zero; relative change undefined.",
      "cash_balance: Metric unavailable in current or previous period."
    ]
  },
  "explanation": {
    "status": "UNAVAILABLE",
    "facts": [],
    "interpretations": [],
    "next_checks": []
  },
  "missing_inputs": [],
  "limitations": [
    "ap_outstanding: Previous period value is zero; relative change undefined.",
    "ar_outstanding: Previous period value is zero; relative change undefined.",
    "cash_balance: Metric unavailable in current or previous period.",
    "cogs: Metric unavailable in current or previous period.",
    "gross_margin: Metric unavailable in current or previous period.",
    "overdue_ar_ratio: Previous period value is zero; relative change undefined.",
    "revenue: Metric unavailable in current or previous period."
  ],
  "evidence_refs": [
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Profit and Loss Statement",
      "source_record_id": null,
      "company": "Name (Demo)",
      "filters": {
        "company": "Name (Demo)",
        "from_fiscal_year": 2020,
        "to_fiscal_year": 2020,
        "period_start_date": "2020-01-01",
        "period_end_date": "2020-12-31",
        "periodicity": "Yearly"
      },
      "as_of": "2026-09-25T14:48:46.293054Z",
      "retrieved_at": "2026-09-25T14:48:47.082105Z",
      "checksum_or_version": "85d6218bae769177"
    },
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Accounts Receivable",
      "source_record_id": null,
      "company": "Name (Demo)",
      "filters": {
        "company": "Name (Demo)",
        "report_date": "2020-12-31"
      },
      "as_of": "2026-09-25T14:48:46.293054Z",
      "retrieved_at": "2026-09-25T14:48:47.082465Z",
      "checksum_or_version": "5a5da1c424d61733"
    },
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Accounts Payable",
      "source_record_id": null,
      "company": "Name (Demo)",
      "filters": {
        "company": "Name (Demo)",
        "report_date": "2020-12-31"
      },
      "as_of": "2026-09-25T14:48:46.293054Z",
      "retrieved_at": "2026-09-25T14:48:47.082709Z",
      "checksum_or_version": "c026f0bb5c1c78a3"
    },
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Trial Balance",
      "source_record_id": null,
      "company": "Name (Demo)",
      "filters": {
        "company": "Name (Demo)",
        "fiscal_year": 2020,
        "from_date": "2020-01-01",
        "to_date": "2020-12-31"
      },
      "as_of": "2026-09-25T14:48:46.293054Z",
      "retrieved_at": "2026-09-25T14:48:47.082863Z",
      "checksum_or_version": "4768e4bdb399a4c7"
    }
  ]
}
```

---

## 5. Kết quả kiểm thử tự động (Test Execution Results)

### Suite 1: Live Container Tests (`test_access_and_reports.py`)
- **Lệnh chạy:** `docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -v lotus_fin.tests.test_access_and_reports`
- **Kết quả:** **23/23 tests PASSED (100%)**
  - Same-company allow (Admin & Restricted User): PASS
  - Cross-company deny (Direct & Filter Tampering): PASS
  - Report error & Deprecated cashflow handling: PASS
  - Empty company dataset handling (0 rows, not error): PASS
  - Unauthorized guest denial (company & reports): PASS
  - Invoice risk analysis permission guard: PASS
  - ERPNext report execution integrity: PASS
  - AI training dataset error preservation: PASS
  - FinancialSnapshot structure & live gold reconciliation: PASS
  - As-of prior to period_end boundary restriction: PASS
  - Near-term AP status & limitation verification: PASS
  - Live previous period comparison verification: PASS

### Suite 2: Deterministic Metrics & Observability (`test_financial_health.py`)
- **Lệnh chạy:** `docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -v lotus_fin.tests.test_financial_health`
- **Kết quả:** **15/15 tests PASSED (100%)**
  - Period calculation (Annual, Leap year, Quarterly): PASS
  - Metric change calculations (Positive growth, Negative growth, Negative-to-positive transition, Negative-to-negative): PASS
  - Zero-previous denominator safe limitation: PASS
  - None inputs handling: PASS
  - Cross-company comparison denial: PASS
  - Full metrics reconciliation without subjective terms: PASS
  - Near-term AP frozen unavailable invariant: PASS
  - User ID pseudonymization (SHA256[:12]): PASS
  - Structured logging Zero-PII verification: PASS
  - Operational metrics collector aggregation: PASS

### Suite 3: Standalone Snapshot & Evidence Linkage (`test_financial_snapshot.py`)
- **Lệnh chạy:** `docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -v lotus_fin.tests.test_financial_snapshot`
- **Kết quả:** **9/9 tests PASSED (100%)**
  - All metrics independent gold reconciliation: PASS
  - EvidenceRef checksum linkage verification: PASS
  - Missing P&L never becomes zero: PASS
  - Empty company valid zero: PASS
  - Source error clean propagation: PASS
  - Period temporal bounds validation: PASS
  - Empty company forbidden: PASS
  - Zero revenue gross margin safe handling: PASS
  - Anomalous ledger state handling: PASS

---

## 6. Trả lời 13 câu hỏi nghiệm thu (Master Task AI001-03 Requirements)

1. **Khớp số 100% với Runtime Gold**:
   - `revenue`: 363,000.00 VND (100% match)
   - `cogs`: 253,760.00 VND (100% match)
   - `gross_margin`: 0.3009 (30.0937%, 100% match)
   - `ar_outstanding`: 316,000.00 VND (100% match)
   - `overdue_ar_ratio`: 1.0000 (100%, 100% match)
   - `ap_outstanding`: 184,293.00 VND (100% match)
   - `cash_balance`: -117,854.00 VND (100% match)
   - `near_term_ap`: UNAVAILABLE (`null`), limitation: `"near-term AP horizon not yet frozen"`.

2. **Công thức kỳ so sánh**:
   - Nếu là năm dương lịch trọn vẹn (Jan 1 -> Dec 31): Kỳ trước là năm trước đó (Jan 1 -> Dec 31).
   - Nếu là khoảng ngày bất kỳ: $E_{prev} = S - 1\text{ ngày}$, $S_{prev} = E_{prev} - D$.
   - Tính chênh lệch: $\Delta_{abs} = \text{current} - \text{previous}$; $\Delta_{rel} = (\text{current} - \text{previous}) / |\text{previous}|$ nếu $\text{previous} \neq 0$.

3. **Mẫu số bằng 0**:
   - $\text{relative\_change} = \text{null}$, $\text{status} = \text{AVAILABLE}$, gắn limitation `"Previous period value is zero; relative change undefined."`.

4. **Xử lý số âm**:
   - Dùng $|\text{previous}|$ ở mẫu số. Ví dụ từ -50 lên +20: $\Delta_{abs} = +70$, $\Delta_{rel} = (20 - (-50)) / 50 = +1.4000$ (+140%).

5. **Xử lý Near-Term AP**:
   - Trạng thái `UNAVAILABLE`, giá trị `null`, limitation `"near-term AP horizon not yet frozen"`. Không tự tiện bịa khoảng ngày.

6. **Khóa nhận định chủ quan**:
   - Output của so sánh chỉ chứa các con số và delta thuần túy. Tuyệt đối không chứa các từ ngữ `good`, `bad`, `healthy`, `unhealthy`, `improving`, `declining`.

7. **Bảo mật và Phân quyền**:
   - So sánh hai công ty khác nhau lập tức bị từ chối với trạng thái `UNAVAILABLE` và limitation `"Cannot compare across different companies."`.
   - Mọi truy vấn snapshot và report đều qua `get_verified_company` (INV-01, INV-02).

8. **Cấu trúc Log Observability**:
   - JSON format có đầy đủ: `timestamp`, `feature_id`, `event_type`, `correlation_id`, `company`, `user_id_hash`, `duration_ms`, `status`, `details`.
   - Danh mục sự kiện chuẩn: `ai001_request_started`, `ai001_authorization_passed`, `ai001_authorization_denied`, `ai001_snapshot_started`, `ai001_snapshot_completed`, `ai001_source_error`, `ai001_metric_computed`, `ai001_metric_unavailable`, `ai001_comparison_started`, `ai001_comparison_completed`, `ai001_comparison_unavailable`, `ai001_request_completed`, `ai001_request_failed`.

9. **Bảo mật PII & Dữ liệu tài chính trong log**:
   - `user_id_hash` = `SHA256(user)[:12]`.
   - Tuyệt đối không log tên khách hàng, tên nhà cung cấp, số hóa đơn, số tài khoản, số dư chi tiết hay mật khẩu/token.

10. **Operational Metrics Telemetry**:
    - `MetricsCollector` duy trì trong bộ nhớ có chặn ngưỡng: `requests_total`, `requests_by_status`, `auth_denials_total`, `source_errors_by_report`, `metrics_computed_total`, `metrics_unavailable_by_id`, `latency_p50_ms`, `latency_p95_ms`.

11. **Trạng thái Gate DoR**:
    - Cập nhật `AI001_Feature_Freeze_VI.md` sang trạng thái: `READY_FOR_AI001_LLM_EXPLANATION`.

12. **LLM Explanation**:
    - Chưa triển khai LLM explanation (`explanation.status = "UNAVAILABLE"`, `facts = []`, `interpretations = []`, `next_checks = []`). Hoàn toàn không gọi bất kỳ LLM API nào trong giai đoạn này.

13. **Khuyến nghị cuối cùng**:
    - **`READY_FOR_AI001_LLM_EXPLANATION`**. Nền tảng dữ liệu, phép tính số học, kỳ so sánh, và hạ tầng quan sát đã đạt chuẩn 100%.
