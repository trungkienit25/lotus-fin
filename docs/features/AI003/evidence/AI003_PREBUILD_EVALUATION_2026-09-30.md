# AI003 candidate v0.2 — independent pre-build evaluation

**Verdict: NEEDS_CHANGE / CONTRACT FREEZE NOT_READY.** No AI003 implementation or financial-policy approval was made. WR-01/WR-02 remain fixed within their previously verified scope; this contract creates additional source/security requirements and exposes new concrete defects.

## Environment, authority and reproducibility

- HEAD `c6f4cd13c677e167ac645d4d0c48d236383c4fac`, unchanged from candidate basis. Production code unchanged during this evaluation.
- Docker backend image `sha256:220e4f5dc54973a3bef476a9ef37ca1ea49a71689cad48526d1da8ddcc383bca`; Frappe 16.34.0, ERPNext 16.35.0; isolated site `ai003-verify.localhost`, timezone `Asia/Ho_Chi_Minh`; approved cash scope `["Cash - A3G"]`, Company currency VND. Required Company scope column exists; prior migration evidence retained, no new full migration claimed.
- Authorities: supplied [candidate v0.2](../AI003_CANDIDATE_CONTRACT_v0.2.md), [Work prompt](../AI003_WORK_PREBUILD_EVALUATION_PROMPT_v0.2.md), current SSOT §32, feature specification v2 §7 and workflow v3. Field mapping: [feasibility table](../AI003_CONTRACT_FEASIBILITY_v0.2.md).
- Created synthetic Company `AI003 Gold 2026` (A3G), leaf customer/supplier groups and territory, one synthetic Customer/Supplier, chart/opening JE, 4 Sales Invoices, 8 Purchase Invoices, 4 Payment Entries, 2 separate-credit returns and 2 allocated-credit returns. Created voucher-free Company `AI003 Empty 2026` for genuine empty-source verification. Both on isolated site only. Existing AI002 fixture reused as denied cross-company scope; its data was not modified.
- Transient future/backdated/cancelled/amended vouchers, restricted user, User Permissions and Custom Role changes were rolled back. Final checks: probe user absent, Custom Role absent, transient invoice count zero. `frontend` was not mutated or used for tests.
- Oracle [prebuild_oracle.py](prebuild_oracle.py) reads submitted vouchers/payment references and Payment Ledger Entry attribution; **imports no Lotus Fin production metric/rule code**. It does not trust Invoice.outstanding_amount or use AR/AP reports to calculate expected residuals.
- Run commands: copy oracle/verifiers to backend `/tmp`, then `docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 /home/frappe/frappe-bench/env/bin/python /tmp/prebuild_verifier.py` and the same command with `/tmp/prebuild_additional_probes.py`. Source and scripts are saved next to this report. Generate manifest with `python docs/features/AI003/evidence/build_prebuild_gold.py`.
- Final evidence: [main results](AI003_PREBUILD_RESULTS_2026-09-30.json), [additional results](AI003_PREBUILD_ADDITIONAL_RESULTS_2026-09-30.json), [gold manifest](../AI003_GOLD_MANIFEST.yaml). **70 distinct cases: 53 live source/reusable-primitive probes and 17 specification-only cases; 6 unmet checks.** These include AP readiness gaps and two checks of the same permission defect, not six independent bugs. The separate 23-test explanation/security unittest run passed; do not add it to the 70-case total or earlier overlapping suites.
- Initial results are preserved in `AI003_PREBUILD_RESULTS_INITIAL_2026-09-30.json` as superseded diagnostic evidence. The first oracle assumed return_against proved credit allocation; posted ledger inspection disproved that. Final oracle uses actual attribution. Its initial AP mismatch is **not** claimed as a production bug. Additional allocated-credit vouchers exercise both behaviors explicitly.
- GitNexus index was stale/FTS degraded. Refresh made no progress and was interrupted; context lookup did not resolve evidence guard. No clean current graph claimed; exact current code and live probes carry the conclusions. No production symbols were edited or committed.

## Independent numeric gold

| Cutoff | AR net residual | AR overdue net residual | Ratio | AP +1..+7 | AP +1..+30 | Cluster ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-09-20 | 650.000 | 0 | 0 | 1.400.000 | 1.950.000 | 0,7179487179 |
| 2026-09-26 | 565.000 | 65.000 | 0,1150442478 | 275.000 | 975.000 | 0,2820512821 |

AR net arithmetic matches existing AI001 semantics, **not approval of netting policy**. At 26/09, positive AR residual is 575.000 and unallocated credit is -10.000; positive-only overdue is 75.000. Chat must decide scope/netting. Current/baseline net-ratio delta = 11,5044247788 percentage points; the six-day interval remains a verification pair only.

AP D1 residual = 100.000 − payment 20.000 − allocated credit 5.000 = **75.000**. D7 200.000 is included in both windows; D8 300.000 only reference; D30 400.000 only reference; D31 500.000 excluded from both. AP overdue 600.000 and due-today 700.000 are separate context. AP positive total 2.775.000; unallocated credit -10.000 remains separate, not automatically subtracted from D1. The allocated credit is counted once through residual; return_against alone does not prove allocation.

AR due-before residual 75.000 is overdue; due-exact 200.000 and due-after 300.000 are not. Fully paid invoices have zero residual and disappear from positive obligations. Existing report ageing columns default to posting-date ageing; do not use those ranges as overdue-by-due-date authority. Due-date-based arithmetic itself was verified.

## Acceptance matrix

| Group | Status | Evidence and limit |
| --- | --- | --- |
| AR numeric oracle | PASS | Two cutoffs, positive/paid/partial/allocated-credit/unallocated-credit, exact due boundary; netting remains business policy. |
| AP numeric oracle | PASS | Two cutoffs, inclusive +1/+7/+8/+30/+31, overdue/today context and credits. This verifies source inputs, not an AI003 signal implementation. |
| Legitimate empty | PASS | Actual voucher-free Company report is empty; independent denominator zero. AI003 ratio must be undefined, not benign. Existing AI001 empty-ratio zero needs explicit candidate mapping. |
| Malformed source | PARTIAL | Bad amount, missing voucher and dict summary fail closed; missing due date and exact duplicate do not. |
| AP date completeness/duplicates | PARTIAL | Adapter permits nullable due date and repeated source_ref. Null due date is an AI003 coverage/contract gap, not proof of a bug in AI002's nullable obligation contract. Exact duplicate can double-count candidate AP inputs. |
| Symbolic boundaries/materiality | PASS (spec only) | Below/equal/above for T_warning/T_high/A_min/D_min/N_min; >= uses TEST_ONLY_POLICY. Comparator, gate composition and business values remain unapproved. POLICY_PENDING produces no finding/severity in the specification. |
| Future posting | PASS | Later AR/AP posting leaves the same historical report input hash unchanged. |
| Backdate/cancel/correction | PASS (posting-date/restatement scope) | AR 565.000 → 688.000 after backdate → 565.000 after cancel → 689.000 after amended replacement; report/evidence checksum changes. AP cancelled voucher removed. Temporary vouchers rolled back. No AS_KNOWN_AT guarantee. |
| Company isolation | PASS | Allowed/denied/nonexistent Company; denied cached other-company request has no opening cash/obligations. |
| Report permission | BLOCKED | Direct ERPNext report refuses denied report, but reusable report guard does not recognize report-specific restriction. |
| Document evidence permission | PASS | Current Company allowed while Customer-specific restriction denies Sales Invoice; regrant restores. Cross-company/arbitrary DocType/invalid snapshot token denied generically. |
| Report/derived evidence replay | PARTIAL | Existing cutoff/filters/checksum and restatement hash verified; no durable authorized REPORT_SNAPSHOT/DERIVED_METRIC replay by ID. Chat must choose dynamic hash-checked replay or durable snapshot design. |
| Cache revoke/regrant | BLOCKED | Populated cache, report-specific revoke, same request returns same cached financial payload; regrant works. |
| Currency/Finance Book | PASS (verified scope) | Live VND-company USD request and nonempty AI002 Finance Book return VALIDATION_ERROR. AI003 must explicitly reject unsupported book/FX scope. |
| Model failure design/reuse | PASS (pre-build) | Timeout/unavailable/malformed/grounding failure yield explanation UNAVAILABLE, metrics unchanged; no external model calls. Reuse AI001 minimized payload/provider/schema/grounding and AI002 allowlisted tool/next-check pattern. AI003 endpoint-specific tests belong to G4B. |

## Concrete findings returned to Chat first

**PB-SEC-01 — HIGH: report-specific revoke does not stop cache payload.** Repro: create restricted Accounts User with Company A3G permission; populate AI002 cache from real sources; on isolated site set Custom Role for Accounts Receivable to Accounts Manager; Frappe `Report.is_permitted()` becomes false and direct report returns error/no data. `check_ai002_report_permission` still returns normally. Same AI002 request returns `FORECAST_UNAVAILABLE`, **same forecast ID, 10 obligations and opening cash present**. Root cause: `security/access.py:check_report_permission` imports `has_permission` from query_report, but in installed Frappe it is generic DocType/document permission and checks the Report document; it does not enforce the report's `is_permitted`/custom allowed roles. Cache reauthorization reuses this insufficient primitive. Minimal remediation: use correct report-specific authorization for the explicit active user, preserve Company/ref-DocType checks and generic FORBIDDEN, evict denied cache. Regression must exercise real Frappe Custom Role restriction with Company/Account permission retained, denial inside TTL and regrant. Do not fix by broadly invalidating caches without correct authorization.

**PB-DATA-01 — AR overdue input becomes AVAILABLE with missing due-date information.** Remove due_date/overdue/overdue_amount from the first actual positive AR row. AI001 still reports `overdue_ar_ratio=AVAILABLE -0,0177`: the positive overdue amount disappears while a credit contributes negative overdue. Expected: typed unavailable/inconclusive for the affected overdue metric until due/overdue information is proven. Minimal remediation: validate the authoritative overdue basis; retain total AR if valid but never interpret missing date as zero overdue. Include malformed dates and credit-scope invariants in regression; do not assume a credit's due date fixes a missing positive invoice date.

**PB-DATA-02 — exact duplicate not detected.** Append an exact copy of an actual AR row: total becomes **640.000 instead of 565.000**, still AVAILABLE. AP adapter similarly produces repeated Purchase Invoice source_ref (8 positive obligations instead of 7). Expected: reject inconsistency or apply an explicitly verified source identity rule before aggregation. Minimal remediation must distinguish true duplicate from legitimate payment-term/account splits; do not deduplicate by voucher alone. Add exact-copy/conflicting-copy and valid split regressions.

Contract changes also needed: AP null-date completeness policy, unallocated-credit/net residual semantics, observation identity, zero denominator, precision before threshold comparison, equality/materiality gate composition, precedence of SOURCE_INVALID versus POLICY_PENDING, and report/evidence replay policy. These are not all remediation bugs; some belong to the candidate contract/build plan.

## Required final assessment

```text
CANDIDATE CONTRACT: NEEDS_CHANGE
AR SOURCE GOLD: PARTIAL (numeric oracle PASS; source quality/netting policy open)
AP SOURCE GOLD: PARTIAL (numeric/window oracle PASS; completeness/dedup/policy open)
TEMPORAL: PASS (tested POSTING_DATE_CUTOFF/restatement cases)
PERMISSION: PARTIAL (Company/doc PASS; report/cache BLOCKED)
EVIDENCE REPLAY: PARTIAL
CACHE REVOKE/REGRANT: BLOCKED
GOLD MANIFEST: PASS (source/symbolic artifact; no production signal verdict)
G1: PASS (isolated verification runtime only)
G2: PARTIAL
G3: BLOCKED
G4A: BLOCKED (concrete source report/cache security defect)
G4B: NOT_APPLICABLE_YET
CONTRACT FREEZE RECOMMENDATION: NOT_READY
NEXT ACTION: ChatGPT Chat reviews PB findings and contract decisions, approves a focused remediation handoff; Work re-tests after the approved fix. No AI003 implementation yet.
```

Open approvals: AR baseline, warning/high thresholds, materiality/denominator/count floors; AP 7/30 windows, warning/high thresholds/materiality/count floors; severity labels; credit/netting and comparable-snapshot policy. Work supplied evidence and symbolic behavior, not approval.
