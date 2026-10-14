# B1-S Correction Round 1 — Independent G4B recheck

**Verdict: `B1S_G4B_CHANGES_REQUIRED`.** Antigravity đã sửa được cả **16 case từng FAIL**; **20 case trước đó PASS vẫn PASS**. Tuy nhiên, 12 case bổ sung trong đúng contract correction còn **11 FAIL / 1 PASS**. Không đóng G4B dựa trên 4 bài pytest PASS. G10 vẫn BLOCKED riêng; chưa có acceptance backend/session/deployment.

Đây là revision kiểm tra mới trong chuỗi audit hiện hữu, ngày 2026-10-10. [Review trước](B1S_INDEPENDENT_G4B_VERIFICATION.md), [ledger trước](B1S_G4B_TEST_RESULTS.json), packet trước và 60 raw evidence cũ được giữ nguyên; không đổi verdict lịch sử thành kết quả hiện tại. Scope chỉ đọc nguồn, chạy kiểm tra cô lập và ghi bằng chứng. Không sửa application/test, commit, dispatch hoặc implementation.

## Source identity và phạm vi

`develop`, HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`; implementation vẫn uncommitted. HEAD không đủ xác định bản sửa. [Fingerprint trước review](../evidence/b1s-g4b-correction-r1-2026-10-10/SOURCE_BEFORE.json) chứa current SHA256, SHA256 từ G4B trước và số dòng thực tế.

So với G4B trước, 5 file nguồn/test đổi: normalizer, hook, Panel, test Python và fixture main. Renderer, Drawer, fixture HTML/config, package và lock không đổi. Builder report được append correction, vẫn giữ lịch sử. So với baseline Round3, 331/333 protected hashes khớp; 2 khác biệt là Panel/Drawer đã được phép từ implementation đầu. Không quy mọi untracked file trong workspace cho correction. [Protected comparison](../evidence/b1s-g4b-correction-r1-2026-10-10/PROTECTED_COMPARISON.json).

Số dòng thật: normalizer **126**, hook **160**, renderer **57**, Panel **540**, Drawer **55**, Python test **211**, fixture main **169**. Các production file mới dưới 200; Panel dùng variance đã duyệt; test dưới exception **320** được user cho phép ở correction này. Không cần xin lại variance. Builder report ghi 104/137/49/496/56/177, không phải số dòng toàn file hiện tại. Hash normalizer/hook/Panel/test khớp report, nhưng hash renderer/Drawer report không khớp source được preserve; cần sửa lineage báo cáo, không sửa hai file đó.

GitNexus graph-first được thử bằng CLI cache đã xác minh SHA256, bounded 10s; `context useCopilotRequest` trả not found. Index ở commit `316c5bd…`, ngày 2026-10-02, chậm HEAD 61 commits. Đây là limitation/UNKNOWN, không phải symbol dead hoặc low risk. Dùng fallback đọc source/caller đã cho phép trong correction; không refresh/acquire package. Không có application edit nên không có symbol impact/change gate được tuyên bố PASS. Người sửa tiếp phải chạy bounded impact và xác nhận caller theo AGENTS trước edit.

## Actual verification

Dependencies đã có được copy vào workspace `%TEMP%/lotus-b1s-g4b-…` riêng; 11 hash source/package/lock copy khớp nguồn. Không cài/download dependency. Node22.19.0/npm11.7.0, Python3.13.7, pytest9.0.2, Playwright1.58.0, Chromium1208. [Tool fingerprints](../evidence/b1s-g4b-correction-r1-2026-10-10/ENVIRONMENT.json).

| Kiểm tra đã chạy | Kết quả thực tế |
|---|---|
| `node node_modules/typescript/bin/tsc -b --pretty false` | PASS, exit0 |
| `node node_modules/vite/bin/vite.js build` sau typecheck | PASS, exit0; hai bước của build script, không npm install |
| Oxlint trên 5 file production liên quan | Exit0; warning còn, không clean-code PASS toàn bộ |
| 4 bài test hiện tại, assertion không đổi | 4 PASS; wrapper reviewer thay server/browser/network setup |
| 3 bài test gốc, phục dựng khớp SHA256 từng byte từ evidence cũ | 3 PASS; assertion gốc không đổi, cùng wrapper cô lập |
| 36 case độc lập G4B trước, giữ gold | **36 PASS**: 16 FAIL→PASS, 20 PASS→PASS |
| 12 case bổ sung bounded theo contract correction | **1 PASS / 11 FAIL** |

48 case DOM độc lập: **37 PASS / 11 FAIL / 0 BLOCKED**. Hai pytest suite có coverage trùng và được tính riêng. [Ledger chính thức của lượt recheck](B1S_CORRECTION_R1_TEST_RESULTS.json), [raw DOM](../evidence/b1s-g4b-correction-r1-2026-10-10/DOM_RESULTS.json), [follow-up DOM](../evidence/b1s-g4b-correction-r1-2026-10-10/FOLLOWUP_RESULTS.json), [gold JUnit](../evidence/b1s-g4b-correction-r1-2026-10-10/ORIGINAL_GOLD_JUNIT.xml).

Lỗi oracle reviewer ở case late-unmount failure ban đầu đọc `result.text` thay vì `userFacingText`: raw completion thực tế đã được fence và rỗng. Đã sửa oracle, chạy lại riêng case này và xác nhận **PASS**; raw lượt đầu giữ nguyên. Ledger đánh dấu kết quả đầu superseded, không tính đó là product FAIL. Reproduction đã chạy và reproduction follow-up đều được lưu; không có script ERP/business ad-hoc.

Browser chỉ vào Vite riêng ở 127.0.0.1:5188, production source được import thật; Page dùng router/i18n thật, Company A/B là synthetic. API cần thiết có fixture, outbound khác bị chặn; service worker bị block, WebSocket không nối upstream. Không có unexpected network. Các test module vẫn có broad API fallback nội bộ, nên wrapper không chứng minh F07 của chính module đã đóng. Mọi server reviewer-owned đã kết thúc và 5188 free; private copy được dọn theo resolved root/junction đã kiểm tra. Không kill shared process. [Cleanup](../evidence/b1s-g4b-correction-r1-2026-10-10/WORKSPACE_CLEANUP.json).

## Findings còn mở

### R1-F01 — HIGH: type guard và status precedence chưa đủ

`copilotPresentation.ts:56–59,73–79,94–114`:

- `status: true`, object hoặc array bị `extractStatus` bỏ qua như không có status. Có reply thì thành **OK**, `SENSITIVE_MARKER` xuất hiện trong DOM. Ba case `R1_BOOLEAN_STATUS`, `R1_OBJECT_STATUS`, `R1_ARRAY_STATUS` FAIL. Đây là thiếu fail-closed với unsupported input, không phải XSS thực thi; production request hiện vẫn bị khóa.
- Root FORBIDDEN + nested UNRECOGNIZED ra NOT_AVAILABLE vì unknown check chạy trước denial. HTTP500/504 + body FORBIDDEN ra SOURCE_ERROR/TIMEOUT vì transport return chạy trước body denial. Ba case `R1_DENIAL_UNKNOWN`, `R1_HTTP_500_DENIAL`, `R1_HTTP_504_DENIAL` FAIL. Contract yêu cầu recognized FORBIDDEN ưu tiên tuyệt đối.
- SOURCE_ERROR + NOT_AVAILABLE và TIMEOUT + NOT_AVAILABLE không được coi là contradictory terminal failures. Hai case conflict FAIL; chỉ cặp SOURCE_ERROR+TIMEOUT hiện được reconcile đúng.
- Traversal hiện cố định root/message/tool_output, không recursive; chưa có size bounds rõ ràng cho unknown status/reply. Đây là static gap, chưa chạy acceptance tải payload lớn và không tự đặt acceptance size mới.

Acceptance: giữ các case cũ; explicit typed guards phân biệt absent với unsupported; reconcile bounded supported fields; denial trước các nhánh khác; mọi conflicting non-auth terminal failure → NOT_AVAILABLE; fixed safe text, widgets false, marker không lọt. Không cho response tự cấp source trust.

### R1-F05 — MEDIUM: timeout heuristic che mất denial

`useCopilotRequest.ts:119–146`: `ECONNABORTED` cũ đã PASS, nhưng `ETIMEDOUT` thành SOURCE_ERROR. Installed Axios1.20.0 XHR/HTTP adapters dùng ETIMEDOUT khi `clarifyTimeoutError` bật; mặc định hiện false, nên đây là compatibility gap thực, không khẳng định default request đã gặp nó. HTTP403 Axios error có diagnostic chứa từ `timeout` lại thành TIMEOUT trước khi xét permission. `R1_ETIMEDOUT`, `R1_DENIAL_TIMEOUT_WORD` FAIL. Raw error không lọt UI.

Acceptance: ưu tiên 401/403/recognized denial, dùng known timeout signals thay vì substring diagnostic; phân biệt cancel/stale/outage. Không cần backend/session sửa hoặc chờ timeout thật 15s.

### R1-F06 — MEDIUM: financial quick actions chưa được gate ở UI

`VercelChatPanel.tsx:291,429–449`: cả bốn quick button vẫn enabled, không có title/text unavailable: Financial Health, Cash Forecast 30D, Risk Signals, What-If Studio. DOM case `R1_QUICK_ACTIONS_GATE` FAIL. Reports đã disabled; welcome GL claim đã bỏ. Hook vẫn chặn production POST nên chưa có live financial operation.

Acceptance: disable hoặc ghi rõ unavailable ngay trên các shortcut chưa được hỗ trợ, giữ ordinary Page reports ngoài scope. Chuỗi loading “Analyzing General Ledger records...” còn ở dòng414; nhánh đó hiện unreachable từ production guard, nhưng contract remove unconditional loading claim vẫn chưa hoàn tất. Không mô tả chuỗi này như claim đã thấy trong runtime hiện tại.

### R1-F07 — MEDIUM: harness và evidence claim chưa đủ

`test_copilot_failclosed.py:23–55,65–70,134–149,158,195–211`:

- Preflight occupied-port refusal đã thêm, nhưng startup chỉ kiểm tra socket; không xác minh PID/listener sau spawn hoặc launcher exit. Teardown terminate `.cmd` launcher chưa chứng minh Node child cleanup; không có post-teardown port ownership check. **Native harness lifecycle acceptance NOT_RUN**, không suy diễn PASS từ wrapper reviewer.
- Broad API `{}` 200 fallback vẫn tồn tại; module không deny undeclared outbound/service worker/WebSocket. Fixture Panel/Drawer không thay cho actual Page acceptance.
- `exp_widgets` vẫn trong table nhưng không assert; assertion widget false và benign reply text của gold trước đã bị bỏ. Đợi status text cùng giá trị ở case tiếp có thể đọc kết quả trước. [Assertion diff](../evidence/b1s-g4b-correction-r1-2026-10-10/TEST_ASSERTION_DIFF.patch).
- 4 tests không thực thi sáu pending races, timeout injection, unmount hoặc actual Page, nên builder ghi toàn bộ đã verified RESOLVED là rộng hơn bằng chứng cung cấp. Reviewer đã chạy các đường này độc lập; không chuyển số PASS ấy thành chất lượng của harness builder.

Acceptance: restore golden assertions; đợi response/generation từng case; explicit API fixtures + deny undeclared network; exact owned PID/listener startup/cleanup; actual callers/Page và pending success/failure/unmount cases. Sửa report hash/count/commands và giới hạn claims theo evidence thực, vẫn giữ lịch sử. Không thêm framework/dependency.

## Các phần đã đóng trong phạm vi hẹp

F02: các descriptor result/action/demo và unknown-tool cases cũ PASS; falsey presence checks đã có trong source. Không suy rộng thành financial source verification. F03: actual Page company change và Panel contextKey clear PASS. F04: sáu success/failure scope/reset races giữ new loading; unmount success và failure đều fence đúng, PASS. F08: production thiếu injected transport luôn NOT_AVAILABLE, hai caller không POST; boolean không mở lại axios production branch. Fixed date còn trong branch synthetic transport, không phải current production authority/date acceptance. XSS literal rendering, CID constraints, Drawer remount, console minimization cũ PASS; renderer/Drawer được preserve.

## Gates và handoff

| Gate | Current verdict |
|---|---|
| G1 | PASS narrow source/environment/caller identity; không immutable deployment |
| G2 | FAIL: remaining approved contract gaps |
| G3 | PARTIAL: production0POST, widget suppression PASS; financial qualification NOT_RUN |
| G4A | PARTIAL: supplied harness/evidence chưa đầy đủ |
| G4B | **CHANGES_REQUIRED** |
| G10 | **BLOCKED riêng**, không có deployment/site/image/worker evidence mới |
| G01–G03 | NOT_CLOSED bởi UI synthetic tests |

NOT_RUN: ERP/LLM thật, financial truth, permissions/session/cross-user/site/product runtime, native supplied harness acceptance, image/HTTP smoke, p95/throughput/RSS/SQL và timeout-after-commit. Docker không dùng nên không đưa connectivity hay container baseline thành PASS. Build logs và execution time chỉ là log, không performance qualification. Lotus Fin là sản phẩm riêng; ERPNext là nền công nghệ/integration target, không được đồng nhất từ Frappe imports. Không mở F101/F102/COGS/CAGR/concentration, SDK/topology hay B0/V1 trong lượt này.

**Next owner: Chat** nhận [packet nhỏ](B1S_CORRECTION_R1_WORK_TO_CHAT.md), quyết định correction hẹp tiếp theo; Antigravity sửa các nhánh còn lại nếu được dispatch, Work reverify đúng source fingerprints. Không freeze/dispatch từ reviewer. Không rollback tự động; rollback Panel cũ mang lại fallback/HTML risk nên nếu chọn rollback phải giữ entry unavailable. Không dùng khóa UI đã PASS để quảng bá chatbot thao tác tài chính đã qualified cho FinTechathon Shenzhen.
