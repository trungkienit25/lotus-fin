<div align="center">

# 🪷 Lotus Fin (莲华智财)

### **面向中小企业的企业级确定性 AI 智能财务 Copilot**

*打通对话式 AI 与可审计 ERP 总账底层数据。零财务幻觉 · 30天动态流动性建模 · L5 双重控制安全治理。*

<p align="center">
  <a href="#-为什么选择-lotus-fin"><img src="https://img.shields.io/badge/架构-整洁架构%20%7C%20ReAct%20Loop-3b82f6?style=for-the-badge&logo=fastapi" alt="整洁架构" /></a>
  <a href="#-快速开始"><img src="https://img.shields.io/badge/部署-一键云端部署%20(80端口)-10b981?style=for-the-badge&logo=docker" alt="Docker 容器化" /></a>
  <a href="#-l5-双重控制安全策略门禁"><img src="https://img.shields.io/badge/安全-L5%20双重控制门禁-ef4444?style=for-the-badge&logo=shield" alt="双人复核控制" /></a>
  <a href="#-多提供商韧性与自动故障降级"><img src="https://img.shields.io/badge/大模型-Gemini%20%7C%20OpenAI%20%7C%20NVIDIA-8b5cf6?style=for-the-badge&logo=openai" alt="支持多模型" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/协议-MIT-f59e0b?style=for-the-badge" alt="开源协议" /></a>
</p>

<p align="center">
  <a href="#-项目概述">项目概述</a> •
  <a href="#-为什么选择-lotus-fin">核心优势</a> •
  <a href="#-七大核心财务量化模块-f001--f007">核心模块</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-系统整体架构">系统架构</a> •
  <a href="#-文档与链接">文档导航</a> •
  <a href="#-贡献指南">贡献指南</a>
</p>

[English README](README.md) • **简体中文**

---

</div>

## 📌 项目概述

**Lotus Fin (莲华智财)** 是一套专为中小型企业（SME）量身打造的企业级开源 AI 智能财务助理与自主决策支持系统。

传统的生成式 AI 在面对严肃的财务会计任务时，极易编造看似合理却完全错误的财务数字（AI 幻觉），无法满足企业财务的严谨要求。**Lotus Fin 坚决推行“零幻觉（Zero-Hallucination）”技术准则**：系统通过严格受控的 **ReAct Agent 智能循环** 解析自然语言，并强制调用经过独立数学审计的 **确定性 Python 量化工具**，直接对接 Frappe / ERPNext 实时总账（General Ledger）。

无论是**未来 30 天每日现金流与缺口预测**、**债务短期集中到期预警**、**压力情景敏感度模拟（What-If）**，还是**一键生成并发送真实超期发票催收函**，Lotus Fin 都能为企业管理者与财务团队提供具备确定性数学依据的高级管理洞察。

```
       "如果未来收入下降 20%，且 Grant Plastics 延迟 30 天回款，我们的现金流还能撑多久？"
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                            Lotus Fin AI Copilot                           │
   │  ✓ 确定性 ReAct 工具触发: simulate_what_if_scenario                       │
   │  ✓ 读取 ERP 真实总账: 从 MariaDB 提取 Grant Plastics 实际应收与到期账目    │
   │  ✓ 纯数学模型推演: 测算现金流入减损、支出刚性与每日现金结余折线           │
   │  ✓ 自动化呈现门禁: 过滤系统底层 technical code，转化为商务规范汇报        │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
   "已为 Lotus-fin 执行量化压力模拟（What-If 模型）：
    • 应用假设：收入波动 -20%（预期收入：40,000,000 VND），客户回款延迟 +30 天
    • 预测净现金流：-117,854 VND | 预测期末现金结余：111,146 VND (状态：HEALTHY)
    💡 管理建议：企业在预测期内仍可保持正向流动性缓冲，无需启动紧急垫资。"
```

---

## ⚡ 为什么选择 Lotus Fin？

| 中小企业传统财务管理痛点 | Lotus Fin 的破局方案 |
| :--- | :--- |
| **通用大模型存在数字幻觉** | **零幻觉 ReAct 架构：** 严禁 LLM 自行编造或估算财务数据，所有关键数据均由确定性 Python 算子从凭证账目中直接运算。 |
| **表格孤立，账实脱节** | **原生对接 ERPNext 实时总账：** 深度集成销售发票、采购发票、会计凭证（GL Entry）以及付款排期（Payment Schedule）。 |
| **第三方大模型限流/报错导致业务中断** | **多 Key 轮换与自动故障降级：** 统一支持 Google Gemini、OpenAI 以及 NVIDIA NIM (`z-ai/glm-5.3-flash`)，遇到 429 限流或欠费自动无缝切换备用密钥。 |
| **AI 越权操作风险** | **L5 双重控制安全门禁：** 严格封死对外转账等高危动作，作废已入账发票必须经过财务总监与董事会双人复核。 |
| **云端部署繁琐、依赖复杂** | **一键 80 端口容器化部署：** 单一命令 `./run.sh deploy` 自动完成服务器 Swap 扩容、Docker 环境初始化、数据种子水化及 Nginx 网关配置。 |

---

## 🧭 七大核心财务量化模块 (F001 — F007)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            LOTUS FIN 智能财务套件                            │
├─────────────────────┬────────────────────────────────────────────────────────┤
│ F001 · 财务健康快报 │ 实时净营业收入、毛利率、现金储备余额、应收应付账期分析 │
│ F002 · 现金流预测   │ 基于真实发票付款排期的未来 30 天每日动态流动性建模     │
│ F003 · 风险信号监控 │ 统计学债务聚集预警（AP 挤兑风险与 AR 逾期账龄恶化预警）│
│ F004 · 压力测试引擎 │ What-If 情景推演（收入骤降与客户拖欠复合压力模拟）     │
│ F005 · 银行信贷撮合 │ 基于真实企业评级智能匹配商业银行流动资金信贷产品       │
│ F006 · 供款与利率测算│ 等额本息（PMT）精算与基点利率上行冲击测试（+100~300bps）│
│ F007 · 对账催收函电 │ 提取真实发票一键拟定专业催款函，直通 SMTP 网关自动发送 │
└─────────────────────┴────────────────────────────────────────────────────────┘
```

- **F001 — 企业财务健康快报 (AI001):** 实时从总账提炼净收入、毛利率、现金比率与应收应付总览。
- **F002 — 30 天动态现金流预测 (AI002):** 深度解析已过账发票的合同约定付款期（Payment Schedule），拒绝机械线性平摊。
- **F003 — 财务风险信号与债务聚集 (AI003):** 自动侦测供应商集中到期付款波峰（`AP_DUE_CLUSTER`）与客户超期欠款（`AR_OVERDUE_SPIKE`）。
- **F004 — 压力情景模拟测试 (AI004/AI005):** 支持管理者交互式调整营运参数，即时观察企业最低现金底线变化。
- **F005 — 银行信贷与融资产品匹配:** 依据偿债备付率（DSCR）与经营流水，为中小企业智能测算信贷通过概率并推荐产品。
- **F006 — 还款计划与利率冲击模拟:** 采用标准年金公式精准测算分期明细，支持自定义利率浮动基点冲击评估。
- **F007 — 账单对账催收函拟定与邮件发送:** 实时关联超期客户发票生成标准催款商函，支持前端交互修改，并通过内置 `frappe.sendmail` 发送。

---

## 🛡️ L5 双重控制安全策略门禁

为避免自动化脚本对企业核心财务账目造成不可逆破坏，Lotus Fin 构筑了严密的安全授权矩阵：

```
                          用户 / Copilot 操作指令
                                     │
                                     ▼
                   ┌───────────────────────────────────┐
                   │    L5 双重控制安全策略门禁        │
                   └─────────────────┬─────────────────┘
                                     │
            ┌────────────────────────┴────────────────────────┐
            ▼                                                 ▼
    [ 低风险/只读分析指令 ]                           [ 高风险总账变更操作 ]
 (查询发票、浏览报表、拟定邮件)                   (作废已入账发票、对外资金划转)
            │                                                 │
            ▼                                                 ▼
      单人即时确认                                    安全评估决策判定
  (直接执行并呈现结果)                       ┌────────────────┴────────────────┐
                                             ▼                                 ▼
                                      [ 作废已入账发票 ]               [ 发起大额电汇转账 ]
                                    强制触发双人审批门禁               系统硬性绝对阻断 (403)
                                (需财务总监 + 董事成员复核)         (严禁脚本代执行，仅限人工U-Key)
```

---

## 🚀 快速开始

### 🌟 云服务器一键全自动生产部署（推荐 · 80 端口）
在全新购置的 Linux 云服务器（Ubuntu 22.04 / 24.04、Debian、腾讯云/阿里云/华为云 VPS、AWS EC2）上：

```bash
# 1. 克隆代码仓库
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin

# 2. 赋予脚本执行权限
chmod +x run.sh scripts/*/*.sh

# 3. 运行一键全自动部署
./run.sh deploy
```

> **全自动部署流水线优势：**
> - **自动扩容 Swap：** 自动探测物理内存，内存受限时**自动分配并挂载 2GB Swapfile**，从根源消除 Frappe 容器内存溢出。
> - **Docker 自动就绪：** 全自动安装官方 Docker Engine 与 Compose 插件。
> - **无损数据水化（Hydration）：** 自动恢复预设 MariaDB 种子快照（`scripts/data/database/initial_db_seed.sql.gz`），同步表结构并激活 SMTP 网关。
> - **Nginx 网关聚合：** 自动在**标准 HTTP 80 端口**对外提供服务，前端单页应用与后端 API 路由一体化。

---

### 💻 本地开发者启动指南

#### Linux / macOS / WSL 环境：
```bash
./run.sh dev
```

#### Windows 原生 PowerShell 环境：
```powershell
.\scripts\dev\run-dev.ps1
```

- **前端应用面板：** `http://localhost:5173` (Vite 极速热更新)
- **Frappe 后台与 Desk：** `http://localhost:8080`
- **默认超级管理员：** `Administrator` / `admin`

---

## 🔄 多提供商韧性与自动故障降级

在 `.env` 配置文件中填入以逗号分隔的多组 API 密钥，保障全天候不间断服务：

```ini
# AI 提供商设定 ('gemini' | 'openai' | 'nvidia' | 'deepseek' | 'mock')
LOTUS_AI_PROVIDER=gemini
LOTUS_AI_MODEL=gemini-flash-latest

# Google Gemini (支持多 Key 自动故障切换)
GEMINI_API_KEY=AQ.Ab8RN6KcdBJg..., AQ.Ab8RN6J6ZVGE..., AQ.Ab8RN6J1q4sH...

# OpenAI / DeepSeek (多 Key 自动轮换)
OPENAI_API_KEY="sk-proj-key1...", "sk-proj-key2..."

# NVIDIA NIM 高并发加速端点
NVIDIA_API_KEY="nvapi-key1...", "nvapi-key2..."
NVIDIA_MODEL_NAME=z-ai/glm-5.3-flash

# 发件 SMTP 邮箱配置 (自动同步注入 ERP 系统)
LOTUS_SMTP_SERVER=smtp.gmail.com
LOTUS_SMTP_PORT=587
LOTUS_SMTP_EMAIL=your_email@gmail.com
LOTUS_SMTP_PASSWORD=your_app_password
LOTUS_SMTP_USE_TLS=1
```

---

## 🏛️ 系统整体架构

```
                                [ 最终用户 / 财务人员浏览器 ]
                                              │
                                              │ HTTP / WebSocket (80 端口)
                                              ▼
                    [ Nginx 生产反向代理网关 (静态托管与流量分发) ]
                      ├── /               ──> React 19 单页前端 (TailAdmin)
                      └── /(api|desk|app) ──> [ Frappe ERPNext 后端 (:8080) ]
                                                     │
                             ┌───────────────────────┼────────────────────────┐
                             ▼                       ▼                        ▼
                     [ ReAct 智能体循环 ]     [ MariaDB 11.8 ]         [ Redis 6.2 ]
                     (Prompt 组装与工具分发) (企业凭证与实时总账)     (队列、作业与缓存)
                             │
                             ▼
                 [ 确定性财务量化引擎 (F001 至 F007) ]
```

---

## 📁 仓库核心目录速览

```
lotus-fin/
├── docker/production/         # 生产环境 Nginx Dockerfile 与 docker-compose 定义
├── frontend/                  # React 19 单页前端工程 (TailAdmin 样式规范)
│   ├── src/components/        # 可复用财务图表及指标展示卡片
│   ├── src/constants/         # 财务字典与策略门禁规则定义
│   └── src/pages/copilot/     # AI Copilot 对话交互、L3 卡片及 L5 门禁视图
├── lotus_fin/                 # Frappe 核心应用工程
│   ├── api/                   # RESTful 接口层
│   ├── application/agent/     # ReAct Agent 执行循环、Prompt 引擎与呈现门禁
│   ├── domain/constants/      # 全局常量定义与业务术语表
│   ├── infrastructure/llm/    # 多 Key 自动轮换 LLM 适配器
│   └── modules/               # 核心财务量化业务模块 (F001 — F007)
├── scripts/                   # 模块化运维与自动化脚本库
│   ├── deploy/                # 一键生产部署流水线 (run-deploy.sh)
│   ├── dev/                   # 本地开发启动工具 (run-dev.sh / run-dev.ps1)
│   ├── packaging/             # 容器镜像打包 (run-packaging.sh)
│   ├── container/             # 容器运维管控 (run-container.sh)
│   ├── data/database/         # 数据库种子快照 (initial_db_seed.sql.gz)
│   └── README.md              # 运维脚本操作手册 (英文/越南文)
└── docs/                      # 深度技术规格与安全白皮书
    ├── TECHNICAL_SPECIFICATION.md  # 详细系统架构与底层接口技术规范
    └── zh/                    # 全套中文文档库 (文档与操作手册)
```

---

## 📚 文档与链接

- 📖 [系统底层技术规范与深度架构白皮书 (英文)](docs/TECHNICAL_SPECIFICATION.md)
- 🛠️ [运维与自动化部署脚本说明手册](scripts/README.md)
- 🇨🇳 [中文文档主页](docs/zh/README.md)
- 🛡️ [安全单一信任源设计规范 (SSOT)](docs/security/README.md)
- 📑 [Frappe Framework 官方技术文档](https://frappeframework.com/docs)

---

## 🤝 参与贡献

欢迎提交 Issue、功能优化建议以及 Pull Request！
1. Fork 本项目仓库。
2. 创建您的特性分支 (`git checkout -b feat/AmazingFeature`)。
3. 提交您的修改 (`git commit -m 'feat: Add some AmazingFeature'`)。
4. 推送至远程分支 (`git push origin feat/AmazingFeature`)。
5. 开启 Pull Request。

---

<div align="center">

**专为全球中小企业韧性成长倾心打造。**  
基于 [MIT 开源许可证](LICENSE) 发布。

</div>
