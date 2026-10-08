# WORKFLOW THAM KHẢO KHI BUILD MỘT AI AGENT

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

> **Một AI Agent production-grade không chỉ cần "code đúng"; nó cần đúng bài toán, đúng data, đúng quyền, đúng tool, có evidence, có benchmark, observable, monitorable và có khả năng fail safely.**
