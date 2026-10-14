# P1 final — Packet quyết định độc lập

12/10/2026 · Asia/Saigon · Independent Backend QA / Application Security.

**P1-A: P1A_OFFLINE_PASS**  
**P1-B: P1B_OFFLINE_PASS**

Đã kiểm tra source hiện tại và tái hiện độc lập F01–F04. **Đề nghị chuyển sang P2-A target qualification preflight.** Chưa thực hiện preflight hoặc triển khai P2-A.

**Artifact:** `develop@07f7251d3a0744356bf96fb2fea55ec6df9a0ce2`, staged rỗng; backend P1 untracked. [SHA-256/source snapshot](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/SOURCE_BEFORE.json) và [exact diff](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/INDEPENDENT_SOURCE_DIFF.patch.txt) định danh working tree; chưa định danh serving image. Domain/codec/controller/helper: 198/147/117/56 dòng.

|Finding|Quan sát trên source thật|Kết luận|
|---|---|---|
|F04|Đủ 5 denial reasons, OK/PARTIAL, dict/list; domain/DTO/serializer reject; terminal 403/null, không protected data; benign control 200.|CLOSED_VERIFIED|
|F01|Public ref không raw actor/email/SID/secret key; matching actor valid, wrong actor/scope/key/version/purpose/expiry denied.|CLOSED_VERIFIED|
|F02|Healthy sink đúng 1 attempt/1 ack/1 log line cho từng terminal path. Missing/failing/suppressed/short-write/flush-fail không claim delivery; không protected success.|CLOSED_VERIFIED|
|F03|Valid UUID4 echo nguyên; missing/invalid thay UUID4 với INVALID_REQUEST; body/header/event IDs khớp.|CLOSED_VERIFIED|
|A16/B03|14/14 và 8/8 rerun PASS; giữ shared-handler locking/ack, exact Company/actor và unavailable-seam denial.|CLOSED_VERIFIED|

**Lệnh/exits thực tế:** `git rev-parse HEAD`, status/diff: exit 0. `Get-Content -Raw …/FOCUSED_REPRODUCTION.txt | C:/Python313/python.exe -B -`: **173/173 PASS, exit 0**. Tương tự `NEGATIVE_REPRODUCTION.txt`: **138/138 PASS, exit 0**. Reviewed stdin A16/B03 qua `python -B -`: **exit 0/0**. `…/` là `docs/reviews/evidence/chatbot-p1-final-independent-recheck-2026-10-12/`. [Exact commands/args/exits](../evidence/chatbot-p1-final-independent-recheck-2026-10-12/COMMANDS.json); không cộng overlapping suites thành unique coverage.

**Integrity:** 27 code/test files <200 dòng; original assertions giữ nguyên, chỉ hai disabled-test inputs thêm valid ID. 3.484 historical artifacts và 13 B1-S snapshots bảo toàn; 4.215 fingerprints không đổi trong phiên này. Không implementation edit/install/ERP/Docker/commit/deploy. GitNexus stale 61 commits, current symbols UNKNOWN; static callers được đối chiếu, không tuyên bố graph all-clear.

**Giới hạn gate:** ERP permission positives dùng qualified doubles, không chứng minh live authorization. HTTP/auth/CSRF và ERP document/field/revocation rights **NOT_RUN**. Invoice search/open **vẫn disabled**. B1-S historical PASS giữ nguyên. **G10 independently BLOCKED**.

Không có material offline blocker tái hiện. Gate kế tiếp đủ điều kiện để đề nghị Chat xét duyệt là **P2-A target qualification preflight**, với target/artifact/baseline/lifecycle riêng; không phải quyền bật capability hoặc deployment. [Báo cáo độc lập đầy đủ](CHATBOT_P1_FINAL_INDEPENDENT_RECHECK.md).
