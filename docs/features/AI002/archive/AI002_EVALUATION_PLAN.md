# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI002 evaluation plan

> **AI002-00B update:** [Gold manifest](../AI002_GOLD_FIXTURE_MANIFEST.yaml) now independently derives a **11,550,000 VND** ledger opening from a dedicated, synthetic 2026 ERPNext transaction fixture and enumerates 30 internal EOD arithmetic points. There are no eligible confirmed future cash-date events, so expected service/UX state is `FORECAST_UNAVAILABLE` with no rendered forecast line or shortfall event. Runtime observed partial/full payments and stale positive Payment Schedule amounts after settlement. This is **fixture gold, not a passing engine evaluation**; AI002 engine, full failure matrix, evidence/cache E2E, credit/transfer/advance/cancel/FX and live model fallback remain `NOT_RUN`. Threshold equality tests are conditional on Finance/Product approval; until then assert no shortfall claim. This update supersedes the older statement below that no independent gold existed.

**Status:** proposed, no AI002 forecast evaluation executed. Separate numeric correctness, conditional timing quality and explanation quality. P0 is deterministic scheduled projection only.

## 1. Deterministic correctness

Independent Decimal gold ledger for each daily point: opening cash + eligible dated inflows − eligible dated outflows, with same-day ordering/cutoff, currency/rounding, threshold-crossing date, deduplication and evidence IDs. Check reconciliation of opening cash to GL/Trial Balance and invoice outstanding after allocations/credits. Test verified zero versus missing/error; negative and zero cash; no due date; partial/advance payments; draft/cancelled/future invoices; overdue items; multiple currencies/missing FX; account/book variation; source timeout; mixed dict/list/summary rows; period/year boundary, timezone and backdated posting. Run unauthorized company/report/filter and stale-company-switch tests separately.

P0 **mandatory**: independent Decimal gold, opening cash reconciliation, every daily point, first shortfall date after an approved threshold exists, threshold equality boundary, same-day ordering, verified zero versus missing, partial/advance payment, credit note, cancelled/future/overdue invoices, duplicate/order/invoice schedules, mixed dict/list/summary rows, multi-currency/missing FX, timezone/year boundary/backdated posting, source timeout, company isolation, filter tampering, stale company switch and evidence integrity. Explicitly test that a settled invoice with a positive original Payment Schedule contributes zero future cash. Test coverage classifications (`TRADE_ONLY`, `OPERATING_CORE`, `COMPREHENSIVE`) and missing/unverified categories. If threshold remains `NOT_FROZEN`, assert shortfall events are unavailable rather than guessing a boundary.

Fixture sources: (1) existing ERPNext demo transactions with sanitized manifest, (2) controlled synthetic **valid ERPNext transactions** in a test site: submitted Sales/Purchase Invoices, Payment Entries and allocations, credit notes, bank/cash postings and due dates. Do not seed direct `cash=X`, `AR=Y`, `AP=Z` without generating accounting events. Capture site/version, fixed as-of, transaction IDs in a protected manifest, expected balances and independent calculation. Include an empty company fixture and a company with different chart/currency. Synthetic stays labeled test/demo, never actual live business data.

## 2. Forecast quality — conditional on estimated timing

**Rolling-origin backtests and confidence intervals are mandatory only when estimated settlement/statistical timing is enabled.** For a pure deterministic schedule, historical replay is supplementary if point-in-time data are available; lack of enough history for confidence intervals alone does not block that MVP. If estimation is enabled, use rolling-origin cutoffs on historical snapshots. At each cutoff, features include only data visible then; later settlements and reversals are held out as outcomes. Freeze horizon and obligation coverage per experiment. Compare against actual daily closing cash only where actual cash and obligations are complete. Segment by company, horizon, input coverage and positive/negative opening cash. A missing source invalidates a comparison, not a zero error.

When estimated timing is enabled, primary SME metrics are shortfall **recall** (missed pressure is costly), **precision** (false alarms consume attention), first-shortfall date error, and absolute cash path error in currency units. Report counts and denominators. MAE supports interpretability; RMSE highlights severe misses but is outlier-sensitive. **MAPE is not a mandatory metric** at zero/negative cash; SMAPE can be supplementary and unstable near zero. Directional accuracy is secondary. Threshold and acceptable values require Finance/Product sign-off. Assess alert utility against a carry-forward opening-cash baseline, and record source-coverage rate alongside accuracy.

## 3. Explanation quality

Use a fixed typed forecast payload and gold facts/evidence. Assert no numeric override, invented obligation or certainty about collection timing; evidence access is company-scoped; facts, interpretations, limitations and next checks remain separate. Include prompt injection in invoice descriptions, model timeout, malformed schema and company-switch race. Human finance reviewer grades usefulness and omissions on representative cases; record prompt/model/version and disagreement. If no live provider is configured, mock tests can validate schema/fallback but **cannot** pass live-provider quality.

## Gate evidence

Before implementation approval: freeze threshold or explicitly disable shortfall claims, source scope/coverage and gold manifest; demonstrate as-of data extraction and non-admin permission checks. Before release: deterministic tests, runtime reconciliation, security matrix, explanation review, UI E2E, telemetry/redaction and fallback evidence. Add rolling-origin report with counts/confidence intervals **only if estimated timing is enabled**. Current result: `NOT_RUN`; no AI002 numeric quality claim. The 2020-12-31 demo GL↔Trial Balance reconciliation is runtime evidence, not a forecast test suite.


