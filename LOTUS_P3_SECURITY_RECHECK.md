# Lotus P3 security recheck

13 October 2026 · Asia/Saigon · Independent acceptance of `E:/lotus-fin`.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. The candidate is current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push, merge or deployment was performed. Tests used only local fixtures and the previously qualified isolated `lotus-core-01a13314` / `core-01a13314.localhost` / loopback 8097. N0 remains BLOCKED.

Evidence directory: [p3-independent-2026-10-13](docs/reviews/evidence/p3-independent-2026-10-13). Exact candidate: [CANDIDATE_SOURCE.json](docs/reviews/evidence/p3-independent-2026-10-13/CANDIDATE_SOURCE.json), 616 files, SHA256 `02da08611f41de6e9ceff876e95bf48e11150cf9cdbe8e06819f816ae3cb8c70`. Every executed test command, inner-command exit code and output hash is in [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p3-independent-2026-10-13/COMMANDS_AND_EXITS.json). Collector shells may exit 0 after recording a failed child; use the recorded child exit. Failed attempts are retained.

**SECURITY_PRE_PUSH: FAIL.** P1-01 and P1-02 are independent, reproducible blockers. No actual native financial data was accessed.

| Real case | HTTP | Outcome reason | Traceback observed |
|---|---|---|---|
| `guest_generic_user_resource` | 403 | framework/non-outcome | False |
| `guest_generic_get_value` | 403 | framework/non-outcome | False |
| `guest_generic_get_list` | 403 | framework/non-outcome | False |
| `guest_get_context` | 401 | framework/non-outcome | False |
| `guest_search_invoices` | 401 | framework/non-outcome | False |
| `guest_open_invoice` | 401 | framework/non-outcome | False |
| `ordinary_login` | 200 | framework/non-outcome | False |
| `desk_token` | 200 | framework/non-outcome | False |
| `native_disabled_get_context` | 503 | CAPABILITY_DISABLED | False |
| `native_disabled_search_invoices` | 503 | CAPABILITY_DISABLED | False |
| `native_disabled_open_invoice` | 503 | CAPABILITY_DISABLED | False |
| `canonical_authenticated_route` | 404 | framework/non-outcome | False |
| `baked_static_entry` | 200 | framework/non-outcome | False |
| `core_get_rejected` | 403 | framework/non-outcome | True |
| `core_wrong_csrf` | 400 | framework/non-outcome | False |
| `forged_demo_headers` | 422 | INVALID_REQUEST | False |
| `forged_demo_body` | 422 | INVALID_REQUEST | False |
| `generic_user_resource_denied` | 403 | framework/non-outcome | False |
| `generic_get_user_denied` | 403 | framework/non-outcome | False |
| `generic_get_value_user_denied` | 200 | framework/non-outcome | False |
| `generic_absent_sales_invoice` | 403 | framework/non-outcome | False |
| `generic_legacy_run_doc_method` | 500 | framework/non-outcome | True |
| `legacy_resource_alias` | 403 | framework/non-outcome | True |
| `disabled_user_existing_cookie` | 200 | framework/non-outcome | False |
| `disabled_user_native_cookie` | 503 | CAPABILITY_DISABLED | False |
| `disabled_user_standard_save_cookie` | 200 | framework/non-outcome | False |
| `disabled_user_standard_save_native` | 503 | CAPABILITY_DISABLED | False |
| `ordinary_relogin` | 200 | framework/non-outcome | False |
| `desk_token_2` | 200 | framework/non-outcome | False |
| `logout` | 200 | framework/non-outcome | False |
| `revoked_cookie_readiness` | 401 | framework/non-outcome | False |
| `explicit_revoked_cookie_replay` | 401 | framework/non-outcome | False |

Native active-user POSTs have exactly one message envelope, server CID matching header/body, source/context/data null, status NOT_AVAILABLE/reason CAPABILITY_DISABLED, and private/no-store. Guest methods deny 401; wrong CSRF denies 400; forged profile headers/body/query cannot enable a server DEMO provider and deny 422. No successful native financial read is asserted. Framework pre-handler failures need not carry the native envelope; their traceback disclosure remains a concrete defect. Guest generic protected resource denial and ordinary permissions do not qualify future native document/field grants.

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

## Keys, sessions and supply chain

The local DEMO transport contains only fictional DEMO-SINV identities and public deterministic handles; no signing key exists to claim HMAC authorization. CORE signing/config loaders remain fail-closed by default, and no source/key/DEMO provider was introduced into backend composition. The browser profile-crossing defect violates this presentation isolation despite the backend remaining disabled. Real QA credentials stayed in ignored .runtime and were never copied to audit evidence. Administrator was used solely for restoring/toggling the synthetic QA User during the isolated security test, never for protected HTTP requests. The redacted source scan found 22 hits, all inspected as translation labels, mock-key or explicit offline test keys, not proven live credentials; historical/private snapshots are excluded from staging and are not certified by this limited scan.

npm audit: 10 affected package entries (8 high, 2 moderate), not 10 independently exploited flaws. Principal advisory families include path-to-regexp, braces and postcss-selector-parser; reachability must be reviewed separately. Backend wheel-hash/SBOM/vulnerability acceptance was not run. No automatic dependency upgrade occurred.

## Graph review and authority

Bound repo/index: `lotus-fin`, `E:/lotus-fin`, indexed 2026-10-12T07:02:27.060Z at the same Git HEAD; working-tree/untracked coverage is incomplete. Concept query returned no definitions with FTS disabled. Explicit UID impact on the actual VercelChatPanel returned **HIGH**, 7 impacted symbols, 3 direct callers (LotusCopilotDrawer, LotusCopilotPage and fixture composition), App/UniversalPageView processes and 4 modules. HIGH is not waived by its LOW shared-axis score. New enforce_request_boundary is absent from the index; text inspection follows that unresolved graph result.

`detect-changes --scope all` reports 23 tracked files, 78 symbols, 12 processes, HIGH risk. Rerun with `--limit 500` still prints only 15 symbols/10 flows. This is not a clean graph gate and cannot cover the 140 unstaged/untracked candidate additions/changes or all unindexed source. No commit was attempted. Refresh the actual source index and obtain complete, non-partial/non-truncated change analysis before a future commit; do not quote the builder's “2 files / no breaking changes” as acceptance.

Final CLI status explicitly reports stale. The mandated `analyze --index-only` refresh was attempted and exited 1 after 375.80 seconds: native parse worker startup failed (5000ms readiness limit; bounded self-heal exhausted). No fresh graph acceptance is claimed. Existing risk receipts and source confirmation remain evidence with this coverage limitation. Global tool reinstall or production source changes were not performed to conceal the failure.

Authorities inspected: AGENTS.md, ADR001, Security Code V3, frozen P1/P2-B references, all seven required platform/runtime/N0/inventory reports and all seven current P3 builder reports. Latest user architecture supersedes legacy ERP assumptions and old transport descriptions. All remaining native source/policy approvals stay BLOCKED. Reports are evidence claims, not source authority or human N0 approval.
