# P4 security recheck — SECURITY_PRE_PUSH: FAIL

13 October 2026 · Asia/Saigon · Independent targeted P4 acceptance.

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Reviewed current dirty/untracked working-tree bytes, not HEAD. No production source edit, stage, commit, push or merge. Only owned isolated project `lotus-core-p4c-01a13415-r5`, site `core-p4c-01a13415-r5.localhost`, loopback `127.0.0.1:8101` was tested and restarted; volumes retained. N0 remains **BLOCKED**.

P1-02 and P1-03 are independently closed for this isolated disabled-native runtime. P1-01 profile transitions are corrected; its required actor/session scope clearing is incomplete.

**P4-F01 · P1 acceptance blocker — mounted actor/session scope is not bound.** Profile changes are fixed, but the actual page and drawer omit `contextKey`; their invoice scope defaults to company/default/profile/scenario. External logout switches the authoritative server to Guest (bootstrap 401), yet three synthetic rows and one open document remain. Logging in as a second ordinary QA user without remount leaves them intact; an old selection opens DEMO-SINV-2026-001. See ACTOR_SCOPE_BROWSER.json, SESSION_SCOPE_BROWSER.json and page/drawer actor screenshots. This is synthetic presentation/provider leakage, **not demonstrated native financial disclosure or backend authentication bypass**. The requested actor/session clearing acceptance still fails. Bind both mounts and the DEMO provider lifetime to a current authenticated actor/session epoch, clear immediately on auth invalidation/visibility/session change, fence old results, and replay both surfaces without reload.


## Real authentication and framework boundary

| Real observation | HTTP | Result |
| --- | --- | --- |
| `guest-get_context` | 401 | PASS |
| `guest-search_invoices` | 401 | PASS |
| `guest-open_invoice` | 401 | PASS |
| `ordinary-login` | 200 | PASS |
| `ordinary-bootstrap` | 200 | PASS |
| `active-readiness` | 200 | PASS |
| `active-get_context` | 503 | PASS |
| `active-search_invoices` | 503 | PASS |
| `active-open_invoice` | 503 | PASS |
| `missing-csrf` | 400 | PASS |
| `invalid-csrf` | 400 | PASS |
| `native-get-denied` | 403 | PASS |
| `protected-user-resource` | 403 | PASS |
| `protected-user-get` | 403 | PASS |
| `protected-user-get-value` | 200 | PASS |
| `public-user-list` | 200 | PASS |
| `absent-sales-invoice` | 403 | PASS |
| `legacy-run-doc-method` | 500 | PASS |
| `v2-legacy-alias` | 403 | PASS |
| `framework-report` | 404 | PASS |
| `protected-user-write` | 403 | PASS |
| `persisted-disabled-cookie-readiness` | 401 | PASS |
| `persisted-disabled-cookie-bootstrap` | 401 | PASS |
| `persisted-disabled-cookie-get_context` | 401 | PASS |
| `persisted-disabled-cookie-search_invoices` | 401 | PASS |
| `persisted-disabled-cookie-open_invoice` | 401 | PASS |
| `explicit-revoked-cookie-readiness` | 401 | PASS |
| `explicit-revoked-cookie-bootstrap` | 401 | PASS |
| `explicit-revoked-cookie-get_context` | 401 | PASS |
| `explicit-revoked-cookie-search_invoices` | 401 | PASS |
| `explicit-revoked-cookie-open_invoice` | 401 | PASS |
| `reenabled-revoked-cookie-readiness` | 401 | PASS |
| `reenabled-revoked-cookie-bootstrap` | 401 | PASS |
| `reenabled-revoked-cookie-get_context` | 401 | PASS |
| `reenabled-revoked-cookie-search_invoices` | 401 | PASS |
| `reenabled-revoked-cookie-open_invoice` | 401 | PASS |
| `reenabled-new-login` | 200 | PASS |
| `new-active-bootstrap` | 200 | PASS |
| `new-active-native` | 503 | PASS |

All 39 observations matched expected HTTP behavior and contained no Traceback. Standard User.doc.save disabled the actual QA account and persisted readback was checked; its old cookie denied readiness, bootstrap and all three native methods. The exact old session was then explicitly revoked in tabSessions; re-enable did not revive it. A new ordinary login retained real valid CSRF/503 behavior. Administrator was used only for isolated fixture administration, never as an HTTP principal or business authorization substitute. Cleanup receipts are [QA_RESTORATION.json](docs/reviews/evidence/p4-independent-2026-10-13/QA_RESTORATION.json) and [TEMPORARY_ACTOR_CLEANUP.json](docs/reviews/evidence/p4-independent-2026-10-13/TEMPORARY_ACTOR_CLEANUP.json).

The ordinary User resource/get and empty PUT deny 403; get_value returns an empty object, not Administrator fields. Public user-list access remains a framework primitive. Absent Sales Invoice, run_doc_method, report and v2 alias errors are sanitized. No future native document/field authorization is qualified by absent schemas. Actual invalid/missing CSRF is 400 CSRFTokenError, permitted as denial; it is not claimed 403. Successful native POST has exactly one message envelope, NOT_AVAILABLE/CAPABILITY_DISABLED, null data/source/context, consistent CID and private/no-store. Generic pre-dispatch errors retain their framework envelope.

## DEMO reference negatives

The four original oracle checks now deny forged context, wrong context version, forged selection and cross-provider reuse; actual provider status is 409, not the 422 stated in P4-A documentation. Both providers are client-local synthetic objects, not server authorization or cryptographic proof. Profile and per-provider binding does not cover actor/session change, as six live observations prove. Partial results remain non-actionable.

## Supply-chain triage

Fresh npm audit findings are affected-package entries, not ten distinct exploitable application bugs. Braces and PostCSS parsing paths are primarily build tooling; production-only audit narrows to path-to-regexp and its two affected parents. Whether Lotus passes attacker-controlled patterns to that parser is not demonstrated. Primary advisory references: [braces](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm), [optional route groups](https://github.com/advisories/GHSA-j3q9-mxjg-w52f), [route wildcards](https://github.com/advisories/GHSA-27v5-c462-wpq7), [selector parsing](https://github.com/advisories/GHSA-rj75-hqrm-r3gf).

The installed backend inventory has 136 distributions; 134 exact-version PyPI lookups succeeded. Frappe and Lotus source packages are separately unresolved by that catalog. Six distributions have advisory records, including duplicate GHSA/PYSEC aliases: oauthlib 3.3.1, pdfkit 1.0.0, PyJWT 2.13.0, pypdf 6.15.0, weasyprint 68.0 and Werkzeug 3.1.6. See PYTHON_DEPENDENCY_ADVISORIES.json and PYTHON_ADVISORY_SUMMARY.json for version-specific primary PyPI URLs. Those successful lookups are inventory evidence, not a security PASS. [PyJWT exact-version metadata](https://pypi.org/pypi/PyJWT/2.13.0/json) and [OAuthLib metadata](https://pypi.org/pypi/oauthlib/3.3.1/json) support follow-up triage.

The qualified image is Linux; [Werkzeug's Windows/NTFS device-name issue](https://github.com/pallets/werkzeug/security/advisories/GHSA-g6x2-hccm-hh4m) does not apply to this serving OS. Ghostscript is absent in the backend, limiting the specific [WeasyPrint EPS/Ghostscript issue](https://github.com/Kozea/WeasyPrint/security/advisories/GHSA-r543-q48m-4c9j); this does not dismiss its other untrusted-rendering advisories. OAuth/JWT/PDF route and input reachability still needs scoped review. No supply-chain fix or harmful proof of concept was executed.

## Remaining security evidence limits

**P4-F04 · P2 — reproducible source/check gates remain incomplete.** Broad pytest still imports nonexistent BaselineSourceError; three other collection errors require the Frappe test environment. No documented enforced suite boundary resolves that mismatch. README still says invoice/L3 have separate synthetic test mounts; some older transport docs name wrong methods. P4-B lists a nonexistent demo_preview endpoint and 403 CSRF examples while the real server returns framework 400 CSRFTokenError. CI build-and-test is an echo placeholder and SAST continues on error; push triggers omit codex/* branches. Whitespace check fails; ESLint/config are absent (the actual lint gate is oxlint). No P4-D report was found. Correct these concrete gates without hiding security assertions.

**P4-F05 · P2 — graph/commit risk unresolved.** The stale 2026-10-12 index cannot resolve the current boundary; concept queries return empty with FTS disabled. HIGH chat-panel impact has three direct callers (page, drawer and fixture), seven impacted symbols and App/UniversalPageView processes. The aggregate tracked change report is CRITICAL and truncates 99 symbols/16 flows even with limit 500; it omits new/untracked source coverage. Separate-index refresh timed out after 480 seconds. UNKNOWN/empty is not low risk, and LOW shared axes do not waive HIGH. Obtain a current, complete, non-truncated graph review before a commit.


Core financial authority remains disabled. Historical legacy controller Administrator fallbacks are present behind the unavailable integration boundary; no reachable fallback was observed in the qualified CORE native methods. Enabling legacy/native capabilities needs separate source and permission review. Full generic CRUD/report/print/OAuth attack coverage and complete accessibility certification were not asserted. Commands/exits: [COMMANDS_AND_EXITS.json](docs/reviews/evidence/p4-independent-2026-10-13/COMMANDS_AND_EXITS.json).
