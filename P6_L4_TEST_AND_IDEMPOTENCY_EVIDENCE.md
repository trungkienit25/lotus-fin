# P6 L4 TEST AND IDEMPOTENCY EVIDENCE

**Environment**: Windows 11 · Python 3.13.7 · Pytest 9.0.2 · Pnpm / Vite 8.3.3  
**Date**: 2026-10-13  

---

## 1. Backend Test Execution Log

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.0.2, pluggy-1.6.0
rootdir: E:\lotus-fin\lotus_fin
configfile: pyproject.toml
collected 13 items

lotus_fin\lotus_fin\tests\test_l4_mutation_security.py .............     [100%]

============================= 13 passed in 0.95s ==============================
```

### Verified Test Cases:
1. `test_e2e_successful_proposal_and_confirmation`: Confirms end-to-end proposal generation and isolated write.
2. `test_missing_rights_denial`: Confirms unprivileged user is blocked from draft record preparation.
3. `test_guest_user_denial`: Confirms `Guest` role is explicitly rejected with 403 Forbidden.
4. `test_tampered_or_altered_args_denial`: Proves that modifying arguments between proposal and confirmation causes immediate rejection.
5. `test_different_actor_and_tenant_denial`: Proves that a user from another tenant cannot hijack or confirm a proposal.
6. `test_different_session_denial`: Proves that a proposal bound to session A cannot be confirmed from session B.
7. `test_expired_proposal_denial`: Proves expired proposals transition to `EXPIRED` status and fail.
8. `test_double_click_challenge_reuse_protection`: Proves that clicking confirmation twice returns the existing operation without duplicate execution.
9. `test_concurrent_double_worker_race`: Validates thread-safe lock under multi-worker race conditions; exactly 1 target entity created.
10. `test_unknown_outcome_and_reconciliation`: Proves network timeout leads to `UNKNOWN_OUTCOME` and successful reconciliation recovery.
11. `test_production_write_port_fail_closed`: Proves production write port fails closed.
12. `test_cancellation_flow`: Validates user rejection/cancellation transition to `REJECTED`.
13. `test_controller_endpoints_and_serialization`: Validates HTTP presentation controller contracts and JSON status codes.

---

## 2. Frontend Build Evidence

```text
> frontend@0.0.0 build E:\lotus-fin\frontend
> tsc -b && vite build

vite v8.3.3 building client environment for production...
transforming...
✓ 399 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.85 kB │ gzip:   0.48 kB
dist/assets/index-CLLT4KOO.css   66.86 kB │ gzip:  11.34 kB
dist/assets/index-DfNIPy4p.js   810.52 kB │ gzip: 233.06 kB
✓ built in 5.21s
```
TypeScript compilation and bundler completed with exit code 0.
