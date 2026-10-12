# LOTUS FIN — SECURITY REQUIREMENTS SSOT
## Code / Implementation Version for Engineers and Coding Agents

> **Version:** 3.0 — 2026-09-24  
> **Language:** English  
> **Scope:** UC001–UC010  
> **Platform:** Frappe / ERPNext custom application  
> **Reviewed code commit:** `f743acf57a43ac4c72090b9f07971b4803eb0667`  
> **MVP Bank policy:** `R4 = DENY`, `R5 = DENY`  
> **Authority:** This is the implementation-oriented security SSOT for new Lotus Fin code. Runtime facts not proven by tests remain `NOT_VERIFIED`.

---

# 1. Normative Keywords

- `MUST` / `MUST NOT`: mandatory for enabled MVP capability.
- `SHOULD` / `SHOULD NOT`: recommended; deviation requires documented rationale.
- `MAY`: optional.
- A control associated with a disabled feature may be marked `N/A` only if no reachable code path/capability exists.

---

# 2. Official UC Mapping

- UC001 — Manage and Normalize Financial Data
- UC002 — Manage Business Activities and Financial Transactions
- UC003 — Analyze Business Financial Health
- UC004 — Forecast Cash Flow
- UC005 — Detect Financial / Operational Risk Signals
- UC006 — Financial Copilot Chat
- UC007 — Match Financing Options
- UC008 — Simulate Financing Repayment / Stress Scenarios
- UC009 — Dashboard and Reports
- UC010 — User / Role / Audit Management

Do not use the obsolete UC001–UC006 security mapping.

---

# 3. Current Architecture Assumption

```text
ERPNext/Frappe
  ├── DocTypes
  ├── Query Reports
  ├── Auth/permission framework (runtime behavior NOT_VERIFIED)
  └── financial records
        ↓
Lotus Frappe app
  ├── whitelisted endpoints
  ├── report adapter
  ├── hooks/scheduler
  └── deterministic intelligence services TO_BUILD
        ↓
Typed tools TO_BUILD
        ↓
Copilot TO_BUILD
```

No second writable ledger MUST be introduced.

---

# 4. Mandatory Security Invariants

`INV-01` Authorization MUST be decided by server-side code/Frappe permissions, never by LLM.  
`INV-02` Every business-data request MUST be scoped to an authorized company/tenant/resource.  
`INV-03` Material financial values MUST come from deterministic/statistical code and verified source data.  
`INV-04` A missing/error source MUST NOT be silently converted to `0`.  
`INV-05` The existing `AR - AP` function MUST NOT be exposed as cash-flow forecast.  
`INV-06` AI MUST NOT have direct DB credentials or direct Bank credentials.  
`INV-07` R4/R5 bank-write is denied in MVP.  
`INV-08` External text, report values, customer/supplier names and AI output are untrusted presentation data.  
`INV-09` AI/RAG content cannot alter authorization, tool allowlist, company scope or financial truth.  
`INV-10` Raw chain-of-thought MUST NOT be stored.

---

# 5. Company / Tenant Authorization Contract

Until runtime testing proves otherwise, `company` MUST be treated as an untrusted request parameter.

Every Lotus endpoint that accepts any of `company`, `filters`, `doctype/name`, `invoice_id`, `customer_id`, `supplier_id`, or `report_name` MUST enforce authorization before data access.

Pseudo-contract:

```python
def authorize_company_request(user, company, action, resource=None):
    require_authenticated(user)
    require_company_exists(company)
    require_user_company_access(user, company)
    if resource is not None:
        require_resource_company(resource, company)
        require_resource_permission(user, resource, action)
    return ALLOW
```

No endpoint may rely only on default company, UI-hidden field, LLM instruction or caller-provided filter.

Required negative tests:

```text
User A + Company A -> Company B = DENY
User A + Invoice B (Company B) = DENY
User A + bulk export filters Company B = DENY
```

---

# 6. Endpoint Security Requirements

## 6.1 Report Adapter

The report adapter MUST:

- allowlist report names;
- validate filter schema;
- bind/verify company;
- reject caller-selected company outside scope;
- cap rows/output size;
- return explicit `ERROR`/`PARTIAL`, never silently empty success;
- record source report and filters in evidence metadata.

## 6.2 Bulk Export

Bulk export MUST:

- use authorized company scope;
- apply row/size/module limits;
- preserve per-module error status;
- never represent partial export as complete;
- not be named “training dataset” unless labels/split/manifest/task exist.

Recommended rename:

```text
get_ai_training_dataset
→ export_financial_analysis_bundle
```

## 6.3 Invoice Risk

Before `get_doc`/history query:

- verify invoice permission;
- verify invoice company;
- bind all related queries to same company;
- avoid unrestricted customer history across companies.

---

# 7. Deterministic Financial Integrity

Every material numeric output MUST have:

```yaml
value: decimal
currency: string|null
as_of: datetime|null
formula_version: string
evidence_refs: []
limitations: []
```

A result MAY be called forecast only when it includes opening cash, time horizon, dated inflows/outflows or explicit assumptions, AR/AP due timing and known obligations or explicit limitations.

Missing required input MUST produce:

```yaml
status: INSUFFICIENT_DATA
missing_inputs: []
```

Forbidden:

```text
report error → [] → 0 → LOW risk
```

All repayment schedules MUST use deterministic decimal arithmetic with explicit conventions and independent gold tests.

---

# 8. Action Levels

| Level | Action | MVP |
|---|---|---|
| R0 | Read/view | ALLOW if authorized |
| R1 | Compute/simulate | ALLOW if typed/authorized |
| R2 | Draft | limited |
| R3 | Commit internal state | explicit confirmation if enabled |
| R4 | Bank sandbox submit | DENY |
| R5 | real financial execution | DENY |

No active R4/R5 route, tool, worker, credential or write egress.

---

# 9. Copilot Tool Security

Before UC006 is enabled, implement an allowlisted tool registry.

Allowed candidate P0 tools:

```yaml
- get_financial_health
- get_cash_forecast
- get_risk_signals
- run_scenario
- match_financing_options
- simulate_repayment
```

Each tool schema MUST include:

```yaml
subject:
  user_id: string
  company: string
request:
  tool: string
  parameters: object
context:
  correlation_id: string
  tool_version: string
```

Server MUST verify user authentication, company authorization, tool allowlist, schema/bounds, resource ownership, action level, source availability and deterministic numeric generation.

The LLM MUST NOT supply arbitrary report names, arbitrary URLs or raw SQL.

---

# 10. Prompt / Indirect Injection

When LLM/RAG is enabled:

- user/retrieved/external text MUST be tagged as untrusted;
- retrieved text MUST NOT be interpreted as system/tool instruction;
- injection MUST NOT modify company scope or authorization;
- model output MUST pass tool schema validation;
- tool result text is also untrusted;
- financing catalog instructions are data only.

On RAG failure return `INSUFFICIENT_EVIDENCE`, not a fabricated citation.

---

# 11. Output Encoding & Client Security

`SEC-029` is P0.

Requirements:

- escape customer/supplier/report/AI strings in UI;
- avoid raw HTML interpolation;
- sanitize only when HTML is truly needed;
- protect CSV formula injection;
- no stack trace/path/secret in client error;
- CSP SHOULD be used according to Frappe deployment capability.

The current Sales Invoice popup MUST be regression-tested with XSS canary data.

---

# 12. Logging / Audit

MUST NOT log by default: secrets/tokens, passwords, raw CoT, full financial documents, full account identifiers or full prompts with PII.

Structured event:

```yaml
event_id: string
occurred_at: timestamp
correlation_id: string
event_type: string
user_id: string|null
company: string|null
resource_id: string|null
action: string|null
policy_decision: ALLOW|DENY|N/A
status: SUCCESS|FAIL|PARTIAL
error_class: string|null
tool_version: string|null
model_version: string|null
```

Existing hooks that log customer/party/amount MUST be reviewed and minimized.

---

# 13. Financing Catalog Security

Before UC007, every catalog record MUST include:

```yaml
product_id: string
provider: string
source_ref: string
source_as_of: date
retrieved_at: datetime
ttl: duration
status: VERIFIED|STALE|UNVERIFIED
```

System MUST NOT infer approval probability, invent rate/criteria, use stale terms as current without warning, or submit an application.

---

# 14. Upload/OCR Controls

Only applicable when UC001 upload/OCR is enabled.

```text
upload
→ type/size check
→ quarantine
→ malware/MIME/magic validation
→ parser/OCR sandbox
→ Candidate
→ reconciliation/review
→ Trusted
```

Parser/OCR process MUST NOT have DB/Bank credentials.

---

# 15. Control Catalog v3

| ID | Requirement |
|---|---|
| SEC-001 | Verify MFA configuration for sensitive roles if available/required |
| SEC-002 | Step-up authentication for sensitive admin actions enabled in MVP |
| SEC-003 | Server-side RBAC + resource/company isolation; do not mandate PostgreSQL RLS on a non-PostgreSQL stack |
| SEC-004 | Scope jobs/cache/tools to company/tenant |
| SEC-005 | Upload quarantine when UC001 enabled |
| SEC-006 | Parser/OCR sandbox when enabled |
| SEC-007 | Candidate→Trusted before material calculation |
| SEC-008 | Deterministic financial source of truth |
| SEC-009 | Direct/indirect prompt-injection containment |
| SEC-010 | RAG ACL/provenance/freshness when RAG enabled |
| SEC-011 | Tool allowlist + typed schema + server policy |
| SEC-012 | Agent step/token/time/cost budgets |
| SEC-013 | Exact approval binding for enabled R3 actions |
| SEC-014 | Bank-write idempotency — N/A in MVP because R4 disabled |
| SEC-015 | Bank transport/webhook security — N/A in MVP |
| SEC-016 | Output grounding + numeric binding |
| SEC-017 | PII/secret minimization |
| SEC-018 | No raw CoT / no secret logging |
| SEC-019 | Correlation ID + audit trail |
| SEC-020 | AI cannot access DB/Bank directly |
| SEC-021 | No hard-coded secrets; approved secret storage |
| SEC-022 | SAST/SCA/secret scan; SBOM as feasible |
| SEC-023 | Pin/version app/model/tool/policy for release |
| SEC-024 | Safe degradation; no fabricated financial output |
| SEC-025 | Incident/restore procedure |
| SEC-026 | Regression/adversarial release gates |
| SEC-027 | Persistent free-text memory disabled by default |
| SEC-028 | Financing source + as_of + TTL |
| SEC-029 | Output encoding/CSP/formula-injection defense |
| SEC-030 | Separate privileged operational identity; audited elevation where applicable |

---

# 16. Release Gates

**G-01 Auth/RBAC** — unauthorized privileged action = 0.  
**G-02 Company/Tenant Isolation** — cross-company canary leak = 0.  
**G-03 File/Parser** — `N/A` until upload/parser is enabled; mandatory afterward.  
**G-04 Prompt Injection** — mandatory before Copilot/RAG.  
**G-05 Tool Authorization** — non-allowlisted/wrong-company tool execution = 0.  
**G-06 Numeric Integrity** — 100% material values match deterministic gold.  
**G-07 Approval Binding** — applicable to enabled R3 actions.  
**G-08 Bank** — R4/R5 unavailable/denied; no write credential/egress/tool/route.  
**G-09 Output Privacy** — no secret/unauthorized PII/cross-company content.  
**G-10 Safe Failure** — source/tool/model faults never fabricate numeric conclusion.  
**G-11 Audit** — enabled critical flow reconstructable by correlation ID.  
**G-12 Change Gate** — applicable security/numeric/adversarial tests rerun on changes.

---

# 17. Required P0 Tests

```text
AUTH-001 unauthorized company override
AUTH-002 invoice IDOR/cross-company
AUTH-003 bulk export scope override

NUM-001 report error does not become zero
NUM-002 missing forecast input -> INSUFFICIENT_DATA
NUM-003 gold KPI
NUM-004 gold repayment
NUM-005 scenario numeric gold

WEB-001 XSS customer name
WEB-002 unsafe AI output rendering
WEB-003 CSV formula injection

BANK-001 no R4 route/tool
BANK-002 no write credential configured

AI-001 non-allowlisted tool blocked
AI-002 LLM company override blocked
AI-003 tool number cannot be overwritten by LLM
AI-004 retrieved prompt injection cannot change policy
```

---

# 18. Secure Definition of Done

A security/finance-sensitive PR is not done until:

- [ ] associated UC/AI feature is identified;
- [ ] authorization allowed + denied tests exist;
- [ ] company isolation test exists;
- [ ] numeric gold exists if material finance math changed;
- [ ] missing/error source path fails safely;
- [ ] output encoding reviewed;
- [ ] logs reviewed for PII/financial leakage;
- [ ] tool schema/bounds validated when AI tool changes;
- [ ] docs/status updated (`IMPLEMENTED`, `PARTIAL`, etc.);
- [ ] no claim exceeds test evidence.
