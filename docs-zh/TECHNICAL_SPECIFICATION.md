# Lotus Fin — 核心系统技术白皮书与架构设计规范

## 1. 系统全景概述 (System Overview)

**Lotus Fin** 是一套专为中小型企业 (SME) 打造的企业级 AI 财务 Copilot 与自主决策支持系统。平台通过在对话式生成式 AI 与确定性 ERP 复式记账总账系统之间构建确定性执行桥梁，从根本上杜绝了大语言模型在核心企业财务会计计算中的幻觉风险。

```
+-----------------------------------------------------------------------------------+
|                                  客户端展现层 (CLIENT LAYER)                         |
|                   React 19 SPA (Vite, TypeScript, TailwindCSS)                    |
+-----------------------------------------+-----------------------------------------+
                                          | HTTP / WebSocket (80 端口统一入口)
                                          v
+-----------------------------------------------------------------------------------+
|                             边缘网关层 (EDGE GATEWAY / 反向代理)                     |
|                       Nginx Gateway 容器 (监听 80 端口)                             |
|       / -> 静态 React SPA | /(api|desk|assets) -> Frappe 后端集群 (:8080)          |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                               应用与核心业务逻辑层                                  |
|   +------------------------------------+   +----------------------------------+   |
|   |        Frappe v16 / ERPNext        |   |         Lotus Fin 自定义模块     |   |
|   |  - 核心 DocType 实体与复式总账账簿 |   |  - 整洁架构分层内核 (<200行/文件)|   |
|   |  - 用户认证、RBAC 多租户权限管控   |   |  - ReAct 智能推理循环控制器       |   |
|   |  - 邮件服务集成 (Frappe SMTP)      |   |  - L5 敏感资金双人复核安全防线   |   |
|   +------------------------------------+   +-----------------+----------------+   |
+--------------------------------------------------------------|--------------------+
                                                               | 工具白名单调用
                                                               v
+-----------------------------------------------------------------------------------+
|                      确定性金融数学与分析引擎 (F001 - F007)                         |
|  - F001: 企业财务健康度全息诊断 (毛利率、现金比率、营运资本健康度分析)            |
|  - F002: 30天确定性现金流预测与资金跑道 (基于合同应收应付确定性到期日程)          |
|  - F003: 财务异动与风险预警探测 (应付账款堆叠挤兑、应收账款逾期激增)              |
|  - F004: 压力测试与敏感性情景模拟 (收入骤降波动冲击、账期拖延违约压力)            |
|  - F005: 商业信贷与流动资金贷款智能撮合 (基于真实 DSCR 与开票流水匹配方案)        |
|  - F006: 商业贷款等额分期偿还测算 (PMT 标准数学模型、基点基准利率加息压力测算)    |
|  - F007: 应收账款对账催收与邮件自动化发送 (自动生成 L3 函件、Frappe SMTP 投递)   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                               数据持久化与缓存集群                                |
|          MariaDB 11.8 (ERP 核心总账)    |    Redis 6.2 (内存缓存与 Celery 任务队列)|
+-----------------------------------------------------------------------------------+
```

---

## 2. 核心技术栈 (Technical Stack)

| 层级 | 核心技术选型 | 规格与关键版本 |
| :--- | :--- | :--- |
| **边缘网关** | Nginx Alpine | 反向代理、Gzip 静态加速、统一对外暴露 HTTP 80 端口 |
| **前端单页应用** | React, TypeScript, Vite | React 19, TailwindCSS, Lucide Icons, Headless UI |
| **后端底层框架** | Frappe Framework, Python | Python 3.12/3.13, Frappe v16.36.1, ERPNext v16.36.1 |
| **AI 编排引擎** | 确定性 ReAct 推理循环 | 白名单工具调度中心、专业财务 System Prompt、严格表现层拦截过滤网关 |
| **LLM 供应商支持** | 多 Key 负载轮询与平滑降级 | Google Gemini API、OpenAI API、NVIDIA NIM (`z-ai/glm-5.3-flash`) |
| **关系型数据库** | MariaDB | 11.8 (`utf8mb4_unicode_ci`), 严格 ACID 事务隔离 |
| **队列与分布式缓存** | Redis Alpine | Redis 6.2 (缓存集群与异步后台任务队列独立隔离) |
| **容器编排** | Docker & Docker Compose | 多阶段镜像构建、非 Root 运行隔离、健康检查守护 |

---

## 3. 确定性金融数学与业务分析引擎 (F001 — F007)

```
                       用户自然语言财务提问
                                │
                                ▼
               ┌───────────────────────────┐
               │    ReAct 智能调度循环     │
               │  - System Prompt 领域约束 │
               │  - 严格工具调用白名单校验 │
               └─────────────┬─────────────┘
                                │ 结构化参数工具调用
                                ▼
    ┌──────────────────────────────────────────────────┐
    │             确定性金融功能执行注册表             │
    ├───────────────────┬──────────────────────────────┤
    │ F001: 财务健康    │ 损益表、应收应付、流动性指标 │
    │ F002: 现金流预测  │ 30天确定性收支流动性曲线     │
    │ F003: 风险预警    │ 应付账款到期堆叠与坏账异动   │
    │ F004: 压力测试    │ 收入剧变与账期延误敏感性分析 │
    │ F005: 信贷撮合    │ 商业金融机构流动资金贷款匹配 │
    │ F006: 贷款测算    │ 标准 PMT 等额分期与加息测算  │
    │ F007: 催收对账    │ 账目核对函自动生成与 SMTP 发送│
    └───────────────────┴──────────────────────────────┘
                                │ 纯确定性计算结果 JSON
                                ▼
               ┌───────────────────────────┐
               │     表现层过滤网关        │
               │  - 剥离底层调试参数与Token│
               │  - 强制高管汇报级严谨用词 │
               └─────────────┬─────────────┘
                                │ 净化后的精准财务洞察
                                ▼
                        用户前端对话交互呈现
```

### 核心功能模块规格：
- **F001 — 企业财务全息健康诊断 (Financial Health Snapshot)：** 直接聚合查询 MariaDB 总账 GL Entry，秒级出具毛利率、净利率、经营活动现金净额及坏账率分析。
- **F002 — 30天确定性现金流预测与资金跑道 (30-Day Cash Forecast)：** 严格依据系统内已生效提交的 `Sales Invoice`（销售发票）与 `Purchase Invoice`（采购发票）中的确切付款账期表排期，绝不进行无依据的统计插值脑补。
- **F003 — 早期财务风险预警雷达 (Early Risk Signals)：** 针对近期到期账单进行聚类排查，精准定位 7~14 天内的集中支付兑付危机（`AP_DUE_CLUSTER`）及长期未收回逾期款项（`AR_OVERDUE_SPIKE`）。
- **F004 — 压力测试与敏感性情景模拟 (What-If Stress Testing)：** 模拟营收剧烈变动（-30% 至 +20%）及下游客户回款普遍延期（+15 至 +60 天）情境下的企业营运资金安全边际。
- **F005 — 中小企业信贷金融方案撮合 (SME Loan Matcher)：** 基于真实的偿债备付率 (DSCR)、资产负债比率及近 12 个月银行开票流水，自动匹配最符合条件的商业银行流动资金贷款与税贷产品。
- **F006 — 商业贷款等额分期偿还测算 (Loan Amortization Engine)：** 采用国际通用的标准年金公式（PMT），精确测算还款总额、月度还本付息明细，并模拟市场利率上浮 (+100 至 +300 个基点 bps) 带来的利息负担压力。
- **F007 — 逾期账款催收核对与自动化通知 (Debt Follow-up & Automated Dispatch)：** 智能检索逾期往来单位，快速生成三级阶梯式（温和提示、正式催告、法务预备）对账催收函件，并通过系统绑定的 `frappe.sendmail` SMTP 协议直接投递至客户财务负责人邮箱。

---

## 4. 敏感操作双人复核安全策略网关 (L5 Policy Gate)

为杜绝大语言模型或自动化工具误操作篡改核心财务总账、违规对外发起资金划转，系统建立了基于 L5 级别的强管控安全策略网关：

```
                    用户触发敏感财务操作意图
                               │
                               ▼
               ┌───────────────────────────────┐
               │   双人复核安全策略网关        │
               │   (Dual-Control Policy Gate)  │
               └───────────────┬───────────────┘
                               │ 评估操作安全等级
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [ 低/中度风险操作 ]             [ 高/极高风险操作 ]
       - 查询发票清单                  - 作废/红冲销售发票
       - 查看应收账期报表              - 发起银行资金划转
               │                               │
               │ 单用户确认执行                ├─ 作废发票: 必须通过双人电子复核
               ▼                               │  (财务主管 + 董事会审批流)
       执行调用并输出结果                      └─ 资金划转: 核心硬编码阻断 (仅允许网银人工操作)
```

| 操作标识 (Action ID) | 风险等级 | 策略执行逻辑 | 权限与复核要求 |
| :--- | :---: | :---: | :--- |
| `submit_sales_invoice` | 高 (High) | 条件性允许 | 需具备财务开票员或会计主管角色单人确认 |
| `cancel_sales_invoice` | 极高 (Critical) | 受限管控 | **强制双人复核机制：** 需财务总监与管理层独立复核授权 |
| `send_statement_email` | 中 (Medium) | 允许执行 | 严格校验接收方邮箱域名是否在往来单位合法备案名单内 |
| `request_disbursement` | 高 (High) | 条件性允许 | 应付账款专员发起申请 -> 财务经理审批预算指标 |
| `execute_wire_transfer` | 极高 (Critical) | **硬性阻断** | **严禁 AI 代理或自动化触发**，必须由人工在网银前置机操作 |
| `autonomous_reconciliation` | 极高 (Critical) | **硬性阻断** | **严禁黑盒自动抹账调账**，所有差额调整必须人工录入审计依据 |

---

## 5. 系统运维与生命周期管理规范

Lotus Fin 的日常运维、开发与部署任务均已被统一封装在 [`scripts/`](../scripts/README.md) 体系下，并由根目录调度脚本 [`run.sh`](../run.sh) 统一暴露：

```
scripts/
├── deploy/
│   └── run-deploy.sh                 # 云服务器一键化生产部署流水线
├── dev/
│   ├── run-dev.sh                    # Linux / macOS / WSL 本地极速开发启动器
│   └── run-dev.ps1                   # Windows 原生 PowerShell 极速开发启动器
├── packaging/
│   └── run-packaging.sh              # 生产级多阶段容器镜像打包工具
├── container/
│   └── run-container.sh              # 生产容器集群运维守护与状态管理
└── data/database/
    └── initial_db_seed.sql.gz        # 预置开箱即用全量演示企业账本快照
```

### 云端生产环境部署（单行指令无忧部署）
```bash
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin
chmod +x run.sh scripts/*/*.sh
./run.sh deploy
```
1. 自动对宿主机硬件进行环境审查；若内存紧张自动分配 **2GB Swap 交换分区**。
2. 自动安装或校验宿主机 Docker 与 Docker Compose 运行环境。
3. 编译打包前端工程至 `lotus-fin/gateway:latest` Nginx 反向代理镜像。
4. 启动监听在 **HTTP 80 端口** 的生产容器集群。
5. 全自动导入预置账本压缩包（`initial_db_seed.sql.gz`），执行 `bench migrate` 补丁更新，并根据环境注入 SMTP 发信服务。
6. 完成 HTTP 80 端到端连通性冒烟验收，输出公网访问地址。

### 本地极速开发模式
- **POSIX (Linux / macOS / WSL)：**
  ```bash
  ./run.sh dev
  ```
- **Windows (PowerShell 原生终端)：**
  ```powershell
  .\scripts\dev\run-dev.ps1
  ```
- 前端热重载地址：`http://localhost:5173` | ERPNext 后台总账地址：`http://localhost:8080`

### 生产镜像打包
```bash
./run.sh packaging
```

### 容器运维管理指令
```bash
./scripts/container/run-container.sh status    # 检查生产集群各容器健康状态与资源消耗
./scripts/container/run-container.sh logs      # 聚合输出容器集群实时控制台日志
./scripts/container/run-container.sh restart   # 平滑重启生产服务集群
./scripts/container/run-container.sh stop      # 优雅停止生产容器集群
```

---

## 6. 环境配置文件配置参考 (`.env`)

```ini
# AI 服务商与核心模型选型 ('gemini' | 'openai' | 'nvidia' | 'deepseek' | 'mock')
LOTUS_AI_PROVIDER=gemini
LOTUS_AI_MODEL=gemini-flash-latest

# 多 Key 自动轮询与限流平滑降级机制 (支持英文逗号隔开)
GEMINI_API_KEY=key_1, key_2, key_3
OPENAI_API_KEY="sk-key1", "sk-key2"
NVIDIA_API_KEY="nvapi-key1", "nvapi-key2"
NVIDIA_MODEL_NAME=z-ai/glm-5.3-flash

# 数据库与凭据
DB_HOST=db
DB_PORT=3306
MYSQL_ROOT_PASSWORD=admin
MARIADB_ROOT_PASSWORD=admin

# 自动化催收邮件 SMTP 发信凭据
LOTUS_SMTP_SERVER=smtp.gmail.com
LOTUS_SMTP_PORT=587
LOTUS_SMTP_EMAIL=notifications@yourdomain.com
LOTUS_SMTP_PASSWORD=your_app_password
LOTUS_SMTP_USE_TLS=1
```

---

## 7. 相关技术规范索引

- [系统运维与自动化脚本手册 (Operations Manual)](../scripts/README.md)
- [企业级安全架构统一设计规范 (Security SSOT)](security/README.md)
- [英文核心系统技术白皮书 (English Technical Specification)](../docs/TECHNICAL_SPECIFICATION.md)
