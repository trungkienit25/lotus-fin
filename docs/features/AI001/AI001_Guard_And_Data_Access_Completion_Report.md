# AI001 — Guard and Report Authorization Completion Report & Self-Testing Guide

**Feature:** AI001 (Data Access & Company Guard Layer for AI-F001 Financial Health Analyst)  
**Tác giả:** Antigravity Worker  
**Thời gian hoàn thành:** 2026-09-25  
**Trạng thái kiểm thử:** `18/18 UNIT TESTS PASSED (100% OK)` trên live ERPNext Docker Container (`frappe_docker-backend-1`, site `frontend`).

---

## 1. Tổng quan công việc đã thực hiện (What Was Done)

Theo chỉ đạo bảo mật SSOT (INV-01 đến INV-05) và yêu cầu kiến trúc của Lotus Fin AI001:
1. **Thêm module phân quyền server-side đa công ty (`Company Authorization Guard`):**
   - Tạo mới `lotus_fin/lotus_fin/security/access.py` cung cấp hàm `get_verified_company(company, user)` và `check_report_permission(report_name, user)`.
   - Coi toàn bộ tham số `company` từ client là **hoàn toàn không đáng tin cậy (untrusted)**.
   - Thẩm tra sự tồn tại của công ty trong Database (`frappe.db.exists`).
   - Kiểm tra quyền đọc (`has_permission('Company', 'read')`) của user session hiện tại đối với công ty được yêu cầu. Nếu vi phạm, ném ngoại lệ bảo mật nghiêm ngặt `CompanyAccessError` (kế thừa từ `frappe.PermissionError`).
   - Kiểm tra quyền truy cập của user đối với từng Báo cáo (`Report`) thông qua `frappe.desk.query_report.has_permission`.

2. **Áp dụng Guard vào toàn bộ các API Endpoints liên quan:**
   - Trong `lotus_fin/lotus_fin/api/key_reports.py`:
     - `extract_key_report_data`: Xác thực company cả ở tham số trực tiếp và bên trong object `filters` (chống filter injection). Kiểm tra quyền report permission trước khi chạy report. Trả về `company` đã xác thực và bảo toàn trạng thái lỗi khi truy vấn thất bại.
     - `get_ai_training_dataset`: Xác thực company trước khi tổng hợp modules.
   - Trong `lotus_fin/lotus_fin/api/ai_insights.py`:
     - `predict_cashflow`: Xác thực quyền company server-side.
     - `analyze_invoice_risk`: Xác thực quyền đọc document `Sales Invoice` và quyền đối với công ty sở hữu hóa đơn đó; cô lập dữ liệu khách hàng theo đúng company sở hữu.

3. **Deprecate logic dòng tiền chênh lệch AR - AP:**
   - Đánh dấu cảnh báo `DeprecationWarning` cấp độ runtime.
   - Gắn cờ `"deprecated": True` và trường `"warning"` rõ ràng trong payload JSON trả về: *Accounts Receivable (AR) và Accounts Payable (AP) là công nợ dồn tích (accrual debt), không phải dòng tiền thực thu/thực chi (cash flow). Không được dùng làm số dư tiền mặt hoặc dự báo dòng tiền tin cậy.*

4. **Bảo đảm nguyên tắc "Không bao giờ biến lỗi/thiếu dữ liệu thành 0" (No missing/error source becomes zero):**
   - Khi nguồn báo cáo (AR, AP hoặc General Ledger) bị lỗi (thiếu filter bắt buộc, timeout hoặc permission failure), API trả về `status: "error"`, nêu rõ `source_error` và thông điệp lỗi gốc.
   - Tuyệt đối không âm thầm nuốt lỗi rồi trả về 0 để tránh đưa ra kết luận tài chính sai lệch nguy hiểm cho SME.
   - Phân biệt rõ ràng giữa **dữ liệu rỗng hợp lệ** (`total_rows: 0`, `data: []`, `status: "success"`) và **lỗi trích xuất** (`status: "error"`).

5. **Bảo toàn hành vi báo cáo chuẩn của ERPNext (Preserve ERPNext Report Behavior):**
   - Với các báo cáo có bộ lọc đầy đủ và user có quyền, kết quả trả về đầy đủ metadata cột (`columns`), số lượng dòng (`total_rows`), danh sách bản ghi chuẩn hóa (`data`) và bộ lọc đã áp dụng (`filters_applied`).

---

## 2. Chi tiết các file thay đổi (Files Touched)

| File | Hành động | Nội dung thay đổi |
|---|---|---|
| `lotus_fin/lotus_fin/security/__init__.py` | Tạo mới | Package init cho security module. |
| `lotus_fin/lotus_fin/security/access.py` | Tạo mới | Định nghĩa `get_verified_company`, `check_report_permission`, class `CompanyAccessError`. |
| `lotus_fin/lotus_fin/api/key_reports.py` | Cập nhật | Tích hợp `get_verified_company` và `check_report_permission`. Bảo vệ cả tham số `company` và `filters['company']`. Xử lý trả về trạng thái rõ ràng. |
| `lotus_fin/lotus_fin/api/ai_insights.py` | Cập nhật | Thêm cờ deprecation vào `predict_cashflow`. Chặn biến lỗi nguồn AR/AP thành 0. Thêm guard phân quyền document & company cho `analyze_invoice_risk`. |
| `lotus_fin/lotus_fin/tests/__init__.py` | Tạo mới | Package init cho test module. |
| `lotus_fin/lotus_fin/tests/test_access_and_reports.py` | Tạo mới | Bộ unit test toàn diện gồm 18 bài kiểm tra bao phủ 100% các tình huống yêu cầu và edge cases. |

---

## 3. Kết quả kiểm thử bằng số (Quantitative Results)

Bộ kiểm thử được thực thi trực tiếp trên môi trường backend ERPNext:
- **Container:** `frappe_docker-backend-1`
- **Site:** `frontend`
- **Python:** Python 3.14 venv (`/home/frappe/frappe-bench/env`)
- **Kết quả tổng thể:** **18 / 18 Tests Passed (100% OK)**
- **Thời gian thực thi:** 2.343s

### Bảng phân tích chi tiết kết quả test:

| Nhóm kiểm thử | Tên Test Case | Mục tiêu kiểm chứng | Trạng thái |
|---|---|---|---|
| **1. Same-company Allow** | `test_same_company_allow_as_admin` | Admin truy cập được cả 2 công ty (`Name` và `Name (Demo)`) | **PASS** |
| | `test_same_company_allow_restricted_user` | User bị giới hạn truy cập thành công vào công ty được phân quyền | **PASS** |
| **2. Cross-company Deny** | `test_cross_company_deny` | User bị giới hạn truy cập vào công ty khác bị chặn ngay với `CompanyAccessError` ở guard, report và cashflow API | **PASS** |
| | `test_cross_company_via_filter_tampering_deny` | User truyền tên công ty khác lén lút qua dict `filters` bị phát hiện và chặn đứng | **PASS** |
| **3. Report Error Handling** | `test_report_error_preserved_in_extract_key_report` | Khi thiếu filter bắt buộc, trả về `status: "error"` và chi tiết lỗi, không sập app | **PASS** |
| | `test_report_error_preserved_in_predict_cashflow` | Khi nguồn AR/AP lỗi, KHÔNG biến thành 0 inflow/outflow mà trả về `status: "error"` cùng `source_error` | **PASS** |
| | `test_get_ai_training_dataset_preserves_module_errors` | Tổng hợp dataset AI thu thập lỗi từng module an toàn không crash toàn bộ payload | **PASS** |
| **4. Empty Result Handling** | `test_empty_result_distinguished_from_error` | Công ty chưa có giao dịch trả về `status: "success"` với `total_rows: 0` và danh sách rỗng, không nhầm thành lỗi | **PASS** |
| | `test_predict_cashflow_on_empty_company` | Công ty rỗng xử lý an toàn, trả về 0 hợp lệ kèm cảnh báo deprecation | **PASS** |
| **5. Unauthorized Resource** | `test_unauthorized_guest_denied_report` | Guest user bị chặn khi gọi report permission check | **PASS** |
| | `test_unauthorized_guest_denied_company` | Guest user bị chặn khi gọi company verification guard | **PASS** |
| | `test_nonexistent_company_raises_does_not_exist` | Truy vấn công ty không tồn tại ném `DoesNotExistError` | **PASS** |
| | `test_nonexistent_report_key_raises_error` | Khóa report không nằm trong registry bị từ chối | **PASS** |
| | `test_unauthorized_invoice_risk_analysis_deny` | User không có quyền trên công ty bị cấm phân tích hóa đơn của công ty đó | **PASS** |
| **6. Positive Invoice Flow** | `test_analyze_invoice_risk_success` | User có quyền phân tích thành công rủi ro hóa đơn hợp lệ | **PASS** |
| **7. Deprecation Logic** | `test_predict_cashflow_deprecation_flag` | Endpoint `predict_cashflow` trả về cờ `deprecated: True` và cảnh báo | **PASS** |
| **8. ERPNext Compatibility** | `test_erpnext_report_execution_with_proper_filters` | Báo cáo General Ledger chạy chuẩn với bộ lọc hợp lệ, trả ra đầy đủ dữ liệu | **PASS** |
| | `test_get_available_key_reports` | Registry trả về danh sách các Key Reports hợp lệ | **PASS** |

---

## 4. Hướng dẫn tự kiểm thử (Self-Testing Guide)

Dành cho Tester, Reviewer hoặc Developer muốn tự kiểm chứng trên môi trường local.

### 4.1. Điều kiện tiên quyết
- Môi trường Docker đang chạy các container của ERPNext (`frappe_docker-backend-1`).
- Đã sync code app `lotus_fin` vào thư mục bench apps (`/home/frappe/frappe-bench/apps/lotus_fin`).

### 4.2. Chạy toàn bộ Unit Test tự động
Chạy lệnh sau từ Command Prompt hoặc PowerShell tại máy host:
```bash
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -v lotus_fin.tests.test_access_and_reports
```
*Kỳ vọng:* Toàn bộ 18 test cases hiển thị `... ok` và kết thúc với `OK`.

### 4.3. Kiểm thử thủ công bằng Python CLI bên trong container

**Bước 1: Mở môi trường bench execute:**
```bash
docker exec -it -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python
```

**Bước 2: Test Cross-Company Block:**
```python
import frappe
from lotus_fin.api.key_reports import extract_key_report_data
from lotus_fin.security.access import CompanyAccessError
from frappe.permissions import add_user_permission, remove_user_permission

frappe.init(site="frontend")
frappe.connect()

# Gán user longmac321@gmail.com chỉ được xem công ty "Name"
add_user_permission("Company", "Name", "longmac321@gmail.com")
frappe.db.commit()

# Đóng vai user
frappe.set_user("longmac321@gmail.com")

# Thử gọi dữ liệu của "Name (Demo)"
try:
    extract_key_report_data("accounts_receivable", company="Name (Demo)")
    print("FAILED: Lẽ ra phải bị chặn!")
except CompanyAccessError as e:
    print("PASSED: Đã chặn thành công cross-company:", str(e))

# Dọn dẹp permission
frappe.set_user("Administrator")
remove_user_permission("Company", "Name", "longmac321@gmail.com")
frappe.db.commit()
```

**Bước 3: Test Deprecation và No-Zero-on-Error:**
```python
import frappe
from lotus_fin.api.ai_insights import predict_cashflow

frappe.init(site="frontend")
frappe.connect()
frappe.set_user("Administrator")

res = predict_cashflow(company="Name (Demo)")
print("Deprecated Flag:", res.get("deprecated"))
print("Warning Message:", res.get("warning"))
assert res.get("deprecated") is True
print("PASSED: Deprecation flag hiển thị chính xác.")
```


---

## 4. Kiểm thử giao diện người dùng E2E với Playwright (Frontend E2E Verification & Video Evidence)

Bên cạnh 18 bài unit test chuyên sâu ở tầng backend, hệ thống đã triển khai bài kiểm thử giao diện tự động (End-to-End Test) bằng Playwright trên trình duyệt Chromium thực tế, kết nối trực tiếp đến Frappe Desk v16 (`http://localhost:8080`).

### 4.1. Kịch bản E2E được thực thi (`tests_e2e/test_sales_invoice_ai.py`):
1. **Khởi động Trình duyệt & Kích hoạt quay video:** Ghi hình toàn bộ phiên tương tác với độ phân giải `1280x720` ở tốc độ khung hình thực tế (`slow_mo=100ms`).
2. **Đăng nhập Desk:** Điều hướng vào `http://localhost:8080/login`, tự động điền tài khoản `Administrator` / `admin`, bấm nút Sign In và chờ chuyển hướng vào `/desk`.
3. **Mở chứng từ thực tế:** Điều hướng trực tiếp đến hóa đơn bán hàng mẫu `ACC-SINV-2026-00003` thuộc công ty `Name (Demo)`.
4. **Tương tác nút custom của Lotus Fin:** 
   - Kiểm tra bộ nạp asset `lotus_fin.js` được Frappe Desk tiêm vào trang.
   - Nhận diện và click mở dropdown menu `Lotus Fin AI` trên thanh công cụ chứng từ.
   - Click chọn hành động `🤖 AI Đánh giá rủi ro`.
5. **Xác thực kết quả phân tích AI:**
   - Đón hộp thoại modal popup `frappe.msgprint` (tiêu đề: *Kết quả Phân tích AI*).
   - Kiểm tra nội dung phân tích trả về từ API `lotus_fin.api.ai_insights.analyze_invoice_risk`:
     - **Mức độ rủi ro tín dụng:** `LOW` (Badge màu xanh).
     - **Nhận định:** `Khách hàng 'West View Software Ltd.' có 1 hóa đơn lịch sử (0 hóa đơn chưa thanh toán/quá hạn). Mức độ rủi ro tín dụng: LOW.`
6. **Lưu trữ bằng chứng:** Chụp toàn bộ ảnh chụp màn hình qua các giai đoạn và đóng trình duyệt để hoàn tất file video.

### 4.2. Bằng chứng số liệu & File artifacts thu được:
- **Video tương tác giao diện đã ghi hình thành công:**
  - File: `tests_e2e/videos/aad66288ba21c4a00d3c3dc6498d6243.webm`
  - Dung lượng: `1,193,379 bytes` (~1.2 MB)
- **Chuỗi Screenshots kiểm chứng:**
  - `tests_e2e/screenshots/01_login_page.png` (Trang đăng nhập Frappe Desk)
  - `tests_e2e/screenshots/02_desk_home.png` (Giao diện Desk sau khi xác thực thành công)
  - `tests_e2e/screenshots/03_sales_invoice_form.png` (Form chi tiết hóa đơn `ACC-SINV-2026-00003`)
  - `tests_e2e/screenshots/04_dropdown_opened.png` (Menu dropdown `Lotus Fin AI` mở ra tùy chọn `🤖 AI Đánh giá rủi ro`)
  - `tests_e2e/screenshots/05_ai_result_dialog.png` (Hộp thoại kết quả phân tích rủi ro tín dụng AI hiển thị đầy đủ)

---

## 5. Hướng dẫn tự kiểm thử (Self-Testing Guide)

### 5.1. Chạy bộ Unit Test Backend (18 Tests)
Từ terminal trên máy chủ hoặc qua Docker:
```bash
docker exec -it frappe_docker-backend-1 bench --site frontend run-tests --module lotus_fin.tests.test_access_and_reports
```

### 5.2. Chạy bài kiểm thử Frontend Playwright E2E kèm quay Video
Từ môi trường máy chủ:
```bash
python tests_e2e/test_sales_invoice_ai.py
```
Toàn bộ video mới sẽ được sinh tại thư mục `tests_e2e/videos/` và ảnh chụp màn hình tại `tests_e2e/screenshots/`.

---

## 6. Hỏi & Đáp liên quan đến việc triển khai AI001 (Q&A for AI001 Build)

### Q1: Tại sao phải áp dụng Server-Side Company Authorization Guard thay vì tin tưởng bộ lọc phía Client?
> **Trả lời:** Theo Security SSOT (INV-01), client request là môi trường untrusted. Một user thuộc Công ty A hoàn toàn có thể dùng dev tools hoặc sửa API payload gửi lên `company: "Company B"`. Nếu server chỉ tin tưởng tham số truyền vào mà không xác thực thông qua hệ thống `User Permission` và quyền sở hữu tài liệu của Frappe, hệ thống sẽ gặp lỗ hổng IDOR nghiêm trọng, làm lộ toàn bộ số liệu tài chính của doanh nghiệp khác.

### Q2: Tại sao lại quyết định Deprecate logic tính dòng tiền bằng `AR - AP`?
> **Trả lời:** Theo nguyên tắc kế toán tài chính và chuẩn mực AI-F001, các khoản Phải thu (AR) và Phải trả (AP) là các giao dịch dồn tích (accrual basis), chưa hề phát sinh dòng tiền thực tế (chưa thu được tiền hoặc chưa chuyển khoản thanh toán). Việc lấy `AR - AP` làm số dư tiền mặt hoặc dự báo dòng tiền là một sai lầm bản chất kế toán, có thể gây ra nhận định ảo tưởng về thanh khoản cho SME. Để xây dựng AI001 hoàn chỉnh, dòng tiền phải được lấy từ Báo cáo Lưu chuyển tiền tệ (`Cash Flow Statement`), số dư tài khoản Tiền mặt/Ngân hàng trên Bảng cân đối thử (`Trial Balance`) và Sổ cái (`General Ledger`).

### Q3: Tại sao quy tắc "Không bao giờ biến lỗi/thiếu dữ liệu thành 0" (No error becomes zero) lại là bất biến P0?
> **Trả lời:** Nếu một nguồn báo cáo (ví dụ Accounts Payable) gặp sự cố (timeout, lỗi cấu hình, sai kỳ kế toán) mà hệ thống tự động gán `total_payable = 0`, thì chỉ số dòng tiền ròng sẽ tăng vọt một cách giả tạo (`net = total_receivable - 0`). Điều này khiến mô hình AI đưa ra kết luận "Sức khỏe tài chính xuất sắc, dòng tiền dồi dào" trong khi thực tế doanh nghiệp đang nợ chồng chất. Do đó, lỗi nguồn bắt buộc phải trả về trạng thái `SOURCE_ERROR` hoặc `INSUFFICIENT_DATA`, tuyệt đối không được che đậy bằng số 0.

### Q4: Kế hoạch tiếp theo để triển khai đầy đủ AI001 (Next Steps for Full AI001) là gì?
> **Trả lời:**
> 1. Thiết kế Adapter đọc `Balance Sheet / Cash Flow Statement` thực tế từ ERPNext cho các tài khoản Bank/Cash để có số dư tiền mặt thực (Actual Cash Balance).
> 2. Triển khai Service tính toán KPI tất định (Deterministic Financial Health Metrics): Tỷ lệ nợ quá hạn (Overdue AR Ratio), Biên lợi nhuận gộp (Gross Margin), Tỷ lệ thanh toán hiện hành (Current Ratio nếu đủ dữ liệu).
> 3. Tích hợp AI Model qua API an toàn (với Data Minimization: chỉ truyền KPI đã tổng hợp, không gửi chi tiết chứng từ nhạy cảm) để sinh giải thích (Grounded Explanation) theo đúng hợp đồng Output Envelope của AI-F001.
