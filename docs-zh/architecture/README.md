# 🏛️ LOTUS FIN — 代码库整洁架构与面向对象设计总览 (CLEAN ARCHITECTURE & OOP)

---

## 1. 架构总览与重构背景
Lotus Fin 采用标准的**整洁六边形架构 (Clean Hexagonal Architecture / Ports & Adapters)**，系统被划分为四个核心解耦层级：`表现层 (Presentation)` ➔ `应用用例层 (Application)` ➔ `领域核心层 (Domain)` ➔ `基础设施适配层 (Infrastructure)`。

**核心架构设计目标：**
1. **整洁六边形架构：** 严格解耦接口表现、业务编排、领域实体与底层基础设施网关。
2. **独立于外部框架：** 将全部金融数学算法（F001 - F007）和 AI ReAct 推理循环从 Frappe 框架全局函数中彻底剥离，实现 100% 纯 Python 环境下的毫秒级自动化测试。
3. **全面贯彻 SOLID 与面向对象设计模式：** 淘汰散落硬编码的分支逻辑，全面采用策略模式 (Strategy)、工厂模式 (Factory)、命令模式 (Command)、适配器模式 (Adapter) 与外观模式 (Facade)。
4. **100% 零回归向下兼容：** 严格保障对 Frappe Desk 端点及原有 API 协议的无缝兼容。

---

## 2. 核心架构目录全景拓扑

```text
lotus_fin/
├── presentation/                      # [第一层] 表现交互层 (Web 与 Desk 统一入口)
│   ├── controller/
│   │   └── copilot_controller.py      # HTTP 与 Frappe Desk 交互控制器
│   └── dto/
│       ├── chat_request.py            # Pydantic 输入参数校验 DTO
│       └── chat_response.py           # Pydantic 规范化前端呈现 DTO
│
├── application/                       # [第二层] 应用编排与业务用例层 (Use Cases)
│   ├── agent/
│   │   ├── agent_runner.py            # ReAct 循环内核 (自主工具调度与函数调用)
│   │   └── prompt_engine.py           # 金融专业 System Prompt 与规则组装器
│   ├── port/                          # 抽象端口定义 (依赖倒置 Inversion of Control)
│   │   ├── i_chat_service.py          # 对话用例抽象接口
│   │   ├── i_llm_provider.py          # LLM 模型服务商统一适配端口
│   │   └── i_tool_registry.py         # 工具注册与白名单过滤端口
│   └── service/
│       └── copilot_service.py         # IChatService 用例实现类
│
├── domain/                            # [第三层] 领域核心层 (Entities, Schemas & Policies)
│   ├── model/
│   │   ├── chat_session.py            # 会话与消息领域实体 (ChatSession, MessageRole)
│   │   └── user_context.py            # 用户安全上下文值对象 (公司、角色 RBAC、当前日期)
│   ├── policy/
│   │   └── permission_policy.py       # 模块安全策略与权限策略接口
│   ├── schema/
│   │   ├── tool_definition.py         # Function Calling 工具 JSON Schema 定义
│   │   ├── tool_call_request.py       # 工具调用请求 DTO
│   │   └── tool_execution_result.py   # 确定性计算结果 DTO
│   └── repository/
│       └── i_session_repository.py    # 会话仓储抽象接口
│
├── infrastructure/                    # [第四层] 基础设施适配层 (Concrete Adapters)
│   ├── llm/                           # LLM 适配器与多模型工厂
│   │   ├── adapter/
│   │   │   ├── openai_llm_adapter.py  # OpenAI / DeepSeek / vLLM 适配器
│   │   │   ├── gemini_llm_adapter.py  # Google Gemini 1.5/2.5 适配器
│   │   │   └── mock_llm_adapter.py    # 零调用成本单元测试 Mock 适配器
│   │   └── llm_factory.py             # 支持多 Key 轮询的 LLMProviderFactory
│   ├── erpnext/
│   │   └── erpnext_gateway.py         # ERPNext 核心总账 GL、发票查询网关
│   ├── security/
│   │   └── frappe_access_gateway.py   # Frappe RBAC 权限核验适配器
│   ├── observability/
│   │   └── observability.py           # PII 敏感脱敏日志与链路跟踪 (Correlation ID)
│   ├── persistence/
│   │   └── in_memory_session_repository.py # 会话内存持久化适配器
│   └── tool/                          # 命令模式与工具注册中心
│       ├── command/
│       │   └── base_tool_command.py   # IToolCommand 命令接口
│       ├── registry/
│       │   ├── tool_registry.py       # 统一工具注册表与权限白名单过滤器
│       │   └── default_tools.py       # 预置金融计算工具集加载工厂
│       ├── invoker/
│       │   └── tool_invoker.py        # 防御性安全调用器 (Fail-safe Invoker)
│       └── impl/                      # 封装 F001-F007 的具体命令类：
│           ├── f001_health_tool.py    # 企业健康度体检
│           ├── f002_cashflow_tool.py  # 30 天确定性现金流预测
│           ├── f003_risk_tool.py      # 财务异动与风险预警
│           ├── f004_whatif_tool.py    # 压力测试与敏感性分析
│           ├── f005_financing_tool.py # 商业信贷贷款智能撮合
│           └── f006_repayment_tool.py # 商业贷款等额分期测算 (PMT)
│
├── modules/                           # [第五层] 确定性金融数学与核心业务引擎
│   ├── f001_health/                   # 财务健康诊断引擎 (损益、资产负债、DSCR)
│   ├── f002_cashflow/                 # 30天确定性现金流排期与跑道测算
│   ├── f003_risk_signal/              # 集中兑付挤兑与账期异动雷达
│   ├── f004_what_if/                  # 宏观与业务波动多变量模拟引擎
│   ├── f005_financing/                # 商业银行中小企业流动资金信贷准入核验
│   ├── f006_repayment/                # 国际标准贷款分期测算与基点利率冲击模型
│   └── f007_debt_recovery/            # 逾期往来账目核实与催告邮件自动投递
│
└── tests/                             # 自动化工程级测试用例集 (>460 tests)
```

---

## 3. 架构专题文档索引

1. [**docs-zh/architecture/01_LAYER_ARCHITECTURE.md**](01_LAYER_ARCHITECTURE.md):
   - 详细剖析 4 层架构的核心职责边界、完全解耦原则与单向依赖传递规则（Dependency Rule）。
2. [**docs-zh/architecture/02_DIRECTORY_AND_IMPLEMENTATION.md**](02_DIRECTORY_AND_IMPLEMENTATION.md):
   - 深入逐个解析每个核心目录、重点文件代码结构及具体落地技术方案。
3. [**docs-zh/architecture/03_INTERACTION_AND_DESIGN_PATTERNS.md**](03_INTERACTION_AND_DESIGN_PATTERNS.md):
   - 类图调用拓扑、ReAct 推理全生命周期图解、时序图以及设计模式落地实践。
4. [**docs-zh/architecture/04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md**](04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md):
   - 双层会话持久化方案 (Redis + JSON) 与企业级 AI 沙箱运行审计日志技术规范。
