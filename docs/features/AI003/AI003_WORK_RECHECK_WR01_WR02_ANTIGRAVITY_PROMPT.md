# Antigravity/Zcode prompt — WR-01/WR-02 focused remediation

Bạn là implementation engineer cho **AI001/AI002 foundation**, không xây AI003. Đọc `AGENTS.md`, `docs/features/AI003/evidence/AI003_WORK_RECHECK_2026-09-30.md`, `docs/features/AI003/evidence/AI003_WORK_VERIFICATION_2026-09-30.md`, và đúng các hàm được nêu dưới đây. Giữ nguyên mọi thay đổi có sẵn của working tree. GitNexus impact trước khi sửa, detect-changes trước commit; index hiện chậm 10 commit/FTS thiếu, nên kiểm tra callers bằng code khi graph không đủ. Không tự nâng gate trong SSOT.

## Kết quả đã qua — không làm lại việc không cần thiết

Work đã tự chạy lại **182/182 local, 218/218 Docker**. Site `ai003-verify.localhost` tại 2026-09-26 cho AI001 revenue 8m, AR 6,9m, AP 7,95m, cash 11,55m, overdue ratio 0,2899; AI002 có 4 AR 6,9m và 4 AP 7,95m. Footer list thật từ Frappe đã hoạt động. Chỉ sửa hai lỗ hổng dưới đây và hồi quy liên quan; không viết lại toàn bộ WV-01/02.

## WR-01 — hàng tổng dict không đáng tin bị bỏ qua

Repro tối thiểu:

```python
parse_ar_data([{"is_total_row": True, "outstanding": 123}])  # hiện trả AR=0
_parse_report_rows({"status":"success", "data":[{"is_total_row":True,"outstanding":123}]}, "Accounts Receivable")  # hiện trả []
```

`cashflow/adapters.py:_parse_report_rows` còn bỏ `{"party":"Total","outstanding":123}` ở giữa report khi thiếu voucher. `ai/financial_snapshot.py:parse_ar_data/parse_ap_data` bỏ `is_total_row` bất kể vị trí/shape/provenance. Hãy chỉ bỏ summary dict khi chứng minh được đó là output report hợp lệ của Frappe/ERPNext version đang chạy, với metadata/vị trí/shape phù hợp; nếu không chứng minh được thì typed fail-closed. Kiểm tra cả AR và AP, đầu/giữa/cuối, all-summary, mixed valid+fake, marker truthy giả, amount malformed, total có voucher, no footer và footer list thật. `success + data=[]` thật vẫn là verified zero; fake summary không được thành zero. Đối chiếu test cũ đang expect skip `party="Total"` cuối với raw report behavior, rồi sửa test/contract dựa trên bằng chứng. Không blanket-skip dict hay dùng `party` string một mình làm authority.

## WR-02 — AI001 đếm row dương không có voucher

`parse_ar_data`/`parse_ap_data` chỉ xác minh DB voucher khi `voucher_no`/`name` tồn tại; hàng `{"outstanding":123}` vẫn được cộng vào metric. Với Company trên live site, hàng thiếu định danh không được báo AVAILABLE nếu không có provenance thay thế đã chứng minh từ ERPNext. Dùng mã report tại container để xác định row giao dịch hợp lệ có thể thiếu voucher hay không. Nếu không, reject typed; nếu có, định nghĩa và xác minh định danh/account/party/company thay thế, rồi chứng minh độc lập bằng fixture. Giữ AI001 và AI002 nhất quán về fail-closed, không bịa voucher từ prefix hoặc pattern tên.

## Test và acceptance

1. Thêm test nhỏ cho hai repro nêu trên và trường hợp bình thường: footer list thật, report rỗng thật, dict summary thật nếu được chứng minh, mixed malformed, voucher có/thiếu, AR/AP, row cross-leg. Test phải gọi đường public/service phù hợp để chắc top-level không trả metric zero hoặc obligations rỗng giả khi source sai.
2. Chạy 7 suite local; chạy Docker discovery; replay site cô lập `ai003-verify.localhost` với oracle tại 2026-09-20 (AR 8m/AP 9,5m/cash 12m) và 2026-09-26 (AR 6,9m/AP 7,95m/cash 11,55m). Không sửa `frontend`, không thay đổi fixture để số khớp.
3. Chỉ tra cứu docs/source Frappe/ERPNext chính thức trên mạng nếu mã cài trong container không giải đáp được shape của dict summary hoặc voucher identity. Ghi link/version và kết luận; không crawl web rộng.
4. Xuất báo cáo ngắn `docs/features/AI003/AI003_WR01_WR02_REMEDIATION_REPORT.md`: root cause, file/dòng sửa, before→after repro, test command và kết quả thật, live oracle, giới hạn, GitNexus result. Không ghi Work PASS hoặc contract freeze. Không commit nếu detect-changes không đủ dữ liệu hoặc test cần thiết chưa chạy.

**Stop condition:** nếu một kiểu summary/voucher không thể được chứng minh là hợp lệ, giữ fail-closed và ghi rõ quyết định cần Work/Chat; hoàn thành phần độc lập còn lại. Handoff cho Work để kiểm chứng lại. AI003 engine, threshold, severity và signal gold nằm ngoài scope lượt này.
