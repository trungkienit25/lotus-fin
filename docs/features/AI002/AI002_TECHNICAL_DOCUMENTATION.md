# AI002 Cash-flow Forecast Copilot — Technical Documentation

## 1. System Overview & Architecture

The **AI-F002 Cash-flow Forecast Copilot** provides a deterministic 30-day daily EOD cash forecast with bounded agentic AI explanation, built on ERPNext/Frappe.

### Governing Architectural Invariant
> `ERP truth → deterministic policy → deterministic finance → typed evidence → bounded agent → grounded explanation`

The Large Language Model (LLM) never computes, estimates, or alters financial numbers. Financial truth is strictly computed in-memory using Python `Decimal` arithmetic.

---

## 2. Core Components

### 2.1 Data Models & Types (`models.py`)
- **`ForecastRequest`**: Strictly validated typed parameters including `company`, `financial_as_of`, `forecast_start`, `forecast_end`, `reporting_currency`, and `coverage_scope` (`TRADE_ONLY`).
- **`ForecastResponse`**: Formal envelope returning `status`, `opening_cash`, `forecast_points`, `obligations`, `cash_events`, `coverage`, `shortfall_events`, `explanation`, and `evidence_refs`.
- **`OpeningCash`**: Aggregated cash & bank balance reconciled with Trial Balance, tracking `has_constituent_deficit`.
- **`ShortfallEvent`**: Explicit tracking of negative modeled cash (`INHERITED_FROM_OPENING` vs `NEW_MODELED_DEFICIT`).

### 2.2 Deterministic Forecast Engine (`engine.py`)
- $O(N)$ in-memory daily running sum:
  $$\text{modeled\_cash}(EOD_t) = \text{opening\_cash} + \sum \text{inflows}_{\le t} - \sum \text{outflows}_{\le t}$$
- Evaluates exactly 30 calendar days.
- Implements the Shortfall State Machine (distinguishing inherited deficits from newly modeled negative balances).

### 2.3 Data Adapters & Sources (`adapters.py`, `source_interface.py`)
- **GL Opening Cash**: Single SQL query window over `tabGL Entry` filtered by authorized company and posting date.
- **Trade Obligations**: Query over `Sales Invoice` (AR) and `Purchase Invoice` (AP) with contractual due dates and outstanding balances. Party names are pseudonymous hashes (`SHA256[:12]`).
- **Future Settlement Events**: Uses `FutureEventSource` abstract interface. Defaults to `FailClosedSource` (returning `FORECAST_UNAVAILABLE` with `NO_CONFIRMED_SETTLEMENT_EVENTS` when no confirmed settlement events exist). `SyntheticFixtureSource` is provided for test/evaluation suites.

### 2.4 Bounded Agentic Copilot (`agent.py`, `tools.py`, `grounding.py`)
- Bounded read-only architecture with 6 allowlisted tools:
  - `cash_forecast.get`
  - `cash_forecast.get_coverage`
  - `cash_forecast.get_obligations`
  - `cash_forecast.get_drivers`
  - `cash_forecast.get_evidence`
  - `cash_forecast.get_missing_inputs`
- **Security & Safety Controls**:
  - 5000ms circuit breaker on model invocations.
  - Strips free-text (`remarks`, `notes`, `description`) to neutralize indirect prompt injection.
  - Grounding validator verifies that claims match deterministic financial facts.
  - Deterministic Next-Checks allowlist with ERPNext deep links (`RECONCILE_BANK_TRANSACTIONS`, `FOLLOW_UP_OVERDUE_AR`, etc.).

### 2.5 Security, Hardening & Observability (`access.py`, `observability.py`, `cache.py`)
- Server-side company authorization check (`get_verified_company`).
- Compile-time report allowlist (`General Ledger`, `Accounts Receivable`, `Accounts Payable`).
- Re-authorization of evidence drilldowns (`verify_evidence_access`).
- Zero-PII structured JSON audit logging (`log_ai002_event`) with sentinel canary verification.
- Compound SHA256 cache key with 300s TTL and single-flight concurrency lock.

---

## 3. API Contract Reference

### REST Endpoint
`POST /api/method/lotus_fin.api.ai_insights.get_ai002_cash_forecast`

#### Parameters:
- `company` (str, required)
- `financial_as_of` (str YYYY-MM-DD, optional, default: yesterday)
- `forecast_start` (str YYYY-MM-DD, optional, default: financial_as_of + 1)
- `forecast_end` (str YYYY-MM-DD, optional, default: forecast_start + 29)
- `currency` (str, default: "VND")
- `include_explanation` (bool, default: False)
- `use_fixture_source` (bool, default: False)

---

## 4. UI Architecture (`cash_forecast.js`)

Located at Frappe Page `/app/cash-forecast`:
1. **Tier 1 (Ledger Truth)**: Opening cash card, account breakdown, 30-day daily EOD trajectory table.
2. **Tier 2 (Trade Obligations)**: AR / AP contractual due dates with pseudonymous party hashes.
3. **Tier 3 (Copilot Sidebar)**: Verified ledger facts, grounded AI interpretation, deterministic next checks, and contract limitations.
4. **Alerts**:
   - Red banner on `NEW_MODELED_DEFICIT`.
   - Amber banner on `INHERITED_FROM_OPENING` or `has_constituent_deficit`.
   - Zero-leakage `FORBIDDEN` landing card on unauthorized access.
