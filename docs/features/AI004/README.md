# AI-F004 — WHAT-IF MULTI-VARIABLE SCENARIO SIMULATOR (AI004)

> **Feature Identifier:** `AI004` / `AI-F004`  
> **Status:** Implemented & Verified with Gold Test Fixtures  
> **Computation Class:** In-Memory Deterministic Simulation + Grounded LLM Explanation  
> **Target Module:** `lotus_fin.modules.f004_what_if`  
> **Invariants:** Zero DB Mutation, Python `Decimal` Arithmetic, `data_mode = "simulation"`  

---

## 1. Feature Overview & Problem Statement
Enables SME financial officers and business owners to model complex hypothetical business shocks in-memory and evaluate immediate impacts across 9 core financial health KPIs over a 30 to 90 day planning horizon.

### Supported Simulation Modifiers
1. **Sales Shock:** Models percentage revenue expansions or contractions (e.g. `-20%` sales decline).
2. **Collection Delay:** Models client payment slippage (e.g. average collection extended by `+15 days`).
3. **Payable Extension:** Simulates negotiated vendor payment deferrals (e.g. `+30 days` credit extension).
4. **Expense Surge:** Injects unexpected operational expenditures or payroll inflation.
5. **Financing Injection:** Simulates new debt injections or capital draws on designated calendar dates.

---

## 2. 9-KPI Delta Output Matrix
The simulation computes exact baseline vs. simulated delta trajectories:
- Opening Cash Balance, Closing Cash Balance, Minimum Cash Point, First Shortfall Date, Cash Runway Days, Total Inflow Delta, Total Outflow Delta, Shortfall Status, and Working Capital Delta.

---

## 3. Architectural Invariants & Security Controls
1. **`INV-SIM-01` (Zero DB Mutation):** All simulation runs execute strictly in-memory. Transactional accounting ledgers are never modified.
2. **`INV-SIM-02` (Simulation Stamping):** All simulation payloads, DTOs, and UI cards bear `data_mode = "simulation"`.
3. **`INV-SIM-03` (Deterministic Math):** All delta computations are calculated via Python `Decimal` with zero float rounding errors.
4. **Multi-Tenant Isolation:** Enforces company permission gates before reading baseline cash events.
