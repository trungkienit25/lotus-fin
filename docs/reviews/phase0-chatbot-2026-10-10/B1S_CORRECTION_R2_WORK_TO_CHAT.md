# Work → Chat — Round2 G4B recheck

**`B1S_G4B_CHANGES_REQUIRED`**, dù **48/48 previous gold PASS**. 11 FAIL cụ thể Round1 đã đóng, không regression của36case cũ. Typecheck/build exit0, targeted lint exit0/5warnings. Current4tests và original3gold từng-byte PASS; các suite trùng coverage, không cộng thành qualification.

**Hai phần còn lại trong đúng contract:**

1. **F05 catch precedence:** error có ETIMEDOUT + HTTP500 + body FORBIDDEN vẫn thành TIMEOUT. Case bổ sung `R2_BODY_DENIAL_TIMEOUT` FAIL. Normalizer trực tiếp đúng; chỉ cần ưu tiên recognized body denial trong catch trước timeout, reuse parser/CID/safe text, giữ lifecycle.
2. **F07 native acceptance FAIL thật:** native pytest4PASS nhưng Node child15224 vẫn giữ5188 sau teardown launcher24756. Undeclared local API được handler trả `{}`/200 mà test không fail. Reviewer đã stop đúng child thuộc private root. Foreign-listener refusal PASS. Native module chưa deny outbound/SW/WS hoặc synchronize generation; thiếu actual Page/pending races/timeout tests. Reviewer containment/coverage không thay cho native acceptance.

Minimal tasks: direct owned Node/PID+listener/cleanup assertions; explicit mocks + fail unexpected network/SW/WS; restore Reports assertion và response/generation synchronization; representative Page/Drawer/pending lifecycle/timeout cases; thêm body-denial timeout probe. Giữ48gold và source guard0POST. Không thêm SDK/backend/session/framework. Current normalizer149/hook169/renderer57; Panel545 có variance; test228 còn dưới approved cap320. Không xin lại cap; nếu essential scope vượt thì SCOPE_CHANGE_REQUIRED.

Builder report phải bổ sung exact HEAD/current hashes, sửa preserved hashes/line counts bằng annotation và bỏ claim F07 đã đóng toàn diện. Parsing fixed3levels không recursive; payload-size cap/qualification chưa có, không invent performance acceptance.

Source: develop HEAD `07f7251d3a0744356bf96fb2fea55ec6df9a0ce2` + current uncommitted manifest. Chỉ normalizer/hook/Panel/test/report đổi từR1; renderer/Drawer/fixture/package/lock preserve. GitNexus stale/notfound vẫn UNKNOWN: bounded impact + static caller verification trước edit. Review không sửa source; 123rawhash và6deliverables trước preserve.

G1PASS narrow identity; **G2FAIL, G4AFAIL, G4BCHANGES_REQUIRED**; G3PARTIAL; **G10BLOCKED riêng**, G01–G03NOT_CLOSED. ERP/LLM/session/deployment/performance NOT_RUN. Lotus Fin không đồng nhất với ERPNext; chưa qualified chatbot ERP automation cho FinTechathon Shenzhen.

**Chat** quyết định dispatch hẹp, **Antigravity** sửa, **Work** recheck source/gold/native gates, **Chat** đóng batch. Không freeze/dispatch/implementation từ reviewer.

[Full recheck](B1S_CORRECTION_R2_INDEPENDENT_RECHECK.md) · [ledger](B1S_CORRECTION_R2_TEST_RESULTS.json) · [native evidence](../evidence/b1s-g4b-correction-r2-2026-10-10/NATIVE_RESULTS.json).
