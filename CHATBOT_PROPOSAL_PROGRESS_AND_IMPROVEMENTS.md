# Lotus Fin Chatbot — Tổng kết theo proposal và hướng cải tiến

**Ngày cập nhật:** 14/10/2026, múi giờ Asia/Saigon.

**Branch bàn giao:** `codex/chatbot`.

**Phạm vi:** bản tích hợp P6 hiện tại, phục vụ review mã nguồn và DEMO có kiểm soát.

**Kết luận acceptance độc lập:** `P6_SECURITY_BLOCKED`; chưa đạt điều kiện phát hành tài chính thật hoặc G10.

## 1. Proposal gốc và cách đánh giá

Đối chiếu với [Solution Design Chatbot hỗ trợ thao tác](<docs/reviews/LOTUS_FIN_CHATBOT_ASSISTED_ACTIONS_SOLUTION_DESIGN_VI (1).md>), [kế hoạch hoàn thiện proposal](docs/reviews/chatbot-contract-handoff-2026-10-12-01a12f82/CHATBOT_PROPOSAL_COMPLETION_PLAN_UPDATED.md) và [đề xuất kiến trúc native](LOTUS_NATIVE_ARCHITECTURE_FROZEN_PROPOSAL.md).

Proposal hướng đến một trợ lý giúp người dùng tìm đúng chứng từ theo quyền, chọn và mở chứng từ, chuẩn bị nội dung, xem trước thay đổi rồi xác nhận riêng trước khi thực thi. Các mức L0–L5 có ranh giới khác nhau: đọc dữ liệu, soạn nháp và ghi/gửi thật không được coi là cùng một khả năng.

Tài liệu này phân biệt rõ **đã có mã và chạy được**, **đã kiểm chứng trong DEMO**, **chưa được chấp nhận về bảo mật** và **chưa có nguồn/quyền để chạy thật**. Không tính phần trăm hoàn thành từ số lượng test hoặc coi dữ liệu mô phỏng là dữ liệu tài chính production.

## 2. Những gì đã làm được

| Phần trong proposal | Kết quả hiện tại | Giới hạn còn lại |
| --- | --- | --- |
| L0 — giải thích, hướng dẫn, hỏi rõ yêu cầu | Có định tuyến intent giới hạn và phản hồi clarification trong chatbot tích hợp. | Chưa có một trợ lý hiểu mọi yêu cầu nghiệp vụ; không tự khẳng định đã đọc dữ liệu tài chính thật. |
| L1 — tìm hóa đơn | Có typed request/response, bộ lọc, kết quả bounded, trạng thái đầy đủ/rỗng/PARTIAL và kiểm tra reference. DEMO trả danh sách hóa đơn giả có nhãn nguồn. | CORE chưa có native source được duyệt; chưa chứng minh tìm kiếm trên dữ liệu tài chính thật. |
| L2 — chọn và mở | Người dùng phải chọn rõ ràng. Page và Drawer mở được minimum read-only view của hóa đơn DEMO. Có kiểm tra scope/version trong nền tảng read. | Chưa phải form chứng từ native đầy đủ hoặc điều hướng đến chứng từ thật đã qualified. |
| L3 — chuẩn bị nội dung | Soạn, sửa, review, copy/discard bản nháp cục bộ. Có thời hạn nháp và chuyển nội dung đã review sang form đề xuất L4. Luồng chọn hóa đơn → soạn nhắc → review → chuyển đã được chạy trên React thật. | Nháp không tự chèn số dư, khách hàng hay thông tin tài chính chưa xác minh. Chưa có generic `form.prefill` đã được duyệt. |
| L4 — proposal và xác nhận | Có action catalog Task/Note/Draft, proposal có digest/challenge/TTL, nút xác nhận riêng, trạng thái operation và adapter test. Page và Drawer hoàn thành flow tạo Task mô phỏng. | Đây là receipt và record **mô phỏng**, không phải Task/Draft thật trong hệ thống nghiệp vụ. Native write vẫn BLOCKED. |
| L4 — chống lặp và xử lý kết quả không rõ | Xác nhận lặp/concurrent trả một operation, một lần thực thi. Store SQLite giữ trạng thái mô phỏng. Test độc lập chứng minh rollback khi process chết trước commit và UNKNOWN_OUTCOME được reconcile mà không chạy lại mù. | Chưa qualified ledger, delivery và audit cho side effect thật. Audit hiện lưu sự kiện mô phỏng, chưa phải audit outcome production. |
| L5 — policy cho thao tác tác động lớn | Có catalog/policy cho submit, cancel, email, payment và scheduler. UI hiển thị lý do bị chặn hoặc thiếu approval provider. Các execution route không được mở. | Chưa thực thi thật; chưa có adapter và approval provider được chấp nhận. |
| V1 — hóa đơn đã qua hạn cuối còn dư nợ | Có evaluator deterministic: ngày đến hạn, số dư Decimal, currency, lifecycle và scope. DEMO có hai gold rows, hiển thị đúng trên HTTP, Page và Drawer. | Chưa có native source; independent oracle phát hiện bốn lỗi validation/fail-closed cần sửa. |
| Runtime độc lập ERPNext | Runtime được kiểm tra chỉ cài `frappe` và `lotus_fin`; không import được ERPNext, không có Company/Sales Invoice/GL Entry. React, đăng nhập và DEMO hoạt động. | Đây là độc lập của shell/DEMO, chưa phải toàn bộ sản phẩm tài chính độc lập. AI001–AI003 còn nguồn legacy theo ERP. |
| HTTP và truy nguyên artifact | Đã kiểm tra ordinary-user auth, CSRF, no-store, CORE/DEMO separation và cookie replay sau logout. 331 tệp backend cùng JS/CSS build khớp image và asset phục vụ qua HTTP. | Không thay thế acceptance native, clean clone, kiểm chứng mọi job CI hoặc G10. |

V1 DEMO dùng mốc quan sát cố định `2026-10-13T12:00:00+00:00`, không dùng ngày hiện tại để giả lập dữ liệu mới: DEMO-INV-001 quá hạn 12 ngày, dư nợ `15000000.00 VND`; DEMO-INV-002 quá hạn 8 ngày, dư nợ `2850000.50 VND`. Hai dòng này không có native selection handle.

## 3. Những gì chưa làm được hoặc chưa được chấp nhận

**Bảo mật session chưa đạt.** Logout bên ngoài và đổi actor đã có cải thiện, nhưng Page và Drawer đang hiển thị vẫn giữ ba dòng hóa đơn, một chứng từ và sử dụng được handle cũ sau khi session bị revoke trên server. Poll hiện không xác minh lại server nếu cookie tên người dùng không đổi. Một bootstrap trả về muộn còn có thể phục hồi scope VERIFIED sau khi đã revoke. Đây là hai lỗi P1, giữ P4-F01 ở trạng thái mở.

**V1 chưa fail-closed đầy đủ.** Thiếu completeness vẫn được mặc định COMPLETE; thiếu source evidence vẫn có thể trả kết quả OK với complete coverage. Timestamp không có timezone và currency ba ký tự bất kỳ cũng được chấp nhận. Gold DEMO hợp lệ không chứng minh các đường dữ liệu lỗi đã an toàn.

**Nguồn và hành động thật chưa qualified.** Chưa có native financial source được Product/Data/Security duyệt và đối soát độc lập. Chưa có đọc/mở chứng từ native positive end-to-end, ghi Task/Note/Draft thật, gửi email, submit/cancel, payment hoặc scheduler thật. N0 và các cổng L4/L5 này vẫn BLOCKED.

**Một số khả năng rộng hơn trong proposal chưa được giao:** customer lookup/disambiguation đã xác minh, full native form/navigation, generic form prefill, phân tích/xếp ưu tiên chứng từ từ số liệu đã kiểm chứng, installment-aware overdue và historical accounting as-of. Không coi tìm kiếm metadata hoặc PastFinalDue hiện tại là các khả năng này.

**Quality và supply chain chưa sạch.** Full host pytest collection có bốn lỗi; CI chưa bao phủ đầy đủ các regression P1/P2/AI001–003. Audit frontend còn tám mục package HIGH và hai MODERATE; metadata advisory của sáu package Python phục vụ runtime cần triage. Header có thể hiển thị actor cũ hoặc tên Administrator mặc định. Scenario selector trong Drawer 420px bị tràn. Một số báo cáo module còn mô tả readiness/timing/endpoint quá mức thực tế.

## 4. Bằng chứng kiểm chứng độc lập

| Kiểm tra | Kết quả |
| --- | --- |
| Backend invoice/action/session/P6 regression | 507 passed |
| Frontend P1/P2/L3/P4/P6 | 124 passed, không skip |
| AI001–AI003 theo lựa chọn regression | 376 passed và 7 subtests passed |
| P6 subset | 67 passed; có trùng với suite 507 |
| HTTP contract độc lập | 39 observations đạt kỳ vọng |
| Crash/UNKNOWN_OUTCOME/audit failure trên store mô phỏng | 3 trường hợp đạt |
| Oracle V1 độc lập | 18/22 đạt, 4 thất bại |
| Probe session độc lập | 2/2 phát hiện lỗi |
| Full host test collection | 968 collected, 4 collection errors |

Các suite có phần trùng nhau; không cộng thành tổng test độc lập. Các dòng PASS áp dụng đúng lớp và phạm vi đã kiểm tra. Browser fault injection, acceptance native và một số kiểm chứng mobile/CI vẫn chưa được qualified.

## 5. Đề xuất cải tiến theo thứ tự

1. **Đóng hai lỗi session P1 trước.** Giữ shared Page/Drawer và các controller hiện có. Thêm authoritative revalidation có giới hạn thời gian/freshness; fence bootstrap và bước hash theo generation. Replay revoke, disable, same-user rotation và late response trên hai surface mà không reload.
2. **Siết hợp đồng V1.** Yêu cầu completeness/source evidence rõ ràng, timestamp aware và currency hợp lệ; không trả financial success khi nguồn thiếu. Giữ gold độc lập, Decimal chính xác và không bổ sung FX/historical semantics ngoài scope.
3. **Khép quality và dependency gates.** Sửa mismatch BaselineSourceError, chạy framework suites trong môi trường Frappe phù hợp, đưa regression hiện có vào CI bằng dependencies được pin. Triage advisory theo version/range/reachability và cập nhật tối thiểu; không dùng blanket major audit fix.
4. **Sửa các điểm UX và tài liệu cụ thể.** Header bám verified actor, không giả định Administrator; selector fit container Drawer; sửa claim production-ready, endpoint cũ và cam kết ≤200ms. Recheck trên viewport thực tế.
5. **Mở native read bằng một pilot hẹp sau khi N0 được duyệt.** Chốt nguồn, tenant/company/document/field policy, observation/version và đối soát balance/final due. Sau đó chạy ordinary-user HTTP/browser positive và negative với chứng từ thật. Không tạo schema tài chính mới chỉ để thay tên ERP.
6. **Qualified từng hành động thật riêng.** Với L4: target, fresh permission, idempotency, durable outcome/audit. Với L5: approval provider và policy cho từng family; email/payment/scheduler không được kế thừa PASS từ DEMO. Cần quyết định riêng trước khi bật.
7. **Đo giá trị sản phẩm sau khi luồng an toàn.** Đo completion rate, số bước/click, thời gian hoàn thành và tỷ lệ phải sửa nháp bằng một bộ tác vụ chuẩn. Chưa có benchmark nên không gán ROI hoặc hiệu quả giả định.

Mười hai correction batches chi tiết, kèm tệp nguồn và điều kiện chấp nhận, nằm trong [P6_RELEASE_DECISION.md](P6_RELEASE_DECISION.md). Không đề xuất một đợt redesign tổng quát.

## 6. Ý nghĩa của việc push branch này

Theo yêu cầu mới ngày 14/10/2026, mã nguồn và tài liệu hiện tại được bàn giao lên branch tính năng để review. Yêu cầu này cho phép commit/push, thay cho giới hạn “không stage/commit/push” của lượt acceptance trước. Các báo cáo acceptance cũ được giữ nguyên như bằng chứng lịch sử; verdict của chúng không được đổi thành PASS.

Snapshot commit bao gồm source, test, proposal và bằng chứng được chọn; không gồm credentials `.runtime`, cache, dependency folders, tool packs hoặc các bản sao source lịch sử. Rà soát toàn bộ staged diff còn ghi nhận whitespace trong một số tệp nguồn/tài liệu cũ và raw logs. Lần bàn giao này giữ nguyên các bytes đó làm bằng chứng, không dùng việc push để tuyên bố quality gate đã sạch.

GitNexus đã được cập nhật cho branch mới. Phân tích thay đổi xác định 3.243 symbols và 128 luồng bị ảnh hưởng ở mức CRITICAL. Vì công cụ giới hạn 1.000 symbols mỗi lần, kết quả được thu qua 39 nhóm không bị cắt và đối chiếu tổng số với toàn bộ candidate; staging thật không bị đổi trong bước này. Việc liệt kê execution flows của analyzer vẫn có giới hạn, nên không suy ra “không bị ảnh hưởng” từ luồng không xuất hiện. [Bằng chứng graph trước commit](docs/reviews/evidence/p6-github-handoff-2026-10-14/GRAPH_PRE_COMMIT.json).

**Push branch không có nghĩa là release approval.** Trạng thái hiện tại vẫn là `P6_SECURITY_BLOCKED`; reviewed-release readiness, N0, actual L4/L5 external execution và G10 chưa được cấp. Không deploy và không bật các hành động tài chính thật trong lần bàn giao này.

Tài liệu liên quan: [acceptance độc lập](P6_INDEPENDENT_ACCEPTANCE.md), [security recheck](P6_SECURITY_RECHECK.md), [E2E matrix](P6_FULL_E2E_MATRIX.md), [product independence](P6_PRODUCT_INDEPENDENCE.md), [source/pre-push](P6_SOURCE_PRE_PUSH.md), [runbook DEMO](P6_JUDGE_DEMO_RUNBOOK.md).
