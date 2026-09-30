# Prompt giao Antigravity — khép kín remediation Work verification AI003 foundation

> Dán toàn bộ file này vào Antigravity. Đây là **remediation cho AI001/AI002 foundation hiện có**, không phải lệnh xây AI003. Làm trong working tree hiện tại; không tự đổi gate hoặc freeze contract.

## Vai trò, authority và tài liệu phải đọc

Bạn là implementation engineer. Work đã chạy trên site ERPNext cô lập và tìm thấy lỗi runtime. Hãy làm chu trình **inspect → reproduce → patch → test → regression → evidence → handoff** trong một lượt làm việc; chỉ hỏi khi thiếu một quyết định tài chính/bảo mật mà không thể xác minh từ code, chứng từ hoặc tài liệu authority.

Đọc theo thứ tự, chỉ phần cần thiết:

1. `AGENTS.md` (GitNexus bắt buộc: impact trước khi sửa từng symbol; detect-changes trước commit; `UNKNOWN` phải xác minh bằng text search). Graph index từng được thấy chậm hơn HEAD 10 commit. Nếu CLI/MCP không chạy được, ghi nguyên lỗi, đối chiếu callers bằng code/text search và **không tuyên bố graph clean**.
2. `docs/features/AI003/evidence/AI003_WORK_VERIFICATION_2026-09-30.md` — reproduction, oracle, WV-01/02/03.
3. `docs/features/AI003/AI003_MASTER_SSOT.md` §29–30 và `docs/features/AI003/AI003_FOUNDATION_REMEDIATION_REPORT.md` — trạng thái gate, các sửa trước và 159 unit test.
4. `docs/features/LOTUS_FIN_AI_FEATURE_BUILD_WORKFLOW_3_TOOLS_V3_VI.md` — đặc biệt Work → Antigravity remediation, gate Phase 9/10.
5. Chỉ sau đó đọc đường gọi cần sửa: `api/key_reports.py`, `ai/financial_snapshot.py`, `cashflow/adapters.py`, `cashflow/service.py`, test liên quan, mã Frappe/ERPNext **đúng version cài trong container** (`frappe 16.34.0`, `erpnext 16.35.0`).

**Tiết kiệm usage:** không quét toàn repo hoặc viết lại báo cáo cũ. Bắt đầu từ hai finding đã reproduce, dùng một ma trận test tập trung, rồi chạy bộ hồi quy một lần sau khi sửa. Tái dùng site `ai003-verify.localhost` và fixture synthetic hiện có nếu còn; kiểm tra site trước khi thay đổi. Nếu runtime/shell bị chặn, tiếp tục phần có thể làm, ghi lệnh và bằng chứng chưa chạy; tuyệt đối không ghi PASS giả.

## Finding và mục tiêu bắt buộc

### WV-01 — AR/AP report footer hợp lệ bị coi là malformed

Trên site cô lập, mỗi `frappe.desk.query_report.run` cho Accounts Receivable/Payable trả 4 hàng dict giao dịch rồi một footer cuối kiểu `list`; `add_total_row=true`, `skip_total_row=0`, chiều dài bằng số columns (AR 25, AP 24). `extract_key_report_data` hiện chuyển nguyên `result` thành `data` mà bỏ ngữ cảnh total-row. `parse_ar_data`/`parse_ap_data` và AI002 `_parse_report_rows` từ chối list, khiến AI001 `PARTIAL` (AR/AP `UNAVAILABLE`) và AI002 `SOURCE_ERROR / DATA_PIPELINE_ERROR`, dù giao dịch hợp lệ.

**Required fix:** nhận diện/chuẩn hóa đúng footer do Frappe tạo tại boundary phù hợp, dùng metadata và cấu trúc thực tế đã xác minh. Chỉ loại footer khi có bằng chứng đủ mạnh, đúng vị trí, đúng shape và thuộc chính report AR/AP đang đọc; không `skip` mọi list/non-dict, không suy từ việc hàng cuối có cùng chiều dài columns. Tránh để metadata tùy ý từ client/raw-source giả mạo footer hợp lệ. Bảo toàn quyền report/company, provenance, `total_rows`/columns semantics hoặc cập nhật contract/tests nếu thật sự cần. Sau chuẩn hóa, AI001 và AI002 phải dùng cùng quy tắc tin cậy, không hai đường lệch nhau. Nếu Frappe tạo footer khi không có giao dịch, `success + verified empty` mới được ra zero; lỗi source không bao giờ biến thành zero.

### WV-02 — thiếu Party Type master có thể tạo cross-leg AR/AP

Trên fresh site chưa chạy Setup Wizard, `get_party_types_from_account_type("Receivable")` và `("Payable")` trả `[]`. Cả AR lẫn AP report khi đó chứa Customer+Supplier, mỗi bên 14,85 triệu dù có `party_type` filter. Probe `_collect_obligations` với `Supplier / Purchase Invoice` đi vào nhánh AR sinh `type=AR`, `source_ref=Sales Invoice:PI-TEST-1`. Sau khi tạo mapping chuẩn **chỉ ở site cô lập**, report tách đúng AR 6,9 triệu/AP 7,95 triệu.

**Required fix:** xác minh party/voucher/account identity cho **mỗi hàng giao dịch dương và hàng có thể ảnh hưởng aggregate**, trước khi gán AR/AP hoặc cộng KPI. Dùng trường report đáng tin cậy cùng đối chiếu DB/voucher phù hợp khi report thiếu trường; kiểm tra cả trường hợp dữ liệu trái nhau, thiếu, trộn, hoặc filter bị ERPNext bỏ qua. Cần preflight phát hiện master Party Type thiếu/sai, nhưng preflight một mình không thay cho kiểm tra semantic theo row. Khi không thể chứng minh phía, fail closed bằng trạng thái typed của từng nguồn/toàn forecast; không tạo obligation với ref_prefix giả, không âm thầm bỏ row và báo zero. Không tự sửa global Party Type master hoặc tự cấp quyền trên site sản phẩm. Nếu các voucher không phải Sales/Purchase Invoice được ERPNext report hỗ trợ hợp lệ, nghiên cứu nguồn đúng version và định nghĩa chính sách rõ; không đoán hoặc silently drop.

### WV-03 — các giới hạn chưa đủ authority để tự “fix”

Kiểm tra và ghi evidence riêng cho P&L/COGS mapping, `as_known_at` với backdate/cancel/correction, và live cache-role revocation sau khi WV-01 cho phép tạo cache. Sửa bug đã chứng minh trong AI001/AI002 nếu có authority rõ và test độc lập. Nếu COGS không cô lập được, giữ `UNAVAILABLE`; nếu `as_known_at` chưa support, giữ limitation/typed refusal. **Không tự đặt threshold, severity, denominator policy, AI003 signal gold, hoặc đánh dấu AI003 PASS.** Nêu chính xác việc nào còn để Work/Chat quyết định. Đừng mở rộng sang feature AI003 để “giải quyết hết” bằng giả định.

## Ma trận test tối thiểu — phải có kết quả cho từng nhóm

1. **Footer/source envelope:** payload Frappe v16 thật đã sanitize; footer hợp lệ cuối; không footer; report thực sự rỗng; chỉ footer hợp lệ khi report rỗng; list ở đầu/giữa; hai footer; footer sai chiều dài/cột/giá trị; dict total row thật; dict `party="Total"` giả hoặc ở giữa; unknown/error status; thiếu/non-list `data`; company/report mismatch; metadata thiếu/giả/không khớp; row valid+invalid. Với ambiguity, typed unavailable, không partial sum/verified zero.
2. **Numeric:** missing amount alias, `None`, chữ, NaN/Infinity, negative/zero, credit/settled rows, Decimal rounding, duplicate/summary row, overdue due-date thiếu/sai, zero denominator. Không thay công thức chỉ để test xanh; giữ behavior có authority và ghi limitation nếu chưa rõ.
3. **Cross-leg:** Customer/Sales Invoice trong AR, Supplier/Purchase Invoice trong AP; hoán đổi; mixed trong cùng report; thiếu `party_type`/`voucher_type`/voucher id; tham chiếu voucher không tồn tại, sai Company, sai account/currency; master Party Type thiếu hoặc cấu hình sai; report filter bị bỏ qua. Kiểm tra cả AI001 aggregate và AI002 obligations; mọi hàng có thể làm sai số phải bị phát hiện trước khi trả số.
4. **Security/cache:** Guest, user có/không quyền Company/report, cross-company request/payload, revoked role trên cache hit rồi regrant trong TTL, no financial payload khi FORBIDDEN, cache isolation per user/company/cutoff/scope; không log PII hay raw financial rows. Giữ server-side authorization trước xử lý report/cache.
5. **Temporal/currency:** `as_of` invalid/đầu kỳ/giữa kỳ, cutoff trước/sau payment, prior-period alignment, VND company với USD request, foreign-currency row, Finance Book explicit refusal, cancellation/backdate chỉ nếu nguồn hỗ trợ replay; không ngụy tạo historical truth.
6. **Regression:** 159 test hiện có (127 cũ + 32 remediation) phải tiếp tục qua; test mới chỉ cho behavior thực sự quan trọng, parametrized/fixture dùng lại, không sao chép implementation vào expected. Chạy unit ở workspace và Docker nếu có thể; sau đó live site replay với actual report output, không chỉ mock parser.

## Live acceptance oracle và ranh giới môi trường

Chỉ dùng `ai003-verify.localhost`, Company synthetic `AI002 Fixture 2026`; **không migrate/reset/sửa timezone/master data của `frontend`**. Không xoá site/volume, không đụng dữ liệu thực. Có thể dùng transaction rollback cho probe users/Company; chứng minh không để lại dữ liệu probe ngoài fixture.

Oracle độc lập từ submitted vouchers/GL (không gọi AI001/AI002 để sinh expected):

| Cutoff | AR | AP | Cash GL |
| --- | ---: | ---: | ---: |
| 2026-09-20 | 8.000.000 | 9.500.000 | 12.000.000 |
| 2026-09-26 | 6.900.000 | 7.950.000 | 11.550.000 |

Tại 26/09: overdue AR 2.000.000, ratio ≈ 0,289855; Sales Invoice revenue 8.000.000. Fixture hiện có trong `docs/features/AI002/fixture_scripts/`. Sau patch phải đối chiếu source report, AI001 metrics và AI002 obligations/forecast với oracle. Không dùng diagnostic in-memory footer removal làm acceptance. Nếu một metric không có source chứng minh được, trả `UNAVAILABLE` có lý do.

## Tra cứu ngoài khi cần

Ưu tiên đọc mã Frappe/ERPNext trong container và raw output đã reproduce. **Chỉ khi còn mơ hồ** về total-row construction, report row schema, party-type filtering, voucher semantics hoặc behavior theo version, tra cứu online từ docs/source/issue chính thức của Frappe/ERPNext, đúng version/commit nếu có; ghi link, version, câu hỏi cụ thể và kết luận. Không crawl web rộng, không tải dữ liệu tài chính bên thứ ba, không dùng blog làm authority tài chính. Fixture synthetic + DB source của site cô lập là dữ liệu kiểm chứng số.

## Ranh giới thay đổi và stop conditions

- Chỉ sửa lớp AI001/AI002 source boundary/adapters, preflight liên quan và tests/docs cần thiết; tối thiểu file, tối thiểu API churn. Không tạo RiskSignal, threshold/severity, KPI v2, Finance Engine mới hoặc UI AI003. Không sửa `AI003_MASTER_SSOT.md` để tự tuyên PASS/freeze.
- Không biến lỗi thành `0`, `OK` hoặc forecast có số khi provenance/semantic chưa được chứng minh; không chọn kết quả “đẹp” từ các alias hoặc source mâu thuẫn.
- Không commit trước `GitNexus detect-changes --scope all` đủ dữ liệu; `partial/truncated/UNKNOWN` không phải clean. Nếu cần commit theo quy trình, chỉ commit file do lượt này thay đổi và sau khi mọi required check có kết quả; giữ nguyên thay đổi có sẵn của người khác.
- Nếu không thể nhận diện footer an toàn hoặc không có authority về một loại voucher/COGS/temporal, dừng **phần đó**, giữ fail-closed, ghi reproduction và decision cần Work/Chat. Tiếp tục các phần độc lập có thể hoàn thành.

## Đầu ra bắt buộc, gọn nhưng audit được

1. Báo cáo `docs/features/AI003/AI003_WORK_VERIFICATION_REMEDIATION_REPORT.md` gồm: finding → root cause có dòng code/raw payload metadata → fix/diff → bảng test (command, environment, pass/fail) → numeric oracle → security/temporal result → rủi ro/giới hạn. Không tuyên PASS nếu chưa chạy.
2. Liệt kê chính xác file đã sửa, kết quả GitNexus impact/detect-changes và mọi fallback; nêu rõ có commit hay không. Redact tên người dùng/PII nếu log live.
3. Handoff ngắn cho Work: `Verified / Not verified / Reproduced bugs / Security findings / Data findings / Test evidence / Recommended re-test`. Chỉ đề nghị nâng gate sau khi Work tự replay; Antigravity không tự quyết định contract freeze.

**Expected next state:** WV-01/WV-02 được sửa và chứng minh bằng test + live site, hoặc còn typed blocker được mô tả cụ thể. Work có thể chạy lại cùng oracle và gate; AI003 vẫn chờ Chat/Work quyết định sau G1/G2/G3/G4A.
