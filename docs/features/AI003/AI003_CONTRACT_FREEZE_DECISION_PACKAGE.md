# AI003 CONTRACT FREEZE DECISION PACKAGE (2026-09-30)

Prepared by: Independent Verification Lead (IVL), revision `c6f4cd1`, branch `feature/risk-signal-agent`, isolated runtime `ai003-verify.localhost` (Frappe 16.34.0 / ERPNext 16.35.0, timezone `Asia/Ho_Chi_Minh`). For **ChatGPT Chat** to decide the contract freeze. No AI003 implementation exists; no business policy is approved here; no gate is raised without evidence.

## Evidence index

| # | Deliverable | File |
| --- | --- | --- |
| 1 | SSOT authoritative append | [`AI003_MASTER_SSOT.md`](AI003_MASTER_SSOT.md) §34 (plus Work §32–33) |
| 2 | Contract semantics review / feasibility assessment (v0.2) | [`AI003_IVL_CONTRACT_SEMANTICS_REVIEW_v0.2.md`](AI003_IVL_CONTRACT_SEMANTICS_REVIEW_v0.2.md) + [`AI003_CONTRACT_FEASIBILITY_v0.2.md`](AI003_CONTRACT_FEASIBILITY_v0.2.md) |
| 3 | Gold manifest + independent oracle evidence | [`AI003_GOLD_MANIFEST.yaml`](AI003_GOLD_MANIFEST.yaml), [`evidence/AI003_IVL_GOLD_CLOSURE_2026-09-30.md`](evidence/AI003_IVL_GOLD_CLOSURE_2026-09-30.md), [`evidence/prebuild_oracle.py`](evidence/prebuild_oracle.py) |
| 4 | Focused remediation verification | [`AI003_IVL_REMEDIATION_VERIFICATION_2026-09-30.md`](AI003_IVL_REMEDIATION_VERIFICATION_2026-09-30.md) |
| 5 | Business Policy Decision Sheet (8 rows, all PENDING) | [`AI003_BUSINESS_POLICY_DECISION_SHEET.md`](AI003_BUSINESS_POLICY_DECISION_SHEET.md) |
| 6 | Replay-design feasibility harness | [`evidence/ivl_phase_c_replay_harness.py`](evidence/ivl_phase_c_replay_harness.py) + probe scripts in `docker/ai003-local/` |

## Decision summary

```text
FOUNDATION REMEDIATION
PASS   (WR-01/WR-02 VERIFIED FIXED by Work §32; Buckets A–D unit+live verified;
        IVL re-confirmed 197/197 suites, runtime sync, unchanged numeric gold)

AR SOURCE + GOLD
PARTIAL   (numeric oracle independently verified at both cutoffs; netting,
          missing-due-date and duplicate-identity policy open; PB-DATA-01/02 open)

AP SOURCE + GOLD
PARTIAL   (numeric/inclusive-window oracle verified incl. +1/+7/+8/+30/+31,
          overdue/due-today context, allocated/unallocated credits;
          null-due-date coverage and dedup identity open)

SECURITY + CACHE
BLOCKED   (PB-SEC-01 HIGH reproduced independently by IVL: report-specific
          Custom Role revoke denied by Frappe yet guard passes and AI002 cache
          returns the identical financial payload; document/company isolation PASS)

TEMPORAL
PASS   (posting-date cutoff + restatement semantics verified; future posting
        inert; backdate/cancel/amend restates with new fingerprint;
        as_known_at explicitly unsupported — consistent with contract)

EVIDENCE REPLAY DESIGN
PASS   (DYNAMIC_AUTHORIZED_REPLAY + SAVED_HASH_COMPARISON proven feasible in an
        isolated harness: MATCH / RESTATED / UNAVAILABLE / FORBIDDEN all correct;
        snapshot ID never an auth token; no production endpoint built; durable
        REPORT_SNAPSHOT storage remains an alternative Chat may choose)

TECHNICAL CONTRACT
NOT_READY   (v0.2 verdict NEEDS_CHANGE per Work §33; seven semantic gaps/conflicts
             recorded; mandate references v0.3 which does not exist — Chat must issue it)

BUSINESS POLICY
PENDING   (8-row decision sheet awaiting Finance/Product; no production threshold
           inferred from fixtures; DEMO_ONLY must stay a separate scope)

G1: PASS (isolated verification runtime only — image/services/migration/timezone
    synced to c6f4cd1; no production-site deployment claim)
G2: PARTIAL (field mapping feasible; netting/identity/precision/precedence/replay
    policy and financial approvals open)
G3: BLOCKED (PB-DATA-01 and PB-DATA-02 reproduced; policy floors unapproved;
    numeric source gold exists)
G4A: BLOCKED (PB-SEC-01 independently reproduced; absence of an AI003 endpoint is
     NOT the blocker)
G4B: NOT_APPLICABLE_YET

CONTRACT FREEZE RECOMMENDATION:
NOT_READY

EXACT REMAINING BLOCKERS:
- PB-SEC-01 (HIGH): report-specific authorization primitive replaces generic
  query_report.has_permission in check_report_permission + cache-hit
  reauthorization; deny → FORBIDDEN, evict cache; Company/DocType checks and
  generic FORBIDDEN preserved
  → owner: Antigravity/Zcode (after Chat approves scope); required evidence:
    real Frappe Custom Role revoke/regrant regression inside TTL + Work re-test
- PB-DATA-01: AR overdue basis validated; missing/malformed due-date → typed
  inconclusive/SOURCE_INVALID, never zero-overdue interpretation
  → owner: Antigravity/Zcode (after Chat approval); required evidence: regression
    incl. malformed dates and credit-scope invariants + Work re-test
- PB-DATA-02: source-identity rule distinguishing true duplicates from legitimate
  installment/account splits; conflicting-copy rejection
  → owner: Antigravity/Zcode (after Chat approval); required evidence: exact-copy,
    conflicting-copy and valid-split regressions + Work re-test
- Technical contract v0.3: resolve the seven recorded conflicts (net vs
  positive-only, unallocated credits, observation identity, missing due date,
  SOURCE_INVALID > POLICY_PENDING precedence, comparator/equality + ordering,
  no-rounding-before-threshold; replay design choice)
  → owner: ChatGPT Chat; required evidence: issued v0.3 document
- Business policy: 8 decisions in the decision sheet (AR baseline, both signal
  threshold sets, floors, severity labels)
  → owner: Finance / Product; required evidence: sheet rows moved to APPROVED
- Minor: purge 4 cancelled transient invoices + temp Customer from the isolated
  gold fixture (zero numeric impact, gold re-verified after cleanup)
  → owner: Work, next fixture pass
```

## Gate detail

| Gate | Acceptance criteria | Verified evidence | Missing evidence | Remaining blocker | Owner |
| --- | --- | --- | --- | --- | --- |
| G1 Runtime | Aligned isolated runtime: image/source/migration/timezone consistent; suites green | Image `220e4f5d…`, source SHA256 = `c6f4cd1`, scope column + timezone verified, 197/197 (7 suites) + 233/233 discovery, AI001 eval 15/15 | Production-like deployment, CI | Deployment outside isolated runtime | Work/DevOps |
| G2 Contract | Frozen candidate with resolvable semantics for both P0 signals | v0.2 evaluated (NEEDS_CHANGE); feasibility table complete; 7 conflicts recorded; replay design proven | v0.3 with decisions; replay-storage policy | Contract gaps | Chat |
| G3 Data & Method | Source-quality defects fixed; independent gold closed; policy approved | Numeric gold verified independently (oracle, no production imports); boundaries/empty/restatement closed | PB-DATA-01/02 fixes; approved floors/thresholds | 2 reproduced defects + PENDING_APPROVAL policy | Zcode + Finance |
| G4A Pre-build security/evaluation | Report/document/company authorization + cache revocation proven with real Frappe primitives | Document/company denial, cross-company, forged token: PASS; Custom Role revoke/regrant on documents: PASS; 197 unit + live probes | Real-role report revoke honored by guard and cache | PB-SEC-01 (reproduced by Work and IVL) | Zcode (approved fix) → Work |
| G4B Implementation E2E | AI003 endpoint exists with signal-level security/eval tests | NOT_APPLICABLE_YET — endpoint absence is not used against G4A | AI003 implementation after freeze | Frozen contract first | Antigravity/Zcode (later) |

## Explicitly out of scope of this package

No AI003 engine, threshold values, severity scale or signal verdict was created; no `frontend`-site mutation; no fixture numbers changed to force passes (gold re-verified unchanged after probe cleanup); SSOT gates were assessed, not raised. Historical evidence (§4–33, superseded initial oracle results) is preserved untouched.
