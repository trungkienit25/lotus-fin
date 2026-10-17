# Lotus Fin — Technical Specification & System Architecture

## 1. System Overview

**Lotus Fin** is an enterprise-grade AI Financial Copilot and Autonomous Decision Support System tailored for Small and Medium Enterprises (SMEs). The platform bridges conversational AI with deterministic ERP General Ledger systems, eliminating hallucination risks in mission-critical corporate accounting.

```
+-----------------------------------------------------------------------------------+
|                                  CLIENT LAYER                                     |
|                   React 19 SPA (Vite, TypeScript, TailwindCSS)                    |
+-----------------------------------------+-----------------------------------------+
                                          | HTTP / WebSocket (Port 80)
                                          v
+-----------------------------------------------------------------------------------+
|                             EDGE GATEWAY (Reverse Proxy)                          |
|                       Nginx Gateway Container (Port 80)                           |
|       / -> Static React SPA | /(api|desk|assets) -> Frappe Upstream (:8080)       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        APPLICATION & BUSINESS LOGIC LAYER                         |
|   +------------------------------------+   +----------------------------------+   |
|   |        Frappe v16 / ERPNext        |   |         Lotus Fin App            |   |
|   |  - Core DocTypes & General Ledger  |   |  - Clean Architecture Core       |   |
|   |  - Auth, Role-Based Access Control |   |  - ReAct Agent Controller        |   |
|   |  - Outgoing SMTP Mail Services     |   |  - Dual-Control Policy Gate (L5) |   |
|   +------------------------------------+   +-----------------+----------------+   |
+--------------------------------------------------------------|--------------------+
                                                               | Tool Calls
                                                               v
+-----------------------------------------------------------------------------------+
|                      DETERMINISTIC FINANCIAL ENGINE (F001 - F007)                 |
|  - F001: Corporate Financial Health Analyst (P&L, Cash Ratio, Working Capital)    |
|  - F002: 30-Day Cash Forecast & Runway (Contractual Payment Schedule Source)      |
|  - F003: Financial Risk Signal Detector (AP Due Clusters, AR Overdue Spikes)      |
|  - F004: What-If Stress Testing Engine (Revenue Shock, Collection Delay)          |
|  - F005: Bank Facility & Working Capital Loan Matcher                             |
|  - F006: Loan Amortization & Basis Point Interest Rate Shock (PMT Engine)         |
|  - F007: Receivables Statement Reconciliation & Automated SMTP Dispatch           |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           DATA & PERSISTENCE LAYER                                |
|          MariaDB 11.8 (ERP Ledger)    |    Redis 6.2 (Cache & Celery Queues)      |
+-----------------------------------------------------------------------------------+
```

---

## 2. Technical Stack

| Tier | Technology | Specification / Version |
| :--- | :--- | :--- |
| **Edge Gateway** | Nginx Alpine | Reverse proxy, Gzip compression, single Port 80 entrypoint |
| **Frontend SPA** | React, TypeScript, Vite | React 19, TailwindCSS, Lucide Icons, Headless UI |
| **Backend Framework** | Frappe Framework, Python | Python 3.12/3.13, Frappe v16.36.1, ERPNext v16.36.1 |
| **AI Orchestration** | Deterministic ReAct Loop | Whitelisted tool dispatcher, prompt engine, presentation gate |
| **LLM Providers** | Multi-Key Rotating Adapters | Google Gemini API, OpenAI API, NVIDIA NIM (`z-ai/glm-5.3-flash`) |
| **Relational Database** | MariaDB | 11.8 (`utf8mb4_unicode_ci`), ACID transactional storage |
| **Queue & Cache** | Redis Alpine | Redis 6.2 (separate cache and job queues) |
| **Container Engine** | Docker & Docker Compose | Multi-stage build, rootless isolation, healthchecks |

---

## 3. Financial Engine Specifications (F001 — F007)

```
                       User Prompt
                            │
                            ▼
              ┌───────────────────────────┐
              │    Agent Runner Loop      │
              │  - System Prompt Engine   │
              │  - Tool Whitelist Schema  │
              └─────────────┬─────────────┘
                            │ Structured Tool Invocation
                            ▼
   ┌──────────────────────────────────────────────────┐
   │             Financial Engine Registry            │
   ├───────────────────┬──────────────────────────────┤
   │ F001: Health      │ P&L, AR/AP, Liquidity Ratio  │
   │ F002: Cashflow    │ 30-Day Inflow/Outflow Curves │
   │ F003: Risk        │ AP Cluster & AR Aging Spike  │
   │ F004: What-If     │ Sensitivity Stress Models    │
   │ F005: Lending     │ Commercial Credit Matching   │
   │ F006: Repayment   │ PMT Loan Amortization Engine │
   │ F007: Reminder    │ Debt Letter & SMTP Dispatch  │
   └───────────────────┴──────────────────────────────┘
                            │ Deterministic JSON Response
                            ▼
              ┌───────────────────────────┐
              │     Presentation Gate     │
              │  - Strip Internal Tokens  │
              │  - Enforce Executive Tone │
              └─────────────┬─────────────┘
                            │ Sanitized Natural Output
                            ▼
                    End-User Presentation
```

### Module Breakdown
- **F001 — Financial Health Snapshot:** Evaluates gross margin, net revenue, operating cash, and overdue debt ratios from GL entries.
- **F002 — 30-Day Cash Forecast:** Ingests contractual payment schedules from submitted `Sales Invoice` and `Purchase Invoice` records to map expected daily liquidity without statistical interpolation.
- **F003 — Early Risk Signals:** Runs cluster analysis over due dates to identify upcoming liquidity drains (`AP_DUE_CLUSTER`) and aging receivables degradation (`AR_OVERDUE_SPIKE`).
- **F004 — What-If Stress Testing:** Models working capital impact under revenue changes (-30% to +20%) and debtor payment delays (+15 to +60 days).
- **F005 — SME Loan Facility Matcher:** Compares verified debt-service coverage ratio (DSCR) and revenue history against commercial lending product parameters.
- **F006 — Loan Amortization Engine:** Calculates monthly installments using standard annuity formulas (PMT), modeling baseline and interest rate shocks (+100 to +300 bps).
- **F007 — Debt Follow-up & Automated Dispatch:** Matches overdue customer records, builds an L3 reconciliation draft, and transmits notices through `frappe.sendmail`.

---

## 4. Policy Gate & Security Controls (L5)

To prevent unauthorized ledger alterations or automated capital transfer risks, sensitive operational actions require explicit authorization gates:

```
                  Sensitive User Intent
                            │
                            ▼
            ┌───────────────────────────────┐
            │   Dual-Control Policy Gate    │
            │   (Evaluation Engine)         │
            └───────────────┬───────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    [ Low-Risk Action ]             [ High-Risk Action ]
    - Search Invoices               - Cancel Sales Invoice
    - View Overdue Report           - Wire Transfer Execution
            │                               │
            │ Single-User Confirm           ├─ Cancel: Dual Sign-off Required
            ▼                               │  (Controller & Board Member)
    Execute Request                         └─ Wire: Hard-Blocked (Manual Banking Only)
```

| Action Identifier | Risk Level | Policy Decision | Verification Requirement |
| :--- | :---: | :---: | :--- |
| `submit_sales_invoice` | High | Conditional | Single-level approval from Accounts User or Manager |
| `cancel_sales_invoice` | Critical | Restricted | **Dual-Control Gate:** Independent sign-offs from Controller & Board |
| `send_statement_email` | Medium | Allowed | Sender verification against customer registered domain |
| `request_disbursement` | High | Conditional | Payable Clerk draft -> Finance Manager budget approval |
| `execute_wire_transfer` | Critical | **Blocked** | Prohibited for AI/automation. Manual bank execution only |
| `autonomous_reconciliation` | Critical | **Blocked** | Prohibited. Adjustments require manual audit justification |

---

## 5. Operations & Lifecycle Management

Operational tasks are encapsulated in modular scripts under [`scripts/`](scripts/README.md) and exposed via [`run.sh`](run.sh).

```
scripts/
├── deploy/
│   └── run-deploy.sh                 # 1-Click Cloud Deployment Pipeline
├── dev/
│   ├── run-dev.sh                    # Linux / macOS / WSL Local Dev Server
│   └── run-dev.ps1                   # Windows PowerShell Local Dev Server
├── packaging/
│   └── run-packaging.sh              # Multi-Stage Production Image Builder
├── container/
│   └── run-container.sh              # Production Container Lifecycle Orchestrator
└── data/database/
    └── initial_db_seed.sql.gz        # Portable General Ledger Seed Snapshot
```

### Production Cloud Deployment (Single Command)
```bash
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin
chmod +x run.sh scripts/*/*.sh
./run.sh deploy
```
1. Audits host system; configures **2GB Swapfile** if host memory is constrained.
2. Verifies or installs official Docker Engine and Compose plugin.
3. Packages frontend assets into `lotus-fin/gateway:latest`.
4. Boots the production cluster exposed on **Port 80**.
5. Restores the bundled database snapshot (`initial_db_seed.sql.gz`), executes `bench migrate`, and configures the default SMTP account.
6. Conducts HTTP health verification and outputs the public URL.

### Local Development Environment
- **POSIX (Linux / macOS / WSL):**
  ```bash
  ./run.sh dev
  ```
- **Windows (PowerShell):**
  ```powershell
  .\scripts\dev\run-dev.ps1
  ```
- Dev Frontend: `http://localhost:5173` | Frappe Desk: `http://localhost:8080`

### Image Packaging
```bash
./run.sh packaging
```

### Container Lifecycle
```bash
./scripts/container/run-container.sh status    # Check container health and memory
./scripts/container/run-container.sh logs      # Stream combined container logs
./scripts/container/run-container.sh restart   # Graceful service restart
./scripts/container/run-container.sh stop      # Stop production cluster
```

---

## 6. Configuration Reference (`.env`)

```ini
# AI Provider Configuration ('gemini' | 'openai' | 'nvidia' | 'deepseek' | 'mock')
LOTUS_AI_PROVIDER=gemini
LOTUS_AI_MODEL=gemini-flash-latest

# Multi-Key Rotation & Automatic Fallback (Comma-separated)
GEMINI_API_KEY=key_1, key_2, key_3
OPENAI_API_KEY="sk-key1", "sk-key2"
NVIDIA_API_KEY="nvapi-key1", "nvapi-key2"
NVIDIA_MODEL_NAME=z-ai/glm-5.3-flash

# Database Settings
DB_HOST=db
DB_PORT=3306
MYSQL_ROOT_PASSWORD=admin
MARIADB_ROOT_PASSWORD=admin

# Outgoing SMTP Mail Settings
LOTUS_SMTP_SERVER=smtp.gmail.com
LOTUS_SMTP_PORT=587
LOTUS_SMTP_EMAIL=notifications@yourdomain.com
LOTUS_SMTP_PASSWORD=your_app_password
LOTUS_SMTP_USE_TLS=1
```

---

## 7. Documentation Index

- [Operations & Automated Scripts Manual](scripts/README.md)
- [Enterprise Security Architecture SSOT](docs/security/README.md)
- [中文技术文档 (Chinese Documentation)](docs/zh/README.md)

### Container Lifecycle
```bash
./scripts/container/run-container.sh status    # Check container health and memory
./scripts/container/run-container.sh logs      # Stream combined container logs
./scripts/container/run-container.sh restart   # Graceful service restart
./scripts/container/run-container.sh stop      # Stop production cluster
```

---

## 6. Configuration Reference (`.env`)

```ini
# AI Provider Configuration ('gemini' | 'openai' | 'nvidia' | 'deepseek' | 'mock')
LOTUS_AI_PROVIDER=gemini
LOTUS_AI_MODEL=gemini-flash-latest

# Multi-Key Rotation & Automatic Fallback (Comma-separated)
GEMINI_API_KEY=key_1, key_2, key_3
OPENAI_API_KEY="sk-key1", "sk-key2"
NVIDIA_API_KEY="nvapi-key1", "nvapi-key2"
NVIDIA_MODEL_NAME=z-ai/glm-5.3-flash

# Database Settings
DB_HOST=db
DB_PORT=3306
MYSQL_ROOT_PASSWORD=admin
MARIADB_ROOT_PASSWORD=admin

# Outgoing SMTP Mail Settings
LOTUS_SMTP_SERVER=smtp.gmail.com
LOTUS_SMTP_PORT=587
LOTUS_SMTP_EMAIL=notifications@yourdomain.com
LOTUS_SMTP_PASSWORD=your_app_password
LOTUS_SMTP_USE_TLS=1
```

---

## 7. Documentation Index

- [Operations & Automated Scripts Manual](scripts/README.md)
- [Enterprise Security Architecture SSOT](docs/security/README.md)
- [中文技术文档 (Chinese Documentation)](docs/zh/README.md)

