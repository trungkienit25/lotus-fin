# P6 full independent E2E matrix

Review period: 13–14 October 2026, Asia/Saigon. Target: existing Frappe-only P6 candidate at `http://127.0.0.1:8114`. Browser rows below use actual served React and ordinary QA users, not component fixtures. No verdict is inherited from the builder.

| Acceptance case | Layer / surface | Result and evidence |
| --- | --- | --- |
| Former P4 leak setup: search three invoices, select and open | Browser Page/Alice and Drawer/Bob | PASS setup; DEMO-SINV-2026-001 opened explicitly |
| External logout clears protected results and disables actions | Browser both existing mounts | PASS after completed logout/return to focus; zero retained documents or old Open controls |
| Second ordinary actor without protected-state restoration | Browser both mounts | PASS after Bob login; old documents absent without reloading the protected mounts |
| Same actor, replacement session | Real HTTP and browser focus revalidation | Cross-session confirmation denied; both mounts clear on focus. Continuous active-tab detection FAIL (IA01) |
| Remote server revocation with unchanged actor cookie | Browser visible Page and visible Drawer | FAIL: three rows + one document retained; old handle opens another invoice; `document.hidden=false` |
| Stale bootstrap completion after invalidation | Executed current TypeScript source | FAIL: old response publishes VERIFIED/Alice (IA02); live network-delay injection NOT_VERIFIED |
| Stale protected feature response after scope/profile change | Frontend supplied tests | PASS assertions; does not cover bootstrap-publication race |
| L0 clarification in CORE | Browser Page | PASS scoped: actual request receives truthful L0 clarification; not qualified native analytics |
| L1 → selected L2 → L3 prepare/edit/review | Browser Page | PASS; three fictional rows, explicit Open, local draft and explicit review |
| L3 reviewed text → editable L4 form | Browser Page | PASS; literal user text transferred, no financial facts invented |
| L4 propose → separate confirmation → test adapter receipt | Browser Page and Drawer | PASS, visibly SIMULATED_SUCCEEDED. IDs `op_2b5ba2edaae00d03178d24ffa7e58cae` and `op_9a24255f5d449016142d7136ae02a125` |
| L4 status refresh | Browser Page / real HTTP | PASS simulation receipt; durable fresh-composition reads also pass |
| Wrong challenge / actor / session / revoked role | Real HTTP plus integration tests | PASS denials; revoked role tested in service suite, not live role mutation |
| Repeated and four concurrent confirmations | Real HTTP and store integration | PASS one operation and execution_attempts=1 |
| Cancelled/expired proposal | Supplied integrated service tests | PASS; browser expiry and cancellation replay NOT_VERIFIED |
| Abrupt process death before commit | Independent child process + current SQLite composition | PASS exit 79, no operation/fictional target survives; retry creates one receipt |
| UNKNOWN_OUTCOME after possible commit | Independent process/store composition | PASS survives process exit; confirmation replay remains UNKNOWN; reconciliation succeeds with one attempt |
| Audit storage failure | Independent temporary SQLite trigger / supplied tests | PASS pre-admission rollback; live serving-store outage injection NOT_VERIFIED |
| L5 policy review | Browser Page | PASS, approval provider unavailable and side effects disabled |
| All five L5 families | Real HTTP and backend tests | PASS denial/review-only; execution actions invalid; absent approve/execute routes 403 |
| V1 integrated fixed gold | Browser Page and Drawer, actual HTTP | PASS two exact rows: 12/8 days, 15000000.00/2850000.50 VND; no selectable native references |
| Independent eligibility oracle | Current model/evaluator/service | 22 observations, 18 PASS / 4 FAIL: naive timestamp, invalid currency, omitted completeness, absent source evidence |
| Native/core V1 source unavailable | Provider tests and actual CORE HTTP | PASS fail-closed disabled-provider behavior; reusable malformed-source path FAIL |
| CORE cannot activate DEMO via headers/query | Actual HTTP, four actions | PASS 503; strict body profile wins over forged transport selectors |
| Client-forged authority/adapter fields | Actual HTTP | PASS 400 for all five fields |
| DEMO → CORE stale UI clearing | Browser Page; frontend tests | PASS old gold rows disappear; CORE unavailable labels shown |
| Guest, missing/invalid CSRF, logout cookie replay, method restriction | Actual HTTP | PASS: 401 / 400 / 401 / 403; no examined traceback |
| Actual no-store headers | Actual SPA/bootstrap/503/400/401/403 | PASS; receipts record exact headers |
| Runtime ERPNext absent | Container/module/database inspection | PASS apps exactly frappe + lotus_fin; no erpnext import; Company/Sales Invoice/GL Entry absent |
| Source → built assets → image → HTTP serving | Independent local build + six containers + HTTP hashes | PASS scoped: 331 backend files, JS/CSS bytes match; no source bind mounts |
| Desktop Drawer selector fits its container | Actual DOM geometry | FAIL: right=1288.6, drawer right=1256 at width420 (IA12) |
| 390px mobile closure / broad accessibility | Browser viewport attempt | NOT_VERIFIED: override did not change actual document widths; no inherited 390px or WCAG PASS |
| Live cold restart / serving-process crash | This independent turn | NOT_REEXECUTED; builder receipt read only. Isolated child-process crash is a distinct test |
| Native financial writes / external delivery / G10 | Qualification | BLOCKED |

Test execution receipts: 507 backend invoice/action/session/P6 regression checks pass; separately 67 P6 checks pass (overlap); 124 frontend checks pass with zero skips; AI001–003 selection passes 376 tests + 7 subtests. Broad host collection still has 968 collected tests and four errors. These counts overlap and must not be added as unique coverage.

Browser observations are manually recorded from the tool's DOM/AX results in `BROWSER_OBSERVATIONS.json`. Native date-control fill initially did not update React state; keyboard input generated the change event and proposal review displayed the final date 2026-11-20. This was a test-driver recovery, not a product-date defect. Immediate logout snapshots were pending-state observations; PASS is based on settled logout state. No result based solely on a click attempt is accepted.
