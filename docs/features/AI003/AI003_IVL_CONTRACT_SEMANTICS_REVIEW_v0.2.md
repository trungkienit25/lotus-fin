# AI003 IVL — Candidate Contract semantics review (v0.2, 2026-09-30)

Independent Verification Lead review of [`AI003_CANDIDATE_CONTRACT_v0.2.md`](AI003_CANDIDATE_CONTRACT_v0.2.md) against the verification mandate. The contract is **not modified** here; each gap below becomes a decision row in [`AI003_BUSINESS_POLICY_DECISION_SHEET.md`](AI003_BUSINESS_POLICY_DECISION_SHEET.md) or a Chat contract decision.

**Version conflict (recorded, not resolved):** the verification mandate references "Candidate Contract v0.3", but the latest existing artifact is **v0.2** (`contract_version: 0.2.0-candidate`, status `READY_FOR_WORK_PREBUILD_EVALUATION`). No v0.3 document exists in the repository. This review therefore audits v0.2 as the latest authority; **Chat must confirm** whether v0.3 was intended to exist, is pending, or the reference is stale. Nothing here invents v0.3 content.

## 1. AR semantics

| Topic | v0.2 state | Verification evidence | Assessment |
| --- | --- | --- | --- |
| Net vs positive-only residual | §3.1 ambiguous: "sau khi xét payment allocations, credit notes" — no explicit net/positive-only rule | Oracle at 2026-09-26: net 565,000 (incl. −10,000 unallocated credit) vs positive-only 575,000; positive-only overdue 75,000 vs net overdue 65,000 | **GAP → Chat decision** (Sheet 1). Both bases retained in the independent oracle until Finance approves |
| Unallocated-credit separation | Not specified; §4.3 anti-double-count rule is AP-worded | Unallocated credit −10,000 verified as separate context; netting it silently changes both numerator and denominator | **GAP → Chat decision** (Sheet 2) |
| Verified overdue basis | `due_date < as_of`; due-exact not overdue; ERPNext overdue-amount column must be proven equivalent | Live: due-before 75,000 overdue; due-exact 200,000 not; report ageing columns are posting-date based and unusable as authority | **DEFINED ✓, verified**; keep as contract text |
| Missing/malformed due date | **Not specified** | PB-DATA-01 reproduced: missing due-date info → ratio −0.0177 still AVAILABLE (positive overdue lost, credit overdue counted) | **GAP → typed inconclusive/SOURCE_INVALID rule needed** (Sheet 3 note + remediation blocker) |
| Baseline comparability | §3.3 requires same company/scope/currency/definition/cutoff/comparability; baseline date policy PENDING | 09-20/09-26 is a verification pair only; current/baseline net-ratio delta 11.5044 pp is not a policy | **DEFINED ✓**; policy value pending (Sheet 3) |
| Zero denominator | Ratio undefined, never benign | Empty company: denominator zero, ratio undefined | **DEFINED ✓** |
| Observation identity | **Not specified** | PB-DATA-02: exact duplicate row → 640,000/8 obligations with repeated source_ref | **GAP → Chat decision** (Sheet 7 note); remediation must distinguish true duplicates from legitimate installment/splits |

## 2. AP semantics

| Topic | v0.2 state | Verification evidence | Assessment |
| --- | --- | --- | --- |
| 7/30 window | Proposed +1..+7 short, +1..+30 reference, inclusive; `window_policy_status: PROPOSED` | D1/D7 in; D8/D30 reference; D31 out — inclusive boundaries verified live | **DEFINED ✓ (proposed status); adoption pending** (Sheet 5) |
| Inclusive boundaries | Explicit | Verified | ✓ |
| Null due-date coverage | Listed in §4.3 checks, **no policy** | AP adapter permits nullable due date (Work finding) | **GAP → coverage rule needed** |
| Partial payments | §4.3 check required | Payment Ledger attribution: D1 100,000 − 20,000 = 80,000→75,000 with allocated credit | **VERIFIED** |
| Allocated/unallocated credits | "Không trừ credit note hai lần nếu authoritative residual đã phản ánh" | Allocated credit counted once via residual; `return_against` alone disproven as allocation proof; unallocated −10,000 separate | **VERIFIED**; unallocated treatment still a policy decision |
| Duplicate/split identity | §4.3 lists duplicate check, **no identity rule** | PB-DATA-02 AP leg reproduced | **GAP → Chat decision** |
| Zero denominator | `NOT_APPLICABLE`/unqualifiable, never safe claim | Empty company verified | **DEFINED ✓** |
| Overdue / due-today separation | Explicit separate context | 600,000 / 700,000 verified as context, excluded from future windows | **DEFINED ✓** |
| Due date ≠ settlement date | Explicit ("Không coi ngày đến hạn hợp đồng là ngày thanh toán thực tế") | AI002 `NO_CONFIRMED_SETTLEMENT_EVENTS` fail-closed consistent | **DEFINED ✓** |

## 3. Common rules

| Topic | v0.2 state | Verification evidence | Assessment |
| --- | --- | --- | --- |
| SOURCE_INVALID vs POLICY_PENDING precedence | Both defined separately; **precedence not specified** | Feasibility table flags "define source-invalid precedence" | **GAP → Chat contract decision** (recommend: SOURCE_INVALID wins — a policy must never evaluate an invalid source) |
| Equality / comparator semantics | Not specified; `>=` is TEST_ONLY_POLICY in manifest | Symbolic boundaries only | **GAP → contract decision** |
| Warning/high ordering | Not specified | — | **GAP → contract decision** (recommend: high ⟹ warning not re-fired, or explicit precedence) |
| Decimal precision / rounding before threshold | **Not stated in v0.2** | Oracle uses unrounded Decimals; manifest mandates "no rounding before threshold comparison" at item level | **GAP → write into v0.3** (mandate requires it; currently only in manifest notes) |
| Company/currency/timezone/Finance Book | §2: server-verified company, VND P0, no FX relabel, Finance Book rejected, no `as_known_at` | Live VND/USD VALIDATION_ERROR; Finance Book rejected; timezone Asia/Ho_Chi_Minh verified | **DEFINED ✓, verified** |
| Snapshot & method-version provenance | §5 carries contract/rule/method versions + `source_snapshot_refs` | AI001/AI002 envelopes versioned; checksums stable; **no durable replay by ID** | **PARTIAL → design decision**; Phase C proves the dynamic option (see §4) |

## 4. Evidence replay design — feasibility verdict

Phase C harness (`evidence/ivl_phase_c_replay_harness.py`) proves **DYNAMIC_AUTHORIZED_REPLAY + SAVED_HASH_COMPARISON** is feasible with existing primitives, using the *authoritative* report permission primitive (the fix direction for PB-SEC-01):

| Case | State |
| --- | --- |
| Authorized replay, identical source | MATCH |
| Repeat read, hash stability | MATCH |
| Report Custom-Role revoked before replay | FORBIDDEN (no payload) |
| Cross-company observation | FORBIDDEN (generic) |
| Source unavailable (typed failure) | UNAVAILABLE |
| Backdated restatement (transient, rolled back) | RESTATED (new fingerprint); cancel restores MATCH |

All four required states reproduced. Snapshot IDs/checksums are treated as identity only — forged evidence refs are denied without resource authorization (C8). **No production replay endpoint was built.** Remaining design decision for Chat: dynamic hash-checked replay (proven above) vs durable REPORT_SNAPSHOT/DERIVED_METRIC storage (not built; feasibility table marks it NOT_SUPPORTED today).

## 5. Conflicts register (for Chat — no self-edits made)

1. Mandate references contract **v0.3**; only **v0.2** exists.
2. v0.2 §3.1 net-vs-positive-only ambiguity vs oracle's dual bases.
3. v0.2 missing due-date policy vs PB-DATA-01 required typed inconclusive behavior.
4. v0.2 missing observation-identity rule vs PB-DATA-02.
5. v0.2 missing SOURCE_INVALID/POLICY_PENDING precedence.
6. v0.2 missing precision/no-rounding-before-threshold clause (present only in manifest notes).
7. Report/cache reauthorization primitive (`query_report.has_permission`) is provably insufficient (PB-SEC-01) while v0.2 §8/§9 assume correct reauthorization — contract must reference the authoritative primitive after remediation.
