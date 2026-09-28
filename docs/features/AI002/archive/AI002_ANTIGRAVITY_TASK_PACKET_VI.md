# SUPERSEDED

Current SSOT: [AI002_MASTER_SSOT_V1.md](../AI002_MASTER_SSOT_V1.md)

This file is retained for historical evidence only. Do not use it for current implementation decisions.

---

# AI002 — Antigravity discovery-to-build task packet

> **AI002-00B handoff (current):** [00B report](AI002_00B_CONTROLLED_FIXTURE_AND_GATE_CLOSURE_REPORT.md) and [gold manifest](../AI002_GOLD_FIXTURE_MANIFEST.yaml) supersede the older gate status and “fixture missing” tasks below. Dedicated local test company has 2026 transaction-backed synthetic fixture and reconciled Cash 11,550,000 VND; no confirmed future cash date. All four gates remain `PARTIAL`; next action **Continue AI002-00B**, not implementation.

## Data instruction for Antigravity — from the user

**Prioritize real operational data with clear provenance.** First inspect authorized ERPNext records and ask the data owner for current, sanitized business transactions and off-ERP obligation inventory. When crawling public material, record original URL, publisher, access date, license/terms, exact field meaning and whether redistribution is allowed. Use public data only for research, benchmarking or fixture realism; public macro statistics are **not** company accounting truth. Never crawl private data, bypass access controls, or treat a scraped dataset as Lotus Fin's cash, AR/AP or commitments. If real authorized data are unavailable, use valid ERPNext transactions on the approved test site, label every record and output `SYNTHETIC_TEST_ONLY`, and never call those amounts real SME finances. Keep actual, forecast and simulation separate. The 2026 fixture here is synthetic/test even though its GL and invoices are real submitted ERPNext documents.

**Current technical boundary:** strict P0 baseline includes opening cash plus separately evidenced future confirmed cash dates/verified settlement schedules; invoice due date stays an obligation. Due-date estimated overlay is P1 or an explicit Finance/Product decision, with separate UX/evaluation. No shortfall claim until threshold approval. Confirm accounting timezone and scope; normalize denial without requested company name. Complete credit/advance/internal transfer/cancel/backdating, evidence/cache/company-switch and logging-canary tests. `predict_cashflow` remains excluded from UI/agent tools.

**Status:** `HOLD_FOR_GATES`. This packet is a handoff checklist, **not authorization to implement AI002**. Governing freeze: [AI002 feature freeze](AI002_FEATURE_FREEZE_VI.md). User asked to stop after discovery/contract.

## Task 0 — clear discovery blockers

1. Site identity, timezone and historical 2020 reconciliation are recorded in [AI002 runtime discovery report](AI002_RUNTIME_DATA_DISCOVERY_REPORT.md). Obtain a **current** transaction-backed test fixture with dated future commitments; record site/app revision and source coverage rather than treating 2020 demo data as a 2026 forecast.
2. Complete a lower-privilege authorized/denied role matrix for cash, AR/AP, Payment Entry/Ledger, future-obligation sources and evidence. Current controlled test used a non-Administrator with broad System Manager rights and a rolled-back User Permission. Check account permissions, arbitrary DocType, cache and company-switch race.
3. Verify cutoff precision, report empty/error behavior, partial payment, advances, credit notes, cancellation, backdating, multi-schedule invoices, order→invoice overlap, FX and finance-book variation. Reconcile a fresh current opening cash and AR/AP snapshot; inventory business obligations beyond ERP. Update [runtime facts](AI002_RUNTIME_FACTS.md) and [source map](AI002_DATA_SOURCE_MAP.md) with sanitized evidence.
4. Finance/Product approves P0 coverage scope (`TRADE_ONLY`, `OPERATING_CORE`, or `COMPREHENSIVE`), shortfall threshold or its disabled state, cash-account policy and supported data horizon. Security approves source allowlist, generic denial and role matrix. QA produces independent transaction-backed gold and as-of snapshots.
5. Update freeze/contract only from evidence. Reassess four gates; proceed to build only when all mandatory gates PASS.

## Conditional implementation packet after gate PASS

Build a company-scoped, allowlisted source adapter with exact filters; normalize Decimal, dates and currencies; reconcile opening cash; deduplicate remaining obligations and posted payments; compute daily deterministic points and shortfall events with source coverage. Add versioned evidence refs and typed failures. Add optional minimized/grounded LLM explanation with deterministic fallback. Expose a dedicated workspace and reauthorized evidence drilldown. Add correlation-linked redacted telemetry. Keep AI004 simulation separate. Never reuse deprecated `predict_cashflow` AR−AP computation or expose a `LOW` liquidity label from it.

## Acceptance evidence required

Independent gold for cash path and first shortfall date **after threshold approval**; empty/missing/error and all edge cases in [evaluation plan](AI002_EVALUATION_PLAN.md); lower-privilege cross-company and filter tampering tests; live role-safe report/DocType access; as-of leakage check; UI states and evidence flow E2E; redaction/fallback. Rolling-origin quality report is required **only if estimated/statistical timing is enabled**. Record commands/results, revision, environment, sample sizes, unresolved conflicts and owner sign-off. Do not call mock-provider tests a live-provider pass.

## Current handoff decision

Gate 1 `BLOCKED`; Gate 2 `PARTIAL`; Gate 3 `BLOCKED`; Gate 4 `PARTIAL`. Recommendation `AI002_PARTIAL`; next action **continue AI002-00 discovery**. Next owners: ERP runtime/data scout for current dated fixture and source semantics, Finance/Product for scope/threshold, Security and QA for restricted-role and gold evidence. This packet remains `HOLD_FOR_GATES`; do not start AI002-01 contract freeze or implementation until the blocking facts are resolved.


