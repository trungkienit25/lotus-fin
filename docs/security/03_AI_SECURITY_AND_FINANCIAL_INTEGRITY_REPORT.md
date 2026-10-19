# ARTIFICIAL INTELLIGENCE & FINANCIAL INTEGRITY SPECIFICATION REPORT
## AI Copilot Security, Deterministic Financial Integrity & Human-in-the-Loop Governance

> **Project Name:** Lotus Fin — SME Financial Management Core with AI Key Report Pipeline  
> **Competition:** The 2026 Shenzhen International FinTech Competition — WeBank FinTech University Challenge (Topic E)  
> **Version:** 3.0 (Technical Deep-Dive, Quantitative Metrics & Implementation Aligned)  
> **Methodology:** `Problem` $\to$ `Solution` $\to$ `Implementation Blueprint` $\to$ `Verification Evidence`  
> **Reference Standards:** OWASP Top 10 for Large Language Model Applications (2025), NIST AI Risk Management Framework (AI RMF 1.0), MITRE ATLAS  

---

## 1. AI THREAT LANDSCAPE & ATTACK SURFACE IN FINANCIAL COPILOTS

Integrating Large Language Models (LLMs) into enterprise financial software introduces specific systemic vulnerabilities that directly threaten accounting integrity:
1. **Financial Hallucination & Misinformation (OWASP LLM09):** Probabilistic models fabricate plausible revenue totals, miscalculate amortization interest, or invent cash balances.
2. **Prompt Injection & System Prompt Override (OWASP LLM01):** Malicious instructions embedded in customer queries or invoice metadata attempt to bypass business logic and authorization boundaries.
3. **Excessive Agency & Autonomous Mutation (OWASP LLM06):** AI assistants autonomously executing state-mutating actions (such as generating payment tasks or dispatching collection notices) without human review.
4. **Sensitive Data Disclosure & Context Leakage (OWASP LLM02):** Unsanitized transmission of confidential ledger details or internal database structures to third-party model providers.
5. **Unbounded Resource Consumption (OWASP LLM10):** Runaway ReAct agent loops or denial-of-wallet attacks that exhaust enterprise API token budgets.

Lotus Fin resolves these vulnerabilities through **Defense-in-Depth** and an **Absolute Separation between Natural Language Reasoning and Deterministic Calculation Engines**:

```
[ User Query via Copilot Interface ]
                   │
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 1. INPUT ADMISSION & SANITIZATION LAYER                                │
│    - Length Ceiling: Max 500 characters (Prompt flooding defense)      │
│    - System instruction segregation & Unicode control character stripping│
└──────────────────┬─────────────────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. CONTROLLED ReAct AGENT RUNNER (Bounded Orchestration)               │
│    - Max 4 Iterations per turn | Max 6 Tool calls per turn             │
│    - Closed Tool Whitelist via Pydantic schemas (Unknown tools denied) │
│    - Sliding Context Window: 8 most recent messages + System Prompt    │
│    - Circuit Breaker: Tripped after 5 consecutive provider errors      │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ Structured Tool Request (JSON)
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. ZERO-AI DETERMINISTIC DOMAIN CALCULATORS                            │
│    - F001: General Ledger Financial Snapshot (Audited GL records)      │
│    - F002: 30-Day Deterministic Cash Flow Trajectory & Shortfall Engine│
│    - F003: Overdue AR Spike & AP Clustering Anomaly Detection         │
│    - F004: 9-Layer Multivariate What-If Stress Simulation Matrix       │
│    - F006: Loan Amortization (PMT Formula) & Rate Shock bps Simulation│
└──────────────────┬─────────────────────────────────────────────────────┘
                   │ Deterministic Numerical Output (Decimal Precision)
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. AUTOMATED PRESENTATION GATE (Schema & Metric Sanitization)          │
│    - Absolute Numeric Tolerance Check: |Claim - Calculated| < 0.05    │
│    - Strips 100% internal DB columns & boolean flags (deficit tags)    │
│    - Filters internal contract keys: STRICT_BASELINE_V1, TRADE_ONLY    │
└──────────────────┬─────────────────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. LEVEL 4 HUMAN-IN-THE-LOOP ACTION GATE (Two-Phase Commit)            │
│    - Phase 1: Propose (SHA-256 canonical digest + 24-byte challenge)   │
│    - Phase 2: Confirm (Human review of visual diff; Maker-Checker)     │
│    - High-risk autonomous mutation strictly blocked (R4=DENY, R5=DENY) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DEEP-DIVE AI SECURITY CONTROLS & IMPLEMENTATION BLUEPRINTS

### 2.1. Strict Tool Whitelist & Bounded Execution Budgets

#### Problem
In an indirect prompt injection attack, text contained within invoice notes or vendor statements instructs the LLM to invoke unauthorized functions or enter an infinite loop, exhausting API quota.

#### Solution
1. **Closed Tool Whitelist:** The LLM is restricted exclusively to 7 registered analytical tools. Any tool call referencing an unlisted name is rejected by the invoker before execution.
2. **Immutable Execution Budgets:**
   * **Turn Iteration Cap:** Strictly limited to **4 iterations** per user request.
   * **Tool Call Ceiling:** Maximum of **6 tool invocations** per conversational turn.
   * **Provider Circuit Breaker:** If 5 consecutive failures occur within 30 seconds, outbound calls are temporarily suspended to protect system stability.

#### Implementation Blueprint
* **Agent Execution Loop:**
  * Initialize conversational working context bounding history to the 8 most recent messages.
  * Execute turn cycles in a bounded `while` loop incrementing an iteration counter.
  * If the LLM generates tool call requests, verify tool count against the budget ceiling. Once 6 calls are reached, immediately halt execution, log a budget-exceeded trace, and return available results.
  * Dispatch tool calls through the authorization invoker, verifying the user's role against the tool definition.
  * Append tool outputs to the context for the final conversational synthesis.

---

### 2.2. Deterministic Financial Calculations & Zero-AI Arithmetic (INV-03)

#### Problem
LLMs are probabilistic token predictors, not mathematical processors. They frequently make arithmetic errors in compound interest calculations, net profit margins, and daily cash flow schedules.

#### Solution
1. **Zero-AI Calculation Invariant:** The LLM is strictly prohibited from performing accounting arithmetic. All financial metrics are generated by dedicated mathematical engines utilizing high-precision `Decimal` types:
   * **Revenue & Gross Profit:** Aggregated directly from posted General Ledger entries (`docstatus = 1`).
   * **30-Day Cash Trajectory:** Built from confirmed payment due dates on booked purchase and sales invoices.
   * **Loan Amortization:** Computed using the standard PMT formula:
     $$\text{PMT} = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$
   * **Interest Rate Shock:** Modeled by applying basis point increases ($+100$, $+200$, $+300$ bps) directly to annual interest parameters.
2. **Absolute Numeric Tolerance Verification:** Financial narratives generated by the LLM are evaluated against underlying calculation results. Statements asserting figures that deviate by more than $\pm 0.05$ from calculated values are discarded in favor of structured data tables.

---

### 2.3. Automated Presentation Gate & Schema Sanitization

#### Problem
Model outputs frequently leak raw database column names (such as `has_constituent_deficit`), empty arrays (`shortfall_events: []`), or internal verification keys (`STRICT_BASELINE_V1`). This clutters executive communications and exposes underlying database schemas.

#### Solution
Lotus Fin deploys an automated regex-based **Presentation Gate** (`sanitize_executive_reply`) executed at the presentation layer prior to message persistence or client rendering.

#### Implementation Blueprint
* **Sanitization Interceptor Pipeline:**
  * Intercept the raw text generated by the model before session storage.
  * Execute regular expression filters targeting raw boolean flags and internal property keys (e.g., removing `constituent_deficit: false` and `opening_cash_deficit: true`).
  * Remove empty JSON structures and bracketed shortfall keys.
  * Strip internal test tags and verification flags (`STRICT_BASELINE_V1`, `TRADE_ONLY`, `NO_CONFIRMED_SETTLEMENT_EVENTS`).
  * Normalize whitespace, remove orphaned punctuation, and ensure clean markdown presentation for executive review.

---

### 2.4. Level 4 Human-in-the-Loop Governance & Two-Phase Commit Gate

#### Problem
Granting autonomous mutation capabilities to AI agents (such as writing journal entries or sending collection demands) creates severe financial and legal liabilities.

#### Solution: 4-Tier Autonomy Governance Architecture
Lotus Fin organizes all system operations into 4 explicit operational tiers:
* **Tier 0 (Read-Only Analysis):** Reading financial summaries and analyzing aging receivables. Permitted autonomously for authenticated users.
* **Tier 1 (Simulation & Drafting):** Simulating What-If stress scenarios and generating localized reminder previews. Permitted autonomously.
* **Tier 2 (Operational Mutations):** Persisting operational follow-up tasks and staged drafts. **Strictly requires human review and two-phase confirmation.**
* **Tier 3 (High-Risk Financial Actions):** Direct wire transfers, altering bank accounts, or external tax filings. **Permanently disabled (`R4=DENY, R5=DENY`).**

```
[ PHASE 1: PROPOSE (L4 Proposal Generation) ]
AI generates an action proposal with cryptographic integrity:
{
  "proposal_id": "prop-m490f2",
  "action_id": "lotus.task.create",
  "target_entity": "Sales Invoice/ACC-SINV-2026-00001",
  "arguments": { "title": "Follow up overdue invoice", "due_date": "2026-10-25" },
  "canonical_args_digest": "sha256(canonical_json(arguments))",
  "confirmation_challenge": "chal-b928f01a88c2419ef",
  "expires_at_utc": "2026-10-19T21:30:00Z" (10-minute TTL)
}
                       │
                       ▼
[ PHASE 2: HUMAN REVIEW (Visual Diff Card) ]
Accountant inspects the proposal in the interactive UI (`L4ProposalChatCard.tsx`).
Displays clear before/after diff of task attributes.
                       │
                       ├─► [ CANCEL ] ──► Proposal immediately invalidated in the store.
                       │
                       └─► [ CONFIRM ]
                                 │
                                 ▼
[ PHASE 3: VERIFICATION & EXECUTION (L4 Confirm) ]
Client transmits confirmation request with the single-use challenge token.
Backend executes strict verification:
 1. Validate argument digest: Verify arguments have not been altered.
 2. Check expiration: Reject if current time exceeds 10-minute TTL.
 3. Re-verify user role: Require active `Accounts Manager` or `System Manager` status.
 4. Execute atomic transaction: Commit audit entry and mutation receipt idempotently.
```

#### Implementation Blueprint
* **Two-Phase Confirmation Engine:**
  * During proposal creation, compute an SHA-256 digest over the canonical JSON representation of all arguments.
  * Generate a cryptographically secure 24-byte random challenge token and assign a 10-minute expiration window.
  * When receiving a confirmation request, verify challenge authenticity and compare the argument digest.
  * Execute the state change within a transactional database block that records an immutable audit log entry simultaneously.
  * Enforce idempotency: multiple confirmation requests bearing the same proposal ID resolve to the original receipt without duplicate execution.

---

### 2.5. Model Credential Isolation & Context Minimization

#### Problem
Hardcoding API credentials or forwarding sensitive personal data (PII) to external model providers risks credential theft and regulatory violations.

#### Solution
1. **Server-Side Environment Vault:** API credentials (`GEMINI_API_KEY`) reside exclusively in server-side environment variables and are never transmitted to client browsers.
2. **Chain-of-Thought Elimination (INV-10):** Internal chain-of-thought traces generated during reasoning are stripped prior to database persistence, protecting analytical tradecraft.
3. **Audit Log Sanitization:** Conversational audit logs record operational metadata (`session_id`, `user_id`, `company`, `tool_called`, `latency_ms`) while masking customer identifiers and account numbers.

---

## 3. OWASP TOP 10 FOR LLM (2025) COMPLIANCE MAPPING

| Vulnerability Code | Risk Description | Lotus Fin Defensive Mechanism | Verification Status |
| :--- | :--- | :--- | :---: |
| **LLM01: 2025** | Prompt Injection | Input bounded to 500 characters; system prompts segregated from user input; server-side authorization enforcement independent of model text |  **PASS** |
| **LLM02: 2025** | Sensitive Data Disclosure | Multi-tenant boundary checks (`get_verified_company`); PII masking and omission of chain-of-thought traces in persistent logs |  **PASS** |
| **LLM03: 2025** | Supply Chain Vulnerabilities | Pinned base container digests; frozen dependencies via SHA-256 lockfiles (`requirements.txt`, `package-lock.json`) |  **PASS** |
| **LLM04: 2025** | Data & Model Poisoning | Financial inputs sourced exclusively from submitted accounting ledger entries (`docstatus = 1`); models are not trained on user inputs |  **PASS** |
| **LLM05: 2025** | Improper Output Handling | Markdown rendered through an AST pipeline: `react-markdown` + `remark-math` + `rehype-katex` + DOMPurify, preventing XSS execution |  **PASS** |
| **LLM06: 2025** | Excessive Agency | Level 4 Two-Phase Commit gate; autonomous ledger modification or financial transfers permanently disabled (`R4=DENY, R5=DENY`) |  **PASS** |
| **LLM07: 2025** | System Prompt Leakage | Automated Presentation Gate strips internal configuration flags, test metadata, and system instructions |  **PASS** |
| **LLM08: 2025** | Vector & Embedding Vulnerabilities | Context retrieval strictly keyed by `company_id` and verified user identity; sessions isolated at the storage level |  **PASS** |
| **LLM09: 2025** | Misinformation / Hallucination | Zero-AI Calculation invariant; 100% of financial figures computed by deterministic calculators; absolute tolerance check $\pm 0.05$ |  **PASS** |
| **LLM10: 2025** | Unbounded Consumption | Execution budget caps: max 4 iterations, 6 tool calls; API rate limit 10r/s; Circuit breaker tripped after 5 consecutive errors |  **PASS** |

---

## 4. QUANTITATIVE VERIFICATION & AUDIT EVIDENCE SUMMARY

```text
================================================================================
          AI SECURITY & FINANCIAL INTEGRITY TEST VERIFICATION REPORT
================================================================================
[TEST SUITE] Pytest Full Integration & Mutation Gate Suites:
Command: python -m pytest lotus_fin/tests/test_copilot_full_integration.py
Results:
- test_l3_to_l4_confirm_persists_and_is_idempotent ................... [PASS]
- test_old_proposal_cannot_cross_scope_or_revoked_permissions ......... [PASS]
- test_core_demo_isolation_and_disabled_source ....................... [PASS]
- test_v1_actual_evaluator_fixed_gold ................................ [PASS]
- test_l5_policy_review_denies_side_effects .......................... [PASS]
- test_cancel_and_expired_proposal ................................... [PASS]
- test_failed_audit_rolls_back_before_simulation ..................... [PASS]
- test_concurrent_confirmation_single_receipt ........................ [PASS]
- test_unknown_outcome_reconciles_without_reexecution ................ [PASS]
- test_client_cannot_supply_authority_or_execution_adapter ........... [PASS]
=> Total: 26/26 Integration Tests PASS in 1.03s (100% Success Rate)

[TEST SUITE] Pytest Clean Architecture & Remediation Suites:
Command: python -m pytest lotus_fin/tests/test_clean_architecture.py lotus_fin/tests/test_architecture_remediation.py
=> Total: 41/41 Architecture Remediation Tests PASS in 0.51s (100% Success Rate)

[TEST SUITE] Frontend Node Test Runner:
Command: node --test frontend/tests/*.test.ts
=> Total: 58/58 Tests PASS in 349ms (100% Success Rate)
   (Verifies: Oracle L301-L318, 600s TTL, Proposal Expiration, Scope Key Reset)
================================================================================
```
