# Prompt → ChatGPT Chat: review Work pre-build v0.2 findings trước remediation/freeze

Bạn là contract owner/arbiter. Work đã thực hiện prompt independent pre-build verification cho AI003 candidate v0.2, trên unchanged HEAD `c6f4cd13c677e167ac645d4d0c48d236383c4fac`. Hãy review các finding sau **trước khi giao Antigravity/Zcode sửa code**, đúng điều kiện bạn đã đặt trong prompt Work. Không giao build AI003 hoặc freeze ở trạng thái này.

Tài liệu cần dùng (gửi kèm nếu phiên Chat không truy cập workspace):

1. `docs/features/AI003/AI003_CANDIDATE_CONTRACT_v0.2.md`.
2. `docs/features/AI003/evidence/AI003_PREBUILD_EVALUATION_2026-09-30.md`.
3. `docs/features/AI003/AI003_CONTRACT_FEASIBILITY_v0.2.md`.
4. `docs/features/AI003/AI003_GOLD_MANIFEST.yaml` và SSOT §33 khi cần exact cases/current gate. Các mục SSOT trước đó là lịch sử.

## Verified facts

- 70 distinct cases (53 live source/reusable-primitive, 17 symbolic/specification-only), 6 unmet checks; không cộng với unit suites overlap hoặc coi six unmet checks là six bugs. Numeric AR/AP/window boundaries PASS; temporal posting-date/restatement PASS; document/company isolation PASS; model fallback keeps deterministic metrics unchanged.
- Gold fixture riêng `AI003 Gold 2026`, VND trên `ai003-verify.localhost`, Frappe 16.34.0/ERPNext 16.35.0; actual voucher-free Company kiểm tra empty; temporary permission/voucher probes đã rollback; frontend không bị mutate.
- Independent oracle dùng submitted vouchers/payment references + actual Payment Ledger attribution, không import production metric/rule functions. Hai cutoff 20/09 và 26/09 là verification pair, chưa là baseline production.
- Tại 26/09: AR net 565k, overdue net 65k, ratio 0,1150442478; positive-only AR 575k và overdue 75k; unallocated AR credit -10k riêng. AP +1..7 =275k, +1..30=975k, ratio0,2820512821; AP overdue600k/due-today700k/contextunallocatedcredit-10k riêng. Allocated credit 5k giảm invoice residual đúng một lần. `return_against` không tự chứng minh credit đã allocated.

## Concrete defect 1 — PB-SEC-01 HIGH

Restricted Accounts User có Company/Account permission. Sau khi populate AI002 cache bằng real source read, tạo Custom Role trên Accounts Receivable chỉ cho Accounts Manager. `Report.is_permitted()` false; direct ERPNext report từ chối/no data. Tuy nhiên `check_ai002_report_permission` vẫn return normally; request giống hệt trả **same cached forecast ID, 10 obligations, opening cash**, dù source-report permission đã bị thu hồi.

Root cause: `security/access.py:check_report_permission` gọi generic `has_permission` import từ query_report để kiểm tra Report document, không enforce report-specific allowed/custom roles. Minimal fix cần primitive report-specific đúng active user (kể cả explicit user parameter), giữ Company/ref-DocType guards, generic FORBIDDEN và evict cache khi deny. Regression phải dùng real Frappe permission change trong TTL với Company/Account permissions còn giữ, cùng regrant. Không chỉ thêm cache clearing hoặc mock test.

## Concrete defect 2 — PB-DATA-01

Xóa due_date/overdue/overdue_amount của một actual positive AR row. AI001 vẫn trả `overdue_ar_ratio=AVAILABLE -0,0177`; phần dương quá hạn bị mất trong khi credit góp phần âm. Expected: overdue metric unavailable/inconclusive khi không chứng minh được basis; không zero/benign. Có thể giữ total AR nếu total source vẫn valid. Chốt rule cho null/malformed due date, explicit overdue amount và netting; không tự đổi công thức cho test xanh.

## Concrete defect 3 — PB-DATA-02

Append exact copy của actual AR row làm total `AVAILABLE 640k` thay vì565k. AP adapter tạo repeated Purchase Invoice source_ref, positive obligations8 thay vì7. Cần identity/consistency rule trước aggregation; đừng dedup theo voucher alone vì payment-term/account splits có thể hợp lệ. Cho phép builder xác minh actual ERPNext split schema rồi xử lý exact/conflicting duplicates có bằng chứng.

## Candidate decisions required

- AP null due date là coverage gap của candidate; AI002 cho phép nullable obligation, không mặc định là bug cần fail cả forecast. AI003 cluster phải inconclusive khi coverage không chứng minh đủ.
- AR net vs positive residual, unallocated-credit context, observation identity/count, zero denominator, baseline/window/materiality/severity approvals.
- Comparator equality, high/warning ordering, rounding before threshold comparisons và precedence SOURCE_INVALID vs POLICY_PENDING.
- Report/derived evidence replay: document reauthorization PASS, actual cutoff/checksum/restatement change verified; no durable authorized report snapshot replay by ID. Chọn dynamic authorized report replay + saved-hash comparison/restatement status, hoặc bounded durable snapshot design. Không coi checksum/snapshot ID là permission token.
- `get_risk_signals` endpoint/agent chưa có là expected pre-build state; không dùng việc đó làm G4A failure. Current G4A blocked bởi actual report/cache defect.

## Output requested

1. Review finding dispositions, phân biệt foundation defect, candidate design change và Finance approval pending. Không xoá/chỉnh historical evidence hoặc tự nâng gate.
2. Tạo candidate contract v0.3 draft hoặc quyết định bổ sung rõ cho các semantics cần chốt; threshold production vẫn pending nếu chưa có Finance approval.
3. Viết **một prompt tập trung cho Antigravity/Zcode**, scope sửa PB-SEC-01/PB-DATA-01/PB-DATA-02 được bạn chấp nhận, yêu cầu GitNexus impact/detect-changes, tests/live replays và bảo vệ frontend. Tái dùng Gold fixture/independent oracle; không sửa fixture/formula để test xanh; không xây AI003 trong remediation.
4. Viết handoff ngắn cho Work để re-test affected source gold/permission/cache sau fix. Chỉ cân nhắc freeze khi G1/G2/G3/G4A đủ PASS và business policies có approval thật.

Latest gates: G1 PASS isolated runtime; G2 PARTIAL; G3/G4A BLOCKED; G4B NOT_APPLICABLE_YET; **CONTRACT FREEZE NOT_READY**. WR-01/WR-02 vẫn VERIFIED FIXED trong scope trước đó.
