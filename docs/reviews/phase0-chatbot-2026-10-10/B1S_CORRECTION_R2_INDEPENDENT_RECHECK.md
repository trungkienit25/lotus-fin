# B1-S Correction Round 2 — Independent G4B recheck

**Verdict: `B1S_G4B_CHANGES_REQUIRED`.** Cả **48/48 gold đã PASS**: 36 case cũ và 12 case Round1, không đổi expected outcome. Các 11 FAIL cụ thể của Round1 đã được sửa. Tuy nhiên, acceptance Round2 còn hai blocker: **harness native không tự cô lập/cleanup đúng** và **recognized FORBIDDEN trong error body bị timeout code lấn át ở hook**. Không kết luận G4B PASS chỉ từ gold hoặc bốn pytest PASS.

Revision mới ngày 2026-10-10; giữ nguyên [Round1](B1S_CORRECTION_R1_INDEPENDENT_RECHECK.md), ledger/packet trước, 123 raw hashes của hai lượt trước và sáu deliverables lịch sử. Review chỉ đọc/chạy kiểm tra UI cô lập/ghi evidence; không sửa application/test, backend/session, commit hoặc dispatch implementation.

## Identity, scope và lineage

`develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, implementation uncommitted. [Current/previous SHA256](../evidence/b1s-g4b-correction-r2-2026-10-10/SOURCE_BEFORE.json) xác định bản được test; HEAD đơn lẻ không đủ.

So với Round1, chỉ ba production file normalizer/hook/Panel và test Python đổi, report append Round2. Renderer, Drawer, ba fixture files, package/lock preserve. 333 protected fingerprints đối chiếu Round1: chỉ Panel đổi; các backend/session/Docker paths trong manifest không đổi. Các untracked files không liên quan được giữ nguyên, không quy cho Antigravity. [Diff theo revision](../evidence/b1s-g4b-correction-r2-2026-10-10/R1_TO_R2_DIFF.patch).

Số dòng toàn file thật: normalizer **149**, hook **169**, renderer **57**, Panel **545**, Drawer **55**, Python test **228**, fixture main **169**. Production mới dưới200; Panel dùng variance đã duyệt; test dưới user-approved cap320. Không xin lại approval ADR. Report ghi 150/170/49/546/229; sai khác +1 ở một số file và renderer49 chưa được sửa. Round2 chưa bổ sung current source hash manifest hoặc đính chính hai preserved hashes sai ở Round1. Đây là lineage/report gap, không lý do sửa renderer/Drawer.

GitNexus exact cached CLI hash được xác minh, context hook bounded10s trả notfound; graph ở commit `316c5bd…`, indexed 2026-10-02, chậm HEAD61 commits. UNKNOWN/stale không là all-clear. Static fallback đúng scope được dùng; không acquire/refresh dependency, không tuyên bố symbol dead. Review không edit source nên không cấp impact/change PASS; người sửa sau phải tuân AGENTS trước edit.

## Actual execution

Private copy `%TEMP%/lotus-b1s-g4b-…`, 11 copied source/package/lock hashes khớp. Dependencies hiện có được copy, không install/download. Node22.19.0/npm11.7.0, Python3.13.7/pytest9.0.2/Playwright1.58.0/Chromium1208. [Fingerprints](../evidence/b1s-g4b-correction-r2-2026-10-10/ENVIRONMENT.json), [nine build artifact hashes](../evidence/b1s-g4b-correction-r2-2026-10-10/BUILD_ARTIFACT_MANIFEST.json).

| Kiểm tra | Actual |
|---|---|
| Typecheck `node node_modules/typescript/bin/tsc -b --pretty false` | PASS / exit0 |
| `node node_modules/vite/bin/vite.js build` sau typecheck | PASS / exit0; hai bước của build script |
| Targeted Oxlint, năm file production | Exit0, **5 warning**, không blanket clean-code PASS |
| Current bốn tests, reviewed server/browser/network setup | **4 PASS**, pytest exit0 |
| Ba original golden tests, source từng byte khớp SHA256 cũ | **3 PASS**, pytest exit0; assertions không sửa |
| Previous independent gold | **48 PASS / 0 FAIL** |
| Một probe bổ sung cho precedence F05 được Round2 yêu cầu | **FAIL**, body FORBIDDEN + ETIMEDOUT → TIMEOUT |
| Current bốn tests, **native server fixture không override** | **4 PASS**, pytest exit0, nhưng native acceptance experiment exit1 |
| Native pre-existing listener refusal | **PASS**, trước spawn; sentinel reviewer giữ nguyên |
| Native undeclared API policy | **FAIL**, undeclared local request nhận `{}`/200, pytest vẫn green |
| Native teardown | **FAIL**, Node con vẫn LISTENING5188 sau pytest |

49 independent DOM cases =48 PASS/1 FAIL; native policy/lifecycle probes và các pytest suites tính riêng, có coverage trùng. [Ledger](B1S_CORRECTION_R2_TEST_RESULTS.json), [DOM raw](../evidence/b1s-g4b-correction-r2-2026-10-10/DOM_RESULTS.json), [native raw](../evidence/b1s-g4b-correction-r2-2026-10-10/NATIVE_RESULTS.json), [original JUnit](../evidence/b1s-g4b-correction-r2-2026-10-10/ORIGINAL_GOLD_JUNIT.xml).

Oracle late-unmount failure đã dùng đúng `userFacingText`, theo erratum Round1; PASS, không có oracle failure mới. Native probes không sửa assertions của test: ghi lại launch PID/listener, chạy request synthetic local vào handler hiện hữu, quan sát teardown. Browser binary/outbound containment vẫn do reviewer cung cấp để chạy an toàn; không biến containment đó thành PASS của native module. Chỉ private static/API origin ở5188 được dùng; không ERP/LLM/shared frontend, service workers bị chặn và WebSockets không nối upstream.

## Findings cần đóng

### R2-F05 — MEDIUM: hook chỉ ưu tiên HTTP denial, bỏ sót business denial trước timeout

`useCopilotRequest.ts:119–154`: catch đọc body/header, nhưng chỉ return trước timeout nếu HTTP401/403. Khi error mang `code:ETIMEDOUT`, `response.status:500`, `response.data.message.status:FORBIDDEN`, hook trả TIMEOUT trước khi normalizer đọc denial. Case **`R2_BODY_DENIAL_TIMEOUT` FAIL**. Normalizer gọi trực tiếp cùng body/status đã xử lý FORBIDDEN đúng; lỗi nằm trong catch precedence, không cần viết lại parser.

Round2 §5 yêu cầu disposed/stale/cancel → discard; **HTTP401/403 hoặc recognized denial** → FORBIDDEN; sau đó mới timeout. Đây là kiểm tra nhánh còn thiếu của contract đã duyệt, không đổi gold hoặc mở kiến trúc. Không có marker/raw financial output lọt ở case này và production POST vẫn khóa.

Minimal acceptance: inspect recognized supported body denial trước timeout code, reuse normalizer đã có, giữ CID/safe text. Bổ sung case này vào suite; giữ48gold, sáu race và unmount success/failure. Không thêm financial context/ERP/session dependency.

### R2-F07 — MEDIUM: native harness thực tế fail dù bốn tests green

`test_copilot_failclosed.py:16–55,65–70,145–150`:

1. `.cmd` launcher PID**24756** có Node child PID**15224**. Reviewer ghi listener5188 thuộc child khi test chạy. Native teardown chỉ terminate launcher; sau pytest, Node15224 vẫn sống và LISTENING5188. **`NATIVE_PROCESS_CLEANUP` FAIL**. Reviewer xác minh command line chứa đúng private root rồi stop riêng PID15224; sau đó no owned node/no listener. Không kill node chung hoặc shared server.
2. Unqualified-callers test vẫn có generic `route.fulfill(...body="{}")`. Probe `/api/method/reviewer_undeclared_probe` được chính handler trả **200/`{}`**, không làm pytest fail. **`NATIVE_UNDECLARED_API_DENY` FAIL**. Report nói đã loại broad fallback là chưa đúng toàn module. Một số handler khác abort unknown nhưng không ghi/raise/assert unexpected traffic; abort đơn lẻ chưa chứng minh unknown request làm test FAIL.
3. Native module không block service worker/WebSocket hoặc outbound chung; reviewer đã cung cấp containment. Preflight occupied-port refusal có thực thi PASS, nhưng native startup không xác minh launcher exit/listener PID; teardown không kiểm tra port release. Không suy diễn network/process acceptance từ wrapper.
4. Widgets false và exact benign SAFE_REPLY assertions đã restore. Tuy nhiên, wait vẫn dựa vào status text cũ, thiếu response/generation synchronization; Reports-disabled assertion Round1 bị bỏ khỏi scope test. Native suite chưa thực thi pending races/unmount/timeout distinctions hoặc actual Page. Independent reviewer có test các đường này, không chuyển coverage đó thành coverage native.

Minimal acceptance: direct owned Node startup hoặc tracked owned child lifecycle; strict5188, refuse foreign listener, verify exact owner, finally stop riêng PID và assert release. Central explicit fixture registry/deny-all + fail unexpected traffic, SW/WS containment rõ ràng. Restore Reports assertion; response/generation waits, actual Page/Drawer và pending lifecycle/timeout tests. Giữ test cap320, dùng existing fixture files nếu cần; không thêm dependency/framework. Nếu cần thay đổi scope thì báo SCOPE_CHANGE_REQUIRED thay vì nới im lặng.

### Report và bounded-input limitations

Builder report cần current HEAD/hash manifest, exact changed paths, actual commands/exits và phân biệt 48gold với native acceptance. Đính chính preserved hashes/line counts bằng annotation mới, giữ lịch sử. Không tiếp tục claim “đóng toàn diện F07”.

F01 tám known regressions đã PASS: unsupported typed statuses, denial precedence, terminal conflicts. Traversal chỉ ba known envelopes, không recursion/collection walk; source chưa có explicit string/payload size cap. **Payload-size qualification NOT_RUN**; không tự đặt ngưỡng acceptance từ một request và không tuyên bố parsing budgets đã được qualify. F06 hero/pill shortcuts có native disabled, tooltip unavailable, bỏ onClick; loading GL claim thay bằng neutral processing. Reports/unqualified provenance vẫn PASS. F02/F03/F04/F08 và rendering/CID/Drawer gold preserve.

## Gates và next owner

| Gate | Current |
|---|---|
| G1 | PASS narrow source/environment/caller identity; không deployed identity |
| G2 | FAIL: body-denial vs timeout precedence còn sai |
| G3 | PARTIAL: production0POST/no verified widget PASS; financial source qualification NOT_RUN |
| G4A | **FAIL**: native isolation/cleanup acceptance đã chạy và fail |
| G4B | **CHANGES_REQUIRED** |
| G10 | **BLOCKED riêng**, không deployment/site/image/worker evidence mới |
| G01–G03 | NOT_CLOSED bởi UI mocks |

Source12hash và tracked dirty diff unchanged trong review. Browser/server riêng đóng; orphan native child đã dọn chính xác; private copy được remove sau root/junction/PID/port validation. [Cleanup](../evidence/b1s-g4b-correction-r2-2026-10-10/WORKSPACE_CLEANUP.json), [final validation](../evidence/b1s-g4b-correction-r2-2026-10-10/FINAL_VALIDATION.json).

NOT_RUN: live ERP/LLM/financial truth, backend permission/session/cross-user/site/product, image/HTTP deployment, p95/throughput/RSS/SQL và real timeout-after-commit. Docker không dùng; không claim connectivity/image acceptance. Lotus Fin vẫn là sản phẩm riêng, ERPNext là integration technology; không mở SDK/topology/B0/V1/F101/F102 trong lượt này. UI safety green không chứng minh chatbot thao tác tài chính qualified cho FinTechathon Shenzhen.

**Next owner: Chat**, dùng [packet hẹp](B1S_CORRECTION_R2_WORK_TO_CHAT.md) quyết định phần correction còn lại; Antigravity sửa tối thiểu nếu được dispatch, Work reverify. Reviewer không tự dispatch/freeze/rollback hoặc triển khai.
