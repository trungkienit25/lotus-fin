# Lotus Fin — 中小企业企业级 AI 智能财务 Copilot

[![Status](https://img.shields.io/badge/Status-%E7%94%9F%E4%BA%A7%E5%B0%B1%E7%BB%AA-success)]()
[![Architecture](https://img.shields.io/badge/%E6%9E%B6%E6%9E%84-%E6%B8%85%E6%B5%81%E6%9E%B6%E6%9E%84%20%7C%20ReAct%20Agent-blue)]()
[![Framework](https://img.shields.io/badge/%E5%BA%95%E5%B1%82%E6%A1%86%E6%9E%84-Frappe%20v16%20%7C%20ERPNext-orange)]()
[![Frontend](https://img.shields.io/badge/%E5%89%8D%E7%AB%AF-React%2019%20%7C%20Vite%20%7C%20TailAdmin-61DAFB)]()
[![Gateway](https://img.shields.io/badge/%E7%BD%91%E5%85%B3-Nginx%20%E7%AB%AF%E5%8F%A3%2080-009639)]()

> **Lotus Fin** 是一套专为中小型企业（SME）量身打造的企业级 AI 财务助理与自主决策支持系统。系统基于确定性、零幻觉的 ReAct Agent 智能循环、双重控制安全策略门禁（Dual-Control Policy Gates）以及与 Frappe/ERPNext 实时总账的无缝集成，全面赋能首席财务官（CFO）和企业管理者实现现金流预测、财务风险预警与营运资金优化。

---

## 🌟 核心业务功能与智能化模块

### 1. 🤖 确定性量化 AI Copilot 与工具调用
- **零幻觉执行机制（Zero-Hallucination）：** 所有财务分析指标与结论均严格基于 ERP 总账实际凭证与经过审计的量化模块计算，彻底杜绝大模型在财务领域的数字幻觉。
- **自动化呈现门禁（Presentation Gate）：** 自动清洗底层技术标签（如 `STRICT_BASELINE_V1`、布尔值参数），统一转换为符合企业高级管理规范的自然商务语言。
- **多模型高可用与密钥轮换机制：** 针对 **Google Gemini**、**OpenAI** 以及 **NVIDIA NIM**（`z-ai/glm-5.3-flash`），内置多 API Key 自动轮换与故障自动降级机制（遇 429 配额限制或 5xx 错误时无缝切换到备用密钥）。

### 2. 📊 核心财务分析模块 (F001 — F007)
- **F001 — 企业财务健康快报（Corporate Financial Health）：** 实时统计并展现净营业收入、毛利率、现金储备余额、应收账款（AR）与应付账款（AP）余额。
- **F002 — 30 天动态现金流预测（30-Day Cash Forecast）：** 基于已确认的 ERP 购销发票付款排期（Payment Schedule），对未来 30 天每日结存现金曲率与缺口风险进行量化建模。
- **F003 — 财务风险信号与债务聚集监控（Risk Signals）：** 自动侦测应付账款短期集中到期（`AP_DUE_CLUSTER`）与应收账款逾期激增（`AR_OVERDUE_SPIKE`），提前预警流动性挤兑。
- **F004 — 压力情景模拟测试（What-If Stress Testing）：** 支持设定收入波动比例与客户回款延迟天数，快速推演不同压力情景下企业现金流承受底线。
- **F005 — 银行信贷与融资产品精准匹配（Financing Matching）：** 结合企业真实财务评级，智能匹配最契合的商业银行授信额度与短期流动资金贷款产品。
- **F006 — 还款计划测算与利率冲击模拟（Amortization & Rate Shock）：** 采用等额本息（PMT）精算月度供款金额，并可加载 +100 至 +300 个基点的利率上行压力测试。
- **F007 — 账单催收函拟定与邮件通知（Debt Reminder）：** 一键自动关联超期发票生成标准化商函，支持在线编辑、一键复制，并通过内置 SMTP 网关（`frappe.sendmail`）发送通知邮件。

### 3. 🛡️ 双重授权安全策略门禁 (L5 Policy Gate)
- 涉及改变系统总账数据的关键行为（如作废已提交销售发票、发起大额银行转账申请），必须触发安全审核门禁，需财务总监与董事会双重授权后方可执行。

---

## 🚀 极速部署与运行指南

Lotus Fin 在 [`scripts/`](../scripts/README.md) 目录下提供了模块化运维脚本，并通过根目录下的统一分发脚本 [`run.sh`](../run.sh) 进行统一调用。

### 方案 A：云服务器一键生产部署（默认暴露 HTTP 80 端口）
在全新安装的 Linux 云服务器（Ubuntu 22.04 / 24.04、Debian、腾讯云/阿里云/华为云 VPS、AWS EC2）上：

```bash
# 1. 克隆项目仓库
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin

# 2. 赋予脚本执行权限
chmod +x run.sh scripts/*/*.sh

# 3. 运行一键全自动部署
./run.sh deploy
```

#### `run.sh deploy` 执行的 7 步全自动化流水线：
1. **系统资源诊断：** 检测操作系统、物理内存，内存不足时**自动建立 2GB Swap 交换分区**，防止 Frappe 容器内存溢出。
2. **环境自动化就绪：** 自动检测并安装官方最新 Docker Engine 及 Docker Compose 插件。
3. **环境参数校验：** 检查并初始化生产环境变量配置文件 `docker/production/.env.production`。
4. **Nginx 网关打包：** 多阶段自动构建前端单页应用并组装 `lotus-fin/gateway:latest` 容器镜像。
5. **容器集群拉起：** 启动 8 个生产容器集群，统一通过 Nginx 网关对外暴露 **80 端口**。
6. **数据库自动水化（Hydration）：** 自动导入 [`scripts/data/database/initial_db_seed.sql.gz`](../scripts/data/database/initial_db_seed.sql.gz) 数据库快照、执行 `bench migrate` 同步结构，并自动配置好 SMTP 邮件通知账号。
7. **可用性就绪核验：** 执行 HTTP 健康探测，返回服务器公网 IP 与登录入口。

### 方案 B：本地开发环境快速启动
- **在 Linux / macOS / WSL 环境下：**
  ```bash
  ./run.sh dev
  ```
- **在 Windows PowerShell 环境下：**
  ```powershell
  .\scripts\dev\run-dev.ps1
  ```
- **访问入口：**
  - 前端开发界面：`http://localhost:5173`
  - Frappe 后台与 Desk：`http://localhost:8080`
  - 默认管理员账号：`Administrator` / `admin`

---

## 🏗️ 整体系统架构图

```
[ 客户端浏览器 / 用户终端 ]
        │ (标准 HTTP 80 端口)
        ▼
[ Nginx 生产反向代理网关 (SPA 静态托管 + API 分发) ]
   ├── /               ──> React 19 + Vite + TailwindCSS 前端面板
   └── /(api|desk|app) ──> [ Frappe ERPNext 后端微服务网关 (端口 8080) ]
                                  │
          ┌───────────────────────┼────────────────────────┐
          ▼                       ▼                        ▼
  [ ReAct 智能体引擎 ]     [ MariaDB 11.8 关系型数据库 ]  [ Redis 缓存与队列 ]
  (Prompt Engine / 门禁)   (存储凭证、发票与系统总账)      (高频状态与后台作业)
          │
          ▼
  [ 确定性财务工具集 ]
  (F001 至 F007 模块)
```

---

## 📁 项目目录结构树

```
lotus-fin/
├── docker/                    # Docker 容器编排配置目录
│   └── production/            # 生产级 Nginx Dockerfile 及 compose.prod.yml
├── frontend/                  # React 19 TailAdmin 单页前端工程
│   ├── src/components/        # 财务可视化图表与 UI 组件
│   ├── src/constants/         # 财务字典与策略门禁规则定义
│   └── src/pages/copilot/     # AI Copilot 对话交互、L3 卡片与 L5 审核视图
├── lotus_fin/                 # Frappe 核心应用模块
│   ├── api/                   # RESTful 数据接口
│   ├── application/agent/     # ReAct Agent 循环、Prompt 引擎与呈现门禁
│   ├── domain/constants/      # 全局常量定义与业务术语表
│   ├── infrastructure/llm/    # 多 Key 自动轮换 LLM 适配器 (Gemini/OpenAI/NVIDIA)
│   └── modules/               # 核心财务分析业务逻辑模块 (F001 - F007)
├── scripts/                   # 自动化运维与部署脚本库
│   ├── deploy/                # 一键生产部署脚本 (run-deploy.sh)
│   ├── dev/                   # 本地开发启动脚本 (run-dev.sh / run-dev.ps1)
│   ├── packaging/             # 容器镜像打包脚本 (run-packaging.sh)
│   ├── container/             # 容器生命周期管理脚本 (run-container.sh)
│   ├── data/database/         # 数据库初始化种子快照 (initial_db_seed.sql.gz)
│   └── README.md              # 运维脚本操作手册 (英文)
├── docs/                      # 英文技术文档总库
└── docs-zh/                   # 完整中文技术文档总库
    ├── README.md              # 中文技术文档入口主页
    ├── TECHNICAL_SPECIFICATION.md # 系统架构白皮书与技术规格
    ├── SETUP_AND_AI_ONBOARDING_GUIDE.md # 开发者与 AI 智能体上手指南
    ├── GIT_WORKFLOW.md        # 分支流转与提交规范
    ├── AI_MODULE_ARCHITECTURE_PROPOSAL.md # AI 模块架构设计提案
    ├── API_DESIGN_CONVENTIONS.md # API 设计与 DTO 规范
    ├── adr/                   # 架构决策记录 (ADR)
    ├── architecture/          # 架构分层与设计模式解析
    ├── scripts.md             # 运维脚本中文手册
    └── security.md            # 企业级安全与合规设计说明
```

---

## 📖 相关文档链接
- [系统架构白皮书与技术规格](TECHNICAL_SPECIFICATION.md)
- [开发者与 AI 智能体上手指南](SETUP_AND_AI_ONBOARDING_GUIDE.md)
- [Git 分支与约定式提交规范](GIT_WORKFLOW.md)
- [运维与部署自动化脚本中文手册](scripts.md)
- [安全合规与权限架构设计说明 (中文版)](security.md)
- [English Documentation Suite](../docs/README.md)

