# 🚀 Project Setup & Developer/Agent Onboarding Guide

This guide describes the complete workflow for setting up the local environment, booting Docker service clusters, and installing the custom app **`lotus_fin`** atop Frappe and ERPNext.

---

## 🏗️ 1. Multi-Tier Architecture Overview

Lotus Fin is structured into three clear architectural layers:

```mermaid
flowchart TD
    subgraph Layer3["Layer 3: Custom App & AI Copilot (lotus_fin)"]
        AI_PIPELINE["Key Reports Data Pipeline\n(api/key_reports.py)"]
        AI_INSIGHTS["Cash Flow & Risk Insights\n(api/ai_insights.py)"]
        CUSTOM_UI["React 19 Frontend SPA\n(Vite + TailwindCSS)"]
    end

    subgraph Layer2["Layer 2: ERP Core & Business Domain (ERPNext)"]
        ACC["Accounting (General Ledger, Invoicing, P&L)"]
        BUY["Buying & Accounts Payable"]
        SELL["Selling & Accounts Receivable"]
        ASSETS["Assets & Depreciation"]
    end

    subgraph Layer1["Layer 1: Platform & Infrastructure (Frappe & Docker)"]
        FRAPPE["Frappe Framework Core (Auth, DocType ORM, REST API, RBAC)"]
        CONTAINERS["Docker: MariaDB 11.8 + Redis Cache/Queue + Nginx Gateway"]
    end

    Layer3 --> Layer2
    Layer2 --> Layer1
```

---

## 💻 2. Setup Guide for Developers & AI Agents

### Prerequisites:
- **Operating System:** Linux, macOS, or Windows 10/11 (with WSL2 or PowerShell).
- **Docker & Docker Compose:** Docker Engine running.
- **Node.js 18+ & npm:** Required for building frontend assets.

---

### Step 1: Clone Repository & Verify Structure
```bash
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin
```

### Step 2: Automated Startup via Operational Scripts
Lotus Fin provides automated setup scripts under `scripts/`:

#### Option A: Quick Dev Launch (Frontend + Backend)
- **Linux / macOS / WSL:**
  ```bash
  ./run.sh dev
  ```
- **Windows (PowerShell):**
  ```powershell
  .\scripts\dev\run-dev.ps1
  ```
This starts MariaDB, Redis, and Frappe in the background, syncs `lotus_fin`, applies database migrations, seeds demo accounting records, and launches the Vite dev server at `http://localhost:5173`.

#### Option B: 1-Click Production Cloud Deployment (Port 80)
```bash
./run.sh deploy
```
This automatically allocates a 2GB Swapfile (if memory is low), packages the Nginx Gateway, hydrates database seed records (`scripts/data/database/initial_db_seed.sql.gz`), and exposes the app on HTTP Port 80.
