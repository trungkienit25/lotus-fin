# Work verification — WR-01/WR-02 sau Zcode

Ngày: 2026-09-30. Revision: `c6f4cd1` (`fix(ai003): fail-closed WR-01/WR-02`). Phạm vi: sửa foundation AI001/AI002 và chuẩn bị môi trường trước AI003. Không có AI003 engine được kiểm chứng trong lượt này.

## Kết quả độc lập

- Workspace: chạy lại 7 unittest suite AI001/AI002, **197 passed / 0 failed**.
- Docker backend: chạy lại full discovery, **233 passed / 0 failed**, AI001 evaluation **15/15**. Sau đóng image và tạo lại dịch vụ, full discovery vẫn **233/233**.
- Đọc mã và test WR mới: unverified dict summary (`is_total_row` truthy hoặc `party=Total` không voucher) bị typed reject; AI001 row không voucher bị reject trước khi cộng metric; genuine empty vẫn verified zero. Các fixtures cũ được bổ sung identity, không thay số để làm test xanh.
- Live injection trên `ai003-verify.localhost`: fake `is_total_row`, fake `party=Total`, positive row thiếu voucher đều làm AI001 `ar_outstanding=UNAVAILABLE`, `value=None`, AR xuất hiện trong `missing_inputs`. AI002 summary/mixed-source fail-closed có unit evidence; live injection script chỉ thử clean AI002 read, không được coi là live poisoned AI002 service test.

## Numeric replay

Replay source thật qua `extract_key_report_data` và AI002 service, đối chiếu với oracle voucher/GL độc lập đã khóa ở báo cáo Work trước:

| Cutoff | AI001 AR | AI001 AP | AI001 cash | AI002 obligations | Overdue AR ratio |
| --- | ---: | ---: | ---: | --- | ---: |
| 2026-09-20 | 8.000.000 | 9.500.000 | 12.000.000 | 5 AR = 8m; 5 AP = 9,5m | 0,0 |
| 2026-09-26 | 6.900.000 | 7.950.000 | 11.550.000 | 4 AR = 6,9m; 4 AP = 7,95m | 0,2899 |

Revenue 8m tại cả hai cutoff. AI001 top-level `PARTIAL` do COGS/gross margin và near-term AP chưa chứng minh. AI002 `FORECAST_UNAVAILABLE / NO_CONFIRMED_SETTLEMENT_EVENTS` là kết quả đúng khi chỉ có obligation và chưa có verified future settlement source. Không dùng obligation due date làm ngày tiền thực thu/chi.

## Runtime alignment đã hoàn tất cho môi trường kiểm chứng

Zcode trước đó chỉ chép mã vào running backend. Work đã build lại `lotus-fin:ai003-local` từ revision hiện tại bằng Dockerfile có sẵn, rồi tạo lại backend, frontend, queue-short, queue-long, scheduler, websocket với Compose hiện hành và `--no-deps`. Cả sáu dùng cùng image ID `sha256:220e4f5dc54973a3bef476a9ef37ca1ea49a71689cad48526d1da8ddcc383bca`. DB/Redis/site volumes được giữ lại, không migrate hoặc đổi timezone của `frontend`.

SHA256 workspace/backend trước rebuild khớp cho `financial_snapshot.py`, `key_reports.py`, `adapters.py`. Replay hai cutoff sau rebuild vẫn khớp bảng trên. Các dịch vụ ứng dụng đều Up; DB healthy khi kiểm tra.

## Kết luận và giới hạn

**WR-01: VERIFIED FIXED. WR-02: VERIFIED FIXED.** Foundation remediation trong phạm vi đã kiểm tra: **PASS**. Không phát hiện regression mới trong phạm vi này. AI002 zero/credit row không voucher vẫn được bỏ qua trước validation vì không tạo positive obligation; điều này không chứng minh nguyên report có đầy đủ provenance và cần được xác định rõ trong source contract AI003, không dùng empty obligation set như bằng chứng zero AP/AR.

Các điều kiện AI003 còn mở: approved signal scope; baseline/window/denominator/threshold/severity policy; independent signal gold; missing/malformed due-date policy; backdate/cancel/correction under posting-date semantics; live cache revoke/regrant và evidence permission replay. `as_known_at` vẫn unsupported, COGS mapping chưa verified, live CASH_SHORTFALL chưa có nguồn settlement. GitNexus query còn rỗng, FTS thiếu, index chậm 11 commit; không tuyên graph review hiện tại đủ dữ liệu.

G1 `PARTIAL` (isolated runtime aligned, deployment target/remaining runtime evidence chưa chốt); G2 `PARTIAL`; G3/G4A `BLOCKED`; G4B `NOT_APPLICABLE_YET`; **CONTRACT FREEZE: NOT_READY**. Bước tiếp theo: **ChatGPT Chat review evidence và hoàn thiện candidate contract**, rồi Work thực hiện independent gold/security/temporal evaluation theo contract; Chat quyết định freeze khi đủ G1/G2/G3/G4A. Chưa giao Antigravity xây AI003.
