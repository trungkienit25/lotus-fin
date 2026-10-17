<div align="center">

# 🪷 Lotus Fin

### **Enterprise-Grade Deterministic AI Financial Copilot for SMEs**

*Bridging Conversational AI with Auditable ERP General Ledgers. Zero Hallucinations. Continuous Liquidity Modeling. Dual-Control Governance.*

<p align="center">
  <a href="#-why-lotus-fin"><img src="https://img.shields.io/badge/Architecture-Clean%20%7C%20ReAct%20Loop-3b82f6?style=for-the-badge&logo=fastapi" alt="Clean Architecture" /></a>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/Deployment-1--Click%20Cloud%20(Port%2080)-10b981?style=for-the-badge&logo=docker" alt="Docker Ready" /></a>
  <a href="#-dual-control-policy-safety-gate-l5"><img src="https://img.shields.io/badge/Security-Dual--Control%20Gate%20(L5)-ef4444?style=for-the-badge&logo=shield" alt="Dual Control" /></a>
  <a href="#-multi-provider-resilience--fallback"><img src="https://img.shields.io/badge/LLM-Gemini%20%7C%20OpenAI%20%7C%20NVIDIA-8b5cf6?style=for-the-badge&logo=openai" alt="LLM Providers" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge" alt="License" /></a>
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-why-lotus-fin">Why Lotus Fin</a> •
  <a href="#-core-modules-f001--f007">Core Modules</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-documentation--links">Documentation</a> •
  <a href="#-contributing">Contributing</a>
</p>

**English** • [简体中文 (Chinese)](README-zh.md)

---

</div>

## 📌 Overview

**Lotus Fin** is an open-source, enterprise-grade AI Financial Copilot engineered specifically for Small and Medium Enterprises (SMEs). 

While conventional generative AI tools invent plausible-sounding numbers and fail in mission-critical accounting, **Lotus Fin enforces a zero-hallucination paradigm**: natural language queries are parsed through an audited **ReAct Agent Loop**, which triggers **deterministic financial execution tools** directly connected to live General Ledger databases (ERPNext/Frappe Framework).

Whether you need a **real-time 30-day cash runway projection**, early warnings on **debt clustering**, dynamic **stress testing**, or **automated debt follow-up notices sent via SMTP**, Lotus Fin delivers mathematical certainty paired with modern executive intelligence.

```
       "How is our cash runway if sales drop 20% and Grant Plastics delays payment 30 days?"
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                            Lotus Fin AI Copilot                           │
   │  ✓ Deterministic ReAct Tool Call: simulate_what_if_scenario               │
   │  ✓ Audited GL Ingestion: Pulls verified AR/AP milestones from MariaDB     │
   │  ✓ Math Engine: Models cash deficit curve with exact variance             │
   │  ✓ Presentation Gate: Strips raw internal keys & formats executive report │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         │
                                         ▼
   "Executed What-If Stress Test for Lotus-fin:
    • Revenue Shock Applied: -20% (Projected Revenue: 40,000,000 VND)
    • Debtor Delay: +30 Days
    • Ending Cash Balance: 111,146 VND (HEALTHY)
    💡 Recommendation: Working capital buffer remains positive for 30 days."
```

---

## ⚡ Why Lotus Fin?

| Challenge in Traditional SME Accounting | How Lotus Fin Solves It |
| :--- | :--- |
| **Generative AI Hallucinations** | **Zero-Hallucination ReAct Loop:** LLMs are never permitted to generate, guess, or interpolate financial amounts. Every figure is produced by verified, deterministically audited Python calculations. |
| **Disconnected Spreadsheets** | **Live General Ledger Integration:** Connects directly with Frappe / ERPNext accounting tables, invoices, payments, and payment schedules. |
| **High API Failure Rates & Rate Limits** | **Multi-Key Rotating Fallback:** Native support for multiple API keys across Google Gemini, OpenAI, and NVIDIA NIM (`z-ai/glm-5.3-flash`) with seamless failover upon encountering HTTP 429 or quota caps. |
| **Uncontrolled AI Actions** | **L5 Dual-Control Safety Gates:** Prohibits autonomous money transfers and requires dual independent sign-offs (Controller + Board) for ledger cancellations. |
| **Complex Deployment & DevOps Overhead** | **1-Click Port 80 Deployment:** Single script (`./run.sh deploy`) self-heals system swap, spins up Docker, hydrates database seed, and serves everything behind Nginx on Port 80. |

---

## 🧭 Core Modules (F001 — F007)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            LOTUS FIN FINANCIAL SUITE                         │
├─────────────────────┬────────────────────────────────────────────────────────┤
│ F001 · Health       │ Real-time P&L, Gross Margin, Cash Ratio, AR/AP Aging   │
│ F002 · Cashflow     │ 30-Day Predictive Cash Forecast from Payment Schedules │
│ F003 · Risk Signals │ Statistical Cluster Alerts (AP Spikes & AR Delinquency)│
│ F004 · What-If      │ Stress Simulations: Revenue Shocks & Debtor Delays     │
│ F005 · Financing    │ SME Commercial Loan & Working Capital Facility Matcher │
│ F006 · Amortization │ Equal Monthly Installments (PMT) & Basis Point Shocks  │
│ F007 · Debt Followup│ Dynamic L3 Customer Reminder Drafting & Auto-SMTP Mail │
└─────────────────────┴────────────────────────────────────────────────────────┘
```

- **F001 — Corporate Financial Health (AI001):** Instant calculation of net revenue, gross margin, cash buffers, and receivables turnover from real ledger vouchers.
- **F002 — 30-Day Predictive Cash Flow (AI002):** Ingests contractual payment schedules from submitted `Sales Invoice` and `Purchase Invoice` records to map daily liquidity without statistical fiction.
- **F003 — Early Risk Signals & Debt Clustering (AI003):** Identifies impending liquidity crunches by detecting concentration spikes in vendor dues (`AP_DUE_CLUSTER`) and deteriorating debtor aging (`AR_OVERDUE_SPIKE`).
- **F004 — What-If Stress Testing Engine (AI004/AI005):** Simulates liquidity runway under configurable business stress parameters (revenue shifts, supplier payment compression, debtor delays).
- **F005 — SME Loan Facility Matcher:** Evaluates debt-service coverage ratios (DSCR) against commercial banking loan products and calculates match scores.
- **F006 — Loan Amortization & Rate Shock:** Models fixed-rate loan amortization schedules (PMT) with variable basis point interest shocks (+100 to +300 bps).
- **F007 — Receivables Statement Reconciliation & Automated Dispatch:** Auto-generates formal debt reminders with live customer metadata, editable templates, and 1-click dispatch via standard `frappe.sendmail`.

---

## 🛡️ Dual-Control Policy Safety Gate (L5)

Lotus Fin incorporates an enterprise dual-control governance model to safeguard SME treasury:

```
                          User / Copilot Action Request
                                       │
                                       ▼
                     ┌───────────────────────────────────┐
                     │    Dual-Control Policy Gate (L5)  │
                     └─────────────────┬─────────────────┘
                                       │
              ┌────────────────────────┴────────────────────────┐
              ▼                                                 ▼
      [ Read / Draft Tasks ]                         [ High-Risk Ledger Mutations ]
   (Search Invoices, Draft Mail)                     (Cancel Invoices, Wire Transfers)
              │                                                 │
              ▼                                                 ▼
        Single Confirm                                 Evaluation Verdict
    (Immediate Dispatch)                     ┌──────────────────┴──────────────────┐
                                             ▼                                     ▼
                                    [ Cancel Invoice ]                     [ Wire Transfer ]
                                    Dual Sign-offs Required                Hard Blocked (403)
                                (Finance Controller + Board)           (Manual Banking Token Only)
```

---

## 🚀 Quick Start

Deploy Lotus Fin in under 5 minutes on any cloud server or local machine.

### 🌟 1-Click Production Cloud Deployment (Port 80)
For fresh Linux VPS instances (Ubuntu 22.04 / 24.04, Debian, AWS EC2, DigitalOcean):

```bash
# 1. Clone repository
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin

# 2. Grant execution permissions
chmod +x run.sh scripts/*/*.sh

# 3. Launch automated cloud deployment
./run.sh deploy
```

> **Automated Pipeline Features:**
> - **Self-Healing Swap:** Automatically detects host memory and provisions a **2GB Swapfile** if RAM is constrained.
> - **Docker Auto-Bootstrap:** Installs Docker Engine & Compose plugin if not present.
> - **Zero-Config Database Hydration:** Automatically restores the bundled MariaDB database snapshot (`scripts/data/database/initial_db_seed.sql.gz`), migrates schemas, and activates default SMTP accounts.
> - **Nginx Gateway (Port 80):** Serves the compiled React 19 SPA and proxies API routes without requiring custom host reverse proxy setups.

---

### 💻 Local Developer Setup

#### On Linux / macOS / WSL:
```bash
./run.sh dev
```

#### On Windows (PowerShell):
```powershell
.\scripts\dev\run-dev.ps1
```

- **Frontend Application:** `http://localhost:5173` (Vite Hot-Reload)
- **Frappe Desk & API:** `http://localhost:8080`
- **Default Credentials:** `Administrator` / `admin`

---

## 🔄 Multi-Provider Resilience & Fallback

Never experience downtime due to API quota depletion. Configure comma-separated keys in your `.env` file:

```ini
# Provider Selection ('gemini' | 'openai' | 'nvidia' | 'deepseek' | 'mock')
LOTUS_AI_PROVIDER=gemini
LOTUS_AI_MODEL=gemini-flash-latest

# Google Gemini (Supports Multiple Keys with Automatic Failover)
GEMINI_API_KEY=AQ.Ab8RN6KcdBJg..., AQ.Ab8RN6J6ZVGE..., AQ.Ab8RN6J1q4sH...

# OpenAI / DeepSeek (Multiple Keys)
OPENAI_API_KEY="sk-proj-key1...", "sk-proj-key2..."

# NVIDIA NIM High-Performance Endpoint
NVIDIA_API_KEY="nvapi-key1...", "nvapi-key2..."
NVIDIA_MODEL_NAME=z-ai/glm-5.3-flash

# Outgoing SMTP Mail Settings (Auto-Provisions into ERPNext)
LOTUS_SMTP_SERVER=smtp.gmail.com
LOTUS_SMTP_PORT=587
LOTUS_SMTP_EMAIL=your_email@gmail.com
LOTUS_SMTP_PASSWORD=your_app_password
LOTUS_SMTP_USE_TLS=1
```

*When any key encounters HTTP 429 (Rate Limit) or quota exhaustion, Lotus Fin automatically falls back to the next healthy key in the pool.*

---

## 🏛️ System Architecture

```
                                  [ Client Browser ]
                                          │
                                          │ HTTP / WS (Port 80)
                                          ▼
                [ Nginx Gateway Container (Static Hosting & Routing) ]
                  ├── /               ──> React 19 SPA (Vite + TailwindCSS)
                  └── /(api|desk|app) ──> [ Frappe ERPNext Backend (:8080) ]
                                                 │
                         ┌───────────────────────┼────────────────────────┐
                         ▼                       ▼                        ▼
                 [ ReAct AI Agent ]     [ MariaDB 11.8 ]         [ Redis 6.2 ]
                 (Prompt & Tool Loop)   (General Ledger Records) (Cache & Workers)
                         │
                         ▼
             [ Financial Engine (F001 - F007) ]
```

---

## 📁 Repository Tour

```
lotus-fin/
├── docker/production/         # Production Nginx Gateway & Docker Compose definitions
├── frontend/                  # React 19 Single Page Application (TailAdmin theme)
│   ├── src/components/        # Reusable financial widgets & charts
│   ├── src/constants/         # Policy catalogs & executive dictionary
│   └── src/pages/copilot/     # AI Copilot chat interface, L3 cards & L5 audit view
├── lotus_fin/                 # Frappe Framework Core Application
│   ├── api/                   # RESTful API endpoints for Copilot and financial data
│   ├── application/agent/     # ReAct Agent loop, Prompt Engine, Presentation Gate
│   ├── domain/constants/      # Centralized business messages & safety verdicts
│   ├── infrastructure/llm/    # Multi-key rotating adapters (Gemini, OpenAI, NVIDIA)
│   └── modules/               # Core analytical calculation modules (F001 — F007)
├── scripts/                   # Modular Operational Automation
│   ├── deploy/                # 1-Click production cloud deployer (run-deploy.sh)
│   ├── dev/                   # Local developer setup (run-dev.sh / run-dev.ps1)
│   ├── packaging/             # Multi-stage container packaging (run-packaging.sh)
│   ├── container/             # Container lifecycle manager (run-container.sh)
│   ├── data/database/         # Exported database seed (initial_db_seed.sql.gz)
│   └── README.md              # Detailed scripts operations manual
└── docs/                      # Technical Documentation & Specs
    ├── TECHNICAL_SPECIFICATION.md  # Detailed System Architecture Specification
    └── zh/                    # Complete Chinese Documentation (中文技术文档)
```

---

## 📚 Documentation & Links

- 📖 [Technical Specification & Deep Architecture](docs/TECHNICAL_SPECIFICATION.md)
- 🛠️ [Operations & Deployment Manual](scripts/README.md)
- 🇨🇳 [中文文档 (Chinese Documentation Hub)](docs/zh/README.md)
- 🛡️ [Security Single Source of Truth (SSOT)](docs/security/README.md)
- 📑 [Frappe Framework Official Guide](https://frappeframework.com/docs)

---

## 🤝 Contributing

We welcome community contributions, bug reports, and pull requests!
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feat/AmazingFeature`).
3. Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feat/AmazingFeature`).
5. Open a Pull Request.

---

<div align="center">

**Built with pride for resilient SMEs worldwide.**  
Licensed under the [MIT License](LICENSE).

</div>
