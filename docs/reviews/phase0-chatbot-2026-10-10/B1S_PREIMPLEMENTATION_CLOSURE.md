# Round 3 — B1-S preimplementation closure

10/10/2026 · FinTechathon Shenzhen · **B1S_READY_FOR_CHAT_APPROVAL** · **FIRST_IMPLEMENTATION_BATCH = B1-S**. Readiness means the exact safety change and independent evaluation are reviewable/provisionable. It is not contract approval, ADR variance, implementation dispatch, backend permission closure or post-fix PASS. Contract candidate: **B1S_UI_SAFETY_V1, PROPOSED**.

## Authority, new evidence and pending decisions

Incorporate the user's Round 3 D1–D5 as proposed directions: remove fabricated financial fallback/unqualified badges, render untrusted text safely, disable source-dependent requests without qualified context, restrict V1 to past-final-due invoices, choose judge delivery by evidence. Formal Chat approval of contract/file set and ADR variance remains pending. [Workflow §34](../../features/LOTUS_FIN_AI_FEATURE_BUILD_WORKFLOW_3_TOOLS_V3_VI.md), [ADR001](../../adr/001-clean-architecture-core-first-adr.md), [Security Code V3](../../security/LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md) remain authority.

Current `develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`;333protected hashes unchanged. [Current source manifest](../evidence/phase0-round3-2026-10-10/SOURCE_MANIFEST.json), [numbered selected source](../evidence/phase0-round3-2026-10-10/SELECTED_SOURCE.txt). Cached GitNexus exact fingerprint reverified; context/impact notfound/UNKNOWN, bounded10s calls only, no package-manager acquisition. Static confirmation finds two direct panel callers and the page's route wrapper; no symbol declared dead. Graph risk remains unresolved; subsequent implementation must repeat bounded impact and confirm current callers, not infer low risk from zero.

New evidence changes the old runner blocker: lockfile v3 contains422entries,23direct dependencies; all direct resolved versions satisfy declared ranges, root ranges match, and Node22.19.0 satisfies declared engine ranges. Every non-root entry has resolved/integrity metadata, registry URLs only. One declared install script belongs to optional Darwin-only fsevents. React19.3.0, Vite8.3.3 and TypeScript6.0.3 primary registry metadata returned HTTP200 and matched lockfile integrity. This is **not** a full transitive download/native compatibility/build PASS. [Lock audit](../evidence/phase0-round3-2026-10-10/LOCKFILE_SEMVER_AUDIT.json), [metadata integrity](../evidence/phase0-round3-2026-10-10/CORE_REGISTRY_INTEGRITY.json). No installation executed.

Installed Python3.13/Playwright1.58.0/pytest9.0.2/pytest-playwright0.7.2 are available. Chromium145.0.7632.6 successfully ran3 synthetic DOM assertions with offline network + deny-all interception; context/browser closed. [Actual smoke](../evidence/phase0-round3-2026-10-10/OFFLINE_BROWSER_SMOKE.txt), [browser fingerprint](../evidence/phase0-round3-2026-10-10/BROWSER_FINGERPRINT.json). It proves usable browser/DOM assertions only, not an app exploit or G4B. Vite/tsc/dist remain absent locally. The harness is credibly provisionable after authorization, so missing installed frontend dependencies alone no longer blocks preimplementation review.

## Exact source/caller/context map

| File / symbol | Current identity and responsibility |
|---|---|
| `frontend/src/pages/copilot/components/VercelChatPanel.tsx` / handleSendMessage, renderFormattedText, rendering/lifecycle | SHA256 `CD0BEA832F6269F58836BC624941DDDDF62EE1277ADC5DF18C85125C9A749D51`,738lines. Inline axios calls Copilot API with fixed2026-09-26; catch creates financial constants; raw JSON/unescaped HTML and unconditional truth badges. **Allowed edit.** |
| `frontend/src/components/copilot/LotusCopilotDrawer.tsx` / panel mount | SHA256 `0529C47CB3FD69F1EBFFF325A4A51F933C57D74B2AC6BCAA0595620954141868`,55lines. Hardcoded demo company; close unmounts panel. **Allowed edit only to remove fake scope and preserve unavailable presentation.** |
| `frontend/src/pages/copilot/LotusCopilotPage.tsx` | SHA256 `3B728165954CCC04B684AA0AC6879E781C6AD57259BFB24B20D89AC8A8CEA149`,427lines. selectedCompany starts demo; GET `/api/resource/Company?fields=["name"]` populates options, errors silently retained. Selected label/list visibility is not financial authorization. **Read-only caller regression.** |
| `frontend/src/components/layout/AppLayout.tsx` | SHA256 `017DB86C292CD21DAE85462FDE93B2B0E2C3E2234D67759688194A04683C84E5`,256lines. Mounts Drawer on non-AI pages, no authorized connection context prop. **Read-only regression.** |
| `frontend/src/App.tsx`, `pages/dynamic/UniversalPageView.tsx` | `/ai`, `/copilot` and AI workspace aliases render the page; `/page/lotus-copilot` maps through UniversalPageView. Additional manifest hashes preserved. **Read-only test route dependencies.** |
| `lotus_fin/lotus_fin/api/copilot_api.py`, presentation controller/DTO, core.ai.agent_copilot | Current DTO has no qualified provenance/observation/CID. Host API has legacy fallback; controller defaults2026-12-31 and legacy routes also fixed dates. **Read-only dependency; no backend edits.** |

No current product/site/connection switch state or authoritative observation provider is wired to these callers. An unseen external connection switch cannot be detected from company alone. **B1-S enables no source-dependent backend requests under the current caller contracts.** It must not guess a safe nonfinancial intent via regex/LLM: the same endpoint can dispatch financial tools. Preserve local help, input/user text and safe already-returned/rendered replies where applicable; show unavailable on attempted remote action. Do not build a new nonfinancial backend endpoint here.

Panel gains optional **presentation-only** `contextKey?: string` for lifecycle invalidation; it conveys no authority and cannot enable requests. Generation identity includes company/contextKey and mount/reset epoch. Existing callers may omit it because all current remote financial actions remain disabled. Future connection integration must provide a key on actor/product/site/connection/version change or require remount/full reload; do not advertise hidden-switch handling before that integration. Drawer removes the hardcoded company, using an empty/unavailable scope rather than fake demo authorization. Full page keeps selected company as an explicitly unqualified label, never permission evidence.

Pending requests/reset/scope change/unmount: increment generation, abort owned AbortController, clear assistant facts/tool/widget/expanded output/loading; validate generation before every success/error/finally update. User text never authorizes financial calls. Future server-owned context dependency is separate: authenticated bootstrap with bound actor/product/site/connection/company, observed instant/local date/timezone/version, permission/capability and CID policy; validated request-date binding, expired/revoked handling, no fixed defaults. No name or client prop proves that dependency exists.

## B1S_UI_SAFETY_V1 compatibility contract

Separate axes: HTTP/transport outcome, recognized business outcome, financial-source provenance, rendering eligibility. Transport input is `unknown`, parsed into a discriminated presentation type; no `any` trust decision. Profile **CURRENT_UNQUALIFIED** accepts the observed reply/content/string forms and recognized root/nested business statuses. It grants **no ERP_VERIFIED numeric widgets and no enabled demo capability**. Metadata merely spelling `ERP_VERIFIED`/`DEMO_ONLY` cannot upgrade this profile. Qualified source/demo adapters are later contracts, not fields claimed implemented today.

Precedence: scope-generation mismatch → discard; HTTP401/403 or any recognized FORBIDDEN → permission outcome; known transport timeout → TIMEOUT; other transport outage → SOURCE_ERROR. Within a200 body, nested failure overrides wrapper success; one consistent terminal failure maps to its safe outcome; contradictory terminal failures/unsupported values map NOT_AVAILABLE. PARTIAL overrides generic success and retains only safely qualified available rendering. A financial tool/action with missing qualification maps NOT_AVAILABLE even when prose/root success exists. Missing/whitespace generic text and no supported result is NOT_AVAILABLE. No missing/error value becomes zero.

Exact conservative financial-result detector: any nonempty tool_called, nonempty executed_tools, tool_output/ui_widget/result payload or finance-action descriptor is source-dependent, including unknown tool names. Do not whitelist unknown output merely because its root says success. Reply-only benign text can use neutral rendering; its numbers, if any, gain no verified status. Error precedence runs before this detector so supported SOURCE_ERROR/FORBIDDEN/TIMEOUT/PARTIAL stays distinguishable while numerical payloads remain suppressed.

| Input | Visible safe result / invariant |
|---|---|
| 401/403 or FORBIDDEN | `FORBIDDEN` — “Bạn không có quyền thực hiện yêu cầu này.” No tool completion or financial content. |
| Source/API outage | `SOURCE_ERROR` — “Không thể truy cập nguồn dữ liệu. Vui lòng thử lại.” No fallback metrics. |
| Timeout | `TIMEOUT` — “Yêu cầu đã hết thời gian chờ.” Scope abort is silent discard. |
| Empty, unsupported, contradictory, missing financial source/context | `NOT_AVAILABLE` — “Chưa đủ ngữ cảnh hoặc nguồn đã xác minh để thực hiện yêu cầu này.” No remote call when prerequisite missing. |
| Legacy generic safe reply without finance tool/result | Reply as React text, neutral “Nguồn chưa xác minh”; no verification badge/widget. |
|200 success + nested SOURCE_ERROR | SOURCE_ERROR; do not echo contradictory successful/financial model prose. |
| PARTIAL | Visible partial status/limitation, no unsupported numerical widget; no all-complete badge. Missing/unqualified amounts stay absent. |
| Qualified-success test declaration | Preserve genuine safe text; this profile still suppresses verified numeric widgets. Full qualified financial rendering is **NOT_APPLICABLE to B1-S**, pending later approved adapter. |
| Explicit demo test declaration | Unsupported here: no fake demo capability. Preserve benign text only if nonfinancial; otherwise NOT_AVAILABLE. A future formally supported demo must be isolated and labelled, never entered by failure/company name. |

Source-to-render threat: model `reply`/legacy `content` and user attachments/text → message.content → formatBrandText/local regex markup → dangerouslySetInnerHTML in list/paragraph branches. Regex transforms bold/italic/code but does not escape `<script>`/`img onerror`/unsafe links. Tool output → stored `any` payload → JSON.stringify in expanded `<pre>` leaks arbitrary nested error/document fields. Tool name → widget/actions/trust badge without source qualification. This is **static risk**, not a browser exploit reproduced against the app.

Smallest fix: render text using React text nodes with preserved line breaks; remove local HTML converter/unsafe insertion and automatic linkification. No new sanitizer/markdown dependency. Remove raw tool JSON and financial payload from presentation state; allow only fixed tool labels/status and safe text. No text can create a script/image/iframe, trusted link, tool/action or scope. Remove unconditional Deterministic/ERP Live/Verified/GL loading claims. Block panel's finance quick prompts, financial widget/action and inspector shortcut without qualified context; unrelated report tabs outside this selected path are not remediated by B1-S.

CID: permit one returned response header `X-Correlation-ID` if safe `[A-Za-z0-9][A-Za-z0-9._:-]{0,63}`; it is a proposed preservation rule, not a claim the current endpoint supplies it. No CID from model prose/nested tool payload; no fabricated server CID. Missing ID is absent; malformed/conflicting IDs suppressed. Only fixed error text/CID may appear; no raw error object/message, args or sensitive payload in DOM/console.

## Exact candidate implementation packet and ADR choice

Owner sequence: Chat approves **B1S_UI_SAFETY_V1 + exact allowlist + one-time ADR variance + isolated dependency provisioning** → Antigravity implements → Work runs independent G4B → Chat closure. No dispatch now.

**Recommended strategy:** one-time safety variance for the existing738line panel; add small typed responsibilities, not a full UI decomposition. Two existing edited files: panel and Drawer above. Seven **new proposed** paths, currently absent, each source file must remain <200lines:

- `frontend/src/pages/copilot/components/copilotPresentation.ts`: normalization/safe messages/CID; ~80–150lines.
- `frontend/src/pages/copilot/components/CopilotMessageBody.tsx`: plain-text/status rendering reused by panel and fixture; ~40–100lines.
- `frontend/src/pages/copilot/components/useCopilotRequest.ts`: owned abort/generation/reset handling; ~70–140lines, injectable transport only as internal dependency, no production test flag/permission toggle.
- `tests_e2e/test_copilot_failclosed.py`: table-driven independent DOM assertions; ~100–180lines.
- `tests_e2e/copilot_fixture/index.html` and `tests_e2e/copilot_fixture/main.tsx`: test-only mount of real message body/hook/panel/callers; ~10–120lines each.
- `tests_e2e/copilot_fixture/vite.config.ts`: plain test-only configuration, no shared proxy, strict local port, no production route; ~30–60lines.

The allowlist contains **seven new paths** (HTML included); no other source/config/package/lockfile edits. Estimated total delta ~400–750lines including tests, ~150–300 existing lines removed/replaced; estimates are review planning, not a line-budget PASS. Existing page/AppLayout/route/auth files remain read-only. Test harness mounts internal request hook with test-author request eligibility and intercepted transport to exercise error/race cases; it cannot enable production financial actions, and does not prove authorization. Caller tests separately assert current production gating sends **zero Copilot POSTs**. No runtime test entry shipped in production.

Alternative ADR-compliant full decomposition would split header/composer/messages/tools/scope/request responsibilities, ~6–9production files and ~700–1000moved/reviewed lines, plus tests; removes the738line violation but increases layout/state/export regression surface. Exact alternative names if selected: `CopilotHeader.tsx`, `CopilotComposer.tsx`, `CopilotMessageList.tsx`, `CopilotToolStatus.tsx`, plus the three typed files above and slim panel. This is a different allowlist requiring Chat approval. Recommended variance is solely this safety batch; Page427/AppLayout256 remain untouched and no broad ADR compliance is claimed. **No variance has been granted.**

Rollback: revert only approved files and disable the unsafe Copilot entry if rollback reintroduces fabricated success/injection; no ERP/session/data rollback. Non-goals: backend dates/permissions/provider/session, financial engines, ordinary report views, V1, F101/F102, SDK install, paid LLM, throughput or judge release. Before edits repeat source/hash/impact checks; fingerprint mismatch requires targeted reconciliation, not copying runtime files.

## Reproducible isolated harness and independent oracle

Provision only after authorization in a fresh private checkout/copy named for this batch. Verify source/lock hashes before starting: package SHA256 `35386677A8EC903A6FD9C75B09E5732603A2A4626EABCB4E528386F7E81DA50C`, lock SHA256 `4530FD8C3E9496A684A8569EE6A47DD0F3EB8D010B3DEF7A6D4222DB67F23DD9`. Use Node22.19.0/npm11.7.0 and installed Python/browser fingerprints. No npmrc/credentials inherited; cache/temp files owned by this checkout. Proposed provisioning `npm ci --ignore-scripts --no-audit --no-fund` in its frontend directory; do not update lockfile. Review optional native dependencies and require build success; if scripts/binaries are needed, stop for bounded review, never broadly enable scripts. No new frontend test framework. Actual downloads/build remain NOT_RUN.

Proposed harness fixture configuration uses `127.0.0.1:5188`, strictPort, no proxy/HMR/service workers, fixture-only root and allowed imports from this isolated frontend source/node_modules. It must refuse occupied port or unexpected origin, never fall back to5173/8080. Use the installed local Vite executable, not npx. Python tests intercept **all** API requests before navigation, fulfill declared auth/company fixtures if mounting callers and abort everything undeclared; static files only from the exact fixture origin. Route HTTP200/401/403 or transport failure/delay deterministically. Block websocket/fetch/beacon/external origins and assert no unhandled network; add unreachable test-server API fallback so requests cannot proxy to ERP if browser interception fails. Any unexpected network request fails the test. Build/typecheck the approved source under its actual tsconfig; fixture JSX transpilation alone is not typecheck PASS.

Reproduction after approval, from the isolated checkout: use `frontend/node_modules/.bin/vite.cmd --config tests_e2e/copilot_fixture/vite.config.ts --host 127.0.0.1 --port 5188 --strictPort` (POSIX local binary equivalent); run `python -m pytest tests_e2e/test_copilot_failclosed.py` with required explicit fixture URL and test-owned temp path. The proposed test module owns reviewed server startup/teardown and refuses absent configuration. Auth/company fixtures are synthetic declared responses for `/api/method/frappe.auth.get_logged_user` and `/api/resource/Company`; other caller-layout reads must be enumerated from the hashed source before being fulfilled, never forwarded or handled by a broad success fallback. G4B also runs the existing `npm run build` under the locked isolated frontend directory and records any unrelated build blocker separately; no automatic dependency upgrade or broad source repair.

Fixture data lives in the proposed test's parameter table: `SAFE_REPLY`, `SENSITIVE_MARKER`, synthetic identities/scopes/dates, exact error statuses and inert injection strings; no financial fixture represents real ERP truth. Fixture mount uses actual I18nProvider/router where callers require them. Pure normalization + actual MessageBody/hook DOM cases do not need production bootstrap; both caller mounts must prove disabled current-context behavior. Keep independent expected strings/status/absence assertions separate from normalization implementation; never derive gold from the code under test.

| Deterministic fixture | DOM/pass-fail oracle |
|---|---|
| Declared qualified success with SAFE_REPLY | Exact text rendered; CURRENT_UNQUALIFIED profile shows no verified KPI/badge/action. Later qualified-widget acceptance explicitly outside B1-S. |
| Legacy reply, no provenance/tool | SAFE_REPLY visible; neutral source label; no ERP Live/Verified. |
| Declared DEMO_ONLY / company named Demo | Cannot grant supported demo/financial action; no ERP badge; financial case unavailable. No exception→demo transition. |
|401/403, source failure, timeout | Exact distinct safe status/message; no numeric widget/completed tool, no SENSITIVE_MARKER. |
| Empty200;200 root success+nested SOURCE_ERROR | NOT_AVAILABLE for empty; SOURCE_ERROR beats success; no fabricated completion/content. |
| PARTIAL with unavailable metric | Partial visible; unavailable metric/raw numeric widget absent, not replaced by0. |
| `<script>`, `<img onerror>`, HTML/unsafe-link text in user/model/source | Literal text/no generated script/img/iframe/link; marker JS does not execute, no tool/action/network created. |
| Company/contextKey changes while old fixture response pending | Clear previous content immediately; late old success/error/finally cannot add facts or change new loading state; abort/reset verified. |
| Drawer close/remount | New panel empty; disposed request cannot update remount; no hardcoded authorized demo scope. |
| Missing/expired/context-default date | Both current callers make0Copilot POSTs; visible unavailable; never omitted date activating fixed backend default. |
| Safe returned header CID; forged CID/nested secret | One safe ID unchanged; malformed/nested ID absent; SENSITIVE_MARKER absent from DOM/console/state-visible payload. |

For the declared qualified-success fixture, SAFE_REPLY is a nonfinancial benign reply; a second variant with a known financial tool must instead show NOT_AVAILABLE under CURRENT_UNQUALIFIED. A response spelling a qualified source cannot grant financial eligibility. Demo preservation is conditional on a future actually supported server contract; unsupported demo declarations are negative tests here, not a new demo feature.

All app cases **DESIGNED / NOT_RUN**. The3actually-run synthetic smoke assertions are separate. Cleanup in fixture finally: close owned context/browser; stop only recorded Vite PID/process tree; verify port no longer belongs to test PID; remove only resolved batch-owned temp/profile/build paths after root validation; preserve manifests/redacted traces. No broad process kill, repository deletion, shared container/site/volume removal or screenshots of real records.

## Gate arbitration

| Gate | B1-S preimplementation verdict |
|---|---|
| G1 | **PASS scope readiness**: exact current sources/callers, locked environment and browser capability; provisioning/build execution pending authorized implementation. |
| G2 | **PARTIAL / ready for approval**: exact proposed compatibility + disabled-context behavior; formal Chat approval/ADR variance pending. |
| G3 | **PASS narrow safety dependency**: current source remains unqualified and cannot enable financial rendering/actions; no backend financial-source PASS implied. |
| G4A | **PARTIAL / design ready for approval**: independent fixture/DOM/network/cleanup design, executable browser and credible provision plan; no post-fix assertions required to PASS yet. |
| G4B | **NOT_RUN**: implement then real source DOM/build regressions. |
| G10 | **BLOCKED independently**: fresh immutable artifact/site/HTTP acceptance absent; does not block this local safety change. |

G01–G03 not closed by this UI patch/mock harness; required separately for stateful AI007. Exact remaining approval is contract/ADR/allowlist/provisioning; not another general audit. If Chat refuses the variance, choose the explicit decomposition alternative before dispatch.
