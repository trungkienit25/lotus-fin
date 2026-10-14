# B1-S Correction Round 4 — Independent F07 recheck

**Verdict: `B1S_G4B_CHANGES_REQUIRED` / `B1S_R4_PARTIAL`.** Bốn lỗi cụ thể từ Round3 đã PASS tại probe tương ứng: API alias, foreign outbound, foreign WS và cleanup khi readiness exception. **52/52 independent application cases vẫn PASS**, F05 CLOSED. Tuy nhiên, “definitive F07” chưa đạt: eight additional failing scenarios chứng minh bốn root causes còn thiếu trong registry, readiness ownership, teardown ledger và case synchronization.

Revision bắt đầu 2026-10-10, chốt 2026-10-11 (Asia/Saigon), nối tiếp [Round3](B1S_CORRECTION_R3_INDEPENDENT_RECHECK.md), không đổi lịch sử/verdict trước. One agent, targeted read-only application/test audit + private E2E; không broad audit, app fix, commit, dispatch, deploy hoặc external business call.

## Working tree, scope và fingerprints

`develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, uncommitted implementation. [Current manifest](../evidence/b1s-g4b-correction-r4-2026-10-10/SOURCE_BEFORE.json) xác định artifact; HEAD đơn lẻ không đủ. So Round3 chỉ Python test và builder report đổi; production/fixture/package/lock fingerprints preserve. [Diff](../evidence/b1s-g4b-correction-r4-2026-10-10/R3_TO_R4_DIFF.patch).

Test SHA256 `513CD72533FAD2534547344579A0A6694489BBBCD6FE4D3C39B22729718E017C`,300 full-file lines, trong user-approved cap320. Report416lines, SHA256 `F6D0845E43F546FFE9460F3F2D578D7D52341D8B5DBD2956A3B002F39FA60015`. Hook173, normalizer149, renderer57, Panel545, Drawer55 và fixture169/29/12 giữ nguyên. Production mới dưới200; Panel variance không đổi; reviewer không xin lại ADR approval.

333 protected fingerprints,286 historical raw hashes và12 historical deliverables giữ nguyên. Source snapshots, status/dirty diff và final comparison nằm trong current evidence; unrelated work được preserve. GitNexus bounded contexts `copilot_server`, `install_network_guard`, `vite_fixture_server` dùng exact cached CLI trả notfound; index `316c5bd…` từ2026-10-02,61 commits behind. UNKNOWN/stale chưa resolved. Dùng scope-authorized static fallback, không refresh/acquire/declare dead; không source edit hoặc commit nên không cấp graph-impact/change PASS. Fixer sau phải tuân AGENTS trước edit.

## Actual verification

Fresh unique private TEMP copy;11 copied source/package/lock hashes khớp; existing dependencies copied, không install. Actual production imports chạy trong Chromium1208; Python3.13.7, pytest9.0.2/Playwright1.58.0, Node22.19.0. [Environment](../evidence/b1s-g4b-correction-r4-2026-10-10/ENVIRONMENT.json). Native server fixture không override trong native qualification; reviewer bổ sung browser binary, offline containment, PID/listener observation và controlled fault injection. Source không patch.

| Check | Actual current Round4 |
|---|---|
| Ordinary native suite | 4 PASS, pytest0; exact owned PID22680=listener; cleanup PASS |
| Current suite + reviewed lifecycle wrapper | 4 PASS, pytest0; coverage overlap |
| Independent actual DOM/hook application gold | 52 PASS/0 FAIL; nguyên48 gold +four F05 cases |
| Exact safe-message assertions trên captured records | 32 PASS; không thêm case/request |
| Original matching native qualification | 17 records PASS, gồm Q1–Q6 ownership/cleanup observations |
| Extended native unique records, tổng gồm original | 31 PASS/8 FAIL/0 BLOCKED |
| Typecheck/build/lint | NOT_RUN Round4: test-only edit, config/production/lock unchanged; Round3 PASS/5lintwarnings là historical |

[Ledger](B1S_CORRECTION_R4_TEST_RESULTS.json), [DOM](../evidence/b1s-g4b-correction-r4-2026-10-10/DOM_RESULTS.json), [process commands/exit/deadlines](../evidence/b1s-g4b-correction-r4-2026-10-10/REVIEW_PROCESS_RESULTS.json). Raw LOCAL_WS có hai assertions về cùng probe; ledger loại một duplicate khỏi unique count, giữ nguyên raw. Không cộng overlapping pytest suites/messages/probes vào52 application cases. Original3 byte-exact suite không rerunRound4; historical PASS giữ riêng.

Actual Page/router/Company A→B, Drawer0POST, pending scope/reset/loading/unmount races, CID/XSS và actual ETIMEDOUT500/body FORBIDDEN đều giữ PASS. Synthetic responses không tạo ERP authority. Foreign/API negative pytest1 là qualification PASS khi abort/event assertion đúng lý do; reviewer runner0. ALIAS/OUTBOUND/WS/API JUnit có explicit native `Unexpected network traffic detected`. SW block có ở bốn native page contexts; actual negative SW attempt NOT_RUN.

## Four remaining F07 findings — priority MEDIUM, test infrastructure

**R4-F07-A — registry chỉ exact origin/path, chưa exact request contract hoặc bounded assets/WS.** [Test source lines88–114](../../../tests_e2e/test_copilot_failclosed.py#L88): method/query không validate; local path không bắt đầu `/api/` tự continue; WS prefix excused mọi path local.

| Safe local/offline probe | Native actual |
|---|---|
| GET exact Copilot path, fixture intended POST |200 empty mock, pytest0 |
| Company GET + `reviewer_undeclared=1` |200 Company fixture, pytest0 |
| `/%61pi/method/reviewer_undeclared_probe` |200 fixture HTML từ Vite fallback, pytest0 |
| `/reviewer-undeclared-static-probe` |200 fixture HTML, pytest0 |
| `ws://127.0.0.1:5188/reviewer_undeclared_ws` |No upstream; no unexpected failure, pytest0 |

Five scenarios expected deny +pytest1, đều FAIL qualification. [METHOD](../evidence/b1s-g4b-correction-r4-2026-10-10/METHOD_RESULTS.json), [QUERY](../evidence/b1s-g4b-correction-r4-2026-10-10/QUERY_RESULTS.json), [ENCODED](../evidence/b1s-g4b-correction-r4-2026-10-10/ENCODED_RESULTS.json), [ASSET](../evidence/b1s-g4b-correction-r4-2026-10-10/ASSET_RESULTS.json), [LOCAL_WS](../evidence/b1s-g4b-correction-r4-2026-10-10/LOCAL_WS_RESULTS.json). No ERP path reached. Installed Playwright primary source confirms routed WS defaults to no upstream connection; không gọi `connect_to_server`, nên foreign WS blocking hiện tốt. Local WS issue là missing ledger enforcement, không upstream leak. Fixture hmr:false giữ nguyên nhưng Vite client vẫn attempts local WS; cần narrowly documented exact HMR exception hoặc loại attempt, không localhost-prefix allowlist. Full URL được log chưa sanitized, static gap theo Round4.

**R4-F07-B — socket readiness chưa chứng minh expected owned HTTP server.** Lines59–70 chỉ proc.poll + socket-connect, không HTTP response hoặc listener PID verification. Controlled sentinel bind sau actual Vite spawn/preflight: fixture **yield**, listenerPID23932 thuộc reviewer sentinel trong khi owned NodePID11308 vẫn running. [READINESS_RACE](../evidence/b1s-g4b-correction-r4-2026-10-10/READINESS_RACE_RESULTS.json). Đây là local race injection, không shared listener. Reviewer release đúng sentinel; owned Node exit1, final listener0. Q5 pre-existing listener refusal vẫn PASS; preflight không thay thế post-spawn ownership check.

**R4-F07-C — ledger được assert trước teardown, không có shared guaranteed final assertion.** Lines150–152 và228–229 assert rồi browser.close. Controlled request lúc native browser close bị native abort và ledger ghi HTTP event, nhưng **pytest0**. [LATE](../evidence/b1s-g4b-correction-r4-2026-10-10/LATE_RESULTS.json). Source callback/expected assertions nguyên vẹn; reviewer observation/probe after final assertion. Guard phải sống tới settled context close, rồi assert trong exception-safe finalizer; pending/setup/teardown events không được bỏ lọt.

**R4-F07-D — IDLE chưa bind current generation/result.** Lines209–217 chỉ click rồi waitIDLE. Controlled omission của send thứ22 (`R1_HTTP_504_DENIAL`, trước đó cũng FORBIDDEN):26 attempted clicks/25 actual synthetic requests, **pytest0**, đọc previous result. [SYNC](../evidence/b1s-g4b-correction-r4-2026-10-10/SYNC_RESULTS.json). Đây là test-harness fault injection, không app bug hoặc sửa expected. Cần response/request counter/generation-specific result hoặc clear result trước case; completed current request và exact message phải được chứng minh. Native chưa assert fixed error texts; independent32 exact checks có PASS.

## Report accuracy, gates và next batch

Builder current hash/line manifest khớp. Report references `python tests_e2e/run_q_probes.py`, nhưng file không còn trong current tree; report không link retained Q raw PID/exit evidence. [Claim check](../evidence/b1s-g4b-correction-r4-2026-10-10/BUILDER_CLAIM_CHECK.json). Không suy ra builder chưa chạy; command đó hiện không reproducible. Independent current original probes thực sự PASS, nhưng không đủ chứng nhận “strict registry/comprehensive/shared assertion/current-case sync”. Append factual correction ở vòng sau; không sửa historical claims thành current PASS.

| Gate | Current scope |
|---|---|
| G1/G2 | PASS narrow source identity/tested B1S UI contract |
| G3 | PARTIAL: actual production0POST; financial qualification NOT_RUN |
| G4A/G4B | FAIL / CHANGES_REQUIRED |
| G10 | BLOCKED riêng, unchanged |
| G01–G03 | NOT_CLOSED |

Minimal test-only next batch: strict method/query/path/assets/exact local WS policy; post-spawn HTTP +verified listener ownership; centralized per-test guard owner/finalizer; response/generation-specific synchronization. Preserve52 gold and17 original qualification PASS; tám failing scenarios phải chuyển sang PASS qualification. Không sửa production đã PASS. Nếu không thể sạch trong cap320/approved paths, fixer báo một SCOPE_CHANGE_REQUIRED helper proposal để Chat duyệt trước thêm; không code-golf hoặc tự mở scope. [Work→Chat](B1S_CORRECTION_R4_WORK_TO_CHAT.md); reviewer không dispatch/freeze.

NOT_RUN: real ERP/LLM/financial truth/permissions/session; immutable image/site/worker deployment; financial mutation/timeout-after-commit; payload/SQL/p95/throughput/RSS. Không dùng Docker/shared site/frontend, không business mutation. Lotus Fin riêng ERPNext; SDK/topology/F102 không đổi ở lượt này. FinTechathon Shenzhen automation demo chưa được financial acceptance.

[Reproduction](../evidence/b1s-g4b-correction-r4-2026-10-10/REPRODUCTION.md) lưu exact reviewed programs, expected negative exits và source lineage. Reviewer postprocessor từng đọc nhầm hook record shape; corrected field reading, không thay oracle/rerun. Cleanup guard ban đầu stop trước delete vì Target scalar indexed thành character; normalized absolute junction target rechecked rồi cleanup. [Final cleanup](../evidence/b1s-g4b-correction-r4-2026-10-10/WORKSPACE_CLEANUP.json): private copy removed, owned Node0/port released/Chromium0, không shared kill. [Final validation](../evidence/b1s-g4b-correction-r4-2026-10-10/FINAL_VALIDATION.json), [raw hashes](../evidence/b1s-g4b-correction-r4-2026-10-10/RAW_EVIDENCE_HASHES.json), [deliverable hashes](../evidence/b1s-g4b-correction-r4-2026-10-10/DELIVERABLE_HASHES.json).


---

## Current revalidation — 11/10/2026: independent quality audit Track A

**B1S_G4B_CHANGES_REQUIRED**, không closure/freeze/dispatch. Scope hiện tại là final UI/F07 verification; architecture Track B có [report riêng](CHATBOT_ARCHITECTURE_SCALE_DEBUG_AUDIT.md) và không tự tạo B1 blockers. `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + dirty tree. **12/12 source/report fingerprints khớp Round4 trước khi chạy**; test300lines, SHA256 `513CD72533FAD2534547344579A0A6694489BBBCD6FE4D3C39B22729718E017C`; report416lines, SHA256 `F6D0845E43F546FFE9460F3F2D578D7D52341D8B5DBD2956A3B002F39FA60015`. Không application/test edit, dependency install, live ERP/LLM, Docker/shared Redis, commit/deploy.

### Actual independent execution

Fresh UUID private TEMP workspace; existing dependencies copied,11 file identities matched. Node22.19.0/React19.3.0/Vite8.3.3/TS6.0.3, Python3.13.7/pytest9.0.2/Playwright1.58.0/Chromium1208. Actual production modules imported by fixture. Native qualification dùng server fixture nguyên vẹn, bổ sung độc lập browser executable, network containment, PID/listener observation và controlled fault. DOM gold dùng reviewed lifecycle wrapper, không dùng wrapped PASS để đóng native gate.

| Check thực chạy lại | Actual result |
|---|---|
| Independent application gold | **52/52 PASS**; Page/Drawer0POST, source/status precedence, safe DOM/CID, scope/reset/races/unmount và disabled shortcuts |
| Exact-message assertions | **32/32 PASS**, trên cùng52captured records; không cộng thêm32cases |
| Supplied native assertions | **4/4 PASS**, pytest0; PID observed equals direct owned Node listener |
| Supplied assertions under reviewer DOM wrapper | **4/4 PASS**, pytest0; cùng test bodies, không thành8unique cases |
| Q1 substring API alias | blocked, native ledger assertion, expected pytest1, owner/cleanup PASS |
| Q2 foreign non-API outbound | blocked locally, native event assertion, expected pytest1, cleanup PASS |
| Q3 foreign WS | intercepted without upstream connection, native event assertion, expected pytest1, cleanup PASS |
| Q4 setup/readiness exception | injected fault sau spawn, native finally cleanup PASS |
| Q5 occupied foreign listener | reviewer sentinel refused before spawn, no spawn, sentinel retained until reviewer close: PASS |
| Q6 normal/assertion-failure cleanup | native normal/API-failure runs release owned Node/5188; unrelated process kills0 |
| Original Q1–Q6 qualification records | **17 PASS** (observations/assertions, không17pytest cases) |
| Additional METHOD qualification | owner/cleanup2PASS; undeclared GET check **FAIL** |
| Current native qualification tổng | **20 records:19PASS/1FAIL/0BLOCKED**;5negative pytest invocations:4expectedfail +1incorrectpass |
| Typecheck | `node node_modules/typescript/bin/tsc -b`, exit0 |
| Production build | `node node_modules/vite/bin/vite.js build`, exit0;757.04kB JS /216.81kB gzip; >500kB warning, không latency claim |
| Relevant lint | installed Oxlint on five B1production files, exit0; five warnings, no errors; không gate failure |

Current **smallest demonstrated blocker**: fixture normalization mock accepts **GET** `http://127.0.0.1:5188/api/method/lotus_fin.api.copilot_api.chat_copilot`; response **HTTP200, empty body**, native pytest **exit0**; `Unexpected network traffic detected` absent. Exact-owned PID18472 và cleanup đều PASS. Expected contract: undeclared method must abort, ledger event recorded and enclosing pytest1. [METHOD evidence](../evidence/chatbot-quality-audit-2026-10-11/METHOD_RESULTS.json), [JUnit](../evidence/chatbot-quality-audit-2026-10-11/METHOD_JUNIT.xml). Root cause `install_network_guard` checks origin/API path only, mock accepts path without method/query contract. Không gọi real API.

Các tám failing scenarios/bốn root causes trong phần Round4 phía trên **không được xóa hoặc coi closed**: current fixture byte-identical; source reinspection vẫn có unrestricted local static continuation/localWS-prefix, socket-only readiness, ledger-before-close và non-case-bound IDLE. Lượt này chỉ reexecute METHOD để có smallest current blocker; QUERY/ENCODED/ASSET/LOCAL_WS/READINESS_RACE/LATE/SYNC không rerun, giữ đúng historical run identity. Không blanket inherit unrelated findings. SW block static ở four native page contexts; actual negative SW attempt NOT_RUN. Observed network qualification không chứng minh universal escape-proof khi registry còn fail.

### Gate và next eligible batch

| Gate | Current verdict |
|---|---|
| G2 | **Narrow PASS** cho unchanged B1-S UI safety,52gold |
| G3 | **PARTIAL / outside live verification**; no financial truth/permission closure |
| G4A | **FAIL**: native negative method qualification còn thiếu |
| G4B | **B1S_G4B_CHANGES_REQUIRED** |
| G10 | **Independently BLOCKED/NOT_RUN**: private Vite build không là fresh judge image/site acceptance |

Next eligible batch **B1-S/F07 test-only correction**, existing approved paths/cap320: complete exact HTTP method/path/query/assets/WS declarations; verify post-spawn readiness/listener ownership; central final ledger check after settled close; case-specific synchronization. Keep production52gold and17original qualification; eight previously failing R4scenarios phải qualify correctly. Nếu không thể clean trong allowlist/cap: one concrete helper proposal → Chat scope approval, không tự add/split. Không sửa production, broad audit hoặc mở invoice/ERP implementation trong batch này.

### Evidence và lịch sử

[Current summary](../evidence/chatbot-quality-audit-2026-10-11/RESULT_SUMMARY.json), [executed process ledger](../evidence/chatbot-quality-audit-2026-10-11/CURRENT_PROCESS_RESULTS.json), [exact engineering commands/exits](../evidence/chatbot-quality-audit-2026-10-11/ENGINEERING_RESULTS.json), [private build hashes](../evidence/chatbot-quality-audit-2026-10-11/BUILD_ARTIFACT_HASHES.json), [reproduction](../evidence/chatbot-quality-audit-2026-10-11/REPRODUCTION.md), [cleanup](../evidence/chatbot-quality-audit-2026-10-11/WORKSPACE_CLEANUP.json), [final validation](../evidence/chatbot-quality-audit-2026-10-11/FINAL_VALIDATION.json).

Initial private copy timeout150s completed incrementally and11hashes checked; initial DOM launcher rejected Unicode stdin before execution, corrected UTF8 and ran unchanged gold once. Desk method probes completed/stored UTF8 before parent display encoding error; no product failure inferred from launcher/display issues. Diagnostics stored separately. Native/DOM lifecycle results are before reviewer cleanup; no owned Node/listener left. Private directory removed after resolved path/junction checks; no shared process stopped.

Historical Round4 raw manifest and report text above remain historical. This requested report append deliberately changes current file hash: original SHA256 `B9B85176B5BE7720443F2C00E63AFB1EDB18322A2B231A10BFA3B1BB1238A9CB` preserved in [pre-append snapshot](../evidence/chatbot-quality-audit-2026-10-11/R4_RECHECK_BEFORE_APPEND.md); final check verifies exact original-byte prefix. Old manifest is not rewritten to claim new bytes were old evidence. All other protected/history comparisons and intentional doc append exceptions are explicit in final ledger.
