# Round 2 — B1-S Copilot UI fail-closed packet

10/10/2026 · FinTechathon Shenzhen · **B1S_CHANGES_REQUIRED**. This is the leading remediation candidate, but **not an approved implementation packet**. Source/callers are established; executable React test environment, observation-context policy and narrow ADR/scope decisions remain open. Deployment G10 is separately blocked and is not a substitute for these source/test prerequisites.

## Exact selected source and route

`develop` / `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, unchanged protected tree. `frontend/src/pages/copilot/components/VercelChatPanel.tsx`, SHA256 **CD0BEA832F6269F58836BC624941DDDDF62EE1277ADC5DF18C85125C9A749D51**, 738 lines. [Manifest](../evidence/phase0-round2-2026-10-10/SELECTED_SOURCE_MANIFEST.json), [numbered source](../evidence/phase0-round2-2026-10-10/HOST_SELECTED_SOURCE.txt). GitNexus context/impact first: notfound/UNKNOWN on stale index; static caller confirmation follows. No safe/unused graph conclusion.

```text
LotusCopilotPage → components/index export → VercelChatPanel.handleSendMessage
AppLayout → LotusCopilotDrawer → VercelChatPanel.handleSendMessage
  → axios POST /api/method/lotus_fin.api.copilot_api.chat_copilot
  → CopilotController.handle_send_message → ChatResponseDTO
  → API exception fallback: core.ai.agent_copilot.process_copilot_query
  → res.data.message / catch → message/tool/widget/status/badges
```

Two active **source callers**, not claimed browser execution: `LotusCopilotPage.tsx:295` passes selectedCompany with no identity key/reset; `LotusCopilotDrawer.tsx:28` always passes `Lotus-fin (Demo)` and is mounted by `AppLayout.tsx:253`. Drawer company is not proof of explicit demo authorization. Panel only scrolls on messages/loading; no abort/generation fence, no scope-clear effect. Global `formatBrandText` is shared elsewhere; keep selected rendering changes local. The actual request is inline axios; there is no separate `frontend/src/api/copilotApi.ts` in this path.

| Current branch | Source-observed behavior |
|---|---|
| Request | query/company plus fixed `as_of_date: 2026-09-26`; same fabricated args shown in tool trace. |
| HTTP200 + nonempty reply | `reply`/`content`/string treated as completed; nested failure ignored; tool-name selects widget without status/source qualification. |
| Empty response or transport error | catch produces hardcoded health/cash/risk/what-if/financing values and claims verified ERP/GL/completion. |
| Rendering | Unconditional `Lotus Fin Verified`, `ERP Live`, GL-analysis loading claim and green tool indicator; expanded output exposes raw JSON. |
| Untrusted text | Local `renderFormattedText` inserts markup without HTML escaping; `dangerouslySetInnerHTML` receives response/user text. Safe errors must not retain this raw-HTML path. This is source evidence, not an executed exploit. |

Current `ChatResponseDTO` SHA256 `262F3F8ECD9B7470AA06738BEAB232506DBC2B777C37EF4778A22D6C7EED06CF`: session_id/reply/tool_called/tool_label/tool_output/ui_widget/executed_tools; **no root status/provenance/cutoff/CID contract**. Extra root fields are not declared and default Pydantic handling ignores them. Legacy responses can retain statuses inside tool_output; method-level `success` does not qualify those outputs. Current host API allows guests and falls back on exceptions; runtime differs. B1-S is not permission enforcement or backend correctness closure.

Removing the UI date alone is insufficient: `CopilotController` defaults missing date to **2026-12-31**, and legacy risk routing contains **2026-09-26**. No server-owned current observation envelope is established. Changing these backend defaults is a separately approved dependency, not an implicit UI edit.

## Proposed typed presentation contract and compatibility

Local discriminated view model, **PROPOSED**: outcome `OK | PARTIAL | FORBIDDEN | SOURCE_ERROR | TIMEOUT | NOT_AVAILABLE`; `provenance=ERP_VERIFIED | DEMO_ONLY | UNKNOWN`; safe text, optional qualified widget, validated server CID, explicit observation date/timezone/source version when present. Parse transport `unknown`; no `any`-based trust decision. Transport, business status and source provenance are different axes. Root/nested contradictory statuses fail closed; failure in any displayed tool overrides a method-level success. Unsupported/malformed values map to NOT_AVAILABLE, not zero or completion.

| Existing input | Safe proposed UI mapping |
|---|---|
| HTTP401/403 / supported explicit FORBIDDEN | FORBIDDEN; fixed permission message, no financial widget or previous facts. Do not imply all permission failures currently use these HTTP codes. |
| Network failure / supported SOURCE_ERROR | SOURCE_ERROR; retry/navigation only, no financial content generated locally. |
| Recognized timeout / supported TIMEOUT | TIMEOUT; separate safe message; abort due to scope change is silent discard. |
| Empty/whitespace reply and no valid supported result | NOT_AVAILABLE; no synthetic financial success. Valid structured result without prose may still display its independently qualified widget; explanation unavailable is separate. |
| HTTP200, root success but tool_output SOURCE_ERROR/FORBIDDEN | Corresponding business failure; no success badge/widget/raw nested exception. |
| Supported PARTIAL | PARTIAL; show only explicitly available, qualified fields and visible limitation; missing schema/availability → suppress financial widget. Never generic “all complete”. |
| Legacy nonempty success without provenance | Render escaped/plain reply with UNKNOWN/neutral source label; no ERP-verification badge or financially verified widget. UI cannot certify model prose. |
| Qualified successful source envelope | OK; preserve genuine safe text and allowlisted widget; ERP_VERIFIED only after server source/context/evidence contract qualifies it. This complete envelope is a future contract case, not a current DTO claim. |
| Explicit isolated DEMO_ONLY envelope | Clearly label demo; no ERP badge. Company name, client checkbox or exception cannot establish demo mode. Existing backend support NOT_VERIFIED. |
| Returned server correlation ID | Preserve one validated allowlisted ID from an approved field/header, including errors; no invented ID labelled as server CID. Current standard DTO does not promise one. |

No raw error.message/trace/request args/doc JSON in DOM or console. Only fixed safe error text plus safe CID. Use React text nodes/explicit formatting tokens; test that HTML-like input cannot create elements. Loading text describes a pending request, not actual GL access. Financial badges and tool completion require qualified results, including nested status; remove raw-output `<pre>`. A generic successful natural-language reply can remain visible without representing financial truth.

**Observation/scope dependency decision:** preferred server-owned `observed_at`, timezone, authorized company and connection/version. Until an approved backend envelope exists, Chat must choose (a) an explicit user-selected historical cutoff labelled as requested/unverified, or (b) disable financial requests when qualified context is absent. Do not silently omit fixed dates or infer “today” from browser time. Company switch and unmount clear results/expanded payloads, cancel pending requests and fence all response/finally updates by generation. For connection/site/product changes, choose a real context-version prop or remount/reload contract; current company-only props cannot detect invisible connection switches. Drawer must receive authorized context or its financial chat must remain unavailable; hardcoded demo-company selection cannot stand in for authorization.

## Test runner and deterministic DOM acceptance

Current package has dev/build/lint/preview scripts, no frontend test runner. Vite/tsc local executables and dist **absent**, so React build/browser acceptance is **NOT_RUN**. Host Node22.19.0 is available. Existing installed Python Playwright/pytest/pytest-playwright and browser cache are inventoried, not launch-tested. Existing `tests_e2e/test_financial_health_workspace.py` is a convention reference but uses a shared target/admin and screenshot artifacts; it was not executed. [Test environment](../evidence/phase0-round2-2026-10-10/TEST_ENVIRONMENT.json), [installed packages](../evidence/phase0-round2-2026-10-10/EXISTING_PYTHON_TEST_DEPENDENCIES.txt).

Smallest feasible **proposal**: use existing Python Playwright/pytest against an isolated locked React build, intercept all `/api/**` traffic, deny other outbound calls and use DOM assertions. No new Vitest/RTL/jsdom dependency needed for this option. Provisioning the declared existing frontend lockfile/build environment and checking compatible browser availability remain prerequisites; no packages installed this round. New proposed test path `tests_e2e/test_copilot_failclosed.py` does not yet exist. It must own reviewed UI-server setup/teardown and fixtures, rather than use an ad-hoc runtime script or shared8080 proxy. Runner command after approval: `python -m pytest tests_e2e/test_copilot_failclosed.py`, with an explicit isolated UI URL and deny-all network fixture; no implicit shared-target default.

All assertions below are **DESIGNED, NOT_RUN**; fixture envelope values are test declarations, not real ERP gold:

| Case | Required DOM/behavior assertions |
|---|---|
| Qualified success | Exact returned text/qualified widget; only authoritative badge; no fallback constants; one server CID. |
| Legacy success / missing provenance | Text still visible; no ERP Live/Verified/GL assertion or qualified financial widget. |
| Explicit demo | Visible DEMO_ONLY; no ERP badge; failing real request cannot transition into demo. |
| 401/403 | Permission message; no financial content/tool-completed indicator; no raw response markers. |
| API/source outage; timeout | Distinct SOURCE_ERROR/TIMEOUT labels and retry availability; no fake KPI/chart/action. |
| Empty HTTP200 | NOT_AVAILABLE; no “completed analysis”, invented values or false zero. |
| HTTP200 + nested SOURCE_ERROR | Failure wins over root success and nonempty prose; widget absent. |
| HTTP200 + PARTIAL | Partial label and supported available subset only; unavailable metrics absent; no all-success badge. |
| Company switch / drawer close / connection reset | Old data immediately absent; delayed old response/finally cannot repopulate facts or alter new loading state; pending request aborted/fenced. |
| Safe output/CID | A recursive sensitive marker absent from DOM/console/widget; returned safe CID unchanged once; forged/HTML-like CID rejected; injected markup renders as text with no script/image element. |
| Cutoff | Request/context reflects approved date policy; fixed2026-09-26 absent; missing context does not fall into backend fixed default silently. |

## Conditional minimal implementation scope

Owner: **Chat** approves contract and any ADR variance; **Antigravity** implements exact approved batch; **Work** verifies independently. Source identity is the manifest above. Candidate existing edits are `VercelChatPanel.tsx` (`handleSendMessage`, local formatting/status/render branches, scope lifecycle) and `LotusCopilotDrawer.tsx` (authorized context/unavailable behavior). `LotusCopilotPage.tsx` and `AppLayout.tsx` are verified impacted callers, **read-only unless Chat approves the chosen context-prop plumbing**. Global brand helper, API/DTO/controller, agent runner, sessions and financial engines stay outside B1-S changes. New typed helper/hook/test files require exact names in the approved packet; the test path above is proposed, not created.

Minimal future edit order: typed compatibility parser → remove failure-generated finance/false badges/raw output → scope reset/abort/fence → approved cutoff/context behavior → deterministic DOM regressions for both callers. Preserve ordinary genuine responses. ADR001 source <200 lines conflicts with panel738, page427 and AppLayout256; a narrowly documented safety-patch variance or approved responsibility-based decomposition is required. Work cannot silently waive ADR or enlarge B1-S into a general refactor.

Rollback: revert only approved UI/helper/test edits to the manifest; disable the unsafe financial chat entry if rollback restores false-truth behavior. No ERP/session/data rollback. Preconditions still missing: executable isolated frontend environment; typed context/cutoff choice; Drawer context; exact helper/file set under ADR decision. Deployment and real backend provenance are separate release prerequisites. Remaining approval is Chat scope/contract arbitration, not a request to implement now. No F101/F102, engine/session rewrite, ERP writes, new SDK, paid LLM, or broad benchmark.

**Next bounded verification:** provide the locked isolated React runner/build identity, validate both callers' context propagation and the agreed envelope/cutoff fixture, then run the listed DOM cases. No further broad repository discovery is needed to decide B1-S scope.
