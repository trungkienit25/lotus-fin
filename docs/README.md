# Lotus Fin — Technical & Architecture Documentation Index

Welcome to the **Lotus Fin** technical documentation repository. This directory houses architectural specifications, feature implementation details, operational guidelines, and security single-source-of-truth (SSOT) documents.

For Chinese readers, a complete translation of all project guides is available in the [`docs/zh/`](zh/README.md) directory.

---

## 📚 Documentation Catalog

### 1. 🚀 Deployment & Operations
- [**Operations & Automation Scripts Guide**](../scripts/README.md): Step-by-step instructions for 1-click cloud deployment (`run-deploy.sh`), container lifecycle management, and local developer startup.
- [**Database Hydration & Seed Management**](../scripts/README.md#1-triển-khai-1-click-lên-cloud-server-run-deploysh): Procedures for exporting and restoring MariaDB General Ledger states across instances.

### 2. 🤖 Core Financial AI Copilot (F001 — F007)
- **F001 — Corporate Financial Health (AI001):** [Technical Specification](features/AI001/AI001_TECHNICAL_DOCUMENTATION.md) | [Security Self-Assessment](features/AI001/AI001_SECURITY_SELF_ASSESSMENT.md)
- **F002 — 30-Day Cash Flow Forecast (AI002):** [Technical Specification](features/AI002/AI002_TECHNICAL_DOCUMENTATION.md) | [Security Self-Assessment](features/AI002/AI002_SECURITY_SELF_ASSESSMENT.md)
- **F003 — Risk Signal & Debt Cluster Detection (AI003):** [Technical Specification](features/AI003/AI003_TECHNICAL_DOCUMENTATION.md) | [Security Self-Assessment](features/AI003/AI003_SECURITY_SELF_ASSESSMENT.md)
- **F004 / F005 — What-If Stress Testing Engine:** Deterministic simulation of cash runway under revenue variance and payment delay shocks.
- **F006 — Loan Amortization & Interest Rate Shock:** Equal monthly payment calculations and variable rate shock impact analysis.
- **F007 — Debt Reminder & Statement Reconciliation:** Interactive L3 template generation, real ERP invoice linkage, and automated SMTP dispatch.

### 3. 🛡️ Enterprise Security & Governance
- [**Security Single Source of Truth (SSOT)**](security/README.md): System architecture, STRIDE threat models, identity access control, and cryptographic standards.
- [**ISO 27001 & PCI-DSS Compliance Alignment**](security/12-compliance-iso27001-pcidss.md): Compliance frameworks and regulatory safeguards for corporate financial data.
- [**Dual-Control Policy Gate Architecture**](security/04-identity-access-control.md): Role-based multi-sign-off verification for ledger-impacting transactions.

---

## 🌐 Language Navigation
- **English Documentation:** [docs/README.md](README.md)
- **中文文档 (Chinese Translation):** [docs/zh/README.md](zh/README.md)
