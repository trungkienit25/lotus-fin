# LOTUS FIN P6-2: L5 SECURITY SELF-ASSESSMENT

## 1. Compliance with Security Code V3 & Invariants

| Invariant | Requirement | Status | Evidence / Implementation |
| :--- | :--- | :--- | :--- |
| **INV-01** | Server-side authorization, never LLM | **ENFORCED** | Policy evaluation is strictly handled in `L5PolicyEngine` on the backend server. |
| **INV-02** | Scoped to authorized company / tenant | **ENFORCED** | Enforces `context.authorized_company == context.target.company` fail-closed. |
| **INV-03** | Material values from verified data | **ENFORCED** | Caps on payment requests (`max_amount`), currency allowlisting. |
| **INV-06** | No agent-held credentials or DB credentials | **ENFORCED** | Zero credentials exposed to agents or client responses. |
| **INV-07** | Bank write blocked in candidate/MVP | **ENFORCED** | `PAYMENT_EXECUTION` configured with `BLOCKED_DISALLOWED` and `ProductionBlockedAdapter`. |

---

## 2. Threat Analysis and Defenses

1. **Confused Deputy Attack**:
   - *Attack*: Attacker requests modification of another company's invoice.
   - *Defense*: Server strictly verifies authorized session company against document target company. Cross-tenant requests fail closed with `COMPANY_MISMATCH`.

2. **Replay & Double-Click Attacks**:
   - *Attack*: Intercepted proposal execution submitted multiple times.
   - *Defense*: Unique idempotency keys and server-side operation ledger track executed states. Duplicate requests return `ALREADY_COMMITTED` without rerunning adapters.

3. **TOCTOU (Time of Check / Time of Use)**:
   - *Attack*: Invoice status modified concurrently between UI approval and execution.
   - *Defense*: Mandatory re-authorization checks resource version freshness immediately prior to reserving lease and executing the adapter.

4. **Prompt Injection / Unauthorized Intent**:
   - *Attack*: Malicious text instructing chatbot to transfer funds.
   - *Defense*: All actions are mapped to typed allowlisted catalog actions. Direct execution of arbitrary actions returns `UNKNOWN_ACTION_NAME`.

---

## 3. Verdict Summary

- **L5_CONTRACT**: **PASS**
- **L5_POLICY_ENGINE**: **PASS**
- **L5_APPROVAL_WORKFLOW**: **PASS**
- **L5_SIMULATED_E2E**: **PASS**
- **L5_EXTERNAL_EXECUTION**: **BLOCKED** (Designated fail-closed)
- **L5_PAYMENT_EXECUTION**: **BLOCKED** (Designated fail-closed)
- **L5_SCHEDULER_EXECUTION**: **BLOCKED** (Designated fail-closed)
