# B1-S Round 7 — Independent G4B closure review

11/10/2026 · Lotus Fin · FinTechathon Shenzhen 2026.

**Verdict: `B1S_G4B_PASS`. R6-F07-C CLOSED.** Current cache-query rejection, hai exact Round 5 probes, Q1–Q8 và original F07 requirements đã kiểm chứng độc lập. Native **4/4**, application gold **52/52**, hermetic predicates **15/15** PASS. Không còn demonstrated material F07 blocker trong scope này. Đề nghị Chat đóng B1-S theo contract UI safety/test infrastructure; financial/backend/judge gates giữ trạng thái riêng.

## Current artifact và scope

`develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; working tree dirty, staged empty. HEAD không đủ định danh: dùng current per-file SHA256 và verified private copy. Hai tracked Panel/Drawer changes có từ baseline, không đổi trong review. Unrelated untracked files được giữ nguyên; `tests_e2e/_run.txt` đã hiện diện trong Round 6, không quy kết cho Round 7 hoặc thực thi.

|Artifact|Lines|Current SHA256|
|---|---:|---|
|Native test|286 ≤320|`4075D799EC2A1D7F89E3ACCF82671797E2E96ED03E44EC2DD38C4E128D2DCC09`|
|Helper|165 ≤200|`1802FA19BD2127522CC104EA6B377BBC662E61BECF429CA456BC947CB5D1B240`|
|Implementation report|635|`74C777F29641DC7BA1C8471C0170B128B840B3B89D2B0632142E47D742D6419C`|

[13-file manifest](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/SOURCE_BEFORE.json) và [exact Round 6→7 diff](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/R6_TO_R7_DIFF.patch): chỉ helper cache-query branch và report append đổi. Five production files, native test, three fixtures, package/lock unchanged. Native byte-identical với Round 6, 23 assert AST và 26-case vector retained. Report substantive historical prefix retained; trailing whitespace thay ở điểm append nên strict byte-prefix false.

Final rehash: **13 current sources**, **333 protected source/backend/session/dependency fingerprints**, **1,231 historical/builder hash checks** unchanged. Đây là integrity counts, không phải test coverage. Reviewer không sửa production/test/helper/report source, dependency, permissions hoặc shared data; chỉ tạo review deliverables/raw evidence. ADR001 và explicit native/helper caps được giữ; không mở rộng historical Panel variance.

GitNexus graph-first context `is_allowed_static_asset` notfound; query trả các flow không liên quan, index báo behind 61 commits, indexed 02/10/2026 tại `316c5bd…`. UNKNOWN không là all-clear. Bounded static tracing xác nhận `install_network_guard` gọi predicate, four native entrypoints dùng guard; không có source edit/commit hoặc tooling download trong review. [Graph limitation](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/GITNEXUS_IDENTITY.json).

## Exact blocker closure và engineering review

Current helper dùng `parse_qsl(query, keep_blank_values=True)` và kiểm tra **list length=1/key=`v`**, không chuyển sang dict làm mất duplicate. Empty query và blank `v=` giữ behavior; additional/unknown/duplicate keys bị deny. Method/path/extensions và `/@fs/`/WS/process policy không đổi. Một central native request policy; rejection đi vào existing `UNDECLARED_ASSET` ledger/abort. Sửa nhỏ, không thêm dependency, competing guard hoặc filesystem check sai cho virtual cache assets.

Probe lấy **actual current resource URL** từ page entries, không hardcode historical version:

|Control/probe|Actual|Exit/result|
|---|---|---|
|`/.vite/deps/react.js?v=22edaa89`|HTTP 200, `text/javascript`|Positive PASS|
|Cùng URL thêm `&reviewer_undeclared=1`|Fetch aborted; native ledger `UNDECLARED_ASSET`; final assertion sau browser close|pytest **1**, reviewer **0**; qualification PASS|

Listener **18740** bằng direct owned Vite PID, command line trỏ private root. Native cleanup Nodes/listeners empty trước reviewer fallback; fallback kills 0. Failure là native expected assertion, không phải containment/bootstrap/stale-result error. [Probe/ownership](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/CACHE_ASSET_RESULTS.json), [actual native assertion](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/CACHE_ASSET_JUNIT.xml).

[15/15 hermetic checks](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/HERMETIC_PREDICATES.json): empty/sole/blank `v`, `.js`/`.map`, unknown and blank unknown keys, duplicate/blank duplicate, empty key, valueless extra key, disallowed method/extensions. Predicate-only evidence tách khỏi HTTP qualification/gold. Không mở speculative probes hoặc refactor sau khi demonstrated invariants qualify.

## Frozen negative qualifications

|Qualification|Current actual failure reason|Result|
|---|---|---|
|Q1 METHOD|GET exact Copilot endpoint → METHOD_QUERY, abort, pytest1|PASS|
|Q2 QUERY|Company undeclared query → METHOD_QUERY, abort, pytest1|PASS|
|Q3 ENCODED|Encoded API alias → UNDECLARED_API, abort, no HTML success, pytest1|PASS|
|Q4 ASSET|Unknown local asset → UNDECLARED_ASSET, abort, pytest1|PASS|
|Q5 LOCAL_WS|Unknown localhost WS → WS ledger, no upstream, pytest1|PASS|
|Q6 READINESS|Post-spawn sentinel listener PID mismatch; owned process exits; sentinel retained to reviewer cleanup, pytest1|PASS|
|Q7 LATE|Unexpected request during browser close captured; final ledger assertion fails, pytest1|PASS|
|Q8 SYNC|Suppress case22 request; prior FORBIDDEN/IDLE retained,21 requests; current response timeout, pytest1|PASS|

Hai exact Round 5 probes cũng PASS: outside-root `/@fs/E:/lotus-fin/reviewer-undeclared-static-probe.js` aborted/UNDECLARED_ASSET; `ws://127.0.0.1:5188/?token=reviewer-forged-token` recorded WS; enclosing pytest1 với intended native failure. R5-F07-A/B vẫn CLOSED.

Original eight requirements PASS: API alias, foreign HTTP, foreign WS, pre-existing foreign listener refusal, normal teardown, assertion-failure teardown, setup/readiness-error teardown và exact owned PID/listener identity. Direct-fixture SETUP/PREFLIGHT ghi RuntimeError thực tế, không invent pytest exit. Q6 secondary occupied-port cleanup exception vẫn giữ original wrong-PID reason trong chain; foreign sentinel không bị native harness terminate.

## Current application và positive regressions

**Native4/4 PASS, pytest0. Application gold52/52 PASS; exact-message32/32 match immutable historical oracle**, overlapping observations không cộng thành unique coverage. DOM supplied-suite aggregate lặp four native assertions, không tính thành eight native cases. F05 vẫn CLOSED.

Coverage hiện tại gồm root/nested FORBIDDEN precedence, Axios timeout distinctions, safe normalization/provenance, XSS text rendering, CID validation/redaction, Page/Drawer zero Copilot POST, company/context reset, delayed success/failure, unmount cancellation và disabled finance shortcuts. Synthetic qualified hook cases không chứng minh backend authorization hoặc financial truth.

Legitimate boot:92 HTTP200 static responses/23 unique URLs; four WS callbacks match owned bootstrap token. `/@vite/client` HTTP200 listener **16836** đúng native-owned PID. Token values redacted/hash retained; WS upstream intentionally absent in contained tests, không claim actual hot-reload acceptance. Current installed Vite/Playwright primary source re-read/hash verified. [Bootstrap controls](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/NORMAL_BOOTSTRAP_IDENTITY.json).

Typecheck/build/targeted lint **exit0**. Five existing lint warnings,757.04kB JS chunk, config-loader/build timing warnings ghi riêng; không phải failed assertion hay gate blocker. Build durations không là p95/throughput/RSS acceptance.

## Independent runtime, containment và cleanup

Fresh private TEMP `b1s-r7-review-ym0ysftx`, không chứa product-name substring;12 source/package/test/fixture copy hashes matched. Dependencies copied từ existing install, private root junction chỉ vào own frontend/node_modules. Python3.13.7, pytest9.0.2, Playwright1.58.0/Chromium1208, Node22.19.0, Vite8.3.3, React19.3.0, TypeScript6.0.3. Private installed versions, executables và primary-source hashes retained.

**19 independent executions** dùng reviewer containment trước native import: exact local HTTP continuation clamp, Python HTTP origin clamp, deny all WS upstream. All19 containment ledgers fallback attempts0; native policy tạo intended failures. No ERP/LLM/provider/public/shared8080/Docker/Redis/site interaction. Service Workers blocked trong mọi supplied context; independent SW-install probe NOT_RUN.

Per-run owned PID/command line/listener and cleanup proof ở [process summary](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/PROCESS_AND_CLEANUP_SUMMARY.json). Owned resources empty trước fallback, fallback Node kills0. Final inventory: owned Nodes/Playwright driver/cached Chromium/listeners0; verified TEMP and internal junction removed. Không unrelated process termination. [Final cleanup](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/WORKSPACE_CLEANUP.json).

Reviewer preparation incident: copy started before private-root snapshot completed, produced extra `E:\frontend`; exact owned Robocopy stopped. Automatic review refused outside-TEMP deletion; user explicitly authorized exact path, extra copy removed. First private-cleanup guard later refused scalar Target indexing; normalization corrected before verified deletion. Các incidents nằm ngoài native acceptance runs, không sửa nguồn/ledger/oracle; factual diagnostics retained, không tính vào test counts. [Preparation diagnostic](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/COPY_PREPARATION_DIAGNOSTIC.json).

Builder evidence có lineage gaps: Round7 SOURCE_BEFORE helper vẫn ghi Round6 SHA `39FDB…`/160lines; WORKSPACE_CLEANUP tham chiếu Round6 TEMP. Builder private root hiện không còn, nhưng copied artifact không chứng minh cleanup của lượt builder. Không inherit builder PASS hoặc sửa history; verdict này dùng current independent manifest/execution/cleanup. Đây là reporting gaps, không remaining demonstrated F07 defect sau independent closure. [Lineage notes](E:/lotus-fin/docs/reviews/evidence/b1s-g4b-correction-r7-independent-2026-10-11/BUILDER_EVIDENCE_LINEAGE_NOTES.json).

Reproduction: rebuild fresh private copy với matching source/dependencies, verify hashes/internal junction, cập nhật OWNED_WORKSPACE; TEMP hiện đã xóa. Run saved CACHE/CONTAINED/ENGINEERING_EXECUTION_REPRODUCTION text qua UTF-8 Python stdin; exact subprocess args, deadlines, exits, JUnit/stdout/stderr và containment logs retained. Native source/oracle unchanged; reviewer injects faults in memory, separate gold owns its fixture lifecycle. Không execute old TEMP paths hoặc app/business scripts.

## Gate matrix và closure recommendation

|Gate|Current decision|
|---|---|
|G1|PASS — current dirty artifact, private copy/environment, scope/integrity|
|G2|PASS — existing synthetic UI safety contract|
|G3|Current financial context unqualified; live acceptance NOT_RUN/outside scope|
|G4A|PASS — exact cache closure +frozen negative/lifecycle set|
|G4B|**B1S_G4B_PASS**|
|G10|BLOCKED independently; judge deployment/site/HTTP acceptance NOT_RUN|
|G01–G03|NOT_CLOSED; backend/session acceptance NOT_RUN|

Actual limits: current Windows/one-fixture-per-review-process lifecycle only; token cache lifecycle across future server restarts, non-Windows netstat, universal symlink/SW/async/performance sweeps NOT_RUN. Docker/ERP image lineage NOT_USED/NOT_VERIFIED. Những giới hạn này không là demonstrated blocker của frozen B1-S contract.

**Chat có đủ evidence đóng B1-S trong scope đã duyệt.** Không cần mở thêm harness refactor. Next product milestone phải scoped riêng: outcome/CID +server-owned authorized read contract, sau đó invoice search/select/open. Lotus Fin/ERPNext product boundary giữ riêng; không bật unqualified financial automation. Không freeze/dispatch/commit/deploy trong lượt review này.

[Machine ledger](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R7_TEST_RESULTS.json) · [Work→Chat](E:/lotus-fin/docs/reviews/phase0-chatbot-2026-10-10/B1S_CORRECTION_R7_WORK_TO_CHAT.md).
