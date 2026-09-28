# AI002 IMPLEMENTATION TASK PACKET — ANTIGRAVITY

## Lotus Fin — AI-F002 Cash-flow Forecast Copilot

**Status:** `AI002_G4B_REMEDIATION_PASSED`

The AI002-01 Contract Freeze review is **COMPLETED & FROZEN** (governed by `AI002_MASTER_SSOT_V1_2_1_REFINED.md` v1.2.1 and `AI002_DECISION_LOG_CONTRACT_FREEZE_REFINED.md`). G4B Remediation has been fully verified and passed (15/15 pure-Python, 86/86 Docker container tests).


---

# 1. Governing sources

Implementation authority:

```text
AI002_MASTER_SSOT_V1.md
AI002_GOLD_FIXTURE_MANIFEST.yaml
```

Archived AI002 documents are historical only.

---

# 2. Non-negotiable implementation rule

High-risk logic must be deterministic.

LLM/Agent must never own:

```text
authorization
financial arithmetic
cash truth
AR/AP residual
currency conversion
source trust
coverage policy
shortfall rule
failure state
PII redaction
cache isolation
write actions
```

Agent may only:

```text
understand intent
select allowlisted read-only tools
explain deterministic results
summarize authorized evidence
suggest next checks
```

---

# 3. Implementation phases

## AI002-02 — Forecast Data Foundation

Build:

- typed request models;
- typed response models;
- authorized company scope;
- explicit Cash/Bank account-set validation;
- GL opening-cash adapter;
- Trial Balance reconciliation;
- AR adapter;
- AP adapter;
- Payment Entry/Ledger reconciliation;
- obligation normalization;
- source/provenance model;
- evidence refs;
- coverage object;
- deterministic error taxonomy;
- typed future-event source interface/provenance boundary and test-fixture adapter.

**Amendment A1 — future commitment source boundary:** AI002-02 must **not** create a production `Lotus Cash Commitment` DocType merely to obtain forecast events. If no approved production settlement-date source exists, preserve `CONFIRMED_FUTURE_EVENT_SOURCE=NOT_VERIFIED` and fail closed. A production commitment model requires a separate approved data/source/security contract.

Do NOT build LLM code in this phase.

### Acceptance

- Decimal only for financial arithmetic;
- company scope enforced server-side;
- compile-time report allowlist enforced: `AI002_PERMITTED_REPORTS = ("General Ledger", "Accounts Receivable", "Accounts Payable")` (CG-SEC-02);
- strict calendar-date filtering (`posting_date <= financial_as_of`) in `Asia/Ho_Chi_Minh`, isolated from Docker UTC system clocks (OBJ-AI002-01, CG-REL-02);
- intraday ledger detection: append `INTRADAY_UNCLOSED_LEDGER` to limitations when `financial_as_of == today()` (OBJ-AI002-09, CG-REL-02);
- multi-account constituent overdraft detection: populate `accounts[]` and set `has_constituent_deficit: true` if any leaf account balance is negative (OBJ-AI002-08, CG-REL-04);
- verified residual reconciliation: `Invoice.outstanding_amount` is authoritative after payment/credit reconciliation; fully settled invoices contribute zero; **do not infer FIFO installment residuals** from Payment Schedule unless explicit schedule-level allocation semantics are verified (OBJ-AI002-03 Amendment A1);
- missing/error never becomes zero;
- settled Payment Schedule does not re-enter future cash;
- due date remains obligation timing;
- typed no-future-event input is representable with `reason_code: NO_CONFIRMED_SETTLEMENT_EVENTS` (OBJ-AI002-04, CG-OPS-01);
- cryptographic compound cache key enforced: `SHA256(user:company:as_of:accounts:scope:version)` with 300s TTL and single-flight lock (CG-SEC-01, CG-PERF-03);
- primary API response caps `cash_events[]` to top 100 items with aggregated unlisted count/amount (CG-PERF-02);
- arbitrary report/DocType is impossible;
- generic FORBIDDEN preserved;
- source evidence traceable.

---

## AI002-03 — Deterministic Forecast Engine

Build the strict P0 engine:

```text
opening cash
+ eligible confirmed future inflows
- eligible confirmed future outflows
→ daily EOD modeled cash
```

P0:

```text
TRADE_ONLY
30 calendar days
daily EOD
Asia/Ho_Chi_Minh contract
strict confirmed/scheduled settlement timing
```

Implement:

```text
NEGATIVE_MODELED_CASH
iff modeled_cash < 0
```

No subjective risk bands.

### Engine performance & architecture (CG-PERF-01)
- Forbid daily SQL query loops.
- Mandate single window query for opening cash (`posting_date <= financial_as_of`) and single window query for future events (`event_date BETWEEN start AND end`).
- Compute daily cumulative balances for all 30 points in-memory using $O(N)$ Python `Decimal` running sums.

### Shortfall mathematical state machine (OBJ-AI002-02, CG-REL-03)
- If `opening_cash < 0`: set `opening_cash_deficit: true`; record `first_date: forecast_start` with `breach_kind: INHERITED_FROM_OPENING`.
- If `opening_cash >= 0` and cash drops below zero on day $T$: record `first_date: T` with `breach_kind: NEW_MODELED_DEFICIT`.
- For oscillatory paths, report earliest crossing (`first_date`), global minimum date (`minimum_date`), and global minimum cash value (`minimum_modeled_cash`).

### Required behavior

No eligible future event:

```text
status: FORECAST_UNAVAILABLE
reason_code: NO_CONFIRMED_SETTLEMENT_EVENTS
forecast_points = []
```

Valid bounded path under `TRADE_ONLY` scope (OBJ-AI002-05, CG-OPS-01):

```text
status: PARTIAL
coverage:
  scope: TRADE_ONLY
  completeness: PARTIAL
  unverified_obligations: ["PAYROLL", "TAX", "DEBT", "RECURRING_OPEX"]
```

Model/LLM is not involved.

### Gold acceptance

Match `AI002_GOLD_FIXTURE_MANIFEST.yaml` exactly.

---

## AI002-04 — Deterministic Evaluation & Security Integration

Implement automated tests for:

- opening GL ↔ Trial Balance;
- no-future-event case;
- confirmed-event changing path;
- 30 EOD points;
- first negative date;
- zero equality boundary;
- posted-payment exclusion;
- partial/full payment;
- settled positive schedule exclusion;
- due-date-only exclusion;
- event start/end boundaries;
- negative/zero opening cash;
- verified zero vs missing;
- source timeout;
- currency mismatch;
- missing FX;
- company isolation;
- tampered filter;
- arbitrary report denial;
- generic FORBIDDEN;
- evidence authorization contract;
- PII-safe log primitive.

If an edge case cannot yet be produced in runtime, add a valid fixture or explicitly carry it into G4B. Never fabricate a pass.

---

## AI002-05 — Bounded Agentic Copilot & Grounded Explanation

Only begin after deterministic engine/tests pass.

Implement bounded read-only Agentic AI.

### Allowed tools

```text
cash_forecast.get
cash_forecast.get_coverage
cash_forecast.get_obligations
cash_forecast.get_drivers
cash_forecast.get_evidence
cash_forecast.get_missing_inputs
```

### Deterministic limits

```text
max_tool_steps = 6
max_retries = 1
per_tool_timeout_ms = 5000
overall_agent_timeout_ms = 20000
max_evidence_items = 12
max_explanation_payload_bytes = 12000
```

### Forbidden

```text
SQL
generic ERP query
generic report
generic DocType
arbitrary URL
payment/write tools
journal/accounting write
model-selected company
model financial arithmetic
policy override
silent assumptions
```

### Explanation requirements

Output typed:

```text
FACT
INTERPRETATION
LIMITATION
NEXT_CHECK
```

Every material number must reconcile to deterministic result/evidence.

### Decoupled Copilot & Sanitization Boundary (CG-REL-01, CG-SEC-05, OBJ-AI002-06, UA-TRU-01)
- **Decoupled execution & circuit breaker:** Wrap LLM in a 5000ms circuit breaker. Deterministic financial calculations execute and commit first.
- **Model failure:**
  ```text
  deterministic result survives (HTTP 200)
  explanation.status = UNAVAILABLE
  reason = LLM_TIMEOUT_OR_CIRCUIT_BROKEN
  ```
- **Free-text sanitization:** For P0, strip all free-text fields (`remarks`, `user_remarks`, `description`, `notes`) before LLM ingestion. The model receives only structured typed fields (`voucher_type`, `amount`, `posting_date`, `due_date`, `party_type`).
- **Deterministic Next-Checks allowlist (UA-ACT-01):** Constrain `next_checks` to allowlisted template codes with direct ERPNext deep-links:
  * `RECONCILE_BANK_TRANSACTIONS` (`/app/bank-reconciliation-tool`)
  * `FOLLOW_UP_OVERDUE_AR` (`/app/query-report/Accounts%20Receivable?status=Overdue`)
  * `CONFIRM_AP_PAYMENT_SCHEDULE` (`/app/purchase-invoice`)
  * `RESOLVE_UNALLOCATED_PAYMENTS` (`/app/payment-entry`)

Prompt injection in ERP text must not alter policy or tool access.

---

## AI002-06 — Cash Forecast Workspace

Build dedicated company-level workspace/page.

Display:

- company;
- accounting as-of;
- timezone;
- reporting currency;
- account scope;
- 30-day product horizon;
- verified source/data horizon;
- opening cash;
- obligations;
- confirmed cash events;
- daily path;
- coverage;
- limitations;
- technical `NEGATIVE_MODELED_CASH`;
- evidence;
- grounded explanation;
- next checks.

### Three-Tier Visual Hierarchy (UA-UX-02)
1. **Tier 1 (Ledger Truth & Baseline):** Solid neutral line for past actuals and starting cash; solid emerald line for confirmed future cash trajectory.
2. **Tier 2 (Contractual Commitments Timeline):** Contractual AR/AP invoice due dates must **never** be plotted on the main cash balance line. Display them in an Upcoming Invoices Timeline below the chart. Show authoritative invoice residual and contractual schedule rows separately; show installment-level reconciliation only when explicit allocation evidence exists, otherwise `UNAVAILABLE` (UA-ACT-02 Amendment A1).
3. **Tier 3 (Projections & Scenarios):** P1 estimated timing is a secondary dashed line (default OFF); AI004 simulations are restricted to a separate sandboxed scenario tab.

### Empty-State & Trust Guardrails (UA-UX-01, UA-UX-03, UA-TRU-02, UA-TRU-03)
- **Zero-event calm baseline:** When `reason_code: NO_CONFIRMED_SETTLEMENT_EVENTS`, display a tranquil Baseline Cash Summary showing verified opening cash and known obligations table without a fabricated chart.
- **Scope transparency:** For `TRADE_ONLY`, display a prominent header pill `[Scope: Trade Payables & Receivables Only]` and an unverified liabilities warning card.
- **Account imbalance alert:** Display an amber warning when `has_constituent_deficit == true` even if aggregate cash is positive.
- **Generic denial landing page:** On generic `FORBIDDEN`, provide a zero-leakage error landing page with "Switch Company" and "Request Access" buttons.
- **LLM failure resilience:** If `explanation.status == UNAVAILABLE`, keep all deterministic charts and tables 100% active with a green "Ledger Data Verified" badge and a retry button.

---

## AI002-07 — E2E, G4B & Acceptance

This is where G4B becomes active.

Verify:

- evidence reauthorization;
- cross-company evidence denial;
- cache isolation;
- company-switch stale-response rejection;
- generic denial at real API/UI;
- actual logging sink redaction;
- PII canary;
- deterministic API E2E;
- UI E2E;
- explanation grounding;
- unsupported numeric claim rejection;
- prompt injection;
- model timeout/fallback;
- source timeout/fallback;
- regression;
- accessibility basics;
- isolated Vietnam site timezone/date-boundary;
- authorized real-business source behavior when available.

G4B must PASS before production/release claim.

---


## AI002-08 — Feature Closure & Competition Delivery Package

Begin only after AI002-07 / G4B has reached the truthful terminal state for the intended demo/release scope.

### Mandatory feature documents

Every completed Lotus Fin AI feature must produce these **two additional final documents**:

1. `AI002_TECHNICAL_DOCUMENTATION.md`
   - system architecture and component/data-flow diagram;
   - authoritative data sources and trust boundaries;
   - core deterministic algorithm / formulas / state machine;
   - Agentic AI role and deterministic-vs-LLM boundary;
   - API/tool contracts;
   - security design summary;
   - failure/degradation design;
   - observability;
   - deployment/runtime dependencies;
   - test/evaluation summary;
   - known limitations;
   - third-party data/code/open-source components and license/provenance references;
   - repository/commit, SSOT and gold-oracle references.

2. `AI002_SECURITY_SELF_ASSESSMENT.md`
   - permission-tier implementation and role matrix;
   - company/tenant isolation;
   - source/report/tool allowlists;
   - evidence authorization and cache isolation;
   - Agent/LLM tool boundary and write-action prohibition;
   - prompt-injection controls;
   - PII/logging/redaction controls;
   - secrets/config handling;
   - security tests and execution evidence;
   - known-risk list, accepted risks, residual risks and owners;
   - G4B security status and unresolved remediation.

### Competition-submission readiness

The feature closure must also leave reusable evidence/assets for the final competition package:

- **Presentation deck:** final presentation no longer than 10 minutes. Maintain a concise feature narrative: problem → architecture → algorithm → security → measurable evidence → demo → limitations/value.
- **Demo video:** optional, no longer than 5 minutes. Keep a deterministic, repeatable demo path and clean sample data; record only authorized/synthetic data.
- **Source code:** repository-ready source with README, repository link, prerequisites, configuration, deployment instructions, fixture instructions, test commands/cases and known limitations.
- **Security self-assessment:** use the mandatory feature security document above.
- **Execution evidence:** for non-on-chain topics, retain simulated-account/sandbox operation logs and reproducible demo evidence/video; for on-chain topics, retain real transaction hashes where required.
- **IP / licensing:** entry work must be independently produced and free of plagiarism/IP infringement. Record licenses/provenance for third-party data, code, models and open-source components. Do not include assets without redistribution/use rights.
- **Competition terms traceability:** record that entry IP remains with contestants while the organizer may have the non-exclusive, royalty-free, non-commercial promotional rights described by the project owner; final interpretation remains governed by the official Competition Rules and Privacy Policy.

### Closure acceptance

Do not mark the feature `FEATURE_CLOSED` until:

```text
[ ] AI002_TECHNICAL_DOCUMENTATION.md complete
[ ] AI002_SECURITY_SELF_ASSESSMENT.md complete
[ ] README/deployment/test commands reproduce successfully
[ ] execution evidence indexed and sanitized
[ ] demo path reproducible
[ ] deck-ready feature summary available
[ ] third-party license/provenance review complete
[ ] known risks and limitations match SSOT/release evidence
```

The feature may be technically implemented before this phase, but it is not competition-delivery complete until this closure gate passes.

---

# 4. Data readiness rule

Keep separate:

```text
IMPLEMENTATION_DATA_READY
REAL_BUSINESS_DATA_READY
```

Synthetic gold may validate implementation.

It must never be presented as actual SME data.

A missing production future settlement source does not justify inventing one.

If no eligible event exists in real data:

```text
FORECAST_UNAVAILABLE
```

is correct behavior.

---

# 5. Security rules

Every external/client value is untrusted.

Server owns:

```text
company authorization
resource authorization
filter validation
source allowlist
account scope
cache scope
evidence authorization
```

No client/model-supplied company/report/resource is trusted directly.

FORBIDDEN must not reveal:

- company existence;
- requested company name;
- amount;
- voucher ID;
- previous-company cached payload.

---

# 6. Observability rules

Use typed allowlisted metadata only.

Allowed examples:

```text
correlation_id
feature_id
contract_version
method_version
formula_version
status
source_type
source_status
record_count
coverage_scope
latency_ms
model_status
error_class
```

Do not log:

```text
raw rows
party names
customer/supplier names
bank accounts
voucher text
financial line values
raw prompts
secrets
chain-of-thought
```

---

# 7. Deprecated route

`predict_cashflow` is not AI002.

Do not reuse its:

```text
AR - AP
LOW / WARNING
```

logic.

Do not connect it to:

- AI002 UI;
- agent tools;
- shortfall output;
- forecast API.

Keep compatibility/deprecation work separate unless explicitly assigned.

---

# 8. Definition of done by phase

## AI002-02 DONE

- typed data foundation exists;
- auth/source allowlist works;
- opening/AR/AP/payment evidence normalizes safely.

## AI002-03 DONE

- deterministic engine matches gold exactly;
- no-future-event fails closed;
- technical negative-cash event is deterministic.

## AI002-04 DONE

- core numeric/security tests pass;
- no missing→zero or due-date→settlement regression.

## AI002-05 DONE

- bounded agent only uses approved tools;
- explanations are grounded;
- model failure is non-fatal.

## AI002-06 DONE

- workspace displays truthful scoped forecast;
- no fake chart/risk badge.

## AI002-07 DONE

- G4B PASS;
- E2E/security/PII/grounding/timezone/regression evidence captured.

## AI002-08 DONE

- `AI002_TECHNICAL_DOCUMENTATION.md` completed;
- `AI002_SECURITY_SELF_ASSESSMENT.md` completed;
- README/deployment/test instructions reproduced;
- execution evidence sanitized and indexed;
- demo flow reproducible;
- deck-ready feature summary prepared;
- third-party license/provenance review completed.

---

# 9. Final release conditions

Do not call AI002 production-ready until:

```text
AI002-01 contract frozen
AI002-02 data foundation done
AI002-03 deterministic engine done
AI002-04 evaluation/security done
AI002-05 agentic layer done
AI002-06 workspace done
AI002-07 G4B PASS
AI002-08 feature technical documentation + security self-assessment + competition evidence package complete
```

If real-business sources are still unavailable:

```text
REAL_BUSINESS_DATA_READY = false
```

must remain visible.

---

# 10. Antigravity execution style

For each phase:

1. inspect current code first;
2. preserve project invariants;
3. make the smallest coherent change;
4. add tests with the change;
5. run targeted tests;
6. run relevant regression tests;
7. update SSOT status/evidence;
8. stop at the phase boundary if a security/financial gate fails.

Do not silently continue after a failed correctness or security gate.

---

# 11. Required implementation evidence

For every completed phase record:

```text
repo revision
files changed
tests added
tests run
results
known limitations
runtime environment
remaining blockers
```

Do not call mock-provider success a live-provider pass.

---

# 12. Final principle

```text
ERP truth
→ deterministic policy
→ deterministic finance
→ typed evidence
→ bounded agent
→ grounded explanation
```

Never:

```text
LLM
→ financial truth
```
