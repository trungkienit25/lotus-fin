# FINANCIAL AI FEATURES SUITE (F001 – F007)

Welcome to the **Lotus Fin Financial AI Engines** directory. Lotus Fin implements 7 deterministic, audit-traceable computational engines designed to empower Small and Medium Enterprises (SMEs) with automated financial intelligence.

---

## 🏛️ CORE ARCHITECTURAL INVARIANTS

Across all 7 modules, Lotus Fin adheres to strict zero-hallucination and security guarantees:

1. **Deterministic Calculation Invariant:** Large Language Models (LLMs) are **strictly prohibited** from performing financial arithmetic, aggregating ledgers, or computing ratios. All metrics are derived from audited Python calculation engines using `Decimal` math.
2. **Grounding & Presentation Gate:** The LLM serves solely to synthesize natural-language executive summaries anchored to verified facts returned by the calculation engines.
3. **Multi-Tenant Boundary:** Every engine enforces tenant isolation via `company` parameter verification (`CompanyAccessError` on violation).
4. **Level 4 Two-Phase Commit (Human-in-the-Loop):** Sensitive external operations (e.g., sending statements, dispatching reminders) require explicit human review and confirmation.

---

## 🤖 FINANCIAL ENGINES CATALOG

| Code | Name | Module Path | Focus & Core Capabilities |
| :---: | :--- | :--- | :--- |
| **F001** | [**Financial Health Analyst (AI001)**](./AI001/README.md) | `lotus_fin.modules.f001_health` | Computes gross margin, P&L, DSCR, quick ratio, and overdue balances from ERP General Ledger. |
| **F002** | [**30-Day Cash Flow Forecast (AI002)**](./AI002/README.md) | `lotus_fin.modules.f002_cashflow` | Daily cash flow projections based on contractual invoice payment schedules without statistical interpolation. |
| **F003** | [**Risk Signal & Debt Cluster Detector (AI003)**](./AI003/README.md) | `lotus_fin.modules.f003_risk_signal` | Scans ledger records for payable concentration (`AP_DUE_CLUSTER`) and receivable aging spikes (`AR_OVERDUE_SPIKE`). |
| **F004** | [**What-If Stress Testing Simulator (AI004)**](./AI004/README.md) | `lotus_fin.modules.f004_what_if` | In-memory simulation of operational shocks (sales contraction, collection delays, expense surges) across 9 KPIs. |
| **F005** | [**SME Financing Matcher (AI005)**](./AI005/README.md) | `lotus_fin.modules.f005_financing` | Evaluates enterprise financial ratios (DSCR, Quick Ratio) against commercial bank underwriting catalogs. |
| **F006** | [**Debt Amortization & Rate Shock (AI006)**](./AI006/README.md) | `lotus_fin.modules.f006_repayment` | High-precision PMT amortization schedules and interest rate shock stress testing (+100 to +300 bps). |
| **F007** | [**Receivables Recovery Copilot (AI007)**](./AI007/README.md) | `lotus_fin.modules.f007_copilot` | Fast lookup of past-due invoices, statement generation, and Level 4 Two-Phase Commit reminder dispatch. |

