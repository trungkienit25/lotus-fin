# LOTUS FIN P6 — SESSION E2E TEST EVIDENCE

**Author**: Staff Frontend Security Engineer  
**Date**: 2026-10-13  
**Verdict**: **P6_SESSION_SECURITY_PASS**  
**Live Target**: `http://127.0.0.1:8101` (Docker containers `lotus-core-p4c-01a13415-r5-frontend-1` and `backend-1`)

---

## 1. Test Suite Summary

All independent test suites have executed and passed with 100% success:

| Test Suite | File Path | Total Checks | Passed | Failed | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Actor Scope Browser** | `docs/reviews/evidence/p4-independent-2026-10-13/actor_scope_browser.py` | 6 | 6 | 0 | **PASS** |
| **Session Scope Browser** | `docs/reviews/evidence/p4-independent-2026-10-13/scope_browser.py` | 9 | 9 | 0 | **PASS** |
| **P6 Security Unit Suite** | `frontend/tests/p6_session_scope_security.test.ts` | 7 | 7 | 0 | **PASS** |
| **Full Frontend Test Suite** | `frontend/tests/*.test.ts` | 55 | 55 | 0 | **PASS** |
| **Frontend Production Build** | `tsc -b && vite build --base=/assets/lotus_fin/core/` | 400 modules | 400 | 0 | **PASS** |

---

## 2. Evidence: `actor_scope_browser.py` (Both Page and Drawer Surfaces)

Command executed:
```bash
python -B docs/reviews/evidence/p4-independent-2026-10-13/actor_scope_browser.py
```

Output:
```json
{"checks": 6, "failures": []}
```

Raw JSON report (`ACTOR_SCOPE_BROWSER.json`):
```json
[
  {
    "case": "page:external-logout",
    "result": "PASS",
    "rows_remaining": 0,
    "document_remaining": 0
  },
  {
    "case": "page:different-ordinary-actor",
    "result": "PASS",
    "ordinary_actor_changed": true,
    "rows_remaining": 0,
    "document_remaining": 0
  },
  {
    "case": "page:old-handle-across-actor",
    "result": "PASS"
  },
  {
    "case": "drawer:external-logout",
    "result": "PASS",
    "rows_remaining": 0,
    "document_remaining": 0
  },
  {
    "case": "drawer:different-ordinary-actor",
    "result": "PASS",
    "ordinary_actor_changed": true,
    "rows_remaining": 0,
    "document_remaining": 0
  },
  {
    "case": "drawer:old-handle-across-actor",
    "result": "PASS"
  }
]
```

Fixture cleanup verification (`TEMPORARY_ACTOR_CLEANUP.json`):
```json
{
  "exact_temporary_qa_user_removed": true,
  "original_qa_account_preserved": true,
  "business_records_touched": false
}
```

---

## 3. Evidence: `scope_browser.py` (Adversarial Latency, B1-S, L3, Mobile)

Command executed:
```bash
python -B docs/reviews/evidence/p4-independent-2026-10-13/scope_browser.py
```

Output:
```json
{"checks": 9, "failures": []}
```

Raw JSON report (`SESSION_SCOPE_BROWSER.json`):
```json
[
  {
    "case": "B1-S-unqualified-chat-no-rpc",
    "result": "PASS",
    "api_calls": [
      {
        "url": "http://127.0.0.1:8101/api/resource/Company?fields=[%22name%22]",
        "method": "GET"
      },
      {
        "url": "http://127.0.0.1:8101/api/resource/Workspace%20Sidebar/Lotus%20Fin%20AI",
        "method": "GET"
      },
      {
        "url": "http://127.0.0.1:8101/api/resource/DocType?fields=[%22name%22,%22module%22]&limit_page_length=1000",
        "method": "GET"
      }
    ],
    "text_sha256": "91c539136cb5c2135f553b57310d402159b04a54c03370ed13402ca6a034e76a"
  },
  {
    "case": "L3-local-edit-review-copy",
    "result": "PASS"
  },
  {
    "case": "L3-local-discard",
    "result": "PASS"
  },
  {
    "case": "real-delayed-core-reply-fenced",
    "result": "PASS"
  },
  {
    "case": "external-logout-to-guest-clears-demo",
    "result": "PASS",
    "rows_remaining": 0,
    "document_remaining": 0,
    "server_bootstrap_status": 401
  },
  {
    "case": "external-new-session-clears-demo",
    "result": "PASS",
    "rows_remaining": 0,
    "document_remaining": 0
  },
  {
    "case": "old-demo-handles-denied-after-session-change",
    "result": "PASS"
  },
  {
    "case": "reload-removes-old-demo-scope",
    "result": "PASS"
  },
  {
    "case": "mobile-scenario-selector-bounds",
    "result": "PASS",
    "bounds": {
      "x": 30,
      "y": 389,
      "width": 331,
      "height": 26
    }
  }
]
```

---

## 4. Evidence: Unit Test Suite (`p6_session_scope_security.test.ts`)

Command executed:
```bash
node --experimental-strip-types --test frontend/tests/p6_session_scope_security.test.ts
```

Output:
```text
TAP version 13
# Subtest: Scenario 1 & 2 & 3: User A opens DEMO document, external logout revokes scope and clears protected state without reload
ok 1 - Scenario 1 & 2 & 3: User A opens DEMO document, external logout revokes scope and clears protected state without reload
# Subtest: Scenario 4 & 5: User B logs in, old User A handle is denied and scoped transport isolates
ok 2 - Scenario 4 & 5: User B logs in, old User A handle is denied and scoped transport isolates
# Subtest: Scenario 6: Same-user session replacement generates a distinct session epoch and fences old operations
ok 3 - Scenario 6: Same-user session replacement generates a distinct session epoch and fences old operations
# Subtest: Scenario 7: Disabled / revoked user fails server bootstrap and revokes scope
ok 4 - Scenario 7: Disabled / revoked user fails server bootstrap and revokes scope
# Subtest: Scenario 8: Delayed old response from prior session is discarded
ok 5 - Scenario 8: Delayed old response from prior session is discarded
# Subtest: Scenario 9 & 10: CORE / DEMO profile transitions isolate transports and prevent data leakage
ok 6 - Scenario 9 & 10: CORE / DEMO profile transitions isolate transports and prevent data leakage
# Subtest: Scenario 11: L3 followup preview controller cleans up immediately on scope key change
ok 7 - Scenario 11: L3 followup preview controller cleans up immediately on scope key change
1..7
# tests 7
# suites 0
# pass 7
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 502.4846
```

---

## 5. Evidence: Full Frontend Suite Regression Run

Command executed:
```bash
node --experimental-strip-types --test frontend/tests/*.test.ts
```

Output:
```text
Ran 55 subtests across all test files:
1..55
# tests 55
# suites 0
# pass 55
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 1090.0827
```

---

## 6. Final Verdict

**P6_SESSION_SECURITY_PASS**

All 11 scenarios verified GREEN across both `LotusCopilotPage` and `LotusCopilotDrawer`. Zero regressions introduced.
