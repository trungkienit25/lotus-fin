# LOTUS FIN — P2-A/P2-B Acceptance Recheck

12/10/2026 · Asia/Saigon · targeted backend/frontend security and product review.

|Outcome|Decision|
|---|---|
|P2A_OFFLINE_INDEPENDENT|**P2A_OFFLINE_INDEPENDENT_PASS**, technical oracle scope below|
|P2B_UI_INDEPENDENT|**CHANGES_REQUIRED**|
|P2AB_LIVE_ACCEPTANCE|**BLOCKED**; real integration tests NOT_RUN|
|CHATBOT_PROPOSAL_COVERAGE|**PARTIAL**|
|G10|**BLOCKED**, independent separate gate|

**Reviewer provenance:** cùng agent này đã trực tiếp sửa P2-A F01–F03 trước đó. Lần này tạo oracle/fixtures mới không nhập builder test fixtures, chạy assertion thực tế và giữ source nguyên; PASS trên là độc lập về oracle, **không phải independent acceptance bởi một reviewer/tổ chức khác**. P2-B source do builder khác triển khai. Không dùng builder verdict làm PASS; organizational separation của P2-A vẫn cần reviewer khác nếu release policy yêu cầu.

## 1. Authority và exact artifact

Đã đọc P1 MASTER; original [Assisted Actions Solution Design](<../LOTUS_FIN_CHATBOT_ASSISTED_ACTIONS_SOLUTION_DESIGN_VI (1).md>) và [Phase0 Round3 packet](PHASE0_WORK_TO_CHAT_PACKET.md); [V1 overdue closure](V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md); P1 final independent PASS; P2-A independent recheck/correction; P2-B implementation/evidence/frozen wire; latest target/HTTP evidence; AGENTS, ADR001, Security Code V3. Các capability L3–L5 được đề xuất không tự trở thành allowed scope. Ordinary invoice read không là PastFinalDue, local preview không là ERP Draft, fixtures không là live rights.

Repo/workspace `lotus-fin / E:/lotus-fin`, branch develop, HEAD `5f805ef34f788245a3ec0e9c2f44e224eb16c305`; dirty correction/Panel/Drawer/UI giữ nguyên. New evidence root `docs/reviews/evidence/chatbot-p2ab-independent-acceptance-2026-10-12/`. [Before manifest](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/SOURCE_BEFORE.json) khóa513protected fingerprints; không dùng Git HEAD thay bytes. Không edit implementation/tests/authority hoặc overwrite historical evidence.

Applied skills: `my-skills/code-reviewer/SKILL.md`, `my-skills/e2e-testing/SKILL.md`; GitNexus contexts cho UI presentation/controller, backend filters/search và prior target graph sources. Graph named UIDs dùng đúng repository; absence of processes không là unused/all-clear. Không source edit/commit nên không sử dụng graph để cấp quyền đổi code.

## 2. P2-A: fresh tests và12prior failures

Fresh focused run: **343/343 PASS =173P1+103existingP2+67correction regressions**, exit0/no skip. Original5P1codec methods AST identical accepted P1 snapshot. Dedicated A16 **14/14**, B03 **8/8**, both exit0. Không cộng overlapping suites thành unique coverage.

Independent oracle core **36/36 PASS**, boundary **14/14 PASS**, **50distinct checks**; boundary runner replays36core nhưng chỉ14newIDs được tính thêm. Guard explicitly forbids importing `lotus_fin.tests`, real Frappe/ERP/provider/LLM/network; private Company seam/read ports/logger only. Actual imported modules verified under current source root with SHA256. No permission grant from signed refs.

|Original ID|Fresh independent expected/observed|Decision|
|---|---|---|
|C02_CONTEXT_DATE_DEFAULTS|Exact site-local from=today−89/to=today, inclusive90; separate local midnight/year/leap/western-timezone probes|PASS|
|C03_CONTEXT_EXPIRY_IS_TOKEN_EXPIRY|Advertised timestamp exactly decoded signed claim; defaultTTL300 distinct5sdeadline,60/600TTL vs1/30sdeadline|PASS|
|C05_SAME_SCOPE_STABLE_FAMILY_VERSION|Actual resolver independently resolves context/search/open, same version|PASS|
|C06_CONTEXT_REF_WITH_FRESH_SEARCH_CONTEXT|Token from actual get_context controller verifies with freshly resolved search context|PASS|
|C08_FRESH_SEARCH_TO_OPEN_UNCHANGED_PRINCIPAL|Actual search mints v2selection, actual fresh open reaches port1/DOCUMENT_READY; no forced-version positive|PASS|
|I03_EXPLICIT_filters_None|Required object, explicit null rejected|PASS|
|I03_EXPLICIT_page_size_None|Omitted defaults20; explicit null rejected|PASS|
|I04_REQUIRED_FILTERS_MISSING|Missing filters rejected|PASS|
|I05_NULL_DATES_posting_from|Present null rejected|PASS|
|I05_NULL_DATES_posting_to|Present null rejected|PASS|
|I05_NULL_DATES_posting_from_posting_to|Both explicit null rejected|PASS|
|I05_NULL_DATE_MUST_NOT_BECOME_DEFAULT_QUERY|Actual typed boundary rejects before service/read port; INVALID_REQUEST/null/port0|PASS|

[Core oracle](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/BACKEND_ORACLE_RESULTS.json), [boundary oracle](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/BACKEND_BOUNDARY_RESULTS.json), [12-ID mapping](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/VERIFICATION_SUMMARY.json), [focused ledger](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/FOCUSED_RESULTS.json).

Per-capability exclusion independently denies all3capabilities; wrong actor/session/site/company/product/connection/context/policy/key config/tamper/purpose/expiry deny before selected port; logout no token grant; changed record stale; revoked port deny wins stale. Missing/invalid site timezone fail safely. Supplied/omitted date/page/NFC/future/range/extra-RPC cases in fresh343; no weakened assertions.

Public search/open remain disabled. INVALID_REQUEST observations are DTO/private core tests, not actual active HTTP422. Real disabled-user/middleware/DocType/field/mask/cache-revocation rights remain live NOT_RUN; synthetic port denial is protocol evidence only.

## 3. P2-B: three reproduced material findings

Existing P2-B **60/60 unit PASS** and **3/3 fixture E2E PASS** do not cover actual empty/partial-empty DTO or current source/context binding. Independent Node oracle: **23cases,12PASS/11FAIL**. Independent real React fixture DOM: **9cases,6PASS/3FAIL**. All failures cluster into the three findings below; no implementation repair in acceptance task.

### P2B-F01 — Valid zero-row backend DTO rejected [P2]

[Presentation144](E:/lotus-fin/frontend/src/pages/copilot/actions/invoiceActionPresentation.ts:144) rejects `selection_required===false` before empty/PARTIAL handling. Actual `SearchInvoicesService` emits false for zero rows via `bool(rows)`, including valid incomplete zero-row results.

Independent service→DTO→serializer→actual UI decoder:

- Completed zero rows: backend OK/EMPTY_RESULT, selection_required=false; UI `unavailable/INVALID_RESPONSE` instead of `empty`.
- Incomplete zero rows: backend PARTIAL/COVERAGE_INCOMPLETE, selection_required=false; UI invalid instead of incomplete non-actionable results.

UI03/UI04 FAIL; DOM04/DOM05 FAIL show actual notice “The response could not be verified, so nothing is shown.” and no expected empty/partial message. Nonempty DTO and reader positive controls PASS. Backend samples derive from **actual service-generated zero-row outputs**, not changing frontend expected shapes. Historical UI fixtures use selection_required=true for empty pages, hiding the mismatch.

Required correction: enforce selection flag relative to item count, allow zero-row false for complete/incomplete, keep PARTIAL no refs/open/cursor/has_more. Tests must use actual backend serialization, not edit backend to require selection for zero rows.

### P2B-F02 — ContextData decoder accepts contract violations [P2]

[Presentation181](E:/lotus-fin/frontend/src/pages/copilot/actions/invoiceActionPresentation.ts:181) treats default dates/allowed_filters as optional; it never validates exact allowed_filters tuple. [Envelope222](E:/lotus-fin/frontend/src/pages/copilot/actions/invoiceActionPresentation.ts:222) does not compare outer context_version with ContextData.context_version.

UI06/UI07/UI08 FAIL: remove both required default dates→`context/defaults:null`; supply `allowed_filters:['arbitrary_sql']`→`context`; outer version different inner version→`context`. These are malformed variants of actual corrected backend ContextData. This does **not** enable arbitrary SQL/server permission; it proves the frozen strict UI decoder is not enforced. Historical E2E context fixtures omit defaults and therefore pass through this relaxed path.

Required correction: mandatory7ContextData fields, exact filter tuple and valid approved default range, outer/inner version equality; missing/inconsistent data fails closed. Update fixture inputs to real current contract while preserving negative assertions.

### P2B-F03 — Response scope not pinned to active context [P1]

[Controller90](E:/lotus-fin/frontend/src/pages/copilot/actions/invoiceActionController.ts:90) passes RID/capability/CID to parser but no expected context/source identity. [Search141](E:/lotus-fin/frontend/src/pages/copilot/actions/invoiceActionController.ts:141) accepts result VM; [Open162](E:/lotus-fin/frontend/src/pages/copilot/actions/invoiceActionController.ts:162) checks only invoice ID and record version. Source parser drops product/site/connection/version anchors from VM.

UI10/UI11(4axes)/UI12 FAIL: current RID/CID/capability with different context_version/site/product/connection/version still becomes results/document. Validly shaped selected document with sameID/version but different site/context and company_label=`QA B` is accepted under current QA A context. **DOM03 reproduces visible QA B in actual React reader.** Generation fence/logout/HTTP403 positives still PASS; those checks do not cover same-generation wrong scope.

This is **synthetic response mismatch exposure**, not evidence of real ERP data theft or an ERP permission bypass. Production transport remains disabled and all fixture network intercepted. P1 MASTER UI01/frozen wire require current context/source identity; backend may deny a later ref but UI already displayed mismatched response bytes.

Required correction: retain expected context_version and validated source anchors from get_context, compare every successful search/open, bind open outer company_label to active authorized context. Reject/clear mismatches before render. Preserve fresh backend authorization, RID/CID/generation fences, no token decode or client authority.

### Bounded compliance observation

New `invoiceActionPresentation.ts` is **343lines**, exceeding ADR001<200; no documented variance for this new responsibility in the reviewed packet. Existing Panel variance does not automatically extend to this module. Cohesive parser/source/context/data and criteria/payload separation can be included in the same targeted UI correction; no broad React/architecture rewrite requested. Source hashes/line counts in verification summary.

## 4. What passed, engineering and harness limits

Independent positives: actual context/defaults, nonempty results and five-field open projection; explicit click even one row; PARTIAL non-actionable; logout/scope/cancellation/late-generation discard; HTTP403 clears data; no console/storage/ref navigation leak; production transport flags absent/off/on all yield disabled503 with0network. React DOM XSS text-node probe PASS, no image/execution; unmount clears results/reader. These do not waive the three negative failures.

|Fresh command/run|Result|Boundary|
|---|---|---|
|343Python focused|343PASS/exit0|Offline P1/P2core/security regressions|
|Backend core+boundary oracles|36+14distinct PASS/exits0|New independent arrangements; no builder fixture import|
|A16/B03 dedicated|14/14 and8/8PASS/exits0|Private sink/exact Company seam only|
|Node existing P2-B unit|60/60PASS/exit0|Existing fixture suite|
|Node independent UI oracle|12PASS/11FAIL/exit1|23cases against actual backend wire and new controller arrangements|
|Combined existing E2E P2-B+B1|3PASS/4FAIL/exit1|B1 teardown reports stale cached Vite websocket token; raw run retained|
|B1 E2E fresh separate process|4/4PASS/exit0|Existing page/Drawer/status/lifecycle/XSS regressions|
|Independent React DOM oracle|6PASS/3FAIL/exit1|Visible foreign-company/valid zero-row defects reproduced|
|TypeScript app+node projects|both exit0|Current projects, no emit, buildinfo directed to evidence|
|Targeted oxlint|exit0|P2-B action modules|
|Default Vite build attempt|exit1|EPERM writing protected .vite-temp config bundle; not app compile defect|
|Vite build with `--configLoader runner`|exit0|Actual full frontend build into new evidence/BUILD; chunk-size warning only|

Combined E2E failure is a **harness lifecycle limitation**, independently explained by `_OWNED_VITE_WS_TOKEN` retained across module-scoped server restarts. Separate fresh process preserved all4B1 tests/assertions and passed; no guard weakened. The three P2-B E2E tests passed in combined run. Individual historical52B1 gold runner not newly executed; no new52count claim. No browser/external traffic except owned127.0.0.1:5188 assets and intercepted fixture APIs; no ERP proxy. DOM reader/server exit and port release verified. No real hard-cancel/resource claim from these tests.

[Commands/exits](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/COMMANDS.json), `UI_ORACLE_REPRODUCTION.txt`, `UI_DOM_ORACLE_REPRODUCTION.txt` and corresponding JSON/stdout/screenshots provide exact replays. Fixture aliases under copilot_api in test harness are **not production endpoint acceptance**.

## 5. Live acceptance

Fresh read-only Docker inspect/source reader: same image `sha256:ed6e02f587eb450a0882ecb4b6fbb259d1a1f27f549e1cc4bbe21a660b3017b7`, no host source mount; **17/17selected P1/P2files MISSING**. [Current runtime identity](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/RUNTIME_METADATA.json), [source presence](../evidence/chatbot-p2ab-independent-acceptance-2026-10-12/RUNTIME_SOURCE_CURRENT.json). Python3.14.7/source Frappe16.34/ERPNext16.35 differ from host3.13.7. Bench apps.txt is not installed-site DB/apps/hook/principal proof.

No newly approved private target/snapshot/restore/cleanup/ordinary-user gold exists in supplied/current packet. Sites frontend/ai003-verify are shared/excluded; not selected. Actual principal/Company/doc/field/mask/custom hooks/GET/POST/Guest/CSRF/single envelope/CID/audit/cross-company/revocation/business+seen/view/queue before-after/cleanup/rollback all **NOT_RUN**. Runtime-source mismatch FAIL; live acceptance **BLOCKED**, ERP_NO_WRITE **NOT_RUN**; no simulated authorization PASS.

## 6. Smallest handoff and stop

First batch: frontend decoder/controller corrections for F01–F03, actual-DTo fixture regressions and cohesive ADR001 split; preserve production disabled client and B1 safety. Fresh graph impact before any edit; do not weaken assertions or change backend to match wrong UI fixtures. Regression gate: independent23+DOM9GREEN, existing60/3/B1 4, typecheck/build/lint once after final changes.

Second independent batch: approve isolated target+canonical current image/map/key/sink/ordinary-user fixture gold/lifecycle, then conditional adapter/HTTP/real no-write/resource/UI qualification. No shared rebuild or automatic enablement. PastFinalDue/L3/L4/L5 remain distinct future capabilities in [proposal matrix](CHATBOT_PROPOSAL_COMPLETION_MATRIX.md).

Current fixture **positive paths** can be shown as a limited, explicitly synthetic technical demonstration: context→generic prefix/date/docstatus search→explicit select→minimum reader, plus B1 safety. **P2-B is not fully demo/acceptance ready** until defects close; do not demo official empty/partial-empty with wrong fixtures or claim live rights/overdue/ERP Draft. No live/judge release.

**Stop after gate decisions and actionable proposal handoff. No automatic feature enablement, fixes, deployment or mutation.**
