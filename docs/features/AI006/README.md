# AI-F006 — DEBT AMORTIZATION & INTEREST RATE SHOCK ENGINE (AI006)

> **Feature Identifier:** `AI006` / `AI-F006`  
> **Status:** Implemented & Verified  
> **Computation Class:** Deterministic Actuarial Amortization (PMT) + Stress Simulation  
> **Target Module:** `lotus_fin.modules.f006_repayment`  

---

## 1. Feature Overview
Generates debt amortization schedules and evaluates corporate sensitivity to macroeconomic interest rate changes.

### Capabilities
- **Amortization Scheduling:** Computes equal monthly payments (PMT / annuity) and equal principal reduction schedules.
- **Interest Rate Shock Stress-Testing:** Simulates liquidity impacts if floating interest rates rise by `+100 bps`, `+200 bps`, or `+300 bps`.
- **Debt Service Coverage Integration:** Calculates future DSCR trajectories under varying debt service commitments.

---

## 2. Architectural Invariants
1. **Actuarial Accuracy:** All installment payments, interest allocations, and principal balance tables are computed using high-precision decimal math.
2. **Zero Hallucination:** Schedules are calculated directly by the deterministic math engine; the LLM merely translates the schedule into user-facing executive summaries.

