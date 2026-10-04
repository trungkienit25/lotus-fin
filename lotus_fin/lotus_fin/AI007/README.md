# Lotus Fin AI007 — Financial Copilot Orchestrator

## Tổng quan
Module **AI007** đóng vai trò là "Bộ não điều phối" (Orchestrator) cho hệ thống AI của Lotus Fin. 
Nó không tự thực hiện các phép tính tài chính phức tạp mà làm nhiệm vụ:
1. **Tiếp nhận Intent:** Phân tích câu hỏi ngôn ngữ tự nhiên của người dùng (NLU/NLP).
2. **Routing (Định tuyến):** Gọi đến đúng các module chuyên sâu:
   - Cần tìm gói vay? ➔ Gọi **AI005 (Financing Matcher)**
   - Cần tính lịch trả nợ / Stress test? ➔ Gọi **AI006 (Repayment Engine)**
3. **Tổng hợp:** Gom kết quả tất định (deterministic) từ các module con và trả về một Response thống nhất cho UI (bao gồm text giải thích + data biểu đồ).

Đây là kiến trúc **Modular Monolith với Orchestrator**, giúp Lotus Fin dễ dàng mở rộng thêm AI008, AI009... sau này mà không làm phình to code xử lý hội thoại.

## Luồng hoạt động (Data Flow) cho người build hệ thống
```text
[Frontend / Chatbot UI]
        │ 1. Gửi chuỗi "Tôi muốn vay 1 tỷ" (API: lotus_fin.AI007.service.chat)
        ▼
[AI007 - service.py]
        │ 2. Khởi tạo CopilotRequest, truyền vào Orchestrator
        ▼
[AI007 - CopilotOrchestrator]
        │ 3. NLU xác định Intent = FINANCING_SUPPORT, Amount = 1 Tỷ
        │ 4. Gọi module AI005.matcher.FinancingMatcher()
        ▼
[AI005 - Matcher]
        │ 5. Trả về kết quả (các gói vay phù hợp)
        ▼
[AI007 - CopilotOrchestrator]
        │ 6. Đóng gói thành CopilotResponse (Kèm Text reply + UI Widget JSON)
        ▼
[Frontend / Chatbot UI]
        │ 7. Render câu trả lời và bảng so sánh gói vay
```

## Cấu trúc thư mục
- `models.py`: Định nghĩa `CopilotRequest`, `CopilotResponse`, và `IntentType`.
- `orchestrator.py`: Chứa logic phân loại câu hỏi (Mock NLU trong bản MVP) và logic điều phối gọi chéo sang `AI005` và `AI006`.
- `service.py`: Expose Frappe API `@frappe.whitelist()` tên là `chat`.
- `test_ai007.py`: Unit test.

## Lưu ý khi tích hợp LLM thực tế
Trong file `orchestrator.py`, hàm `_extract_intent` hiện đang dùng logic "if-else" đơn giản (Mock). 
Khi bạn build bản Production, hãy thay thế hàm đó bằng một API call (ví dụ OpenAI hoặc Vertex AI) với prompt:
`"Classify this user message into one of these intents: [FINANCING_SUPPORT, REPAYMENT_STRESS, GENERAL_QA] and extract the loan amount as JSON."`
