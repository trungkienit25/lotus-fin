# WORKFLOW THAM KHẢO KHI BUILD MỘT AI AGENT

**Phiên bản:** 2.0 — cập nhật bài học AI001 (2026-09-26). Giữ nguyên khung 37 mục của bản gốc; các bổ sung dưới đây áp dụng cho AI002–AI007 theo phạm vi từng feature.

> **Mục đích:** Tài liệu tham khảo end-to-end cho quá trình thiết kế, xây dựng, kiểm thử, đánh giá, triển khai và vận hành một AI Agent.  
> **Định hướng:** Production-minded, phù hợp cho Agent có tool calling, RAG, workflow nhiều bước và các bài toán có yêu cầu cao về tính đúng, bảo mật và khả năng audit.  
> **Áp dụng tốt cho Lotus Fin:** Financial Copilot / Agent sử dụng ERPNext/Frappe làm nguồn dữ liệu, deterministic finance services làm nguồn số liệu và LLM làm lớp hiểu ý định, orchestration và explanation.  
> **Nguyên tắc:** Workflow trước, code sau. Không đánh đồng "chạy được" với "đủ điều kiện release".

---

# 1. Tư duy tổng thể

Một AI Agent production không nên được build theo flow đơn giản:

```text
Idea
→ Code
→ Unit Test
→ Deploy
```

Flow nên được mở rộng thành:

```text
Problem Definition
        ↓
Runtime / Feasibility Verification
        ↓
Agent / Feature Contract
        ↓
Data Readiness
        ↓
Method / Architecture Design
        ↓
Security + Failure Design
        ↓
Observability Design
        ↓
Implementation
        ↓
Unit / Component Testing
        ↓
Integration + Security Testing
        ↓
Offline Evaluation / Benchmark
        ↓
Acceptance + Regression Gate
        ↓
Deployment
        ↓
Online Monitoring + Human Review
        ↓
Failure Analysis
        ↓
Continuous Improvement
        └──────────────────→ quay lại Design / Build
```

Xuyên suốt toàn bộ lifecycle:

```text
Logging
Tracing
Metrics
Evidence
Versioning
Debugging
Audit
```

---

# 2. Nguyên tắc nền tảng

## 2.0 Phân biệt bằng chứng, trạng thái và phạm vi claim

Mỗi tuyên bố hoàn thành phải gắn **phạm vi kiểm chứng**: `DESIGN_FROZEN`, `IMPLEMENTED`, `UNIT_VERIFIED`, `INTEGRATION_VERIFIED`, `E2E_VERIFIED`, `LIVE_PROVIDER_VERIFIED`, `RELEASED`, hoặc `BLOCKED`. Đây là các chiều bằng chứng, không phải một thang trạng thái thay thế cho `OK/PARTIAL/...` của response. Ghi rõ môi trường, phiên bản/commit, lệnh, số test, fixture/company, ngày, artifact và điều kiện còn thiếu. Mock provider chứng minh contract và failure handling; không chứng minh kết nối provider thật, latency, chi phí hay chính sách dữ liệu trên staging. Demo-ready cũng không tự động đồng nghĩa production-ready.

Với AI001, report UI ghi 67/67 test và E2E live bằng Administrator, còn report LLM ghi 60/60 và 15/15 scenario bằng mock; staging live provider vẫn `BLOCKED (NO_CREDENTIALS)`. Các con số là **hai mốc khác nhau**, không cộng thành 127 test độc lập. Khi tài liệu freeze có header lịch sử `NOT_READY_TO_CODE` nhưng checklist sau đó đánh dấu accepted, phải sửa metadata hiện hành hoặc gắn nhãn lịch sử rõ ràng. Không đánh dấu `[x]` cho gate mà bằng chứng ngay trong tài liệu còn `BLOCKED`.

## 2.0.1 Product experience là một phần của contract

Thiết kế kết quả người dùng nhìn thấy ngay từ Feature Contract: context (company, kỳ, `actual/forecast/simulation`, thời điểm chốt), số liệu, so sánh hợp lệ, bằng chứng, diễn giải, giới hạn, trạng thái lỗi và bước kiểm tra tiếp theo. Một modal một nhãn có thể che toàn bộ giá trị của backend. Chọn page/workspace hoặc UI tương đương khi tác vụ cần nhiều lớp thông tin; chỉ dùng modal cho tác vụ ngắn, đủ ngữ cảnh. UI không tự tính lại metric tài chính hay tự quyết định quyền.

## 2.1 AI không tự tạo "truth"

Nếu hệ thống có nguồn dữ liệu hoặc engine authoritative, Agent không được tự suy diễn lại các giá trị quan trọng.

Ví dụ với Lotus Fin:

```text
ERPNext/Frappe
= operational source of truth

Deterministic Finance Services
= authoritative financial computation

LLM
= intent understanding
+ tool orchestration
+ explanation
+ evidence synthesis
```

Không nên:

```text
LLM
→ tự tính gross margin
→ tự tính repayment
→ tự suy diễn cash balance
→ tự quyết định authorization
```

---

## 2.2 Actual, Forecast và Simulation phải tách biệt

```text
Actual
≠ Forecast
≠ Simulation
```

Không chỉ tách ở UI mà nên tách ở:

- data contract;
- service interface;
- Agent tool schema;
- logs;
- traces;
- evaluation;
- evidence.

---

## 2.3 Missing data không phải là zero

Sai:

```text
source error
→ []
→ 0
→ "LOW RISK"
```

Đúng:

```text
source error
→ SOURCE_ERROR

missing mandatory input
→ INSUFFICIENT_DATA

unauthorized access
→ FORBIDDEN
```

---

## 2.4 AI Agent phải observable

Monitoring trả lời:

> "Điều mình đã biết cần đo có đang ổn không?"

Observability cho phép hỏi:

> "Tại sao request X, dùng feature Y, model Z, lại chậm hoặc sai?"

AI Agent có nhiều `unknown-unknowns` hơn ứng dụng truyền thống nên observability không phải phần bổ sung sau cùng; nó là một phần của thiết kế.

---

# 3. Giai đoạn 0 — Runtime / Feasibility Verification

## Mục tiêu

Không thiết kế feature dựa trên giả định về environment, data hoặc permission.

Trước khi code, cần xác minh:

```text
Runtime
Dependencies
Data source
Schemas
Permissions
Tool/API availability
Model availability
External dependency behavior
```

## Checklist

- runtime/framework version;
- installed modules/apps;
- API/report/tool nào thực sự chạy được;
- input/output schema thực tế;
- authentication/authorization behavior;
- tenant/company scope;
- source of truth;
- rate limits;
- model/provider availability;
- required credentials có tồn tại nhưng không log secret;
- required data có đủ hay không;
- dependency nào vẫn `NOT_VERIFIED`.

## Output nên có

```text
RUNTIME_FACTS.md
```

Ví dụ:

```yaml
runtime:
  framework: verified
  database: verified
  llm_provider: verified

data_sources:
  invoices: VERIFIED
  payments: VERIFIED
  opening_cash: NOT_VERIFIED
  payroll: NOT_AVAILABLE

permissions:
  cross_company_test: NOT_VERIFIED
```

## Stop condition

Nếu một runtime fact bắt buộc chưa được xác minh:

```text
STOP
→ mark NOT_VERIFIED
→ không tự bịa schema hoặc permission behavior
```

---

# 4. Giai đoạn 1 — Problem Definition

Trước khi nói đến model hay prompt, phải xác định bài toán.

## 4.1 Câu hỏi cần trả lời

- User là ai?
- User đang cố hoàn thành việc gì?
- Agent giúp ở bước nào?
- Nếu Agent sai thì hậu quả là gì?
- Output nào thật sự cần?
- Output nào tuyệt đối không được tự quyết định?
- Có cần Agent không hay deterministic workflow là đủ?

## 4.2 Problem statement template

```yaml
problem:
  user:
  business_goal:
  user_question:
  current_pain:
  agent_role:
  non_goals:
  high_risk_outputs:
```

Ví dụ:

```yaml
agent_role:
  - understand user question
  - select approved finance tool
  - synthesize evidence
  - explain result

non_goals:
  - post accounting transaction
  - approve credit
  - move money
  - invent financial numbers
```

---

# 5. Giai đoạn 2 — Agent / Feature Contract

## 5.0 Contract phải gồm cả presentation

Chốt request/output envelope, phiên bản contract, các enum trạng thái tổng và từng metric, `snapshot_id`, `EvidenceRef`, `missing_inputs`, `limitations`, comparison, explanation và cách UI hiển thị mỗi trạng thái. Ghi user journey theo đúng đơn vị phân tích: company-level AI001 khác invoice-level credit risk. Freeze metric, công thức, thời hạn/horizon, period mode và danh sách next-check/report allowlist trước khi tạo thẻ KPI hoặc biểu đồ. Nếu thiếu prior period, trình bày `UNAVAILABLE` thay cho trend; nếu model lỗi, giữ phần deterministic có chứng cứ.

Đây là "hợp đồng kỹ thuật" trước implementation.

## Contract mẫu

```yaml
feature_id: AGENT-F001

goal:
  description:

inputs:
  required: []
  optional: []

outputs:
  schema:

computation_class:
  DETERMINISTIC | STATISTICAL | ML_PREDICTIVE |
  LLM_ORCHESTRATION | LLM_EXPLANATION | HYBRID

tools:
  allowed: []

failure_states:
  - INSUFFICIENT_DATA
  - SOURCE_ERROR
  - VALIDATION_ERROR
  - FORBIDDEN
  - MODEL_UNAVAILABLE

evidence:
  required: true

security:
  authorization_boundary:
  tenant_scope:

evaluation:
  metrics:
  benchmark:
  pass_threshold:

observability:
  logs:
  traces:
  metrics:
```

## Gate

Không chuyển sang Build nếu chưa freeze tối thiểu:

```text
Input
Output
Tool boundary
Failure behavior
Security boundary
Evaluation criteria
```

---

# 6. Giai đoạn 3 — Data Readiness

## 6.0 Provenance trước khi tính

Lập source map cho từng company/site: report/DocType, quyền, schema thực tế, sign, cutoff, currency, Finance Book, độ phủ, trust state, data mode và phiên bản chuyển đổi. Report là read projection cần đối soát với sổ; tên report trong tài liệu chưa chứng minh runtime. Ghi `source_kind` và môi trường cho observed/synthetic. Dữ liệu synthetic chỉ dùng cho fixture test/demo được gắn nhãn và có manifest/seed/gold độc lập; không bù vào kết quả actual production khi source thiếu. Mỗi KPI cần định nghĩa verified zero, missing và source error riêng.

AI Agent tốt không cứu được data sai hoặc data thiếu.

## 6.1 Xác định data theo 4 lớp

```text
Source
↓
Trust
↓
Semantics
↓
Freshness
```

### Source

```text
observed
derived
synthetic
user_entered
```

### Trust

```text
raw
candidate
trusted
rejected
```

### Mode

```text
actual
forecast
simulation
```

## 6.2 Data readiness checklist

- nguồn ở đâu;
- ai sở hữu nguồn;
- schema đã verify chưa;
- field nào mandatory;
- missing-value semantics;
- business date vs due date vs settlement date;
- currency;
- timezone;
- freshness / TTL;
- provenance;
- data có permission scope đúng không;
- dữ liệu synthetic có bị lẫn với observed không;
- có temporal leakage không nếu dùng ML;
- có đủ historical labels không.

## 6.3 Readiness states

```text
READY
PARTIAL
NOT_READY
BLOCKED
```

## 6.4 Data Gate

Nếu feature cần 5 nguồn nhưng 2 nguồn mandatory chưa tồn tại:

```text
không "mock rồi gọi là production"
```

Có thể:

```text
A. giảm scope feature
B. trả INSUFFICIENT_DATA
C. dùng assumption nhưng phải explicit
D. chuyển feature sang P1
```

---

# 7. Giai đoạn 4 — Method / Architecture Design

Chỉ sau khi biết data thực sự có gì mới chọn phương pháp.

## 7.1 Chọn loại intelligence

```text
Rule / Deterministic
Statistical
ML Predictive
Retrieval
LLM
Agentic workflow
Hybrid
```

## Nguyên tắc

> Không thêm ML chỉ để feature "trông giống AI".

## 7.2 Với Agent

Xác định:

```text
User Input
  ↓
Intent / Router
  ↓
Policy / Authorization
  ↓
Tool Selection
  ↓
Tool Execution
  ↓
Evidence Collection
  ↓
Answer Synthesis
  ↓
Output Validation
```

## 7.3 Tool contract

Mỗi tool nên typed và bounded:

```yaml
tool:
  name: get_financial_health

subject:
  user_id:
  tenant_or_company:

input:
  period:
  as_of:

output:
  status:
  result:
  evidence_refs:
  limitations:

version:
  tool_version:
```

Agent không được:

- gọi raw SQL;
- chọn arbitrary URL;
- chọn arbitrary report;
- tự tăng permission;
- tự đổi tenant/company scope;
- gọi hidden tool không nằm trong allowlist.

---

# 8. Giai đoạn 5 — Security & Failure Design

## 8.0 Bài học AI001: thứ tự kiểm soát và ma trận lỗi

Thiết kế và kiểm thử flow server: `authenticate → authorize company → authorize report/resource → validate request và filter → read scoped sources → snapshot/evidence → deterministic compute → optional LLM → validate output → audit`. Danh sách company/role trên giao diện chỉ hỗ trợ UX; server luôn lấy user từ session, không tin `company`, report name, URL, filter hay resource ID do client/model gửi. Kiểm tra cross-company cả đường chính, filter sửa tay, report drill-down, cache/job và thông báo lỗi. Allowlist report/tool và output cap; không dùng permission bypass. Với feature chỉ đọc, nút next-check chỉ điều hướng đến nguồn đã duyệt, không kích hoạt ghi sổ, thanh toán hay phê duyệt.

Đóng băng ma trận từ `source result → metric status → aggregate status → explanation status → UI state`. Phân biệt verified zero, empty hợp lệ, missing field, corrupt/inconsistent rows, permission denial, source exception/timeout, prior-period unavailable, model 429/5xx/timeout/schema error và grounding failure. Lỗi nguồn không biến thành mảng rỗng hoặc zero. Metric độc lập còn bằng chứng có thể giữ `AVAILABLE`; phần phụ thuộc chuyển `UNAVAILABLE` và nêu limitation. `FORBIDDEN` không để lộ sự tồn tại của company/resource. `MODEL_UNAVAILABLE` chỉ hạ cấp phần explanation khi KPI vẫn hợp lệ. Không biến `PARTIAL` thành câu kết luận sức khỏe đầy đủ.

## 8.0.1 Checklist edge cases cho finance backend

- Report schema và sign có thể khác theo site, company, chart of accounts, Finance Book, accounting dimension, currency và version; xác nhận bằng runtime, không hard-code demo company. Reconcile P&L, AR, AP, Trial Balance/GL theo định nghĩa đã freeze.
- Xử lý report summary/total rows, duplicate rows, dict/list mixed rows, null, bản ghi chưa submit/cancelled, credit note, partial payment và payment allocation. Không tự sửa dữ liệu mâu thuẫn để có số đẹp.
- Dùng Decimal/minor units cho tiền; chốt precision/rounding. Revenue/AR denominator bằng 0 làm ratio/relative change `UNAVAILABLE`, không `Infinity`/0 giả. Giữ cash âm và metric âm hợp lệ nếu nguồn xác nhận.
- Tách `financial_as_of` khỏi `retrieved_at`; effective cutoff phải nhất quán giữa P&L, AR, AP, TB. So sánh kỳ phải cùng company, độ dài, currency, Finance Book, accounting context, công thức và source semantics; kỳ trước thiếu không làm hỏng kỳ hiện tại.
- `EvidenceRef` phải khớp report/filter thực thi, company, kỳ/as-of, retrieved_at, snapshot/formula version và checksum; metric dẫn xuất tham chiếu đủ nguồn của các input. Không tạo evidence giả.
- Near-term AP, score, DSCR, runway hay causal claim chỉ bật khi horizon/định nghĩa, source và gold đã freeze. AI001 để near-term AP `UNAVAILABLE`; không suy cash từ `AR - AP`.

Security phải được thiết kế trước code, không phải "test thêm sau".

## 8.1 Security flow

```text
Authenticate
    ↓
Resolve allowed tenant/company/resource
    ↓
Validate requested scope
    ↓
Check resource permission
    ↓
Validate input/schema/bounds
    ↓
Execute tool
```

## 8.2 Threats nên xem xét

- prompt injection;
- indirect prompt injection;
- tool abuse;
- arbitrary URL/tool selection;
- cross-tenant data access;
- PII leakage;
- secret leakage;
- output injection/XSS;
- CSV formula injection;
- data poisoning;
- RAG poisoning;
- hallucinated actions;
- unauthorized side effects;
- model output parsing failure.

## 8.3 Failure contract

Các lỗi nên typed:

```text
OK
INSUFFICIENT_DATA
FORBIDDEN
SOURCE_ERROR
VALIDATION_ERROR
MODEL_ERROR
TOOL_ERROR
TIMEOUT
RATE_LIMITED
```

Không nên:

```python
try:
    ...
except Exception:
    return []
```

---

# 9. Giai đoạn 6 — Observability Design

## 9.0 Telemetry phải theo request nhưng không theo dữ liệu nhạy cảm

Tạo `correlation_id` từ server và truyền qua auth, từng report adapter, snapshot, metric/comparison, LLM, response/UI. Log có cấu trúc: feature/contract/formula/prompt/model version khi áp dụng, status, error class, source type, duration, snapshot ID và danh tính giả danh. Đo request, authorization denial, source error, partial/unavailable, grounding failure, latency, model tokens/cost bằng nhãn cardinality thấp. Không log raw report rows, số tiền/PII mặc định, credential, raw prompt hoặc chain-of-thought. Kiểm redaction bằng canary; kiểm event success/deny/source/model failure. Dashboard/alert phải có owner và runbook; threshold SLO chỉ đóng băng sau khi đo baseline, không tự claim từ test mock.

Observability nên được freeze cùng feature contract.

## 9.1 Ba pillars

### Metrics

Trả lời:

```text
Bao nhiêu?
Bao lâu?
Bao nhiêu lỗi?
Tốn bao nhiêu?
```

### Logs

Trả lời:

```text
Sự kiện gì đã xảy ra?
```

### Traces

Trả lời:

```text
Request đã đi qua những bước nào?
Bottleneck nằm ở đâu?
```

Mental model:

```text
Metrics → detect
Traces  → localize
Logs    → root cause
```

---

# 10. Logging Design

## 10.1 Structured logging

Production log nên là structured JSON, không phải text tùy ý.

### Tier 1 — Required

Mỗi entry:

```yaml
ts:
level:
correlation_id:
service:
event_type:
```

### Tier 2 — Context

Khi liên quan:

```yaml
user_id_hash:
session_id:
feature:
model:
environment:
tenant_or_company:
```

### Tier 3 — Payload / Event metrics

```yaml
latency_ms:
tokens_in:
tokens_out:
cost_usd:
error_type:
tool_name:
tool_version:
model_version:
status:
```

Nên có JSON Schema/Pydantic model để validate format trước emit.

---

## 10.2 Correlation ID

Một request end-to-end dùng cùng `correlation_id`.

Ví dụ:

```text
HTTP Request
 correlation_id = abc123
       ↓
Agent Router
       ↓
Retriever
       ↓
Finance Tool
       ↓
LLM
       ↓
Response
```

Mục tiêu:

```text
1 request
→ truy ra toàn bộ event + trace + error
```

---

## 10.3 PII sanitization

### Nên log

- sanitized input metadata;
- topic/category;
- input length;
- output summary;
- tool metadata;
- latency;
- tokens;
- cost;
- error type;
- correlation ID;
- hashed/pseudonymous user ID.

### Không log mặc định

- full raw user input;
- full prompt chứa sensitive data;
- tên/phone/email/ID cá nhân;
- bank account;
- card number;
- API key;
- access token;
- password;
- full financial documents;
- raw chain-of-thought;
- verbose debug payload ở production.

Nguyên tắc:

```text
sanitize before log
```

không phải:

```text
log trước
→ xóa sau
```

---

## 10.4 Log levels

```text
INFO
WARN
ERROR
```

Gợi ý:

```text
INFO
- request completed
- tool success
- model call success

WARN
- fallback used
- retry
- partial data
- stale source
- near rate limit

ERROR
- source failure
- tool exception
- permission failure
- model failure
- schema validation failure
```

Không biến mọi thứ thành ERROR.

---

# 11. Tracing Design

AI Agent nhiều bước cần distributed tracing.

## Một trace điển hình

```text
agent_request
├── auth
├── intent_router
├── retrieval
│   ├── query_rewrite
│   └── vector_search
├── tool_call:get_financial_health
│   ├── permission_check
│   ├── source_read
│   └── deterministic_compute
├── llm_synthesis
└── output_validation
```

## Span nên capture

```yaml
span_name:
start_time:
duration_ms:
status:
model:
tool:
tokens:
cost:
error_type:
```

Không capture raw secret/PII chỉ để trace "đầy đủ".

---

# 12. Metrics Design

## 12.1 Four Golden Signals

```text
1. Latency
2. Traffic
3. Errors
4. Saturation
```

## 12.2 AI-specific signals

Thêm:

```text
5. Cost
6. Quality
```

Một Agent có thể:

```text
UP
latency OK
error rate OK
```

nhưng vẫn:

```text
hallucinate
retrieve sai
tốn token quá mức
```

---

## 12.3 Performance metrics

- end-to-end latency;
- P50/P95/P99;
- TTFT;
- TPOT;
- tokens/sec;
- throughput;
- queue depth;
- uptime;
- context fill %.

P95/P99 quan trọng hơn average đối với trải nghiệm tail latency.

---

## 12.4 Cost metrics

- input tokens/request;
- output tokens/request;
- cost/request;
- cost/user/day;
- cost/feature;
- cost/model;
- retry cost;
- tool/API cost.

---

## 12.5 Quality metrics

Tùy Agent:

- task completion;
- groundedness;
- hallucination rate;
- citation correctness;
- human thumbs up/down;
- user satisfaction;
- tool-call success;
- fallback rate;
- refusal correctness.

---

## 12.6 Cardinality rule

Không dùng high-cardinality values làm metric label:

```text
NO:
user_id
email
request_id
correlation_id
```

Nên dùng:

```text
model
environment
feature
status
tier
```

High-cardinality data:

```text
→ logs / traces
```

---

# 13. SLI / SLO / Alert Design

## 13.1 Khái niệm

```text
SLI = metric đo được
SLO = mục tiêu nội bộ cho SLI
SLA = cam kết bên ngoài
```

## Ví dụ

```yaml
latency_slo:
  indicator: p95_latency
  target: "<= 3s"

error_slo:
  indicator: successful_request_rate
  target: ">= 99%"

cost_slo:
  indicator: daily_agent_cost
  target: "<= configured_budget"
```

## 13.2 Alert nên symptom-based

Tốt:

```text
P95 latency > threshold trong N phút
error rate > threshold
cost/day > budget
tool failure rate > threshold
quality score giảm bất thường
```

Kém:

```text
CPU > 70%
```

nếu user vẫn không bị ảnh hưởng.

## 13.3 Mỗi alert nên có runbook

```yaml
alert:
  name:
  condition:
  severity:
  owner:
  dashboard:
  trace_query:
  runbook:
  rollback_or_fallback:
```

---

# 14. Giai đoạn 7 — Implementation

## 14.0 Hai đường build cần gặp nhau

Backend: secure adapter → immutable/traceable snapshot → deterministic metric/comparison → minimized grounded explanation → typed response. Frontend: native framework/page hiện có → context/filter có quyền → KPI và availability → comparison → facts/interpretations/limitations/next checks → evidence và nguồn được duyệt. Kiểm API contract bằng cùng fixture; frontend chỉ format số/ngày/tiền, không tính lại số tài chính. Escape mọi text untrusted kể cả output model, nhãn report/source; tránh XSS và CSV formula injection nếu export. Kiểm cache theo company + quyền + kỳ + version; đổi company/kỳ phải xóa dữ liệu cũ ngay và tránh race response cũ đè kết quả mới.

Thiết kế loading/empty/error như trạng thái sản phẩm: skeleton ngắn, không dựng tiến độ giả; company rỗng không hiện zero đại trà; lỗi nguồn hiển thị thông báo an toàn thay vì raw exception/modal nội bộ. Không nuốt lỗi rồi chỉ đổi giao diện: server vẫn phát event/error class để vận hành điều tra.

Sau khi các gate trước đã pass mới code.

## Coding principles

- small, reviewable change;
- typed interfaces;
- no hidden permission bypass;
- deterministic arithmetic cho material number;
- feature flags khi cần;
- dependency timeout/retry rõ ràng;
- idempotency nếu có side effect;
- version prompt/tool/model/schema.

## Trong quá trình build

Observability không để tới cuối.

Mỗi major component nên có:

```text
logs
trace spans
metrics hooks
typed errors
```

---

# 15. Giai đoạn 8 — Unit / Component Testing

## Test logic cục bộ

Ví dụ:

- schema parsing;
- tool input validation;
- calculator;
- finance formula;
- retry logic;
- permission helper;
- prompt formatter;
- result validator.

## Minimum paths

```text
happy path
missing data
invalid input
source error
timeout
boundary values
numeric gold test
```

---

# 16. Giai đoạn 9 — Integration + Security Testing

## 16.0 UI/E2E acceptance matrix

Chạy browser E2E trên route thật, kiểm login, quyền page, company được phép, period/comparison, KPI và negative number, prior period thiếu/zero denominator, drawer evidence, next-check allowlist, empty company, `PARTIAL`, source timeout/error, explanation unavailable, XSS canary và chuyển company nhanh. Lưu screenshot/video để xem nội dung người dùng thực sự thấy; assert DOM và response thay vì chỉ chụp ảnh. Test bằng Administrator chứng minh happy path, **không chứng minh** role `Accounts User`/`Accounts Manager` hoặc cross-company isolation; thêm ít nhất một user được phép và một user bị từ chối trong integration/E2E. Kiểm UI không giữ lại dữ liệu của company trước sau `FORBIDDEN`.

Unit test pass chưa có nghĩa Agent đúng.

## Integration

Test:

```text
Agent
→ tool
→ source
→ result
→ evidence
→ final answer
```

## Security tests

- unauthorized user;
- cross-tenant request;
- malicious company/resource ID;
- prompt injection;
- indirect injection;
- arbitrary URL;
- arbitrary tool;
- PII canary;
- XSS canary;
- malicious retrieved document;
- tool result containing adversarial instructions.

## Expected

```text
Authorization luôn được server quyết định.
```

LLM output không thể override policy.

---

# 17. Giai đoạn 10 — Offline Evaluation / Benchmark

## 17.0 Grounded explanation gate học từ AI001

Model chỉ nhận payload tối thiểu từ KPI/evidence/limitations đã xác thực. Output có schema tách `facts`, `interpretations`, `next_checks`, trạng thái; mọi con số material trong văn bản phải đối soát với snapshot/period/currency và evidence. Chặn số bịa, claim nhân quả thiếu Cash Flow/GL, prompt injection trong source text và HTML/script output. Provider 429/5xx/timeout, JSON sai, schema sai hoặc grounding fail → explanation `UNAVAILABLE`; deterministic metrics không bị sửa. Test unit bằng mock và fault injection, eval scenarios có normal/edge/missing/adversarial; staging smoke với provider thật là gate riêng về credential, data handling, latency, cost và schema. Nếu gate đó bị chặn, ghi `BLOCKED` đúng chỗ, không chuyển thành release verification.

Evaluation là engineering discipline, không phải:

> "Mình cảm thấy Agent trả lời khá tốt."

## 17.1 Golden dataset

Tạo bộ test representative:

```text
normal cases
edge cases
failure cases
adversarial cases
high-risk cases
```

Mỗi item:

```yaml
id:
question:
context:
expected_answer:
expected_tool:
expected_evidence:
risk_level:
category:
```

## 17.2 Output quality dimensions

Ít nhất xem:

```text
Correctness
Relevance
Completeness
Coherence
```

## 17.3 Agent metrics

Có thể gồm:

```text
Task completion
Partial completion
Weighted critical-step score
Trajectory correctness
Tool selection accuracy
Tool argument correctness
Citation accuracy
```

Agent nhiều bước nên đánh giá **trajectory**, không chỉ final answer.

---

# 18. RAG Evaluation

Nếu Agent dùng RAG, có thể đo:

```text
Context Recall
Context Precision
Faithfulness
Answer Relevancy
```

Interpretation:

```text
Context Recall thấp
→ retrieval thiếu evidence

Context Precision thấp
→ retrieval nhiều noise

Faithfulness thấp
→ answer không grounded vào context

Answer Relevancy thấp
→ trả lời lệch câu hỏi
```

Lưu ý:

```text
Faithfulness cao
≠ factual truth chắc chắn đúng
```

Nếu source/context sai, answer có thể vẫn "faithful".

---

# 19. LLM-as-Judge

Dùng khi output open-ended và cần nhiều tiêu chí.

## Rubric mẫu

```text
1 = unacceptable
2 = weak
3 = acceptable
4 = good
5 = excellent
```

Có thể chấm:

- correctness;
- relevance;
- completeness;
- groundedness;
- clarity;
- safety.

## Nguyên tắc

- rubric cụ thể;
- không dùng một câu "is this good?";
- calibrate với human examples;
- lưu judge model/version;
- không coi judge là absolute truth.

---

# 20. Human Evaluation

Một Agent high-stakes không nên chỉ dựa vào auto-eval.

Có thể dùng:

```text
Offline automated eval
+
Online production sampling
+
Human expert review
```

### Khi nào dùng human review

- trước demo/launch;
- weekly sampled outputs;
- high-risk use case;
- khi benchmark score drift;
- khi thay model/prompt/tool lớn.

---

# 21. Regression Gate

Mỗi thay đổi có thể phá hành vi cũ.

## Trigger

### Code change

```text
→ offline full suite
```

### Prompt change

```text
→ targeted regression
```

### Model change

```text
→ full benchmark
```

### Embedding / retrieval change

```text
→ RAG regression
```

### Tool schema change

```text
→ tool + integration regression
```

## Rule

```text
Agent không pass required eval
→ không deploy
```

Eval gate nên được xem giống unit-test gate trong CI/CD.

---

# 22. Giai đoạn 11 — Acceptance

## 22.0 Acceptance có cả mắt người dùng và provenance

Review một luồng demo thực tế theo đúng feature: người dùng thấy company, kỳ, mode, KPI, so sánh, facts, interpretations, limitations, next checks và đường mở evidence. Kiểm “số này đến từ đâu?”, “kỳ trước có đủ không?”, “AI đang suy luận điều gì?” và “lỗi model/source thì còn gì dùng được?”. UI không cần thêm chart/score để trông phức tạp; chỉ trình bày intelligence có thật. Sign-off phải ghi rõ các cột `verified`, `partial`, `not verified`, `blocked` theo môi trường và acceptance owner.

Definition of Done nên là:

```text
CODE COMPLETE
    ↓
UNIT PASS
    ↓
INTEGRATION PASS
    ↓
SECURITY PASS
    ↓
OFFLINE EVAL PASS
    ↓
REGRESSION PASS
    ↓
OBSERVABILITY READY
    ↓
RUNBOOK READY
    ↓
RELEASE APPROVED
```

Không nên:

```text
"demo chạy được"
= DONE
```

---

# 23. Giai đoạn 12 — Deployment

## 23.0 Git và release discipline

Làm việc trên feature branch có tên rõ, diff nhỏ, commit theo workstream và liên kết report/gold/artifact với commit SHA. Trước merge: review thay đổi backend, UI, quyền, schema, prompt/model config và docs; chạy regression thích hợp trên revision cuối; xác nhận migration/build assets, route/role, feature flag và rollback. Ghi release notes gồm thay đổi hành vi, limitations, evidence kiểm thử, provider đang dùng và gate còn blocked. “Đã push branch” không đồng nghĩa “đã merge/deploy”; “demo-ready” không đồng nghĩa “production released”. Sau deploy, chạy smoke bằng role người dùng thật, kiểm telemetry và fallback, rồi ghi thời gian/owner/kết quả. Không đánh dấu gate pass chỉ dựa vào completion report chưa đối chiếu artifact hoặc runtime.

Deploy nên có:

- versioned Agent configuration;
- model version;
- prompt version;
- tool version;
- feature flag;
- rollback path;
- dashboards ready;
- alerts ready;
- runbooks ready;
- cost limit/budget;
- safe fallback.

## Production startup checklist

```text
[ ] logs visible
[ ] traces visible
[ ] metrics visible
[ ] correlation ID propagated
[ ] alert test successful
[ ] PII redaction verified
[ ] model/tool version tags present
[ ] cost monitoring enabled
[ ] eval baseline stored
```

---

# 24. Giai đoạn 13 — Online Monitoring

Offline eval không cho biết production traffic đang làm gì.

## Theo dõi liên tục

### Reliability

```text
request rate
error rate
P95/P99 latency
timeout
availability
```

### AI quality

```text
user feedback
groundedness sample
tool-call failure
hallucination heuristic
fallback rate
```

### Cost

```text
tokens/request
$/request
$/user
$/feature
daily budget
```

### Drift

```text
input distribution
query type
retrieval score
tool-use distribution
quality trend
cost trend
```

---

# 25. Dashboard 3 lớp

## Layer 1 — Executive / Product

```text
traffic
success rate
quality
cost
user satisfaction
```

## Layer 2 — Engineering / Agent

```text
P50/P95/P99 latency
LLM latency
tool latency
error types
tokens
cost
quality score
```

## Layer 3 — Debug / Trace

```text
request trace
tool spans
retrieval spans
model calls
error logs
correlation ID
```

---

# 26. Failure Analysis

Không fix bằng cảm tính.

Workflow:

```text
Failure
  ↓
Reproduce
  ↓
Find trace
  ↓
Inspect logs
  ↓
Classify failure
  ↓
Root cause
  ↓
Fix
  ↓
Regression test
  ↓
Benchmark
```

## Root-cause classes

- data;
- retrieval;
- prompt;
- model;
- tool;
- schema;
- permission;
- business logic;
- latency;
- provider;
- UI/output handling.

## 5 Whys

Với worst cases:

```text
Why 1?
Why 2?
Why 3?
Why 4?
Why 5?
→ root cause
```

---

# 27. Continuous Improvement Loop

```text
Observe
  ↓
Measure
  ↓
Analyze
  ↓
Prioritize
  ↓
Fix
  ↓
Evaluate
  ↓
Deploy
  ↓
Observe
```

Evaluation phải:

```text
reproducible
comparable
automatable
```

Mỗi improvement item nên có:

```yaml
issue:
root_cause:
impact:
proposed_fix:
owner:
priority:
benchmark_case:
status:
```

---

# 28. Monitoring vs Evaluation

Hai phần này liên quan nhưng không giống nhau.

## Monitoring

Hỏi:

```text
Agent đang vận hành như thế nào?
```

Ví dụ:

- latency;
- error;
- cost;
- traffic;
- availability.

## Evaluation

Hỏi:

```text
Agent có làm đúng nhiệm vụ không?
```

Ví dụ:

- correctness;
- task completion;
- faithfulness;
- relevance;
- safety;
- trajectory quality.

## Production AI cần cả hai

```text
Monitoring
+
Evaluation
+
Human Review
```

---

# 29. Debugging workflow khuyến nghị

Khi user báo:

> "Agent trả lời sai/chậm."

Không debug từ code ngay.

## Flow

```text
1. lấy correlation_id
        ↓
2. xem request trace
        ↓
3. xác định span chậm/sai
        ↓
4. xem log tương ứng
        ↓
5. check data/tool/model version
        ↓
6. reproduce bằng test case
        ↓
7. classify root cause
        ↓
8. fix
        ↓
9. thêm regression case
        ↓
10. chạy benchmark lại
```

---

# 30. Reference architecture — AI Agent production-minded

```text
User
 │
 ▼
API / UI
 │
 ▼
Authentication
 │
 ▼
Authorization / Tenant Guard
 │
 ▼
Agent Orchestrator
 │
 ├─────────────► Retrieval
 │
 ├─────────────► Typed Tools
 │
 ├─────────────► Deterministic Services
 │
 └─────────────► External Approved APIs
 │
 ▼
Evidence / Tool Results
 │
 ▼
LLM Synthesis
 │
 ▼
Output Validation
 │
 ▼
User

       │
       ├────────► Structured Logs
       ├────────► Distributed Traces
       ├────────► Metrics
       ├────────► Cost Tracking
       └────────► Audit Events
```

---

# 31. Workflow rút gọn để dùng hàng ngày

**Bổ sung khi áp dụng checklist:** giữa Contract và Build phải có UX contract (người dùng thấy được gì, evidence ở đâu, từng lỗi hiển thị thế nào). Giữa Integration và Acceptance phải có UI/E2E bằng role thật, kiểm accessibility cơ bản và trạng thái không có dữ liệu/model. Sau Acceptance phải có docs consistency review, Git/release evidence và smoke trên môi trường mục tiêu. RAG evaluation, tool orchestration và LLM-as-Judge ở §§18–20 chỉ áp dụng khi feature thật sự dùng chúng; không thêm RAG/agent framework để đủ checklist.

Khi build một feature/agent mới, có thể dùng checklist này:

```text
01. Problem
02. Runtime Verify
03. Contract
04. Data
05. Method
06. Security
07. Failure Modes
08. Observability
09. Build
10. Unit Test
11. Integration Test
12. Security Test
13. Offline Eval
14. Regression
15. Acceptance
16. Deploy
17. Monitor
18. Human Review
19. Failure Analysis
20. Improve
```

---

# 32. Four Gates trước khi coding agent được phép code

Đặc biệt hữu ích nếu dùng Antigravity / Gemini / Copilot / Claude Code.

## Gate 1 — Runtime Gate

```text
Các dependency/source/schema có thật không?
```

## Gate 2 — Contract Gate

```text
Input/output/failure/tool scope đã rõ chưa?
```

## Gate 3 — Data & Method Gate

```text
Data đủ chưa?
Phương pháp tính/suy luận đã freeze chưa?
```

## Gate 4 — Security & Evaluation Gate

```text
Permission boundary?
Threats?
Acceptance metrics?
Benchmark?
```

Pass đủ 4 gate:

```text
→ giao task implementation cho coding agent
```

---

# 33. Definition of Ready

**Bổ sung DoR từ AI001:** `[ ]` unit phân tích (company/invoice/transaction) và route UI được chốt; `[ ]` metric/horizon/formula/as-of/currency/evidence cùng verified-zero/missing/error được freeze; `[ ]` ma trận role/company và allowlist report được thử trên runtime; `[ ]` UI states và acceptance journey được mô tả; `[ ]` provider credential/data policy và staging plan được xác nhận hoặc tách thành gate `BLOCKED` rõ ràng; `[ ]` fixture/gold độc lập có provenance. Gate build có thể pass với phần optional đã freeze `UNAVAILABLE`; không được đánh dấu pass cho dependency bắt buộc còn blocked.

Một Agent feature được xem là **READY TO BUILD** khi:

```text
[ ] problem rõ
[ ] runtime facts đủ
[ ] input/output contract rõ
[ ] data sources verified
[ ] missing-data behavior rõ
[ ] method/algorithm rõ
[ ] tool allowlist rõ
[ ] security boundary rõ
[ ] failure states typed
[ ] observability plan rõ
[ ] benchmark/eval criteria rõ
```

---

# 34. Definition of Done

**Bổ sung DoD theo phạm vi release:** `[ ]` report edge cases/Decimal/cutoff/comparison/evidence pass; `[ ]` authn/authz/cross-company và report guard pass bằng non-admin roles; `[ ]` explanation schema, numeric grounding, injection và provider-failure fallback pass; `[ ]` E2E xác nhận UI value, evidence, empty/partial/error/model-unavailable, safe navigation; `[ ]` telemetry/redaction và correlation được kiểm; `[ ]` docs/freeze/report đồng bộ; `[ ]` branch/commit/build/deploy/rollback và staging provider smoke (nếu cần cho release) có evidence. Nếu thiếu một gate bắt buộc, ghi `PARTIAL` hoặc `BLOCKED` cho đúng phạm vi; không dùng 100% test pass để thay gate chưa chạy.

Một Agent feature được xem là **DONE** khi:

```text
[ ] code reviewed
[ ] unit tests pass
[ ] integration tests pass
[ ] security tests pass
[ ] benchmark pass
[ ] regression pass
[ ] logging structured
[ ] correlation ID works
[ ] traces visible
[ ] metrics/dashboard available
[ ] PII sanitization verified
[ ] alerts configured
[ ] runbook exists
[ ] rollback/fallback exists
[ ] versions recorded
```

---

# 35. Gợi ý áp dụng cho Lotus Fin

## 35.0 Mẫu tái sử dụng AI001 cho AI002–AI007

| Lớp | Tái sử dụng | Phải freeze lại cho từng feature |
|---|---|---|
| Runtime/data | secure adapter, source map, EvidenceRef, status/availability, correlation | report/DocType, schema, reconciliation, as-of, currency, company/role |
| Computation | Decimal, gold độc lập, snapshot và failure matrix | forecast/score/detection method, horizon, thresholds, ground truth |
| AI | payload minimization, schema, grounding, injection tests, graceful fallback | model purpose, allowed claims, rubric, provider/data policy |
| Product | page/workspace pattern, facts vs interpretations vs limitations, evidence drawer | user journey, unit phân tích, next checks, UI states, read/write action level |
| Delivery | layered tests, E2E, docs evidence, feature branch, rollback | fixture, acceptance owner, staging/live gate, release decision |

AI002–AI007 có thể khác computation class và risk level; không sao chép metric hay UI AI001 một cách máy móc. Nếu feature có write action, thiết kế authorization, confirmation, idempotency, audit và rollback riêng trước code. Nếu feature không dùng LLM hoặc RAG, bỏ gate không áp dụng và ghi lý do.

Với Lotus Fin, mỗi AI-F001 → AI-F007 nên đi qua lifecycle trên.

Ví dụ:

```text
AI-F002 Cash-flow Forecast
        ↓
Runtime Verification
        ↓
Verify:
opening cash
AR due date
AP due date
settlements
known obligations
        ↓
Data Readiness
        ↓
Deterministic Forecast Method
        ↓
Security / Company Scope
        ↓
Observability Contract
        ↓
Build
        ↓
Gold Numeric Tests
        ↓
Integration/Security Tests
        ↓
Forecast Evaluation
        ↓
Regression
        ↓
Release
```

Copilot sau đó chỉ consume typed results:

```text
FinancialSnapshot
        ↓
Finance Services
        ↓
Typed Tools
        ↓
Financial Copilot
```

Không nên:

```text
LLM
→ đọc DB trực tiếp
→ tự tính financial number
→ tự quyết định quyền
```

---

# 36. Tài liệu nguồn đã tham khảo

**Nguồn bài học AI001 cho phiên bản 2.0:** `AI001_Productization_UI_Completion_Report.md` (2026-09-26), `AI001_LLM_Explanation_Completion_Report.md` (2026-09-25), `AI001_Feature_Freeze_VI.md` và `AI001_MASTER_FEATURE_DOCUMENT_VI.md`. Các report/freeze là bằng chứng và quyết định của dự án tại thời điểm ghi, không thay cho việc kiểm code/runtime của AI002–AI007. Các mốc 60/60, 67/67, 15/15 và E2E được ghi theo nguồn tương ứng; staging live LLM provider còn `BLOCKED (NO_CREDENTIALS)`.

Tài liệu này tổng hợp và chuẩn hóa workflow từ:

1. Lotus Fin AI Feature Specification.
2. Lotus Fin Data Strategy v3.1.
3. Lotus Fin Security SSOT — Code/Human versions.
4. Lotus Fin Antigravity Implementation Blueprint.
5. Master Prompt — Lotus Fin End-to-End Pipeline & Workflow Architecture.
6. VinUniversity AICB Day 13 — *Monitoring, Logging & Observability*.
7. VinUniversity AICB Day 14 — *AI Evaluation & Benchmarking*.

Các nội dung Day 13 được đưa vào tài liệu gồm:

- metrics / logs / traces;
- structured JSON logging;
- correlation ID;
- PII sanitization;
- trace waterfall;
- 4 golden signals + cost + quality;
- SLI/SLO/alerting;
- monitoring dashboard;
- runbook;
- monitoring validation.

Các nội dung Day 14 được đưa vào gồm:

- offline, online và human evaluation;
- golden dataset;
- correctness/relevance/completeness/coherence;
- RAGAS;
- LLM-as-Judge;
- trajectory evaluation;
- regression gates;
- failure analysis;
- continuous improvement.

---

# 37. One-line summary

**Bài học AI001:** giá trị của engine phải nhìn thấy và truy vết được trong UI; mỗi claim hoàn thành phải có bằng chứng đúng môi trường và đúng gate.

> **Một AI Agent production-grade không chỉ cần "code đúng"; nó cần đúng bài toán, đúng data, đúng quyền, đúng tool, có evidence, có benchmark, observable, monitorable và có khả năng fail safely.**

---

# 38. Kỷ luật tài liệu và kiểm tra consistency sau AI001

## 38.1 Một nguồn hiện hành cho mỗi loại thông tin

- **Feature contract/freeze:** scope, metric, công thức, quyền, failure semantics, UI behavior và quyết định còn hiệu lực. Giữ lịch sử quyết định, nhưng cập nhật metadata/status đầu tài liệu hoặc đóng dấu `Historical design state` khi trạng thái đã đổi.
- **Completion report:** việc đã làm, file/commit, môi trường, lệnh kiểm, số test, gold/runtime, E2E artifact, limitation và gate còn chặn. Mỗi report là snapshot tại ngày/commit, không âm thầm sửa lịch sử test count.
- **Master feature document:** bản đồ sản phẩm/kiến trúc và liên kết đến freeze/report hiện hành. Không tạo công thức hoặc trạng thái mới chỉ trong master document.
- **Workflow:** bài học và gate tái sử dụng; ví dụ AI001 phải ghi rõ phạm vi, tránh biến demo fixture thành quy tắc cho mọi company.

## 38.2 Checklist cross-document trước sign-off

1. Soát feature ID, user journey và đơn vị phân tích; AI001 là financial health cấp company, không là credit-risk của Sales Invoice.
2. Soát danh sách KPI bằng **ID**, phân biệt thẻ UI, core metric và near-term AP `UNAVAILABLE`. Tài liệu AI001 đang dùng cụm “6 core metrics” trong khi liệt kê revenue, COGS, gross margin, cash, AR, overdue ratio, AP (7 giá trị); khi chỉnh tài liệu nguồn, chuẩn hóa đếm và cách gọi, không tự thêm KPI.
3. Soát công thức, sign, currency, as-of, period comparison và evidence filter giữa freeze, backend contract, report và UI; verified zero khác missing.
4. Soát status top-level, từng metric, comparison, explanation và UI; `PARTIAL`/`INSUFFICIENT_DATA` không bị đổi thành kết luận `OK` trong lời văn.
5. Soát bảo mật: role trên Page không thay company/report guard server; test Administrator không thay test non-admin/cross-company; claim zero PII phải có kiểm tra payload/log/UI.
6. Soát số test theo mốc: AI001-04 là 60/60 và eval 15/15; AI001-05 là 67/67 gồm 7 UI contract test, kèm E2E report. Không ghi 15 scenario thành 15 unit tests hoặc gọi tất cả là E2E.
7. Soát provider: mock verified và fault injection pass; live staging smoke `BLOCKED (NO_CREDENTIALS)`. Không đánh dấu credential/staging gate `[x]` nếu bằng chứng còn bị chặn.
8. Soát Git/release: branch, commit, merge, deploy, live smoke, rollback và owner là các trạng thái riêng; chỉ claim trạng thái có artifact.

## 38.3 Biên bản review ngắn bắt buộc

Ghi trong report cuối: `Reviewed documents`, `commit/revision`, `environment`, `verified facts`, `known limitations`, `unresolved conflicts`, `blocked gates`, `owner/next action`. Nếu hai tài liệu mâu thuẫn, sửa nguồn hiện hành và ghi chú lịch sử; không xóa nội dung đúng hoặc lặng lẽ chọn con số thuận tiện. Áp dụng cùng quy trình khi cập nhật AI002–AI007.
