# Prompt → ChatGPT Chat: chốt candidate contract trước khi xây AI003

Bạn là contract owner/arbiter cho Lotus Fin AI003 Risk Signal Agent. Work vừa kiểm chứng bản sửa Zcode revision `c6f4cd1`. Hãy dùng evidence dưới đây để hoàn thiện **candidate contract có thể kiểm chứng**, rồi giao Work làm gold/security/temporal evaluation. Chưa freeze hoặc giao implementation khi chưa đủ gate.

## Authority và evidence

Tài liệu liên quan trong repo:

- `docs/features/AI003/AI003_MASTER_SSOT.md`, §32 là latest authority; §4–31 là lịch sử, không lấy blocker cũ làm hiện trạng.
- `docs/features/AI003/evidence/AI003_WR01_WR02_WORK_VERIFIED_2026-09-30.md`.
- `docs/features/LOTUS_FIN_AI_FEATURE_BUILD_WORKFLOW_3_TOOLS_V3_VI.md` — Chat chốt contract, Work kiểm chứng, Antigravity build sau freeze.

Nếu phiên Chat không truy cập được các file này, dùng bản tóm tắt đã xác minh ở đây để tạo draft; nêu rõ file nào chưa đọc. Không giả vờ đã đọc tài liệu. Khi cần đối chiếu một điều chưa có trong prompt, yêu cầu đúng phần tài liệu cần thiết, không bắt người dùng gửi lại toàn repo.

## Hiện trạng Work đã xác minh

- WR-01 fake dict summary → zero và WR-02 AI001 cộng row không voucher: **VERIFIED FIXED**. Foundation remediation PASS trong phạm vi đó.
- **197/197 local tests, 233/233 Docker tests**, AI001 evaluation 15/15. Live poisoned AR source trả `UNAVAILABLE`, không zero.
- Isolated site `ai003-verify.localhost`: Frappe 16.34.0, ERPNext 16.35.0, Company `AI002 Fixture 2026`, VND, timezone `Asia/Ho_Chi_Minh`, approved cash scope `[Cash - A2F]`.
- Work đã build lại image từ commit hiện tại và đồng nhất sáu dịch vụ ứng dụng. DB/site volumes được giữ lại. Site `frontend` chưa được migrate theo kết quả này.
- Oracle độc lập từ submitted voucher/GL, đối chiếu live sau rebuild:

| Cutoff | AR | AP | Cash | AR overdue ratio |
| --- | ---: | ---: | ---: | ---: |
| 2026-09-20 | 8.000.000 | 9.500.000 | 12.000.000 | 0,0 |
| 2026-09-26 | 6.900.000 | 7.950.000 | 11.550.000 | 0,2899 |

Revenue 8m tại cả hai cutoff. AI002 có 5 AR+5 AP tại 20/09 và 4 AR+4 AP tại 26/09, tổng khớp bảng. Đây là source oracle, **chưa phải gold cho signal hoặc baseline đã duyệt**.
- AI001 top `PARTIAL`: COGS/gross margin và near-term AP còn unavailable. AI002 `FORECAST_UNAVAILABLE / NO_CONFIRMED_SETTLEMENT_EVENTS`: nguồn live chưa có verified future settlement; invoice due date chỉ là contractual obligation date.
- Chưa support `as_known_at`; chỉ có posting-date cutoff, không cam kết tái lập trạng thái thông tin từng biết trong quá khứ. Backdate/cancel/correction cần policy và test.
- Live cache revoke/regrant và evidence permission replay còn chưa được Work xác minh hoàn chỉnh. AI003 gold/threshold/severity chưa có approval. G1/G2 `PARTIAL`, G3/G4A `BLOCKED`, G4B `NOT_APPLICABLE_YET`; **CONTRACT FREEZE NOT_READY**.

## Quyết định contract cần hoàn thành

1. Chọn scope nhỏ nhất có nguồn chứng minh: xem xét tối đa `AR_OVERDUE_SPIKE` và `AP_DUE_CLUSTER`; signal nào thiếu authority phải giữ conditional. Chưa thêm SALES_DECLINE/MARGIN_DROP/CASH_SHORTFALL hoặc signals khác chỉ để đủ danh sách.
2. AR: định nghĩa overdue amount/residual, current/baseline comparable cutoffs/windows, spike measure (percentage points/relative/amount), minimum denominator/count, verified empty vs zero-denominator, missing/malformed due date hoặc overdue field. Không biến thiếu thông tin thành benign hoặc ratio zero.
3. AP: định nghĩa approved contractual window, inclusivity tại biên ngày, amount/count/ratio measure, denominator, null due date, partial payment, credits/netting, duplicates. Không gán contractual due date thành actual cash timing.
4. Threshold/severity: đưa phương án khuyến nghị và lý do; gắn nhãn `PROPOSED`, tách demo policy khỏi policy tài chính production. Không dùng fixture hiện có để “học” ra ngưỡng. Nêu rõ quyết định nào cần finance owner/người dùng phê duyệt; gộp câu hỏi tối thiểu khi thật sự cần. Không tự ghi business-approved.
5. Chốt typed output/input, rule/method/formula version, `as_of`/timezone, Company/currency/Finance Book scope, snapshot/evidence provenance, safe forbidden/error payload, source inconsistency behavior, evidence drilldown permission, agent read-only tool allowlist và explanation failure.
6. Viết acceptance matrix cho Work: positive, benign sát ngưỡng, inconclusive, legitimate empty, malformed row/footer/identity, future posting, cancellation/backdate under chosen policy, company/report/doc denial, cache revoke/regrant, model failure. Gold oracle độc lập với production metric/signal functions, lưu voucher IDs/hashes và expected arithmetic/rule status.

## Đầu ra mong muốn — ngắn, đủ triển khai và kiểm chứng

- Candidate contract versioned cho scope được chọn: công thức, field, semantics, source/failure/security boundaries, rule-policy approvals còn thiếu; phân biệt VERIFIED/PROPOSED/UNSUPPORTED.
- Bảng quyết định mở có owner, bằng chứng cần và điều kiện đóng; không yêu cầu Antigravity sửa tiếp nếu không có defect đã reproduce.
- Một **prompt hoàn chỉnh giao ChatGPT Work**, gồm fixture/gold/role/temporal/evidence replay và điều kiện đánh giá từng gate. Work được dùng site synthetic hiện có; bảo vệ site `frontend` và dữ liệu thật. Nếu threshold chưa approved, Work có thể làm symbolic boundary cases và numeric source gold, nhưng không ghi signal verdict production.
- Trạng thái cuối: `READY_FOR_WORK_PREBUILD_EVALUATION` nếu candidate đã đủ rõ, hoặc liệt kê quyết định thực sự chặn. Chỉ cân nhắc freeze khi G1/G2/G3/G4A đều PASS từ evidence; implementation AI003 là lượt Antigravity sau đó.

Ưu tiên tối thiểu vòng lặp: tái dùng foundation evidence đã verified, chỉ kiểm tra lại khi contract/changing code tạo rủi ro mới. Không quét lại cả repo hoặc nghiên cứu web rộng; tra cứu nguồn chính thức chỉ khi có câu hỏi cụ thể không giải đáp từ evidence hiện có.
