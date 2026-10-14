# Lotus P3 independent acceptance

13 October 2026 · Asia/Saigon · Independent acceptance of `E:/lotus-fin`.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. The candidate is current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push, merge or deployment was performed. Tests used only local fixtures and the previously qualified isolated `lotus-core-01a13314` / `core-01a13314.localhost` / loopback 8097. N0 remains BLOCKED.

Evidence directory: [p3-independent-2026-10-13](docs/reviews/evidence/p3-independent-2026-10-13). Exact candidate: [CANDIDATE_SOURCE.json](docs/reviews/evidence/p3-independent-2026-10-13/CANDIDATE_SOURCE.json), 616 files, SHA256 `02da08611f41de6e9ceff876e95bf48e11150cf9cdbe8e06819f816ae3cb8c70`. Every executed test command, inner-command exit code and output hash is in [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p3-independent-2026-10-13/COMMANDS_AND_EXITS.json). Collector shells may exit 0 after recording a failed child; use the recorded child exit. Failed attempts are retained.

**Final decision: SECURITY_BLOCKED.**

DATA_AGNOSTIC_MVP_READY: NO — CHANGES_REQUIRED. FULL_PRODUCT_READY: NO. G10_JUDGE_READY: NO — BLOCKED.

| Gate | Verdict | Evidence / limit |
|---|---|---|
| `P3_FUNCTIONAL_ACCEPTANCE` | **FAIL** | Qualified /copilot returns 404; real mount lacks CSRF initialization; CORE/DEMO controller crossover; mobile clipping. |
| `CORE_AUTHENTICATED_HTTP` | **FAIL** | Ordinary real POST/CSRF/503/CID/no-store work; disabled existing users still admitted. Current React-to-CORE journey fails. |
| `P2B_SECURITY_REGRESSION` | **FAIL** | Retained Node/React decoder/controller tests pass; mounted profile changes violate source fencing. |
| `L3_ACCEPTANCE` | **PASS** | Local fact-free lifecycle: 20 unit cases, 16 independent checks, 11 React checks, fixture E2E and actual app edit/review/copy/discard. No native finance claim. |
| `DEMO_E2E` | **CHANGES_REQUIRED** | Actual app Search→Select→Open works only after explicit tab remount; scenarios retain stale transport without remount. |
| `DEMO_ISOLATION` | **FAIL** | Synthetic records appear under CORE banner; forged references and cross-provider scope accepted. |
| `CORE_ERP_INDEPENDENCE` | **PASS** | Actual isolated startup: only frappe, lotus_fin; ERPNext module and Company/Sales Invoice schemas absent. All 346 backend/support hashes match. |
| `FULL_PRODUCT_INDEPENDENCE` | **FAIL** | Legacy financial providers and exposed route/catalog families still require ERP schemas or lack qualified native replacements. |
| `FULL_FRONTEND_LINT_BUILD` | **CHANGES_REQUIRED** | Clean npm ci and full TS/Vite build pass; oxlint passes; requested ESLint package/config absent. |
| `SOURCE_REPRODUCIBILITY` | **CHANGES_REQUIRED** | Selected source available/hash-bound and clean frontend build reproduced; no staged/committed clean clone and image UI differs from current P3 source. |
| `SECURITY_PRE_PUSH` | **FAIL** | P1 source-profile crossover and disabled-user admission remain; generic RPC error disclosure and dependency review outstanding. |
| `GITHUB_PUSH_READINESS` | **CHANGES_REQUIRED** | Do not push this candidate until security, serving/UI and source/evidence corrections pass. |
| `G10_JUDGE_READINESS` | **BLOCKED** | N0 authority unavailable; independent P3/security gates also fail. Not blocked solely by N0. |

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

## Graph review and authority

Bound repo/index: `lotus-fin`, `E:/lotus-fin`, indexed 2026-10-12T07:02:27.060Z at the same Git HEAD; working-tree/untracked coverage is incomplete. Concept query returned no definitions with FTS disabled. Explicit UID impact on the actual VercelChatPanel returned **HIGH**, 7 impacted symbols, 3 direct callers (LotusCopilotDrawer, LotusCopilotPage and fixture composition), App/UniversalPageView processes and 4 modules. HIGH is not waived by its LOW shared-axis score. New enforce_request_boundary is absent from the index; text inspection follows that unresolved graph result.

`detect-changes --scope all` reports 23 tracked files, 78 symbols, 12 processes, HIGH risk. Rerun with `--limit 500` still prints only 15 symbols/10 flows. This is not a clean graph gate and cannot cover the 140 unstaged/untracked candidate additions/changes or all unindexed source. No commit was attempted. Refresh the actual source index and obtain complete, non-partial/non-truncated change analysis before a future commit; do not quote the builder's “2 files / no breaking changes” as acceptance.

Final CLI status explicitly reports stale. The mandated `analyze --index-only` refresh was attempted and exited 1 after 375.80 seconds: native parse worker startup failed (5000ms readiness limit; bounded self-heal exhausted). No fresh graph acceptance is claimed. Existing risk receipts and source confirmation remain evidence with this coverage limitation. Global tool reinstall or production source changes were not performed to conceal the failure.

Authorities inspected: AGENTS.md, ADR001, Security Code V3, frozen P1/P2-B references, all seven required platform/runtime/N0/inventory reports and all seven current P3 builder reports. Latest user architecture supersedes legacy ERP assumptions and old transport descriptions. All remaining native source/policy approvals stay BLOCKED. Reports are evidence claims, not source authority or human N0 approval.

## Narrow Antigravity correction instructions

**P1-01 — Controller retains DEMO transport and permission under CORE label.** `frontend/src/pages/copilot/actions/useInvoiceActions.ts:21` constructs its controller only once; subsequent `transport` and `allowDemoSource` changes only update `scopeKey`. `VercelChatPanel.tsx:735` changes the profile/scenario without remounting that controller. Reproduce on current actual app: Invoice Actions → DEMO → Chat → Invoice Actions → search `DEMO-SINV` → explicitly Open second row → CORE → Find invoices. Three synthetic rows reappear under “CORE Production Transport Active”; the DEMO badge is absent. CORE→DEMO initially also keeps the CORE transport and fails. Selecting PARTIAL without remount produces complete/selectable NORMAL rows. Evidence: [screenshot](docs/reviews/evidence/p3-independent-2026-10-13/core-demo-crossover.png), [DOM](docs/reviews/evidence/p3-independent-2026-10-13/core-demo-crossover-dom.txt).

Recreate/reset the controller whenever transport/source-profile authorization changes; fence old promises and abort old HTTP before admitting the next profile. Include the supplied presentation/auth context identity in invoice scope clearing, not company/profile alone. Do not keep a controller with `allowDemoSource=true` when CORE is selected. Acceptance: test both profile directions and every scenario without manual tab remount; assert current transport calls, badge/source identity agreement, zero DEMO rows/handles in CORE, protected-state clearing, and delayed old-response rejection. Run on the real mounted page and drawer, not just constructor-level controller tests.

**P1-02 — Persistently disabled user still admitted through an existing cookie.** `lotus_fin/lotus_fin/runtime/boundary.py:22` checks Guest but not current enabled principal. On isolated target: ordinary login and Desk CSRF; save that QA User with `enabled=0` through standard Frappe `doc.save()`; commit and assert DB readback is 0; replay the original cookie. Readiness returns 200; native context reaches handler and returns 503 rather than 401/403. The account is restored in `finally`. Explicit post-logout revoked cookie returns 401. Evidence: `CORE_HTTP_EXTENDED.json`, cases `disabled_user_standard_save_cookie`, `disabled_user_standard_save_native`, `explicit_revoked_cookie_replay`. No financial data leak was demonstrated because native capabilities remain disabled.

Require an enabled, current server principal/session before every CORE request and qualify revocation/cached-session behavior; do not use Administrator as a request fallback. Keep ordinary framework authorization and native grants separate. Acceptance: standard disable and revoked-session cookie replay deny readiness and all three native methods before dispatch; re-enable does not revive an explicitly revoked session; active ordinary users preserve real CSRF and truthful 503 behavior.

**P1-03 — Shipped canonical route and CSRF bootstrap are not complete.** Authenticated `http://127.0.0.1:8097/copilot` returns 404. `/assets/lotus_fin/core/index.html` exists, but baked React inclusion is not routing acceptance. `invoiceActionClient.ts:32` only reads `window.frappe.csrf_token`/`window.csrf_token`; the static React shell initializes neither. On the current-build QA proxy, opening CORE invoices displays INVALID_RESPONSE from a real CSRF failure instead of the truthful N0-disabled notice. Correct the approved server SPA route/base and same-origin authenticated CSRF initialization. Preserve the strict backend token requirement. Acceptance: cold ordinary browser login → direct `/copilot` refresh → CORE POST with valid current session CSRF → exactly one envelope and 503 CAPABILITY_DISABLED; guest 401/403; no mock/proxy-required routing, no CORS/auth weakening. Rebuild image from the new manifest and verify source/assets.

**P2-04 — DEMO authorization is simulated, not scope-enforced.** `demoInvoiceProvider.ts:82` accepts arbitrary payloads; `:295` falls back to `DEMO_RECORDS[0]` on an unknown selection. Forged context, wrong context version, forged selection, and a selection reused across separate providers all return 200. Four independent negative assertions FAIL (`demo-negative-r2`, exit 1). No cryptographic signing or private key exists: refs are deterministic public strings despite UI “synthetic signatures” wording. Keep all data synthetic, remove first-record fallback, bind demo context/selection/version/TTL to a per-demo scope, reject malformed/cross-scope requests, and truthfully label the test authority. Do not borrow CORE keys or production records. All four negative cases must deny with no document; PARTIAL refs stay non-actionable.

**P2-05 — Generic framework routes are not fully qualified.** Ordinary `/api/resource/User/Administrator` and `frappe.client.get` deny 403; `frappe.client.get_value` returns 200 with an empty object, not protected User values. Missing Sales Invoice resource denies 403 for this user. `run_doc_method` with absent Sales Invoice returns 500 with traceback; disallowed v2 alias and native GET responses also contain tracebacks. These observations do not prove a privileged financial read/write bypass, but absent business schema cannot qualify future native generic-resource boundaries. Sanitize framework errors and qualify generic CRUD/get_value/run_doc_method/report/v2 routes under the approved ordinary roles and native policy before enabling N0. Use least privilege; do not block legitimate framework primitives indiscriminately.

**P2-06 — Requested tool/source gates incomplete.** Full ESLint is unavailable; oxlint is the actual npm lint script. Add an agreed reproducible ESLint gate/config or obtain an explicit revised gate; do not describe oxlint as an ESLint run. `npm audit` exits 1: 8 high and 2 moderate affected package entries, no critical. Assess reachability and minimally remediate the lockfile; never apply unreviewed major `audit fix`. Broad pytest collection fails on missing host Frappe plus `test_architecture_remediation.py:29` importing nonexistent `BaselineSourceError`; preserve assertions and correct the test/source contract or define a documented suite boundary. `git diff --check` exits 2 for whitespace/EOF issues. Current README incorrectly says invoice/L3 mounts are fixture-only and lacks an accurate current DEMO run path. Builder route docs name nonexistent `.context/.search/.open` methods and fictitious `CORE_AUTHORITATIVE` wire mode; actual methods are `.get_context/.search_invoices/.open_invoice` and disabled status is NOT_AVAILABLE with reason CAPABILITY_DISABLED.

**P2-07 — Default mobile/accessibility layout needs correction.** At 390×844 the 256px sidebar leaves a severely clipped chat column, tabs and composer; zero document overflow does not prove usability. Evidence: `mobile-copilot.png`. Start collapsed below the agreed breakpoint, preserve all tabs/inputs, and label the unnamed header button and scenario selector. Recheck keyboard, focus, readable layout, page/drawer, 390/768/desktop; no complete accessibility certification is claimed. The 333-line DEMO provider and 769-line chat panel also exceed ADR001's 200-line source limit; split while retaining the same security state machine.

## Source identity

| Source | SHA256 of current bytes |
|---|---|
| `frontend/package.json` | `35386677a8ec903a6fd9c75b09e5732603a2a4626eabcb4e528386f7e81da50c` |
| `frontend/package-lock.json` | `4530fd8c3e9496a684a8569ee6a47dd0f3eb8d010b3def7a6d4222db67f23dd9` |
| `frontend/src/App.tsx` | `d97b68ab9574caca541613a96f1862ff1b6f97dabce3cf54e6ee2a9a6e4216a1` |
| `frontend/src/pages/copilot/components/VercelChatPanel.tsx` | `cc740e1a33b117058865f9af603fc0ced60da698554c68394cc7708591dc985c` |
| `frontend/src/pages/copilot/actions/useInvoiceActions.ts` | `e254951a620ec2b91b16a2702d134b39410e4d22910492bab35caa040dab6e5b` |
| `frontend/src/pages/copilot/actions/invoiceActionClient.ts` | `563953db81934bfa68a224f8e34251bba6a494001f59cd6a01d6208fe44e05ba` |
| `frontend/src/pages/copilot/demo/demoInvoiceProvider.ts` | `c97efae391e45c53c8e08410603fc4b92ceb20871132b139f38dfdd059a7586b` |
| `frontend/src/pages/copilot/prepare/FollowupPreview.tsx` | `c02d95699e67b5e985253a48e518efc496139a7adff8b747f60bea9b2d5a8381` |
| `lotus_fin/lotus_fin/runtime/boundary.py` | `c7094a16e6b5336f004813ce70de9c9c04f58db89477ece59cd67bdb0d88e021` |
| `lotus_fin/lotus_fin/api/invoice_actions_api.py` | `5014b7c161b55f98ce6e5128dc9bdc6f1276b0e6e59fed44906a84f5c6a9928d` |
| `lotus_fin/pyproject.toml` | `73640471508a2243d22ce497971bbc922679988b49ecd3137b321a16fa3ff878` |
| `docker/lotus-core/Dockerfile` | `13f2cfbe27d0c314101c71a774cfebd1954e1dba2ef4a69de555ae5ce8d39cad` |
| `docker/compose.lotus-core.yml` | `09f92a5a41f1009465747b3320f531223ca21615b1317fe11b6cecc5d47915a1` |
| `docker/lotus-core/framework.lock` | `c378b14ca9e669989a5e18164ca3084a32a2c6b54e49be34689587f87f9c8e0a` |
| `docker/lotus-core/requirements.lock` | `98a0e096f85b3d99b8ec6d0def15daff317cb850af5598764b5aab911b3c99ac` |
| `run.ps1` | `82959882727c5f358848dc8d36f6346f91adafb6deef9e4e6b4cb4fc54a4b06f` |
| `run.sh` | `f3718ea77bd03c212dd8b211a98321a339ed100585d534478acd9bd508545bea` |