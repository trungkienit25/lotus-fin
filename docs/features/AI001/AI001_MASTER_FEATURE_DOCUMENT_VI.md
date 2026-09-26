# AI001 — Master Feature Document: Lotus Fin Financial Health Analyst (AI-F001)

**Feature Code:** AI001 / AI-F001  
**Full Name:** Financial Health Analyst  
**Primary Use Case:** UC003 (Financial Health Analysis & Diagnosis)  
**Supporting Use Cases:** UC006 (Executive Reporting), UC009 (Risk & Liquidity Monitoring)  
**Status:** IMPLEMENTED & VERIFIED  
**Target Environment:** Frappe v16.34 / ERPNext v16.35  

---

## 1. Executive Summary & Objective

Lotus Fin transforms raw ERPNext accounting records into traceable, explainable, and actionable financial intelligence.
AI-F001 Financial Health Analyst provides company-level diagnostic visibility into revenue, margins, cash position, receivables, and payables for SMEs without manual report consolidation.

### Fundamental Architectural Principle
> Backend intelligence that is not visible, inspectable, or actionable in the user interface has low product value during real usage and demo evaluation.
>
> **ERPNext** = operational transactional ledger and reporting backend.  
> **Lotus Fin UI** = company-level financial intelligence, synthesis, and decision copilot experience.

---

## 2. Productization & UX Architecture

### 2.1 Why Modal-Only UX Was Insufficient
A previous implementation pattern presented AI intelligence as:
`ERPNext Form → Click AI Button → Loading → Modal Popup → Short 1-2 sentence label (e.g. LOW / HIGH / HEALTHY)`

This architecture suffered from critical product flaws:
1. **Intelligence Concealment:** It reduced multi-statement accounting intelligence to a binary or single-label indicator, hiding deterministic calculations, EvidenceRefs, and period deltas.
2. **Identity Confusion:** Presenting invoice-level credit checks as "financial health" confused transactional analysis with company-wide diagnostic health.
3. **Low Actionability & Trust Deficit:** Modal popups gave users no direct path to audit where numbers originated or what specific ledger drill-downs to perform next.

### 2.2 Dedicated Financial Health Workspace
AI001 is productized as a native, single-column Frappe Page (`financial-health`):
- **Branding & Identity:** Clear Lotus Fin AI-F001 header distinguishing the financial intelligence layer from default ERP table views.
- **Analysis Context:** Company selector (server-authorized), fiscal period selector, comparison mode, and actual data mode indicator.
- **KPI Summary Cards:** 6 core metrics (`revenue`, `cogs`, `gross_margin`, `cash_balance`, `ar_outstanding`, `overdue_ar_ratio`, `ap_outstanding`) + frozen `near_term_ap` status.
- **Period Comparison:** Full equal-length historical comparative analysis with absolute change and percentage growth.
- **AI Analysis Decomposition:** Dedicated 4-part structure separating **What Happened (Facts)**, **Financial Interpretation**, **System Limitations**, and **Recommended Next Checks**.
- **Actionability & Bounded Drill-down:** One-click navigation to approved standard reports (`Profit and Loss Statement`, `Accounts Receivable`, `Accounts Payable`, `General Ledger`, `Trial Balance`).
- **Audit Evidence Drawer:** Inspectable `EvidenceRef` items displaying ERPNext source report, as-of timestamp, filter parameters, and deterministic SHA256 checksums.
- **Graceful Failure & Safe Degradation:** If LLM explanation is unavailable or external APIs fail, all deterministic metrics, comparison tables, and evidence records remain 100% visible and interactive.

---

## 3. Core Engine Architecture

```
ERPNext Accounting Records (P&L, AR, AP, Trial Balance)
         ↓
Safe Report Adapter (`extract_key_report_data`) [Company Guard INV-01, INV-02]
         ↓
`FinancialSnapshot` Engine (`build_financial_snapshot`)
         ↓
Deterministic Metric & Comparison Engine (`compute_metric_change`)
         ↓
Grounded LLM Provider (`validate_grounding`, XSS Sanitization, Minimization)
         ↓
Lotus Fin Financial Health Workspace (`/app/financial-health`)
```

---

## 4. Key Financial Metrics & Verification Baseline

| Metric | Formula / Source | Gold Baseline (FY2020 Demo) | UI Rendering |
|---|---|---|---|
| **Revenue** | Root Income / P&L Leaf | 363,000 VND | `VND 363.000,00` |
| **COGS** | Cost of Goods Sold P&L | 253,760 VND | `VND 253.760,00` |
| **Gross Margin** | `(Revenue - COGS) / Revenue` | 0.3009 (30.09%) | `30.09%` |
| **AR Outstanding** | Total Outstanding in AR | 316,000 VND | `VND 316.000,00` |
| **Overdue AR Ratio** | `Overdue AR / Total AR` | 1.0000 (100.0%) | `100.00%` |
| **AP Outstanding** | Total Outstanding in AP | 184,293 VND | `VND 184.293,00` |
| **Cash Balance** | Bank & Cash Accounts / TB | -117,854 VND | `VND -117.854,00` (Negative red highlight) |
| **Near-Term AP** | Frozen horizon limitation | UNAVAILABLE | `Unavailable` (Horizon not frozen) |

---

## 5. Security & Isolation SSOT

1. **INV-01 (Company Isolation):** Client input for `company` is untrusted; strictly validated server-side. Cross-company access returns `FORBIDDEN` with 0 leaked metrics.
2. **INV-02 (Report Guard):** Users can only execute allowlisted accounting reports with verified permissions.
3. **INV-03 (Zero PII & Data Minimization):** Payloads sent to LLM provider contain only aggregated metrics, limitations, and evidence metadata; no raw GL lines, invoice names, customer PII, or credentials.
4. **Deterministic Invariant:** Missing or errored data sources yield `UNAVAILABLE` or `PARTIAL`, never 0.0.
