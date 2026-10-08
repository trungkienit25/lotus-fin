# AI003 — CANDIDATE CONTRACT v0.2

**Status:** READY_FOR_WORK_PREBUILD_EVALUATION  
**Contract freeze:** NOT_READY  
**Basis:** AI Feature Specification v2 + Work verification summary, revision `c6f4cd1`

## 1. Product boundary

AI003 là hệ thống cảnh báo dấu hiệu tài chính, không phải hệ thống chấm điểm tín dụng hoặc kết luận gian lận.

P0 chỉ xem xét:

- AR_OVERDUE_SPIKE
- AP_DUE_CLUSTER

Các signal khác nằm ngoài phạm vi vòng đánh giá này.

Authoritative calculations phải đến từ deterministic services và các nguồn dữ liệu được xác minh. LLM chỉ có vai trò giải thích kết quả.

## 2. Common request contract

```yaml
feature_id: AI-F003
contract_version: 0.2.0-candidate

request:
  selected_signals:
    - AR_OVERDUE_SPIKE
    - AP_DUE_CLUSTER

  as_of: YYYY-MM-DD
  baseline_as_of: YYYY-MM-DD | null
```

Quy định:

- User được xác thực bằng server session.
- Company phải được server xác minh quyền truy cập.
- `as_of` là ngày cutoff kế toán, tính đến cuối ngày theo timezone kế toán đã xác minh.
- P0 sử dụng VND trên company/fixture hiện tại.
- Không cho phép đổi nhãn tiền tệ hoặc tự chuyển đổi FX.
- Finance Book khác phạm vi đã xác minh phải bị từ chối hoặc trả unsupported.
- Không hỗ trợ `as_known_at`.

Baseline AR phải được cung cấp rõ ràng và xác minh tính tương đương với current snapshot.

Không tự chọn baseline từ dữ liệu sẵn có rồi coi đó là chính sách production.

## 3. AR_OVERDUE_SPIKE

### 3.1 Financial definition

```text
AR Overdue Ratio =
Verified Overdue AR Residual
/
Verified Total AR Residual
```

Đơn vị: ratio.

Chỉ tính trên các nghĩa vụ AR hợp lệ tại accounting cutoff, sau khi xét payment allocations, credit notes và trạng thái chứng từ theo quy tắc nguồn đã xác minh.

Quy tắc ngày được đề xuất:

```text
due_date < as_of
→ overdue
```

Hóa đơn đến hạn đúng ngày `as_of` chỉ trở thành quá hạn sau ngày đó.

Nếu dùng trường overdue amount do báo cáo ERPNext cung cấp, Work phải xác minh trường này tương đương với định nghĩa trên.

### 3.2 Spike measure

```text
AR_SPIKE_PP =
(Current Overdue Ratio − Baseline Overdue Ratio)
× 100
```

Đơn vị: percentage points.

Đây là công thức đề xuất cho P0.

Không sử dụng relative percentage growth khi baseline bằng zero.

### 3.3 Baseline

Current và baseline phải có:

- cùng company;
- cùng accounting scope;
- cùng currency;
- cùng định nghĩa metric;
- cutoff hợp lệ;
- dữ liệu đầy đủ và có thể đối chiếu.

Baseline date do request cung cấp nhưng phải tuân thủ baseline policy đã được phê duyệt.

Các cutoff ngày 20/09 và 26/09/2026 hiện chỉ là một cặp quan sát phục vụ verification. Khoảng cách sáu ngày giữa chúng không tự động trở thành baseline policy.

### 3.4 Policy cần phê duyệt

```yaml
ar_rule_policy:
  baseline_policy: PENDING_APPROVAL
  warning_delta_pp: PENDING_APPROVAL
  high_delta_pp: PENDING_APPROVAL
  minimum_material_overdue_amount: PENDING_APPROVAL
  minimum_ar_denominator: PENDING_APPROVAL
  minimum_observation_count: PENDING_APPROVAL
```

Signal chỉ được kích hoạt khi metric hợp lệ và quy tắc đã được phê duyệt.

Nếu denominator bằng zero, ratio không xác định. Không được tự kết luận benign.

## 4. AP_DUE_CLUSTER

### 4.1 Financial definition

Phát hiện mức độ tập trung của những nghĩa vụ AP có ngày đến hạn hợp đồng trong một khoảng thời gian xác định.

Chỉ sử dụng nghĩa vụ AP còn hiệu lực và residual amount hợp lệ tại accounting cutoff.

Không coi ngày đến hạn hợp đồng là ngày thanh toán thực tế.

### 4.2 Proposed window

Đề xuất thử nghiệm:

```text
Short window:
as_of + 1 đến as_of + 7 ngày

Reference horizon:
as_of + 1 đến as_of + 30 ngày
```

Cả hai khoảng đều bao gồm ngày bắt đầu và ngày kết thúc.

```text
AP_DUE_CLUSTER_RATIO =

Outstanding AP due within short window
/
Outstanding AP due within reference horizon
```

Các nghĩa vụ đã quá hạn tại cutoff không nằm trong hai cửa sổ tương lai; phải được báo cáo riêng như coverage/context, không được âm thầm bỏ qua khỏi bức tranh AP tổng thể.

Nếu reference denominator bằng zero, trả `NOT_APPLICABLE` hoặc trạng thái không đủ điều kiện tính được định nghĩa rõ, không khẳng định doanh nghiệp an toàn.

### 4.3 Data requirements

Mỗi obligation phải có:

```text
verified company
unique voucher identity
valid residual amount
valid contractual due date
accounting cutoff
currency
evidence reference
```

Phải kiểm tra:

- partial payments;
- posted credit-note allocations;
- cancellation;
- duplicate vouchers;
- null due dates;
- inconsistent residual amounts.

Không trừ credit note hai lần nếu authoritative residual đã phản ánh khoản điều chỉnh đó.

Nếu source không chứng minh được các điều kiện quan trọng, signal phải chuyển thành inconclusive.

### 4.4 Policy cần phê duyệt

```yaml
ap_rule_policy:
  short_window_days: 7
  reference_horizon_days: 30

  window_policy_status: PROPOSED

  warning_cluster_ratio: PENDING_APPROVAL
  high_cluster_ratio: PENDING_APPROVAL
  minimum_material_amount: PENDING_APPROVAL
  minimum_observation_count: PENDING_APPROVAL
```

Không dùng fixture để suy ra threshold production.

## 5. Typed output contract

```yaml
feature_id: AI-F003
contract_version:
rule_version:
method_version:

request_context:
  verified_company:
  as_of:
  baseline_as_of:
  accounting_timezone:
  currency:
  finance_book_scope:
  data_mode:

provenance:
  source_snapshot_refs: []
  generated_at:
  correlation_id:

signals:
  - signal_id:
    signal_type:

    source_status:
    coverage_status:
    evaluation_status:

    finding:
    severity:

    metric:
      metric_id:
      value:
      unit:
      status:

    baseline:
      value:
      as_of:
      status:

    change:
      value:
      unit:

    rule:
      threshold_type:
      threshold:
      rule_version:

    rule_inputs:
      denominator:
      observation_count:

    evidence_refs: []
    missing_inputs: []
    limitations: []

    explanation:
      status:
      text:

    next_checks: []
```

## 6. Status semantics

### evaluation_status

```text
EVALUABLE
POLICY_PENDING
INCONCLUSIVE
NOT_APPLICABLE
```

### finding

```text
TRIGGERED
BENIGN
INCONCLUSIVE
null
```

Nếu threshold chưa được approved:

```text
evaluation_status = POLICY_PENDING
finding = null
severity = null
```

Không giả lập production verdict.

### Source/failure states

Giữ riêng:

```text
AVAILABLE
ZERO_VERIFIED
SOURCE_INVALID
SOURCE_ERROR
TIMEOUT
INCONSISTENT_DATA
FORBIDDEN
UNSUPPORTED_CUTOFF
```

Missing hoặc malformed source không được chuyển thành BENIGN.

## 7. Historical semantics

AI003 P0 hỗ trợ:

```text
posting-date cutoff
```

Không hỗ trợ:

```text
as-known-at historical reconstruction
```

Giao dịch có posting date sau cutoff không được ảnh hưởng snapshot tại cutoff.

Đối với giao dịch backdated/cancelled/corrected về sau:

- hệ thống có thể restate historical output;
- phải tạo snapshot/evidence fingerprint mới;
- không được tuyên bố tái tạo chính xác “những gì hệ thống từng biết” tại thời điểm lịch sử.

## 8. Evidence boundary

AI003 không tạo bằng chứng tài chính mới.

Mỗi signal phải giữ provenance về authoritative source:

```text
REPORT_SNAPSHOT
DOCUMENT_REF
DERIVED_METRIC
```

Evidence drilldown luôn:

```text
reauthorize current user
→ verify company/resource
→ return bounded evidence
```

Không dùng snapshot ID như authorization token.

## 9. Security boundary

Server phải thực hiện:

```text
authenticate
→ authorize company
→ authorize source/report/document
→ validate requested signal
→ validate cutoff
→ retrieve approved metrics
→ deterministic signal evaluation
→ evidence binding
→ optional explanation
```

Forbidden request trả generic `FORBIDDEN` và không để lộ sự tồn tại của resource khác company.

Không cho phép:

- arbitrary report;
- arbitrary DocType;
- arbitrary SQL;
- arbitrary URL;
- arbitrary metric ID;
- arbitrary threshold;
- arbitrary company từ prompt.

## 10. Agent boundary

P0 tool:

```text
get_risk_signals
```

Agent được:

- hiểu câu hỏi;
- chọn signal trong allowlist;
- trình bày signal đã được backend tính;
- giải thích evidence;
- đưa approved next-check IDs.

Agent không được:

- tính lại financial metric;
- đặt threshold;
- đổi severity;
- tạo signal mới;
- đổi company;
- claim fraud/default/bankruptcy;
- ghi transaction.

LLM failure:

```text
deterministic signal remains available
explanation = UNAVAILABLE
```

## 11. Acceptance matrix

Work phải tạo independent test evidence cho:

```text
POSITIVE
BENIGN near threshold
INCONCLUSIVE
legitimate empty
zero denominator
malformed row
footer/summary row
missing voucher identity
duplicate voucher
partial payment
credit adjustment
null due date
window boundary
future posting
backdate/cancellation under restatement policy
cross-company denial
report denial
document evidence denial
cache revoke/regrant
model unavailable
grounding failure
```

Gold oracle không được import AI003 production metric/rule implementation.

Mỗi case phải giữ:

```text
voucher IDs or stable hashes
source snapshot hash
cutoff
currency
timezone
expected arithmetic
expected source state
expected evaluation state
```

Nếu threshold production chưa được approve, Work chỉ kiểm chứng:

```text
numeric source gold
+
symbolic threshold boundaries
```

Không ghi production signal verdict.

## 12. Current candidate state

```text
AR_OVERDUE_SPIKE: CONDITIONAL
AP_DUE_CLUSTER: CONDITIONAL

Contract: CANDIDATE
Implementation: NOT_ALLOWED_YET
```

Candidate được coi là:

`READY_FOR_WORK_PREBUILD_EVALUATION`

Không phải:

`AI003_CONTRACT_FROZEN`