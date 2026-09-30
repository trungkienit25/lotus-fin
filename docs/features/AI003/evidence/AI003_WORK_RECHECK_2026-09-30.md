# AI003 foundation — Work recheck sau remediation (2026-09-30)

## Đã xác minh độc lập

- 182/182 unit test của 7 suite AI001/AI002 qua trên workspace; 218/218 test discovery qua trong Docker backend, gồm AI001 evaluation 15/15. Đây là kết quả tôi chạy lại, không chỉ chép từ báo cáo Antigravity.
- Trên site cô lập `ai003-verify.localhost`, cutoff 2026-09-26: AI001 `PARTIAL` do COGS/gross margin và near-term AP chưa có authority, nhưng revenue 8.000.000, AR 6.900.000, overdue ratio 0,2899, AP 7.950.000, cash 11.550.000 đều `AVAILABLE` và khớp oracle voucher/GL. AI002 đọc 4 AR = 6.900.000 và 4 AP = 7.950.000. `frontend` không được dùng cho replay.
- Footer list từ Frappe được tách ở `extract_key_report_data`; preflight Party Type và voucher checks đã được thêm. GitNexus `impact extract_key_report_data` cho 3 caller/LOW nhưng index chậm 10 commit và FTS thiếu; không lấy graph này làm bằng chứng regression đầy đủ.

## Finding còn mở

**WR-01 — Dict summary giả có thể bị bỏ qua và tạo zero giả.** `parse_ar_data`/`parse_ap_data` bỏ qua bất cứ dict nào có `is_total_row` truthy trước khi xác minh vị trí, shape, report provenance hoặc amount. `_parse_report_rows` của AI002 làm tương tự và còn bỏ `party="Total"` không voucher ở bất cứ vị trí nào. Probe cục bộ: `parse_ar_data([{"is_total_row": true, "outstanding": 123}])` trả `AR=0`; `_parse_report_rows({"status":"success","data":[{"is_total_row":true,"outstanding":123}]}, "Accounts Receivable")` trả `[]`; dict `party="Total"` ở giữa report cũng bị adapter âm thầm bỏ. Report đầu vào hợp lệ thực tế đã có list footer tách bằng metadata, nên không được suy rằng các dict này luôn là summary đáng tin. Bộ test hiện tại còn cố ý expect skip dict `party="Total"` cuối; cần xác minh dạng report Frappe thực rồi chỉnh contract/test tương ứng.

**WR-02 — AI001 cộng AR không có voucher/provenance.** `parse_ar_data`/`parse_ap_data` chỉ chạy DB voucher verification nếu `voucher_no` hoặc `name` có giá trị. Một hàng `{ "outstanding": 123 }` vẫn được AI001 tính thành `AVAILABLE=123` (probe cục bộ), ngay cả khi caller truyền company. AI002 từ chối positive obligation thiếu voucher. Cần fail closed hoặc chứng minh có loại report row hợp lệ nào không có voucher bằng mã ERPNext đúng version và một định danh nguồn thay thế đáng tin. Không sửa công thức để hợp thức hóa hàng thiếu nguồn.

Các finding này giữ **Work verification chưa PASS** dù numeric happy path đã qua. WV-03 vẫn còn: COGS mapping, `as_known_at`, gold signal/threshold và live cache revocation chưa được Work chứng minh. G1 `PARTIAL`, G2 `PARTIAL`, G3/G4A `BLOCKED`, G4B `NOT_APPLICABLE_YET`, contract freeze `NOT_READY`. Bước tiếp theo là Antigravity/Zcode sửa WR-01/02 rồi Work replay lại adversarial + live oracle; Chat quyết định contract sau khi đủ gate.
