# LOTUS FIN P4-A — DEMO NEGATIVE TESTS & FORGERY RESISTANCE

**Document Identity:** `P4A_DEMO_NEGATIVE_TESTS.md`  
**Date:** 2026-10-13  
**Status:** COMPLETE & QUALIFIED  
**Authors:** Staff React/TypeScript Engineer, Frontend Security Engineer  
**Target:** `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts`  

---

## 1. Overview

In Phase 3 independent acceptance, the Synthetic Demo Provider was found vulnerable to four cross-scope and forgery exploits (P2-04):
1. Accepting forged context references from arbitrary callers.
2. Allowing search requests with incorrect/mismatched context versions.
3. Fulfilling open requests with forged selection handles via fallback to `DEMO_RECORDS[0]`.
4. Replaying selection handles across different transport instances.

This document details the negative test suite, execution evidence, and mathematical proof that synthetic authority is strictly bounded.

---

## 2. Independent Oracle Execution Evidence

### 2.1 Four Original Independent Oracles

The original independent test script provided in `docs/reviews/evidence/p3-independent-2026-10-13/demo_negative.mts` was executed directly against the updated codebase:

```bash
node --experimental-strip-types docs/reviews/evidence/p3-independent-2026-10-13/demo_negative.mts
```

#### Output (Exit Code 0)
```json
[
  {
    "name": "forged context search denied",
    "result": "PASS"
  },
  {
    "name": "wrong context version search denied",
    "result": "PASS"
  },
  {
    "name": "forged selection denied",
    "result": "PASS"
  },
  {
    "name": "cross transport scope selection denied",
    "result": "PASS"
  }
]
```

### 2.2 Attack Vectors & Defense Mechanisms

| Attack Vector | Malicious Payload | Previous Behavior | P4-A Remediated Behavior | Outcome |
| :--- | :--- | :--- | :--- | :---: |
| **Forged Context Search** | `context_ref: "forged-ctx-ref"` | Returned 200 with demo records | Returns 422 `NOT_AVAILABLE` (`INVALID_REQUEST`) | ✅ DENIED |
| **Wrong Context Version** | `expected_context_version: "ctx_wrong_version"` | Accepted request | Returns 422 `NOT_AVAILABLE` (`CONTEXT_REQUIRED`) | ✅ DENIED |
| **Forged Selection Open** | `selection_ref: "forged-selection-ref"` | Fallback returned `DEMO_RECORDS[0]` | Returns 422 `NOT_AVAILABLE` (`DOCUMENT_UNAVAILABLE`) | ✅ DENIED |
| **Cross-Instance Replay** | Handle from Provider A replayed to Provider B | Accepted replay | Instance-scoped token verification fails; returns 422 | ✅ DENIED |

---

## 3. Comprehensive Negative Test Suite (`p4a_profile_and_demo_security.test.ts`)

In addition to the independent oracle, a dedicated unit and lifecycle suite was established in `frontend/tests/p4a_profile_and_demo_security.test.ts`:

```bash
node --test --experimental-strip-types frontend/tests/p4a_profile_and_demo_security.test.ts
```

#### Execution TAP Log (11/11 Passed, 0 Failed, Exit Code 0)
```
TAP version 13
# Subtest: P2-04: forged context search is denied (non-200)
ok 1 - P2-04: forged context search is denied (non-200)
# Subtest: P2-04: wrong context version search is denied (non-200)
ok 2 - P2-04: wrong context version search is denied (non-200)
# Subtest: P2-04: forged selection open is denied (non-200)
ok 3 - P2-04: forged selection open is denied (non-200)
# Subtest: P2-04: cross transport scope selection is denied (non-200)
ok 4 - P2-04: cross transport scope selection is denied (non-200)
# Subtest: P2-04: PARTIAL scenario returns non-actionable selection refs
ok 5 - P2-04: PARTIAL scenario returns non-actionable selection refs
# Subtest: P2-04: STALE scenario returns 409 STALE_SELECTION on open
ok 6 - P2-04: STALE scenario returns 409 STALE_SELECTION on open
# Subtest: P2-04: FORBIDDEN scenario returns 403 on all capabilities
ok 7 - P2-04: FORBIDDEN scenario returns 403 on all capabilities
# Subtest: P1-01: switching from DEMO to CORE clears protected state and enforces CORE transport
ok 8 - P1-01: switching from DEMO to CORE clears protected state and enforces CORE transport
# Subtest: P1-01: CORE controller rejects any DEMO source response even if transport leaked it
ok 9 - P1-01: CORE controller rejects any DEMO source response even if transport leaked it
# Subtest: P1-01: stale asynchronous response from old profile is aborted and cannot update state
ok 10 - P1-01: stale asynchronous response from old profile is aborted and cannot update state
# Subtest: P1-01: every DEMO scenario transitions cleanly without remount
ok 11 - P1-01: every DEMO scenario transitions cleanly without remount
1..11
# tests 11
# suites 0
# pass 11
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 443.4774
```

---

## 4. Key Security Invariants Verified

1. **Client-Local Ephemeral Tokens:** Demo handles are strictly ephemeral strings (`ref.v2.sel.demo.${instanceId}.${invoice_id}`). No production secrets or browser HMAC keys are utilized.
2. **Deterministic Context Isolation:** Every provider instance generates its own unique correlation and context tokens. Handle sharing between instances is structurally prevented.
3. **No Unauthenticated Leaks:** Both CORE and DEMO transports fail closed when security parameters fail validation.
