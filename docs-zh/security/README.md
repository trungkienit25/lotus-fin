# LOTUS FIN — 企业级安全架构与安全规范总览

> **所属系统：** Lotus Fin — 基于大模型驱动的中小企业财务 AI 助手  
> **竞赛赛题：** 2026 深圳国际金融科技大赛（WeBank FinTech University Challenge）Topic E · *安全与合规权重占比：30%*  
> **文档版本：** 3.0 · **发布日期：** 2026 年 10 月  
> **评估评级：** `ASSESSMENT READY / IMPLEMENTATION ALIGNED` (代码基线完全对齐)  

---

## 核心技术安全规范体系

Lotus Fin 的安全体系由 **3 篇深度专业技术报告** 构成，摒弃低效的代码堆砌，采用业界标准的工程蓝图范式：`痛点定义 (Problem)` $\to$ `解决方案 (Solution)` $\to$ `实现蓝图 (Implementation Blueprint)` $\to$ `验证证据 (Verification Evidence)`：

| 报告编号 | 规范名称 | 核心技术范围与防线 | 参考标准与量化基准 |
| :---: | :--- | :--- | :--- |
| **01** | [**基础设施与网络安全报告**](./01_INFRASTRUCTURE_AND_NETWORK_SECURITY_REPORT.md) | 云 VPC 子网拓扑、L4 有状态安全组防护、本地回环绑定 (127.0.0.1:8080)、内部 Docker 桥接隔离、Nginx 深度加固、DDoS 限流 (10 req/s)、容器非 root 降权运行、2GB Swap 内存防护与 30MB 容器日志轮转上限 | CIS Linux Benchmark, CIS Docker, NIST SP 800-53, 传输层端口监听审计 |
| **02** | [**应用安全与身份访问控制**](./02_APPLICATION_AND_IDENTITY_SECURITY_REPORT.md) | 常数时间防 CSRF 令牌比对、模块级细粒度 RBAC 权限矩阵 (F001–F007)、多租户零信任隔离 (`CompanyAccessError` 强制阻断)、基于 HMAC-SHA256 的不透明令牌编码器 (TTL 300秒, $\le 2048$ 字符) | OWASP ASVS v4.0.3 L2, OWASP API Top 10 (2023), 自动化单测 89/89 通过 |
| **03** | [**AI 安全与金融数据完整性**](./03_AI_SECURITY_AND_FINANCIAL_INTEGRITY_REPORT.md) | 大模型零数学计算不变量、有界 ReAct 智能体闭环 (最多 4 次迭代, 仅开放 6 大受控工具)、Level 4 人机协同双阶段提交机制、展现网关敏感数据脱敏、Prompt 注入防御与 PII 最小化 | OWASP Top 10 for LLM (2025), 自动化单测 26/26 通过 |

---

## 权威安全合规基准 (SSOT)

- [**代码基线对齐安全要求规范 (SSOT)**](./LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md): 面向安全专家与核心研发团队的权威合规规范，对标准强制关键字 (`MUST`、`SHOULD`)、租户数据隔离机制及实施审计状态进行规范化定级。

---

## 五大核心安全架构原则

1. **默认安全 (Secure by Default):** 系统的默认配置即为最高安全规格。所有网络端口、API 路由以及金融计算工具默认完全阻断，必须显式列入白名单方可调用。
2. **纵深防御 (Defense-in-Depth):** 构建五层联动同心圆纵深防线：云厂商底层 L4 安全组 $\to$ 宿主机 UFW 防火墙 $\to$ Host Nginx 接入网关 $\to$ 容器本地回环网络隔离 $\to$ 应用层 DAL 零信任校验门。
3. **最小特权 (Least Privilege):** 运行账号全部降权为普通用户 (`UID 1000` / `UID 999`)，生产环境中严禁数据库服务账号持有 DDL 结构篡改特权。
4. **零信任多租户隔离 (Zero Trust Multi-Tenancy):** 前端传入的企业公司标识 (`company`) 均被视作不可信数据；所有数据检索与业务流转必须强制通过服务端会话用户权限校验二次过滤。
5. **确定性金融计算不变量 (Deterministic Financial Invariant):** 严禁大语言模型计算或推演任何资产负债金额、财务比率或现金跑道天数。所有金融指标全部由经过密闭单元测试的 Python/SQL 原生高精度引擎执行计算。

