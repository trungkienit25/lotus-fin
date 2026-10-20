# LOTUS FIN — 技术与架构文档索引 (中文版)

欢迎查阅 **Lotus Fin** 技术架构文档库。本目录包含系统的架构设计蓝图、功能规格、部署指南以及安全唯一事实来源 (SSOT) 规范。

英文原版技术文档请参阅 [`docs/`](../docs/README.md)。

---

## 目录索引 (Documentation Catalog)

### 1. 核心架构与技术规范 (Core Architecture & Specifications)
- [**系统总体技术规范**](TECHNICAL_SPECIFICATION.md): 涵盖整体系统架构、ReAct 推理执行流、F001–F007 算法细节以及 L5 双控安全策略门。
- [**开发者与 AI Agent 快速上手指南**](SETUP_AND_AI_ONBOARDING_GUIDE.md): 多层架构概述、自动化容器初始化与本地开发工作流。
- [**Git 协作流与分支治理规范**](GIT_WORKFLOW.md): 分支拓扑管理规范、分支保护规则与 Conventional Commits 提交标准。
- [**AI 模块解耦与架构设计提案**](AI_MODULE_ARCHITECTURE_PROPOSAL.md): 核心 AI 组件模块化设计与端口适配器模式。
- [**RESTful API 设计规范**](API_DESIGN_CONVENTIONS.md): 统一响应信封、HTTP 状态码及 Pydantic DTO 验证契约。
- [**ADR-001: 整洁架构标准与单文件 200 行上限**](adr/001-clean-architecture-core-first-adr.md): 严格限制单文件不超过 200 行，杜绝一切临时脚本。
- [**架构深度技术套件**](architecture/README.md): 依赖倒置原则、目录实现职责分配以及面向对象设计模式最佳实践。

### 2. 前端工程与组件体系 (Frontend Engineering)
- [**现代化前端架构与设计系统**](frontend/README.md): 动态运行时元数据引擎 (Dynamic Runtime Engine)、TailAdmin 设计系统、基于 SWR 的内存缓存策略及品牌视觉指南。
- [**前端文档快速导航别名**](fe/README.md): 同步指向前端技术文档的统一入口。

### 3. 云服务器部署与持续运维 (Cloud Deployment & Operations)
- [**端到端 Linux 云服务器部署方案**](deployment/README.md): 7 步标准化部署指南（环境勘测、操作系统安全加固、9 个 Docker 容器集群编排、Host Nginx 反向代理配置、React 生产打包、全场景验证矩阵及 GitHub Actions CI/CD 流水线）。
- [**端到端云部署综合规划方案**](deployment/END_TO_END_CLOUD_DEPLOYMENT_PLAN.md): 包含云 VPC 子网拓扑、L4 有状态安全组及微服务集群架构的生产设计蓝图。

### 4. 核心金融 AI 引擎矩阵 (F001 – F007)
- [**金融 AI 引擎套件总览**](features/README.md): 覆盖 SME 财务管理的 7 大核心引擎全景索引。
- **F001 — 企业财务健康分析师 (AI001):** [功能总览与核心规范](features/AI001/README.md)
- **F002 — 30 天每日现金流预测 (AI002):** [功能总览与核心规范](features/AI002/README.md)
- **F003 — 财务风险信号与账期聚集预警 (AI003):** [功能总览与核心规范](features/AI003/README.md)
- **F004 — 多变量 What-If 财务压力模拟 (AI004):** [功能总览与核心规范](features/AI004/README.md)
- **F005 — 中小企业信贷产品撮合引擎 (AI005):** [功能总览与核心规范](features/AI005/README.md)
- **F006 — 贷款分期与利率冲击模拟 (AI006):** [功能总览与核心规范](features/AI006/README.md)
- **F007 — 催收回款协助与对账凭据派发 (AI007):** [功能总览与核心规范](features/AI007/README.md)

### 5. 企业级安全与合规治理 (Enterprise Security & Compliance)
- [**安全唯一事实来源 (SSOT) 概述**](security/README.md): 覆盖基础设施、应用身份及大模型金融安全的三大技术报告与导航。
- [**01. 基础设施与网络安全报告**](security/01_INFRASTRUCTURE_AND_NETWORK_SECURITY_REPORT.md): 云 VPC 子网拓扑架构、L4 有状态安全组防护、本地回环绑定 (127.0.0.1:8080) 与 Nginx 深度加固。
- [**02. 应用安全与身份访问控制报告**](security/02_APPLICATION_AND_IDENTITY_SECURITY_REPORT.md): 常数时间防 CSRF 令牌、模块级 RBAC 矩阵、多租户零信任隔离 (`CompanyAccessError`) 及基于 HMAC-SHA256 的不透明令牌编解码器。
- [**03. AI 安全与金融数据完整性报告**](security/03_AI_SECURITY_AND_FINANCIAL_INTEGRITY_REPORT.md): 大模型零数学计算不变量、有界 ReAct 推理闭环 (最多 4 次迭代)、Level 4 人机协同双阶段提交、展现网关净化器以及 OWASP GenAI Top 10 对齐矩阵。
- [**代码基线对齐安全规范**](security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md): 面向工程师与 AI 编码代理的标准合规基线。

---

## 🌐 语言版本导航
- **English Documentation:** [docs/README.md](../docs/README.md)
- **中文文档 (Chinese Translation):** [docs-zh/README.md](README.md)

---

## 🌐 语言版本导航
- **English Documentation:** [docs/README.md](../docs/README.md)
- **中文文档 (Chinese Translation):** [docs-zh/README.md](README.md)

