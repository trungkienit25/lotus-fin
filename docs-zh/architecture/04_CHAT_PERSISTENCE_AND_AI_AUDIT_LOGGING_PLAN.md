# 技术设计：对话持久化与企业级审计追踪

> **文档标识符：** `ARCH-04-PLAN`  
> **所属系统：** Lotus Fin (2026 FinTechathon — Topic E: SME Financial AI Copilot)  
> **版本：** 2.0 (数据库持久化与工业级标准对齐)  
> **规范对齐：** 六边形整洁架构、SOLID 设计原则、OpenAI Assistant API v2、OpenTelemetry GenAI 语义规范、企业级多租户隔离。  

---

## 1. 行业领先的对话系统标准对齐

为满足金融监管对于数据留痕与审计追踪的要求，会话持久化与审计引擎对齐以下 4 项工业级标准：

### 1.1. OpenAI Assistant API v2 规范 (Thread – Message – Run Step 生命周期)
* **Thread (会话线程):** 封装用户与 AI 之间的完整交互上下文，作为独立的状态边界，包含唯一 UUID、所属租户 (`company`、`user_id`) 以及生命周期状态。
* **Message (交互消息):** 会话线程内的每条消息均采用**仅追加 (Append-only)** 模式写入，具备强类型角色 (`user`、`assistant`、`system`、`tool`)，确保审计记录不可篡改。
* **Run Step / Tool Execution (工具执行事实记录):** 记录每次金融工具 (F001–F007) 执行时的名称、入参 JSON、事实出参 JSON、耗时 (毫秒) 以及执行状态。

### 1.2. OpenTelemetry GenAI 语义规范 (v1.27+)
* 规范化可观测性指标：
  * `gen_ai.system`: 大模型生态标识 (`gemini`、`openai`、`lotus-react`)。
  * `gen_ai.request.model`: 底层模型名称 (`gemini-flash-latest`、`gpt-4o`、`mock`)。
  * `gen_ai.latency_ms`: 端到端往返耗时（毫秒）。
  * `trace_id` 与 `span_id`: 贯穿 前端 -> 后端 -> 大模型 -> 会计总账 -> 审计日志 的全链路追踪标识。

### 1.3. 状态快照与滑动窗口机制
* **持久化会话快照:** 对话历史在关系型数据库中实现强一致性落地。
* **滑动窗口内存管理 (Buffer Window Memory):** 传递给大模型的短期上下文维持在最近 8–10 条消息以节省 Token，而在底层数据库中则**持久保留 100% 完整历史记录**供复盘审查。

### 1.4. 企业级多租户数据隔离 (ISO/IEC 27001 & SOC 2)
* **租户隔离边界 (`company` 分区):** 所有数据库查询强制按公司租户过滤，防止越权拉取其他企业的财务对话记录。
* **零 PII 敏感信息脱敏:** 银行卡号、个人密码及密钥在持久化前均执行自动脱敏。

---

## 2. 数据库存储模型设计

对话数据通过两个专用的 Frappe DocType 持久化存储在 MariaDB 关系型数据库中：

### 2.1. `Lotus Chat Session` (会话主表)
* `name`: 主键唯一标识 (UUID 字符串，如 `session-9b1deb4d-...`)。
* `company`: 所属企业唯一标识（已建立索引）。
* `user`: 发起用户邮箱账户（已建立索引）。
* `title`: 根据首次问答由系统自动生成的会话摘要标题。
* `status`: 会话状态 (`ACTIVE` 活跃、`ARCHIVED` 归档、`EXPIRED` 过期)。
* `created_at` / `updated_at`: 时间戳字段。

### 2.2. `Lotus Chat Message` (消息与工具调用明细表)
* `session_id`: 外键关联父级 `Lotus Chat Session`。
* `role`: 消息角色 (`user`、`assistant`、`system`、`tool`)。
* `content`: 消息正文文本。
* `tool_name`: 调用的金融工具命令标识（如 `get_cash_forecast`）。
* `tool_input`: 工具入参 JSON 序列化字符串。
* `tool_output`: 工具执行产生的确定性财务结果 JSON。
* `ui_widget`: 前端 UI 卡片与图表渲染配置。
* `execution_time_ms`: 工具执行耗时（毫秒）。
* `trace_id`: 全链路追踪标识。

---

## 3. 高性能双层存储架构

```text
  [ 表现层 / 用户请求 ]
           │
           ▼
  [ CompositeSessionRepository ]
       │                  │
       ▼ (读取快路径)      ▼ (写入同步与落盘兜底)
  [ L1: Redis 缓存 ]   [ L2: MariaDB 关系数据库 ]
```

* **L1 (Redis 内存缓存):** 提供亚毫秒级低延迟读取，加速正在进行的连续多轮对话。
* **L2 (MariaDB 持久层):** 保证 ACID 事务持久性，满足长期合规归档与离线审计需求。

---

## 4. 自动化测试与验收标准

### 自动化测试套件 (`tests/test_chat_persistence_and_audit.py`)
1. `test_database_session_repository_save_and_retrieve`: 验证会话保存与读取的无损完整性。
2. `test_composite_repository_cache_hit_and_miss`: 验证 L1 缓存命中与失效时向 L2 的自动回退。
3. `test_chat_messages_preserve_tool_outputs_and_widgets`: 验证复杂 UI Widget 配置与工具事实数据的结构完整性。
4. `test_sandbox_operation_logging_jsonl`: 验证结构化 JSON Lines 导出格式与 Trace ID 贯穿。
5. `test_multi_tenant_company_isolation`: 断言跨租户访问会话将触发明确的安全拒绝异常。
