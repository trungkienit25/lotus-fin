# Lotus CORE / DEMO E2E matrix

13 October 2026 · Asia/Saigon · Independent acceptance of `E:/lotus-fin`.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. The candidate is current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push, merge or deployment was performed. Tests used only local fixtures and the previously qualified isolated `lotus-core-01a13314` / `core-01a13314.localhost` / loopback 8097. N0 remains BLOCKED.

Evidence directory: [p3-independent-2026-10-13](docs/reviews/evidence/p3-independent-2026-10-13). Exact candidate: [CANDIDATE_SOURCE.json](docs/reviews/evidence/p3-independent-2026-10-13/CANDIDATE_SOURCE.json), 616 files, SHA256 `02da08611f41de6e9ceff876e95bf48e11150cf9cdbe8e06819f816ae3cb8c70`. Every executed test command, inner-command exit code and output hash is in [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p3-independent-2026-10-13/COMMANDS_AND_EXITS.json). Collector shells may exit 0 after recording a failed child; use the recorded child exit. Failed attempts are retained.

| Layer / case | Verdict | Actual evidence and limit |
|---|---|---|
| CORE framework startup | PASS | Frappe-only real nginx/backend/DB/Redis/workers/websocket/scheduler |
| CORE active ordinary session + valid POST CSRF | PASS | Real 503; no source/ref/record minted |
| CORE disabled existing principal | FAIL | Persisted disabled ordinary User still admitted through original cookie |
| CORE revoked cookie after logout | PASS | Explicit old cookie replay 401 |
| Qualified canonical /copilot | FAIL | Real authenticated GET 404 |
| Current React CORE application path | FAIL | Through transparent QA proxy, CSRF fails; raw framework error becomes INVALID_RESPONSE |
| DEMO actual app NORMAL Search→Select→Open | PASS, limited | Actual built app, no HTTP interception; requires select profile then Chat→Invoices remount workaround |
| DEMO PARTIAL | PASS after remount | Three rows, no actionable selections; without remount NORMAL rows remain selectable (FAIL) |
| DEMO EMPTY | PASS after remount | Clear empty notice |
| DEMO FORBIDDEN | PASS after remount | Context absent, search disabled, permission notice |
| DEMO EXPIRED | PASS after remount | Context cleared, restart prompt |
| DEMO STALE version scenario | PASS after remount | Search then explicit Open rejected, context cleared |
| DEMO forged/cross-scope refs | FAIL | Four direct-provider assertions fail; no context/version/instance enforcement |
| DEMO→CORE mounted source isolation | FAIL | DEMO rows visible under CORE banner |
| CORE→DEMO mounted activation | FAIL | Retains CORE transport until unmount/remount |
| Deterministic supported/clarification/L3 intent | PASS, bounded | Text recognizes intent or asks criteria; user must re-enter/action in tab |
| Unsupported main chat explanation | CHANGES_REQUIRED | Safe generic unqualified notice; does not explain supported intent set |
| Page and drawer mounts | CHANGES_REQUIRED | Both use same faulty profile/controller and missing CSRF initialization |
| Loading/cancellation | PASS units / NOT_RUN complete serving UI | Generation/AbortSignal/unmount tests pass; no explicit user cancel control qualified |
| Logout protected-state clearing | PASS limited | Actual app logout then /copilot revisit redirects to login; component unmount/late-response tests pass |
| Scope change | PASS component tests / FAIL mounted profile changes | Actor/session/context identity not included in invoice scope key |
| L3 local lifecycle | PASS | Current app Prepare→Edit→Review→Copy→Discard plus controlled-clock TTL/clipboard race tests |
| Mobile / accessibility | CHANGES_REQUIRED | 390px default sidebar clips chat/tabs/composer; unnamed button/selector |
| Native successful financial Search/Open | BLOCKED | N0 absent; no ERP, synthetic or Administrator substitute |

## Serving provenance

The qualified image serves backend CORE 8097 and has old frontend assets. A transparent audit-only proxy on 5197 served the current npm-built React app with explicit SPA fallback and forwarded real HTTP to owned CORE 8097. `/qa-session` obtained only the existing ordinary synthetic QA cookie through actual Frappe login. Browser actions used the current actual application path and local DEMO provider; no API response interception supplied demo results. This support proxy is not shipped production routing, not a second business server, and cannot repair the 8097 /copilot gate. It was removed after assessment. The current app self-generated synthetic DEMO records; those are not business truth.

The retained eight pytest browser cases and 39 independent P2-B React checks use separately mounted components with intercepted HTTP. They are fixture acceptance, never real-serving CORE/financial E2E. Recorded current app observations: chat-intents.json, demo-ui-{PARTIAL,EMPTY,FORBIDDEN,EXPIRED,STALE}.txt, l3-app-lifecycle.txt, drawer-core-error.txt, after-ui-logout-revisit.txt, mobile-copilot.png and core-demo-crossover-dom.txt.

## Fresh regression results

| Check | Result | Inner exit |
|---|---|---|
| Backend documented P1/P2-A suite, Pydantic/HMAC v2/config/controller/security | 438 passed | 0 |
| Frappe-only admission/CSRF unit boundary | 21 passed | 0 |
| AI001/AI002/AI003 impacted suites | 393 passed, 7 subtests passed | 0 |
| Current frontend P2-B/L3/P3 Node tests | 95 passed, zero skips | 0 |
| Retained independent Node oracles | 23 + 96 + 41 checks passed | 0 each |
| Independent backend/wire oracles | 36 wire; 36 source + 12 extra source-axis checks passed | 0 each |
| Independent P2-B React oracle | 39 checks passed; intercepted synthetic HTTP | 0 |
| Independent L3 oracle / React oracle | 16 / 11 checks passed | 0 each |
| Existing B1-S/P2-B/L3 browser fixtures | 8 pytest cases passed; intercepted fixture HTTP | 0 |
| New DEMO scope/forgery oracle | Four FAIL observations, all incorrectly 200 | 1 |
| Actual isolated CORE baseline HTTP | 15 cases passed | 0 |
| Extended real CORE observations | 32 observations; security failures explicitly recorded | 0 collector, not a PASS gate |
| Clean frontend install | npm ci, 378 packages | 0 |
| Clean full TypeScript + Vite | npm run build | 0 |
| Clean whole frontend oxlint | 0 errors, 86 warnings; conditional hooks fixed | 0 |
| Requested ESLint | Module/config absent | 1 / NOT_RUN tool gate |
| npm audit | 8 high, 2 moderate affected package entries | 1 |
| Broad backend pytest | Four collection errors; three host framework imports and one real test/source mismatch | 2 |
| Git diff whitespace check | Trailing whitespace/EOF findings | 2 |

Counts are per suite and overlap; do not sum them as unique coverage. FIN-F01/F06/F07/F08/F09/F12, malformed envelopes, source/context pins, explicit selection, race/abort/expiry, B1-S no-call behavior, L3 clipboard revision/TTL/unmount are covered by the retained tests. They did not previously exercise live profile switching in VercelChatPanel. No failing security assertion was edited or skipped. Host sandbox EPERM failures for TS build/cache and Vite temp files were retained, then the exact npm build passed outside the sandbox. The first audit DEMO oracle had a bad relative import; the corrected oracle actually exercised the source and failed four assertions. Initial QA toggle probes used the wrong Frappe working directory and failed before mutation; corrected probes assert persisted disabled state and restore it. Retained UI23 initially lacked regenerated wire samples; it passed after the current backend oracle generated them.
