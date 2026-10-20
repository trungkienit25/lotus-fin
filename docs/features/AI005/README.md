# AI-F005 — SME FINANCING PRODUCT MATCHING ENGINE (AI005)

> **Feature Identifier:** `AI005` / `AI-F005`  
> **Status:** Implemented & Verified  
> **Computation Class:** Deterministic Eligibility Scoring + Product Catalog Matching  
> **Target Module:** `lotus_fin.modules.f005_financing`  
> **Invariants:** Advisory Sandbox Only, Deterministic Rules, Zero PII  

---

## 1. Feature Overview & Problem Statement
Bridges the credit gap between SMEs and commercial lending partners. When projected cash deficits or working capital shortfalls are detected, the financing engine evaluates corporate financial metrics (DSCR, operating revenue, accounts receivable collateral) against commercial bank underwriting criteria.

### Capabilities & Product Archetypes
- **Revolving Working Capital Credit Line:** Short-term operational liquidity anchored to historical monthly turnover.
- **Invoice Discounting & Factoring:** Fast liquidity advance backed by verified overdue and unencumbered accounts receivable.
- **Medium-Term Equipment / Capex Loan:** Multi-year financing structured with amortized capital repayments.
- **Merchant Cash Advance:** Unsecured bridge facility evaluated against gross transactional velocity.

---

## 2. Underwriting Criteria
- **DSCR (Debt Service Coverage Ratio):** Evaluates `(EBITDA - Tax) / Total Debt Service` against underwriting floors (>= 1.25x for Tier 1 Banks, >= 1.10x for Fintech partners).
- **Quick Ratio & Turnover:** Verifies liquidity buffers and monthly revenue stability.

---

## 3. Architectural Invariants & Security Controls
1. **Deterministic Underwriting Rules:** Eligibility rules execute via deterministic logic gates; the LLM cannot approve or override financing rules.
2. **Advisory / Sandbox Boundary:** Operates exclusively in advisory/simulation mode. Direct capital disbursement requires formal bank partner integration.
3. **Data Minimization:** Financial metric summaries sent for product matching exclude customer PII and sensitive trade secrets.
