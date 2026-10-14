# LOTUS FIN — P2-B Wire Contract

12/10/2026 · Asia/Saigon · **FROZEN cho DTO/private offline core sau correction F01–F03.**

Authority: [P1 MASTER](CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md), actual source và [correction](CHATBOT_P2A_F01_F03_CORRECTION.md). Đây là contract để xây UI với fixtures; **không xác nhận live HTTP/ERP, không cho phép enable transport hoặc deploy**. Builder/self-verification; independent recheck mới chưa thực hiện. G10 vẫn BLOCKED riêng.

## 1. Source và ranh giới đang hoạt động

Source dưới `lotus_fin/lotus_fin/`:

- Requests và ContextData: `presentation/dto/invoice_action_request.py`.
- Filters/rows/page: `domain/schema/invoice_read.py`.
- Open wire projection: `presentation/dto/invoice_action_response.py`.
- Outcome/source: `domain/schema/action_outcome.py`, `presentation/dto/action_outcome.py`.
- Status/header/safe messages: `presentation/response/action_response.py`.
- Terminal audit: `presentation/response/invoice_action_delivery.py`.
- Fresh scope: `infrastructure/security/frappe_invoice_authorizer.py`, `application/service/resolve_read_context.py`.
- Read orchestration: `application/service/search_invoices.py`, `application/service/open_authorized_invoice.py`.

Ba method declarations **đã tồn tại**, không tạo endpoint mới trong correction:

|Method path hiện có|Capability|
|---|---|
|`/api/method/lotus_fin.api.invoice_actions_api.get_context`|`invoice.context`|
|`/api/method/lotus_fin.api.invoice_actions_api.search_invoices`|`invoice.search`|
|`/api/method/lotus_fin.api.invoice_actions_api.open_invoice`|`invoice.open`|

Declarations ghi authenticated POST, `allow_guest=False`. **Public API hiện chỉ chạy disabled helper; không nối resolver/read services/required terminal sink.** Controller search/open unconditional disabled, kể cả config synthetic `enabled=True`. Controller get_context có positive private offline composition khi config và sink đủ điều kiện. Không suy ra live principal/CSRF/HTTP PASS từ controller tuple.

API hiện trả dictionary `{message: body}` và dùng `frappe.response.status_code/headers`; Frappe wrapping/status/header thực tế chưa qualified, có nguy cơ double `message`. **P2-B không recursively unwrap để che lỗi, không nối transport này.** Sau qualification riêng, decoder mới chỉ nhận một approved bare Outcome hoặc đúng một `{message: Outcome}`; không chấp nhận `message.message`, legacy chat/widget/provider envelopes, raw error hoặc transport200 như bằng chứng success.

## 2. Envelope và IDs

```typescript
type Capability = 'invoice.context' | 'invoice.search' | 'invoice.open';
type Status = 'OK' | 'PARTIAL' | 'FORBIDDEN' | 'SOURCE_ERROR' | 'TIMEOUT' | 'NOT_AVAILABLE';
type Outcome<T> = {
  contract_version: 'p1.invoice.v1';
  status: Status;
  reason_code: ReasonCode; // closed matrix ở §7
  correlation_id: string;
  request_id: string;
  capability: Capability;
  source: SourceEvidence | null;
  context_version: string | null;
  data: T | null;
  user_message: string;
};
```

Extra fields bị forbid tại typed DTO. `user_message` tối đa256 ký tự, serializer thay bằng safe Vietnamese template tương ứng reason. Render text thuần; không HTML hoặc instruction. Unknown version/status/reason/capability, inconsistent status/reason/data/source → decoder fail closed và xóa protected state; không tự map thành OK.

Client tạo UUID4 `request_id` cho từng thao tác. Valid ID, kể cả uppercase, được echo nguyên. Missing/wrong-type/malformed/UUID1 → replacement UUID4 + INVALID_REQUEST trong typed boundary; recognized authorization denial giữ precedence. Request ID không là idempotency, permission hoặc approval. Không tự retry.

CID do server tạo; private helper có thể nhận trusted internal CID. UI không gửi CID làm authority. Qualified response phải header CID = body CID = terminal-event CID, đúng current RID/capability/context/generation. Actual framework pre-handler failures có thể không có typed envelope/CID; coi là transport failure, không giả typed success.

Private serializer headers: `Content-Type: application/json; charset=utf-8`, `X-Correlation-ID`, `Cache-Control: no-store, no-cache, must-revalidate`, `X-Content-Type-Options: nosniff`. Actual HTTP wrapping/header/status/session/CSRF/origin và raw-body16KiB/duplicate-key enforcement đều **NOT_RUN**. Không dùng cookie/API-key/Admin/CORS workaround để tự qualified.

## 3. get_context

```typescript
type ContextRequest = { request_id: string; company_candidate: string };
type ContextData = {
  context_ref: string;
  context_version: string;
  company_label: string;
  allowed_filters: ['invoice_name_prefix', 'posting_date', 'docstatus'];
  default_posting_from: string; // YYYY-MM-DD
  default_posting_to: string;   // YYYY-MM-DD
  expires_at: string;          // ISO8601 UTC, actual signed claim
};
```

`company_candidate`: required strict string1–128 ký tự; chỉ candidate, không Company authority. Exact Company/read/current actor phải được server xác nhận. Actor/SID/site/product/connection/key/policy không nhận từ body. Không tự chọn company toàn cục.

Authorized default date = ngày từ server `observed_at_utc` chuyển qua site IANA timezone lấy bằng `frappe.get_system_settings('time_zone')`. `to=today_site`, `from=today_site−89 ngày`, **90 ngày inclusive**. Missing/unavailable/empty/invalid site timezone hoặc unmapped site fail safely TARGET_UNQUALIFIED; không fallback UTC/hardcoded Việt Nam.

`expires_at` bằng chính `expires_at` của context token đã xác minh chữ ký, không phải request deadline. Default token TTL300s; default request deadline5000ms. Controller đọc expiry từ effective signed claim, kể cả codec phát token TTL ngắn hơn config; không cộng TTL vào thời điểm response để fabricate expiry. ContextData không chứa secret/raw actor/SID.

Context_ref giữ P1 `ref.v1`; version ổn định cùng read-family scope xuyên context→fresh search→fresh open. Scope fingerprint bind actor/session/trusted site/product/site-ref/company/connection/version, contract `p1.invoice.v1`, projection `invoice.min.v1`, timezone và current config/policy/key material. Capability không là scope identity; allowlist kiểm riêng mỗi lần resolve. Scope/config/key/timezone đổi làm refs cũ invalid. Token không cấp quyền đọc.

UI dùng defaults này và xóa handles khi `now >= expires_at`; refresh context cần thao tác mới, không giữ ref cũ. Codec P1 v1 vẫn giữ historical `now > expires_at` verification, không sửa equality semantics trong batch. P2 selection/cursor v2 reject `now >= expires_at`. UI không decode token hoặc suy ra expiry của selection/cursor từ ContextData; chúng không có separate public expiry field.

## 4. Search request

```typescript
type Filters = {
  invoice_name_prefix?: string | null;
  posting_from?: string;
  posting_to?: string;
  docstatus?: 'DRAFT' | 'SUBMITTED' | 'BOTH';
};
type SearchRequest = {
  request_id: string;
  context_ref: string;
  expected_context_version: string;
  invoice_type?: 'SALES'; // actual DTO default SALES; UI nên gửi SALES rõ ràng
  filters: Filters;      // REQUIRED object
  page_size?: number;    // omitted →20; integer1..50, never null/bool/string
  cursor?: string | null;
};
```

`context_ref` required1–2048 ký tự; `expected_context_version` required1–128. Filters missing/null/array/string bị reject. `{filters:{}}` valid. `page_size:null` bị reject. Only both dates **genuinely omitted** mới default90days; any explicit null, one missing, wrong type, noncanonical ISO date, reversed, future hoặc inclusive range>365days → INVALID_REQUEST trước read. Revalidation giữ `exclude_unset=True`, không repair explicit null.

Prefix optional, actual DTO vẫn cho null; UI nên omit khi không dùng. String≤128 ký tự, NFC, reject empty/whitespace/control/NUL. `%`, `_`, quotes và prompt-like content chỉ là dữ liệu prefix; không query language. Port thật phải parameterize/escape và qualify collation; chưa thực thi ERP query trong batch.

Default docstatus BOTH chỉ 0/1, DRAFT→0, SUBMITTED→1; Cancelled2 không được trả. Không coi docstatus là overdue/unpaid/risk. `cursor:null`/omitted là first page; empty/forged string không là default và bị reference verification từ chối. Subsequent page giữ cùng normalized filters/page_size/window/context; query mismatch STALE_CURSOR, không auto broaden/reset query.

Extra scope/RPC/query controls bị forbid: company/user/session/site/product/connection, invoice_id/doctype/fields/SQL/order/offset/method/URL/report/source-mode/financial-as-of. LLM/NL không cung cấp authorization hoặc arbitrary executor. Public disabled search vẫn trả CAPABILITY_DISABLED; các validation/port-zero assertions ở đây là DTO/private offline core, không claim active HTTP INVALID_REQUEST route.

## 5. Search result và selection

```typescript
type InvoiceRow = {
  invoice_type: 'SALES';
  invoice_id: string;
  posting_date: string;
  docstatus: 0 | 1;
  record_version: string;
  selection_ref: string | null;
};
type SearchData = {
  items: InvoiceRow[];
  returned_count: number;
  total_count: null;
  page_complete: boolean;
  has_more: boolean | null;
  next_cursor: string | null;
  selection_required: boolean;
  limitations: Array<'COVERAGE_INCOMPLETE' | 'LIVE_WINDOW'> | null;
};
```

Current private service emits limitations list (`[]` nếu complete không có limitation); schema cũng cho null. Row identity≤128, record_version opaque≤64. **Không customer_label/amount/currency/items/taxes/attachments/child fields** trong projection hiện tại. Display invoice ID, posting date và badge Nháp/Đã ghi sổ; record_version/ref là internal handle, không financial evidence hoặc click authority.

returned_count=items.length, no duplicates, không global count; total_count luôn null. Complete zero rows → OK/EMPTY_RESULT, selection_required=false. Complete nonempty → OK/RESULTS_FOUND, selection_required=true kể cả chỉ một row. **Chỉ explicit user click lên complete current result có selection_ref mới gửi open**; không auto-open, không lấy invoice_id làm URL/RPC authority.

Server fixed `name ASC` keyset; signed cursor bind normalized filters/page_size/order/authorized last/upper bound/window/page index. Max5pages trong private profile. has_more=true cần verified next_cursor và thêm authorized observation từ port; không hidden count hoặc whole-company completeness. Database ordering/lookahead/actual row authorization chưa live qualified.

PARTIAL/COVERAGE_INCOMPLETE: source.coverage=INCOMPLETE, page_complete=false, has_more=null, next_cursor=null, **mọi selection_ref=null**. Zero rows incomplete vẫn PARTIAL, không EMPTY_RESULT. Display safe incomplete subset; disable selection/open/paging handles. Không repair ref/null, invent false has_more hoặc tạo fake total. Refine/restart chỉ do người dùng.

Selection là signed `ref.v2`, purpose invoice.open, scope/contract/projection/key/expiry/exact doc/record_version/query binding. Wrong actor/session/site/company/connection/purpose/key/tamper deny; scope/config/policy change invalidate. Same-scope replay phải fresh authorize/read, không cache grant; revoked rights thắng stale version. Signed không encrypted; UI giữ token opaque trong memory, không decode/log/store/send LLM.

## 6. Open request và five-field document

```typescript
type OpenRequest = {
  request_id: string;
  context_ref: string;
  expected_context_version: string;
  selection_ref: string;
};
type MinimumDocument = {
  invoice_type: 'SALES';
  invoice_id: string;
  posting_date: string;
  docstatus: 0 | 1;
  record_version: string;
};
type OpenData = {
  document: MinimumDocument;
  company_label: string;
  navigation: { kind: 'LOTUS_READ_VIEW'; view: 'sales-invoice-minimal-v1' };
};
```

All OpenRequest fields required; refs1–2048, expected version1–128. Null selection và extras reject. Document **đúng năm field**, không selection_ref/company_label/navigation lồng trong document. Company label và fixed descriptor ở outer data. No arbitrary URL, native ERP Form/getdoc, run_method, full document hoặc child expansion.

Private open core verifies v2 selection trước requested-document port call; port được gọi lại với current authorized context/exact selected ID/record_version/budget. Returned identity/company/projection/source phải khớp; version changed → STALE_SELECTION; explicit denial thắng changed/deleted/source details. Actual Company/DocType/document/field/masking/cache-revocation enforcement tại ERP port vẫn NOT_RUN; concrete adapter chưa được qualified. Expected context_ref/version và fresh resolver composition phải qualify khi controller được nối ở task riêng; current public open disabled.

## 7. Six statuses, closed reasons và HTTP mapping

|Status|Reason codes|Private serializer HTTP|
|---|---|---|
|OK|CONTEXT_READY, RESULTS_FOUND, EMPTY_RESULT, DOCUMENT_READY|200|
|PARTIAL|COVERAGE_INCOMPLETE|200|
|FORBIDDEN|AUTH_REQUIRED|401|
|FORBIDDEN|CSRF_OR_ORIGIN_DENIED, COMPANY_DENIED, CAPABILITY_DENIED, ACCESS_DENIED|403|
|SOURCE_ERROR|SOURCE_FAILURE, INVALID_PROVIDER_RESPONSE|502|
|TIMEOUT|DEADLINE_EXCEEDED|504|
|NOT_AVAILABLE|INVALID_REQUEST, CONTEXT_REQUIRED, PROJECTION_UNAVAILABLE, UNSUPPORTED_INTENT, INVALID_OUTCOME|422|
|NOT_AVAILABLE|CONTEXT_CHANGED, STALE_SELECTION, STALE_CURSOR|409|
|NOT_AVAILABLE|DOCUMENT_UNAVAILABLE|404|
|NOT_AVAILABLE|TARGET_UNQUALIFIED, CAPABILITY_DISABLED|503|

Mọi FORBIDDEN/SOURCE_ERROR/TIMEOUT/NOT_AVAILABLE: data=null, source=null, no executable ref/action. Missing source không là zero/empty result. Denial tại trusted HTTP401/403 hoặc recognized outcome/nested denial thắng success/data/widget. Không retry source errors sang demo/legacy/LLM; không báo quyền từ status200.

Unknown/malformed/inconsistent response là local invalid/transport failure, xóa protected state. Raw framework405/413/CSRF errors có thể không theo envelope; chưa qualify. Không invent seventh business status hoặc approved429/admission policy. Cancellation là local lifecycle, không business status.

## 8. Source labels, audit và disabled behavior

```typescript
type SourceEvidence = {
  mode: 'ERP_READ' | 'DEMO_ISOLATED';
  verification: 'AUTHORIZED_READ';
  product_ref: string;
  site_ref: string;
  connection_ref: string;
  connection_version: string;
  projection_version: 'invoice.min.v1';
  observed_at: string;
  timezone: string;
  coverage: 'PAGE_COMPLETE' | 'INCOMPLETE';
  consistency: 'LIVE_KEYSET';
};
```

Success phải có current matching source/scope/version/timezone. Label “Đọc được phép · thời điểm quan sát · phạm vi trang” và cảnh báo incomplete nếu cần. AUTHORIZED_READ không là VERIFIED financial analysis, snapshot hoặc whole-company completeness. DEMO_ISOLATED nếu dùng fixture phải hiện rõ dữ liệu mô phỏng; không fallback từ ERP failure thành demo.

Private required delivery: healthy sink đúng1 RESPONSE_DELIVERY attempt=ack=line, IDs/status/capability khớp. Missing sink → no admission, null disabled response,0ack. Sink write/flush/ack failure → safe ActionEventDeliveryError, không protected success/retry. ACK không chứng minh durability/retention production. Không log raw actor/SID/key/ref/queries/rows/doc/customer/financial values. Frontend chỉ diagnostic bounded reason/status/CID, không dump body.

InvoiceActionsConfig.enabled mặc định False. Public helper luôn disabled; controller search/open luôn disabled. Valid RID trong disabled response →503 NOT_AVAILABLE/CAPABILITY_DISABLED/null; malformed RID có thể→422 INVALID_REQUEST theo existing sanitation; missing sink ưu tiên disabled. Guest/wrong-method branches và wrappers của API chưa live verified. UI action flag cũng giữ off; flag không là authorization.

## 9. Exact frontend restrictions và handoff gate

1. Chỉ xây component/state/decoder với synthetic fixture contract; **không fetch/enable current ERP/API**, không chỉnh backend flag/Docker/dependencies/permissions/G10 hoặc legacy finance shortcuts để có demo success.
2. User chọn Company candidate→get_context; user xác nhận filters→search; explicit row click→open. Không auto company/filter broadening/auto-open/retry/RPC/NL grant.
3. Một current request/generation; abort/logout/company/connection/context change/unmount tăng generation, clear rows/cursor/refs/reader. Drop late response sai RID/CID/capability/context/generation; không hiển thị error của old request vào scope mới.
4. Giữ ref/context/result trong request-local memory, no localStorage/sessionStorage/service-worker/cache/chat-history/LLM/logging. Context expiry/stale/denial→clear handles; refresh phải fresh server context/read.
5. Render text escaped. Minimum reader chỉ năm document fields + authorized outer label/descriptor; no raw HTML/native form/full-document lazy fetch/financial widgets.
6. Strict status/reason/source/projection validation; PARTIAL không actionable, failure/null không success. No recursive unwrap/coercion/synthetic repair/missing source→empty.
7. Live enablement cần task riêng: immutable serving source/import lineage, approved private target/timezone/key/map/sink, ordinary-user permission gold, actual HTTP/session/CSRF/single wrapper/status/CID/no-store, field/doc revocation, physical budgets/deadlines/audit/no-business-write và cleanup. Offline343/84 PASS không đóng các gate này.

**Freeze áp dụng DTO và fixture UI integration contract; live P2-B readiness/transport qualification chưa được cấp. Dừng ở handoff, không triển khai UI trong batch này.**
