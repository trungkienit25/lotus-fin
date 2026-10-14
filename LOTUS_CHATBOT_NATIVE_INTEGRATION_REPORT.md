# Lotus Fin chatbot native integration — current gate report

12 October 2026, Asia/Saigon. Repository `E:/lotus-fin`, branch `codex/p2a-invoice-read-backend`, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`. This report binds to the [545-file SHA-256 manifest](docs/reviews/evidence/chatbot-native-integration-2026-10-12-01a13088/SOURCE_CANDIDATE_MANIFEST.json), digest `46ede75ac9c27dc935a60629556e6c0d19d3e085c078c41628d2213b678ff05a`. No production source, capability flag, deployment, commit, push, or business data was changed.

## Verdicts

| Required verdict | Status | Evidence and limit |
| --- | --- | --- |
| LOTUS_NATIVE_INTEGRATION | **BLOCKED** | Native invoice/tenant authority and approved versioned semantics absent. Current API and controller return disabled for search/open; no concrete native read port. |
| LOTUS_PRODUCT_INDEPENDENCE | **FAIL** for current runtime recipe | Dockerfile uses `frappe/erpnext:v16.35.0`; judge initialization installs `erpnext`. AI001–003 retain ERP financial inputs. A Frappe-only positive run was not executed. |
| LOTUS_AUTHORIZATION | **BLOCKED** | 343 P1/P2-A isolated regressions pass; Lotus-owned membership/document/field policy and ordinary-user native tests absent. |
| LOTUS_REAL_HTTP | **BLOCKED / NOT_RUN** | No approved isolated native target, current method declarations call the disabled helper, and no real serving Frappe HTTP was exercised. |
| LOTUS_NO_WRITE | **BLOCKED** | No approved native business-store snapshot or before/after measurement. Offline read tests are not a live no-write proof. |
| P2AB_LIVE_ACCEPTANCE | **BLOCKED** | P2-B offline oracle 96/96 passes against snapshot; source, HTTP, permissions and production mount are unqualified. |
| RUNTIME_REPRODUCIBILITY | **FAIL** | HEAD omits action/prepare source; current candidate uses host `node_modules` via junction and has no clean dependency/image/site build. |
| G10_READINESS | **BLOCKED** | Positive ordinary-user native journey, live denials, immutable serving artifact and rollback evidence absent. |

## Prerequisite reconciliation

Read `LOTUS_FIN_PRODUCT_INDEPENDENCE_AUDIT.md`, `LOTUS_FIN_CHATBOT_NATIVE_INTEGRATION_DESIGN.md`, `LOTUS_FIN_NATIVE_DATA_AUTHORITY_MAP.md`, `LOTUS_FIN_INTEGRATION_IMPLEMENTATION_HANDOFF.md`, `LOTUS_FIN_RUNTIME_REPRODUCIBILITY_PLAN.md`, root `AGENTS.md`, ADR001, Security Code V3, P1 MASTER, frozen P2-B wire, latest final integration packet and newer P2-B/L3 correction reports. The newest A0 set is dated 12 October and explicitly records `LOTUS_NATIVE_DATA_AUTHORITY=UNKNOWN`, design `PROPOSED`, and N0 approval outstanding. The latest corrections claim builder readiness for recheck, not Product/Data/Security approval. No later native authority/contract/target approval record was found in the current workspace docs. Older ERP source proposals are not native authority.

GitNexus is bound to `lotus-fin` on this branch at this HEAD, indexed 2026-10-12 07:02 UTC; working-tree additions postdate that index. Concept query returned no flows with FTS disabled. Exact upstream impact for `SearchInvoicesService` returned **LOW**, one controller importer, zero indexed processes. Exact file impact for `invoice_actions_api.py` returned **UNKNOWN**, zero resolved callers; text confirmation finds Frappe dynamic route declarations and test imports. No symbol was edited on the strength of a zero. Graph change detection before commit is inapplicable because no commit is made.

## Current path and offline checks

The authenticated React routes mount `LotusCopilotPage`/`VercelChatPanel`. `InvoiceActionPanel` and `FollowupPreview` have no production import. `invoiceActionClient.ts` produces a disabled response, including when its flag is on. The three `invoice_actions_api.py` POST declarations call `_frappe_post_handler`, which returns `CAPABILITY_DISABLED`. `InvoiceActionsController.search_invoices/open_invoice` are also disabled. `IAuthorizedInvoiceReadPort` has test doubles but no approved native adapter. The existing `ERP_READ`/`Sales Invoice` context cannot truthfully be relabeled native.

On the controlled candidate: P1/P2-A pytest **343 passed, exit 0**; P2-B independent Node oracle **96 PASS/0 FAIL, exit 0**; P2-B units **66 passed, exit 0**; L3 independent oracle **16 PASS/0 FAIL, exit 0**; L3 units **20 passed, exit 0**; TypeScript app/node checks **exit 0**; Vite production build **exit 0**. All use host-installed dependencies. [Commands and output](docs/reviews/evidence/chatbot-native-integration-2026-10-12-01a13088/) give exact invocations and traces. The P2-B candidate browser fixture returned **exit 1** because its network guard rejected a Vite asset resolved through the host dependency junction; this is an environment containment failure, not a native HTTP result. L3 fixture returned **1 passed, exit 0**. Running the same fixture suites from the original working tree with identical source hashes gave **P2-B 3/3** and **B1-S 4/4**, both exit 0; those are host fixture results, not candidate or native HTTP acceptance. See the dedicated [candidate report](LOTUS_CHATBOT_REPRODUCIBLE_CANDIDATE.md) and [authorization test matrix](LOTUS_CHATBOT_NATIVE_AUTHORIZATION_TESTS.md).

The B1-S candidate browser fixture timed out after 150 seconds; its owned local Vite process was stopped and port 5188 released. Neither candidate fixture failure is counted as a product permission result. The hard stop is N0: Product/Data must name and approve the Lotus-owned invoice and tenant authority, record lifecycle/version mapping, and Security must approve membership, row/document/field rights and contract migration. Until then an adapter, HTTP composition, and frontend transport would encode invented authority. [Exact work packages](LOTUS_CHATBOT_INTEGRATION_WORK_TO_CHAT.md) preserve the disabled private stage.
