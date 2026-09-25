# AI001 — FinancialSnapshot & EvidenceRef Implementation Completion Report

**Feature:** AI001 (AI-F001 Financial Health Analyst — Data Foundation & Evidence Linkage)  
**Ngày hoàn thành:** 2026-09-25  
**Trạng thái:** `IMPLEMENTED_AND_TESTED (PASS 100%)`  
**Phương pháp:** Tính toán tất định (`DETERMINISTIC`), không hallucination, liên kết bằng chứng minh bạch (`EvidenceRef`).

---

## 1. Tóm tắt công việc đã thực hiện (Executive Summary)

Theo chỉ thị Feature Freeze (`docs/features/AI001/AI001_Feature_Freeze_VI.md`) và Chiến lược Dữ liệu (`docs/data/LotusFin_Data_Strategy_v3_1_Codebase_Aligned.md`):
1. **Xây dựng module lõi `FinancialSnapshot` & `EvidenceRef` (`lotus_fin/lotus_fin/ai/financial_snapshot.py`):**
   - **Tất định 100%:** Chỉ sử dụng số học Decimal chính xác, làm tròn chuẩn kế toán `ROUND_HALF_UP` 2 chữ số thập phân cho tiền tệ và 4 chữ số cho tỷ lệ.
   - **Phạm vi chỉ số P0 đóng băng (P0 Frozen Scope):**
     - Doanh thu (`revenue`) & Giá vốn hàng bán (`cogs`) từ Báo cáo Kết quả Kinh doanh (`Profit and Loss Statement`).
     - Tỷ suất lợi nhuận gộp (`gross_margin = (revenue - cogs) / revenue`).
     - Tổng nợ phải thu (`ar_outstanding`) và Tỷ lệ nợ quá hạn (`overdue_ar_ratio = overdue / total_outstanding`) từ Báo cáo Phải thu (`Accounts Receivable`).
     - Tổng nợ phải trả (`ap_outstanding`) từ Báo cáo Phải trả (`Accounts Payable`).
     - Số dư Tiền mặt & Tiền gửi Ngân hàng (`cash_balance`) từ Bảng cân đối thử (`Trial Balance`) / Sổ cái (`General Ledger`).
   - **Không triển khai LLM explanation trong giai đoạn này:** `explanation.status` luôn được đặt là `UNAVAILABLE` với facts rỗng, sẵn sàng gắn model ở phase sau khi có gold rubric đánh giá.
   - **Không thêm bất kỳ chỉ số nào ngoài P0:** Không tính DSCR, Quick Ratio, Runway hay Financial Health Score tổng hợp khi chưa được chuẩn hóa định nghĩa.
2. **Bảo đảm các bất biến cốt lõi (Invariants):**
   - **Bảo mật truy cập công ty (INV-01, INV-02):** Kiểm tra và xác thực `company` phía server qua `get_verified_company`. Nếu yêu cầu công ty rỗng hoặc không có quyền truy cập, trả về ngay trạng thái `FORBIDDEN` và bảo mật ẩn danh tính công ty.
   - **Bất biến "Lỗi không bao giờ thành 0" (Zero-is-not-error invariant):** Báo cáo bị lỗi, timeout hoặc thiếu không bao giờ bị âm thầm gán bằng `0.0`. Hệ thống đánh dấu chỉ số là `UNAVAILABLE`, liệt kê nguồn vào `missing_inputs` và trả về trạng thái phong bì tương ứng (`PARTIAL`, `INSUFFICIENT_DATA` hoặc `SOURCE_ERROR`).
   - **Phân định rõ Rỗng hợp lệ vs Lỗi:** Sổ cái thực tế không có giao dịch (`total_rows: 0`) trả về giá trị `0.0` với trạng thái `AVAILABLE` và phong bì `OK`.
   - **Xác thực giới hạn thời gian (Temporal Bounds):** Bắt buộc `period_start <= period_end`. Nếu sai ngày trả về `VALIDATION_ERROR`.
3. **Liên kết bằng chứng minh bạch (`EvidenceRef`):**
   - Mỗi chỉ số có trạng thái `AVAILABLE` đều mang `evidence_refs` chứa mã băm (SHA256 checksum) của nguồn báo cáo ERPNext thực tế.
   - Danh sách `evidence_refs` bao gồm: `source_type`, `source_name`, `company`, `filters`, `as_of`, `retrieved_at`, và `checksum_or_version`.
4. **Endpoint REST API chuẩn hóa:**
   - Mở endpoint whitelisted `@frappe.whitelist() def get_financial_snapshot(...)` trong `lotus_fin/lotus_fin/api/ai_insights.py`.

---

## 2. Chi tiết thay đổi mã nguồn (Diff Summary)

| Đường dẫn file | Thao tác | Mô tả thay đổi |
|---|---|---|
| `lotus_fin/lotus_fin/ai/__init__.py` | Tạo mới | Package init đánh dấu module AI của Lotus Fin. |
| `lotus_fin/lotus_fin/ai/financial_snapshot.py` | Tạo mới | Module lõi tính toán FinancialSnapshot, bóc tách P&L, AR, AP, Cash và sinh EvidenceRef. |
| `lotus_fin/lotus_fin/api/ai_insights.py` | Cập nhật | Bổ sung hàm `@frappe.whitelist() get_financial_snapshot` tích hợp guard và adapter báo cáo ERPNext. |
| `lotus_fin/lotus_fin/tests/test_financial_snapshot.py` | Tạo mới | Bộ unit test chuyên sâu 9/9 tests bao phủ đối soát số học, thiếu dữ liệu, lỗi nguồn, phân quyền và kiểm tra biên. |
| `lotus_fin/lotus_fin/tests/test_access_and_reports.py` | Cập nhật | Tích hợp kiểm thử endpoint `get_financial_snapshot` vào test suite hệ thống. |

---

## 3. Kết quả kiểm thử bằng số (Quantitative Test Results)

Toàn bộ 9/9 ca kiểm thử trong bộ `test_financial_snapshot.py` đã vượt qua xuất sắc (**100% PASS**):

```text
E:\lotus-fin> C:\Python313\python.exe -m unittest discover -s lotus_fin/lotus_fin/tests -p "test_financial_snapshot.py"
.........
----------------------------------------------------------------------
Ran 9 tests in 0.026s

OK
```

### Bảng phân tích chi tiết các ca kiểm thử:

| STT | Mã kiểm thử | Tên Test Case | Mục tiêu kiểm chứng | Kết quả |
|:---:|---|---|---|:---:|
| 1 | `F001-NUM-01` | `test_numeric_gold_reconciliation_all_metrics` | Đối soát 100% số liệu với Gold độc lập (Doanh thu 1M, COGS 600k, Gross Margin 40%, AR 50k, Overdue 40%, AP 45k, Cash 250k) | **PASS** |
| 2 | `F001-DATA-01` | `test_missing_pnl_never_becomes_zero` | Thiếu nguồn P&L thì Revenue/COGS/Gross Margin chuyển sang `UNAVAILABLE`, không bịa `0.0`, trạng thái `PARTIAL` | **PASS** |
| 3 | `F001-DATA-02` | `test_empty_company_yields_valid_zero_not_error` | Công ty mới/rỗng không có công nợ trả về `0.0` hợp lệ, trạng thái `AVAILABLE` thay vì báo lỗi | **PASS** |
| 4 | `F001-SRC-01` | `test_source_error_propagation` | Báo cáo bị lỗi timeout/DB được bắt trọn vẹn, trả về `SOURCE_ERROR` an toàn, không sập runtime | **PASS** |
| 5 | `F001-TIME-01` | `test_period_temporal_bounds_validation` | Truyền `period_start > period_end` lập tức bị chặn với `VALIDATION_ERROR` | **PASS** |
| 6 | `F001-AUTH-01` | `test_empty_company_yields_forbidden` | Truy vấn công ty rỗng hoặc không có quyền bị từ chối với `FORBIDDEN`, ẩn danh tính công ty | **PASS** |
| 7 | `F001-LINK-01` | `test_evidence_ref_linkage` | Mọi metric hợp lệ đều truy vết ngược thành công về checksum của EvidenceRef tương ứng | **PASS** |
| 8 | `F001-EDGE-01` | `test_zero_revenue_gross_margin_handled` | Khi Doanh thu = 0.0, Gross Margin xử lý an toàn `UNAVAILABLE`, không gây lỗi chia cho 0 (`ZeroDivisionError`) | **PASS** |
| 9 | `F001-EDGE-02` | `test_zero_total_ar_with_positive_overdue_anomalous_ledger` | Sổ cái bất thường (Tổng nợ = 0 nhưng có nợ quá hạn) xử lý an toàn và gắn limitation cảnh báo | **PASS** |

---

## 4. Dữ liệu mẫu Output của FinancialSnapshot (Sample JSON Payload)

Dưới đây là payload thực tế trả về từ hàm `build_financial_snapshot`:

```json
{
  "feature_id": "AI001",
  "contract_version": "1.0.0",
  "status": "OK",
  "correlation_id": "28f8c101-cb3d-440d-8f9b-178a69014102",
  "company": "Cong Ty TNHH Mau",
  "period": {
    "start": "2026-01-01",
    "end": "2026-12-31"
  },
  "as_of": "2026-09-25T13:29:49.175260Z",
  "snapshot_id": "SNAP-2CC5694272B8",
  "data_mode": "actual",
  "currency": "VND",
  "metrics": [
    {
      "metric_id": "revenue",
      "status": "AVAILABLE",
      "value": 150000000.0,
      "currency_or_unit": "VND",
      "period": { "start": "2026-01-01", "end": "2026-12-31" },
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-2CC5694272B8",
      "evidence_refs": ["15c29212cfe01c26"],
      "limitations": []
    },
    {
      "metric_id": "cogs",
      "status": "AVAILABLE",
      "value": 90000000.0,
      "currency_or_unit": "VND",
      "period": { "start": "2026-01-01", "end": "2026-12-31" },
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-2CC5694272B8",
      "evidence_refs": ["15c29212cfe01c26"],
      "limitations": []
    },
    {
      "metric_id": "gross_margin",
      "status": "AVAILABLE",
      "value": 0.4,
      "currency_or_unit": "ratio",
      "period": { "start": "2026-01-01", "end": "2026-12-31" },
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-2CC5694272B8",
      "evidence_refs": ["15c29212cfe01c26"],
      "limitations": []
    },
    {
      "metric_id": "ar_outstanding",
      "status": "AVAILABLE",
      "value": 25000000.0,
      "currency_or_unit": "VND",
      "period": { "start": "2026-01-01", "end": "2026-12-31" },
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-2CC5694272B8",
      "evidence_refs": ["858d530bc722374a"],
      "limitations": []
    },
    {
      "metric_id": "overdue_ar_ratio",
      "status": "AVAILABLE",
      "value": 1.0,
      "currency_or_unit": "ratio",
      "period": { "start": "2026-01-01", "end": "2026-12-31" },
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-2CC5694272B8",
      "evidence_refs": ["858d530bc722374a"],
      "limitations": []
    },
    {
      "metric_id": "ap_outstanding",
      "status": "AVAILABLE",
      "value": 15000000.0,
      "currency_or_unit": "VND",
      "period": { "start": "2026-01-01", "end": "2026-12-31" },
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-2CC5694272B8",
      "evidence_refs": ["16ec3bb57e989473"],
      "limitations": []
    },
    {
      "metric_id": "cash_balance",
      "status": "AVAILABLE",
      "value": 80000000.0,
      "currency_or_unit": "VND",
      "period": { "start": "2026-01-01", "end": "2026-12-31" },
      "formula_version": "2026.1",
      "snapshot_id": "SNAP-2CC5694272B8",
      "evidence_refs": ["d9abc61344a7df7b"],
      "limitations": []
    }
  ],
  "comparison": null,
  "explanation": {
    "status": "UNAVAILABLE",
    "facts": [],
    "interpretations": [],
    "next_checks": []
  },
  "missing_inputs": [],
  "limitations": [],
  "evidence_refs": [
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Profit and Loss Statement",
      "source_record_id": null,
      "company": "Cong Ty TNHH Mau",
      "filters": { "from_date": "2026-01-01", "to_date": "2026-12-31" },
      "as_of": "2026-09-25T13:29:49.175260Z",
      "retrieved_at": "2026-09-25T13:29:49.187740Z",
      "checksum_or_version": "15c29212cfe01c26"
    },
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Accounts Receivable",
      "source_record_id": null,
      "company": "Cong Ty TNHH Mau",
      "filters": { "from_date": "2026-01-01", "to_date": "2026-12-31" },
      "as_of": "2026-09-25T13:29:49.175260Z",
      "retrieved_at": "2026-09-25T13:29:49.187871Z",
      "checksum_or_version": "858d530bc722374a"
    },
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Accounts Payable",
      "source_record_id": null,
      "company": "Cong Ty TNHH Mau",
      "filters": { "from_date": "2026-01-01", "to_date": "2026-12-31" },
      "as_of": "2026-09-25T13:29:49.175260Z",
      "retrieved_at": "2026-09-25T13:29:49.187985Z",
      "checksum_or_version": "16ec3bb57e989473"
    },
    {
      "source_type": "ERP_NEXT_REPORT",
      "source_name": "Trial Balance",
      "source_record_id": null,
      "company": "Cong Ty TNHH Mau",
      "filters": { "from_date": "2026-01-01", "to_date": "2026-12-31" },
      "as_of": "2026-09-25T13:29:49.175260Z",
      "retrieved_at": "2026-09-25T13:29:49.188020Z",
      "checksum_or_version": "d9abc61344a7df7b"
    }
  ]
}
```

---

## 5. Đánh giá chất lượng mã nguồn (Code Audit & Quality Assessment)

Áp dụng các kỹ năng kiểm định chất lượng:
- **`vibe-code-auditor` (Audit kiến trúc):**
  - **Type & Arithmetic Safety:** Sử dụng `Decimal` chuẩn mực thay cho số chấm động `float` trong mọi phép tính nhạy cảm; triệt tiêu hoàn toàn rủi ro sai số làm tròn số học (floating-point precision leakage).
  - **Resilience:** Mọi trường hợp chia cho 0 (`ZeroDivisionError`) khi doanh thu = 0 hoặc nợ = 0 đều được kiểm tra trước bằng điều kiện phân nhánh, tránh sập tiến trình.
  - **No Bare Excepts:** Tất cả các khối `try/except` đều bắt lỗi cụ thể (`ValueError`, `InvalidOperation`, `TypeError`), ghi nhận limitation rõ ràng và giữ nguyên trạng thái không suy diễn.
- **`vibe-code-cleanup` (Vệ sinh & Tối ưu hóa):**
  - Đã loại bỏ hoàn toàn các cảnh báo `DeprecationWarning` của Python 3.12+ bằng cách thay thế `datetime.utcnow()` sang `datetime.now(timezone.utc)`.
  - Không có mã rác, không có hard-coded secrets hay URL nhạy cảm.
- **`vibecode-production-qa-validator` (Sẵn sàng môi trường Production):**
  - Định dạng chuẩn ISO 8601 UTC timestamp cho các trường thời gian (`as_of`, `retrieved_at`).
  - Hỗ trợ đầy đủ cả 2 môi trường: Chạy trực tiếp bên trong Frappe/ERPNext context và chạy độc lập (standalone engine/unit testing).
