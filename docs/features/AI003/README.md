# AI-F003 — RISK SIGNAL & DEBT CLUSTER DETECTOR (AI003)

> **Feature Identifier:** `AI003` / `AI-F003`  
> **Status:** Implemented & Production Verified  
> **Computation Class:** Deterministic Risk Signal Rule Engine  
> **Target Module:** `lotus_fin.modules.f003_risk_signal`  
> **Test Coverage:** Full test coverage with verified edge-case assertions  

---

## 1. Feature Overview & Problem Statement
SMEs often fail to detect early warnings of solvency deterioration until liquidity is critically exhausted. AI003 scans General Ledger and aging records to identify impending working capital risks and debt concentration spikes.

### Core Risk Signals Detected
- **`AP_DUE_CLUSTER` (Payable Due Concentration):** Detects clustering of supplier obligations falling due within narrow time windows (e.g. >40% of monthly outflows due within 5 days).
- **`AR_OVERDUE_SPIKE` (Receivable Aging Degradation):** Identifies sudden increases in overdue invoices or client payment delay degradation (>60 days bucket expansion).
- **`LIQUIDITY_DRAIN` (Cash Runway Deterioration):** Warns when cash runway dips below 15 operating days.
- **`REVENUE_VOLATILITY` (Sales Contraction):** Detects sharp month-over-month revenue drops exceeding tolerance thresholds.

---

## 2. Architectural Invariants & Security Controls
1. **Deterministic Rule Gates:** Risk signals trigger exclusively from deterministic mathematical thresholds; the LLM cannot fabricate or suppress risk flags.
2. **Company Access Enforcement:** Enforces verified tenant identity before scanning ledger vouchers.
3. **Audit Trail Traceability:** Every triggered risk signal points directly to the underlying voucher numbers and ledger balances for operator verification.
