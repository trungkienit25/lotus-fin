# LOTUS FIN — AI FEATURE SPECIFICATION
## Codebase-Aligned MVP · FinTechathon 2026 Topic E

> **Version:** 1.0 — 2026-09-24  
> **Status:** Architecture-approved direction, implementation incomplete  
> **Primary code review basis:** `E:\lotus-fin\lotus_fin`, commit `f743acf57a43ac4c72090b9f07971b4803eb0667`  
> **Product direction:** ERPNext/Frappe remains the operational source candidate; Lotus Fin adds financial intelligence, scenario support and a bounded Financial Copilot.  
> **Important:** This document specifies AI/product capabilities. It does **not** claim that all features below are already implemented.  
> **MVP external-action policy:** `R4/R5 bank-write = OFF`; financing is read-only matching plus simulation.

---

# 1. Why AI Exists in Lotus Fin

Lotus Fin is not "ERPNext with an AI button" and is not a replacement ERP.

The product thesis is:

```text
ERPNext / Frappe operational data
            ↓
     trusted financial view
            ↓
 deterministic finance intelligence
            ↓
 forecast / risk / scenarios / financing
            ↓
       Financial Copilot
            ↓
 evidence-grounded explanation and orchestration
```

AI is used where it creates value in:

- understanding natural-language intent;
- choosing allowed analytical tools;
- retrieving authorized evidence;
- converting intent into typed scenario parameters;
- synthesizing multiple deterministic results;
- explaining why a financial result changed;
- comparing financing options based on published terms;
- communicating uncertainty and missing data.

AI must **not** become the source of truth for:

- balances;
- ratios;
- AR/AP totals;
- cash-flow arithmetic;
- repayment schedules;
- authorization;
- tenant/company selection;
- accounting posting;
- loan approval decisions.

---

# 2. Current Code Reality

The reviewed Lotus app is currently small and should be treated as a foundation, not as a completed AI system.

| Capability | Current state from code review | Interpretation |
|---|---|---|
| ERPNext report adapter | `PARTIAL` | useful integration point |
| Financial health engine | `STUB` | reports exist, deterministic KPI layer missing |
| Cash-flow forecast | `STUB` | current AR−AP logic is not a forecast |
| Invoice risk signal | `PARTIAL` | one simple rule exists |
| What-if engine | `NOT_FOUND` | must be built |
| Financing matching | `NOT_FOUND` | must be built |
| Repayment engine | `NOT_FOUND` | must be built |
| LLM/Copilot/RAG | `NOT_FOUND` | must be added only after finance correctness |
| ML training pipeline | `NOT_FOUND` | not required for P0 |
| OCR pipeline | `NOT_FOUND` | P1 unless needed for demo |

Existing paths identified by review:

```text
lotus_fin/lotus_fin/hooks.py
lotus_fin/lotus_fin/api/key_reports.py
lotus_fin/lotus_fin/api/ai_insights.py
lotus_fin/lotus_fin/public/js/lotus_fin.js
```

Any runtime behavior of ERPNext reports, permissions or row schemas remains `NOT_VERIFIED` until tested on the actual site.

---

# 3. Priority Model

## P0 — Competition Core

1. `AI-F001` Financial Health Analyst
2. `AI-F002` Cash-flow Forecast Copilot
3. `AI-F003` Risk Signal Agent
4. `AI-F004` What-if Scenario Agent
5. `AI-F005` Financing Decision Support
6. `AI-F006` Repayment / Stress Simulation
7. `AI-F007` Financial Copilot Orchestrator

## P1 — Extended Intelligence

- `AI-F101` Customer Payment Behavior
- `AI-F102` Sales / Revenue Trend Intelligence
- `AI-F103` Supplier Intelligence
- `AI-F104` Inventory Cash-Risk Intelligence
- `AI-F105` OCR / Document Intelligence

## P2 — Only if a specific demo story requires it

- manufacturing intelligence;
- subcontractor intelligence;
- predictive maintenance;
- advanced demand forecasting;
- industry-specific ML models.

---

# 4. Computation Classes

Every feature must declare one or more computation classes:

```text
deterministic
statistical
ml_predictive
llm_orchestration
llm_explanation
hybrid
```

Rules:

1. If deterministic code can produce the authoritative number, use deterministic code.
2. Statistical/ML components may estimate uncertain behavior, but must never silently overwrite observed facts.
3. LLM output is narrative/orchestration output, not authoritative financial state.
4. P0 must work without custom model training.

---

# 5. AI-F001 — Financial Health Analyst

## 5.1 User value

Example questions:

- Why did cash decrease while revenue increased?
- Why did gross margin decline?
- What is driving working-capital pressure?
- Which KPI changed most this month?

## 5.2 Computation

```text
deterministic KPI engine + LLM explanation
```

No custom training is required.

## 5.3 Required trusted data

Minimum:

- period revenue;
- expense / COGS where available;
- cash balance or validated cash proxy;
- AR total and overdue AR;
- AP total and near-term AP;
- period/currency/company;
- source/evidence metadata.

Optional:

- inventory value;
- customer/supplier concentration;
- previous-period comparisons.

## 5.4 Authoritative calculations

Candidate P0 metrics:

- revenue change;
- gross margin if source supports it;
- AR outstanding;
- overdue AR ratio;
- AP outstanding;
- working-capital indicators;
- cash runway only when required obligations exist.

Every metric must have:

```text
metric_id
value
currency_or_unit
period
formula_version
snapshot_id
evidence_refs[]
```

## 5.5 AI responsibility

Allowed:

- explain movements;
- compare periods;
- summarize material drivers;
- answer grounded follow-up questions.

Forbidden:

- invent missing ratios;
- use guessed denominator;
- calculate a different value from the Finance Engine;
- hide missing-data limitations.

## 5.6 P0 acceptance

- 100% material numeric match against gold fixtures;
- every material statement traceable to a metric/evidence source;
- insufficient data returns an explicit limitation, not a fabricated conclusion.

---

# 6. AI-F002 — Cash-flow Forecast Copilot

## 6.1 Critical correction to current code

Current `predict_cashflow` behavior based on `AR - AP` must **not** be presented as cash-flow forecasting.

A valid scheduled forecast requires at minimum:

```text
opening cash
AR with due dates / collection assumptions
AP with due dates / settlement assumptions
future obligations
forecast horizon
as_of cutoff
```

Where available, future obligations include:

- payroll;
- recurring OPEX;
- tax;
- debt service;
- planned capex.

## 6.2 P0 computation

```text
deterministic scheduled projection
```

ML is not required for P0.

Conceptual equation:

```text
Projected Cash[t]
= Opening Cash
+ actual/expected inflows up to t
- actual/expected outflows up to t
```

Revenue must not be treated as cash receipt. Expense recognition must not be treated as cash payment.

## 6.3 Output contract

```text
forecast_id
snapshot_id
company
as_of
horizon
method
assumptions[]
series[]
shortfall_events[]
missing_inputs[]
limitations[]
version
```

## 6.4 Fail-safe behavior

If a required source/report fails or a critical input is missing:

```text
status = INSUFFICIENT_DATA
```

Never convert report failure into zero and then conclude `LOW` risk.

## 6.5 AI responsibility

Allowed:

- explain when/why cash falls;
- answer "what changed?";
- ask for missing assumptions;
- route a user into a what-if scenario.

Forbidden:

- silently choose unknown opening cash;
- infer cash settlement from invoice status without rule/evidence;
- claim a probabilistic forecast when only scheduled arithmetic is used.

---

# 7. AI-F003 — Risk Signal Agent

## 7.1 Principle

`RiskSignal != fraud conclusion`  
`RiskSignal != credit decision`

P0 should be rule/evidence first.

## 7.2 P0 signal catalog

Candidate signals:

```text
AR_OVERDUE_SPIKE
AP_DUE_CLUSTER
CUSTOMER_CONCENTRATION
SUPPLIER_CONCENTRATION
MARGIN_DROP
EXPENSE_SPIKE
SALES_DECLINE
INVENTORY_CASH_LOCK
CASH_SHORTFALL
COLLECTION_DELAY
```

Implement only signals whose source fields are verified.

## 7.3 RiskSignal contract

```text
signal_id
company
signal_type
severity
metric_name
baseline_value
current_value
threshold
as_of
rule_version
evidence_refs[]
status
```

## 7.4 AI responsibility

- explain the signal;
- prioritize based on deterministic severity and business context;
- propose allowed next analyses;
- never state "fraud" or "will default" without a valid separate model/evidence basis.

---

# 8. AI-F004 — What-if Scenario Agent

## 8.1 User value

Examples:

- What if sales drop 20%?
- What if Customer A pays 15 days late?
- What if payroll rises 10% next quarter?
- What if we borrow 300M for 12 months?

## 8.2 Architecture

```text
Natural language
    ↓
LLM intent parsing
    ↓
validated typed Scenario
    ↓
deterministic Scenario Engine
    ↓
structured result
    ↓
LLM explanation
```

## 8.3 Scenario schema

```text
scenario_id
company
base_snapshot_id
scenario_type
parameters
created_by
created_at
version
data_mode = simulation
```

P0 parameters may include:

```text
sales_change_pct
collection_delay_days
supplier_due_shift_days
refund_change_pct
payroll_change_pct
opex_change_pct
one_off_expense
financing_amount
financing_terms
```

## 8.4 Safety

Scenario outputs must never mutate actual ERPNext records.

Every result must visually and structurally carry:

```text
data_mode = simulation
```

---

# 9. AI-F005 — Financing Decision Support

## 9.1 Scope

P0 performs **read-only matching** against an approved financing catalog.

No bank submission.
No loan approval prediction.
No hidden underwriting inference.

## 9.2 Catalog requirements

```text
provider
product_name
amount_min
amount_max
currency
rate_type
rate_or_range
term_min
term_max
fees
public_eligibility
source_ref
source_as_of
verified_at
ttl
status
```

## 9.3 Matching logic

P0 can use:

- amount/term filters;
- published eligibility rules;
- business needs;
- repayment capacity metrics;
- transparent weighted criteria if versioned.

AI may explain why a product matches, but the system must show:

- source;
- missing criteria;
- stale status;
- assumptions.

---

# 10. AI-F006 — Repayment / Stress Simulation

## 10.1 Computation

```text
deterministic
```

Required inputs:

```text
principal
currency
rate_type
rate
term
payment_frequency
fees
fee_timing
amortization_method
rounding_rule
```

Supported P0 methods may be limited to the smallest set the team can verify, for example:

- equal principal and interest / standard amortized schedule;
- flat-rate schedule only if explicitly labelled and independently tested.

## 10.2 Output

```text
schedule_id
scenario_id
payment_schedule[]
total_interest
total_fees
total_repayment
cashflow_impact[]
assumptions[]
```

## 10.3 Evaluation

Independent hand-worked/gold cases must exist. The production calculator must not generate its own test oracle.

---

# 11. AI-F007 — Financial Copilot Orchestrator

## 11.1 Build order

The Copilot is P0 for the final competition experience, but should be implemented **after** the deterministic financial tools are correct.

## 11.2 Allowed P0 tools

Conceptual allowlist:

```text
get_financial_health
get_cashflow_forecast
get_risk_signals
run_scenario
match_financing_options
simulate_repayment
get_evidence
```

Each tool must have:

- typed input schema;
- explicit company/resource scope;
- backend permission check;
- bounded output;
- audit event;
- safe error contract.

## 11.3 Copilot contract

The Copilot may:

- understand intent;
- ask clarifying questions only when required inputs cannot be derived safely;
- call allowed read/simulation tools;
- explain structured results;
- cite evidence/period/as-of;
- disclose limitations.

The Copilot must not:

- select an arbitrary company supplied only by prompt text;
- access the database directly;
- call arbitrary URLs;
- post accounting records;
- submit financing applications;
- modify ERPNext financial truth;
- override permission checks;
- alter authoritative numeric results.

---

# 12. P1 Feature Definitions

## AI-F101 — Customer Payment Behavior

P0/P1 descriptive fields:

```text
invoice_date
due_date
actual_settlement_date
amount
paid_amount
days_past_due
partial_payment_count
customer_history_cutoff
```

Current code lacks verified settlement history; therefore predictive timing remains `DATA_GAP` until runtime/schema verification.

## AI-F102 — Sales / Revenue Trend Intelligence

Start with deterministic/statistical trend and period comparison.

ML forecasting is optional and only justified if:

- time coverage is sufficient;
- target is explicitly defined;
- temporal split exists;
- naive baseline exists;
- leakage checks pass.

## AI-F103 — Supplier Intelligence

Possible deterministic features:

- purchase concentration;
- AP concentration;
- payment terms;
- price changes;
- delivery reliability only if real source fields exist.

Do not fabricate supplier performance from Olist or missing ERP data.

## AI-F104 — Inventory Cash-Risk Intelligence

Candidate fields:

```text
qty_on_hand
inventory_value
stock_age
sales_velocity
turnover
last_sale_date
```

P0 rules/statistics before ML.

## AI-F105 — OCR / Document Intelligence

Only activate when UC001 upload is in the demo scope.

Output is always `candidate`, never `trusted`, until validation/reconciliation/review.

---

# 13. Feature-to-UC Mapping

| Feature | Primary UC | Supporting UC |
|---|---|---|
| AI-F001 Health Analyst | UC003 | UC009, UC006 |
| AI-F002 Cash Forecast | UC004 | UC005, UC006, UC009 |
| AI-F003 Risk Signals | UC005 | UC003, UC004, UC009 |
| AI-F004 What-if | UC008 / UC006 | UC004, UC005 |
| AI-F005 Financing Support | UC007 | UC004, UC006, UC008 |
| AI-F006 Repayment Simulation | UC008 | UC004, UC007 |
| AI-F007 Copilot | UC006 | UC003–UC008 |
| AI-F101 Payment Behavior | UC005 | UC004 |
| AI-F102 Revenue Trend | UC003/005 | UC004 |
| AI-F103 Supplier Intelligence | UC005 | UC004 |
| AI-F104 Inventory Cash Risk | UC005 | UC003/004 |
| AI-F105 OCR | UC001 | UC003–UC006 downstream |

---

# 14. Feature-Level Evaluation

| Feature | Minimum P0 evidence |
|---|---|
| Health metrics | 100% material numeric gold |
| Health explanation | all material claims grounded |
| Cash forecast | gold cash path + shortfall detection + missing-input tests |
| Risk signals | benign/positive/inconclusive fixtures; false-positive tracking |
| Scenario | 100% material deterministic match |
| Financing matching | criteria relevance + source/as-of/TTL |
| Repayment | independent schedule gold |
| Copilot | tool selection, numeric fidelity, company isolation, injection tests |

---

# 15. P0 Demo Story

A recommended final demonstration:

```text
1. Owner opens Lotus Fin inside ERPNext/Frappe.
2. System loads an authorized Financial Snapshot.
3. Health Analyst highlights working-capital pressure.
4. Forecast shows a shortfall within 30 days.
5. Risk Agent explains overdue AR / AP cluster / concentration evidence.
6. Owner asks Copilot: "What if Customer A pays 15 days late?"
7. Scenario Engine recomputes the path.
8. Copilot shows read-only financing options with source dates.
9. Owner simulates a 300M financing option.
10. Repayment Engine shows impact on future cash.
11. AI explains; human decides. No bank submission occurs.
```

This demonstrates AI interaction without giving the LLM financial or authorization authority.

---

# 16. Out of Scope for MVP

- autonomous underwriting;
- loan approval probability;
- real bank submission;
- real money movement;
- generic ERP copilot for every ERPNext module;
- custom ML forecast without validated labels;
- autonomous accounting posting;
- unrestricted agent plugins/MCP;
- direct LLM database access.

---

# 17. Implementation Dependency Order

```text
Runtime / permission verification
        ↓
Secure ERPNext adapter
        ↓
Financial Snapshot + Evidence
        ↓
Deterministic Finance Engine
        ↓
Health / Forecast / Risk
        ↓
Scenario + Repayment + Financing
        ↓
Bounded Copilot
        ↓
P1 intelligence / ML only if justified
```

This order is normative for the MVP unless an ADR explicitly changes it.
