# Lotus Fin — independent final security recheck

12 October 2026, Asia/Saigon. **CHANGES_REQUIRED for offline UI contract acceptance; live native security BLOCKED.** No new P0 exploit or live cross-company disclosure was demonstrated. This is an independent technical assessment, not organizational security approval.

## Exact scope and authority

Branch `codex/p2a-invoice-read-backend`; HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. Tested artifact is the dirty working tree, identified by the [549-file SHA256 manifest](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/SOURCE_MANIFEST.json), digest `a59b5b472d44d3251a92247d281627ce7f3d4cfa93acdf58158bf3c4df1a3d40`. Final rehash found **zero source changes and zero changes to 222 fingerprinted historical files**. [Integrity](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/FINAL_INTEGRITY.json).

Read Security Code V3, human security/identity/audit authorities, ADR001, P1 MASTER, frozen P2-B wire, proposal/V1/L3/L4 contracts, original independent reproductions, correction reports, and the native architecture/integration/reproducibility outputs. [Authority/report inventory](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/REPORTS_AND_AUTHORITIES.json) records 74 files. User's independent-product instruction supersedes historical ERP-dependent architecture assumptions. Human/design documents are requirements, not proof of deployed controls. P1 MASTER and later native/L3 designs retain proposal boundaries; the P2-B freeze qualifies offline DTO/fixture semantics only.

## Previous finding reconciliation

All original adversarial assertions remain intact in new evidence copies. Original historical files were not changed. Builder PASS claims are not used to decide closure.

| Finding | Fresh result | Scope and evidence |
| --- | --- | --- |
| FIN-F01 — expiry at response admission, P1 | **Reproduced case CLOSED offline** | Context/search/open at equality reject; independent new oracle tests expiry−1/equality/+1. React expired search/open leave no protected DOM. |
| FIN-F02 — source/runtime reproducibility, P1 | **OPEN** | HEAD lacks 49 inventoried paths, including both UI directories. Fresh running-container filesystem probe finds 17/17 backend paths absent. Production bundle/mount omit actions and L3. |
| FIN-F03 — clipboard revision/operation ownership, P1 | **CLOSED in tested L3 scope** | Edit during pending copy cannot acknowledge another revision; old finally cannot release newer copy lock. |
| FIN-F04 — unmount disposal, P1 | **CLOSED in tested L3 scope** | Actual unmount clears old controller body and fences late acknowledgement; remount starts empty. |
| FIN-F05 — monotonic/idle expiry, P1 | **CLOSED in tested L3 scope** | Wall rollback with monotonic elapsed expires; exact TTL blocks copy; idle React editor disappears. |
| FIN-F06 — outer version/expiry grammar, P2 | **Original cases CLOSED offline** | Missing/null/version mismatch and rollover/prose/date-only/local expiry rejected. Separate observation-timestamp defect remains below. |
| FIN-F07 — malformed-response invalidation, P2 | **PARTIALLY CLOSED / OPEN** | Original invalid-open case clears all handles. New malformed-search cases retain context and reuse its handle. Actual React confirms it. |
| FIN-F08 — pagination metadata, P2 | **Original cases CLOSED offline** | Missing/contradictory complete and zero-row cursor metadata rejected; valid complete/PARTIAL/empty preserved. No next-page UI workflow is implemented. |
| FIN-F09 — full source identity, P2 | **Original cases CLOSED offline** | Site/product/connection/version/mode/timezone mismatches reject in controller and actual React; no foreign canary enters protected results/reader. Actor/session cases use context versions/lifecycle scope, not authenticated native users. |
| FIN-F10 — unavailable L3 scope, P2 | **CLOSED in tested L3 scope** | Empty/whitespace/null/undefined scope produces no body/export; actual blank-scope React denies. Scope epoch is lifecycle fencing, not server authority. |
| FIN-F11 — whole-app lint, P3 | **OPEN baseline** | Full frontend lint exit 1 with conditional-hook errors in UniversalPageView. Selected action/L3 lint exits 0 with one control-regex warning. |
| FIN-F12 — invalid observation timestamp, P2, new | **OPEN** | Decoder accepts invalid source timestamp as context; actual React admits impossible-date context. |

Closure here applies to exact reproduced offline cases, not native permission, production exposure, or formal template/mount approval.

## Residual finding: FIN-F07 search cleanup

Location: `frontend/src/pages/copilot/actions/invoiceActionController.ts`, `search`, especially the `vm.kind === "unavailable"` branch. Unlike `openInvoice`, it clears results but retains context for every unavailable outcome, including `INVALID_RESPONSE`.

Independent arrangement uses new actor/company/source identifiers and held transport responses; no builder fixture/expected-value factory. Load a valid context, search, then return one of: extra field, foreign context version, cursor without continuation, wrong count, duplicate rows, or wrong RID. Expected by frozen wire §2/§9: invalid response clears protected context/results/selection/cursor/reader; next search requires fresh context. Actual: context remains, next search dispatches once using its retained handle and can restore rows. **Six cleanup and six handle-reuse assertions fail.** Malformed response rows themselves are rejected; this is not proof of foreign data disclosure.

Actual React independently returns contradictory cursor metadata. Company context stays visible, and a subsequent click adds a search request without a new context. Both assertions fail. [New controller results](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/NEW_ORACLE_RESULTS.json), [React results](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/NEW_P2B_REACT_NEW_QUALIFIED_RESULTS.json).

Correction handoff, not executed: distinguish invalid/unverifiable responses from a typed recoverable source outage; fence and discard all protected handles on the former. Preserve original positives, source errors, denials and concurrency behavior. Independent exit: all new cleanup/reuse assertions green in controller and React.

## New finding: FIN-F12 observation-time validity

Location: `frontend/src/pages/copilot/actions/invoiceActionDecoderHelpers.ts`, `parseSource`. `observed_at` is only checked for bounded string length and sanitized for display. The strict UTC validator protects `expires_at`, not source observation time.

New oracle independently supplies `garbage`, `2026-02-30T01:02:03Z`, date-only, and local timestamp without offset. All four are admitted as `kind: context`. React with the impossible date renders company context. Expected: real UTC observation timestamp, no rollover/prose/local representation, and no protected context admission from invalid source evidence. [Results](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/NEW_ORACLE_RESULTS.json), [React screenshot](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/NEW_INVALID_OBSERVATION.png).

Correction handoff, not executed: validate observation timestamps before source admission while preserving valid backend UTC representations, including its observed microsecond precision. Reusing an expiry validator that rejects legitimate backend precision would create a new compatibility defect. Add invalid source timestamps to context/search/open React admission and require handle invalidation.

## Fresh security execution

| Check | Actual result / exit | Qualification limit |
| --- | --- | --- |
| P1/P2-A 22 focused modules | 343 passed / 0 | Isolated ports, no genuine native document/field authority. |
| Original independent backend protocol/boundary/source | 36 + 14 + 12 passed / 0 each | Private typed service/serializer and controlled framework seam. Repeated core assertions are not additional unique cases. |
| A16 required terminal sink | 14 passed / 0 | Actual offline write/flush/filter/concurrency fault assertions, not live durable sink qualification. |
| B03 exact Company seam | 8 passed / 0 | Exact current user/Company invocation, not native membership or invoice/field policy. |
| Five P1 codec methods | AST-identical | Compatibility preservation only; historical P1 and v2/UI expiry semantics differ and remain version-scoped. |
| Original UI Node / expanded prior Node | 23/23 and 96/96 / 0 | Actual source, synthetic transport, no builder factories. |
| New Node oracle | 25 PASS, 16 FAIL / 1 | 12 failures for search cleanup/reuse; 4 for observation timestamps. |
| Preserved React / expanded React | 34/34 / 0; 36 PASS, 3 FAIL / 1 | New React has two extra valid-timezone negatives and three new defect assertions. Overlapping counts must not be summed. |
| L3 controller / React | 16/16 and 11/11 / 0 | Fake clipboard/controlled clock; actual component. No real browser permission or all telemetry-store proof. |
| P2-B/L3 Node units | 86 passed / 0 | 66 + 20, supplemental builder-authored regressions rerun independently. |
| Deny tool/API oracle | 12/12 / 0 | Nine mutation/autonomous/local-template tool names unregistered; three public Python helpers disabled. No live RPC penetration claim. |
| Real framework security suite | Collection error / 2 | `frappe` unavailable in host interpreter. Zero framework security cases execute; **BLOCKED**, not a skip/PASS. |

[Actual argv/cwd/exits](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/COMMANDS_AND_EXITS.json), [setup/graph attempts](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/SUPPLEMENTAL_EXECUTION.json), [harness lineage](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/HARNESS_LINEAGE.json).

Old React sequencing assumed context survived invalid open. Its unchanged copied harness passed three assertions then timed out on the correctly disabled search button. Qualified copies retain every assertion and obtain fresh context before the independent empty case; initial browser time is frozen at serialized observation, and expiry tests override it. Missing-wire-sample and UTF8 setup failures are recorded separately. No product source or assertion was changed to achieve green results.

## Native, HTTP, authorization, audit and no-write boundary

`IAuthorizedInvoiceReadPort` has two subclasses, both test mocks. No production implementation or approved Lotus invoice/tenant authority was identified. `FrappeInvoiceAuthorizer` checks configured site/company and exact Company permission; it emits `ERP_READ`. Its document method stays disabled. These facts do not establish genuine document/field/masking/custom-hook rights or tenant membership/revocation on Lotus-owned records.

Three invoice declarations specify authenticated POST, but the helper and controller search/open are disabled. No ordinary-user session/CSRF request, framework wrapper/status/header, body limits/duplicate keys, actual disabled-user/logout/revocation, multiworker rights, durable audit, hard SQL/cancellation/byte budget, or business before/after was executed. All are **BLOCKED / NOT_RUN** due absent approved native authority/target. Broad helper exception handling, inner `message` return and framework status/header API assumptions require future actual serving tests; no HTTP PASS or fresh live bypass is inferred.

Legacy `copilot_api.chat_copilot` has `allow_guest=True`, and CopilotController contains missing-framework identity/company fallbacks to elevated defaults. This remains a separate unqualified public composition. Offline narrow invoice PASS does not qualify legacy Desk, grant fallback authority, or excuse exposed routes in a future independent release. No live exploit or paid provider was exercised.

Logical reference/purpose/scope/version/query/expiry, safe terminal delivery, bounds, null-data denial and mutation-tool isolation pass their executed offline tests. Browser guards observe no unexpected requests/storage keys in the tested fixtures. **Neither establishes real business no-write**; no native store was read, mutated or snapshotted.

## P0/P1 release blockers and stop

No new P0 vulnerability is asserted. FIN-F02 remains P1. Native data/policy/HTTP absence and mandatory ERP runtime dependence are release blockers under the user's rules; absence is not permission qualification. Previously reproduced P1 UI admission/L3 lifecycle defects are closed only in the tested scope. Remaining P2 contract defects prevent full offline acceptance. No L4/L5 mutation path was added; future write capabilities remain unimplemented/unapproved.

No source fixes, flags, deployments, site initialization, ERP/business writes, commit or push. Assessment stops at this handoff.
