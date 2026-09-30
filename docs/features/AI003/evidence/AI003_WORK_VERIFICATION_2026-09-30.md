# AI003 Work verification — 2026-09-30

## Phạm vi và môi trường

- Chỉ kiểm tra foundation AI001/AI002 và nguồn ứng viên AI003; chưa chạy AI003 engine hay quyết định threshold.
- Docker image `lotus-fin:ai003-local` chứa working tree hiện tại. Site mới `ai003-verify.localhost` nằm riêng với site đang dùng `frontend`; Frappe 16.34.0, ERPNext 16.35.0, Lotus Fin 0.0.1.
- Trên site cô lập: cài ERPNext và Lotus Fin, `bench --site ai003-verify.localhost migrate` thành công, `Company.ai002_approved_cash_accounts` có mặt, timezone đặt `Asia/Ho_Chi_Minh`. `frontend` vẫn có timezone `Africa/Abidjan` và chưa có cột này.
- Fixture synthetic dùng `docs/features/AI002/fixture_scripts/{setup,transactions,payments,verify}.py`. Vì site mới chưa chạy ERPNext Setup Wizard, chỉ trên site cô lập đã tạo master data tối thiểu: Warehouse Type, Item Group, UOM, Customer/Supplier Group, Territory, Price List, 3 Customer, 3 Supplier và Party Type `Customer→Receivable`, `Supplier→Payable`. Không được suy rằng install-app/migrate tự tạo những master data đó.
- 159/159 unit test đã qua trên máy và Docker ở bước trước. Lượt này là live site replay; không coi unit pass là bằng chứng runtime pass.

## Oracle độc lập từ voucher/GL synthetic

Oracle dưới đây đọc Sales/Purchase Invoice, Payment Entry và GL Entry đã submit, không gọi hàm tính AI001/AI002. Các số là VND của Company `AI002 Fixture 2026`.

| Cutoff | AR outstanding | AP outstanding | Cash từ GL | Diễn giải |
| --- | ---: | ---: | ---: | --- |
| 2026-09-20 | 8.000.000 | 9.500.000 | 12.000.000 | Trước bốn Payment Entry ngày 22/09. |
| 2026-09-26 | 6.900.000 | 7.950.000 | 11.550.000 | Sau thanh toán 1,1 triệu AR và 1,55 triệu AP. |

Tại 26/09, AR quá hạn theo `due_date < cutoff` là 2.000.000; tỷ lệ = 2.000.000 / 6.900.000 ≈ 0,289855. Doanh thu dịch vụ từ năm Sales Invoice là 8.000.000. Đây là oracle số nguồn, **chưa phải** `AI003_GOLD_MANIFEST` hay verdict `AR_OVERDUE_SPIKE`/`AP_DUE_CLUSTER`: threshold, denominator policy và rule version chưa được duyệt.

## Kết quả replay

| Kiểm tra | Kết quả quan sát |
| --- | --- |
| Migration/scope | Site cô lập có cột scope; `get_ai002_cash_account_scope` trả `RESOLVED/APPROVED`, scope `["Cash - A2F"]`. |
| ERPNext AR/AP đúng master data | Mỗi report có 4 hàng dict giao dịch, đúng một phía; AR = 6,9 triệu, AP = 7,95 triệu tại 26/09. Ở 20/09 lần lượt 8 triệu và 9,5 triệu. |
| ERPNext total footer | Frappe `query_report.run` còn thêm một hàng cuối kiểu `list` vào **cả hai** report. `add_total_row=true`, `skip_total_row=0`; chiều dài footer bằng số columns (AR 25, AP 24). `extract_key_report_data` hiện giữ footer trong `data`. |
| AI001 live | Revenue 8 triệu và cash 11,55 triệu `AVAILABLE`, khớp oracle. AR/AP `UNAVAILABLE`, top `PARTIAL`: parser chặn hàng footer không phải dict. COGS/gross margin cũng `UNAVAILABLE` vì không cô lập được hàng COGS; chưa tuyên bố zero. |
| AI002 live | Scope `APPROVED` nhưng forecast `SOURCE_ERROR / DATA_PIPELINE_ERROR`, không trả obligations/points: AR payload contains malformed rows. |
| Chẩn đoán tạm trong bộ nhớ | Khi bỏ **chỉ** footer cuối đã nhận diện rồi gọi lại các hàm hiện tại, AI001 ra AR 6,9 triệu, AP 7,95 triệu, overdue ratio 0,2899; AI002 đọc 4 AR + 4 AP obligations đúng tổng. Đây không phải bản vá production hay bằng chứng pass. |
| Input fail-closed | AI001 invalid `as_of`, `as_of` trước kỳ và USD trên Company VND đều `VALIDATION_ERROR`; AI002 `finance_book` trả `VALIDATION_ERROR`. Các trường hợp đó không có financial payload. |
| Quyền | Guest và Accounts User bị giới hạn sang Company khác đều `FORBIDDEN` trên AI001/AI002, không có metric/obligation/point. Accounts User có quyền Company đọc được AI001 (vẫn `PARTIAL` do footer); AI002 vẫn `SOURCE_ERROR`. Người dùng và Company tạm trong probe đã rollback và được xác nhận không còn. |
| Thời gian | Report AR/AP và GL phân biệt cutoff 20/09 với 26/09 như oracle. Điều này chứng minh posting-date replay của fixture này; **không** chứng minh `as_known_at` cho chứng từ backdate/correction. |

## Finding cần remediation

**WV-01 — ERPNext total footer chặn AR/AP hợp lệ.** `financial_snapshot.py:parse_ar_data/parse_ap_data` và `cashflow/adapters.py:_parse_report_rows` từ chối mọi non-dict row, đúng với malformed input bất kỳ nhưng chưa nhận diện total footer có metadata của `frappe.desk.query_report.run`. Kết quả live là AI001 `PARTIAL` và AI002 `SOURCE_ERROR` dù có voucher hợp lệ. Zcode cần chuẩn hóa tại boundary báo cáo theo `add_total_row`/shape đã xác minh, hoặc một cách tương đương có bằng chứng; vẫn từ chối non-dict ở giữa, footer sai shape, missing amount, mixed valid/malformed rows, unknown status, missing/non-list `data`. Không blanket-skip mọi `list`.

**WV-02 — Thiếu Party Type master có thể làm sai nghĩa AR/AP.** Trước khi thêm mapping chuẩn, `get_party_types_from_account_type` trả `[]` cho cả Receivable và Payable; mỗi report trả 8 hàng Customer+Supplier, tổng 14,85 triệu dù truyền `party_type`. Sau khi thêm mapping chuẩn trên site cô lập, report tách đúng. Probe thuần dữ liệu cho `_collect_obligations` chứng minh một hàng `Supplier / Purchase Invoice` trong nhánh AR hiện được gán `type=AR`, `source_ref=Sales Invoice:PI-TEST-1`. Nếu chỉ sửa WV-01, cấu hình Party Type thiếu/sai có thể tạo obligation sai. Zcode cần kiểm tra loại đối tác/voucher/account phù hợp từng nguồn và fail closed khi không khớp; site preflight phải phát hiện master data chưa sẵn sàng. Không tự tạo Party Type trong sản phẩm nếu chưa có chính sách ERPNext được duyệt.

**WV-03 — P&L/COGS và signal gold còn thiếu.** Revenue fixture khớp 8 triệu; COGS/gross margin vẫn `UNAVAILABLE` do mapping chưa chứng minh. `as_known_at`, temporal correction/cancellation, độc lập gold signal, threshold/severity/denominator và false-positive cases chưa xác minh. Cache-hit role revocation trên live site chưa replay được vì WV-01 ngăn tạo response có thể cache; 32 remediation unit tests là bằng chứng ở mức unit, không thay thế live test.

## Gate và vòng kế tiếp

Foundation code/unit: `PASS`. Work verification: **đã chạy, phát hiện WV-01/WV-02; chưa PASS**. G1 `PARTIAL`, G2 `PARTIAL`, G3 `BLOCKED`, G4A `BLOCKED`, G4B `NOT_APPLICABLE_YET`; `CONTRACT FREEZE: NOT_READY`.

Giao Zcode/Antigravity sửa WV-01/WV-02 theo finding và test hồi quy với payload Frappe v16 thật, trường hợp Party Type thiếu, row cross-leg, footer sai/vị trí giữa, malformed amount và quyền bị thu hồi. Sau đó Work chạy lại unit + isolated-site numeric/role/temporal replay và tiếp tục oracle/signal contract. Giữ site `ai003-verify.localhost` cùng fixture synthetic để tái kiểm tra; không áp migration hoặc timezone lên `frontend` trong lượt này.
