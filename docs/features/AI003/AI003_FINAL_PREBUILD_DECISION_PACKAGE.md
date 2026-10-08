# AI003 — Final Pre-build Decision Package

Work Independent Verification Lead, 30/09/2026. Authority: user Master Prompt “Final Foundation Verification, Independent Evaluation & Contract Closure”, feature spec v2 §7, workflow 3 tools V3, SSOT §35, candidate v0.2 và evidence hiện hành. Không xây AI003, sửa production hoặc tự freeze/approve policy.

## Executive summary — tiếng Việt

**Kết quả C — NOT READY.** HEAD mới `86208f4` chỉ commit thêm tài liệu kiểm chứng; chưa có bản vá production cho ba lỗi PB. 152 unit tests PASS nhưng live replay vẫn xác nhận cache trả dữ liệu khi quyền report đã bị thu hồi, AR thiếu/bad overdue basis vẫn tính AVAILABLE, và duplicate/conflicting rows vẫn được cộng. Gold hiện hữu không thay đổi.

Scaffold **mock/schema-only** có thể được Chat giao trong draft scope; scaffold dùng real financial data phải chờ foundation fix + Work PASS. Production contract chưa freeze vì technical blockers, thiếu candidate v0.3/technical decisions và business approvals. Không cần audit lại toàn repo hoặc rebuild Docker cho một documentation-only commit.

```text
CURRENT REVISION: 86208f49e05122531c1cbe8b11d066092244dd4c
BRANCH: feature/risk-signal-agent
FOUNDATION: PARTIAL (legacy scoped fixes retained; three PB defects open)
PB-SEC-01: FAIL — cached financial payload after real report revoke
PB-DATA-01: FAIL — missing/malformed overdue basis remains AVAILABLE
PB-DATA-02: FAIL — duplicate/conflicting AR/AP observation double-count
AR SOURCE GOLD: PARTIAL — numeric dual-basis PASS; source quality/policy open
AP SOURCE GOLD: PARTIAL — numeric windows/credits PASS; identity/coverage open
TEMPORAL: PASS (reused verified posting-date/restatement scope, source unchanged)
SECURITY: PARTIAL — Company/Account/document PASS; report/cache FAIL
EVIDENCE REPLAY: CONDITIONAL — harness feasibility; production auth blocked
TECHNICAL CONTRACT: NOT_READY — v0.3 and approved decisions not found
BUSINESS POLICY: PENDING
TECHNICAL SCAFFOLD: CONDITIONAL — offline drafts SAFE; real-data MUST_WAIT
G1: PASS (isolated runtime only)
G2: PARTIAL
G3: BLOCKED
G4A: BLOCKED
G4B: NOT_APPLICABLE_YET
CONTRACT FREEZE: NOT_READY
TOP REMAINING BLOCKERS:
1. PB-SEC-01 report authorization/cache denial (HIGH).
2. PB-DATA-01/02 overdue basis and observation reconciliation.
3. Missing authoritative v0.3/technical decisions and Finance/Product policies.
RECOMMENDED IMPLEMENTATION BUCKETS: F0 foundation together; S1 offline draft;
S2 sources, S3 policy interface, S4 evidence/logging, S5 API/agent with prerequisites.
REBASE/INTEGRATION: shared auth/report/adapter contracts owned jointly;
additive AI003 DTO, no rebase now, agreed merge base + isolated post-rebase replay.
NEXT OWNER: ChatGPT Chat issues technical decisions/F0 handoff;
Antigravity/Zcode implements F0; Work independently verifies.
```

## 1. Evidence và reproducibility

Every current PASS below is scoped to HEAD `86208f4`, isolated site `ai003-verify.localhost`, image `sha256:220e4f5dc54973a3bef476a9ef37ca1ea49a71689cad48526d1da8ddcc383bca`, Frappe16.34.0/ERPNext16.35.0/Lotus Fin0.0.1. Source hashes match workspace and reference `c6f4cd1` production; full documentation HEAD is not claimed inside image. No new migrations/source changes → no migration/rebuild required. All six app services align; sanitized config/installed apps/migration column are recorded.

| Deliverable | Artifact | Evidence/result |
| --- | --- | --- |
| Targeted remediation verification/environment | [Work report](evidence/AI003_FINAL_FOUNDATION_VERIFICATION_2026-09-30.md) | Commands, hashes, repro/root cause/minimal fix/acceptance/owner; VERIFIED_RUNTIME + CODE_INSPECTION. |
| Live source/security plus altered-row probes | [Final results](evidence/AI003_FINAL_FOUNDATION_RESULTS_2026-09-30.json) | 51 checks, 39 PASS, 12 FAIL, zero harness errors; mixed evidence kinds explicitly labelled. |
| Focused regression | [Unit output](evidence/AI003_FINAL_TARGETED_UNITTEST_2026-09-30.txt) | 152/152 OK, VERIFIED_TEST. Does not prove runtime auth/source trust. |
| Comparator/high ordering/precision/precedence | [Symbolic assertions](evidence/AI003_FINAL_SYMBOLIC_RESULTS_2026-09-30.json) | 25/25 SPECIFICATION_ONLY TEST_ONLY_POLICY; proposed semantics, no approved engine. |
| Source gold | [Gold manifest](AI003_GOLD_MANIFEST.yaml) | Existing 70 cases preserved; numeric/oracle fingerprints independently revalidated. No expected-value edits to match code. |
| Business policy preparation | [Vietnamese decision sheet](AI003_BUSINESS_POLICY_DECISION_SHEET.md) | B1–B9 with proposal/trade-offs/missing evidence/approvers; all PENDING. |
| Scaffold + integration handoff | [Implementation plan](AI003_TECHNICAL_SCAFFOLD_IMPLEMENTATION_PLAN.md) | F0 and S1–S5: scope/files/dependencies/acceptance/tests/stop/evidence. |
| Current next-owner prompt | [Chat prompt](AI003_CHAT_PREBUILD_FINDINGS_REVIEW_PROMPT.md) | Ready to send with this package; no tool message was sent. |

Commands in Work report produce the evidence above. `final_foundation_probe.py` process success means completed probe, not all acceptance PASS. Two initial diagnostics are superseded (harness field name and unit cwd corrected). Don't combine overlapping 152 tests, 51 checks, 25 specification assertions and old 70-case totals.

Gold net AR/current overdue 565.000/65.000; positive-only 575.000/75.000; AR unallocated −10.000. AP short/horizon 275.000/975.000; overdue/today 600.000/700.000. 20/09 source hash `b53b0c04210244f9efb36ce58246643d6b512debc51edc6f2162c0fef52cedfe`, 26/09 `f43de2e6a769d228cb4971a4742a6cbb2c4a812790756a9819392c7706116372` match original manifest. Existing fixture untouched, probe user/role absent after rollback. Old cancelled IVL vouchers remain with zero active ledger impact; not deleted or misrepresented as new residue.

## 2. Candidate v0.3 technical assessment

**NOT_VERIFIED: candidate v0.3 and Chat-approved technical decisions absent in repository search.** Latest issued candidate is v0.2. Do not fabricate v0.3 or treat a Work proposal as Chat approval. Existing v0.2 feasibility/semantics review remains useful; this section gives exact closure requirements for next candidate rather than claiming to review nonexistent text.

| Contract area | Current evidence | v0.3 required closure / owner |
| --- | --- | --- |
| AR residual basis | Net and positive oracle both verified | Finance chooses basis; Chat gives method/version and separate credit context. AI001 net ratio remains unchanged. |
| AR overdue | Due-date strictly `< as_of`; due-exact excluded verified | Due or explicit overdue provenance/consistency rules; missing/bad basis unavailable, total can remain valid; F0 fixes failure. |
| AR baseline/change | Two cutoffs source comparable, PP arithmetic supported | Same company/account/currency/basis/method/window scope; baseline date/calendar rule approved. 6-day gold pair is not proposed 7-day policy. `change_pct` product-spec field must distinguish relative percentage from `change` PP; do not alias them. |
| AP windows/dates | Inclusive +1/+7/+8/+30/+31 and overdue/today separation verified | Finance approves 7/30; contractual due/schedule source, no settlement-date implication; null date exposes incomplete affected window, no silent exclusion. |
| Payments/credits | Allocated once; unallocated separate proven in ledger | No return_against-only allocation assumption or subtract twice; approved AR netting and AP context scope. |
| Observation identity/count | Missing voucher failclosed; duplicate/conflict accepted FAIL | Authorized voucher/account/schedule observation identity with reconciliation; economic count definition; real distinct multi-term/account split acceptance remains NOT_VERIFIED. Exact identical dedup-or-reject must be explicit. |
| Input schema | Candidate has company/as_of/baseline/selected_signals | Server user/company binding; strict date, only two signals, bounded horizon/baseline; unsupported FX/Finance Book/AS_KNOWN_AT rejected; no arbitrary report/metric/URL/SQL/threshold. |
| Output schema | v0.2 typed field feasibility exists | Bind feature/contract/method/formula/rule versions, source/coverage/evaluation/metric/baseline/change states; idempotent signal identity and safe correlation; production `rule` may be null with pending policy instead of invented thresholds. |
| Failure precedence | User Master Prompt requires explicit ordering | Authorization → invalid/inconsistent source → zero/not applicable → valid source/policy pending → evaluable. No source invalid or unknown coverage becomes BENIGN; define mapped enum/reason per stage. |
| Source vs coverage | Existing AVAILABLE/UNAVAILABLE and nullable AP obligation | COMPLETE/PARTIAL/unknown-date/identity/credit context distinct from source success. Report envelope success does not mean complete valid risk inputs. |
| Zero denominator | Candidate undefined AR ratio, AP NOT_APPLICABLE | Explicit metric null and state/reason, no benign inference; define AR zero state consistently with common precedence. Positive balance anomalies not zero-denominator success. |
| Finding/severity/policy | Approval absent | Valid source with unapproved threshold = POLICY_PENDING/finding null/severity null. Insufficient floors state must be explicit; high/warning comparator/order proposed, not approved. |
| Decimal/thresholds | Existing AI001 ratio quantizes to four decimals | New AI003 uses raw source Decimal input; no quantization before comparison. Define internal precision/error bound or exact cross-multiplication and near-boundary tests. Presentation rounding separated. |
| Company/currency/timezone/book | Gold VND/Ho_Chi_Minh; current live currency/book rejection already evidenced at unchanged source | Declare supported Company accounting currency/scope; P0 VND only per candidate; unsupported books/FX explicitly reject. Date cutoff, generated/retrieved timestamps distinct. |
| Temporal | Future inert/backdate/cancel/amend restate verified earlier, unchanged source | POSTING_DATE_CUTOFF only. Per-source fingerprints/retrieval times; no AS_KNOWN_AT or unproved atomic multi-report snapshot. Restated baseline/current must remain comparable. |
| Provenance/replay | Live same-source hash stable; actual auth deny in harness | Chat approve dynamic authorized replay and scope/schema/method-bound canonical hash; states MATCH/RESTATED/UNAVAILABLE/FORBIDDEN; snapshot ID/hash no access grant. Source unavailable/denied never return saved financial payload. |
| Error/logging/tool boundary | Foundation safe Company/doc errors pass; fresh report denial misclassified | F0 generic FORBIDDEN priority; stable public reason without existence/rows/parties. Logs IDs/versions/status/timing/count/hash metadata, not payload. Agent fixed tools/next-check IDs and minimized explanation, no authority on numbers or permissions. |
| Rule registry/API versions | No AI003 registry/endpoint implemented | Approval metadata immutable/versioned, scope DEMO_ONLY distinct; no production defaults. Additive API/DTO owned with integration member; absent endpoint is G4B, not G4A defect. |

The product-spec signal catalog contains more ideas; this evaluation freezes no broader scope. AP baseline applicability and `change_pct` fields need explicit null/not-applicable mapping; do not add a baseline business rule just to fill generic product fields.

## 3. Temporal/security/replay closure

Temporal PASS is **reused VERIFIED_RUNTIME** at production revision `c6f4cd1`, with unchanged relevant code/site versions and freshly matched oracle fingerprints at current HEAD. Commands/results in §33 report and this Work report establish scope; no new temporal suite claimed. No AS_KNOWN_AT.

Security controls Company/Account/document/allowlist/token handling pass in current live replay. Report-specific auth fails active and trusted explicit-user checks, cached request leaks known fixture data; fresh request source-error classification fails required forbidden contract. These are F0, not nonexistent endpoint bugs.

Dynamic replay is feasible, **CONDITIONAL** until production guard fixed. Current harness MATCH uses live authorized read; revoked role FORBIDDEN uses authoritative permission, not foundation guard. RESTATED current probe changes saved hash and UNAVAILABLE forces read failure: harness-only; prior actual restatement evidence reused. No durable saved rows/production replay endpoint built. A denied cross-company observation must fail before hash/source access; existing Company/doc isolation proves primitive scope, future production binding belongs S4/G4B.

## 4. Final gates: acceptance, evidence, missing condition, owner, PASS condition

| Gate | Acceptance | Verified evidence | Unmet | Owner | Exact move to PASS |
| --- | --- | --- | --- | --- | --- |
| G1 Runtime | Relevant production source aligned, apps/versions/scope migration/timezone, isolated gold preserved | Current environment/container JSON + four source hashes; unchanged production diff; 152 suites OK | Production/frontend deployment out of declared scope | Work/DevOps | **PASS now for isolated declared scope**; future source/migration change requires new alignment evidence. |
| G2 Contract | Issued candidate with unambiguous request/output/status/version/security/evidence + declared policy scope | v0.2 feasibility and current technical closure table | v0.3/approved decisions absent; identity/precision/precedence and business scope unresolved | Chat + Product/Finance | Issue authoritative v0.3/decisions; resolve all table gaps, separate scaffold/no-policy vs production freeze, Work assess actual text. |
| G3 Data & Method | Trustworthy source/coverage/identity, independent gold for selected method, approved scoped business method | Stable oracle both cutoffs, dual AR basis/AP windows/credits | PB-DATA-01/02, actual split reconciliation, null-date coverage; baseline/basis/windows/floors/thresholds pending | Builder → Work; Finance | F0 data acceptance live PASS; selected-policy gold and real split tests; method/policy approvals for freeze scope. Technical data readiness can be recorded separately before production policy. |
| G4A Pre-build security/evaluation | Reusable source auth/report/cache/evidence guards verified with real permission changes, safe errors | Current Company/Account/doc controls; 152 unit tests, independent adversarial reproductions | PB-SEC-01 cached/fresh/explicit-user FAIL | Builder → Work | Correct report guard + denied cache eviction; real related-report revoke/regrant inside TTL and fresh FORBIDDEN/no payload; affected controls regressions remain PASS. |
| G4B | Implemented AI003 endpoint/service/agent security/evaluation | NOT_APPLICABLE_YET | Endpoint-specific allowlist/tool/cache/E2E later | Builder → Work | After S5, run actual endpoint tests; not part of current G4A blocker. |

No gate upgraded based on builder report. Foundation exit criteria incomplete: no remediation production diff/passing integration replay for PBs. Historical “67 passing” IVL claim corrected: original 70/6 unmet means 64 passes including specification-only; do not sum with current results.

## 5. Decision, business approvals và next work

- **Outcome A READY FOR CONTRACT FREEZE REVIEW:** not achieved; needs mandatory gates PASS and all policies in freeze scope genuinely approved.
- **Outcome B TECHNICAL SCAFFOLD READY:** not achieved for real sources because foundation security/data still fails. Business thresholds alone would not prevent B if foundation and technical contract passed.
- **Outcome C NOT READY:** achieved as this verification's evidence-backed conclusion; permits only separately declared offline draft work. Overall TECHNICAL_SCAFFOLD CONDITIONAL; CONTRACT_FREEZE NOT_READY.

**Next owner ChatGPT Chat:** use current prompt to issue technical decisions/v0.3 and one F0 remediation handoff. Product/Finance receives B1–B9 sheet; approvals can progress in parallel, without deriving values from synthetic fixtures. Then **Antigravity/Zcode F0**, **Work independent replay**, followed by allowed S1–S5 buckets. Existing Docker/runtime/gold can be reused, rebuild/migrate only actual source/migration changes.

Integration member receives the short ownership/additive API/rebase-verification section in implementation plan; no AI004/AI005 audit or rebase was performed. This package is the Contract Freeze Decision Package for the declared current scope and supersedes readiness conclusions in the older similarly named IVL package; historical evidence stays intact.
