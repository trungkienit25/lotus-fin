# P4 CORE / DEMO real E2E — CHANGES_REQUIRED

13 October 2026 · Asia/Saigon · Independent targeted P4 acceptance.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Reviewed current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push or merge. Only owned isolated project `lotus-core-p4c-01a13415-r5`, site `core-p4c-01a13415-r5.localhost`, loopback `127.0.0.1:8101` was tested and restarted; volumes retained. N0 remains **BLOCKED**.

The serving application was exercised through its real /copilot and /home drawer routes using ordinary Frappe authentication. No HTTP response replacement, test proxy or manual tab remount was needed for the qualifying journeys. DEMO data originated from the actual client-local provider and is strictly fictional.

## Mounted coverage

| Mounted transition | Result |
| --- | --- |
| `page:NORMAL->EMPTY` | PASS |
| `page:NORMAL->PARTIAL` | PASS |
| `page:NORMAL->FORBIDDEN` | PASS |
| `page:NORMAL->EXPIRED` | PASS |
| `page:NORMAL->STALE` | PASS |
| `page:EMPTY->NORMAL` | PASS |
| `page:EMPTY->PARTIAL` | PASS |
| `page:EMPTY->FORBIDDEN` | PASS |
| `page:EMPTY->EXPIRED` | PASS |
| `page:EMPTY->STALE` | PASS |
| `page:PARTIAL->NORMAL` | PASS |
| `page:PARTIAL->EMPTY` | PASS |
| `page:PARTIAL->FORBIDDEN` | PASS |
| `page:PARTIAL->EXPIRED` | PASS |
| `page:PARTIAL->STALE` | PASS |
| `page:FORBIDDEN->NORMAL` | PASS |
| `page:FORBIDDEN->EMPTY` | PASS |
| `page:FORBIDDEN->PARTIAL` | PASS |
| `page:FORBIDDEN->EXPIRED` | PASS |
| `page:FORBIDDEN->STALE` | PASS |
| `page:EXPIRED->NORMAL` | PASS |
| `page:EXPIRED->EMPTY` | PASS |
| `page:EXPIRED->PARTIAL` | PASS |
| `page:EXPIRED->FORBIDDEN` | PASS |
| `page:EXPIRED->STALE` | PASS |
| `page:STALE->NORMAL` | PASS |
| `page:STALE->EMPTY` | PASS |
| `page:STALE->PARTIAL` | PASS |
| `page:STALE->FORBIDDEN` | PASS |
| `page:STALE->EXPIRED` | PASS |
| `page:DEMO->CORE` | PASS |
| `page:CORE->DEMO` | PASS |
| `drawer:NORMAL->EMPTY` | PASS |
| `drawer:NORMAL->PARTIAL` | PASS |
| `drawer:NORMAL->FORBIDDEN` | PASS |
| `drawer:NORMAL->EXPIRED` | PASS |
| `drawer:NORMAL->STALE` | PASS |
| `drawer:EMPTY->NORMAL` | PASS |
| `drawer:EMPTY->PARTIAL` | PASS |
| `drawer:EMPTY->FORBIDDEN` | PASS |
| `drawer:EMPTY->EXPIRED` | PASS |
| `drawer:EMPTY->STALE` | PASS |
| `drawer:PARTIAL->NORMAL` | PASS |
| `drawer:PARTIAL->EMPTY` | PASS |
| `drawer:PARTIAL->FORBIDDEN` | PASS |
| `drawer:PARTIAL->EXPIRED` | PASS |
| `drawer:PARTIAL->STALE` | PASS |
| `drawer:FORBIDDEN->NORMAL` | PASS |
| `drawer:FORBIDDEN->EMPTY` | PASS |
| `drawer:FORBIDDEN->PARTIAL` | PASS |
| `drawer:FORBIDDEN->EXPIRED` | PASS |
| `drawer:FORBIDDEN->STALE` | PASS |
| `drawer:EXPIRED->NORMAL` | PASS |
| `drawer:EXPIRED->EMPTY` | PASS |
| `drawer:EXPIRED->PARTIAL` | PASS |
| `drawer:EXPIRED->FORBIDDEN` | PASS |
| `drawer:EXPIRED->STALE` | PASS |
| `drawer:STALE->NORMAL` | PASS |
| `drawer:STALE->EMPTY` | PASS |
| `drawer:STALE->PARTIAL` | PASS |
| `drawer:STALE->FORBIDDEN` | PASS |
| `drawer:STALE->EXPIRED` | PASS |
| `drawer:DEMO->CORE` | PASS |
| `drawer:CORE->DEMO` | PASS |

All 60 non-self directed scenario transitions and both profile directions on each surface passed. NORMAL searched three rows and required explicit selection of the second record; read-only fields showed DEMO-SINV-2026-002. EMPTY produced an empty result, PARTIAL no selectable handles, FORBIDDEN disabled search, EXPIRED cleared scope with restart notice, STALE denied open with no read view. CORE displayed the real 503-disabled notice with no rows, document, stale input or DEMO-SINV text. The final MOUNTED_E2E receipt contains 86 checks, including six page/drawer 390/768/1440px viewports and keyboard Enter activation.

## Session/actor failures

**P4-F01 · P1 acceptance blocker — mounted actor/session scope is not bound.** Profile changes are fixed, but the actual page and drawer omit `contextKey`; their invoice scope defaults to company/default/profile/scenario. External logout switches the authoritative server to Guest (bootstrap 401), yet three synthetic rows and one open document remain. Logging in as a second ordinary QA user without remount leaves them intact; an old selection opens DEMO-SINV-2026-001. See ACTOR_SCOPE_BROWSER.json, SESSION_SCOPE_BROWSER.json and page/drawer actor screenshots. This is synthetic presentation/provider leakage, **not demonstrated native financial disclosure or backend authentication bypass**. The requested actor/session clearing acceptance still fails. Bind both mounts and the DEMO provider lifetime to a current authenticated actor/session epoch, clear immediately on auth invalidation/visibility/session change, fence old results, and replay both surfaces without reload.


Both mounted surfaces failed external logout-to-Guest, change to a different ordinary user, and old-handle reuse. Same-user session replacement also fails. The normal application Log Out button does unmount and clear DEMO; a fresh login begins CORE. That narrower PASS does not cover another tab changing the shared cookie. Reload purges state, but reload is not an acceptable scope-fencing requirement.

## Races, local prepare and mobile

Actual Chromium network latency delayed a CORE operation while profiles switched; the late reply did not overwrite the new DEMO result. Existing controller/unit tests also cover abort/old generation disposal; the DEMO provider resolves locally, so no fictitious slow server DEMO response is claimed. B1-S general unqualified chat made no chat_copilot RPC. Local L3 Prepare/Edit/Review/Copy/Discard passed with real clipboard permission; its 16-case oracle and clean fixture test separately cover TTL, revision, concurrent copy and unmount.

**P4-F02 · P2 — mobile scenario selector still clips.** At 390px, x=93.984375 and width=332, ending at 425.984375: about 36px outside the viewport. The sidebar, mode tabs and main input are improved; that does not qualify the whole form. Make the profile/scenario row fit and inspect 390px page/drawer control bounds plus keyboard focus. The accessible-name/Enter smoke is not WCAG certification; the builder's broad compliance wording is unsupported.


Screenshots: [page-390.png](docs/reviews/evidence/p4-independent-2026-10-13/page-390.png), [drawer-390.png](docs/reviews/evidence/p4-independent-2026-10-13/drawer-390.png), [page-768.png](docs/reviews/evidence/p4-independent-2026-10-13/page-768.png), [drawer-768.png](docs/reviews/evidence/p4-independent-2026-10-13/drawer-768.png), [page-1440.png](docs/reviews/evidence/p4-independent-2026-10-13/page-1440.png), [drawer-1440.png](docs/reviews/evidence/p4-independent-2026-10-13/drawer-1440.png), [external-logout-demo.png](docs/reviews/evidence/p4-independent-2026-10-13/external-logout-demo.png), [page-actor-change.png](docs/reviews/evidence/p4-independent-2026-10-13/page-actor-change.png), [drawer-actor-change.png](docs/reviews/evidence/p4-independent-2026-10-13/drawer-actor-change.png).

## Execution layers and harness corrections

Real receipts: [REAL_CORE_HTTP_BROWSER.json](docs/reviews/evidence/p4-independent-2026-10-13/REAL_CORE_HTTP_BROWSER.json), [REAL_SECURITY_HTTP.json](docs/reviews/evidence/p4-independent-2026-10-13/REAL_SECURITY_HTTP.json), [MOUNTED_E2E.json](docs/reviews/evidence/p4-independent-2026-10-13/MOUNTED_E2E.json), [SESSION_SCOPE_BROWSER.json](docs/reviews/evidence/p4-independent-2026-10-13/SESSION_SCOPE_BROWSER.json), [ACTOR_SCOPE_BROWSER.json](docs/reviews/evidence/p4-independent-2026-10-13/ACTOR_SCOPE_BROWSER.json). Ten retained browser regressions passed in a clean copied source tree, using intercepted fixture transport; they do not qualify real native finance. The 114 Node tests and four forgery checks are source-level checks, not browser evidence.

The first transition harness reselected an already-consumed EXPIRED value, which does not dispatch a React select-change event; it failed before completing. The corrected harness initializes the source scenario before each real transition, with unchanged acceptance assertions. An initial L3 harness used obsolete test IDs; current IDs were inspected and corrected. Failed attempts remain recorded. The first concurrent exploratory session harnesses also shared the ordinary actor; qualifying mounted and actor runs were subsequently executed sequentially. No failing security oracle was altered to hide the reproduced session-scope defects.

Canonical 19-check login/direct route/refresh/real CSRF journey passed before and after independent isolated cold restart. CORE native context/search/open remain unavailable, so **native successful invoice Search/Open = BLOCKED** and this DEMO E2E is not production financial evidence.
