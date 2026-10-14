# B1-S — independent G4B verification

10/10/2026 · FinTechathon Shenzhen · **B1S_G4B_CHANGES_REQUIRED**. Contract `B1S_UI_SAFETY_V1` only. B1-S cannot close. **G10 remains BLOCKED separately.** No application/test source correction, ERP call, dependency installation, deployment, commit or dispatch was performed.

## Source and authority

`develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, with uncommitted implementation. HEAD alone does not identify the reviewed artifact: use [source hashes](../evidence/b1s-g4b-2026-10-10/SOURCE_BEFORE.json), [numbered source](../evidence/b1s-g4b-2026-10-10/NUMBERED_SOURCE.txt) and [exact diff](../evidence/b1s-g4b-2026-10-10/TRACKED_DIFF.patch). Latest user request supplies approved review scope; Round 3's historical “PROPOSED/pending approval” wording is preserved, not silently rewritten.

Read implementation report, [B1-S closure](B1S_PREIMPLEMENTATION_CLOSURE.md), Round 3 packet, dated gate matrix, ADR001, Security Code V3, workflow §31–§34 and AGENTS/GitNexus instructions. Requested `LOTUS_FIN_CHATBOT_ASSISTED_ACTIONS_SOLUTION_DESIGN_VI.md` was **not found**, including untracked/ignored workspace inventory. No alternative design was invented; acceptance uses the explicit approved B1-S contract. Provide that reference to Chat if it contains additional obligations.

GitNexus exact cached CLI fingerprint verified; graph `316c5bd…`, indexed 02/10, remains **61 commits stale**. Query returned unrelated historical skill flows; current `VercelChatPanel` context is notfound. No safe/unused verdict or refresh/download. Static fallback confirms Page → Panel and AppLayout → Drawer → Panel. No symbol deletion proposed.

## Exact changes and ownership

Round 3 comparison: **331/333 protected files match; the two mismatches are precisely the approved existing edits**. HEAD unchanged, staged diff empty, no tracked deletion/backend/package/lock/config change. Seven approved new source/test paths and root implementation report were absent at the earlier snapshot. Other pre-existing untracked files, including runtime/session candidates, are not attributed to Antigravity. Attribution is based on baseline inventory and actual contents, not file author metadata.

| Reviewed implementation file | Actual lines, including blanks | Role / compliance |
|---|---:|---|
| `frontend/src/pages/copilot/components/VercelChatPanel.tsx` | 532 | Approved existing variance; fabricated fallback, raw tool state and unsafe HTML removed |
| `frontend/src/components/copilot/LotusCopilotDrawer.tsx` | 55 | Approved existing edit: fake Demo company removed |
| `frontend/src/pages/copilot/components/copilotPresentation.ts` | 184 | New production source <200; normalization incomplete |
| `frontend/src/pages/copilot/components/CopilotMessageBody.tsx` | 57 | New production source <200; React text rendering |
| `frontend/src/pages/copilot/components/useCopilotRequest.ts` | 156 | New production source <200; lifecycle partly correct |
| `tests_e2e/test_copilot_failclosed.py` | 222 | Approved test path; 3 real assertions-based tests, incomplete coverage and standalone isolation |
| `tests_e2e/copilot_fixture/index.html` | 12 | Test entry only |
| `tests_e2e/copilot_fixture/main.tsx` | 121 | Real production imports; hook qualification is synthetic; no actual Page mount in supplied tests |
| `tests_e2e/copilot_fixture/vite.config.ts` | 29 | Local 5188/strictPort/no proxy; broad workspace fs allow; Vite client still attempts local WS |

Root `B1S_IMPLEMENTATION_REPORT.md` read and hashed. Report line counts differ from actual counts; use this manifest. All three new **production** files satisfy <200. The 222-line test exceeds the ADR's general wording; do not extend the panel variance to tests silently. Chat should resolve that test-file limit while approving the narrow correction; no file split/new allowlist assumed here. Read-only caller/dependency fingerprints include Page, AppLayout, route files, package/lock and backend in the 333-file baseline.

## Contract compliance

| Requirement | Result | Evidence / boundary |
|---|---|---|
| S1 remove fabricated financial fallback | PASS narrow | Diff removes fabricated KPI blocks; supplied source/empty/financial failures display no widgets. No live financial correctness claim |
| S2 typed failure precedence / missing source | **FAIL** | Root denial overwritten, nested tool failures lost, unknown/NOT_AVAILABLE statuses become OK; PARTIAL becomes NOT_AVAILABLE; result/action detection incomplete |
| S3 inert untrusted content / error minimization | PARTIAL | Body + actual panel user HTML/unsafe URLs inert; no script/img/a/iframe, console marker absent. Failure normalization can expose synthetic marker in hook DOM; production remote path currently blocked |
| S4 scope clear / success, failure, finally, unmount | **FAIL** | Six company/key/reset success+failure races preserve new loading. Actual Page company switch and panel key switch retain old messages. Hook unmount returns old OK result when transport ignores abort |
| S5 current callers / local functionality | PARTIAL | Actual Page and Drawer both send 0 Copilot POSTs; composer/reset/Drawer close-remount work. Panel financial inspector remains enabled; local GL connection claim remains |
| S6 safe CID | PASS tested subset | Valid returned header preserved; 65-char/conflicting IDs and forged nested CID suppressed. No fabricated server CID |

## Findings

**F01 — HIGH, response safety contract: wrong status precedence and unsupported success.** `copilotPresentation.ts:107–137,155–174` selects one status (`msgObj.status || obj.status`) instead of reconciling supported root/nested outcomes. Actual hook DOM: root FORBIDDEN + nested OK → **OK / SENSITIVE_MARKER**; unknown status and explicit NOT_AVAILABLE + reply → OK. Nested `tool_output.status` SOURCE_ERROR/FORBIDDEN → NOT_AVAILABLE; conflicting SOURCE_ERROR/TIMEOUT → TIMEOUT; PARTIAL + tool output loses PARTIAL. High severity is the approved denial/error contract violation. This is synthetic transport reproduction against actual code, **not** an ERP HTTP exploit or production credential leak: both current production callers block all Copilot requests.

**F02 — HIGH, incomplete financial-result detector.** `copilotPresentation.ts:32–35,140–145` misses `result` and finance-action descriptors, and relies on truthiness for tool/widget payloads. Actual `result`, `suggestedActions`, and DEMO_ONLY + result fixtures retain model prose as OK rather than NOT_AVAILABLE. All tested widget flags remain false, so no numeric widget exploit is claimed. Unknown tool names correctly deny. Add conservative presence/shape handling for the approved descriptor set; demo metadata must not grant eligibility.

**F03 — MEDIUM, old scope presentation survives.** `VercelChatPanel.tsx:43–52,62–66,127–142,152–155`: hook scope reset does not clear component messages. Actual production Page retains `SCOPE_A_LOCAL_MARKER` after selecting Company B; real panel retains `CONTEXT_A_MARKER` after contextKey change. Clear old messages/facts/CID/source labels/copy state with scope/reset, and fence every consumer append. The observed content is local user text and fixed unavailable messages, not retrieved ERP data.

**F04 — MEDIUM, unmount invalidates abort only.** `useCopilotRequest.ts:40–47,98–108,140–144`: cleanup does not increment generation. Controlled injected transport ignores abort; completion after real component unmount returns OK / UNMOUNT_OLD_MARKER to its consumer. React does not restore an unmounted DOM; genuine production Drawer close/remount starts empty (PASS). The flaw is completion eligibility/finally after disposal. Delayed unmount rejection is NOT_RUN, not inferred PASS.

**F05 — MEDIUM, transport timeout loses TIMEOUT.** `useCopilotRequest.ts:129–139`: Axios-style `ECONNABORTED` with no response is mapped to status500 → SOURCE_ERROR. Actual DOM fault injection confirms it. Handle known timeout codes before generic outage and keep cancellation/stale completion silent. This did not measure a live 15-second network timeout.

**F06 — MEDIUM, misleading source claim / financial shortcut.** `VercelChatPanel.tsx:210–221,274–275,280–300,406,420–440`: actual unqualified Page still claims “connected to General Ledger”; Reports remains enabled and calls the financial inspector callback. Starter/quick financial prompts still look enabled, although remote dispatch is blocked. Remove unqualified GL claims and disable panel financial shortcuts/inspector with visible unavailable guidance. Keep ordinary Page report tabs outside this patch. No report API or ERP request was executed to exploit the shortcut.

**F07 — MEDIUM, supplied acceptance harness insufficient alone.** `test_copilot_failclosed.py:27–45,49–54,64–72,127,202`; fixture `main.tsx:19–27,47–55`: startup accepts any listener at5188 without ownership verification; teardown terminates the `.cmd` launcher without demonstrating child-tree cleanup; APIs receive broad `{}` fallback, other network is not denied. It mounts Panel/Drawer, not actual Page. No timeout/PARTIAL/contradiction/scope/unmount negative tests. Hook fixture consumer also stores every result and does not clear result on scope changes, so it cannot independently prove production presentation clearing. Independent review therefore used an owned server and deny-all wrapper, preserving original assertions, plus actual Page and hook/component probes.

**F08 — LOW / latent enablement risk.** `useCopilotRequest.ts:8,54–56,71–75,92`: exported boolean eligibility can bypass the client guard and still dispatch the old fixed `2026-09-26` date. No current Panel caller passes true; current zero-POST gate PASS. Do not advertise this option as server authorization or enable it in later integration. Keep any synthetic eligibility tied to injected test transport; a later qualified context/date contract needs its own approval. No backend fix requested in this review.

Maintainability: `unknown` input and small renderer/hook are useful improvements; `SafePresentationResult` is not a discriminated outcome union, parser casts/coercions under-validate statuses, unused TransportOutcome does not implement separate axes. Lint warns about render-time ref access (`activeGeneration`), effect state updates and unused translation variable; no blanket clean-code PASS. Avoid generic SDK/framework abstractions for this repair.

## Actual execution and evidence

Existing installed dependencies were copied into a private `%TEMP%/lotus-b1s-g4b-…` workspace; **no install/download/lifecycle provisioning**. All 11 copied source/package/lock hashes match host. Node22.19.0/npm11.7.0; Python3.13.7, pytest9.0.2, Playwright1.58.0, Chromium1208. Installed tool hashes and local build artifact hashes retained. No runtime/container/image identity acceptance; Docker was not used.

| Exact command in isolated environment | Exit / result |
|---|---|
| `node node_modules/typescript/bin/tsc -b --pretty false` (frontend cwd) | **0 / PASS** |
| `npm.cmd run build` (frontend cwd) | **0 / PASS**, bundle >500kB warning; not latency/throughput acceptance |
| `npm.cmd run lint -- src/pages/copilot/components/copilotPresentation.ts src/pages/copilot/components/useCopilotRequest.ts src/pages/copilot/components/CopilotMessageBody.tsx src/pages/copilot/components/VercelChatPanel.tsx src/components/copilot/LotusCopilotDrawer.tsx` | **0 / PASS command**, warnings retained |
| `Get-Content -Raw docs/reviews/evidence/b1s-g4b-2026-10-10/REVIEW_REPRODUCTION.txt \| C:/Python313/python.exe -` | pytest assertions **3 passed / pytest exit0**; outer process subsequently failed on stdout encoding, not assertion failure; JUnit preserved |
| same reproduction, `C:/Python313/python.exe - --supplemental-only` | **exit1**, completed **36 named cases:20 PASS/16 FAIL**, no harness BLOCKED in final run |

[Machine ledger](B1S_G4B_TEST_RESULTS.json), [actual DOM results](../evidence/b1s-g4b-2026-10-10/DOM_RESULTS.json), [supplied JUnit](../evidence/b1s-g4b-2026-10-10/SUPPLIED_JUNIT.xml), [reproduction](../evidence/b1s-g4b-2026-10-10/REVIEW_REPRODUCTION.txt). Counts are separate overlapping suites, not a combined coverage metric. Reproduction is review evidence executed through stdin, no ad-hoc ERP/runtime/business script added.

Review wrapper overrides only unsafe fixture lifecycle/browser/network setup, not gold/assertions or production code: existing Chromium, owned5188/strictPort, declared API fixtures, all other outbound/API denied; service workers blocked and WebSockets intercepted without upstream connection. Production Page mounted from its real source with real router/i18n; Company A/B are synthetic. Current remote requests are intentionally disabled, so delayed Drawer financial requests cannot be originated under this contract. No live authorization/session proof.

Preliminary copy exclusions, stdout encoding, synchronous WS-close stall and deferred-promise probe invocation were reviewer harness errors, retained separately; not product FAILs. Owned process trees verified/stopped, no shared PID killed. Final browser/server closed, port5188 free, private workspace deletion tracked in cleanup evidence. Application fingerprints and tracked implementation diff **unchanged throughout review**.

## Gates, rollback and next owner

| Gate | Current verdict |
|---|---|
| G1 | PASS narrow source/environment/caller/test identity; no immutable deployed identity |
| G2 | **FAIL** approved response/lifecycle/presentation contract |
| G3 | PARTIAL: current 0-POST/no financial widget behavior PASS; incomplete source-dependent response handling; no financial-source qualification |
| G4A | PARTIAL: approved negative design not fully implemented/tested by supplied harness |
| G4B | **CHANGES_REQUIRED**, assertion failures reproduced |
| G10 | **BLOCKED separately**, no new deployment/site/worker evidence |
| G01–G03 | **NOT_CLOSED** by UI mocks; no backend session acceptance |

NOT_RUN: live ERP/source/permissions/LLM/session/HTTP/image smoke, performance p95/throughput/RSS/SQL, real timeout, delayed unmount failure, real cross-user/site/product switching. Company/contextKey are presentation invalidators only; they do not prove authorization. Lotus Fin remains the product, ERPNext the technology; no topology/SDK decision changed here. No F101/F102 facts/gates reopened or written to competing SSOT.

Rollback must stay within the approved two edits/seven new paths, but restoring the old panel restores fabricated fallback and unsafe HTML. Keep the Copilot entry unavailable if rollback is chosen; no automatic rollback performed. Protect unrelated untracked files and historical evidence.

**Next owner: Chat**, approve one **B1-S correction only** for F01–F08 and test-limit decision, then send a narrow patch request to Antigravity. **Antigravity** corrects approved parser/lifecycle/presentation/test paths; **Work** rechecks hashes/impact and reruns G4B, then **Chat** decides closure. Do not start B0/V1, enable a qualified-request flag, or expand to backend/session/SDK/financial engines to make these UI tests pass.
