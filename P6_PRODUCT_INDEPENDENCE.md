# P6 product independence

Independent review, 13–14 October 2026, Asia/Saigon. The existing isolated serving image is `sha256:5264a4c2d7992fdeaa69f40c041752b8cfdb3849f2a852ab536eb1075737c256`. Six app containers use it with no source bind mounts.

**CORE runtime independence passes within the disabled-native shell. Full financial product independence remains unqualified and BLOCKED.**

| Boundary | Independent evidence / verdict |
| --- | --- |
| Installed runtime | Exactly frappe + lotus_fin; erpnext import not found |
| ERP finance schemas | Company, Sales Invoice and GL Entry are absent in the actual site |
| React serving and ordinary auth | Actual `/copilot` and `/home` drawer work through Frappe; no ERPNext is needed for tested auth/DEMO composition |
| Native invoice source | CORE returns 503; fictional provider is not a native fallback |
| DEMO activation | Strict body profile plus server boolean; client actor/company/adapter overrides reject |
| L4 | Allowlisted isolated fictional Task/Note/Draft operations; actual production write port refuses precheck/execution |
| L5 | Integrated catalog/policy review only; unapproved execution routes cannot compose a real adapter |
| V1 | Exact fixed fictional gold displays; native provider remains unavailable; reusable contract has independent failures |
| AI001–AI003 financial runtime | Tests pass for chosen algorithms/contracts, but actual legacy sources remain ERP-derived |
| N0 / G10 | BLOCKED; no approved native authority, source reconciliation or external-action qualification supplied |

The remaining source dependencies are concrete: `lotus_fin/lotus_fin/modules/f001_health/extractors.py` consumes ERP-shaped financial extraction; `modules/f002_cashflow/adapters.py` consumes Company/Account, Sales Invoice, Payment Entry and Journal Entry semantics; `modules/f003_risk_signal/sources.py` consumes ERP report and Purchase Invoice schedule semantics. Framework-only import/install success cannot qualify these sources. Existing legacy RPCs are denied by `runtime/boundary.py` unless the separate ERP integration qualification is enabled with its required apps.

The native-source gap is a qualification hold, not a request to create a new financial schema. Narrow next batch for N0: obtain the source/tenant/document/field/version authority decision and an independently reconciled read-only source mapping; keep current fail-closed stubs until that evidence exists. Real L4 writes and each L5 family need separate target, adapter, approval, delivery/outcome and audit qualification. DEMO receipts do not satisfy those gates.

Current README, P6 integrated technical documentation and judge runbook distinguish simulation from production capability. `P6_L4_IMPLEMENTATION_REPORT.md` still calls the engine “production-ready,” while its original ledger is in memory and the integrated durable store is explicitly fictional. `P6_L4_TO_INTEGRATION.md` still advertises a class-method endpoint that is not the registered Frappe route. `P6_SESSION_SCOPE_HANDOFF.md` claims unconditional ≤200ms clearing and describes the client epoch as server-derived. Those claims must be narrowed/corrected (IA10); they cannot be used as release evidence.

Evidence: `runtime-apps.txt`, `runtime-schema-audit.txt`, `PROVENANCE.json`, `HTTP_INDEPENDENT.json`, and `HTTP_BOUNDARY_EXTRA.json` in the independent evidence directory. Builder cold-restart evidence was reviewed but not independently repeated; no deployment/rebuild of the serving stack was performed.
