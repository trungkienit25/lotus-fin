# CLASS INTERACTIONS AND DESIGN PATTERNS (SOLID & DESIGN PATTERNS)

---

## 1. Sequence Flow Between Layers

The sequence diagram below traces the end-to-end execution path from the moment a user submits a prompt in Frappe Desk / React UI until the platform delivers a grounded financial diagnosis paired with an interactive UI widget:

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Frappe Desk / React UI)
    participant Ctrl as CopilotController
    participant Svc as CopilotService
    participant Runner as AgentRunner
    participant LLM as ILLMProvider (Gemini/OpenAI)
    participant Invoker as ToolInvoker
    participant Cmd as IToolCommand (f002_cashflow)
    participant Engine as CashflowEngine (modules/)

    User->>Ctrl: POST /api/method/chat_copilot (JSON)
    Ctrl->>Ctrl: Validate SendMessageDTO & Resolve UserPrincipal
    Ctrl->>Svc: process_message(session_id, query, user)
    Svc->>Svc: Load Session & PromptEngine.assemble()
    Svc->>Runner: run(session, system_prompt, tools, user)
    
    loop ReAct Loop (max 4 iterations)
        Runner->>LLM: generate(working_context, tools)
        LLM-->>Runner: LLMResponse (ToolCallRequest: get_cash_forecast)
        
        alt LLM requests Tool Calling
            Runner->>Invoker: invoke(tool_call, user)
            Invoker->>Cmd: execute(arguments, user)
            Cmd->>Engine: calculate_cash_forecast()
            Engine-->>Cmd: ForecastResult (EOD points, shortfalls)
            Cmd-->>Invoker: ToolExecutionResult (Data + UIWidget)
            Invoker-->>Runner: Return ToolExecutionResult
            Runner->>Runner: Append Tool response to context
        else LLM produces final answer
            Runner-->>Svc: AgentExecutionResult (Reply + Widget)
            Svc-->>Ctrl: ChatResponseDTO
            Ctrl-->>User: JSON Response (Message + Widget Payload)
        end
    end
```

---

## 2. Design Patterns Applied

The Lotus Fin codebase incorporates classical Gang of Four (GoF) design patterns to resolve core architectural challenges:

### 2.1. Command Pattern (Financial Tool Encapsulation)
- **Problem**: Engines F001 through F007 expect distinct parameters and execution contracts. Allowing AgentRunner to directly invoke concrete calculation engines would result in unwieldy switch-case branches and tight coupling.
- **Solution**:
  - The IToolCommand interface standardizes the execution contract: definition, is_authorized(user), and execute(args, user).
  - Each financial engine is encapsulated within a concrete Command (GetFinancialHealthTool, GetCashflowForecastTool, EvaluateRiskSignalTool, etc.).
  - ToolInvoker interacts solely with IToolCommand abstractions without needing insight into inner mathematical procedures.

### 2.2. Abstract Factory & Factory Method Pattern (LLM Provider Selection)
- **Problem**: The system must run offline (Mock), with Google Gemini, or with OpenAI/DeepSeek strictly based on runtime .env variables without changing source code.
- **Solution**:
  - LLMProviderFactory inspects environment variables (LOTUS_AI_PROVIDER / LOTUS_LLM_PROVIDER) and instantiates the designated ILLMProvider implementation (OpenAILLMAdapter, GeminiLLMAdapter, or MockLLMAdapter).

### 2.3. Adapter Pattern (Third-Party API Normalization)
- **Problem**: OpenAI and Google Gemini have divergent payload schemas, message roles (assistant vs. model), and function-calling conventions.
- **Solution**:
  - OpenAILLMAdapter and GeminiLLMAdapter translate between internal domain models (ChatMessage) and provider-specific schemas, reconciling response structures back into a unified LLMResponse.

### 2.4. Facade Pattern (Backward Compatibility)
- **Problem**: Existing test suites and legacy modules imported utility functions directly from lotus_fin.security.access (get_verified_company, check_report_permission).
- **Solution**:
  - Preserved lotus_fin/security/access.py as a lightweight Facade forwarding calls to FrappeAccessGateway, maintaining 100% backward compatibility without breaking existing interfaces.

### 2.5. Strategy Pattern (Module Permission Policies)
- **Problem**: Each financial module requires different permissions on Frappe reports and DocTypes (e.g., F002 needs GL Entry, F003 needs Accounts Payable).
- **Solution**:
  - Encapsulated module access rules via ModuleSecurityPolicy registered in FrappeAccessGateway. Each module constitutes an interchangeable security policy strategy.

---

## 3. SOLID Principles Compliance

| Principle | Implementation in Lotus Fin Codebase |
| :--- | :--- |
| **S — Single Responsibility** | Every class has one single reason to change: <br>• PromptEngine: Prompt composition only.<br>• AgentRunner: ReAct loop orchestration only.<br>• ToolInvoker: Fault-tolerant execution wrapper only.<br>• OpenAILLMAdapter: HTTP payload translation for OpenAI only. |
| **O — Open/Closed** | • Adding a new financial tool (e.g., F007 Debt Actions) requires creating a new class implementing IToolCommand and registering it in ToolRegistry—zero edits to AgentRunner or CopilotService.<br>• Supporting a new model provider requires authoring a new adapter implementing ILLMProvider without touching existing adapters. |
| **L — Liskov Substitution** | Any implementation of ILLMProvider (MockLLMAdapter, OpenAILLMAdapter, GeminiLLMAdapter) can substitute another in CopilotService at runtime while maintaining 100% operational parity. |
| **I — Interface Segregation** | Fine-grained interfaces prevent bloat: ILLMProvider declares only generate(); IToolCommand declares only definition, is_authorized, execute(); IPermissionPolicy isolates access evaluation. |
| **D — Dependency Inversion** | Application services (CopilotService, AgentRunner) depend solely on abstract interfaces (ILLMProvider, IToolInvoker, ISessionRepository) rather than concrete database or HTTP client implementations. Concrete instances are injected via factories. |
