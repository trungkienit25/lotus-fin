# 🏛️ THIẾT KẾ & KẾ HOẠCH TRIỂN KHAI: HỆ THỐNG LƯU TRỮ LỊCH SỬ CHAT VÀO CƠ SỞ DỮ LIỆU (DATABASE PERSISTENCE) & AUDIT LOGGING THEO CHUẨN QUỐC TẾ

> **Mã tài liệu:** `ARCH-04-PLAN`  
> **Dự án:** Lotus Fin (2026 FinTechathon — Topic E: SME Financial AI Copilot)  
> **Phiên bản:** 2.0 (Refined with Database-backed Persistence & Chatbot Industry Standards)  
> **Trạng thái:** Kế hoạch kỹ thuật chi tiết (Detailed Technical Plan)  
> **Nguyên tắc kỹ thuật:** Tuân thủ triệt để Clean / Hexagonal Architecture, SOLID, Design Patterns và các chuẩn công nghiệp quốc tế về thiết kế Chatbot (OpenAI Assistant API v2, OpenTelemetry GenAI Semantic Conventions, Enterprise Multi-Tenant Isolation).

---

## 1. Các Chuẩn Thiết Kế Chatbot Quốc Tế Được Áp Dụng (Recognized Chatbot Standards)

Nhằm đảm bảo giải pháp đạt đẳng cấp doanh nghiệp và đáp ứng các tiêu chuẩn thẩm định khắt khe nhất của Ban giám khảo cuộc thi quốc tế, hệ thống lưu trữ hội thoại của Lotus Fin được thiết kế bám sát 4 bộ chuẩn công nghiệp được công nhận rộng rãi:

### 1.1. Chuẩn OpenAI Assistant API v2 (Thread — Message — Run Step Lifecycle)
* **Thread (Phiên hội thoại):** Đại diện cho một luồng đối thoại liên tục giữa người dùng và AI. Thread là đối tượng độc lập, có định danh duy nhất (`id`), bối cảnh sở hữu (`company`, `user_id`), trạng thái (`status`), và metadata.
* **Message (Tin nhắn):** Mỗi lượt hội thoại trong Thread là một Message có kiểu vai trò rõ ràng (`role`: `user`, `assistant`, `system`, `tool`). Tin nhắn có tính chất **Append-only** (chỉ ghi thêm, không sửa đè) để bảo toàn tính toàn vẹn kiểm toán.
* **Run Step / Tool Execution (Dấu vết thực thi công cụ):** Mỗi khi Agent gọi một công cụ tài chính (F001 - F006), hành động đó được lưu trữ có cấu trúc: Tên Tool, Tham số đầu vào (JSON), Kết quả trả về (JSON), Thời gian phản hồi và Trạng thái hoàn thành.

### 1.2. Chuẩn OpenTelemetry GenAI Semantic Conventions (v1.27+)
* Chuẩn hóa siêu dữ liệu quan sát (Observability):
  * `gen_ai.system`: Tên nền tảng AI (`gemini`, `openai`, `lotus-react`).
  * `gen_ai.request.model`: Tên mô hình chính xác (`gemini-flash-lite-latest`, `gpt-4o`, `mock`).
  * `gen_ai.latency_ms`: Độ trễ toàn trình đo bằng mili-giây.
  * `trace_id` & `span_id`: Mã truy vết duy nhất xuyên suốt từ Frontend ➔ Backend ➔ LLM ➔ Database Sổ cái Kế toán ➔ Audit Log.

### 1.3. Chuẩn LangChain / LangGraph Stateful Checkpointing & Memory
* **Stateful Dialogue Checkpoint:** Lưu trữ trạng thái ngữ cảnh hội thoại bền vững vào Cơ sở dữ liệu (Database-backed Memory).
* **Buffer Window Memory:** Giới hạn cửa sổ ngữ cảnh nạp vào LLM (`max_messages = 8-10`) để tối ưu hóa chi phí token và tránh quá tải context window, nhưng **vẫn lưu giữ toàn bộ 100% lịch sử** trong database để người dùng xem lại bất kỳ lúc nào.

### 1.4. Chuẩn An ninh Doanh nghiệp & Multi-Tenant Data Isolation (ISO/IEC 27001 & SOC 2)
* **Cô lập dữ liệu nghiêm ngặt theo Doanh nghiệp (`company` boundary):** Mọi câu truy vấn Database đều được index và lọc theo `company`. Người dùng thuộc công ty A tuyệt đối không thể đọc lịch sử chat của công ty B.
* **Zero-PII Audit Trail:** Tự động lọc sạch các thông tin nhạy cảm (mật khẩu, API keys cá nhân) trước khi lưu vào database và file log.

---

## 2. Thiết Kế Lược Đồ Cơ Sở Dữ Liệu (Database Schema Design)

Dữ liệu các cuộc trò chuyện được lưu trữ trực tiếp vào Cơ sở dữ liệu (MariaDB của Frappe) thông qua 2 DocType chuyên biệt được index tối ưu:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      tabLotus Chat Session (Thread)                    │
│────────────────────────────────────────────────────────────────────────│
│ PK name / session_id       : VARCHAR(140) [INDEX, UNIQUE]              │
│    title                   : VARCHAR(255) (Tiêu đề tóm tắt hội thoại)  │
│    user                    : VARCHAR(140) [INDEX] (Link: User)         │
│    company                 : VARCHAR(140) [INDEX] (Link: Company)      │
│    status                  : VARCHAR(32)  (Active / Archived / Closed) │
│    first_prompt            : TEXT         (Câu hỏi mở đầu phiên)       │
│    total_messages          : INT          (Tổng số lượt tin nhắn)      │
│    last_tool_called        : VARCHAR(140) (Công cụ tài chính gần nhất) │
│    last_message_at         : DATETIME     [INDEX]                      │
│    creation / modified     : DATETIME                                  │
└────────────────────────────────────────────────────────────────────────┘
                                    │ 1
                                    │
                                    │ N
┌────────────────────────────────────────────────────────────────────────┐
│                      tabLotus Chat Message (Message & Tool Step)       │
│────────────────────────────────────────────────────────────────────────│
│ PK name / message_id       : VARCHAR(140) [INDEX, UNIQUE]              │
│ FK session                 : VARCHAR(140) [INDEX] (Link: Session)      │
│    seq_id                  : INT          (Thứ tự tuần tự trong phiên) │
│    role                    : VARCHAR(32)  (user/assistant/system/tool) │
│    content                 : LONGTEXT     (Nội dung câu hỏi/trả lời)   │
│    tool_called             : VARCHAR(140) (F001..F006 nếu có)          │
│    tool_inputs             : LONGTEXT     (JSON tham số đầu vào)       │
│    tool_output             : LONGTEXT     (JSON kết quả tất định)      │
│    ui_widget               : LONGTEXT     (JSON payload vẽ biểu đồ)    │
│    execution_status        : VARCHAR(32)  (SUCCESS / FAILED)           │
│    latency_ms              : INT          (Thời gian chạy mili-giây)   │
│    llm_provider            : VARCHAR(64)  (gemini / openai / mock)     │
│    model_name              : VARCHAR(64)  (Tên model LLM)              │
│    trace_id                : VARCHAR(64)  [INDEX] (Liên kết Audit Log) │
│    timestamp               : DATETIME     [INDEX]                      │
└────────────────────────────────────────────────────────────────────────┘
```

### Ưu điểm kỹ thuật của thiết kế này:
1. **Hiệu năng cao & Khả năng mở rộng:** Tách riêng `Lotus Chat Session` và `Lotus Chat Message` (quan hệ 1-N chuẩn) giúp việc lấy danh sách các phiên trò chuyện cũ ở Sidebar siêu nhanh (`SELECT * FROM tabLotus Chat Session WHERE user = ... ORDER BY last_message_at DESC`), không phải load toàn bộ nội dung tin nhắn nặng nề.
2. **Hỗ trợ truy vết kiểm toán 1-1 (Traceability):** Trường `trace_id` trong từng message ánh xạ trực tiếp sang file nhật ký `lotus_ai_operations.jsonl`, thỏa mãn tuyệt đối tiêu chí **06 Execution Evidence** của BTC.
3. **Lưu trữ trọn vẹn UI Widgets:** Dữ liệu biểu đồ, bảng tính toán (tool_output, ui_widget) được lưu dưới dạng JSON nguyên vẹn, cho phép khi người dùng F5 hoặc mở lại phiên chat cũ thì các biểu đồ phân tích tài chính vẫn hiển thị nguyên vẹn như lúc vừa hỏi!

---

## 3. Kiến Trúc Phân Tầng Clean Architecture & SOLID

Tuân thủ nguyên tắc **Dependency Inversion** và phân tách trách nhiệm rõ ràng:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION LAYER (Web Endpoints, DTOs, Desk UI, CLI)             │
│    - CopilotController (APIs: send, history, list_sessions, reset)     │
│    - ChatCopilot JS (localStorage session_id + Session List Sidebar)   │
│    - run.sh evidence (CLI runner)                                      │
├────────────────────────────────────────────────────────────────────────┤
│ 2. APPLICATION LAYER (Use Cases, Ports, Orchestration)                 │
│    - IChatService, IOperationLogService (Ports)                        │
│    - OperationLogService (Audit Interceptor)                           │
│    - CopilotService (ReAct Loop + DB Persistence)                      │
├────────────────────────────────────────────────────────────────────────┤
│ 3. DOMAIN LAYER (Entities, Value Objects, Repository Interfaces)       │
│    - ChatSession, ChatMessage, ToolExecutionResult (Pure Entities)     │
│    - SandboxOperationLogEntry (Audit Entity)                           │
│    - ISessionRepository, IOperationLogRepository (Abstract Ports)      │
├────────────────────────────────────────────────────────────────────────┤
│ 4. INFRASTRUCTURE LAYER (Persistence, Adapters, Storage)               │
│    - FrappeDatabaseSessionRepository (Ghi/Đọc MariaDB qua Frappe ORM)  │
│    - CompositeSessionRepository (L1 Redis Cache + L2 MariaDB Store)    │
│    - JsonLinesOperationLogRepository (Ghi log append-only .jsonl)      │
│    - InMemorySessionRepository (Dùng cho Unit Tests không cần DB)      │
└────────────────────────────────────────────────────────────────────────┘
```

### Chi tiết các Design Patterns triển khai:
1. **Repository Pattern (`ISessionRepository`):**
   * Định nghĩa hợp đồng thuần túy ở Domain: `get_session(session_id) -> ChatSession`, `save_session(session) -> None`, `list_sessions(company, user) -> List[SessionSummary]`.
   * Tầng Domain hoàn toàn không biết bên dưới là MariaDB, Redis hay In-Memory.
2. **Composite / Two-Tier Caching Pattern (`CompositeSessionRepository`):**
   * **L1 Cache (Redis via `FrappeCacheSessionRepository`):** Phản hồi siêu tốc (<2ms) cho các lượt tương tác đang diễn ra trong phiên.
   * **L2 Store (Database via `FrappeDatabaseSessionRepository`):** Lưu trữ bền vững vĩnh viễn trong MariaDB.
   * **Luồng đọc:** Kiểm tra L1 Cache ➔ Nếu miss, đọc từ L2 Database và nạp (warm-up) lại vào L1.
   * **Luồng ghi:** Ghi đồng thời vào cả L1 Cache và L2 Database trong cùng một giao dịch.
3. **Interceptor / Observer Pattern:**
   * Tự động bắt sự kiện hoàn thành của mỗi bước Agent để ghi nhật ký vào `IOperationLogRepository` mà không làm thay đổi mã nguồn các công cụ tính toán F001 - F006.

---

## 4. Kế Hoạch Triển Khai Kỹ Thuật Chi Tiết (Implementation Steps)

### Bước 1: Khởi tạo DocType Cơ Sở Dữ Liệu (`lotus_fin_ai/doctype`)
Tạo định nghĩa DocType chuẩn Frappe Framework:
1. `lotus_fin/lotus_fin_ai/doctype/lotus_chat_session/`:
   * `lotus_chat_session.json`: Khai báo các cột `session_id`, `title`, `user`, `company`, `status`, `total_messages`, `last_message_at`.
   * `lotus_chat_session.py`: Controller DocType.
2. `lotus_fin/lotus_fin_ai/doctype/lotus_chat_message/`:
   * `lotus_chat_message.json`: Khai báo các cột `session`, `seq_id`, `role`, `content`, `tool_called`, `tool_inputs`, `tool_output`, `ui_widget`, `latency_ms`, `trace_id`.
   * `lotus_chat_message.py`: Controller DocType.
3. **Tính năng Self-Healing (Tự phục hồi):** Trong `FrappeDatabaseSessionRepository`, nếu phát hiện bảng chưa được tạo (do chưa migrate), tự động thực thi câu lệnh `CREATE TABLE IF NOT EXISTS` để đảm bảo hệ thống **không bao giờ bị crash**.

### Bước 2: Xây Dựng `FrappeDatabaseSessionRepository`
* **Vị trí file:** `lotus_fin/infrastructure/persistence/frappe_database_session_repository.py`
* **Chức năng:**
  * Hiện thực hóa `ISessionRepository`.
  * Thao tác trực tiếp với cơ sở dữ liệu qua `frappe.db.get_value`, `frappe.get_doc`, `frappe.db.sql`.
  * Ánh xạ (Map) hai chiều mượt mà giữa MariaDB Records ➔ Domain Model `ChatSession` (Pydantic).

### Bước 3: Hoàn Thiện `CompositeSessionRepository`
* **Vị trí file:** `lotus_fin/infrastructure/persistence/composite_session_repository.py`
* **Chức năng:** Kết nối **L1 (Redis Cache)** và **L2 (MariaDB Database)** đảm bảo vừa có tốc độ phản hồi tức thì, vừa an toàn bền vững 100%.

### Bước 4: Xây Dựng Hệ Thống Ghi Log Kiểm Toán `SandboxOperationLogger`
* **Vị trí file:** `lotus_fin/infrastructure/observability/jsonlines_operation_log_repository.py`
* **Chức năng:**
  * Ghi nhật ký chuẩn JSON Lines (`.jsonl`) ra file `/home/frappe/frappe-bench/logs/lotus_ai_operations.jsonl`.
  * Lưu đầy đủ: Timestamp, User, Sandbox Account (`Lotus-fin (Demo)`), Prompt, Intent, Tool Dispatched, Latency, Token, Trace ID.

### Bước 5: Cập Nhật `CopilotController` & Whitelisted Endpoints
* **Vị trí file:** `lotus_fin/presentation/controller/copilot_controller.py` & `lotus_fin/api/ai_insights.py`
* **Bổ sung các endpoints:**
  * `lotus_fin.api.ai_insights.get_chat_history(session_id)`: Trả về đầy đủ tin nhắn và biểu đồ cũ từ DB.
  * `lotus_fin.api.ai_insights.list_chat_sessions(company)`: Danh sách các phiên trò chuyện của người dùng.
  * `lotus_fin.api.ai_insights.reset_chat_session(session_id)`: Đặt lại phiên làm việc.
  * `lotus_fin.api.ai_insights.get_operation_logs(limit, company)`: Lấy dữ liệu nhật ký kiểm toán.
  * `lotus_fin.api.ai_insights.export_operation_logs(company)`: Tải file `.jsonl` nộp bài.

### Bước 6: Cập Nhật Giao Diện Frontend (`chat_copilot.js`)
* **Session Management:** Tự động giữ `session_id` trong `localStorage`. Khi F5 trang, tự động gọi `get_chat_history` từ Database để phục hồi lại 100% tin nhắn và biểu đồ.
* **Audit Modal:** Nút **📋 Audit Log** mở modal hiển thị trực quan các bước suy luận và gọi tool của AI.
* **Export Button:** Nút **📥 Export Evidence** tải file `.jsonl` về máy.

### Bước 7: Kịch Bản Tự Động Hóa Nghiệm Thu (`run.sh evidence`)
* Tạo script `lotus_fin/scripts/generate_sandbox_evidence.py` tự động chạy 7 câu hỏi mẫu qua 7 module (F001 -> F007), lưu cả vào Database MariaDB và xuất file `evidence/sandbox_operation_logs.jsonl`.
* Tích hợp lệnh: `./run.sh evidence`.

---

## 5. Kế Hoạch Kiểm Thử Nghiệm Thu (Verification Plan)

### 5.1. Automated Tests (`tests/test_chat_persistence_and_audit.py`)
1. `test_database_session_repository_save_and_retrieve`: Lưu session vào DB và đọc lại nguyên vẹn.
2. `test_composite_repository_cache_hit_and_miss`: Kiểm tra L1 hit, L1 miss fallback L2.
3. `test_chat_messages_preserve_tool_outputs_and_widgets`: Kiểm tra tính toàn vẹn của dữ liệu biểu đồ JSON trong tin nhắn cũ.
4. `test_sandbox_operation_logging_jsonl`: Kiểm tra định dạng JSON Lines và mã trace_id.
5. `test_multi_tenant_company_isolation`: Kiểm tra người dùng công ty khác không thể truy cập session của công ty demo.

Lệnh chạy kiểm thử:
```bash
pytest lotus_fin/lotus_fin/tests/test_chat_persistence_and_audit.py -v
```

### 5.2. Manual Verification Checklist
- [ ] Mở trình duyệt vào trang Chat Copilot, gửi câu hỏi bất kỳ.
- [ ] Kiểm tra trong database: bảng `tabLotus Chat Session` và `tabLotus Chat Message` có bản ghi mới.
- [ ] Bấm F5 tải lại trang -> Lịch sử tin nhắn và biểu đồ widget hiển thị lại nguyên vẹn.
- [ ] Bấm nút "📋 Audit Log" -> Hiển thị danh sách các lần gọi tool và độ trễ mili-giây.
- [ ] Chạy `./run.sh evidence` -> Hoàn tất 7 kịch bản và xuất file `evidence/sandbox_operation_logs.jsonl`.
