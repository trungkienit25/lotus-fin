# LOTUS FIN — TECHNICAL & ARCHITECTURE DOCUMENTATION INDEX

Welcome to the **Lotus Fin** technical documentation repository. This directory contains architectural blueprints, feature specifications, deployment guides, and security single-source-of-truth (SSOT) documents.

For Chinese readers, a complete translation of all project guides is available in the [`docs-zh/`](../docs-zh/README.md) directory.

---

## 📚 DOCUMENTATION CATALOG

### 1. 🏛️ Core Architecture & Specifications
- [**System Technical Specification**](TECHNICAL_SPECIFICATION.md): Comprehensive system architecture, ReAct flow, F001–F007 details, and L5 policy gates.
- [**Developer & AI Agent Onboarding Guide**](SETUP_AND_AI_ONBOARDING_GUIDE.md): Multi-tier architecture overview and automated setup workflows.
- [**Git Workflow & Branch Governance**](GIT_WORKFLOW.md): Branch topology, protection policies, and Conventional Commits.
- [**AI Module Architecture Proposal**](AI_MODULE_ARCHITECTURE_PROPOSAL.md): Modular design for core AI components.
- [**API Design Conventions**](API_DESIGN_CONVENTIONS.md): Response envelopes, status codes, and DTO contracts.
- [**ADR-001: Clean Architecture Standards**](adr/001-clean-architecture-core-first-adr.md): <200 lines/file limit and strict ban on ad-hoc scripts.
- [**Architecture Deep-Dive Suite**](architecture/README.md): Detailed layer breakdown, directory implementation, and OOP design patterns.

### 2. 🎨 Frontend Engineering
- [**Frontend Architecture & Design System Suite**](frontend/README.md): Dynamic Runtime Metadata Engine, TailAdmin design system, API caching with SWR, and brand guidelines.
- [**Frontend Documentation Alias**](fe/README.md): Direct navigation link to the frontend suite.

### 3. 🚀 Cloud Deployment & Operations
- [**Cloud Deployment Guide (Linux Cloud Server)**](deployment/README.md): 7-step deployment guide (Server survey, OS hardening, 9 Docker containers, Host Nginx reverse proxy, React build, test matrix, and GitHub Actions CI/CD).
- [**End-to-End Cloud Deployment Plan**](deployment/END_TO_END_CLOUD_DEPLOYMENT_PLAN.md): Holistic enterprise blueprint covering VPC subnets, L4 security groups, host Nginx proxy, and container topologies.

### 4. 🤖 Financial AI Features Suite (F001 – F007)
- [**Features Suite Overview**](features/README.md): Complete index of all 7 financial engines.
- **F001 — Financial Health Analyst (AI001):** [Overview & Architecture](features/AI001/README.md)
- **F002 — 30-Day Cash Flow Forecast (AI002):** [Overview & Architecture](features/AI002/README.md)
- **F003 — Risk Signal & Debt Cluster Detection (AI003):** [Overview & Architecture](features/AI003/README.md)
- **F004 — What-If Stress Testing Simulator (AI004):** [Overview & Architecture](features/AI004/README.md)
- **F005 — SME Financing Product Matcher (AI005):** [Overview & Architecture](features/AI005/README.md)
- **F006 — Loan Amortization & Interest Rate Shock (AI006):** [Overview & Architecture](features/AI006/README.md)
- **F007 — Receivables Recovery & Payment Reminders (AI007):** [Overview & Architecture](features/AI007/README.md)

### 5. 🛡️ Enterprise Security & Compliance
- [**Security Single Source of Truth (SSOT)**](security/README.md): Overview and navigation of enterprise security controls.
- [**01. Infrastructure & Network Security Report**](security/01_INFRASTRUCTURE_AND_NETWORK_SECURITY_REPORT.md): Cloud VPC subnet diagram, L4 Security Group, Nginx reverse proxy hardening, and container isolation.
- [**02. Application & Identity Security Report**](security/02_APPLICATION_AND_IDENTITY_SECURITY_REPORT.md): Constant-time CSRF tokens, module-level RBAC matrix, and multi-tenant zero-trust isolation.
- [**03. AI Security & Financial Integrity Report**](security/03_AI_SECURITY_AND_FINANCIAL_INTEGRITY_REPORT.md): Zero-AI calculation invariant, bounded ReAct loop, Level 4 two-phase commit, and OWASP Top 10 for LLM compliance.
- [**Codebase Aligned Security Requirements**](security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md): Normative keywords and implementation audit requirements.

---

## 🌐 Language Navigation
- **English Documentation:** [docs/README.md](README.md)
- **中文文档 (Chinese Translation):** [docs-zh/README.md](../docs-zh/README.md)
