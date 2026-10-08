# AI003 Policy Approval Package — 2026-10-02

**Current authority:** G2 CONTRACT PASS; G3 METHOD GOLD PASS; G4A PRE-BUILD RUNTIME/EVAL PASS; METHOD GOLD 66 PASS / 0 FAIL / 0 NOT_RUN; V2.2 VALIDATED; contract NOT_FROZEN. Method/design is closed. On 2026-10-02 the Project Owner approved all six values below as `AI003_DEMO_POLICY_V1` for **DEMO_ONLY**. This supersedes earlier PENDING_APPROVAL placeholders only in DEMO_ONLY scope. Production policy remains unapproved and uncalibrated.

> **NOT APPROVED FOR PRODUCTION.** `production_calibrated=false`; no automatic promotion path from DEMO_ONLY.

| Binding field | Owner-approved value |
|---|---|
| policy_scope | DEMO_ONLY |
| policy_version | AI003_DEMO_POLICY_V1 |
| approver_role / approval_date | Project Owner / 2026-10-02 |
| AR floor / WATCH / HIGH | 0 VND / 5.00pp / 15.00pp |
| AP floor / WATCH / HIGH | 0 VND / .50 / .75 |
| POLICY GOLD | [VERIFIED: 17 REQUIRED PASS, 4 proved N/A](AI003_POLICY_GOLD_EVIDENCE.md) |

**Historical proposal context:** `AI003-POLICY-DRAFT-A-2026-10-02` led to the DEMO_ONLY binding above. Its confidence and calibration limitations remain applicable. References below to OWNER_JUDGMENT_REQUIRED or PENDING_APPROVAL describe production use, not the now-complete DEMO_ONLY record.

## Evidence basis

| ID / classification | Established basis | What it cannot establish |
|---|---|---|
| E1 — INTERNAL_RUNTIME_FACT | [SSOT §20](AI003_MASTER_SSOT.md#20-runtime-recovery--method-gold--2026-10-02), [numeric-domain evidence](AI003_METHOD_GOLD_EVIDENCE.md#numeric-domain): report/AI001 money Q=.01 VND-normalized units; published AR ratio scale4 HALF_UP, hence delta quantum .01pp; AP uses exact N>=T×D | Alert thresholds, business materiality or sensitivity |
| E2 — METHOD_TEST_ONLY | [66-case manifest](AI003_METHOD_GOLD_MANIFEST.yaml) and [independent posted-ledger oracle](AI003_METHOD_GOLD_ORACLE.py) prove arithmetic, monthly cutoffs, identity, permissions, schedules and failure behavior on controlled synthetic transactions | Company-scale distribution, collection behavior, predictive validity or false-positive/negative rates. Fixture amounts/deltas and old test constants are not calibration data |
| E3 — EXTERNAL_REFERENCE | IFRS *Making Materiality Judgements* describes entity-specific judgement based on nature/magnitude; the guidance concerns financial statements and is non-mandatory. [Official Practice Statement 2, §5](https://www.ifrs.org/content/dam/ifrs/publications/amendments/english/2017/ifrs-practice-statement-2-making-materiality-judgements.pdf), [official scope/status](https://www.ifrs.org/issued-standards/list-of-standards/materiality-practice-statement/) | It prescribes no AI003 alert thresholds or VND floors. Applying the entity-specific principle to alert materiality is a PRODUCT_POLICY_JUDGMENT analogy, not an accounting-compliance requirement |
| P1 — PRODUCT_POLICY_JUDGMENT | Coarse human-review tiers, floor elicitation and qualitative sensitivity/risk statements below | Empirically optimal values or measured accuracy |
| N1 — NOT_VERIFIED | Authorized business history across monthly cycles, company/segment size, actionable amount bands, review capacity and labelled outcomes are absent from current evidence | No numerical confidence interval or calibrated universal default can be claimed |

No realtime external data is used as financial truth. Confidence below means **evidence for business suitability**, not a probability of success. It is LOW for each value; technical arithmetic/precision has verified evidence separately.

## Production-calibration discussion (DEMO binding above is already complete)

| Value | Proposal / unit | Rationale and basis | Expected sensitivity | Main false-positive risk | Main false-negative risk | Confidence |
|---|---|---|---|---|---|---|
| AR_MATERIALITY_FLOOR_VND | **OWNER_JUDGMENT_REQUIRED**; F_AR in `(I_AR, M_AR]` VND after owner supplies endpoints | Gate on **current net ar_outstanding**, not overdue amount or its increase. I_AR=largest current net AR balance owner would ignore; M_AR=smallest balance owner would review for this signal. Both must describe the same company/segment. E1 semantics; E3 analogy; P1 range; N1 endpoints | Raising floor suppresses alerts on small current net balances | Floor too low lets a small balance produce a large ratio change | Floor too high misses meaningful small-company exposure; net credits can reduce total below floor despite positive overdue invoices | LOW |
| AR_WATCH_DELTA_PP | **5.00 percentage points** | Candidate starts review after a five-point increase in published net overdue share; coarser than .01pp method quantum. P1 only; no industry standard/calibration claim | More review-sensitive than HIGH; changes below 5pp are benign if method/materiality pass | Invoice ageing, billing-cycle changes, credits or a falling net denominator can cross the threshold without collection deterioration | A meaningful increase below 5pp, or persistently high unchanged overdue share, produces no trigger | LOW |
| AR_HIGH_DELTA_PP | **15.00 percentage points** | Candidate gives earlier review priority to a change three times the WATCH increment. This spacing is a product choice, not a statistical result. P1 only | Reserves HIGH for larger monthly changes; WATCH remains available from 5pp through values below 15pp | Large routine monthly ageing/restatement or credit effects can cause a high delta | Serious exposure can grow by less than 15pp; current ratio near its usual level can conceal continuing risk | LOW |
| AP_DUE_MATERIALITY_FLOOR_VND | **OWNER_JUDGMENT_REQUIRED**; F_AP in `(I_AP, M_AP]` VND after owner supplies endpoints | Gate on **N**, positive AP due D0–D30. I_AP=largest N owner would ignore; M_AP=smallest N owner would review. Not a floor on D, invoice count or bank cash. E1 semantics; E3 analogy; P1 range; N1 endpoints | Raising floor suppresses small due-amount concentrations | Floor too low alerts on trivial near-term amounts | Floor too high suppresses amounts material to a smaller or cash-constrained company | LOW |
| AP_WATCH_DUE_SHARE | **0.50 share (50%)** | At least half of eligible positive-future AP is contractually due D0–D30: a readily explained review tier. P1 only | Detects majority concentration regardless of absolute company size, once N passes its floor | Routine short payment terms can keep the share high; this says nothing about available cash or actual settlement | A large actionable N can sit below 50% because D includes substantial long-dated AP; past-due debt is outside this signal | LOW |
| AP_HIGH_DUE_SHARE | **0.75 share (75%)** | Three quarters of eligible future-positive AP due D0–D30 indicates stronger contractual concentration for review priority. P1 only | Fewer HIGH outcomes than WATCH for the same valid source | Ordinary payment cycles or one near-term invoice with little long-dated AP can produce HIGH | A costly due cluster below 75%, or excluded overdue obligations, may still merit urgent attention | LOW |

**Smallest defensible floor decision range:** obtain I and M from Finance for each signal; require `0<=I<M`, then choose one finite F with `I<F<=M`. These are owner-labelled operational examples, not additional runtime gates. If owner examples do not give an ordered band, resolve that judgement before selecting F. There is currently **no defensible absolute VND interval**: substituting 1/10/100 million would invent a company scale. The technical domain `F>=0` is not a business recommendation. An explicit owner choice of F=0 is contract-valid but removes small-amount suppression; it is not this package's default.

The same absolute floor will be more restrictive for a small company and less restrictive for a large company. Owner must name the intended company/segment and accept or revise the floor for that scope; no automatic percent-of-revenue or scale resolver is added. The four coarse thresholds may also be rejected by the owner. No measured alert rate is available to rank these choices.

AR remains **net**; baseline remains previous-month same-day with month-end clamp; delta is `(current published ratio - baseline published ratio)*100`. Compare the two typed published metrics, never AI001's rounded comparison output. PP is an absolute share change, not relative percentage growth. A positive net denominator must already satisfy method prerequisites before materiality is considered.

AP remains `0<=days_to_due<=30`, N=positive due-window AP, D=positive AP with valid due_date>=as_of; credits and past-due amounts excluded. D>0 is a method prerequisite. The thresholds compare **N>=T×D**; 4dp share display is not an operand. A high due share measures contractual concentration, not liquidity sufficiency or predicted payment/default.

## Candidate reachability — mathematical design check, not gold execution

Let q=.01 VND, and let A be a positive multiple of 100 VND with A>=the applicable floor; keep all amounts within the pinned source numeric range. At A=100 the following threshold witnesses use only q-representable money. Scaling to an owner-supplied floor must be bound and checked before execution. This is METHOD_TEST_ONLY fixture arithmetic, not a suggested floor or business calibration amount.

| Check | AR candidate | AP candidate |
|---|---|---|
| Threshold invariants | **PASS:** 15>=5>=0 | **PASS:** 1>=.75>=.50>=0 |
| Floor invariants | **OWNER_TO_BIND:** finite F_AR>=0; no numeric floor proposed | **OWNER_TO_BIND:** finite F_AP>=0; no numeric floor proposed |
| WATCH-only reachable | **YES:** delta10pp, published ratios .2000→.3000; 5<=10<15, current total A>=F_AR | **YES:** D=4A, N=2.5A; .50D<=N<.75D, N>=F_AP |
| Exact WATCH reachable | **YES:** .2000→.2500 yields 5.00pp on .01pp grid | **YES:** D=4A, N=2A, N=.50D exactly |
| Exact HIGH reachable | **YES:** .2000→.3500 yields 15.00pp on .01pp grid; HIGH wins | **YES:** D=4A, N=3A, N=.75D exactly; HIGH wins |
| Positive below-floor reachable | **IFF F_AR>q**, subject to valid source amounts/prerequisites | **IFF F_AP>q**, subject to valid source amounts/prerequisites |
| F<=q: positive below-floor | Planning N/A: **NO_POSITIVE_REPRESENTABLE_VALUE_BELOW_FLOOR**; every positive amount is >=q>=F | Same proof. However **N=0,D>0 is valid**, so an AP zero-amount below-floor case still exists when 0<F<=q |

Joint materiality/threshold reachability remains conditional until actual floors fit the source domain and the approved policy is bound. Unknown floors, unavailable fixtures or implementation are **NOT_RUN**, never N/A. For these proposed four thresholds, exact boundaries and separate WATCH bands have witnesses: neither EXACT_BOUNDARY_NOT_REPRESENTABLE nor NO_SEPARATE_WATCH_BAND applies. Full exact vectors, nearest boundaries, AP zero case and versioned proof requirements are in [POLICY GOLD plan](AI003_POLICY_GOLD_PLAN.md).

## Production-only owner decision record

Owner supplies: (1) company/segment and effective scope/date/data mode; (2) I_AR/M_AR and I_AP/M_AP, or an explicit independently justified floor; (3) accept/revise the four proposed thresholds; (4) all six finite decimal values, immutable policy version, approver/role/date and supporting operational examples. The examples must use the closed net-AR/AP-N semantics. Approval must record awareness of LOW calibration confidence; Work cannot approve it.

| Parameter | Owner-selected value / unit | Rationale / scope evidence | Approver / date |
|---|---|---|---|
| AR_MATERIALITY_FLOOR_VND | Pending — VND | Pending | Pending |
| AR_WATCH_DELTA_PP | Pending — pp; candidate 5.00 | Pending | Pending |
| AR_HIGH_DELTA_PP | Pending — pp; candidate 15.00 | Pending | Pending |
| AP_DUE_MATERIALITY_FLOOR_VND | Pending — VND | Pending | Pending |
| AP_WATCH_DUE_SHARE | Pending — share; candidate .50 | Pending | Pending |
| AP_HIGH_DUE_SHARE | Pending — share; candidate .75 | Pending | Pending |

```yaml
DEMO POLICY BINDING:
  policy_version: AI003_DEMO_POLICY_V1
  policy_scope: DEMO_ONLY
  production_calibrated: false
  approver/date: Project Owner / 2026-10-02
  AR floor/WATCH/HIGH: 0 VND / 5.00 pp / 15.00 pp
  AP floor/WATCH/HIGH: 0 VND / 0.50 / 0.75
DEMO POLICY GOLD: VERIFIED — 17 REQUIRED PASS; 4 proved N/A
PRODUCTION POLICY: PENDING_APPROVAL — no automatic promotion from DEMO_ONLY
CURRENT VERDICT: POLICY_GOLD_VERIFIED
NEXT OWNER: ChatGPT Chat
```

---

## Historical decision sheet — 2026-09-30, superseded

Everything below is retained verbatim as investigation history. Its labels “latest authority”/“hiện hành”, B1–B9, positive-only AR, seven-day baseline, AP 7/30 windows, extra denominator/count floors and earlier applicability proposals are **not current policy decisions**. V2.2 and the current package above take precedence; do not reopen those closed method choices or use historical test constants as calibration.

### AI003 Business Policy Decision Sheet — Work final review, 2026-09-30

**Latest authority: phần tiếng Việt bên dưới tại HEAD `86208f4`. Tất cả quyết định PENDING.** Bảng IVL dưới đây được giữ làm lịch sử đề xuất; đề xuất net AR ở dòng 1 được thay bằng positive-only để Finance cân nhắc trong B1, chưa được phê duyệt. Không thay công thức AI001, oracle hoặc business policy.

| # | Decision | Proposed option | Alternative | Business trade-off | Evidence available | Approval needed | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | AR net vs positive-only residual | **Net residual** (matches AI001 semantics and oracle; credits reduce exposure) | Positive-only residual + credits as separate context | Net = simpler continuity with AI001, may understate overdue when credit offsets; positive-only = higher but may overstate | Oracle dual bases 26/09: net 565,000/65,000 overdue vs positive-only 575,000/75,000; unallocated credit −10,000 | Finance | Finance | PENDING |
| 2 | Unallocated-credit treatment | **Separate coverage context** — excluded from numerator and denominator, shown as coverage line; never auto-netted because `return_against` is set | Net into residual; or allocate manually before evaluation | Separation avoids hidden denominator distortion; netting hides credit risk | Allocated credits verified counted-once via Payment Ledger; unallocated −10,000 isolated | Finance | Finance | PENDING |
| 3 | AR baseline policy (date + comparability) | **Explicit `baseline_as_of` in request** with comparability validation (same company/scope/currency/definition; comparable-window rule chosen by Finance); never auto-picked | Fixed periodic baseline (e.g., previous period N days) | Explicit = transparent but more user burden; periodic = automated but may compare unlike periods | §3.3 requirements defined; 09-20/09-26 pair is verification-only (11.5044 pp is not policy) | Finance | Finance | PENDING |
| 4 | AR warning/high thresholds + materiality | Structure: `AR_SPIKE_PP = (current−baseline)×100`; T_warning < T_high; fire high only when overdue ≥ materiality floor D_min AND denominator ≥ A_min AND observations ≥ N_min | Relative % growth (rejected at zero baseline) | Symbolic only — no production values proposed; thresholds drive alert noise vs sensitivity | Manifest symbolic boundaries (below/equal/above); `>=` is TEST_ONLY_POLICY | Finance | Finance | PENDING |
| 5 | AP 7/30 window | **Adopt +1..+7 short / +1..+30 reference, both inclusive** (verified arithmetic) | Finance-defined windows (e.g., weekly buckets) | 7/30 matches short-term cash-pressure framing; verified but still PROPOSED status | D1/D7/D8/D30/D31 boundary probes; cluster ratio 0.7179 @09-20, 0.2821 @09-26 | Finance | Finance | PENDING |
| 6 | AP warning/high thresholds + materiality | Structure: cluster ratio vs T_warning/T_high with D_min amount floor and N_min observations; overdue/due-today as separate context, never mixed into the ratio | Absolute-amount trigger instead of ratio | Ratio normalizes company size; amount floor prevents tiny-denominator noise | AP windows + context verified; zero denominator → NOT_APPLICABLE | Finance | Finance | PENDING |
| 7 | Minimum denominator & observation count (A_min, D_min, N_min) | One floor per signal + shared observation-identity rule (installment/account rows of one voucher counted per contract identity rule; exact duplicates rejected, legitimate splits kept) | Per-signal floors without identity rule (insufficient — duplicates currently double-count) | Floors prevent trivial/fragile signals; identity rule is prerequisite (PB-DATA-02) | PB-DATA-02 reproduced (AR 640,000 vs 565,000; AP 8 vs 7 obligations) | Finance | Finance | PENDING |
| 8 | Severity labels & presentation | **warning / high** only for P0, `finding` null when POLICY_PENDING; presentation via approved next-check IDs; no fraud/default claims | Add `critical` tier or numeric scores | Fewer tiers = clearer ownership; scores imply credit-scoring semantics (out of boundary) | §6 semantics + agent boundary §10; model-failure design verified | Product (+Finance for wording) | Product | PENDING |

Prerequisites from contract review (not approvals — contract decisions): SOURCE_INVALID > POLICY_PENDING precedence; equality/comparator semantics; warning/high ordering; no-rounding-before-threshold clause; observation identity definition; missing/malformed due-date → typed inconclusive. See [`AI003_IVL_CONTRACT_SEMANTICS_REVIEW_v0.2.md`](AI003_IVL_CONTRACT_SEMANTICS_REVIEW_v0.2.md).

## Phiếu quyết định hiện hành — Product/Finance

Scope chỉ AR_OVERDUE_SPIKE và AP_DUE_CLUSTER. Work chuẩn bị đề xuất; không có bằng chứng Product Owner đã phê duyệt. Tại 26/09/2026, sau payment và credit đã phân bổ:

| Cách nhìn AR | Tổng còn phải thu | Quá hạn | Tỷ lệ |
| --- | ---: | ---: | ---: |
| Net: cộng cả balance âm chưa phân bổ | 565.000 | 65.000 | 11,5044% |
| Positive-only: chỉ residual dương | 575.000 | 75.000 | 13,0435% |
| Credit chưa phân bổ, hiển thị riêng | −10.000 | Không tự gán cho hóa đơn | Không đưa vào positive-only ratio |

Net phản ánh balance sau bù trừ; positive-only cho thấy các khoản hóa đơn còn mở cần thu. Credit chưa phân bổ không chứng minh một invoice quá hạn khác đã được thanh toán. Positive-only tránh che exposure đó nhưng có thể cao hơn net cần thu cuối cùng nếu Finance sẽ thực sự phân bổ credit.

ERPNext phân biệt outstanding invoice và payment/credit chưa phân bổ; reconciliation gắn chúng với invoice và cập nhật outstanding. Nguồn chính thức hỗ trợ allocation semantics, **không cung cấp threshold AI003**: [Payment Reconciliation](https://docs.frappe.io/erpnext/payment-reconciliation), [Allocating Credit Note and Payment](https://docs.frappe.io/erpnext/allocating-credit-note-and-payment). Source đang cài và oracle là authority runtime.

AP synthetic: +1..7 = 275.000; +1..30 = 975.000 → 28,2051%. Overdue 600.000 và due-today 700.000 hiển thị riêng, không nằm trong future windows. Due date là hạn hợp đồng, không phải cam kết ngày tiền thực sự rời ngân hàng. Payment-term view có thể chia invoice outstanding theo schedule: [Accounts Receivable and Payable](https://docs.frappe.io/erpnext/accounts-receivable-and-payable).

### Quyết định cần duyệt

| ID | Đề xuất | Lý do và trade-off | Phương án khác | Evidence có / còn thiếu | Người duyệt | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 AR basis | AI003 **positive-only**; net và unallocated credits là context; version method riêng, không relabel AI001 net ratio. | Ưu tiên khoản còn mở; credit chưa gắn invoice không che overdue. Có thể cao hơn net nếu sắp allocate credit. | Net chỉ khi Finance định nghĩa scope bù trừ hợp lệ theo party/account/currency và overdue âm. | Có dual oracle. Thiếu Finance approval và dữ liệu vận hành nhiều kỳ. | Finance + Product | PENDING |
| B2 Credits | Allocated credit giảm residual một lần; unallocated credit hiển thị riêng, không tự giảm ratio. | Tránh double subtraction/giả allocation; cần người dùng kiểm tra credit treo. | Finance reconciles trước evaluation; không để LLM phân bổ. | Ledger/allocated 5k/unallocated 10k verified. Thiếu quy trình credits theo party. | Finance | PENDING |
| B3 AR baseline | Cân nhắc **as_of − 7 calendar days**, same company/scope/currency/basis/version/cutoff; thiếu comparable source → INCONCLUSIVE. | Dễ giải thích thay đổi một tuần; nhạy ngày nghỉ, invoice cycle, mùa vụ, restatement. | Explicit baseline hoặc cùng ngày tuần/tháng trước theo chu kỳ công ty. | Gold 20→26/09 là **6 ngày**, không chứng minh policy 7 ngày. Thiếu nhiều chu kỳ và calendar/business-day approval. | Finance + Product | PENDING |
| B4 AP windows | Cân nhắc +1..+7/+1..+30 inclusive; overdue/today riêng; contractual due date. | Review tuần tới trong tháng tới; ratio có thể thấp dù overdue lớn nên phải hiện context. | Weekly buckets theo kỳ thanh toán của công ty. | Biên D1/D7/D8/D30/D31 verified. Thiếu payment cycle data và window approval. | Finance | PENDING |
| B5 Denominator floor | Floor tiền riêng từng signal; denominator=0 → undefined/NOT_APPLICABLE, không BENIGN; dưới floor → status INCONCLUSIVE nếu Chat chốt. | Tránh ratio lớn từ tiền nhỏ; có thể bỏ tín hiệu sớm ở SME nhỏ. | Floor theo segment sau validation. | Có empty/symbolic cases. Thiếu floor production và phân bố dữ liệu. | Finance | PENDING |
| B6 Materiality | AR floor trên overdue exposure (cân nhắc thêm increase); AP floor trên short-window amount; AND với ratio/delta + denominator floor. Chốt tên/unit từng floor. | Giảm noise nhỏ; có thể bỏ khoản nhỏ nhưng quan trọng. Floor exposure khác floor denominator. | Absolute-amount signal cần scope riêng, không tự thêm P0 signal. | Có amount oracle. Thiếu mức trọng yếu công ty chấp nhận. | Finance | PENDING |
| B7 Observation count | Cân nhắc N_min đếm **distinct economic vouchers** sau reconciliation; splits giữ tiền nhưng không phình count. | Tránh nhiều row của một invoice làm giả sample lớn; có thể bỏ sự kiện lớn chỉ từ một invoice. | Bỏ N_min hoặc đếm installments nếu mục tiêu nghiệp vụ/identity được chứng minh. | Missing ID failclosed; duplicates FAIL; actual distinct multi-term/account split chưa verified. | Chat (identity) + Finance (floor) | PENDING |
| B8 Thresholds/severity | AR so delta **percentage points**; AP so ratio; cân nhắc >=, T_high>T_warning, HIGH ưu tiên; một verdict/signal; floors phải đạt. Không suy giá trị production từ fixture. | Hai mức dễ hiểu; threshold thấp tăng noise, cao bỏ tín hiệu. | Demo chỉ metric/POLICY_PENDING; CRITICAL/score ngoài P0. | 25 symbolic assertions TEST_ONLY. Thiếu threshold values, labels approval, validation. | Finance + Product + Chat | PENDING |
| B9 False positives | Hiện cutoff/baseline/coverage/restatement/credits; nguồn thiếu không evaluate; dùng floors đã duyệt và same versions. | Người dùng hiểu signal; suppression nếu thêm sau có thể che thay đổi mới. | Metric-only/POLICY_PENDING trước calibration. | Có temporal/credit/source reproductions. Thiếu labelled review outcomes nhiều kỳ. | Product + Finance | PENDING |

Minimum denominator, materiality và count là ba gate khác nhau. WARNING = nên rà soát; HIGH = ưu tiên rà soát sớm hơn; không kết luận gian lận, vỡ nợ hoặc tín dụng.

### DEMO_ONLY policy

- Chỉ synthetic fixture; immutable registry version có nhãn DEMO_ONLY/TEST_ONLY_POLICY; data_mode/policy_scope luôn hiện trong UI/evidence/logs.
- Marker 10/20 và 100/200/3 trong harness chỉ dùng kiểm tra boundary, **không phải mức cảnh báo tài chính đề xuất**. Product chọn demo policy riêng sau khi semantics và foundation đủ an toàn.
- Không auto-promote demo config sang LIVE/production. Synthetic gold chứng minh số học, biên ngày, allocation và failure behavior; không chứng minh sensitivity, false-positive rate, predictive accuracy hoặc mức cảnh báo phù hợp SMEs.

### PRODUCTION policy

- B1–B9 thuộc scope sử dụng cần approver/date/company scope/policy version/value/unit/comparator/floors/validation evidence. Hiện tất cả pending.
- Khi source hợp lệ và foundation an toàn nhưng policy chưa duyệt: `evaluation_status=POLICY_PENDING`, `finding=null`, `severity=null`. Authorization/invalid/zero có precedence cao hơn policy-pending.
- Validation cần dữ liệu được phép dùng nhiều chu kỳ, review outcomes, seasonality/company sizes, threshold sensitivity. Không crawl dữ liệu tài chính công ty khác để thay ERP source đã cấp quyền.

### Bảng người duyệt điền

| Decision ID | Option/value/unit | Scope DEMO_ONLY/PRODUCTION | Approver/vai trò | Ngày | Policy version | Validation evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1–B9: mỗi quyết định một dòng | Chưa điền | Chưa chọn | Chưa có | Chưa có | Chưa có | Chưa có | PENDING |

Technical mock/schema scaffold có thể làm trong draft scope; real-data adapters phải chờ F0/Work PASS. Xem [implementation plan](AI003_TECHNICAL_SCAFFOLD_IMPLEMENTATION_PLAN.md).
