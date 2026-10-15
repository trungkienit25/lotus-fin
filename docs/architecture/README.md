# 🏛️ LOTUS FIN — TỔNG QUAN KIẾN TRÚC CODEBASE (CLEAN ARCHITECTURE & OOP)

---

## 1. Giới Thiệu & Bối Cảnh Refactor
Trước đây, codebase Lotus Fin phát triển phân tán với các logic nghiệp vụ cũ bị trộn lẫn giữa tầng UI (Frappe Desk), tầng gọi API và các script AI thử nghiệm. Nhiều logic tính toán tài chính bị hardcode, coupled chặt chẽ với framework Frappe, gây khó khăn cho việc mở rộng và kiểm thử độc lập.

**Mục tiêu của đợt tái cấu trúc (Refactoring Milestone):**
1. **Thiết lập Clean Hexagonal Architecture (Ports & Adapters)** chuẩn hóa 4 tầng: `Presentation` ➔ `Application` ➔ `Domain` ➔ `Infrastructure`.
2. **Độc lập Framework**: Tách toàn bộ các thuật toán tài chính (F001 - F006) và lõi AI ReAct Loop khỏi các hàm global của Frappe, cho phép chạy unit test 100% trong môi trường thuần Python.
3. **Áp dụng triệt để SOLID & OOP Design Patterns**: Thay thế toàn bộ code phân nhánh hardcode (if/else rải rác) bằng Strategy, Factory, Command, Adapter, và Facade Pattern.
4. **Bảo toàn 100% Backward Compatibility**: Không gây hồi quy bất kỳ luồng API hoặc dữ liệu lịch sử nào (Zero Logic Regression).

---

## 2. Sơ Đồ Cây Thư Mục Kiến Trúc (Architecture Tree)

```text
lotus_fin/
├── presentation/                      # [TẦNG 1] GIAO TIẾP (Web & Desk Entrypoints)
│   ├── controller/
│   │   └── copilot_controller.py      # Controller nhận request từ Frappe Desk / HTTP
│   └── dto/
│       ├── chat_request.py            # Pydantic DTO xác thực input đầu vào
│       └── chat_response.py           # Pydantic DTO chuẩn hóa payload trả về UI
│
├── application/                       # [TẦNG 2] ĐIỀU PHỐI NGHIỆP VỤ (Orchestration & Use Cases)
│   ├── agent/
│   │   ├── agent_runner.py            # Vòng lặp ReAct Loop (Autonomous Function Calling)
│   │   └── prompt_engine.py           # Bộ lắp ráp System Prompt & Grounding Rules
│   ├── port/                          # Abstract Ports (Inversion of Control)
│   │   ├── i_chat_service.py          # Port giao tiếp Chat Use Case
│   │   ├── i_llm_provider.py          # Port trừu tượng hóa nhà cung cấp LLM
│   │   └── i_tool_registry.py         # Port đăng ký và lọc Tool
│   └── service/
│       └── copilot_service.py         # Triển khai IChatService
│
├── domain/                            # [TẦNG 3] NGHIỆP VỤ CỐT LÕI (Core Entities & Schemas)
│   ├── model/
│   │   ├── chat_session.py            # Entity ChatSession, ChatMessage, MessageRole
│   │   └── user_context.py            # Value Object UserPrincipal (Company, RBAC, Date)
│   ├── policy/
│   │   └── permission_policy.py       # Entity ModuleSecurityPolicy & IPermissionPolicy
│   ├── schema/
│   │   ├── tool_definition.py         # Spec JSON Schema công cụ cho Function Calling
│   │   ├── tool_call_request.py       # DTO yêu cầu gọi Tool từ LLM
│   │   └── tool_execution_result.py   # DTO kết quả thực thi tất định
│   └── repository/
│       └── i_session_repository.py    # Interface kho lưu trữ phiên trò chuyện
│
├── infrastructure/                    # [TẦNG 4] HẠ TẦNG & TÍCH HỢP (Concrete Adapters)
│   ├── llm/                           # LLM Adapters & Multi-model Factory
│   │   ├── adapter/
│   │   │   ├── openai_llm_adapter.py  # Adapter OpenAI / DeepSeek / vLLM (Function Calling)
│   │   │   ├── gemini_llm_adapter.py  # Adapter Google Gemini 1.5/2.5/3.6 (Tool Calling)
│   │   │   └── mock_llm_adapter.py    # Mock Provider cho Unit Tests (0 cost)
│   │   └── llm_factory.py             # LLMProviderFactory tự động nạp cấu hình từ .env
│   ├── erpnext/
│   │   └── erpnext_gateway.py         # Gateway truy xuất dữ liệu sổ cái GL, AR, AP
│   ├── security/
│   │   └── frappe_access_gateway.py   # Triển khai kiểm tra quyền truy cập (Frappe RBAC)
│   ├── observability/
│   │   └── observability.py           # Hệ thống log bảo mật lọc PII & truy vết correlation ID
│   ├── persistence/
│   │   └── in_memory_session_repository.py # Bộ nhớ lưu trữ phiên chat
│   └── tool/                          # Command & Registry Pattern
│       ├── command/
│       │   └── base_tool_command.py   # Interface IToolCommand (Command Pattern)
│       ├── registry/
│       │   ├── tool_registry.py       # Quản lý & Whitelist tool theo quyền người dùng
│       │   └── default_tools.py       # Factory nạp sẵn 6 financial tools
│       ├── invoker/
│       │   └── tool_invoker.py        # Bộ thực thi an toàn bọc ngoại lệ (Fail-safe Invoker)
│       └── impl/                      # 6 Concrete Commands bọc các Engine tài chính:
│           ├── f001_health_tool.py    # Bọc engine Financial Health
│           ├── f002_cashflow_tool.py  # Bọc engine Cash Forecast 30 days
│           ├── f003_risk_tool.py      # Bọc engine Risk Signal
│           ├── f004_whatif_tool.py    # Bọc engine What-If Stress Testing
│           ├── f005_financing_tool.py # Bọc engine Loan Matching
│           └── f006_repayment_tool.py # Bọc engine Repayment Schedule
│
├── modules/                           # [TẦNG 5] CÁC ENGINE TÍNH TOÁN TẤT ĐỊNH (Canonical Business Engines)
│   ├── f001_health/                   # Financial Health Engine (P&L, Balance Sheet, DSCR, EBITDA)
│   ├── f002_cashflow/                 # Direct Cashflow Forecast Engine (Dự báo 30 ngày)
│   ├── f003_risk_signal/              # Cashflow & AR/AP Risk Signal Detection
│   ├── f004_what_if/                  # Multi-variable What-If Simulation Engine
│   ├── f005_financing/                # Loan Matching & Credit Eligibility Rules
│   └── f006_repayment/                # Debt Amortization & Repayment Schedules
│
├── security/                          # Tương thích ngược: Facade chuyển tiếp sang FrappeAccessGateway
├── core/compat/                       # MetaPathFinder map namespace cũ sang modules.*
├── lotus_fin_ai/                      # 7 Frappe Desk Pages UI (Giao diện người dùng)
└── tests/                             # Hệ thống kiểm thử tự động (>460 tests)
```

---

## 3. Bản Đồ Tài Liệu Chi Tiết

Để tìm hiểu sâu từng khía cạnh kiến trúc và hiện thực mã nguồn, vui lòng xem các tài liệu chuyên đề:

1. [**docs/architecture/01_LAYER_ARCHITECTURE.md**](01_LAYER_ARCHITECTURE.md):
   - Phân tích chi tiết trách nhiệm, nguyên tắc độc lập và luồng phụ thuộc (Dependency Rule) của 4 tầng kiến trúc.
2. [**docs/architecture/02_DIRECTORY_AND_IMPLEMENTATION.md**](02_DIRECTORY_AND_IMPLEMENTATION.md):
   - Giải thích vai trò của từng thư mục, từng file code chính và cách chúng được hiện thực.
3. [**docs/architecture/03_INTERACTION_AND_DESIGN_PATTERNS.md**](03_INTERACTION_AND_DESIGN_PATTERNS.md):
   - Bản đồ tương tác giữa các Class, vòng đời ReAct Loop, sơ đồ Sequence và minh chứng tuân thủ SOLID & Design Patterns.
4. [**docs/architecture/04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md**](04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md):
   - Thiết kế chi tiết hệ thống lưu trữ lịch sử trò chuyện bền vững (Two-tier Persistence: Redis + JSON) và Hệ thống ghi nhật ký vận hành AI Sandbox (JSON Lines) đáp ứng tiêu chí Mục 06 FinTechathon 2026.

