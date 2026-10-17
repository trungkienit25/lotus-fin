# 🏛️ LOTUS FIN — CODEBASE ARCHITECTURE OVERVIEW (CLEAN ARCHITECTURE & OOP)

---

## 1. Introduction & Architecture Context
Lotus Fin structures financial intelligence using a standardized **Clean Hexagonal Architecture (Ports & Adapters)** across four layers: `Presentation` ➔ `Application` ➔ `Domain` ➔ `Infrastructure`.

**Core Architectural Goals:**
1. **Clean Hexagonal Architecture**: Strict separation of concerns between presentation, orchestration, core business entities, and infrastructure gateways.
2. **Framework Independence**: Decoupling financial calculation engines (F001 - F007) and the ReAct autonomous loop from Frappe global functions, allowing 100% of the core math to be tested in pure hermetic Python.
3. **Strict SOLID & OOP Design Patterns**: Replacing fragmented if-else logic with Strategy, Factory, Command, Adapter, and Facade design patterns.
4. **100% Zero-Regression Compatibility**: Preserving full backward compatibility with Frappe Desk endpoints and previous API contracts.

---

## 2. Architectural Directory Tree

```text
lotus_fin/
├── presentation/                      # [LAYER 1] Presentation (Web & Desk Entrypoints)
│   ├── controller/
│   │   └── copilot_controller.py      # HTTP & Frappe Desk Controller
│   └── dto/
│       ├── chat_request.py            # Pydantic DTO for request validation
│       └── chat_response.py           # Pydantic DTO for normalized UI responses
│
├── application/                       # [LAYER 2] Application & Orchestration (Use Cases)
│   ├── agent/
│   │   ├── agent_runner.py            # ReAct Loop (Autonomous Function Calling)
│   │   └── prompt_engine.py           # Financial System Prompt & Grounding Assembler
│   ├── port/                          # Abstract Ports (Inversion of Control)
│   │   ├── i_chat_service.py          # Chat Use Case Interface
│   │   ├── i_llm_provider.py          # Abstract LLM Provider Port
│   │   └── i_tool_registry.py         # Tool Registry & Filtering Port
│   └── service/
│       └── copilot_service.py         # IChatService Concrete Implementation
│
├── domain/                            # [LAYER 3] Core Domain (Entities, Schemas & Policies)
│   ├── model/
│   │   ├── chat_session.py            # ChatSession, ChatMessage, MessageRole Entities
│   │   └── user_context.py            # UserPrincipal Value Object (Company, RBAC, Date)
│   ├── policy/
│   │   └── permission_policy.py       # ModuleSecurityPolicy & IPermissionPolicy
│   ├── schema/
│   │   ├── tool_definition.py         # Tool JSON Schema for Function Calling
│   │   ├── tool_call_request.py       # Tool Call Request DTO
│   │   └── tool_execution_result.py   # Deterministic Execution Result DTO
│   └── repository/
│       └── i_session_repository.py    # Session Repository Interface
│
├── infrastructure/                    # [LAYER 4] Infrastructure & Adapters (Concrete)
│   ├── llm/                           # LLM Adapters & Multi-Provider Factory
│   │   ├── adapter/
│   │   │   ├── openai_llm_adapter.py  # OpenAI / DeepSeek / vLLM Adapter
│   │   │   ├── gemini_llm_adapter.py  # Google Gemini 1.5/2.5 Adapter
│   │   │   └── mock_llm_adapter.py    # Zero-cost Mock Adapter for Hermetic Unit Tests
│   │   └── llm_factory.py             # LLMProviderFactory with multi-key rotation
│   ├── erpnext/
│   │   └── erpnext_gateway.py         # ERPNext General Ledger & Invoice Data Gateway
│   ├── security/
│   │   └── frappe_access_gateway.py   # Frappe RBAC Access Gateway
│   ├── observability/
│   │   └── observability.py           # PII-redacted Logging & Correlation ID Tracing
│   ├── persistence/
│   │   └── in_memory_session_repository.py # Session Persistence Adapter
│   └── tool/                          # Command & Registry Pattern
│       ├── command/
│       │   └── base_tool_command.py   # IToolCommand Interface (Command Pattern)
│       ├── registry/
│       │   ├── tool_registry.py       # Tool Registry & Whitelist Filter
│       │   └── default_tools.py       # Default Financial Tools Loader
│       ├── invoker/
│       │   └── tool_invoker.py        # Fail-safe Protected Tool Invoker
│       └── impl/                      # Concrete Commands wrapping F001-F007:
│           ├── f001_health_tool.py    # Financial Health Snapshot
│           ├── f002_cashflow_tool.py  # 30-Day Cash Flow Forecast
│           ├── f003_risk_tool.py      # Early Risk Signal Detector
│           ├── f004_whatif_tool.py    # What-If Stress Testing
│           ├── f005_financing_tool.py # SME Loan Product Matcher
│           └── f006_repayment_tool.py # Loan Amortization (PMT)
│
├── modules/                           # [LAYER 5] Canonical Deterministic Financial Engines
│   ├── f001_health/                   # Financial Health Engine (P&L, Balance Sheet, DSCR)
│   ├── f002_cashflow/                 # Direct Cashflow Forecast Engine (30-day Horizon)
│   ├── f003_risk_signal/              # Cashflow & AR/AP Risk Signal Detection
│   ├── f004_what_if/                  # Multi-variable What-If Simulation Engine
│   ├── f005_financing/                # Loan Matching & Commercial Eligibility Rules
│   ├── f006_repayment/                # Debt Amortization & Repayment Schedules
│   └── f007_debt_recovery/            # Debt Statement Follow-up & Automated Dispatch
│
└── tests/                             # Automated Test Suites (>460 tests)
```

---

## 3. Architecture Documentation Suite

1. [**docs/architecture/01_LAYER_ARCHITECTURE.md**](01_LAYER_ARCHITECTURE.md):
   - Detailed layer responsibilities, independence principles, and the Dependency Rule across the 4 layers.
2. [**docs/architecture/02_DIRECTORY_AND_IMPLEMENTATION.md**](02_DIRECTORY_AND_IMPLEMENTATION.md):
   - Comprehensive file-by-file directory explanation and implementation details.
3. [**docs/architecture/03_INTERACTION_AND_DESIGN_PATTERNS.md**](03_INTERACTION_AND_DESIGN_PATTERNS.md):
   - Class interactions, the ReAct loop lifecycle, sequence diagrams, and SOLID / Design Pattern compliance.
4. [**docs/architecture/04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md**](04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md):
   - Two-tier session persistence (Redis + JSON) and AI Sandbox operational audit logging design.
