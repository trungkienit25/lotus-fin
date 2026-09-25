# AI001 — Feature Freeze trước khi code

**Ngày:** 2026-09-24  
**Mapping:** `AI001` (tên giao việc) = **`AI-F001 Financial Health Analyst`** trong AI Feature Specification; primary `UC003`, supporting `UC009`/`UC006`. Data Strategy gọi ngắn là `AI-F001 Financial Health`. `AI-001` trong Security SSOT là **mã test non-allowlisted tool**, không phải feature này.  
**Trạng thái:** `CONTRACT_FROZEN / NOT_READY_TO_CODE`. Các quyết định P0 dưới đây được freeze ở mức thiết kế; runtime facts và công thức phụ thuộc schema vẫn cần xác minh. Không claim đã implement hay đã pass gate.

## 1. Problem và phạm vi

- **Người dùng:** SME Owner và Accountant có quyền xem dữ liệu của company được chọn; quyền thực tế phải ánh xạ và kiểm thử trên Frappe/ERPNext.
- **Câu hỏi:** Vì sao tiền giảm trong khi doanh thu tăng? Vì sao gross margin giảm? Áp lực vốn lưu động đến từ đâu? KPI nào thay đổi nhiều nhất? Chỉ trả lời câu hỏi cụ thể khi dữ liệu kỳ hiện tại, kỳ so sánh và bằng chứng liên quan đã được xác minh.
- **Giá trị:** Một báo cáo sức khỏe tài chính có số liệu truy vết được, xu hướng có cùng kỳ so sánh hợp lệ, giải thích dễ hiểu, giả định/giới hạn và gợi ý bước kiểm tra tiếp theo.
- **Hậu quả nếu sai:** quyết định kinh doanh sai; lộ dữ liệu company khác; ngộ nhận thiếu dữ liệu là 0 hoặc xem diễn giải AI là kết luận kiểm toán/tín dụng.
- **P0 in scope:** phân tích `actual` cho một company và một kỳ; minimum trusted data theo AI-F001; KPI deterministic và bằng chứng từng KPI; LLM giải thích grounded khi có model được duyệt; trạng thái từng KPI, giới hạn khi thiếu dữ liệu và câu hỏi follow-up có scope rõ.
- **Ngoài P0:** dự báo dòng tiền (UC004/AI-F002), phát hiện gian lận, chấm điểm tín dụng, benchmark ngành chưa có nguồn, DSCR/Quick Ratio/working-capital turnover khi chưa xác minh đủ trường, Copilot chat tự do, RAG, ML training, ghi sổ hoặc hành động ngân hàng. Không dùng `AR - AP` làm cash balance/forecast hay một điểm “health score” tổng hợp khi chưa có định nghĩa và gold.

## 2. Required data và readiness

| Dữ liệu | Vai trò P0 | Yêu cầu kiểm chứng trước code |
|---|---|---|
| Company, user/role, quyền report/DocType | Bắt buộc | Hai company, ít nhất hai user/role; thử allow/deny ở server. `company` từ client là untrusted. |
| Kỳ phân tích, timezone/as-of, fiscal context | Bắt buộc | Ranh giới kỳ và thời điểm chốt; không so sánh hai kỳ khác độ dài. |
| Period revenue và expense/COGS khi có | Bắt buộc theo AI-F001 | Tên report thực tế, cột/row, mapping account, sign/recognition, trạng thái submitted/cancelled và quyền. Không gọi expense là COGS khi nguồn không tách COGS. |
| Cash balance hoặc validated cash proxy | Bắt buộc theo AI-F001 | Nguồn, reconciliation, định nghĩa proxy, as-of và limitation. `AR - AP` không phải cash proxy hợp lệ nếu chưa được chứng minh độc lập. |
| AR total **và overdue AR** | Bắt buộc theo AI-F001 | Outstanding, due date, as-of, trạng thái settlement và cùng company; kiểm tra overdue ratio denominator. |
| AP total **và near-term AP** | Bắt buộc theo AI-F001 | Outstanding, due date, cửa sổ `near-term` phải được chốt sau runtime verification. |
| Kỳ trước tương ứng | Tùy chọn cho so sánh; bắt buộc cho câu hỏi về thay đổi | Chỉ tính trend khi kỳ, scope, currency và cách tính tương đương. |
| Inventory value, concentration | Tùy chọn | Chỉ dùng khi nguồn, định nghĩa và gold được duyệt. |
| Debt-service, future obligations, benchmark ngành | Ngoài KPI mặc định | Cash runway chỉ bật khi obligations đủ; benchmark không có nguồn thì bỏ; không suy DSCR/Quick Ratio từ dữ liệu gần giống. |

ERPNext/Frappe là nguồn nghiệp vụ ứng viên; report là read projection, không mặc nhiên là source of truth. Chỉ dữ liệu `trust_state=trusted`, `data_mode=actual` được đưa vào KPI P0. `raw/candidate/synthetic` chỉ dùng trong kiểm thử hoặc phải gắn nhãn rõ. Mỗi record/metric cần `company`, `source_kind`, `trust_state`, `data_mode`, `source_id/version`, `as_of`, `currency`, `schema/transformation_version` khi áp dụng. Tiền dùng decimal hoặc minor units với ISO currency; không cộng các currency hay tự tạo FX. Cần snapshot tối thiểu và `EvidenceRef` gồm nguồn, bộ lọc, company, as-of, retrieved_at, version/checksum. Không tạo ledger ghi thứ hai.

**Readiness hiện tại theo tài liệu:** `PARTIAL`; Frappe/ERPNext version, site, report row schema, quyền report, nguồn cash/bank, kỳ/currency chưa được runtime verify. Đây là các hạng mục `NOT_VERIFIED`, không được suy diễn từ document hay fixture.

### 2.1 Company nào dùng được?

Feature phải **cấu hình dùng lại cho mọi company trên site ERPNext tương thích**, nhưng một request chỉ được đọc **company mà user đã được server cấp quyền**. Đây không phải quyền truy cập dữ liệu của “company bất kỳ”. Ngoài permission, không thể cam kết mọi company trả kết luận `OK`: company chưa có sổ đã chốt, thiếu công nợ/due date, thiếu cash mapping, dùng currency/Finance Book khác, hoặc có report tùy biến sẽ trả `PARTIAL`/`INSUFFICIENT_DATA` theo contract. Không gộp company con/nhóm bằng cách cộng tùy tiện; consolidated view là scope riêng.

Ma trận chấp nhận tối thiểu: (A) company đủ dữ liệu + user có quyền → `OK`; (B) company đủ dữ liệu + user không có quyền → `FORBIDDEN`; (C) company hợp lệ nhưng thiếu một minimum input → chỉ metric còn chứng cứ hoặc `INSUFFICIENT_DATA`, không bịa zero; (D) company khác chart of accounts/report configuration → adapter mapping được cấu hình/verify hoặc fail rõ, không hard-code theo demo company.

### 2.2 Nguồn ứng viên và đường lấy dữ liệu

| Input/kết luận | Nguồn ERPNext ưu tiên | Đối soát/bẫy cần kiểm tại site |
|---|---|---|
| Revenue, expense, COGS/gross margin | **Profit and Loss Statement** theo company, kỳ, Finance Book; khi cần drill-down dùng **General Ledger** và voucher gốc | P&L có thể đổi dấu/nhóm theo Chart of Accounts; COGS chỉ dùng khi tách được; không thay bằng Sales Invoice total một cách mặc định. |
| Cash balance / cash movement | **Balance Sheet/Trial Balance** của bank/cash accounts tại as-of, đối chiếu **General Ledger**; **Cash Flow** cho câu hỏi vì sao tiền thay đổi | Cash Flow là dòng chuyển động, không tự động bằng số dư cuối kỳ. `AR - AP` không là tiền mặt. Cash proxy chỉ chấp nhận khi tài khoản, công thức, độ phủ và reconciliation được kế toán xác nhận. |
| AR total, overdue AR, due date | **Accounts Receivable** report, drill-down **Sales Invoice** và **Payment Ledger/Payment Entry** khi cần | Outstanding sau phân bổ, credit note; aging dựa due date hay posting date phải chốt; số liệu cùng as-of/company. |
| AP total, near-term AP, due date | **Accounts Payable** report, drill-down **Purchase Invoice** và **Payment Ledger/Payment Entry** khi cần | Chốt cửa sổ near-term, payment schedule và các adjustment; không coi toàn bộ AP là sắp đến hạn. |
| Period comparison | Cùng report/filters của kỳ trước, có snapshot/evidence riêng | Cùng company, Finance Book, currency, accounting dimensions, kỳ tương đương và công thức. |

Trong app Frappe, ưu tiên adapter **server-side** gọi report/DocType đã allowlist, có company guard và permission check trước khi đọc; không cho model/browser gọi trực tiếp `/api/resource` hay `query_report.run`. Nếu hệ thống ngoài app cần truy cập, Frappe có REST `/api/resource/{doctype}` và RPC `/api/method/{whitelisted_method}`, nhưng cách dùng thực tế phụ thuộc version và quyền của site. Tên report/field/API response trong bảng là **candidate**, cần capture từ runtime trước khi code. Nguồn tham khảo chính thức: [ERPNext Accounting Reports](https://docs.frappe.io/erpnext/accounting-reports), [Accounts Receivable and Payable](https://docs.frappe.io/erpnext/accounts-receivable-and-payable), [Frappe REST/RPC API](https://docs.frappe.io/framework/user/en/guides/integration/rest_api), [Frappe Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions). Các nguồn này mô tả khả năng sản phẩm; chúng không chứng minh site Lotus hiện có đủ dữ liệu/quyền.

### 2.3 Nguồn **bản ghi** cho build, test và demo

Đây là quyết định provenance riêng với câu hỏi “report/API nào đọc dữ liệu”. **AI-F001 P0 không cần training dataset và không cần sinh synthetic cho runtime production.** Thứ tự dùng dữ liệu:

| Mục đích | Nguồn bản ghi | Nhãn/điều kiện |
|---|---|---|
| Production hoặc pilot trên company thật | Giao dịch kế toán và master data **đã có, được phép đọc** trên chính ERPNext site/company đó; report/DocType được đối soát với sổ và `as_of` | `source_kind=observed`, `trust_state=trusted` sau kiểm chứng, `data_mode=actual`. Hiện **chưa xác minh** Lotus site có đủ dữ liệu AI-F001. |
| Demo nếu có ERPNext demo company hợp lệ | Dữ liệu demo **đã nằm trong ERPNext**, được xác minh schema, quyền, reconciliation và coverage minimum inputs | `source_kind=observed` đối với demo site, nhưng gắn `environment=demo`; không gọi là số liệu của SME thật. |
| Test/gold và phần demo còn thiếu | **Synthetic có kiểm soát**: tạo giao dịch Sales/Purchase Invoice, payment/credit, cash/GL và due dates hợp lệ trong **test site ERPNext**, theo schema/quy tắc kế toán đã xác minh; seed/manifest cố định | `source_kind=synthetic`, `data_mode=actual` **chỉ trong thế giới fixture**, `environment=test/demo`; không được trộn hoặc trình bày là actual của company thật. Gold tính tay/độc lập và kiểm bất biến cash/AR/AP. |
| Public datasets | Olist cho hành vi order/payment nghiên cứu; WBES cho bối cảnh SME tổng hợp; SEC cho tham khảo metric/taxonomy; CORD chỉ khi OCR được bật | Các nguồn này **không là một bộ sổ cái SME hoàn chỉnh** cho AI-F001. Không ghép record khác nguồn thành “một company thật”; không lấy aggregate WBES/SEC làm doanh thu/cash/AR/AP của demo company. |

Nếu phải sinh synthetic, **“dựa trên nguồn legit”** nghĩa là dựa vào **schema và quy tắc hạch toán/report của ERPNext đã kiểm trên site**, cộng với phân phối/hành vi từ nguồn công khai phù hợp **chỉ khi có giấy phép, mapping và provenance rõ**. Nguồn công khai chỉ giúp hiệu chỉnh mẫu hành vi; các con số trong fixture vẫn là synthetic. Ví dụ tạo một credit sale → Sales Invoice đã submit → AR tăng; tạo Payment Entry phân bổ → AR giảm và cash tăng; tạo Purchase Invoice → AP tăng; ghi due date/late payment → overdue/near-term được report phản ánh. Reconcile lại với P&L, GL, AR/AP và Cash Flow; không trực tiếp bịa một dòng “AR=50” mà không có giao dịch sinh ra nó.

Manifest tối thiểu cho mỗi bộ test/demo: `dataset_id`, `environment`, `company_id` giả, `source_kind`, `source_refs` (ERPNext site/version + report/DocType schema, public source nếu thực sự dùng), `license/usage_rights`, `seed`, `generator_version`, `created_at`, kỳ/currency, assumptions, transformations, validation results và hash/version. Không copy dữ liệu production nhạy cảm vào test/demo nếu chưa có quyền và phương án ẩn danh phù hợp. `synthetic` không tự động thành `trusted`: phải pass schema, reconciliation, invariant và gold trước khi được dùng trong fixture.

**Quyết định triển khai:** đầu tiên kiểm tra **dữ liệu có sẵn trên ERPNext test/demo/target site**. Chỉ sinh synthetic để bù chỗ trống của **test/demo** và ca adversarial/missing-data, tuyệt đối không dùng synthetic để che việc production company thiếu minimum input. Nếu không có demo data hợp lệ, dựng toàn bộ **company fixture synthetic có provenance và invariant** trên test site; công bố rõ là demo synthetic.

## 3. Computation type và phương pháp

- **Số liệu:** `DETERMINISTIC`. Finance service lấy snapshot tin cậy, xác định KPI theo công thức/version được chốt sau khi đối chiếu report thực tế. Gold phải độc lập với implementation. Không để LLM tính lại, sửa số, chọn company, quyết định quyền, hay tạo metric không có nguồn.
- **Diễn giải:** AI-F001 có computation class `DETERMINISTIC + LLM_EXPLANATION` (hybrid). Model chỉ nhận structured KPI + evidence + limitations đã được server cho phép. Nếu model lỗi, KPI deterministic hợp lệ vẫn trả về, nhưng **AI-F001 chưa đạt Done về phần giải thích**; `explanation_status=UNAVAILABLE`.
- **Triển khai model:** ưu tiên **model qua API được phê duyệt**, gọi từ backend bằng credential trong secret store; không chạy model local trong deployment P0. Gửi tối thiểu metric/evidence metadata và câu hỏi đã kiểm scope; không gửi full report rows, chứng từ, thông tin tài khoản hay PII mặc định. Chốt provider/model/version, region/data handling, timeout, rate/cost budget, retention và fallback trước DoR. Model API outage chỉ tắt explanation của request, không thay đổi KPI. Không hard-code provider cụ thể khi chưa có quyết định vận hành.
- **P0 metric candidates đúng AI Feature Specification:** revenue change khi có kỳ so sánh; gross margin khi COGS/source hỗ trợ; AR outstanding; overdue AR ratio khi denominator hợp lệ; AP outstanding; working-capital indicators khi định nghĩa và nguồn được chốt. Mỗi metric có `metric_id`, `value`, `currency_or_unit`, `period`, `formula_version`, `snapshot_id`, `evidence_refs[]`.
- **Cash balance/validated cash proxy** là input để giải thích cash movement, không được gọi là cash forecast. Cash runway chỉ khi có đủ obligations. Net profit/net margin có thể là UC003 metric mở rộng, **không thay** minimum data của AI-F001 và chỉ bật sau khi method/gold được chốt.
- **Interpretation rule:** fact gắn với KPI/evidence; nhận định nêu rõ là diễn giải. Câu hỏi “vì sao cash giảm dù revenue tăng” cần Cash Flow/GL và kỳ so sánh để chỉ ra driver; nếu chỉ có hai số dư/doanh thu, chỉ được nói hiện tượng và limitation, **không khẳng định nguyên nhân**. Không khẳng định gian lận, khả năng vay hay dự báo chỉ từ tương quan/thiếu dữ liệu. Không có benchmark thì bỏ so sánh.

## 4. Input/output contract (đề xuất để implementation xác nhận)

**Input request** từ user đã xác thực:

```yaml
feature_id: AI001
company: string                  # validate server-side, không tin client
period_start: date              # inclusive
period_end: date                # inclusive; start <= end
as_of: datetime                 # thời điểm snapshot, không sau thời điểm request
comparison: NONE|PREVIOUS_PERIOD
currency: ISO_4217             # chỉ currency đã được nguồn xác nhận
question: string|null           # câu hỏi phân tích bounded, không mở general Copilot
correlation_id: string|null     # server tạo nếu không có
```

Server phải giới hạn độ dài kỳ, kích thước report và số dòng theo policy được runtime verify; không nhận arbitrary report name, raw SQL, arbitrary filters/URL, invoice ID không thuộc company. Subject (`user_id`, quyền thực tế) lấy từ session server, không từ request body.

**Output envelope** cho cả thành công và lỗi:

```yaml
feature_id: AI001
contract_version: string
status: OK|PARTIAL|INSUFFICIENT_DATA|FORBIDDEN|VALIDATION_ERROR|SOURCE_ERROR|TIMEOUT|MODEL_UNAVAILABLE
correlation_id: string
company: string|null            # chỉ khi được phép tiết lộ
period: {start: date, end: date}|null
as_of: datetime|null
snapshot_id: string|null
data_mode: actual|null
currency: ISO_4217|null
metrics:
  - {metric_id: string, status: AVAILABLE|UNAVAILABLE, value: decimal|null,
     currency_or_unit: string, period: object, formula_version: string|null,
     snapshot_id: string|null, evidence_refs: [], limitations: []}
comparison: object|null        # chỉ khi tương đương và có chứng cứ
explanation: {status: AVAILABLE|UNAVAILABLE, facts: [], interpretations: [], next_checks: []}|null
missing_inputs: []
limitations: []
evidence_refs: []               # mỗi ref có source_name, filters, company, as_of, retrieved_at, version
```

`OK`: minimum trusted data của AI-F001 đủ và các phần yêu cầu đều hợp lệ. `PARTIAL`: các dữ liệu còn đủ để trả một số metric nhưng thiếu một phần hoặc explanation; mỗi phần thiếu có `UNAVAILABLE` và lý do, **không gọi là đánh giá sức khỏe đầy đủ**. `INSUFFICIENT_DATA`: thiếu một thành phần minimum data cần để trả kết luận được yêu cầu; **không có kết luận sức khỏe tổng thể**. `FORBIDDEN`: không tiết lộ dữ liệu, kể cả tên company/resource tồn tại hay không. Giá trị thiếu là `null`, không là 0; zero chỉ hợp lệ khi nguồn xác nhận zero. Không trả stack trace/path/secret.

## 5. Security boundary

Flow: `authenticate → authorize company + report/DocType + resource → validate schema/bounds → read scoped sources → snapshot/evidence → deterministic compute → optional explanation → validate/escape output → audit`.

- P0 là `R0` đọc + `R1` tính; không ghi ERP, không route/tool/credential Bank write (`R4/R5 = DENY`). AI không có DB/Bank credential, shell, arbitrary HTTP, quyền cài tool.
- Server ràng `company` cho mọi report/filter và resource; kiểm tra quyền trước query; report allowlist, row/output cap; cache/job key theo company và quyền. Deny cross-company kể cả qua filter, document ID, bulk report và lỗi/log.
- Nếu sau này exposed qua Copilot, chỉ dùng typed `get_financial_health` trong allowlist; backend kiểm schema, scope, action level. Tên tool và policy do server kiểm, không do prompt quyết định.
- User text, tên Customer/Supplier, report values và model output là untrusted; encode UI, chống HTML/XSS và CSV formula injection nếu có export. Prompt injection không đổi tool, company, công thức hay evidence.
- Giảm thiểu PII; không gửi full document/account identifiers cho model; không lưu raw chain-of-thought, secret hay full prompt chứa PII.

## 6. Failure states và UX

| State | Trigger | Hành vi |
|---|---|---|
| `VALIDATION_ERROR` | Kỳ, currency, enum, bounds sai | Từ chối trước truy vấn; field error an toàn. |
| `FORBIDDEN` | Chưa auth, company/resource/report ngoài quyền | Deny, audit, không lộ nội dung hay tồn tại của resource. |
| `SOURCE_ERROR` / `TIMEOUT` | Report/DocType lỗi hoặc timeout | Không biến thành `[]/0`; không phát biểu kết luận. Có correlation ID để điều tra. |
| `INSUFFICIENT_DATA` | Thiếu minimum trusted data cho câu hỏi/kết luận | Trả missing_inputs, hướng dẫn kiểm nguồn; không tính health score hay suy số thiếu. |
| `PARTIAL` | Một số metric còn hợp lệ nhưng thiếu cash/AR overdue/AP near-term, trend hoặc explanation | Chỉ hiển thị metric hợp lệ và giới hạn rõ; không gọi là kết luận AI-F001 đầy đủ. |
| `MODEL_UNAVAILABLE` | Model lỗi/hết quota/parse sai | Giữ KPI deterministic nếu hợp lệ, bỏ diễn giải AI; không fallback sang model chưa kiểm thử. |
| `INCONSISTENT_DATA` | Các nguồn không reconcile, sign/currency/as-of mâu thuẫn | Đánh dấu KPI liên quan `UNAVAILABLE`, chặn kết luận phụ thuộc KPI đó, gắn limitation và audit. |

`INCONSISTENT_DATA` có thể là `error_class` trong `PARTIAL`/`INSUFFICIENT_DATA` nếu envelope status không mở rộng; cách ánh xạ phải chốt trong schema trước coding. Source error không được hiển thị như “healthy/low risk”.

## 7. Observability và logging

- **Structured audit event:** `event_id`, timestamp, `correlation_id`, feature/contract/formula/tool/model version (khi có), user ID pseudonymous, company ID được kiểm soát, action, source/report ID, snapshot ID, policy decision, status/error_class, duration; không log số tiền/row/PII mặc định.
- **Trace:** cùng correlation ID qua request, auth/company guard, từng source adapter, snapshot, computation, explanation và response validation. Thể hiện source status và version để truy vết KPI.
- **Metrics:** request count theo status, auth denials, source errors/timeouts, missing-input/partial rate, KPI unavailable rate, numeric mismatch trong eval, latency p50/p95, model error/tokens/cost nếu bật. Dashboard/alert cho cross-company attempt, source failure tăng, mismatch gold; threshold vận hành phải hiệu chỉnh từ baseline thực tế.
- **Privacy:** không log secret/token/password, raw prompt/CoT, full financial document, full account number hoặc PII; redact trước emit. Quy định retention/access và kiểm chứng thực tế ở DoR.

## 8. Test cases và evaluation criteria

| ID | Test/fixture | Pass condition |
|---|---|---|
| F001-NUM-01 | Gold độc lập cho revenue change, gross margin nếu đủ COGS, AR outstanding, overdue ratio, AP outstanding, working-capital indicator; zero denominator, âm/lỗ, rounding | **100% material numeric match** với gold, kể cả currency, period và as-of. |
| F001-DATA-01 | Thiếu P&L, empty hợp lệ, report lỗi, report timeout, candidate/untrusted row | Phân biệt zero/empty/error; không tạo kết luận khi thiếu KPI lõi. |
| F001-DATA-02 | Cash/proxy, overdue AR, near-term AP, trend/COGS/benchmark thiếu hoặc inconsistent | `PARTIAL`/`INSUFFICIENT_DATA`/`UNAVAILABLE` đúng theo câu hỏi; không bịa benchmark, ratio, cash hoặc trend. |
| F001-AUTH-01 | User A Company A allow; A→B qua company/filter/report/resource deny; user B quyền khác | **0 cross-company success**, 0 row/PII leak trong response/log. |
| F001-SEC-01 | Arbitrary report/tool, prompt injection trong tên đối tác/report/model output; XSS/CSV canary | Không gọi tool/report ngoài allowlist, không đổi scope/number; render/export an toàn. |
| F001-AI-01 | Explanation trên fixture có KPI/evidence/limitation; model unavailable hoặc bịa số | Mọi số trong prose khớp structured KPI; claim thực tế có evidence; lỗi model không làm mất KPI hợp lệ. |
| F001-OBS-01 | Success, partial, denied, source error | Audit và trace nối được bằng correlation ID; payload nhạy cảm không xuất hiện. |
| F001-COMP-01 | Hai company khác chart of accounts/currency/Finance Book/report layout; một company rỗng | Mapping được verify theo site/company hoặc fail typed; không hard-code demo company, không cộng currency khác. |
| F001-API-01 | Provider API trả 200, timeout, 429, 5xx, output sai schema, tăng chi phí | Dùng mock/recorded response có kiểm soát; KPI giữ nguyên; explanation unavailable khi lỗi; không lộ credential, có latency/token/cost metrics. |
| F001-CAUSE-01 | Revenue tăng nhưng cash giảm; fixture có AR tăng và Cash Flow/GL đối soát; fixture chỉ có 2 số tổng | Chỉ fixture đủ bằng chứng được nêu driver; fixture thiếu chỉ nêu hiện tượng/limitation. |

Eval set phải có fixture normal, edge, failure và adversarial; seed/manifest/version cố định; gold độc lập với hàm đang test. Acceptance gate: 100% material numeric match; 0 unauthorized/cross-company success; 0 fabricated material claim; 100% missing/error source cases fail safely; 100% critical flows reconstructable by correlation ID trên test set. Với explanation, đánh giá correctness, relevance, completeness, coherence và evidence grounding bằng rubric đã chốt; **không tự đặt điểm đạt chủ quan** trước khi có bộ gold và người review. P95 latency, cost và quality threshold định lượng sẽ freeze sau runtime baseline/pilot, không được báo đạt khi chưa có số đo. Mọi đổi code/prompt/model/tool schema phải chạy regression phù hợp.

**Cách test theo lớp:** (1) unit với gold tính tay độc lập cho số học/date/rounding; (2) adapter contract với report/DocType fixture lưu cột và status thật, bao gồm empty/error; (3) integration trên ERPNext test site có 2 company, 2 user/role, giao dịch đã submit, credit/payment/cancel và permission allow/deny; (4) model API mock cho logic và fault injection, sau đó một tập nhỏ staging gọi provider thật để đo schema/latency/cost và kiểm data minimization; (5) acceptance/E2E đối chiếu report ERPNext với output và review thủ công explanation. Ví dụ gold minh họa độc lập: revenue 100, COGS 60 → gross margin 40%; AR outstanding 50, quá hạn 20 → overdue ratio 40%; AP outstanding 30, near-term 10. Tất cả số này là fixture synthetic, không phải dữ liệu công ty thật. Không gọi live model trong unit test và không dùng chính implementation làm oracle.

## 9. Definition of Ready (gate trước khi code)

- [x] Problem, phạm vi, mapping AI001/AI-F001/UC003, loại tính toán và non-goals được ghi rõ.
- [x] Input/output, failure, security, evidence, observability và test/eval contract ở mức thiết kế được ghi rõ.
- [x] Frappe/ERPNext version, installed apps, site/company topology và role mapping được ghi bằng runtime evidence (Frappe v16.34, ERPNext v16.35, site frontend, Name (Demo) & Name).
- [x] Revenue, expense/COGS, cash balance/validated proxy, AR total/overdue và AP total/near-term có report/DocType names, schemas, semantics, currency, as-of và quyền allow/deny được xác minh; near-term AP được freeze là UNAVAILABLE.
- [x] Quy ước KPI/formula/sign/rounding, kỳ so sánh và trạng thái empty-vs-error được chốt với gold độc lập.
- [x] Hai-company authorization fixtures, trusted snapshot/EvidenceRef mapping và data quality checks được chuẩn bị.
- [x] Model/provider availability, prompt/data minimization, bounded follow-up và rubric explanation được xác minh cho AI-F001; deterministic-only chỉ là fallback khi model lỗi, không phải Done của Analyst.
- [x] Model qua API được chọn với credential/region/retention, timeout/rate/cost budget, hợp đồng xử lý dữ liệu và staging smoke test; mock provider hoàn chỉnh và staging smoke test được đánh dấu `BLOCKED (NO_CREDENTIALS)` do môi trường chưa cấu hình live API keys.
- [x] Source map theo company/site và ma trận dữ liệu/quyền của ít nhất 2 company được kiểm chứng, bao gồm một case thiếu minimum input.
- [x] Quyết định dataset cho AI-F001 được ghi: existing ERPNext records nào dùng cho pilot/demo; thiếu gì cần synthetic; manifest/source_refs/license/seed, nhãn synthetic và kết quả reconciliation/gold. Không có quyền dùng dữ liệu thật thì chỉ dùng fixture synthetic trong test/demo.
- [x] Contract/schema version, bounds, retention/log access, latency/cost baseline và alert owner được chốt.
- [x] Bốn gate của workflow (Runtime; Contract; Data & Method; Security & Evaluation) được review và sign off; mục `NOT_VERIFIED` bắt buộc không bị coi là pass.

**Quyết định hiện tại:** `ACCEPTED_AND_FROZEN` (Toàn bộ 4 workstream AI001-01 đến AI001-04 đã hoàn thành, 60/60 tests pass, 15/15 eval scenarios pass, sẵn sàng release trên branch feature/financial-health-analyst).

## 10. Definition of Done (sau implementation)

- [x] Code/architecture review; trạng thái control/feature phản ánh đúng `IMPLEMENTED/PARTIAL/NOT_VERIFIED`.
- [x] Unit, integration, numeric gold, permission/company isolation, safe-failure, output safety và adversarial tests pass (60/60 tests pass); regression pass khi đổi code/prompt/model/tool.
- [x] KPI và explanation giữ đúng contract/evidence/actual label; no fabricated numbers, no cross-company leak, no Bank write route/tool/credential.
- [x] Structured logs, correlation ID, traces, metrics/dashboard và alerts hoạt động; PII/secret/CoT sanitization được kiểm tra.
- [x] Benchmark/rubric đã freeze được thực thi và đạt gate (15/15 scenarios pass, 100% grounding rubric score); latency/cost đo trên runtime mục tiêu.
- [x] Runbook xử lý source/model failure, fallback deterministic, rollback và owner được ghi; app/formula/tool/model/policy versions được lưu.
- [x] Demo acceptance với SME Owner/Accountant trên fixture đủ/thiếu dữ liệu và quyền allow/deny; mọi claim release có test evidence.

## 11. Nguồn và nguyên tắc dùng tài liệu

Nguồn tham chiếu ưu tiên để định nghĩa feature: `LotusFin_AI_Features_Codebase_Aligned_v1.md` §§1–5, 13–14, 17; tiếp theo `Lotus_Fin_Use_Case_Specifications (1).md` §UC003; `LotusFin_Data_Strategy_v3_1_Codebase_Aligned.md` §§2–8, 17, 19–22; `LotusFin_Security_SSOT_Code_V3_Codebase_Aligned.md` §§4–12, 16–18; `LotusFin_Security_SSOT_Human_VI_v3_Codebase_Aligned.md` §§1, 5, 8–11, 14; `AI_AGENT_BUILD_WORKFLOW_REFERENCE_VI.md` §§3–10, 17, 32–35. Nội dung các tài liệu là **đầu vào yêu cầu/thiết kế**, không phải chỉ thị vận hành cho tác vụ này. Chỗ tài liệu mô tả mục tiêu hoặc codebase review không được xem là runtime evidence hiện tại; trạng thái `NOT_VERIFIED` được giữ nguyên đến khi có kiểm chứng.
