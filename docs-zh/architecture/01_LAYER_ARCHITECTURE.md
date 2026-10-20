# 分层整洁架构 (CLEAN / HEXAGONAL ARCHITECTURE)

---

## 1. 依赖倒置原则 (The Dependency Rule)

在 Lotus Fin 的架构设计中，依赖关系**必须且只能由外向内单向依赖**：

```text
  +-------------------------------------------------------------+
  | 1. PRESENTATION LAYER (表现层: HTTP 控制器, 校验 DTO)       |
  |   │                                                         |
  |   ▼                                                         |
  | 2. APPLICATION LAYER (应用层: 用例编排, 智能体循环, 抽象端口)|
  |   │                                                         |
  |   ▼                                                         |
  | 3. DOMAIN LAYER (领域核心层: 核心业务实体, 规则契约)         |
  |   ▲                                                         |
  |   │                                                         |
  | 4. INFRASTRUCTURE LAYER (基础设施层: 大模型适配器, 总账网关)|
  +-------------------------------------------------------------+
```

- **领域层 (Domain Layer)**: 核心业务的心脏，**绝对不依赖**任何外部框架、第三方库、Frappe 框架或具体的数据库驱动。
- **应用层 (Application Layer)**: 仅依赖领域层及应用层自身声明的抽象接口 (Ports)，绝不直接实例化具体的底层适配器（控制反转 IoC）。
- **基础设施层 (Infrastructure Layer)**: 实现应用层定义的接口端口，并在运行时通过依赖注入提供给应用层调用。
- **表现层 (Presentation Layer)**: 负责接收用户或前端发起的请求，将原始请求体反序列化并校验为强类型的 DTO，然后分派给应用服务执行。

---

## 2. 各层级核心职责

### 2.1. 表现层 (`lotus_fin/presentation`)
- **核心职责**:
  - 作为系统对外暴露的唯一网络入口（覆盖 Frappe Web Desk、REST API 及 React 前端）。
  - 接收外部 HTTP 请求，利用 Pydantic 严格校验数据类型与边界条件。
  - 从用户当前会话 (`frappe.session`) 中解析并建立当前用户的安全上下文 (`UserPrincipal`)。
- **核心组件**:
  - `controller/copilot_controller.py`: 接收自然语言问答或财务操作指令。
  - `dto/chat_request.py`: `SendMessageDTO`（请求入参校验契约）。
  - `dto/chat_response.py`: `ChatResponseDTO`, `ToolTraceDTO`, `UIWidgetDTO`（统一出参信封）。

---

### 2.2. 应用编排层 (`lotus_fin/application`)
- **核心职责**:
  - 编排业务流程。该层不包含具体的财务数学计算公式，但严格负责协调整个用例的执行生命周期。
  - 管理 ReAct 智能体执行闭环：组装系统提示词、向大模型提供已授权的工具注册表、处理工具调用意图、协调工具执行器并将执行事实组装为最终解答。
  - 声明出站抽象端口 (Ports)，满足依赖倒置原则。
- **核心组件**:
  - `service/copilot_service.py`: 实现 `IChatService` 接口，协调会话状态与智能体调度。
  - `agent/agent_runner.py`: 带有最大迭代步数保护 (`max_iterations = 4`) 的 ReAct 推理循环。
  - `agent/prompt_engine.py`: 组装财务事实锚定规则、企业租户安全边界及大模型行为约束。
  - `port/i_chat_service.py`: 对话服务抽象接口。
  - `port/i_llm_provider.py`: 大模型统一调用抽象接口 (`generate(messages, tools)`）。
  - `port/i_tool_registry.py`: 可用金融工具注册、发现与权限过滤接口。

---

### 2.3. 领域核心层 (`lotus_fin/domain`)
- **核心职责**:
  - 系统的领域模型核心，封装核心实体 (Entities)、值对象 (Value Objects) 与全局契约。
  - 彻底解耦于底层数据库或具体云服务。
- **核心组件**:
  - `model/chat_session.py`: 维护多轮对话状态、上下文历史及工具执行审计跟踪 (`ToolTrace`)。
  - `model/user_context.py`: `UserPrincipal` 安全主体值对象（包含用户 ID、归属公司、RBAC 角色组及财务截止日期）。
  - `policy/permission_policy.py`: 声明 `IPermissionPolicy` 与 `ModuleSecurityPolicy`。
  - `schema/tool_definition.py`: 兼容 OpenAPI 标准的工具元数据 JSON Schema。
  - `schema/tool_call_request.py`: 大模型生成的工具调用结构体。
  - `schema/tool_execution_result.py`: 带有 UI 卡片配置的确定性工具执行输出。
  - `repository/i_session_repository.py`: 会话持久化抽象仓储接口。

---

### 2.4. 基础设施与适配器层 (`lotus_fin/infrastructure`)
- **核心职责**:
  - 落地实现上层声明的所有抽象端口与接口。
  - 承担具体的网络与 I/O 交互：向大模型厂商发起 HTTP 调用、查询 ERPNext 底层总账表、内存缓存维护及系统审计日志输出。
- **核心组件**:
  - `llm/adapter/`: 具体大模型适配器（`OpenAILLMAdapter`, `GeminiLLMAdapter`, `MockLLMAdapter`）。
  - `llm/llm_factory.py`: `LLMProviderFactory` 动态读取配置并按需初始化适配器。
  - `security/frappe_access_gateway.py`: 落地实现权限策略，校验用户对 DocType 及会计报表的访问权。
  - `erpnext/erpnext_gateway.py`: 从总账 (GL Entry)、应收 (AR)、应付 (AP) 中提取事实数据。
  - `observability/observability.py`: 具备敏感信息自动脱敏 (PII-free) 与 Trace ID 贯穿的审计日志器。
  - `tool/command/` 与 `tool/invoker/`: 运用命令模式将各个金融计算引擎封装为受安全保护的可执行工具。

---

### 2.5. 金融计算核心模块层 (`lotus_fin/modules`)
- **核心职责**:
  - 承载独立封装的 7 大确定性金融计算引擎 (F001 - F007)。
  - 纯原生 Python 运行，实行严格的高精度 Decimal 运算，杜绝一切大模型数值幻觉。

