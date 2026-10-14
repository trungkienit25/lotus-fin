# P1 Final Fix — Work → Chat, 2026-10-12

**P1_FINAL_FIX_LOCAL_PASS; P1A_LOCAL_PASS; P1B_LOCAL_PASS.** Đã sửa trực tiếp F04→F01→F02/F03 và kiểm thử tuần tự. Đây là builder/local verification; Chat cần acceptance độc lập trước khi công bố P1 closed.

- F04: đủ5FORBIDDEN reasons, bounded dict/list scan, final revalidation; denial403/null, malformed success502/null; benign OK/PARTIAL giữ đúng hợp đồng.
- F01: keyed/domain-separated opaque actor; session opaque giữ nguyên, required binding/projection; reject legacy payload và preserve integrity. Public decode/log không raw actor/SID/key.
- F02/F03: một delivery helper56dòng; admitted terminal có đúng1safe acknowledged event; valid RID echo, server CID/header đồng nhất. Sink thiếu không admission; outage safe typed error,1attempt/0ack, không retry.
- A16/B03 implementation, API/legacy/financial/B1-S và lịch sử không đổi. Test disabled cũ chỉ thêm validID cho2input, giữ assertion503.

**Tests:** final173/173 PASS =86historical+87new. Reruns riêng: Track A22/22, B14/14, A16 14/14, B03 8/8, F01–F04 findings8+controls3=11/11; không cộng overlap. Syntax/import/assert-preservation/ADR/scope PASS. Exact commands/exits/assertions, logger healthy/outage, before/after hashes/diff ở `docs/reviews/evidence/chatbot-p1-final-direct-fix-2026-10-12/`.

**Source:** develop@`07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, staged rỗng. Source uncommitted/untracked định danh bằng manifest. Edits3primary+1helper,4newtests+1fixture adjustment. GitNexus stale61/UNKNOWN, bounded static corroboration đã ghi, không graph all-clear.

**Material offline blockers:** không còn tái hiện trong approved matrix. Independent acceptance pending. `P1B_LIVE_AUTHORIZATION=NOT_RUN`; `G10=BLOCKED` riêng. Invoice search/open vẫn disabled, zero business reads; chưa cho phép financial automation. B1-S historical PASS preserved, browser chưa rerun.

**Next eligible batch/owner:** reviewer độc lập chạy exact F01–F04/prior A16/B03 và source preservation trên current hashes. Nếu acceptance đủ, Chat chốt P1 offline và chuẩn bị target qualification preflight riêng: target/site/product/version/ownership, principal/exact Company/document permissions, required audit config, live auth/CSRF và read-only lifecycle/cleanup đã duyệt. Lotus Fin và ERPNext là hai product facts riêng. Không tự triển khai P2-A hoặc bật invoice action.

Chi tiết trong `CHATBOT_P1_FINAL_FIX_IMPLEMENTATION.md`, `CHATBOT_P1_FINAL_FIX_TEST_EVIDENCE.md`. Historical verdict independent cũ bảo tồn.
