# Work → Chat — B1-S Correction Round 1 recheck

**Decision: `B1S_G4B_CHANGES_REQUIRED`.** Antigravity đã đóng **16/16 case FAIL cũ**, giữ **20/20 PASS cũ**. 12 case bổ sung bounded theo approved contract còn **11 FAIL / 1 PASS**. Typecheck/build exit0; lint exit0 còn warning. 4 tests hiện tại và 3 golden tests gốc từng-byte đều PASS dưới wrapper server/browser/network reviewer; các suite trùng coverage, không cộng thành acceptance rộng hơn.

Identity: develop HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + uncommitted hashes. Correction đổi normalizer/hook/Panel/test/main fixture; renderer/Drawer/package/lock preserve. Source review không bị sửa. 60 raw evidence và 3 deliverables G4B cũ nguyên vẹn. GitNexus context notfound, graph stale/UNKNOWN; không được dùng làm all-clear. F102 và topology/SDK không mở lại.

## Remaining small batch

| Task | Root cause / minimal acceptance |
|---|---|
| **F01 HIGH** — normalizer | boolean/object/array status bị bỏ qua → OK và marker lọt DOM; unknown check/HTTP early return che FORBIDDEN; hai terminal conflict còn sai. Explicit bounded typed guards, absolute recognized denial priority, unsupported/conflicting non-auth states → NOT_AVAILABLE, no marker/widgets. Giữ 36 gold cũ. |
| **F05 MEDIUM** — hook | ETIMEDOUT thiếu; diagnostic chứa “timeout” lấn HTTP403. Permission trước timeout; known timeout signals, không substring heuristic. Giữ silent stale/cancel và sáu race PASS. |
| **F06 MEDIUM** — Panel | Bốn finance quick buttons vẫn bật, không unavailable guidance. Disable/mark rõ; Reports đã khóa, welcome đã sửa. Loading GL string còn static nhưng hiện unreachable; remove theo contract. Ordinary Page reports ngoài scope. |
| **F07 MEDIUM** — harness/report | `{}` API fallback, thiếu deny-all/owned Node child cleanup; widgets/benign assertions bị bỏ; status wait có thể đọc case cũ. Restore gold, response/generation waits, declared mocks, PID+listener cleanup, actual Page/races. Report sửa hash/count và chỉ claim tests thực chạy. |

F02 descriptor cases, F03 company/context clear, F04 sáu race + unmount success/failure, F08 production0POST PASS trong scope hẹp. Fixed date chỉ ở injected synthetic branch; không server authority. Renderer literal text/CID/Drawer remount PASS.

Giữ allowlist correction hiện hữu; không mới application file/dependency/backend/session/ERP. New production126/160/57lines dưới200; Panel540 dùng variance; test211 dưới user-approved cap320. Không xin lại approval test cap. Bounded impact + caller confirmation theo AGENTS bắt buộc trước application edit; graph UNKNOWN không low risk.

## Gates và next owner

G1 PASS narrow source identity; **G2 FAIL**, G3 PARTIAL, G4A PARTIAL, **G4B CHANGES_REQUIRED**. **G10 BLOCKED riêng**, G01–G03 NOT_CLOSED. ERP/LLM/session/security runtime, native builder harness lifecycle, deployment và performance NOT_RUN. Reviewer dùng private copy/server ở5188, outbound blocked; cleanup riêng, không Docker/shared frontend/data mutation. Lotus Fin là sản phẩm riêng; không biến UI safety patch thành chatbot thao tác ERP đã qualified cho FinTechathon Shenzhen.

**Chat** quyết định dispatch một correction hẹp nếu tiếp tục; **Antigravity** sửa tối thiểu, **Work** recheck hash/gold/gates, **Chat** đóng batch sau verdict mới. Reviewer không dispatch/freeze/rollback. Không mở B0/V1/SDK để làm UI tests PASS.

[Full current recheck](B1S_CORRECTION_R1_INDEPENDENT_RECHECK.md) · [ledger](B1S_CORRECTION_R1_TEST_RESULTS.json) · [raw evidence](../evidence/b1s-g4b-correction-r1-2026-10-10/DOM_RESULTS.json). Oracle late-failure ban đầu dùng sai property, đã chạy lại đúng và PASS; ledger minh bạch supersession, giữ raw lịch sử.
