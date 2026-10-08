# 📂 CHI TIẾT TỪNG THƯ MỤC VÀ CÁCH TRIỂN KHAI MÃ NGUỒN

---

## 1. Tầng Presentation (`lotus_fin/presentation`)

### 1.1. `presentation/controller/copilot_controller.py`
- **Cách triển khai**:
  - Cung cấp class `CopilotController` với phương thức tĩnh `handle_send_message(request_data, service=None)`.
  - Nhận dictionary thô từ client, chuyển thành `SendMessageDTO` để validate kiểu dữ liệu.
  - Phân giải bối cảnh người dùng: Lấy `frappe.session.user`, thẩm định quyền truy cập công ty qua `get_verified_company(dto.company)`, khởi tạo Value Object `UserPrincipal`.
  - Khởi tạo `CopilotService` (mặc định lấy từ factory tự động nạp môi trường qua `get_copilot_service()`).
  - Trả về dictionary đã qua kiểm định chuẩn bởi `ChatResponseDTO`.

### 1.2. `presentation/dto/`
- **`chat_request.py`**:
  - `SendMessageDTO(BaseModel)`: Chứa các trường `message: str`, `session_id: Optional[str]`, `company: Optional[str]`, `as_of_date: Optional[str]`.
- **`chat_response.py`**:
  - `ChatResponseDTO(BaseModel)`: Chứa `session_id: str`, `reply: str`, `tool_called: Optional[str]`, `tool_output: Optional[Dict]`, `ui_widget: Optional[Dict]`, `executed_tools: List[str]`.

---

## 2. Tầng Application (`lotus_fin/application`)

### 2.1. `application/agent/agent_runner.py`
- **Cách triển khai**:
  - Triển khai thuật toán ReAct Loop:
    ```text
    Khởi tạo working_context = [SystemPrompt, HistoryMessages]
    Lặp lại tối đa 4 lần:
      1. response = llm_provider.generate(working_context, tools)
      2. Nếu không có tool_calls:
            -> Thêm câu trả lời vào session, trả về AgentExecutionResult.
      3. Nếu có tool_calls:
            -> Lưu tin nhắn ASSISTANT vào working_context.
            -> Duyệt qua từng tool_call:
                 Gọi tool_invoker.invoke(tool_call, user)
                 Lưu kết quả TOOL vào working_context.
    Nếu hết 4 lần mà chưa dừng:
      -> Kích hoạt cơ chế fallback an toàn, trả về cảnh báo cùng các số liệu đã trích xuất được.
    ```

### 2.2. `application/agent/prompt_engine.py`
- **Cách triển khai**:
  - Cung cấp hàm `assemble_system_prompt(user: UserPrincipal) -> str`.
  - Tích hợp các nguyên tắc định hướng chặt chẽ:
    1. *Greeting & Intent*: Khi người dùng chỉ chào hỏi xã giao, giới thiệu năng lực hỗ trợ mà không tự ý kích hoạt tool.
    2. *Deterministic Evidence Only*: Nghiêm cấm bịa đặt số liệu kế toán; mọi số tiền, tỷ lệ, ngày nợ đều phải xuất phát từ tool.
    3. *Corporate Boundary*: Gắn chặt ranh giới công ty mục tiêu (`user.company`) vào prompt để tránh rò rỉ dữ liệu chéo công ty.

### 2.3. `application/port/`
- **`i_llm_provider.py`**: Khai báo Interface `ILLMProvider` với phương thức `generate(messages: List[ChatMessage], tools: List[ToolDefinition]) -> LLMResponse`.
- **`i_chat_service.py`**: Khai báo Interface `IChatService` với phương thức `process_message(session_id, message, user) -> Dict[str, Any]`.
- **`i_tool_registry.py`**: Khai báo Interface `IToolRegistry` để lấy danh sách công cụ được phép cho một `UserPrincipal`.

---

## 3. Tầng Domain (`lotus_fin/domain`)

### 3.1. `domain/model/`
- **`chat_session.py`**:
  - Chứa thực thể `ChatSession` lưu giữ danh sách `ChatMessage` và danh sách `ToolExecutionResult`.
  - Phương thức `get_context_window(max_messages=8)`: Giới hạn cửa sổ ngữ cảnh để tối ưu token gửi lên mô hình.
- **`domain/policy/permission_policy.py`**:
  - `ModuleSecurityPolicy(dataclass, frozen=True)`: Khai báo allowlist tĩnh của từng module (`permitted_reports`, `permitted_evidence_doctypes`).
  - `IPermissionPolicy(ABC)`: Cổng trừu tượng xác thực thẩm quyền đọc công ty, báo cáo sổ cái và truy vết bằng chứng.

---

## 4. Tầng Infrastructure (`lotus_fin/infrastructure`)

### 4.1. `infrastructure/llm/`
- **`adapter/openai_llm_adapter.py`**:
  - Hiện thực hóa `ILLMProvider`.
  - Giao tiếp qua HTTP REST `urllib.request` tới endpoint `/chat/completions`.
  - Hỗ trợ Native Function Calling: Parse `choice.message.tool_calls` thành danh sách `ToolCallRequest`.
- **`adapter/gemini_llm_adapter.py`**:
  - Hiện thực hóa `ILLMProvider`.
  - Giao tiếp trực tiếp với Google Gemini REST API (`generateContent`).
  - Chuyển `ToolDefinition` thành `functionDeclarations`.
  - Xử lý các tin nhắn `TOOL` với vai trò `role: user` và `parts: [{functionResponse: ...}]` theo đúng chuẩn Google Generative AI.
- **`llm_factory.py`**:
  - `LLMProviderFactory.create_provider()`: Tự động nạp `.env` từ thư mục gốc hoặc thư mục app, phân giải biến môi trường `LOTUS_AI_PROVIDER` (hoặc `LOTUS_LLM_PROVIDER`) để khởi tạo Adapter phù hợp.

### 4.2. `infrastructure/security/frappe_access_gateway.py`
- **Cách triển khai**:
  - Hiện thực hóa `IPermissionPolicy`.
  - Quản lý `MODULE_SECURITY_REGISTRY: Dict[str, ModuleSecurityPolicy]` cho phép mở rộng quy tắc phân quyền cho module mới mà không sửa mã nguồn cũ (OCP).
  - Kiểm tra thẩm quyền truy cập Company, Report và DocType qua `frappe.has_permission()` và `Report.is_permitted()`.
  - Đảm bảo cơ chế bảo mật Fail-closed: Bất kỳ trường hợp thiếu quyền, sai định dạng ref hoặc ngoài allowlist đều ném ngoại lệ `FORBIDDEN`.

### 4.3. `infrastructure/tool/`
- **`command/base_tool_command.py`**: Giao diện `IToolCommand` với 3 phương thức: `definition` (lấy spec schema), `is_authorized(user)` (kiểm tra phân quyền), và `execute(arguments, user)` (thực thi tác vụ).
- **`registry/tool_registry.py`**: Bộ nhớ lưu trữ danh sách lệnh `IToolCommand`, lọc công cụ theo `is_authorized(user)`.
- **`invoker/tool_invoker.py`**: Bộ thực thi an toàn. Bọc toàn bộ quá trình parse tham số và gọi tool trong khối `try...except`, đảm bảo nếu tool gặp lỗi sẽ trả về `ToolExecutionResult(is_success=False, error_message=...)` thay vì làm sập cả hệ thống Copilot.
- **`impl/f001_health_tool.py` - `f006_repayment_tool.py`**: Các lớp Command cụ thể đóng gói 6 engine tài chính thành các công cụ chuẩn mực.

---

## 5. Tầng Modules (`lotus_fin/modules`)

Toàn bộ các engine tài chính cốt lõi nằm độc lập trong thư mục `modules/`:
1. **`f001_health/`**: Tính toán các chỉ số sức khỏe tài chính: Doanh thu, COGS, Biên lợi nhuận gộp, DSCR, Working Capital, Quick Ratio từ số cái ERPNext.
2. **`f002_cashflow/`**: Dự báo dòng tiền trực tiếp 30 ngày (Direct Cash Forecast) dựa trên số dư đầu kỳ (Opening Cash) và các nghĩa vụ hợp đồng (Sales Invoice AR, Purchase Invoice AP). Có cơ chế phát hiện thâm hụt (Shortfall Detection) và đối chiếu số cái kép (Ledger Reconciliation).
3. **`f003_risk_signal/`**: Quét và phát hiện các rủi ro công nợ quá hạn (AR Overdue spikes) và các đợt thanh toán nhà cung cấp dồn dập (AP Clusters).
4. **`f004_what_if/`**: Phòng lab mô phỏng kịch bản đa biến: Áp dụng các bộ điều chỉnh (Sales, Collection Delay, Expense, Financing) và đo lường sự biến thiên trên 9 KPI tài chính.
5. **`f005_financing/`**: Ghép nối nhu cầu vốn lưu động của doanh nghiệp với danh mục sản phẩm tín dụng ngân hàng, chấm điểm điều kiện cấp tín dụng (Eligibility Scoring).
6. **`f006_repayment/`**: Lập lịch trả nợ (Amortization Schedule: trả gốc đều, trả góp đều), mô phỏng áp lực sốc lãi suất (+100 bps, +200 bps).
