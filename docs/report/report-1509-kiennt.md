# SOFTWARE REQUIREMENT SPECIFICATION (SRS MINI)
## Dự án: Lotus Fin — AI-Powered Financial Copilot for SMEs
**Đường đua:** FinTechathon 2026 — International Artificial Intelligence Track (Topic E: SME Finance Copilot)  
**Phiên bản:** 1.0  

---

## 1. Introduction
### 1.1 Objective
Tài liệu này xác định các yêu cầu chức năng và phi chức năng của hệ thống **Lotus Fin**. Hệ thống được thiết kế như một AI Financial Copilot hỗ trợ các doanh nghiệp vừa và nhỏ (SME) tự động phân tích sức khỏe tài chính, quản lý và cảnh báo rủi ro dòng tiền, đồng thời kết nối đối soát các phương án cấp vốn tối ưu từ ngân hàng và các tổ chức tín dụng.

### 1.2 Scope
* **Trong phạm vi (In-scope):**
  * Trích xuất, chuẩn hóa và làm sạch báo cáo tài chính, hóa đơn, sao kê dòng tiền từ tệp PDF, CSV, Excel.
  * Dự báo dòng tiền (Cash flow forecasting) trong 30/60/90 ngày và cảnh báo sớm nguy cơ thâm hụt tiền mặt (Cash runway alerts).
  * Phân tích chỉ số tài chính doanh nghiệp (DSCR, Quick Ratio, Working Capital) và diễn giải tự động bằng ngôn ngữ tự nhiên.
  * Khớp nối và đề xuất danh mục gói tài trợ vốn phù hợp (Financing-option matching).
  * Giao diện Copilot Chatbot tương tác tự nhiên, giải thích nguyên nhân biến động tài chính và hỗ trợ chạy thử kịch bản trả nợ.
* **Ngoài phạm vi (Out-of-scope):**
  * Tự động giải ngân trực tiếp tài khoản ngân hàng thực tế (hệ thống dừng ở mức đánh giá hồ sơ và mô phỏng sandbox).
  * Kê khai và nộp thuế trực tuyến với cơ quan nhà nước.

### 1.3 Glossary
| STT | Thuật ngữ | Diễn giải |
| :--- | :--- | :--- |
| 1 | **DSCR** | Debt Service Coverage Ratio — Hệ số khả năng trả nợ. |
| 2 | **Cash Runway** | Số tháng doanh nghiệp có thể duy trì hoạt động trước khi cạn tiền mặt nếu doanh thu không đổi. |
| 3 | **Prompt Injection** | Dạng tấn công can thiệp vào ngữ cảnh câu lệnh của AI Agent nhằm trích xuất dữ liệu nội bộ hoặc vượt qua hạn mức kiểm soát. |
| 4 | **SME** | Small and Medium Enterprises — Doanh nghiệp vừa và nhỏ. |

---

## 2. Overall Description
### 2.1 Khảo sát sơ bộ các sản phẩm tương tự trên thị trường
* **Float / Nume.ai:** Chuyên sâu về dự báo dòng tiền bằng AI kết nối sổ kế toán; trực quan hóa đồ thị tốt nhưng thiếu module AI Copilot đối thoại giải thích sâu và chưa hỗ trợ kết nối hồ sơ cấp vốn.
* **QuickBooks Online / Xero AI:** Hệ sinh thái quản trị kế toán toàn diện, tự động phân loại giao dịch; tuy nhiên cơ chế dự báo rủi ro còn dạng rule-based cơ bản, thiếu agent tự động thẩm định tín dụng.
* **Microsoft Copilot for Finance:** Tích hợp sâu vào ERP/Excel cho tập đoàn lớn; chi phí cao và không tối ưu cho bài toán tiếp cận hạn mức tín dụng ngân hàng của phân khúc SME.
* **Điểm đột phá của Lotus Fin:** Kết hợp giữa **Engine tính toán xác định (Deterministic Engine)** và **LLM Agent** để vừa chủ động cảnh báo sớm thâm hụt tiền, vừa chuẩn hóa hồ sơ vay đáp ứng tiêu chuẩn thẩm định tín dụng của WeBank/ngân hàng thương mại.

### 2.2 Tác nhân hệ thống (Actors)
1. **SME Owner (Chủ doanh nghiệp):** Xem dashboard tổng quan, tiếp nhận cảnh báo rủi ro dòng tiền và lựa chọn phương án vay vốn.
2. **Accountant (Kế toán nội bộ):** Tải lên báo cáo tài chính, hóa đơn, điều chỉnh thông số ngân sách.
3. **Financial Institution / Bank API:** Cung cấp danh mục gói vay và tiêu chí xét duyệt tín dụng (Credit Policy Rules).
4. **LLM Engine & Orchestrator:** Xử lý ngôn ngữ tự nhiên, lập luận và sinh báo cáo phân tích.

---

## 3. Detailed Requirements (Use Case Specifications)

### UC001: Upload & Normalize Financial Data
* **Mã Use Case:** UC001
* **Tác nhân:** Accountant, SME Owner
* **Tiền điều kiện:** Người dùng đã đăng nhập vào hệ thống Lotus Fin.
* **Luồng sự kiện chính (Basic Flow):**
  1. Người dùng chọn tải lên dữ liệu tài chính (PDF hóa đơn, bảng cân đối kế toán hoặc CSV sao kê ngân hàng).
  2. Hệ thống kiểm tra định dạng tệp và giới hạn dung lượng (<= 25 MB).
  3. Module Parser/OCR trích xuất các trường dữ liệu: Dòng tiền vào, Dòng tiền ra, Công nợ phải thu/phải trả (AP/AR), Số dư tiền mặt tức thời.
  4. Hệ thống che mờ (masking) các thông tin định danh cá nhân nhạy cảm (PII).
  5. Hệ thống lưu trữ dữ liệu đã chuẩn hóa vào cơ sở dữ liệu và hiển thị bản tóm tắt xác nhận.
* **Luồng thay thế (Alternative Flow):** Nếu tệp hỏng hoặc sai định dạng: Hệ thống báo lỗi, chỉ rõ cột/dòng thiếu và yêu cầu tải lại.
* **Hậu điều kiện:** Dữ liệu tài chính được chuẩn hóa sẵn sàng cho các engine phân tích và dự báo.

---

### UC002: Forecast Cash Flow & Trigger Shortfall Alert
* **Mã Use Case:** UC002
* **Tác nhân:** SME Owner, Accountant
* **Tiền điều kiện:** Đã có dữ liệu tài chính hợp lệ từ UC001.
* **Luồng sự kiện chính (Basic Flow):**
  1. Hệ thống định kỳ chạy mô hình dự báo dòng tiền 30/60/90 ngày dựa trên lịch sử thu chi và kỳ hạn AP/AR.
  2. Hệ thống tính toán điểm rơi tiền mặt và chỉ số Cash Runway.
  3. Nếu phát hiện số dư tiền mặt dự kiến xuống dưới ngưỡng an toàn (Safety Margin), hệ thống kích hoạt trạng thái cảnh báo thâm hụt.
  4. Hệ thống hiển thị cảnh báo trên Dashboard và gửi email thông báo chi tiết nguyên nhân (ví dụ: công nợ khách hàng trễ hạn kết hợp hạn trả gốc vay).
* **Luồng thay thế (Alternative Flow):** Nếu dữ liệu không đủ tối thiểu 3 chu kỳ kế toán: Hệ thống đánh dấu mức độ tin cậy thấp (Confidence Score < 60%) và đề xuất bổ sung số liệu.
* **Hậu điều kiện:** Cảnh báo dòng tiền được lưu vết; quy trình đề xuất phương án cấp vốn được khởi tạo ngầm.

---

### UC003: Analyze Business Financial Health
* **Mã Use Case:** UC003
* **Tác nhân:** SME Owner
* **Tiền điều kiện:** Có dữ liệu báo cáo tài chính hợp lệ trong hệ thống.
* **Luồng sự kiện chính (Basic Flow):**
  1. Người dùng kích hoạt chức năng "Financial Analysis Report".
  2. Hệ thống tính toán các chỉ số cốt lõi: DSCR, Tỷ suất lợi nhuận ròng, Vòng quay vốn lưu động, Quick Ratio.
  3. LLM Engine tổng hợp các chỉ số, so sánh với benchmark chuẩn ngành của phân khúc SME.
  4. Hệ thống sinh báo cáo phân tích bằng ngôn ngữ tự nhiên gồm 3 phần: Điểm mạnh, Rủi ro tiềm ẩn và Khuyến nghị hành động.
* **Luồng thay thế (Alternative Flow):** Nếu hệ số DSCR rơi vào mức báo động (< 1.0): Hệ thống gắn cờ cảnh báo đỏ "High Credit Risk" và ưu tiên điều hướng sang tính năng tìm gói tài trợ vốn (UC004).
* **Hậu điều kiện:** Báo cáo sức khỏe tài chính được lưu trữ và hỗ trợ xuất định dạng PDF.

---

### UC004: Match Financing Options
* **Mã Use Case:** UC004
* **Tác nhân:** SME Owner, Bank API
* **Tiền điều kiện:** Hệ thống đã hoàn tất đánh giá chỉ số tín dụng (UC003) và xác định nhu cầu vốn (UC002).
* **Luồng sự kiện chính (Basic Flow):**
  1. Người dùng yêu cầu tìm kiếm phương án cấp vốn ("Find Financing Options").
  2. Hệ thống truy vấn danh mục gói vay khả dụng từ Bank API (thấu chi, bao thanh toán hóa đơn, vay tín chấp/thế chấp).
  3. Engine so khớp đối soát điều kiện vay (Eligibility Matching) dựa trên DSCR, doanh thu và tài sản đảm bảo của SME.
  4. Hệ thống hiển thị danh sách các gói tài trợ vốn phù hợp, xếp theo: Lãi suất tối ưu, Tỷ lệ duyệt dự kiến, Thời gian giải ngân.
* **Luồng thay thế (Alternative Flow):** Nếu doanh nghiệp không đủ điều kiện cho gói vay thương mại: Hệ thống đề xuất các giải pháp phi tín dụng (rút ngắn hạn nợ khách hàng, tái cấu trúc chi phí vận hành).
* **Hậu điều kiện:** Danh sách gói vay được lưu lại để người dùng thực hiện mô phỏng trả nợ (UC006).

---

### UC005: Interactive Financial Copilot Chat
* **Mã Use Case:** UC005
* **Tác nhân:** SME Owner, Accountant, LLM Engine
* **Tiền điều kiện:** Người dùng đang mở giao diện hội thoại Copilot.
* **Luồng sự kiện chính (Basic Flow):**
  1. Người dùng nhập câu hỏi bằng ngôn ngữ tự nhiên (ví dụ: *"Nếu khách hàng A chậm trả 200 triệu trong tháng tới thì công ty còn đủ tiền mặt vận hành bao lâu?"*).
  2. Lớp bảo vệ (Security Guardrail) quét kiểm tra Prompt Injection và các nỗ lực truy xuất trái phép dữ liệu.
  3. Module RAG truy xuất dữ liệu sổ sách hiện tại và ngữ cảnh dòng tiền doanh nghiệp.
  4. Copilot tạo phản hồi ngắn gọn kèm dẫn chứng số liệu thực tế và đề xuất phương án ứng phó.
* **Luồng thay thế (Alternative Flow):** Khi phát hiện truy vấn vi phạm chính sách bảo mật hoặc nỗ lực prompt injection: Hệ thống từ chối trả lời, ghi log cảnh báo mã `SEC-403`.
* **Hậu điều kiện:** Lịch sử phiên hội thoại được lưu vết phục vụ kiểm toán nội bộ.

---

### UC006: Simulate Financing Repayment Scenarios
* **Mã Use Case:** UC006
* **Tác nhân:** SME Owner
* **Tiền điều kiện:** Người dùng đã chọn 1 gói cấp vốn từ danh sách đề xuất của UC004.
* **Luồng sự kiện chính (Basic Flow):**
  1. Người dùng cấu hình thông số gói vay (Số tiền vay mong muốn, Kỳ hạn, Lãi suất dự kiến).
  2. Hệ thống tính toán bảng lịch trả nợ chi tiết (Gốc + Lãi theo dư nợ giảm dần hoặc niên kim).
  3. Hệ thống đưa lịch trả nợ mới vào mô hình dòng tiền tương lai (UC002) để dựng đồ thị mô phỏng ứng suất (Stress-test).
  4. Hệ thống đưa ra kết luận: Gói vay có gây thâm hụt dòng tiền trong các tháng kế tiếp hay không.
* **Luồng thay thế (Alternative Flow):** Nếu lịch trả nợ làm hệ số DSCR tương lai giảm xuống dưới ngưỡng 1.0: Hệ thống cảnh báo quá tải tài chính và gợi ý điều chỉnh hạ số tiền vay hoặc kéo dài thời hạn.
* **Hậu điều kiện:** Kịch bản mô phỏng được lưu lại trong hồ sơ xin cấp vốn của doanh nghiệp.

---

## 4. Supplementary Specification

### 4.1 Security & Compliance (Trọng số 30%)
* **Phòng vệ Prompt Injection:** Xây dựng bộ tiền xử lý (Input Sanitizer & Guardrails) trước khi chuyển prompt vào LLM nhằm ngăn chặn rò rỉ dữ liệu tài chính hoặc can thiệp hạn mức vay.
* **Kiểm soát truy cập dựa trên vai trò (RBAC):** Thiết lập phân quyền chặt chẽ giữa SME Owner (toàn quyền phê duyệt) và Accountant (chỉ có quyền cập nhật số liệu và xem báo cáo).
* **Bảo mật dữ liệu (Data Privacy):** Tự động che mờ (masking) thông tin số tài khoản ngân hàng, thông tin định danh người đại diện pháp luật trước khi gửi dữ liệu qua các API mô hình ngôn ngữ lớn bên ngoài.

### 4.2 Reliability & Availability
* Cam kết mức độ sẵn sàng SLO >= 99.5% hàng tháng cho các API dịch vụ cốt lõi.
* Xử lý lỗi giao dịch: Áp dụng cơ chế Idempotency khi kết nối với Bank API nhằm tránh tạo yêu cầu cấp vốn trùng lặp.

### 4.3 Performance
* Thời gian phản hồi truy vấn qua Copilot Chatbot: p95 <= 3 giây.
* Thời gian tính toán mô hình dự báo dòng tiền và kiểm tra stress-test: <= 2 giây.

---

# PHỤ LỤC: KHẢO SÁT & ĐÁNH GIÁ CÁC SẢN PHẨM TƯƠNG TỰ TRÊN THỊ TRƯỜNG (MARKET BENCHMARKING & GAP ANALYSIS)

## 1. Bối cảnh thị trường
Trong phân khúc quản trị tài chính doanh nghiệp vừa và nhỏ (SME), các công cụ truyền thống (ERP, phần mềm kiểm toán đóng gói) thường chỉ mang tính chất thống kê hồi tố (backward-looking) — ghi nhận những giao dịch đã phát sinh thay vì chủ động dự báo tương lai (forward-looking). Sự bùng nổ của AI Agent và Large Language Models (LLMs) đã mở ra một làn sóng sản phẩm hỗ trợ tài chính thế hệ mới. 

Để định vị năng lực cạnh tranh cho **Lotus Fin** trong khuôn khổ đề tài *Topic E (SME Finance Copilot)* của FinTechathon 2026, hệ thống đã thực hiện phân tích các giải pháp tiêu biểu trên thế giới và tại khu vực. Các sản phẩm được đưa vào bảng khảo sát đều là các nền tảng tài chính/AI có thật trên thị trường quốc tế:

* **Agicap:** [agicap.com](https://agicap.com/) — Nền tảng SaaS quản lý và dự báo dòng tiền cho SME hàng đầu châu Âu.
* **Float:** [floatapp.com](https://floatapp.com/) — Ứng dụng dự báo dòng tiền kết nối trực tiếp với Xero, QuickBooks và FreeAgent.
* **QuickBooks (Intuit Assist):** [quickbooks.intuit.com](https://quickbooks.intuit.com/) — Hệ thống kế toán phổ biến toàn cầu với trợ lý AI tích hợp.
* **Xero (Just Ask Xero - JAX):** [xero.com](https://www.xero.com/) — Nền tảng kế toán đám mây tích hợp Generative AI hỗ trợ tương tác tự nhiên.
* **Microsoft Copilot for Finance:** [microsoft.com/en-us/microsoft-365/copilot/copilot-for-finance](https://www.microsoft.com/en-us/microsoft-365/copilot/copilot-for-finance) — Trợ lý AI tài chính chuyên sâu của Microsoft tích hợp vào Excel và ERP.
* **Finmap:** [finmap.online](https://finmap.online/) — Công cụ quản lý dòng tiền và phân tích thu chi cho SME/Startup tích hợp AI bot/Telegram bot.
* **Gradient Labs:** [gradientlabs.ai](https://gradientlabs.ai/) — AI Agent tự động hóa các quy trình vận hành và tín dụng trong lĩnh vực Fintech/Banking.

*(Các link trên để kiểm chứng trực tiếp tính năng sản phẩm).*

---

## 2. Phân tích chi tiết các sản phẩm tương tự

### 2.1 Agicap & Float (Nhóm công cụ chuyên quản trị dòng tiền - Cash Flow Management)
* **Mô hình hoạt động:** Là các giải pháp SaaS chuyên biệt về lập kế hoạch dòng tiền, kết nối trực tiếp với tài khoản ngân hàng và sổ sách kế toán (QuickBooks, Xero).
* **Điểm mạnh:**
  * Khả năng dựng đồ thị dự báo thu chi tiền mặt đa kỳ hạn (30/60/90 ngày) rất trực quan.
  * Đồng bộ tự động hóa đơn phải thu (AR) và phải trả (AP).
* **Hạn chế đối với SME:**
  * Tính năng dự báo chủ yếu là **rule-based** (dựa trên thuật toán cộng trừ tuyến tính), thiếu khả năng thích ứng linh hoạt với các cú sốc doanh thu bất ngờ hoặc phân tích nhân quả phức tạp.
  * Hoàn toàn thiếu vắng module **Financing Matching** — khi dự báo thấy thâm hụt tiền, hệ thống chỉ dừng lại ở việc báo đỏ mà không thể kết nối hoặc đề xuất các giải pháp tài trợ vốn ngân hàng khả thi cho doanh nghiệp.
  * Không có giao diện Copilot đàm thoại tự nhiên để giải thích các nguyên nhân tiềm ẩn.

---

### 2.2 QuickBooks Online & Xero AI Copilot (Nhóm hệ sinh thái ERP/Kế toán phổ thông)
* **Mô hình hoạt động:** Hệ thống kế toán đám mây trọn gói dành cho doanh nghiệp siêu nhỏ và nhỏ, đã tích hợp trợ lý AI để tự động hóa nghiệp vụ sổ sách.
* **Điểm mạnh:**
  * Tự động hóa tốt khâu phân loại chứng từ, đối soát sao kê ngân hàng và lập báo cáo P&L, Balance Sheet.
  * Tệp khách hàng lớn và độ bao phủ cao.
* **Hạn chế đối với SME:**
  * **Thiếu năng lực phân tích tín dụng chuyên sâu (Credit Underwriting Readiness):** Báo cáo tài chính sinh ra nhằm mục đích khai thuế/nội bộ, chưa được chuẩn hóa theo các tiêu chuẩn thẩm định tín dụng khắt khe của ngân hàng thương mại (như tính toán hệ số DSCR, dòng tiền tự do phục vụ nợ FCF).
  * Trợ lý AI chủ yếu hỗ trợ tra cứu tính năng hoặc tóm tắt số liệu quá khứ, chưa đóng vai trò như một **CFO ảo** chủ động đưa ra khuyến nghị chiến lược và chạy thử kịch bản vay.

---

### 2.3 Obol AI / Finmap AI Copilot (Nhóm AI Copilot tài chính chuyên dụng thế hệ mới)
* **Mô hình hoạt động:** Các nền tảng FinTech tiên phong ứng dụng Generative AI để biến dữ liệu tài chính thô thành trợ lý phân tích tự động bằng ngôn ngữ tự nhiên.
* **Điểm mạnh:**
  * Hỗ trợ hỏi đáp tự nhiên (Plain-English Q&A) về tình hình tài chính doanh nghiệp (*"Tại sao tuần này biên lợi nhuận giảm?"*, *"Dòng tiền khả dụng còn bao nhiêu?"*).
  * Tự động phát hiện bất thường trong chi phí nhà cung cấp và cảnh báo nợ đọng.
* **Hạn chế đối với SME:**
  * Trọng tâm phục vụ nội bộ phòng tài chính (CFO/Finance Teams) của doanh nghiệp lớn hoặc các startup công nghệ; độ phức tạp cao đối với các chủ doanh nghiệp SME truyền thống (nhà hàng, xưởng sản xuất, bán lẻ).
  * Chưa tích hợp cơ chế mô phỏng trả nợ (Repayment Stress-test) gắn với các tiêu chí cấp tín dụng của ngân hàng đối tác.

---

### 2.4 Intuitech / Gradient Labs (Nhóm AI Agent tự động hóa cấp tín dụng phía Ngân hàng)
* **Mô hình hoạt động:** Các nền tảng AI Agent cung cấp cho ngân hàng và tổ chức tài chính để tự động hóa quy trình thẩm định, giải ngân và thu hồi nợ đối với khoản vay SME.
* **Điểm mạnh:**
  * Khả năng bóc tách hơn 1.200 trường dữ liệu tài chính, tự động hóa soạn thảo hồ sơ đề xuất tín dụng (Credit Proposals).
  * Đảm bảo tiêu chuẩn an toàn bảo mật và tuân thủ ngân hàng cực kỳ khắt khe.
* **Khoảng trống thị trường:**
  * Các giải pháp này phục vụ **phía ngân hàng (Lenders/Underwriters)**, không phải công cụ dành cho **chủ doanh nghiệp SME (Borrowers)**. SME vẫn gặp rào cản lớn do không hiểu tiêu chí chấm điểm tín dụng của ngân hàng, dẫn đến tỷ lệ hồ sơ bị từ chối cao.

---

## 3. Giá trị khác biệt và Lợi thế cạnh tranh của Lotus Fin (Competitive Moat)

1. **Lấp đầy khoảng cách giữa SME và Ngân hàng (Bilateral Bridge):**  
   Hầu hết công cụ trên thị trường hoặc chỉ hỗ trợ kế toán nội bộ (QuickBooks, Float), hoặc chỉ phục vụ thẩm định của ngân hàng (Intuitech). **Lotus Fin đóng vai trò là cầu nối:** giúp SME chuẩn hóa dữ liệu dòng tiền theo đúng ngôn ngữ mà bộ phận thẩm định tín dụng ngân hàng yêu cầu (chỉ số DSCR, Cash Runway, dòng tiền thực tế).

2. **Vòng lặp khép kín: "Cảnh báo thâm hụt -> Khớp nối nguồn vốn -> Mô phỏng khả năng trả nợ":**  
   Khi phát hiện doanh nghiệp có nguy cơ thiếu hụt tiền mặt trong 45 ngày tới (UC002), Lotus Fin không chỉ đưa ra cảnh báo bị động mà ngay lập tức gợi ý các gói cấp vốn phù hợp từ ngân hàng đối tác (UC004) và cho phép chủ doanh nghiệp kiểm tra thử kịch bản trả nợ để đảm bảo không bị quá tải thanh khoản (UC006).

3. **Kiến trúc bảo mật hai lớp (Security & Compliance First):**  
   Khác với các chatbot AI thông thường dễ bị tấn công qua prompt injection hoặc làm lộ thông tin tài chính nhạy cảm, Lotus Fin tích hợp cơ chế che mờ định danh (Data Masking) và lớp lọc kiểm soát (Guardrail) nghiêm ngặt, đáp ứng tiêu chí đánh giá an toàn thông tin (trọng số 30%) của cuộc thi FinTechathon.