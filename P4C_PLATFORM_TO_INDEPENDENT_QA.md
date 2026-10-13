# P4-C platform handoff to independent QA

Date: 2026-10-13. Final candidate is frozen at [`CANDIDATE_SOURCE_R5.json`](docs/reviews/evidence/p4c-2026-10-13/CANDIDATE_SOURCE_R5.json), SHA-256 `2600017e48b01eee74b788f2ebbbbb39689baf1a0d2a49851603b92b42244c8e`. Use the isolated `lotus-core-p4c-01a13415-r5` project at `http://127.0.0.1:8101/copilot`. After the user recovered Docker, P4-C corrected missing database/Redis restart policies and verified automatic dependency recovery plus full isolated cold start. P4-A and P4-B source was present before this frozen build. The old port 8097 target was untouched.

| Gate | P4-C verdict | Evidence / qualification limit |
| --- | --- | --- |
| `CANONICAL_COPILOT_ROUTE` | **PASS** | Authenticated direct route and refresh, guest redirect, qualified fallback and asset base on r5. |
| `CSRF_BOOTSTRAP` | **PASS** | Actual Frappe current-session token, real protected POST, invalid/missing token denial and logout replay. |
| `REAL_AUTHENTICATED_CORE_HTTP` | **PASS** | Ordinary browser mount → one native `get_context` POST → exact 503 disabled envelope; 19 checks before and after restart. |
| `CURRENT_SOURCE_IMAGE` | **PASS** | Frozen 517-file source, locks, 334 backend hashes, bundle/private HTML hashes and exact image/container identity; zero drift. |
| `ERP_FREE_RUNTIME` | **PASS** | Only Frappe and Lotus app; ERPNext import/install, legacy hooks and business schemas absent. |
| `N0_NATIVE_DATA_AUTHORITY` | **BLOCKED** | No native invoice data authority; 503 `CAPABILITY_DISABLED` is the required truthful result. |

P4-C source tests: 114 frontend checks, 9 renderer checks, and frontend lint passed. The final r5 integrated-image recheck also passed after a cold restart. **Independent QA replay remains pending**; platform's PASS records only the checks actually run on this isolated candidate. The older r2 diagnostic image passed 16 checks but is superseded and does not support the final gate.

QA should replay [`real_core_browser.py`](docs/reviews/evidence/p4c-2026-10-13/real_core_browser.py) on the owned r5 site, inspect [`REAL_CORE_HTTP_BROWSER.json`](docs/reviews/evidence/p4c-2026-10-13/REAL_CORE_HTTP_BROWSER.json) and [`RUNTIME_PROVENANCE.json`](docs/reviews/evidence/p4c-2026-10-13/RUNTIME_PROVENANCE.json), and verify current source manifest drift remains empty. This P4-C result does not qualify full financial operations, legacy module routes, native invoice search/open, or overall product release. No commit, push, shared deployment, or business-data mutation occurred.

The stale graph index and repository-wide CRITICAL change assessment remain separate commit-readiness limits, documented in [`GRAPH_ASSESSMENT.md`](docs/reviews/evidence/p4c-2026-10-13/GRAPH_ASSESSMENT.md). These are not reported as clean checks. Disk preservation details are in [`DISK_PRESERVATION.md`](docs/reviews/evidence/p4c-2026-10-13/DISK_PRESERVATION.md).

The hash-bound closing receipt is [`P4C_FINAL_RECEIPT.json`](docs/reviews/evidence/p4c-2026-10-13/P4C_FINAL_RECEIPT.json). Detailed reports:

- [Canonical routing and CSRF](P4C_CANONICAL_ROUTING_AND_CSRF.md)
- [Real CORE HTTP/browser evidence](P4C_REAL_CORE_HTTP_BROWSER_EVIDENCE.md)
- [Serving image provenance](P4C_SERVING_IMAGE_PROVENANCE.md)
- [CORE startup and restart](P4C_CORE_STARTUP_AND_RESTART.md)
