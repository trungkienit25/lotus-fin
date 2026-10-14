# Lotus Fin — independent final E2E matrix

12 October 2026, Asia/Saigon. **Fixture journey verified with residual negative UI failures; actual native serving HTTP BLOCKED / NOT_RUN.** Branch `codex/p2a-invoice-read-backend`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`; [source manifest](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/SOURCE_MANIFEST.json) SHA256 `a59b5b472d44d3251a92247d281627ce7f3d4cfa93acdf58158bf3c4df1a3d40`.

## Journey and transport identity

| Stage | Executed fixture/private evidence | Actual native HTTP |
| --- | --- | --- |
| Authenticated Lotus user | Lifecycle key and controlled framework principal; no real login | **NOT_RUN** — ordinary-user native target absent. |
| Supported invoice intent | Structured fixture panel criteria/name-prefix/date/docstatus | **NOT_RUN** — product chatbot route has no mounted invoice panel/typed transport. Free-text intent-to-action integration unqualified. |
| Authorized company context | Private resolver/serializer tests; actual React receives serialized independent context | **NOT_RUN** — no approved native membership/company policy. |
| Typed search | Actual typed service over independent fake port; separate actual React decoder/controller | **NOT_RUN** — public route/controller disabled. |
| Native authoritative source | None | **BLOCKED** — no concrete native port implementation/data owner/schema approval. |
| Results | Complete/nonempty/empty/PARTIAL displayed in actual component tests | **NOT_RUN** against owned native records. |
| Explicit selection | One row requires click; no automatic open; incomplete rows not actionable | **NOT_RUN** on production UI/HTTP. |
| Fresh authorized open | Private scope/reference/version/denial oracle; serialized wire displayed by actual React | **NOT_RUN** — no genuine native document/field permission engine. |
| Minimum read-only view | Exact five-field reader/fixed descriptor tested, escaped literal text | **NOT_RUN** as live Lotus product feature. |
| Optional L3 preview | Separate actual fact-free local component; review/edit/copy/discard/expiry tests | **NOT_RUN** as approved mounted feature; template/TTL/mount approval absent. No selected-invoice facts are supplied. |

The synthetic browser aliases are `/api/method/lotus_fin.api.copilot_api.invoice_context`, `invoice_search`, `invoice_open`. The actual declared family is `/api/method/lotus_fin.api.invoice_actions_api.get_context`, `search_invoices`, `open_invoice`. Browser routing fulfills fixture aliases locally. This is **not** an end-to-end call through serving Lotus/Frappe middleware and a native source, nor one connected backend-to-browser native transaction.

## Positive and adversarial matrix

| ID | Independent arrangement / expected oracle | Executed outcome | Native outcome |
| --- | --- | --- | --- |
| E01 | Same-scope context → search → one explicit click → minimum reader | PASS, fixture/private boundaries | NOT_RUN |
| E02 | Complete authorized zero rows → empty, no selection | PASS in Node and React | NOT_RUN |
| E03 | PARTIAL zero/nonzero → incomplete, no selection/open/cursor | PASS in preserved oracles | NOT_RUN |
| E04 | Genuine HTTP401/403 must clear protected state regardless of success body | PASS with injected status, actual React | NOT_RUN through middleware |
| E05 | Context/search/open response at expiry−1/equality/+1 | PASS in new Node; equality search/open React PASS | NOT_RUN with actual issued native context |
| E06 | Scope logout/company/session/source switch aborts/fences late responses | PASS in prior Node/fixture cases | NOT_RUN with real sessions/policy |
| E07 | Site/product/connection/version/mode/timezone mismatch admits no foreign canary | PASS across new controller axes and actual React; valid UTC mismatch tested | NOT_RUN against multiple native sources |
| E08 | Wrong actor/session/company/context version | PASS using context/lifecycle mutation; not independent authenticated users | NOT_RUN with two ordinary users/tenants |
| E09 | Malformed/null outer context, invalid expiry/calendar and pagination | Original negatives PASS | NOT_RUN on actual HTTP parsing |
| E10 | Invalid open company/identity/version clears handles | PASS controller and React | NOT_RUN |
| E11 | Invalid search must clear context, reject next action until fresh context | **FAIL** — 6 controller arrangements retain/reuse; 2 actual React failures | NOT_RUN; FIN-F07 remains open |
| E12 | Invalid source observation timestamp must invalidate context | **FAIL** — 4 Node and 1 actual React assertions | NOT_RUN; FIN-F12 |
| E13 | Old response/denial cannot overwrite newer request; abort unmount | PASS in preserved Node/React/fixture tests | NOT_RUN with serving concurrent workers |
| E14 | Valid same-scope replay freshly authorizes; revoked rights take precedence over stale/missing detail | PASS in controlled backend ports | NOT_RUN against native policy/cache/records |
| E15 | Signed selection/cursor wrong purpose/key/query/window/identity/version | PASS focused/independent private tests | NOT_RUN against native source |
| E16 | Source error/timeout/audit outage cannot produce protected success | PASS in private typed faults; source transport is simulated | NOT_RUN with real middleware/adapter/sink |
| E17 | Resource/date/page/scan/provider/response limits; no financial augmentation | PASS logical offline bounds and five-field projection | Physical SQL/hydration/deadline/cancellation NOT_RUN |
| E18 | HTML/XSS literal rendering; no raw token/storage/URL leakage | PASS in tested React fixture observations | Full deployed telemetry/storage/proxy NOT_RUN |
| E19 | L3 pending-copy edit/old finally/generation ownership | PASS controller and actual React | Real clipboard permissions NOT_RUN |
| E20 | L3 unmount clears old body/late callback; empty remount | PASS actual React | Production lifecycle composition NOT_RUN |
| E21 | L3 monotonic rollback/exact TTL/idle expiry | PASS controller and actual React | No operational retention/SLO certification |
| E22 | L3 unavailable/blank/null/undefined scope prevents preview/export | PASS; missing scope actual React PASS | Product scope/approval NOT_RUN |
| E23 | Saved draft/submit/cancel/send/payment/autonomous/generic-write names unavailable | 9 names denied offline; 3 public helpers disabled | Alternate live RPC inventory/penetration NOT_RUN |
| E24 | No ERP mandatory package/schema/role/credential dependency | **FAIL current recipe/source**, no ERP-free positive run | BLOCKED |
| E25 | No business writes; audit/framework side effects separately measured | Fixture no-unexpected-network only; not business-store proof | **BLOCKED**, no approved before/after target |
| E26 | Clean complete source → image → new worker → actual bundle/HTTP | **FAIL lineage**; 49 manifest paths absent from HEAD, 17/17 absent in running backend | BLOCKED |

## Commands, exits and cleanup

[Complete command ledger](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/COMMANDS_AND_EXITS.json) gives actual argv, working directory, elapsed time and exit for each test/build/archive/runtime invocation. [Supplemental setup/graph record](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/SUPPLEMENTAL_EXECUTION.json) retains limitations and failed setup attempts. No proposed native command is presented as executed.

| Actual run | Exit | Result |
| --- | --- | --- |
| `python -B -m pytest -p no:cacheprovider --noconftest -q tests_e2e/test_invoice_actions_e2e.py` | 0 | 3 fixture tests |
| Same command for `test_copilot_failclosed.py` | 0 | 4 B1-S fixture tests |
| Same command for `test_followup_preview_e2e.py` | 0 | 1 L3 fixture test |
| `python -B <evidence>/P2B_REACT_QUALIFIED.py` | 0 | 34 preserved assertions; original nine included |
| `python -B <evidence>/P2B_REACT_NEW_QUALIFIED.py` | 1 | 36 PASS / 3 FAIL, no unexpected network |
| `python -B <evidence>/l3_dom_oracle.py` | 0 | 11 PASS / 0 FAIL, no unexpected network |
| `node --experimental-strip-types <evidence>/new_oracle.mjs` | 1 | 25 PASS / 16 FAIL |

`<evidence>` resolves to `E:/lotus-fin/docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1`; the ledger expands every path. Counts overlap and must not be combined as unique acceptance totals. Harness copies disclose clock/output substitutions and fresh context setup after invalid-open cleanup; no adversarial assertion removed. [Lineage](docs/reviews/evidence/lotus-final-acceptance-2026-10-12-01a130c1/HARNESS_LINEAGE.json).

Owned browser fixtures were terminated. Preserved React PID26544, expanded React PID22916, L3 PID21568 report exited and port released. Final port probes show 5188 and 5191 free. No shared running container/site was stopped or altered. Container inspection was filesystem/identity only, without site initialization, app imports or business access.

## Required live exit evidence

Before actual serving qualification, provide an approved Lotus-owned invoice/tenant/schema/policy authority, selected ERP-free core artifact, ordinary users and rights matrix, named isolated target, audit sink, versioned references and authorized snapshot/restore/cleanup boundary. Then run positive read plus two-tenant same-ID, field/document denial, disabled/logout/revoke, expiry, concurrent/late response, source mismatch/outage, invalid HTTP/schema/CSRF, audit and measured no-write/resource cases. NI-01–NI-14 in the existing native handoff are future designs, **not collected passing tests**. No approved native source/target exists in the reviewed materials; live acceptance remains BLOCKED.
