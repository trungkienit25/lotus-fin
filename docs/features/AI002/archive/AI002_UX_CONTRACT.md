# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI002 workspace UX contract

> **AI002-00B governing UX note:** Current 2026 synthetic fixture has reconciled opening cash and dated AR/AP **obligations**, but no confirmed future cash dates. Display opening, remaining obligations, due dates, evidence and missing-source checklist; **do not plot the flat internal gold arithmetic as a 30-day forecast**. A due-date timing overlay is P1 / Finance/Product decision and must have a separate visual legend and named assumption if enabled. Daily point is EOD in a confirmed accounting timezone, not intraday. Shortfall claims are disabled pending threshold approval. See [00B report](AI002_00B_CONTROLLED_FIXTURE_AND_GATE_CLOSURE_REPORT.md). This note supersedes any implied path/demo claim below.

**Status:** proposed. Route candidate `/app/cash-forecast` as a dedicated company-level Frappe Page, subject to route/role verification. Reuse AI001 page patterns for status, evidence and escaping, not its KPI layout or fiscal-year defaults.

## Screen and journey

Header: authorized company selector, financial as-of with **site timezone**, currency/account scope, product horizon and **verified data horizon** separately, coverage scope and status/last refreshed. Summary: opening cash with evidence; when coverage is partial, label the minimum **“Lowest modeled cash within included sources”**, never “Projected lowest cash” without qualification. Show first threshold breach only after threshold approval and usable cash-date evidence; total dated inflows/outflows split by confirmed versus estimated timing. Main panel: real daily points in line and accessible table, with actual opening marker and forecast segment visually distinct; no synthetic chart interpolation. Next panels: obligations by contractual due date **separate from** cash events by expected/confirmed cash date, missing obligations and data-quality coverage, explicit assumptions, limitations, optional grounded explanation and safe next checks. Evidence drawer opens approved source records/reports after authorization recheck, with exact filters/as-of and no arbitrary report URL.

Demo flow: open Cash Forecast → select company → select provisional horizon → inspect opening cash → inspect dated commitments and estimated items → see pressure window if supported → explain drivers → open evidence. Scenario adjustments link to a separately labeled AI004 mode only when implemented; they do not mutate AI002 baseline.

## Visible states

| State | UI behavior |
| --- | --- |
| `OK` | Show full dated path, component labels, coverage and threshold with evidence |
| `PARTIAL` | Show bounded path only if valid, prominent incomplete-coverage banner, no safe/no-risk verdict; list `included_sources`, `missing_sources`, `unverified_sources` and scope |
| `INSUFFICIENT_DATA` / `FORECAST_UNAVAILABLE` | Show available actual facts and missing-input checklist; no projected line |
| `SOURCE_ERROR` / `TIMEOUT` / `INCONSISTENT_DATA` | Show source-specific retry/check and preserve only independently verified facts |
| `FORBIDDEN` | Generic access message, no company names/amounts or cached prior-company data |
| `VALIDATION_ERROR` | Explain invalid field and correction without financial data |
| Model unavailable | Keep deterministic result, mark explanation unavailable, offer source-based checks |
| Verified zero | Display `0` with source/as-of; never render as “missing” |

Use distinct text and visual styles for `Actual`, `Known obligation (due date)`, `Estimated cash timing`, and `Confirmed cash date`. A known obligation is **not** a guaranteed dated cash movement. `Simulation` remains a separate AI004 view, never included in AI002 baseline. Prominent partial-coverage copy: “Incomplete obligation coverage. Payroll and tax schedules are not verified. This path must not be interpreted as a complete liquidity forecast.” Adapt category names to actual missing sources. If no future cash date is verified, show obligations and missing-data checklist rather than a fabricated line. With `SHORTFALL_THRESHOLD=NOT_FROZEN`, show no shortfall/risk badge. Currency and dates must be localized without changing stored Decimal values. Table labels, keyboard access, focus, contrast and screen-reader summaries are acceptance criteria. Render all source/model text escaped. Cancel or ignore stale async responses after company/filter changes; clear old sensitive content while loading. On every risk statement show threshold, horizon, input coverage and limitation.


