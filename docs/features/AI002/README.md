# AI-F002 — 30-DAY CASH FLOW FORECAST ENGINE (AI002)

> **Feature Identifier:** `AI002` / `AI-F002`  
> **Status:** Implemented & Production Verified  
> **Computation Class:** Deterministic Contractual Payment Schedule Aggregation  
> **Target Module:** `lotus_fin.modules.f002_cashflow`  
> **Test Coverage:** Full hermetic test suite passing  

---

## 1. Feature Overview & Problem Statement
Cash flow insolvency is the primary cause of SME failure. Unlike high-level statistical forecasts, AI002 models upcoming liquidity by aggregating verified contractual cash commitments from real sales invoices, purchase invoices, and debt amortization obligations.

### Capabilities & Key Projections
- **30-Day Daily Cash Horizon:** Forecasts daily expected inflows, outflows, and net closing cash positions for each day over the next 30 days.
- **Contractual Payment Integration:** Pulls expected due dates and payment terms from submitted ERP transactions without statistical interpolation.
- **Liquidity Valley & Shortfall Detection:** Pins the exact calendar date of the minimum cash point and flags potential liquidity deficits in advance.
- **Operating Cash Runway:** Computes the number of business days the enterprise can sustain operations at current burn rates.

---

## 2. Architectural Invariants & Security Controls
1. **Contractual Veracity:** Liquidity figures are derived solely from verified ERP voucher schedules (`Sales Invoice`, `Purchase Invoice`, `Payment Schedule`).
2. **Zero Hallucination:** The LLM does not forecast or estimate cash numbers; it only interprets the deterministic schedule table.
3. **Multi-Tenant Scoping:** Cash flow data is strictly bounded to the authorized tenant `company`.
4. **Voucher Deduplication:** Prevents double-counting across overlapping invoice and payment schedules.
