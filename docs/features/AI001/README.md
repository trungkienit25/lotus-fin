# AI-F001 — FINANCIAL HEALTH ANALYST (AI001)

> **Feature Identifier:** `AI001` / `AI-F001`  
> **Status:** Implemented, Formally Grounded & Production Verified  
> **Computation Class:** Deterministic ERP Aggregation + Grounded LLM Explanation  
> **Target Module:** `lotus_fin.modules.f001_health`  
> **Test Coverage:** Hermetic test suites (>77 test cases) passing  

---

## 1. Feature Overview & Problem Statement
SME business owners frequently struggle with fragmented accounting reports across General Ledgers, Balance Sheets, and Aging Statements. AI001 transforms raw ERP accounting records into an explainable, unified financial health snapshot without manual spreadsheet consolidation.

### Core Metrics Computed
- **Net Revenue & Gross Profit:** Calculated strictly from General Ledger P&L revenue and Cost of Goods Sold (COGS).
- **Gross Margin:** `(Revenue - COGS) / Revenue` calculated via Python `Decimal`.
- **Debt Service Coverage Ratio (DSCR):** Operating cashflow relative to active debt service commitments.
- **Net Working Capital & Quick Ratio:** Evaluates liquid treasury solvency against short-term operational liabilities.
- **Overdue AR / AP Balance:** Outstanding customer receivables and vendor payables categorized by aging buckets.

---

## 2. Architectural Invariants & Security Controls
1. **Zero-AI Calculation Invariant:** The LLM is strictly prohibited from computing financial metrics or ledger totals. All metrics are aggregated via deterministic Python services.
2. **Deterministic Unavailable State:** Incomplete or unmapped account periods yield explicit `UNAVAILABLE` or `PARTIAL` statuses rather than synthetic or fabricated zeros.
3. **Multi-Tenant Isolation:** Queries require explicit tenant authorization (`company` boundary). Cross-tenant access triggers immediate fail-closed `CompanyAccessError`.
4. **Zero-PII Grounded Explanation:** Explanations synthesized by the LLM consume exclusively sanitized metrics and aggregated ratios without customer names, bank details, or trade secrets.
