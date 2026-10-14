# P6 independent acceptance — P6_SECURITY_BLOCKED

Independent Staff Security / Full-Stack QA / Release review, 13–14 October 2026, Asia/Saigon. Repository `E:/lotus-fin`; branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Evaluated current integrated working-tree bytes and existing loopback P6 runtime. Earlier P4 and P6-0/1/2/3/4 reports were read as claims, not adopted verdicts. No source correction, stage, commit, push or deployment was performed.

**The candidate is not ready for a reviewed commit. P4-F01 remains open.** The original logout/actor-switch path is substantially corrected, but actual visible Page and Drawer still retain and use fictional invoice handles after server-side session revocation. A late bootstrap also resurrects revoked frontend scope. Server-side auth/CSRF and native fail-closed boundaries passed the examined cases; native financial disclosure or real external execution was not demonstrated.

| Mandatory acceptance | Independent verdict |
| --- | --- |
| 1. Two ordinary users/sessions and Page/Drawer leak replay | Executed actual Alice/Bob browser flows plus separate same-user HTTP sessions. External logout/actor replacement clears; remote revoke fails on both visible mounts. |
| 2. P4-F01 including external logout, rotation, stale async | NOT_CLOSED: focus-based rotation clearing passes; continuous active-tab detection and old-bootstrap publication fail. |
| 3. L4 explicit confirmation / adapter / durable status / duplicate/concurrent/revoke/crash/UNKNOWN | PASS for examined isolated simulation paths; actual browser Page/Drawer, real concurrent HTTP, independent child-process rollback/UNKNOWN reconciliation. Native write BLOCKED. |
| 4. L5 enforcement and external effects | PASS_DISABLED_BOUNDARY: five families deny/review only; arbitrary execute actions reject; absent prepare/approve/execute/reconcile routes 403. Real adapter qualification BLOCKED. |
| 5. V1 exact predicate/date/Decimal/currency/source/gold | Fixed HTTP/browser gold passes; independent22-case oracle finds four failures. CHANGES_REQUIRED. |
| 6. Integrated React browser workflows | Executed Page L1→L2→L3→L4, Page/Drawer L4 and V1, Page L5, L0 clarification, profile and session transitions. Scope/remaining cases in matrix. |
| 7. Frappe-only runtime | PASS: installed apps exactly frappe + lotus_fin; erpnext import and three ERP finance schemas absent. |
| 8. CORE/DEMO isolation and forgery | PASS examined header/query/profile/authority negatives and actual CORE UI clearing; unqualified native data never supplied. |
| 9. Actual HTTP/CSRF/no-store/invalidation/audit/outcomes | PASS scoped HTTP/store checks; frontend invalidation FAIL; simulation audit is not native outcome-audit qualification. |
| 10. Source-to-serving-image identity | PASS scoped:331 backend files and independently rebuilt JS/CSS match six containers and actual HTTP assets. |
| 11. Relevant P1/P2/L3/AI001–003/P6 tests | 507 backend +124 frontend pass; separate AI selection376 +7 subtests pass; P6 subset67 overlaps. Full collection968 has four errors. |
| 12. CI/source staging/locks/dependency security | Empty staging preserved, whitespace/build/lint/lock dry-run/pip consistency pass; CI regression scope and advisory closure remain incomplete. |
| 13. Simulation documentation | README/integrated docs truthful; module “production-ready,” endpoint and session timing claims remain wrong. CHANGES_REQUIRED. |
| 14. Developer commit vs native release vs G10 | Developer readiness withheld for concrete defects. N0, real L4/L5, native V1/full-product finance and G10 separately BLOCKED. |

The serving image is `sha256:5264a4c2d7992fdeaa69f40c041752b8cfdb3849f2a852ab536eb1075737c256`, existing site `core-p6-01a1358e.localhost`, port8114. No build/deployment or restart of that stack occurred in this independent review. A local frontend build and read-only container/HTTP comparisons verified image identity. Builder cold-restart evidence was reviewed without claiming an independent repeat.

The independent oracle creates its own boundary observations and expected decisions rather than using builder PASS labels. Fixed gold is DEMO-INV-001:12 days/15000000.00 VND and DEMO-INV-002:8 days/2850000.50 VND at the explicitly fictional October13 observation. This remains fixed DEMO data after the review crosses midnight into October14.

Read [P6_SECURITY_RECHECK.md](P6_SECURITY_RECHECK.md), [P6_FULL_E2E_MATRIX.md](P6_FULL_E2E_MATRIX.md), [P6_PRODUCT_INDEPENDENCE.md](P6_PRODUCT_INDEPENDENCE.md), [P6_SOURCE_PRE_PUSH.md](P6_SOURCE_PRE_PUSH.md), and [P6_RELEASE_DECISION.md](P6_RELEASE_DECISION.md). The release decision names twelve exact defects and one narrow correction batch for each. No further general architecture redesign is requested.

Evidence directory: `docs/reviews/evidence/p6-independent-2026-10-13/`. Source probes/collectors can exit0 while recording failed observations; their behavioral results, not their collector exit, determine acceptance. Counts overlap across suites. Browser390px, broad accessibility, live network-fault injection and independent serving restart are explicitly unqualified; no hidden PASS is substituted.
