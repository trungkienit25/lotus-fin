# LOTUS FIN — 代码库架构概览 (整洁架构与面向对象设计)

---

## 1. 架构介绍与核心目标
Lotus Fin 采用严格的标准 **整洁六边形架构 (Ports & Adapters)** 组织金融业务智能，划分为四大核心层次：`Presentation (表现层)` → `Application (应用编排层)` → `Domain (领域核心层)` → `Infrastructure (基础设施与适配器层)`。

**核心架构目标:**
1. **整洁六边形架构**: 表现层、用例编排、核心业务实体与底层网关之间严格关注点分离。
2. **框架解耦独立性**: 核心金融计算引擎 (F001 - F007) 以及 ReAct 自主循环完全脱离 Frappe 全局函数，支持在纯原生 Python 环境下进行 100% 确定性单测。
3. **严格遵循 SOLID 与经典设计模式**: 杜绝条件分支 if-else 堆砌，广泛应用策略模式 (Strategy)、工厂模式 (Factory)、命令模式 (Command)、适配器模式 (Adapter) 与门面模式 (Facade)。
4. **100% 零回归兼容性**: 保持对既有 Frappe Desk API 端点与前后端数据契约的完全向后兼容。

---

## 2. 架构目录结构

```text
lotus_fin/
├── presentation/                      # [第 1 层] 表现层 (Web 与 Desk 统一入口)
│   ├── controller/
│   │   └── copilot_controller.py      # HTTP 控制器
│   └── dto/
│       ├── chat_request.py            # 请求校验 Pydantic DTO
│       └── chat_response.py           # 标准化响应 Pydantic DTO
│
├── application/                       # [第 2 层] 应用编排层 (Use Cases 业务编排)
│   ├── agent/
│   │   ├── agent_runner.py            # ReAct 有界自主循环
│   │   └── prompt_engine.py           # 金融提示词引擎与事实锚定组装器
│   ├── port/                          # 抽象端口定义 (依赖倒置)
│   │   ├── i_chat_service.py          # 对话服务接口
│   │   ├── i_llm_provider.py          # 大语言模型抽象端口
│   │   └── i_tool_registry.py         # 工具注册与权限过滤端口
│   └── service/
│       └── copilot_service.py         # IChatService 具体实现
│
├── domain/                            # [第 3 层] 领域核心层 (实体、规则与契约)
│   ├── model/
│   │   ├── chat_session.py            # 对话会话与消息实体
│   │   └── user_context.py            # 用户安全主体值对象 (Company, RBAC, Cutoff Date)
│   ├── policy/
│   │   └── permission_policy.py       # 模块权限安全策略契约
│   ├── schema/
│   │   ├── tool_definition.py         # OpenAPI 格式工具元数据规范
│   │   ├── tool_call_request.py       # 工具调用请求 DTO
│   │   └── tool_execution_result.py   # 确定性工具执行结果 DTO
│   └── repository/
│       └── i_session_repository.py    # 会话持久化接口
│
├── infrastructure/                    # [第 4 层] 基础设施与适配器层 (具体实现)
│   ├── llm/                           # 大模型适配器与工厂
│   │   ├── adapter/
│   │   │   ├── openai_llm_adapter.py  # OpenAI / DeepSeek / vLLM 适配器
│   │   │   ├── gemini_llm_adapter.py  # Google Gemini 适配器
│   │   │   └── mock_llm_adapter.py    # 离线确定性单元测试 Mock 适配器
│   │   └── llm_factory.py             # 支持密钥轮询的大模型工厂
│   ├── erpnext/
│   │   └── erpnext_gateway.py         # ERPNext 会计总账与发票数据提取网关
│   ├── security/
│   │   └── frappe_access_gateway.py   # 权限访问控制网关
│   ├── observability/
│   │   └── observability.py           # 脱敏日志记录与链路追踪
│   ├── persistence/
│   │   └── in_memory_session_repository.py # 会话内存存储适配器
│   └── tool/                          # 命令与注册表模式
│       ├── command/
│       │   └── base_tool_command.py   # IToolCommand 命令接口
│       ├── registry/
│       │   ├── tool_registry.py       # 工具注册表实现
│       │   └── default_tools.py       # 默认工具加载器
│       ├── invoker/
│       │   └── tool_invoker.py        # 具备熔断与异常捕获的工具执行器
│       └── impl/                      # 封装 F001-F007 的具体命令类
│
├── modules/                           # [第 5 层] 确定性金融计算核心引擎
│   ├── f001_health/                   # 财务健康诊断引擎 (P&L, DSCR, 营运资本)
│   ├── f002_cashflow/                 # 30 天每日现金流预测引擎
│   ├── f003_risk_signal/              # 应收逾期与应付账期聚集扫描引擎
│   ├── f004_what_if/                  # 9 大 KPI 多变量情景压力测试引擎
│   ├── f005_financing/                # 信贷产品智能撮合与准入评分引擎
│   ├── f006_repayment/                # 等额本息/本金还款计划与利率冲击引擎
│   └── f007_debt_recovery/            # 逾期账单催收通知与凭据生成引擎
│
└── tests/                             # 自动化回归测试套件 (>460 个测试用例)
```

---

## 3. 架构深度指南套件

1. [**01_LAYER_ARCHITECTURE.md**](01_LAYER_ARCHITECTURE.md):
   - 深入讲解四层体系、依赖倒置原则及业务独立性设计。
2. [**02_DIRECTORY_AND_IMPLEMENTATION.md**](02_DIRECTORY_AND_IMPLEMENTATION.md):
   - 逐文件剖析核心类实现、数据结构与控制反转方式。
3. [**03_INTERACTION_AND_DESIGN_PATTERNS.md**](03_INTERACTION_AND_DESIGN_PATTERNS.md):
   - 类交互时序图、ReAct 执行生命周期以及 SOLID 设计原则的落地证据。
4. [**04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md**](04_CHAT_PERSISTENCE_AND_AI_AUDIT_LOGGING_PLAN.md):
   - 双层会话持久化（Redis 缓存 + MariaDB 总账）与 OpenTelemetry 审计标准规范。
