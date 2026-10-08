# Final foundation verification — Work, 2026-09-30

## Kết luận

**FOUNDATION: PARTIAL. PB-SEC-01 FAIL, PB-DATA-01 FAIL, PB-DATA-02 FAIL.**

HEAD `86208f49e05122531c1cbe8b11d066092244dd4c`, branch `feature/risk-signal-agent`. `git diff c6f4cd1..HEAD -- lotus_fin` rỗng: commit mới chỉ thêm tài liệu/script; chưa có remediation production cho ba PB defects. Các fix WR-01/WR-02 và A–D được giữ trong phạm vi đã chứng minh; không suy rộng thành toàn bộ foundation an toàn.

## Environment Alignment Verdict — VERIFIED_RUNTIME

- Sáu dịch vụ app cùng image `sha256:220e4f5dc54973a3bef476a9ef37ca1ea49a71689cad48526d1da8ddcc383bca`, đang chạy. Hash workspace/container khớp:

| Source | SHA256 |
| --- | --- |
| `security/access.py` | `cfd1de3acf166790aca101db6169d2ecff7b2de569b60c81ace900186c73b2df` |
| `ai/financial_snapshot.py` | `b786dccdadce55f2958654d2d31536ea7f8396c7eea805ba3c98dab3ca242e59` |
| `cashflow/adapters.py` | `96643487acfd377afe18b9e58b13d05de5d37067b0da0b7c60c1839c8c45de5b` |
| `cashflow/service.py` | `cf347ba7184514ce2867062853f68fd37d8b17b5fa5423941d38854801a75fd3` |

- Isolated site `ai003-verify.localhost`: Frappe 16.34.0, ERPNext 16.35.0, Lotus Fin 0.0.1, installed apps `[frappe, erpnext, lotus_fin]`; timezone `Asia/Ho_Chi_Minh`, MariaDB. Không xuất credential.
- Cột `Company.ai002_approved_cash_accounts` tồn tại; Gold currency VND, cash scope `["Cash - A3G"]`. Không có production/migration diff mới, nên không rebuild hoặc migrate chỉ để đổi nhãn revision tài liệu. Đây là alignment của **source liên quan**, không tuyên bố image chứa toàn bộ HEAD tài liệu.
- Evidence: [environment JSON](AI003_FINAL_ENVIRONMENT_2026-09-30.json), [container image list](AI003_FINAL_CONTAINER_ALIGNMENT_2026-09-30.txt). Không thao tác site `frontend`.
- Dirty tree trước phiên gồm các file untracked của người dùng; không overwrite/reset/rebase/commit. Các file mới trong phiên nằm tại AI003 docs/evidence.

## Commands và kết quả

Chạy từ project root sau khi copy scripts/oracle vào backend `/tmp`:

```powershell
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/final_environment_probe.py
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/final_foundation_probe.py
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python -m unittest -q lotus_fin.tests.test_ai003_foundation_remediation lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed
python docs/features/AI003/evidence/final_symbolic_probe.py
```

| Evidence | Result | Giới hạn |
| --- | --- | --- |
| [Foundation results](AI003_FINAL_FOUNDATION_RESULTS_2026-09-30.json), [script](final_foundation_probe.py) | 51 checks: 39 PASS / 12 FAIL / 0 harness errors | Gồm real runtime, altered live rows, và harness-only; 12 FAIL thuộc ba defects, không phải 12 bugs. Process exit 0 chỉ xác nhận script hoàn tất. |
| [Targeted unittest](AI003_FINAL_TARGETED_UNITTEST_2026-09-30.txt) | 152/152 OK | VERIFIED_TEST; bộ mock/unit hiện tại không bắt được các PB defects ở runtime. Không cộng với suite lịch sử/51 checks. |
| [Symbolic results](AI003_FINAL_SYMBOLIC_RESULTS_2026-09-30.json) | 25/25 specification assertions | `TEST_ONLY_POLICY`; kiểm tra bảng comparator/ordering/precedence được đề xuất, không chứng minh production engine hoặc approval. |

Hai lần khởi chạy ban đầu được giữ trong diagnostic files: harness dùng nhầm tên `points` thay cho `forecast_points`, unit runner chạy sai cwd nên Frappe logger không tìm thấy thư mục logs. Đã sửa **script kiểm chứng/cwd**, không sửa production. Chỉ các final results trên được tính.

## PB-SEC-01 — HIGH, FAIL / VERIFIED_RUNTIME + CODE_INSPECTION

**Reproduction:** User Accounts User mới, Company A3G được cấp, quyền Account còn hợp lệ. Populate cache bằng source thật: `FORECAST_UNAVAILABLE`, forecast `FC-6CDB4EB5`, 10 obligations, opening cash hiện diện. Tạo Custom Role AR chỉ cho Accounts Manager trong cùng transaction; authoritative `Report.is_permitted()` false và direct ERPNext report từ chối. Guard active user và trusted explicit user (session Administrator kiểm tra restricted user) vẫn cho qua. Cache request giữ cùng ID và financial payload. `skip_cache=True` trả `SOURCE_ERROR`, payload rỗng, nhưng không đáp ứng generic `FORBIDDEN`. Regrant khôi phục source read.

**Root cause:** `security/access.py:check_report_permission` gọi generic `query_report.has_permission` cho Report document, không kiểm tra report-specific allowed/custom roles. `cashflow/service.py:_reauthorize_cached_resources` và adapters tái sử dụng guard này; lỗi permission ở report envelope bị phân loại thành source failure trên fresh request.

**Affected contract:** quyền source report, cache revoke/eviction, error precedence, trusted user, replay/evidence adapter tái sử dụng foundation.

**Minimal fix:** dùng report-specific authorization đúng explicit active user; giữ Company, ref-DocType và Account/document guards; denied cache evict và trả generic FORBIDDEN không financial payload; fresh request cũng trả FORBIDDEN. Không dùng session Administrator thay explicit restricted user; không chỉ clear cache.

**Acceptance:** real Frappe Custom Role revoke/regrant trong TTL cho từng allowlisted report có liên quan, cached/fresh denial, session-vs-explicit-user distinction, Company/Account còn được cấp; revoked payload tuyệt đối rỗng. Unit + live replay. **Owner:** Antigravity/Zcode sau Chat chốt handoff F0; Work kiểm lại.

Company cross-denial, Account User Permission denial, document Customer User Permission denial/regrant, cross-company evidence, arbitrary report and forged snapshot token đều PASS trong current probe. Chúng không bù cho lỗi report/cache.

## PB-DATA-01 — FAIL / LIVE_ROWS_MUTATION + CODE_INSPECTION

**Reproduction:** từ AR thật cutoff 26/09, bỏ due_date/overdue fields trên positive row 75.000; hoặc thay due_date bằng `not-a-date`. Total vẫn 565.000, overdue thành −10.000, ratio −0,0177 thay cho typed unavailable. Valid due-date hoặc explicit amount giữ 565.000/65.000. Explicit amount có thể đi qua dù date malformed: đây chỉ là observed parser behavior, không phê duyệt equivalence/consistency của hai basis.

**Root cause:** parser fallback due-date có `except: pass`; thiếu basis không đặt unavailable; credit âm vẫn được cộng vào overdue. **Affected contract:** overdue coverage, source-invalid precedence, source trust của AR current/baseline.

**Minimal fix:** thiếu/malformed authoritative basis làm affected overdue metric UNAVAILABLE/INCONCLUSIVE; total hợp lệ có thể giữ AVAILABLE. Explicit overdue phải có provenance và được kiểm tra consistency/scope; không tự đổi net/positive formula của AI001.

**Acceptance:** missing due, missing explicit, both missing, malformed dates, conflicting basis, valid explicit/date, mixed good/bad rows, positive residual + negative credit; không partial overdue sum hoặc missing→zero. **Owner:** Antigravity/Zcode F0 → Work.

## PB-DATA-02 — FAIL / LIVE_ROWS_MUTATION + CODE_INSPECTION

- Exact AR duplicate: AI001 565.000 → 640.000; AI002 positive AR obligations 3 → 4.
- Exact AP duplicate: AI001 net AP 2.765.000 → 2.840.000; AI002 positive AP obligations 7 → 8. Net AP và positive-only AP 2.775.000 có semantics khác nhau, không ép chúng bằng nhau.
- Conflicting amount cùng voucher identity cũng được AI002 chấp nhận thêm ở cả hai leg.
- Missing voucher identity fail-closed trong cả AI001/AI002, giữ WR-02 PASS.
- Hai row giả lập payment-term chia đều vẫn giữ tổng. Report thật với `based_on_payment_terms=1` thành công nhưng fixture hiện hữu không chứng minh hai installment distinct cùng voucher. **Legitimate multi-term/account split identity: NOT_VERIFIED**, không coi giả lập là chứng minh ERP allocation.

**Root cause:** không có observation identity/reconciliation trước summation/obligation construction. **Affected contract:** totals, windows, minimum count, source completeness, evidence references.

**Minimal fix:** identity phiên bản hóa theo authorized report scope + voucher + account + schedule/allocation discriminator khi được chứng minh. Exact identical observation không double-count (dedup có audit note hoặc typed rejection); conflicting/ambiguous identity fail-closed. Không blanket dedup theo voucher_no hoặc theo due_date/payment-term description; valid splits phải reconcile với authoritative ledger/schedule, rồi giữ đủ amounts. Nếu source thiếu discriminator, reject unsupported split scope hoặc bổ sung verified adapter; không phỏng đoán.

**Acceptance:** exact/conflicting AR/AP ở AI001 + AI002; missing/ambiguous ID; real multi-term/account split với oracle độc lập; source totals khớp. N_min định nghĩa count economic voucher hay installment phải được Chat/Finance chốt riêng. **Owner:** Antigravity/Zcode F0 → Work.

## Independent gold closure

Oracle chỉ dùng submitted vouchers/payment allocations/Payment Ledger; không import production formulas. Hai source hashes **khớp manifest cũ byte-for-byte**, nên giữ expected numbers và 70-case manifest; chỉ thêm metadata revalidation, không relabel các lỗi cũ PASS.

| Cutoff | Net AR | Net overdue | Positive AR / overdue | AP +1..7 / +1..30 | AR credit |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20/09 | 650.000 | 0 | 650.000 / 0 | 1.400.000 / 1.950.000 | 0 |
| 26/09 | 565.000 | 65.000 | 575.000 / 75.000 | 275.000 / 975.000 | −10.000 |

26/09 AP overdue 600.000, due-today 700.000, unallocated AP credit −10.000; allocated credit 5.000 đã giảm invoice residual đúng một lần. Gold vẫn 6 submitted SI, 10 submitted PI (gồm returns), 4 PE, 1 JE. Bốn cancelled invoices tồn tại từ IVL trước, không vào oracle; giữ nguyên vì không cần xóa để kiểm chứng. Probe phiên này không tạo voucher, không commit; cuối phiên User/Custom Role thử nghiệm absent và gold fingerprint unchanged.

## Evidence reuse và giới hạn

- Temporal source ở §33 được reuse có điều kiện: production diff rỗng, source hashes/site versions/oracle fingerprints không đổi. Future posting, backdate/cancel/amend = posting-date/restatement semantics; **không AS_KNOWN_AT**. Không chạy lại temporal matrix hoặc cộng test totals cũ.
- Dynamic replay: current live same-source MATCH; real report revoke FORBIDDEN nhờ authoritative guard trong **harness**; changed saved hash RESTATED và forced unavailable UNAVAILABLE là HARNESS_ONLY. Historical actual backdated source change có evidence §33/IVL; không dựng lại vouchers. Chưa chứng minh production replay adapter đã an toàn.
- Replay cần bind immutable request scope/cutoff/company/report/method/currency/timezone và canonical row/schema hash; source refs/hashes không phải token. Authorization trước hash comparison; denied không trả stored data. Multi-report atomic snapshot chưa có; cutoff giống nhau không chứng minh chung transaction snapshot.
- Unit/model failure evidence trước được reuse ở unchanged relevant source; không gọi external model. Không có AI003 endpoint → G4B NOT_APPLICABLE_YET.
- GitNexus context/impact: report guard LOW với extract_key_report_data, AI001 fetcher/predict_cashflow/training callers; AR parser LOW với build_financial_snapshot/API; `_collect_obligations` UNKNOWN. Index 12 commits behind; detect-changes compare thấy 24 docs/script files, no indexed-symbol overlap, **không clean check**. Actual code inspection xác nhận thêm AI002 adapters/cache paths index bỏ sót. No production symbol edits. Code inspection limitation được giữ, không suy UNKNOWN là an toàn.
- Correction: §34/IVL nói “67 passing” của matrix §33 là sai cách đếm. Matrix gốc 70 cases, 6 unmet → **64 passed** (gồm 17 specification-only), không 67; không dùng con số này nâng gate.

## Exit criteria

Baseline/reproduction/code review/targeted suites/current runtime replay đã có cho ba PB defects. **Remediation diff và passing acceptance/integration replay chưa có**; không ký đóng Phase 1. Không nghiên cứu lại KPI ngoài hai signal hoặc tạo thêm defect bucket không có reproduction.
