Bạn là **independent pre-build verifier** cho Lotus Fin AI003.

## Authority

Đọc trước:

1. `docs/features/AI003/AI003_MASTER_SSOT.md`
   - §32 trở đi là authority hiện hành.
   - Không dùng blocker lịch sử đã được supersede làm trạng thái hiện tại.

2. `docs/features/AI003/evidence/AI003_WR01_WR02_WORK_VERIFIED_2026-09-30.md`

3. `LotusFin_AI_Features_Codebase_Aligned_v2.md`

4. `docs/features/LOTUS_FIN_AI_FEATURE_BUILD_WORKFLOW_3_TOOLS_V3_VI.md`

5. Candidate Contract AI003 v0.2 do ChatGPT Chat cung cấp.

Current verified implementation revision:

```text
c6f4cd1
```

Nếu repository đã thay đổi revision:

- ghi exact HEAD;
- đánh giá delta có ảnh hưởng phạm vi verification hay không;
- không tự checkout ngược hoặc bỏ thay đổi.

## Goal

KHÔNG implement AI003.

Nhiệm vụ:

```text
Candidate Contract v0.2
→ controlled fixture
→ independent source gold
→ symbolic rule boundaries
→ permission/security verification
→ temporal verification
→ evidence replay verification
→ gate reassessment
```

Chỉ kiểm tra lại foundation evidence khi contract mới tạo rủi ro cần kiểm chứng.

Không quét lại toàn repo.

---

# 1. Runtime safety

Dùng isolated site:

`ai003-verify.localhost`

Có thể tạo/thay đổi synthetic fixture tại site này khi cần và ghi rõ dữ liệu được tạo.

Bảo vệ:

- site `frontend`;
- company/data thật;
- credential;
- business data ngoài fixture.

Không mutate site `frontend`.

Ghi:

```text
repo HEAD
container/image revision
Frappe version
ERPNext version
timezone
company
currency
cash scope
migration status
```

Không cộng các test suite overlap thành một total duy nhất.

---

# 2. Verify contract feasibility

Review Candidate Contract v0.2.

Mỗi field đánh:

```text
SUPPORTED
SUPPORTED_WITH_CHANGE
NOT_SUPPORTED
NOT_VERIFIED
```

Đặc biệt xác minh:

- accounting `as_of`;
- baseline date;
- company scope;
- VND currency enforcement;
- Finance Book behavior;
- snapshot refs;
- EvidenceRef compatibility;
- typed source states;
- evidence reauthorization.

Không implement service AI003.

---

# 3. Independent AR gold

Tạo/khóa controlled AR fixture đủ để tính độc lập:

```text
total AR residual
overdue AR residual
overdue ratio
baseline overdue ratio
delta percentage points
```

Không import AI003 code.

Oracle nên tính trực tiếp từ submitted vouchers/payment allocations hoặc nguồn độc lập phù hợp.

Kiểm tra:

### Valid source

- positive residual;
- partial payment;
- paid invoice;
- credit allocation nếu applicable;
- invoice due exactly `as_of`;
- invoice due before `as_of`;
- invoice due after `as_of`.

Verify candidate semantic:

```text
due_date < as_of
→ overdue
```

Nếu ERPNext authoritative overdue semantics khác, báo conflict thay vì ép fixture pass.

### Data quality

Test:

- legitimate empty;
- zero denominator;
- malformed amount;
- missing voucher identity;
- missing overdue/due-date information;
- footer/summary row;
- duplicate row.

Expected behavior:

```text
missing/malformed != zero
missing/malformed != benign
```

### Baseline

Dùng ít nhất hai valid cutoffs.

Giữ cutoff 20/09 và 26/09 đã có nếu chúng vẫn phù hợp, nhưng không coi khoảng sáu ngày là production baseline policy.

Tính independent numeric oracle và source hashes.

Không dùng fixture để derive business threshold.

---

# 4. Independent AP gold

Thu thập due dates và residual amounts của AP fixture.

Oracle phải chứng minh:

```text
amount due days 1..7
amount due days 1..30
cluster ratio
```

Candidate formula:

```text
AP_CLUSTER_RATIO =
AP due in [as_of+1, as_of+7]
/
AP due in [as_of+1, as_of+30]
```

Verify inclusive boundaries.

Đừng sử dụng tổng AP 9,5m/7,95m để suy cluster nếu chưa có due dates.

Test:

- due at +1;
- due at +7;
- due at +8;
- due at +30;
- due at +31;
- already overdue;
- null due date;
- partial payment;
- cancelled voucher;
- duplicate voucher;
- credit adjustment/netting nếu applicable.

Xác minh không double-count credit adjustment nếu residual đã phản ánh nó.

Due date ở đây là contractual date.

Không biến nó thành expected/actual cash timing.

---

# 5. Symbolic rule tests

Production thresholds chưa được Finance approved.

Không chọn threshold từ fixture.

Dùng symbolic:

```text
T_warning
T_high
A_min
D_min
N_min
```

Kiểm chứng rule engine semantics ở mức oracle/test specification:

```text
value < T
value == T
value > T
```

và materiality gate tương tự.

Nếu cần numeric values cho test harness, ghi rõ:

```text
TEST_ONLY_POLICY
```

Không ghi chúng vào production contract.

Expected:

```text
threshold approval missing
→ POLICY_PENDING
→ finding=null
→ severity=null
```

---

# 6. Temporal evaluation

P0 policy:

```text
POSTING_DATE_CUTOFF
```

Không support:

```text
AS_KNOWN_AT
```

Test:

### Future posting

Tạo voucher với posting date sau cutoff.

Recompute same historical snapshot.

Expected:

```text
metric/rule input unchanged
```

### Backdated/cancelled/corrected transaction

Theo candidate policy, historical output có thể restate.

Verify:

- recomputation reflects restated ledger;
- snapshot/evidence fingerprint changes;
- no claim of immutable historical knowledge.

Nếu current system cannot expose restatement provenance safely, mark limitation/blocker.

---

# 7. Permission/evidence evaluation

Use restricted users/roles where possible.

Test:

```text
authorized company
unauthorized company
report permission denial
document evidence denial
cross-company evidence ref
tampered signal filter
arbitrary report
arbitrary DocType
arbitrary metric ID
```

FORBIDDEN must:

- return generic payload;
- not expose company/resource existence;
- return no stale prior signal payload.

Evidence drilldown must reauthorize at access time.

Snapshot ID alone must never grant access.

---

# 8. Cache revoke/regrant

Complete the verification that remained open.

Flow:

```text
authorized
→ populate cache/read result

revoke relevant permission
→ repeat same request
→ cached financial data must NOT be returned

regrant permission
→ correct authorized behavior restored
```

Test cross-company isolation if fixture setup supports it.

Do not modify shared production/demo company to achieve this.

---

# 9. Model/explanation failure design

Không cần AI003 implementation.

Validate pre-build expectations against existing bounded explanation architecture:

```text
model timeout
model unavailable
malformed response
grounding failure
```

Expected future AI003 behavior:

```text
deterministic signal remains unchanged
explanation = UNAVAILABLE
```

Nếu existing AI001/AI002 framework can be safely reused, record exact reusable components.

Không build new agent framework.

---

# 10. Gold manifest

Create/update:

`docs/features/AI003/AI003_GOLD_MANIFEST.yaml`

Gold phải độc lập với future AI003 production implementation.

Per test case store tối thiểu:

```yaml
case_id:
company:
as_of:
baseline_as_of:
timezone:
currency:

source_refs:
source_hashes:

expected:
  source_state:
  metric_inputs:
  metric_value:
  baseline_value:
  change_value:
  evaluation_state:

policy:
  status:
  symbolic_thresholds:

notes:
```

Raw sensitive financial rows không đưa vào public logs/docs nếu không cần.

---

# 11. Acceptance matrix

Report status cho từng nhóm:

```text
AR numeric oracle
AP numeric oracle
legitimate empty
malformed source
window boundaries
temporal future posting
backdated/restated policy
company isolation
report permission
evidence permission
cache revoke/regrant
model failure design
```

Statuses:

```text
PASS
PARTIAL
BLOCKED
NOT_APPLICABLE
```

Mọi PASS phải có:

```text
environment
commit
command/test
result
artifact
```

---

# 12. Gate reassessment

Reassess:

```text
G1 Runtime
G2 Contract
G3 Data & Method
G4A Security/Evaluation
G4B NOT_APPLICABLE_YET
```

Important:

G4A không yêu cầu AI003 endpoint/E2E chưa tồn tại.

Pre-build G4A đánh giá:

- security architecture;
- reusable authorization primitives;
- source permission behavior;
- fixture/gold plan;
- adversarial source tests;
- cache/evidence protections.

AI003 endpoint-specific security/E2E sẽ thuộc G4B sau implementation.

---

# 13. Approval handling

Các business decisions chưa approved:

```text
AR baseline policy
AR warning/high thresholds
AR materiality floor
AP 7/30 window
AP warning/high thresholds
AP materiality floor
minimum observation policies
severity labels
```

Work KHÔNG tự approve.

Work có thể:

- supply distributions/source evidence;
- show symbolic boundary behavior;
- identify consequences of each option.

Không dùng fixture để “learn” threshold production.

---

# 14. Required output

Update current SSOT by appending a new authoritative section.

Không rewrite historical evidence.

Create concise Work evidence report:

`docs/features/AI003/evidence/AI003_PREBUILD_EVALUATION_<DATE>.md`

Final summary:

```text
CANDIDATE CONTRACT
SUPPORTED / NEEDS_CHANGE / BLOCKED

AR SOURCE GOLD
PASS / PARTIAL / BLOCKED

AP SOURCE GOLD
PASS / PARTIAL / BLOCKED

TEMPORAL
PASS / PARTIAL / BLOCKED

PERMISSION
PASS / PARTIAL / BLOCKED

EVIDENCE REPLAY
PASS / PARTIAL / BLOCKED

CACHE REVOKE/REGRANT
PASS / PARTIAL / BLOCKED

GOLD MANIFEST
PASS / PARTIAL / BLOCKED

OPEN BUSINESS POLICY
- ...

TECHNICAL BLOCKERS
1.
2.
3.

G1:
G2:
G3:
G4A:
G4B: NOT_APPLICABLE_YET

CONTRACT FREEZE RECOMMENDATION:
READY_FOR_CHAT_FREEZE_REVIEW
or
NOT_READY

NEXT ACTION:
...
```

Do not implement AI003.

Do not ask Antigravity to modify code unless this evaluation reproduces a concrete defect. If a defect is found, record:

```text
reproduction
expected
actual
affected contract
minimal remediation
required regression
```

and return it to ChatGPT Chat first.