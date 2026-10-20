# 目录结构与实现映射详解

---

## 1. 表现层实现 (`lotus_fin/presentation`)

### 1.1. `presentation/controller/copilot_controller.py`
- **核心职责**:
  - 提供 `CopilotController` 入口控制器与 `handle_send_message(request_data, service=None)` 方法。
  - 解析外部输入 JSON 载荷至强类型的 `SendMessageDTO`，触发 Pydantic 类型校验。
  - 从全局会话上下文 `frappe.session.user` 中提取用户标识，结合 `get_verified_company(dto.company)` 建立强类型 `UserPrincipal` 安全主体。
  - 调用 `CopilotService` 应用服务（支持从依赖注入工厂 `get_copilot_service()` 获取）。
  - 将处理结果包装为 `ChatResponseDTO` 统一响应信封返回。

### 1.2. `presentation/dto/`
- **`chat_request.py`**:
  - `SendMessageDTO(BaseModel)`: 校验入参字段 `message: str`, `session_id: Optional[str]`, `company: Optional[str]`, `as_of_date: Optional[str]`。
- **`chat_response.py`**:
  - `ChatResponseDTO(BaseModel)`: 封装出参字段 `session_id: str`, `reply: str`, `tool_called: Optional[str]`, `tool_output: Optional[Dict]`, `ui_widget: Optional[Dict]`, `executed_tools: List[str]`。

---

## 2. 应用编排层实现 (`lotus_fin/application`)

### 2.1. `application/agent/agent_runner.py`
- **核心职责**:
  - 管理有界 ReAct 智能体循环生命周期：
    ```text
    初始化 working_context = [SystemPrompt, HistoryMessages]
    循环迭代 (最大迭代次数 max_iterations = 4):
      1. response = llm_provider.generate(working_context, tools)
      2. 若大模型未产生 tool_calls:
            -> 生成并返回最终的 AgentExecutionResult；
      3. 若大模型请求 tool_calls:
            -> 将 ASSISTANT 思考步骤追加至 working_context；
            -> 针对每个待执行 tool_call:
                 调用 tool_invoker.invoke(tool_call, user) 获取执行结果；
                 将 TOOL 事实反馈信息追加至 working_context；
    若达到最大迭代上限仍未收敛:
      -> 强制触发兜底保护，基于已有财务事实生成总结回复。
    ```

### 2.2. `application/agent/prompt_engine.py`
- **系统提示词组装与事实锚定**:
  - 动态注入系统角色定位、财务安全边界、可用工具功能定义及租户隔离约束。

### 2.3. `application/service/copilot_service.py`
- **业务协调编排**:
  - 实现 `IChatService` 核心应用契约。
  - 借助 `ISessionRepository` 实现会话历史提取与持久化。
  - 从 `IToolRegistry` 中依据 `user.has_permission` 过滤得到当前用户有权调用的工具清单。
  - 协调 `AgentRunner` 执行并捕获每次工具执行的审计追踪 (`ToolTrace`)。

---

## 3. 领域核心层实现 (`lotus_fin/domain`)

### 3.1. `domain/model/`
- **`chat_session.py`**: 维护会话实体状态、消息列表及工具执行链。
- **`user_context.py`**: `UserPrincipal` 安全主体值对象，封装用户唯一标识、授权公司列表、RBAC 角色及财务结算基准日。

### 3.2. `domain/policy/permission_policy.py`
- **安全策略契约**: 声明 `IPermissionPolicy` 抽象接口及 `ModuleSecurityPolicy` 策略实体。

### 3.3. `domain/schema/`
- `tool_definition.py`: 遵循 OpenAPI 标准的 JSON Schema 工具元数据声明。
- `tool_call_request.py`: 大模型生成的结构化工具调用请求对象。
- `tool_execution_result.py`: 包含确定性计算结果与 UI 卡片配置的执行回包。

---

## 4. 基础设施与适配器层实现 (`lotus_fin/infrastructure`)

### 4.1. `infrastructure/llm/`
- **`adapter/openai_llm_adapter.py`**:
  - 实现 `ILLMProvider` 抽象接口。
  - 发起标准 HTTP POST 请求调用 `/chat/completions`。
  - 解析 OpenAI 原生 Function Calling 协议并转换为标准 `ToolCallRequest`。
- **`adapter/gemini_llm_adapter.py`**:
  - 实现 `ILLMProvider` 抽象接口。
  - 调用 Google Gemini REST API (`generateContent`)。
  - 将 `ToolDefinition` 映射为 Gemini 的 `functionDeclarations`。
  - 支持多 API Key 自动故障转移与轮询。
- **`llm_factory.py`**:
  - `LLMProviderFactory.create_provider()`: 依据 `.env` 配置按需加载对应大模型适配器。

### 4.2. `infrastructure/security/frappe_access_gateway.py`
- **安全权限控制网关**:
  - 落地实现 `IPermissionPolicy` 抽象接口。
  - 维护 `MODULE_SECURITY_REGISTRY` 注册表，解耦具体 DocType 授权规则。
  - 对未授权调用实施 Fail-closed 默认阻断，返回通用 `FORBIDDEN` 错误。

### 4.3. `infrastructure/tool/`
- **`command/base_tool_command.py`**: 声明 `IToolCommand` 命令契约：`definition`、`is_authorized(user)` 与 `execute(arguments, user)`。
- **`registry/tool_registry.py`**: 实现工具注册、查找与租户权限动态过滤。
- **`invoker/tool_invoker.py`**: 承担工具执行生命周期管理、超时控制与异常降级。
- **`impl/`**: 封装 F001 至 F007 各金融计算模块的具体命令实现类。

---

## 5. 金融计算核心模块 (`lotus_fin/modules`)

- `f001_health/`: 财务健康诊断引擎（计算毛利率、营业净现金流、偿债倍数 DSCR、营运资金）。
- `f002_cashflow/`: 30 天每日现金流预测引擎（基于合同收付款排期，杜绝数值插值幻觉）。
- `f003_risk_signal/`: 财务风险信号扫描引擎（逾期账款峰值、应付账期过度聚集）。
- `f004_what_if/`: 多变量情景压力测试模拟器（9 项核心 KPI 联动仿真）。
- `f005_financing/`: 中小企业信贷产品撮合与准入评分引擎。
- `f006_repayment/`: 等额本息/本金还款计划排期与利率基点冲击引擎。
- `f007_copilot/`: 账单催收协助与交互式凭据确认分发引擎。
