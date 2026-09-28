# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI002 method and horizon options

> **AI002-00B semantic decision (PROPOSED, supersedes ambiguous table wording below):** P0 technical default is **Option A strict deterministic baseline**: reconciled opening cash plus future `CONFIRMED_CASH_DATE` or a `VERIFIED_SCHEDULE` whose **cash settlement semantics** are proven. A Sales/Purchase Invoice or Payment Schedule contractual due date stays in the obligations layer and contributes no baseline cash event. A due-date estimated overlay is P1 unless Finance/Product explicitly approves it for P0 with a named assumption, separate UI line and temporal evaluation. Option C, if ever selected, must be called an **estimated due-date cash path**. The local 2026 fixture has no confirmed future cash date, so its flat arithmetic points are internal gold only, not a renderable forecast. See [00B report](AI002_00B_CONTROLLED_FIXTURE_AND_GATE_CLOSURE_REPORT.md). The old phrase “remaining invoice obligations” in Option A is superseded by this paragraph.

**Decision after AI002-00 discovery:** retain deterministic scheduled projection for P0, with explicit coverage and assumptions. No model-generated financial numbers. On the 2026-09-26 demo site, all surviving AR/AP due dates and all Payment Schedule dates are in 2020; no verified future cash date supports a 2026 path. Method choice is a design decision, not data readiness.

| Option | Data / ground truth | Explanation / robustness | Leakage, complexity, cost | Decision |
| --- | --- | --- | --- | --- |
| A. Deterministic scheduled cash | Opening cash, dated confirmed commitments and remaining invoice obligations | Highest traceability; good baseline but incomplete source coverage limits conclusions | Low compute cost; leakage controlled by as-of | **P0 candidate** once sources and cutoff verified |
| B. Rule-based expected settlement | A plus approved due-date/delay rules | Can show estimated AR/AP, but timing can be falsely precise | Moderate calibration burden; requires explicit assumptions and validation | P1 or optional clearly labeled estimated layer |
| C. Statistical payment-delay model | Sufficient point-in-time invoice/payment history and settlement labels | May improve timing; uncertain for sparse, changing SME data | High leakage/sample risk, backtest burden | Defer |
| D. Hybrid schedule + empirical delay | A plus reliable historical distribution by segment | Potentially more realistic, but coverage and confidence intervals needed | More complex governance and drift monitoring | Defer |
| E. ML predictive forecast | Broad high-quality history, temporal labels, baseline improvement | Hardest to explain and audit | Highest data, leakage, operations and cost burden | Exclude P0 |

No empirical evidence yet shows B–E improve SME shortfall detection over A. Competition value comes from a useful timeline, evidence, honest gaps and safe checks, not from claiming an ML forecast.

## P0 arithmetic and classification

For each daily point `t`: `modeled_cash(t) = opening_cash(as_of) + Σ eligible dated cash inflows(as_of < date ≤ t) − Σ eligible dated cash outflows(as_of < date ≤ t)`. Use Decimal, one verified reporting currency and stable account/book scope. Posted payments through as-of belong in actual/opening state and must not be scheduled again. **Obligation due date ≠ cash settlement date.** An invoice due date may support a separately labeled estimated timing assumption, never a confirmed cash date. The site's Payment Schedule retains original positive amounts on five fully settled invoices and includes order plus invoice schedules; use remaining AR/AP and deduplicate parent chains before any schedule can enter a cash path. Overdue items require explicit treatment; do not shift silently to tomorrow. Show excluded obligations and coverage before any shortfall or safety claim. A zero scheduled inflow is not proof no cash will arrive.

## Horizon comparison

| Horizon | Use | Data burden / confidence | P0 choice |
| --- | --- | --- | --- |
| 7 days | Immediate payment checks | Lowest timing uncertainty; may miss monthly payroll/AP | Useful later |
| 14 days | Two-week operations | Still misses some month-end events | Useful later |
| 30 days | SME monthly liquidity planning and demo timeline | Covers common cycles; requires obligation coverage and dated inputs | **Provisional default**, daily points |
| 60 days | Longer planning | More missing obligations and timing uncertainty | P1 only after validation |
| 90 days | Quarter view | Sparse inputs make precise daily path misleading | Defer |

The 30-day selection matches the user's provisional question and offers useful monthly coverage. It is **not frozen as production-ready** until runtime coverage, thresholds, timezone and validation pass. As of 2026-09-26, the verified future cash-date horizon is **none**, so even a 14-day path is unsupported by current demo data. A shorter bounded path can be shown only if later evidence supports it. Configurable horizons belong to P1 and require horizon-specific quality evidence. Statistical/hybrid/ML timing needs historical settlement labels, point-in-time correctness, leakage controls and repeatable improvement over this baseline; none has been shown.


