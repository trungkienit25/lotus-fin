# Lotus Fin — Enterprise AI Financial Copilot for SMEs

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![Stack](https://img.shields.io/badge/Architecture-Clean%20Architecture%20%7C%20ReAct%20Agent-blue)]()
[![Framework](https://img.shields.io/badge/Framework-Frappe%20v16%20%7C%20ERPNext-orange)]()
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%7C%20Vite%20%7C%20TailAdmin-61DAFB)]()
[![Gateway](https://img.shields.io/badge/Gateway-Nginx%20Port%2080-009639)]()

> **Lotus Fin** is an enterprise-grade AI Financial Copilot and Autonomous Decision Support System built for Small and Medium Enterprises (SMEs). Powered by a deterministic, zero-hallucination ReAct Agent loop, dual-control policy security gates, and real-time General Ledger integration with Frappe/ERPNext, Lotus Fin empowers CFOs and business owners to manage cash flow, mitigate risk, and optimize working capital.

---

## 🌟 Key Capabilities

### 1. 🤖 Quantitative AI Copilot & Deterministic Tool Calling
- **Zero-Hallucination Execution:** Financial answers are strictly derived from live ledger entries and audited calculation modules rather than raw generative hallucinations.
- **Automated Presentation Gate:** Natural executive English formatting that enforces corporate standards and strips internal technical keys (`STRICT_BASELINE_V1`, raw boolean flags).
- **Multi-LLM Resilience:** High-availability adapters with automatic multi-key rotation and failure fallback for **Google Gemini**, **OpenAI**, and **NVIDIA NIM** (`z-ai/glm-5.3-flash`).

### 2. 📊 Core Financial Intelligence Modules
- **F001 — Corporate Financial Health (AI001):** Real-time monitoring of Net Revenue, Gross Margin, Liquidity Ratio, Debtors/Creditors Aging, and Balance Sheet health.
- **F002 — 30-Day Predictive Cash Flow & Runway (AI002):** Continuous 30-day modeled cash trajectory utilizing verified ERP contractual Payment Schedules (`Sales Invoice` & `Purchase Invoice`).
- **F003 — Early Risk Signals & Debt Concentration (AI003):** Statistical cluster detection (`AP_DUE_CLUSTER`, `AR_OVERDUE_SPIKE`) for accounts payable bottlenecks and receivables aging deterioration.
- **F004 — What-If Stress Testing Engine (AI004/AI005):** Monte Carlo & deterministic sensitivity simulations modeling revenue drops, supply chain price hikes, and customer payment delays.
- **F005 — Commercial Bank Loan & Facility Matching:** Rule-based matching engine pairing verified corporate financial profiles against bank lending facilities.
- **F006 — Loan Amortization & Interest Rate Shock:** Equal monthly payment calculations (PMT) with variable basis point interest rate shock stress tests (+100 to +300 bps).
- **F007 — Executive Debt Reminder & Statement Reconciliation:** Interactive L3 draft generator pulling real customer invoice records with direct editing, one-click copying, and automatic dispatch via default SMTP Gateway (`frappe.sendmail`).

### 3. 🛡️ Dual-Control Policy Safety Gate (L5)
- Sensitive ledger-modifying operations (such as sales invoice cancellation or wire transfer requests) are evaluated through a Dual-Control Safety Gate requiring multiple independent sign-offs before execution.

---

## 🚀 Quick Start & Deployment Guide

Lotus Fin provides modular, automated lifecycle scripts under [`scripts/`](scripts/README.md) and a top-level dispatcher [`run.sh`](run.sh).

### Option A: 1-Click Production Cloud Deployment (Port 80)
To deploy Lotus Fin on a fresh Linux Cloud Server (Ubuntu 22.04 / 24.04, Debian, AWS EC2, DigitalOcean):
```bash
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin

# Grant execution permissions
chmod +x run.sh scripts/*/*.sh

# Run 1-click automated deployment
./run.sh deploy
```
**What `run.sh deploy` automates:**
1. **Resource Audit:** Detects OS, RAM, and automatically allocates a **2GB Swapfile** on memory-constrained servers to prevent OOM errors.
2. **Environment & Docker:** Installs official Docker Engine & Docker Compose plugin if missing.
3. **Gateway Packaging:** Builds the multi-stage `lotus-fin/gateway:latest` container (React SPA + Nginx reverse proxy).
4. **Stack Launch:** Boots the 8-container production cluster mapped to standard HTTP **Port 80**.
5. **Database Hydration:** Automatically imports the bundled ledger snapshot [`scripts/data/database/initial_db_seed.sql.gz`](scripts/data/database/initial_db_seed.sql.gz) into MariaDB, applies migrations (`bench migrate`), and provisions the default SMTP notifications gateway.
6. **Readiness Probe:** Runs an HTTP status check and returns the public server IP.

### Option B: Local Developer Onboarding
For developers developing locally with hot reload:
- **On Linux / macOS / WSL:**
  ```bash
  ./run.sh dev
  ```
- **On Windows (PowerShell):**
  ```powershell
  .\scripts\dev\run-dev.ps1
  ```
- **Endpoints:**
  - Frontend SPA: `http://localhost:5173`
  - Frappe Desk & API: `http://localhost:8080`
  - Default Credentials: `Administrator` / `admin`

---

## 🏗️ Architecture & Stack

```
[ Client Browser ]
        │ (Port 80 HTTP)
        ▼
[ Nginx Production Gateway (SPA Static Hosting & Proxy) ]
   ├── /               ──> React 19 + Vite + TailwindCSS (TailAdmin)
   └── /(api|desk|app) ──> [ Frappe ERPNext Backend Gateway (Port 8080) ]
                                  │
          ┌───────────────────────┼────────────────────────┐
          ▼                       ▼                        ▼
  [ ReAct Agent Engine ]   [ MariaDB 11.8 ]       [ Redis Cache & Queue ]
          │                (General Ledger &      (Job Queues & Session)
          ▼                 DocType Store)
  [ Deterministic Tools ]
  (F001 - F007 Modules)
```

---

## 📁 Repository Structure

```
lotus-fin/
├── docker/                    # Container definitions and production compose
│   └── production/            # Nginx gateway Dockerfile and compose.prod.yml
├── frontend/                  # React 19 TailAdmin Single Page Application
│   ├── src/components/        # Reusable financial widgets & charts
│   ├── src/constants/         # Policy catalogs and executive business dictionaries
│   └── src/pages/copilot/     # AI Copilot interface, L3 cards & L5 safety gate views
├── lotus_fin/                 # Frappe Core Application Module
│   ├── api/                   # RESTful endpoints for Copilot and financial data
│   ├── application/agent/     # ReAct Agent loop, Prompt Engine, Presentation Gate
│   ├── domain/constants/      # Centralized executive messages and verdicts
│   ├── infrastructure/llm/    # Multi-key rotating adapters (Gemini, OpenAI, NVIDIA)
│   └── modules/               # Core analytical modules (F001 to F007)
├── scripts/                   # Modular operational scripts
│   ├── deploy/                # 1-Click production cloud deployer (run-deploy.sh)
│   ├── dev/                   # Local developer onboarding (run-dev.sh / run-dev.ps1)
│   ├── packaging/             # Container packaging script (run-packaging.sh)
│   ├── container/             # Container management lifecycle (run-container.sh)
│   ├── data/database/         # Exported database seed (initial_db_seed.sql.gz)
│   └── README.md              # Detailed scripts operations manual
└── docs/                      # Technical specifications, security SSOT, and guides
    └── zh/                    # Complete documentation translated into Chinese (中文文档)
```

---

## 🌐 Multi-Language Documentation
- [English Documentation](README.md) (Current)
- [中文文档 (Chinese Documentation)](docs/zh/README.md)
- [Scripts & Operations Guide](scripts/README.md)
- [Security Architecture SSOT](docs/security/README.md)
