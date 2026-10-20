# DIRECTORY STRUCTURE AND IMPLEMENTATION GUIDE

---

## 1. Presentation Layer (lotus_fin/presentation)

### 1.1. presentation/controller/copilot_controller.py
- **Implementation Design**:
  - Implements CopilotController with static entrypoint handle_send_message(request_data, service=None).
  - Ingests raw client dictionaries, converts them into SendMessageDTO for strong Pydantic validation.
  - Resolves authenticated user context: obtains frappe.session.user, validates multi-tenant company access via get_verified_company(dto.company), and constructs the UserPrincipal value object.
  - Resolves CopilotService (defaulting to the automated environment factory get_copilot_service()).
  - Serializes and emits normalized response dictionaries through ChatResponseDTO.

### 1.2. presentation/dto/
- **chat_request.py**:
  - SendMessageDTO(BaseModel): Strongly typed fields message: str, session_id: Optional[str], company: Optional[str], as_of_date: Optional[str].
- **chat_response.py**:
  - ChatResponseDTO(BaseModel): Returns session_id: str, reply: str, tool_called: Optional[str], tool_output: Optional[Dict], ui_widget: Optional[Dict], executed_tools: List[str].

---

## 2. Application Layer (lotus_fin/application)

### 2.1. application/agent/agent_runner.py
- **Implementation Design**:
  - Encapsulates the bounded ReAct execution loop:
    ```text
    Initialize working_context = [SystemPrompt, HistoryMessages]
    Iterate up to max_iterations = 4:
      1. response = llm_provider.generate(working_context, tools)
      2. If no tool_calls present:
            -> Append final reply to session history, return AgentExecutionResult.
      3. If tool_calls present:
            -> Append ASSISTANT message to working_context.
            -> For each tool_call:
                 Execute via tool_invoker.invoke(tool_call, user)
                 Append TOOL output message to working_context.
    If loop limit reached without termination:
      -> Trigger safe fallback mechanism, returning boundary warnings alongside retrieved factual data.
    `

### 2.2. application/agent/prompt_engine.py
- **Grounding Rules Formulation**:
  - Assembles prompt contracts binding the model: forbids mathematical invention, bounds reasoning strictly to verified tool execution outputs, forces standard accounting terminology, and enforces tenant company restrictions.

### 2.3. application/service/copilot_service.py
- **Implementation Design**:
  - Implements IChatService.
  - Coordinates session retrieval/storage via ISessionRepository.
  - Gathers authorized tool commands from IToolRegistry filtered by user.has_permission.
  - Invocates AgentRunner and persists execution traces (ToolTrace).

---

## 3. Domain Layer (lotus_fin/domain)

### 3.1. domain/model/
- **chat_session.py**: Maintains multi-turn dialog sessions, in-memory message history, and execution audit trails.
- **user_context.py**: Encapsulates UserPrincipal (authenticated user ID, tenant company, role set, accounting as-of cutoff).

### 3.2. domain/policy/permission_policy.py
- **Policy Contract**: Declares abstract interface IPermissionPolicy and structural configuration ModuleSecurityPolicy.

### 3.3. domain/schema/
- tool_definition.py: Declares tool specifications as OpenAPI JSON Schema objects.
- tool_call_request.py: Strongly typed payloads for tool invocations emitted by the model.
- tool_execution_result.py: Encapsulates tool execution output, UI widget metadata, and status flags.

---

## 4. Infrastructure Layer (lotus_fin/infrastructure)

### 4.1. infrastructure/llm/
- **adapter/openai_llm_adapter.py**:
  - Implements ILLMProvider.
  - Dispatches HTTP REST calls via urllib.request to /chat/completions.
  - Handles native function calling: parses choice.message.tool_calls into ToolCallRequest instances.
- **adapter/gemini_llm_adapter.py**:
  - Implements ILLMProvider.
  - Interfaces directly with Google Gemini REST API (generateContent).
  - Serializes ToolDefinition into functionDeclarations.
  - Handles TOOL execution feedback messages as role: user with parts: [{functionResponse: ...}] in strict adherence to Gemini API specifications.
- **llm_factory.py**:
  - LLMProviderFactory.create_provider(): Reads environment configuration and initializes the designated concrete adapter.

### 4.2. infrastructure/security/frappe_access_gateway.py
- **Implementation Design**:
  - Implements IPermissionPolicy.
  - Manages MODULE_SECURITY_REGISTRY: Dict[str, ModuleSecurityPolicy] enabling extensibility for new modules without editing core codebase (OCP).
  - Validates company, report, and DocType access through frappe.has_permission() and Report.is_permitted().
  - Enforces fail-closed security: missing permissions or unlisted resources immediately trigger FORBIDDEN exceptions.

### 4.3. infrastructure/tool/
- **command/base_tool_command.py**: IToolCommand contract declaring definition, is_authorized(user), and execute(arguments, user).
- **egistry/tool_registry.py**: Tool storage and discovery service filtering tools by is_authorized(user).
- **invoker/tool_invoker.py**: Fault-isolated invocation wrapper catching exceptions and transforming failures into structured ToolExecutionResult(is_success=False, error_message=...) without crashing the Copilot session.
- **impl/**: Concrete command adapters wrapping financial engines F001 through F007 into standardized callable tools.

---

## 5. Modules Layer (lotus_fin/modules)

All deterministic financial calculation engines reside isolated in modules/:
1. **f001_health/**: Computes corporate financial health metrics: Revenue, COGS, Gross Margin, DSCR, Working Capital, Quick Ratio from ERPNext General Ledger.
2. **f002_cashflow/**: 30-day direct daily cash forecast based on opening cash balance and contractual receivables/payables (AR/AP).
3. **f003_risk_signal/**: Scans and pinpoints overdue receivables (AR spikes) and concentrated supplier payments (AP clusters).
4. **f004_what_if/**: Multi-factor financial simulation lab adjusting sales shocks, payment delays, expense surges, and debt injections across 9 financial KPIs.
5. **f005_financing/**: Matches working capital shortfalls with commercial credit products, scoring financing eligibility.
6. **f006_repayment/**: Loan amortization schedules (fixed principal vs. equal monthly payments) and interest rate shock simulations (+100 bps, +200 bps).
7. **f007_debt_recovery/**: Action-assisted receivables recovery, statement verification, and payment reminder dispatch.
