# BƯỚC 6: KẾ HOẠCH KIỂM THỬ TOÀN DIỆN & ĐỐI SOÁT (VERIFICATION MATRIX)

> **Giai đoạn:** Bước 6 / 7 trong quy trình triển khai Lotus Fin  
> **Mục tiêu:** Chạy bộ kiểm thử 6 kịch bản end-to-end (kết nối mạng, đăng nhập Desk, API AI Copilot, Unit tests, kịch bản sốc What-If và đo lường tải tài nguyên thực tế) để đảm bảo hệ thống đạt chuẩn nghiệm thu.  
> **Điều kiện tiên quyết:** Đã hoàn thành [Bước 5: Triển khai Frontend](./STEP_5_FRONTEND_DEPLOYMENT.md).  

---

## 1. MA TRẬN 6 KỊCH BẢN KIỂM THỬ TOÀN DIỆN

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MA TRẬN KIỂM THỬ LOTUS FIN                            │
├─────────────────────┬────────────────────────────────┬──────────────────────┤
│ 1. Network & Ping   │ Kiểm tra Nginx, cổng mạng,     │ HTTP 200 Pong        │
│                     │ chuyển tiếp Docker :8080       │ Phản hồi < 50ms      │
├─────────────────────┼────────────────────────────────┼──────────────────────┤
│ 2. Frappe Desk      │ Đăng nhập Desk Kế toán,        │ Đăng nhập thành công │
│                     │ phân hệ Financial Health       │ Load đầy đủ đồ thị   │
├─────────────────────┼────────────────────────────────┼──────────────────────┤
│ 3. AI Copilot API   │ Gọi endpoint /chat_copilot,    │ Trả về JSON phân tích│
│                     │ xử lý ngôn ngữ tự nhiên        │ Không lỗi quyền truy │
├─────────────────────┼────────────────────────────────┼──────────────────────┤
│ 4. Unit & UI Tests  │ Chạy test suite tự động        │ 15/15 tests PASS     │
│                     │ của phân hệ tài chính          │ Thời gian < 1 giây   │
├─────────────────────┼────────────────────────────────┼──────────────────────┤
│ 5. Stress What-If   │ Mô phỏng kịch bản sốc tài chính│ Đầy đủ ma trận 9 lớp │
│                     │ doanh số giảm 20%, nợ trễ 15d  │ KPI không có NaN/Null│
├─────────────────────┼────────────────────────────────┼──────────────────────┤
│ 6. Resource Audit   │ Đo đạc RAM & CPU của toàn bộ   │ RAM Docker ≤ 1.2 GB  │
│                     │ 9 container khi đang chịu tải  │ RAM trống ≥ 6.0 GB   │
└─────────────────────┴────────────────────────────────┴──────────────────────┘
```

---

## 2. QUY TRÌNH THỰC HIỆN TỪNG KỊCH BẢN CHI TIẾT

Đăng nhập vào máy chủ qua SSH: `ssh root@<YOUR_SERVER_IP>`.

### Kịch bản 1: Kiểm tra kết nối mạng & API Ping
* **Mục đích:** Xác nhận Nginx Host kết nối thông suốt với Docker container Frappe tại cổng `8080`.
* **Lệnh thực thi:**
  ```bash
  echo "--- 1. Kiểm tra Web Root Nginx ---"
  curl -Is http://127.0.0.1/ | head -n 1

  echo "--- 2. Kiểm tra Frappe Ping qua Nginx ---"
  curl -s http://127.0.0.1/api/method/ping
  ```
* **Tiêu chuẩn nghiệm thu:**
  * Request 1 trả về: `HTTP/1.1 200 OK`.
  * Request 2 trả về: `{"message":"pong"}`.

---

### Kịch bản 2: Đăng nhập Frappe Desk & Kiểm tra Workspace
* **Mục đích:** Đảm bảo hệ quản trị ERPNext/Frappe hoạt động ổn định, phân quyền tài chính chính xác.
* **Thao tác:**
  1. Mở trình duyệt truy cập: `http://<YOUR_SERVER_IP>/desk/financial-health`
  2. Đăng nhập với tài khoản:
     * **Username:** `Administrator`
     * **Password:** `admin`
  3. Kiểm tra thanh Sidebar bên trái:
     * Xuất hiện phân hệ **Lotus Fin AI** và **Financial Health**.
     * Bảng điều khiển tải lên các chỉ số: Doanh thu (Revenue), Tỷ suất lợi nhuận gộp (Gross Margin), Vòng quay tiền (Cash Conversion Cycle - CCC), Dòng tiền thuần (Net Cash Flow).
* **Tiêu chuẩn nghiệm thu:** Không có popup cảnh báo lỗi Database hay DocType missing.

---

### Kịch bản 3: Kiểm tra API AI Copilot (Natural Language Dispatcher)
* **Mục đích:** Kiểm tra endpoint `/api/method/lotus_fin.api.copilot_api.chat_copilot` xử lý truy vấn tiếng Việt và điều phối tool trong kiến trúc Clean Architecture.
* **Lệnh thực thi từ terminal:**
  ```bash
  curl -s -X POST "http://127.0.0.1:8080/api/method/lotus_fin.api.copilot_api.chat_copilot" \
       -H "Content-Type: application/json" \
       -d '{"query": "sức khỏe tài chính doanh nghiệp", "company": "Lotus-fin (Demo)"}' | jq .
  ```
* **Tiêu chuẩn nghiệm thu:**
  * JSON trả về chứa kết quả phân tích chỉ số tài chính của công ty `Lotus-fin (Demo)`.
  * Cấu trúc JSON có các trường: `message`, `module_id: "AI001"`, `widgets` với dữ liệu biểu đồ.

---

### Kịch bản 4: Chạy bộ kiểm thử tự động tài chính (Integration Tests)
* **Mục đích:** Xác minh logic tính toán công nợ, nhận diện hóa đơn quá hạn và bảo mật dữ liệu PII trong container.
* **Lệnh thực thi:**
  ```bash
  cd ~/lotus-fin
  ./run.sh test lotus_fin.tests.test_financial_health
  ```
* **Kết quả đo được thực tế:**
  ```text
  Running 15 unspecified-category tests for lotus_fin
  lotus_fin.tests.test_financial_health.TestFinancialHealthMetricsAndComparison
      ✔  test_comparison_block_cross_company_deny
      ✔  test_comparison_block_full_metrics_reconciliation
      ✔  test_compute_previous_period_annual
      ✔  test_compute_previous_period_leap_year
      ✔  test_compute_previous_period_quarterly
      ✔  test_metric_change_negative_growth
      ✔  test_metric_change_negative_to_more_negative
      ✔  test_metric_change_negative_to_positive_transition
      ✔  test_metric_change_none_inputs
      ✔  test_metric_change_positive_growth
      ✔  test_metric_change_zero_previous_denominator_limitation
      ✔  test_metrics_collector_aggregation
      ✔  test_near_term_ap_is_frozen_unavailable
      ✔  test_structured_log_contains_no_pii_or_amounts
      ✔  test_user_id_pseudonymization
  ----------------------------------------------------------------------
  Ran 15 tests in 0.136s
  OK
  ```
* **Tiêu chuẩn nghiệm thu:** 15/15 tests PASS hoàn toàn, không có lỗi assertion hay exception.

---

### Kịch bản 5: Chạy mô phỏng kịch bản sốc tài chính What-If (AI004)
* **Mục đích:** Kiểm tra động cơ tính toán đa biến khi doanh nghiệp gặp cú sốc giảm doanh thu 20% và khách hàng chậm thanh toán 15 ngày.
* **Lệnh thực thi:**
  ```bash
  cd ~/lotus-fin
  ./run.sh simulate
  ```
* **Tiêu chuẩn nghiệm thu:** Trả về đầy đủ cấu trúc ma trận 9 lớp chỉ số KPI tài chính:
  1. `revenue`: -200,000,000 VND (-20%)
  2. `gross_profit`: -80,000,000 VND (-20%)
  3. `gross_margin`: 0.4 (40%)
  4. `ar_outstanding`: +83,333,333 VND (+33.3%)
  5. `dso`: tăng từ 22.5 ngày lên 37.5 ngày (+15 ngày trễ)
  6. `net_cash_flow`: giảm -193,333,333 VND
  7. `ending_cash`: số dư tiền mặt cuối kỳ giảm tương ứng
  8. `ccc`: Vòng quay tiền mặt tăng 15 ngày
  9. `cash_shortfall`: 0 VND (chưa thâm hụt tiền mặt)

---

### Kịch bản 6: Đo lường tài nguyên thực tế (Resource Audit)
* **Mục đích:** Xác minh mức tiêu hao tài nguyên thực tế của toàn bộ 9 container trên máy chủ.
* **Lệnh thực thi:**
  ```bash
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
  ```
* **Bảng chỉ số đo được thực tế:**
  ```text
  NAME                          CPU %     MEM USAGE / LIMIT     MEM %
  frappe_docker-frontend-1      0.00%     8.45MiB / 7.8GiB      0.10%
  frappe_docker-backend-1       0.02%     159.3MiB / 7.8GiB     1.99%
  frappe_docker-queue-long-1    0.00%     100.9MiB / 7.8GiB     1.26%
  frappe_docker-scheduler-1     0.00%     98.9MiB / 7.8GiB      1.24%
  frappe_docker-queue-short-1   0.00%     103.1MiB / 7.8GiB     1.29%
  frappe_docker-websocket-1     0.03%     75.5MiB / 7.8GiB      0.94%
  frappe_docker-db-1            1.72%     225.8MiB / 7.8GiB     2.82%
  frappe_docker-redis-queue-1   0.12%     8.1MiB / 7.8GiB       0.10%
  frappe_docker-redis-cache-1   0.14%     9.0MiB / 7.8GiB       0.11%
  ```
* **Tiêu chuẩn nghiệm thu:**
  * Tổng RAM của 9 container chỉ chiếm **~789 MiB** (~0.77 GB).
  * Bộ nhớ RAM vật lý còn dư trên máy chủ: **> 6.5 GiB**.
  * CPU ở chế độ nghỉ (Idle): **< 2%**.

---

## 3. CHECKLIST ĐÁNH GIÁ CHUNG BƯỚC 6

- [ ] Kịch bản 1: Ping Pong API `200 OK`.
- [ ] Kịch bản 2: Desk Login & Dashboard tải đầy đủ biểu đồ.
- [ ] Kịch bản 3: AI Copilot endpoint phản hồi JSON có cấu trúc.
- [ ] Kịch bản 4: Chạy test suite `test_financial_health` đạt 15/15 OK.
- [ ] Kịch bản 5: Mô phỏng What-If trả về trọn vẹn 9 lớp KPIs.
- [ ] Kịch bản 6: Docker stats xác nhận mức tiêu hao RAM < 1.2 GB.

---

👉 **Chuyển sang:** [BƯỚC 7: TỰ ĐỘNG HÓA CI/CD TỪ GITHUB ACTIONS](./STEP_7_CICD_AUTOMATION.md)
