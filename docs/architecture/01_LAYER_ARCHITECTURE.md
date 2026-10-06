# 🧱 KIẾN TRÚC PHÂN TẦNG (CLEAN / HEXAGONAL ARCHITECTURE)

---

## 1. Nguyên Tắc Phụ Thuộc (The Dependency Rule)

Trong kiến trúc của Lotus Fin, hướng phụ thuộc **chỉ được phép trỏ từ ngoài vào trong**:

```text
  ┌─────────────────────────────────────────────────────────────┐
  │ 1. PRESENTATION LAYER (Web / Frappe Entrypoints, DTOs)      │
  │   ▼                                                         │
  │ 2. APPLICATION LAYER (Use Cases, Agent Runner, Ports)       │
  │   ▼                                                         │
  │ 3. DOMAIN LAYER (Entities, Domain Policies, Contracts)       │
  │   ▲                                                         │
  │ 4. INFRASTRUCTURE LAYER (LLM Adapters, DB, ERPNext Gateways) │
  └─────────────────────────────────────────────────────────────┘
```

- **Domain Layer** là trung tâm thuần khiết nhất: **KHÔNG** phụ thuộc vào bất kỳ thư viện bên thứ ba nào, không phụ thuộc Frappe, không phụ thuộc cơ sở dữ liệu.
- **Application Layer** chỉ biết tới các Interface (Ports) do Domain hoặc Application định nghĩa, không trực tiếp khởi tạo các adapter cụ thể (Inversion of Control).
- **Infrastructure Layer** hiện thực hóa các Port này và được tiêm (inject) vào Application lúc runtime.
- **Presentation Layer** tiếp nhận request từ người dùng hoặc web, chuẩn hóa thành DTO và gọi Application Service.

---

## 2. Chi Tiết Trách Nhiệm Của Từng Tầng

### 2.1. Presentation Layer (`lotus_fin/presentation`)
- **Trách nhiệm**:
  - Đóng vai trò là cửa ngõ giao tiếp đầu tiên của hệ thống với thế giới bên ngoài (Frappe Web Desk, REST API, Front-end UI).
  - Tiếp nhận HTTP request, parse payload thô thành các Data Transfer Object (DTO) được kiểm tra kiểu dữ liệu nghiêm ngặt bằng Pydantic.
  - Thiết lập bối cảnh bảo mật người dùng (`UserPrincipal`) từ phiên làm việc (`frappe.session`).
- **Thành phần cốt lõi**:
  - `controller/copilot_controller.py`: Nhận request trò chuyện hoặc thực thi tác vụ tài chính.
  - `dto/chat_request.py`: `SendMessageDTO`, `ContextFilterDTO` (validate kiểu dữ liệu đầu vào).
  - `dto/chat_response.py`: `ChatResponseDTO`, `ToolTraceDTO`, `UIWidgetDTO` (đóng gói dữ liệu trả về cho UI).

---

### 2.2. Application Layer (`lotus_fin/application`)
- **Trách nhiệm**:
  - Điều phối luồng nghiệp vụ (Orchestration). Không chứa logic toán học tính toán cụ thể nhưng nắm giữ quy trình vận hành use case.
  - Quản lý vòng lặp ReAct Agent Loop: Lắp ráp System Prompt, đưa câu hỏi và danh sách công cụ vào LLM, tiếp nhận Tool Call Request, điều phối Tool Invoker thực thi và tổng hợp câu trả lời cuối cùng.
  - Định nghĩa các cổng trừu tượng (Ports) theo nguyên lý Dependency Inversion.
- **Thành phần cốt lõi**:
  - `service/copilot_service.py`: Hiện thực hóa `IChatService`, điều phối session và giao tiếp với `AgentRunner`.
  - `agent/agent_runner.py`: Vòng lặp ReAct Loop có kiểm soát (giới hạn cứng `max_iterations = 4` để chống lặp vô hạn).
  - `agent/prompt_engine.py`: Lắp ráp các quy tắc cơ sở (Grounding Rules), ranh giới bảo mật công ty và hướng dẫn hành vi của AI.
  - `port/i_chat_service.py`: Interface của Chat Service.
  - `port/i_llm_provider.py`: Interface trừu tượng hóa phương thức `generate(messages, tools) -> LLMResponse`.
  - `port/i_tool_registry.py`: Interface đăng ký và lọc danh sách công cụ.

---

### 2.3. Domain Layer (`lotus_fin/domain`)
- **Trách nhiệm**:
  - Trái tim nghiệp vụ của hệ thống. Chứa các Entity, Value Object và Hợp đồng Schema cốt lõi.
  - Hoàn toàn độc lập với Framework Frappe và bất kỳ dịch vụ đám mây nào.
- **Thành phần cốt lõi**:
  - `model/chat_session.py`: Quản lý thực thể phiên trò chuyện, lưu vết lịch sử tin nhắn và dấu vết thực thi công cụ (`ToolTrace`).
  - `model/user_context.py`: Value Object `UserPrincipal` đại diện cho danh tính người dùng đã được xác thực, công ty sở tại, danh sách quyền RBAC và ngày chốt số liệu kế toán.
  - `policy/permission_policy.py`: Khai báo Interface `IPermissionPolicy` và `ModuleSecurityPolicy` (Open-Closed Principle).
  - `schema/tool_definition.py`: Cấu trúc đặc tả công cụ dưới dạng JSON Schema tương thích OpenAPI.
  - `schema/tool_call_request.py`: Payload yêu cầu gọi công cụ được trả về từ LLM.
  - `schema/tool_execution_result.py`: DTO kết quả thực thi tất định trả về kèm UI Widget payload.
  - `repository/i_session_repository.py`: Interface trừu tượng để lưu trữ và truy xuất ChatSession.

---

### 2.4. Infrastructure Layer (`lotus_fin/infrastructure`)
- **Trách nhiệm**:
  - Hiện thực hóa toàn bộ các Ports và Interfaces được khai báo ở tầng trên.
  - Chịu trách nhiệm giao tiếp I/O thực tế: Gọi mạng HTTP tới nhà cung cấp LLM, truy vấn cơ sở dữ liệu Frappe/ERPNext, lưu trữ bộ nhớ đệm, ghi log giám sát.
- **Thành phần cốt lõi**:
  - `llm/adapter/`: Các Adapter cụ thể (`OpenAILLMAdapter`, `GeminiLLMAdapter`, `MockLLMAdapter`) hiện thực hóa `ILLMProvider`.
  - `llm/llm_factory.py`: `LLMProviderFactory` tự động nạp `.env` và khởi tạo adapter phù hợp lúc runtime.
  - `security/frappe_access_gateway.py`: Hiện thực hóa `IPermissionPolicy`, kiểm tra quyền hạn thực tế trên DocType và Report của ERPNext.
  - `erpnext/erpnext_gateway.py`: Adapter trích xuất dữ liệu từ General Ledger, AR, AP và Invoices.
  - `observability/observability.py`: Giám sát audit log, tự động lọc sạch thông tin nhạy cảm (PII-free) và gắn mã Correlation ID.
  - `persistence/in_memory_session_repository.py`: Kho lưu trữ phiên làm việc trong RAM/Cache.
  - `tool/command/` & `tool/invoker/`: Triển khai Command Pattern bọc các Engine tính toán thành các công cụ callable an toàn.

---

### 2.5. Modules Layer (`lotus_fin/modules`)
- **Trách nhiệm**:
  - Tập hợp 6 Engine tính toán tài chính tất định chuyên biệt (F001 - F006).
  - Các Engine này hoạt động độc lập, có quy tắc kiểm tra nghiêm ngặt (Strict Numeric Contracts), không bao giờ suy diễn số liệu và bảo vệ 100% bằng bộ kiểm thử hơn 460 tests.
