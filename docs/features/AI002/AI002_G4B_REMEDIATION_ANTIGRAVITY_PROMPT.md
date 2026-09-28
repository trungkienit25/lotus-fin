# GOOGLE ANTIGRAVITY MASTER PROMPT — AI002 REMEDIATION & G4B RE-VALIDATION

## Lotus Fin — AI-F002 Cash-flow Forecast Copilot

**Execution target:** Google Antigravity  
**Task type:** Immediate remediation / hardening  
**Current state:** `IMPLEMENTED_BUT_REMEDIATION_REQUIRED`  
**Contract:** keep `AI002_01_CONTRACT_FROZEN` unless a real contract contradiction is proven  
**G4B:** `FAIL / NOT_READY`  
**AI002-08 / Feature Closure:** NOT APPROVED  
**User-ready / Competition-ready:** NO

---

# 1. Mission

Fix runtime/code first, prove the fixes with reproducible tests, then update documentation.

Required order:

```text
CODE FIX
→ TARGETED TESTS
→ REGRESSION TESTS
→ DOCKER / RUNTIME VERIFICATION
→ UI / E2E VERIFICATION
→ G4B RE-ASSESSMENT
→ ONLY THEN documentation update
```

Do NOT redesign AI002. Do NOT weaken the frozen contract. Do NOT make reports look green before runtime is green.

Authoritative inputs:

```text
AI002_MASTER_SSOT_V1_2_1_REFINED.md
AI002_GOLD_FIXTURE_MANIFEST.yaml
AI002_DECISION_LOG_CONTRACT_FREEZE_REFINED.md
AI002_IMPLEMENTATION_TASK_PACKET_ANTIGRAVITY_REFINED.md
AI002_TECHNICAL_DOCUMENTATION.md
AI002_SECURITY_SELF_ASSESSMENT.md
AI002_TONG_HOP_KET_QUA_TRIEN_KHAI.md
```

Runtime/code is authoritative for what is actually implemented.

---

# 2. Non-negotiable principle

Anything high-risk remains deterministic and server-enforced.

LLM / Agent must NOT own:

```text
authorization
financial arithmetic
opening cash
AR/AP residual
fixture/live mode
source trust
coverage policy
shortfall rule
failure state
PII redaction
cache isolation
evidence authorization
write actions
```

---

# 3. P0 CRITICAL — isolate synthetic fixture data from normal runtime

## Problem

Current implementation reportedly allows `use_fixture_source` through normal API/UI. Fixture events can be attached to a requested company and the cache does not sufficiently distinguish fixture/live mode. A normal request was reproduced receiving 3 synthetic events from cache.

## Required fix

1. Remove `use_fixture_source` from the normal user-facing API contract.
2. Remove/disable any normal UI toggle that enables fixture mode.
3. Fixture mode may exist only in isolated test/dev harnesses and must be enabled by **server-side configuration**, never by a client boolean.
4. Default/production behavior:

```text
fixture source = disabled
```

5. Synthetic events must always carry explicit test provenance and can never be treated as business truth.
6. Cache identity must include source semantics, at minimum:

```text
user
verified_company
financial_as_of
forecast_start
forecast_end
cash_account_scope
coverage_scope
contract_version
method_version
source_mode
source_provider_version
```

or fixture mode must bypass production cache entirely.

## Required invariant

```text
LIVE request can NEVER receive fixture result
FIXTURE request can NEVER poison LIVE cache
```

## Required tests

```text
normal endpoint cannot enable fixture source
normal UI exposes no fixture toggle
fixture mode requires server-side test config
live request after fixture request contains zero synthetic events
fixture request after live request stays isolated
cache key differs by source mode/provider
cross-company fixture leakage impossible
```

This is a release blocker.

---

# 4. P0 CRITICAL — opening cash reconciliation must be real

## Problem

Current adapter reportedly auto-selects Cash/Bank accounts when scope is absent, does not actually reconcile Trial Balance, yet can return `TRIAL_BALANCE_RECONCILED`; a no-Frappe path reportedly returned `0 VND` with that label.

## Required fix

### Explicit account scope

P0 requires:

```text
explicit authorized cash_account_scope
```

Do not silently auto-select all Cash/Bank accounts.

If scope is missing/invalid, fail closed with the correct typed contract state.

### Validate every account

Each account must be:

```text
authorized
active
leaf
Cash or Bank type
supported currency
same supported book/scope
```

Reject group/restricted/unauthorized/unsupported accounts.

### Real reconciliation

Opening cash must:

1. read submitted GL through `financial_as_of`;
2. compute using Python `Decimal`;
3. independently obtain Trial Balance for the same company/date/account scope;
4. compare GL vs TB;
5. return a truthful typed reconciliation state.

Do not return `TRIAL_BALANCE_RECONCILED` unless equality was actually verified.

Recommended states:

```text
RECONCILED
NOT_RECONCILED
RECONCILIATION_UNAVAILABLE
INTRADAY_UNCLOSED
```

### Fail closed

Never:

```text
source unavailable
→ 0 VND
→ RECONCILED
```

Use `SOURCE_ERROR`, `TIMEOUT`, `INSUFFICIENT_DATA`, or `INCONSISTENT_DATA` according to the frozen contract.

## Required tests

```text
GL/TB equal → RECONCILED
GL/TB mismatch → INCONSISTENT_DATA
Trial Balance unavailable → not reconciled
Frappe unavailable → no false zero
missing account scope → fail closed
group account rejected
unauthorized account rejected
negative real balance valid
real zero balance valid zero
```

---

# 5. P0 SECURITY — generic FORBIDDEN must not leak company/resource identity

## Required fix

Normalize user-facing denial to generic:

```text
status: FORBIDDEN
message: generic
```

Do not include:

```text
requested company
resource existence
voucher ID
amount
previous-company cached data
```

Internal logging may retain only policy-compliant redacted diagnostics.

## Required tests

```text
existing but unauthorized company
nonexistent company
tampered company filter
cross-company record
```

User-facing responses must not allow existence inference.

---

# 6. P0 SECURITY/UI — company switch and stale responses

## Required fix

On company switch:

```text
1. increment request generation/token
2. cancel or ignore prior in-flight request
3. clear sensitive prior-company forecast/evidence/explanation immediately
4. issue new request
5. render only if response token AND response company match active workspace state
```

Required invariant:

```text
response.company == active_workspace_company
AND
response_generation == current_generation
```

otherwise discard.

## Required tests

```text
A request starts → switch to B → B arrives → A arrives late → A discarded
company switch clears prior financial UI immediately
FORBIDDEN leaves no prior-company chart/table/evidence
```

---

# 7. P0 SECURITY — evidence reauthorization must be wired, not merely implemented

Locate every AI002 evidence/drilldown path.

Before returning evidence:

```text
authenticate
→ verify active company
→ verify evidence belongs to company
→ verify record read permission
→ return evidence
```

Every AI002 evidence endpoint/tool must invoke this boundary.

## Required tests

```text
authorized evidence → allowed
cross-company evidence → FORBIDDEN
record without read permission → FORBIDDEN
tampered evidence ID → generic failure
stale previous-company evidence → rejected
```

---

# 8. P0 AI SAFETY — numeric/date grounding must reject hallucinated financial claims

## Problem

The reported test phrase:

```text
Cash will be 999999999 VND tomorrow
```

was accepted although that amount was absent from deterministic results.

## Required fix

Ground every material claim to typed deterministic result/evidence.

Validate at minimum:

```text
amount
date
company
currency
opening cash
shortfall date
minimum cash
driver amount
event type
confirmed-vs-obligation semantics
```

Prefer a structured explanation schema with field references, for example:

```yaml
facts:
  - fact_type:
    value_ref:
    statement:
interpretations:
limitations:
next_checks:
```

A material number/date/company claim without deterministic support must be rejected or make the explanation unavailable.

## Required adversarial tests

Reject:

```text
999999999 invented amount
altered shortfall date
altered opening cash
wrong currency
wrong company
invented confirmed payment
due date presented as settlement date
unsupported SAFE / LOW RISK / HIGH RISK claim
```

---

# 9. P0 AI SAFETY — model failure must degrade correctly

If the model:

```text
times out
raises exception
returns malformed schema
fails grounding
fails policy validation
```

then:

```text
deterministic financial result remains unchanged
explanation.status = UNAVAILABLE
explanation.error_code = typed error
```

Never return `explanation.status = OK` on model failure.

Required tests:

```text
timeout
exception
malformed output
invented number
grounding failure
prompt injection
provider unavailable
```

---

# 10. Cache review

Re-review all cache dimensions.

No cached response may cross:

```text
user
company
fixture/live source mode
account scope
coverage scope
cutoff/horizon
contract version
method/source version
```

Add explicit collision tests.

---

# 11. One active SSOT only

Current artifact validation reportedly detects two files claiming active SSOT authority.

There must be exactly:

```text
ONE active human-readable AI002 SSOT
ONE active machine-readable gold oracle
```

Recommended current authority:

```text
AI002_MASTER_SSOT_V1_2_1_REFINED.md
AI002_GOLD_FIXTURE_MANIFEST.yaml
```

Archive or replace all competing SSOT variants with `SUPERSEDED` pointers.

Run `validate_artifacts.py` until this passes.

---

# 12. Test evidence — one canonical truth

Current docs reportedly contain conflicting counts:

```text
81 vs 82 Docker tests
10 vs 11 local tests
```

After fixes, rerun everything and record exact evidence:

```yaml
environment:
repo_commit:
date:
command:
test_scope:
tests_collected:
tests_passed:
tests_failed:
tests_skipped:
duration:
```

Separate:

```text
local pure-Python
Docker/Frappe integration
security tests
evaluation scenarios
UI/E2E
```

Do not sum overlapping suites.

If Docker cannot run:

```text
DOCKER_VERIFICATION = NOT_VERIFIED
```

Do not preserve an old PASS.

---

# 13. Required test order

## A. Targeted blockers

```text
fixture isolation
cache isolation
opening cash reconciliation
generic FORBIDDEN
evidence reauthorization
numeric grounding
model failure fallback
```

## B. Deterministic AI002 regression

```text
gold no-future-event
gold changing path
30 EOD points
first negative date
zero boundary
settled schedule exclusion
due-date-only exclusion
```

## C. Shared Lotus Fin / AI001 regressions

Verify security/observability changes do not break prior features.

## D. Docker/Frappe integration

Run when available.

## E. UI/E2E

```text
fixture absent from normal UI/API
company switch
late stale response
FORBIDDEN cleanup
evidence auth
explanation UNAVAILABLE
```

---

# 14. G4B re-validation gate

Do NOT mark G4B PASS until all mandatory items below have reproducible evidence:

```text
[ ] normal API cannot enable fixture source
[ ] normal UI cannot enable fixture source
[ ] fixture/live cache isolation
[ ] opening cash uses explicit authorized account scope
[ ] GL/TB reconciliation is actually executed
[ ] false reconciliation status impossible
[ ] generic FORBIDDEN leaks no company/resource identity
[ ] cross-company cache isolation
[ ] stale response rejected after company switch
[ ] prior-company UI data cleared
[ ] evidence reauthorization is wired and tested
[ ] hallucinated numeric claim rejected
[ ] altered date/company/currency claims rejected
[ ] model failure → explanation UNAVAILABLE
[ ] prompt injection does not alter tools/policy
[ ] PII/logging canary passes
[ ] deterministic API E2E passes
[ ] UI E2E passes
[ ] exactly one active SSOT
[ ] current test evidence is reproducible
```

If any mandatory item fails:

```text
G4B = PARTIAL / FAIL
AI002-08 = NOT_APPROVED
FEATURE_CLOSED = false
```

---

# 15. Documentation — update only after runtime passes

After code and tests, reconcile:

```text
AI002_MASTER_SSOT_V1_2_1_REFINED.md
AI002_TECHNICAL_DOCUMENTATION.md
AI002_SECURITY_SELF_ASSESSMENT.md
AI002_TONG_HOP_KET_QUA_TRIEN_KHAI.md
AI002_IMPLEMENTATION_TASK_PACKET_ANTIGRAVITY_REFINED.md
```

## Security Self-Assessment

No `PASS` without evidence.

For each invariant record:

```text
status
test name
environment
command
result
known limitation
```

Re-evaluate especially:

```text
authorization
tenant isolation
fixture/live isolation
cache isolation
evidence reauthorization
PII logging
prompt injection
numeric grounding
model failure resilience
```

## Technical Documentation

Remove any claim not reproduced by runtime/tests.

Especially verify before claiming:

```text
Trial Balance reconciliation
grounded explanation
zero-leakage FORBIDDEN
evidence reauthorization
cache isolation
```

## Completion Report

Do not say `AI002-02 → AI002-08 complete` until G4B and Feature Closure really pass.

Use truthful intermediate status when necessary.

---

# 16. AI002-08 Feature Closure remains mandatory

Do not mark `FEATURE_CLOSED` until all of the following are synchronized with tested behavior:

```text
AI002_TECHNICAL_DOCUMENTATION.md
AI002_SECURITY_SELF_ASSESSMENT.md
README / deployment / test instructions
execution evidence
reproducible demo path
deck-ready summary
third-party license/provenance review
```

Preserve sanitized execution evidence for the competition package.

---

# 17. Forbidden remediation shortcuts

Do NOT:

```text
weaken the contract to make tests pass
label synthetic data as real
hide source failure as zero
trust a client fixture flag
trust LLM numerical output
mark reconciliation without reading Trial Balance
claim Docker PASS without running Docker
edit reports to PASS before runtime passes
create another active SSOT
```

---

# 18. Expected final state

Only if evidence supports it:

```yaml
contract:
  status: AI002_01_CONTRACT_FROZEN
implementation:
  status: IMPLEMENTED
G4B:
  status: PASS
AI002_08:
  status: PASS
feature:
  status: FEATURE_CLOSED
user_ready: true
competition_ready: true
real_business_data_ready: false
```

`real_business_data_ready` may remain false until an authorized real settlement-date source / SME dataset exists, as long as the feature fails closed truthfully.

---

# 19. Final Antigravity response

Return a concise remediation report.

## A. Critical fixes

For each:

```text
problem
root cause
files changed
fix
tests
result
```

## B. Test evidence

Exact commands and exact counts.

## C. G4B checklist

PASS / FAIL item-by-item.

## D. Documentation reconciliation

What was downgraded/upgraded and why.

## E. Final status

Exactly:

```text
Contract:
Implementation:
G4B:
AI002-08:
Feature Closure:
User-ready:
Competition-ready:
Real-business-data-ready:
```

## F. Remaining blockers

Only real unresolved blockers.

---

# FINAL PRINCIPLE

```text
Fix runtime truth first.
Then prove it.
Then document it.
Never reverse that order.
```
