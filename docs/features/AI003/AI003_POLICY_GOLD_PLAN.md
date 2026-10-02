# AI003 POLICY GOLD plan — AI003_DEMO_POLICY_V1, 2026-10-02

**Status: EXECUTED / VERIFIED for DEMO_ONLY.** The Project Owner bound `AI003_DEMO_POLICY_V1` on 2026-10-02: both floors 0, AR WATCH 5.00pp / HIGH 15.00pp, AP WATCH .50 / HIGH .75, `production_calibrated=false`. See [manifest](AI003_POLICY_GOLD_MANIFEST.yaml) and [execution evidence](AI003_POLICY_GOLD_EVIDENCE.md): 17 REQUIRED PASS, 4 V2.2-proved N/A, 0 FAIL/NOT_RUN/errors. **NOT APPROVED FOR PRODUCTION.** METHOD GOLD remains closed at 66 PASS; it was not rerun.

## Binding and oracle

Reuse the [existing manifest structure](AI003_METHOD_GOLD_MANIFEST.yaml), controlled fixture naming/site conventions and [independent oracle](AI003_METHOD_GOLD_ORACLE.py). Do not modify protected METHOD GOLD transactions/hashes. Later implementation verification must consume the existing public AI001 snapshot twice for AR and the authorized public AP report plus checked-user parent metadata for AP. No internal class dependency; no invented allocation identity; >1 schedules remains fail-closed before policy evaluation.

Oracle inputs are posted PLE attribution and authorized invoice metadata, independent of candidate output. Reuse `ar_expected`/`ap_expected` and integer `rounded_fraction`; after validating method prerequisites, add the approved policy comparison in test-only expectation code using **Fraction/integer arithmetic**. Never import an AI003 engine to obtain expected findings. AR expectation applies published 4dp HALF_UP before delta; actual evaluation must use the two typed public metrics. AP expectation applies exact N>=T×D; display only is 4dp HALF_UP.

Before execution bind: owner-approved six finite values/scope; policy version; V2.2 method identity; source/domain identity and hashes with q=.01 VND and AR .01pp. Method boundary/source versions remain AI001 1.0.0 / formula 2026.1 and AI002 1.2.1 / STRICT_BASELINE_V1, where referenced; AI002 forecast values are not AP-policy inputs. Candidate ID is not an approved policy version. No production limit or floor is inferred from witness amounts. Verify generated invoice amounts fit pinned ERP field/normalization limits; absent proof remains NOT_RUN, not N/A.

For independently valid, authorized method inputs, expected deterministic policy outcome is:

- `A_current<F_AR` or `N<F_AP`: status=OK, result.finding=BENIGN, result.triggered=false, result.severity=null, reason_code=BELOW_MATERIALITY_FLOOR.
- Otherwise HIGH first with >=; then WATCH with >=; otherwise BENIGN. Successful evaluation has status=OK. TRIGGERED has result.triggered=true and result.severity=HIGH or WATCH; BENIGN has result.triggered=false and result.severity=null.
- Source/auth/method failures keep their already-verified typed outcomes and precede policy. Pending policy does not permit executing candidate constants as production defaults.

## Exact AR cases

Define `q=.01`, `A_AR=100*ceil(max(F_AR,q)/100)` VND (minimum 100; a money-grid construction, not a floor recommendation). Use baseline 2026-08-26 / current 2026-09-26, previous-month same-day, equal positive net total A_AR at both cutoffs. For delta d below, baseline published ratio .2000; current ratio `.2000+d/100`. All d are .01pp-representable.

Realize a boundary row using at most three submitted SI, posted on/before baseline: amount `.20*A_AR` due before baseline; amount `(d/100)*A_AR` due after baseline and strictly before current; remaining `(.80-d/100)*A_AR` due after current. All amounts are positive and q-representable; overdue balances are exactly .20A at baseline and (.20+d/100)A at current. Posted ledger/report oracle must confirm actual balances, not assume item rate equals PLE. Native invoice rounding must preserve minor units as already demonstrated in METHOD GOLD.

| Case ID / purpose | Exact inputs | Expected policy outcome after binding | Applicability |
|---|---|---|---|
| AR-MAT-POSITIVE-BELOW | `a=ceil(F_AR/q)*q-q`; baseline/current total a>0, published ratios 0→1, delta 100pp | BENIGN / BELOW_MATERIALITY_FLOOR despite delta>HIGH | REQUIRED iff F_AR>q; otherwise positive-below-floor N/A proof |
| AR-MAT-FIRST-ELIGIBLE | `a=max(q,ceil(F_AR/q)*q)`; total a at both cutoffs; ratios 0→1, delta 100pp | TRIGGERED / HIGH | REQUIRED; a=F if F>=q and aligned, otherwise first eligible positive money amount |
| AR-WATCH-BELOW | total A_AR; .2000→.2499; d=4.99pp | BENIGN | REQUIRED; benign below WATCH and nearest lower WATCH boundary |
| AR-WATCH-EXACT | total A_AR; .2000→.2500; d=5.00pp | TRIGGERED / WATCH | REQUIRED; exact WATCH |
| AR-WATCH-ONLY | total A_AR; .2000→.3000; d=10.00pp | TRIGGERED / WATCH | REQUIRED; strictly between thresholds |
| AR-HIGH-BELOW | total A_AR; .2000→.3499; d=14.99pp | TRIGGERED / WATCH | REQUIRED; nearest lower HIGH boundary |
| AR-HIGH-EXACT | total A_AR; .2000→.3500; d=15.00pp | TRIGGERED / HIGH | REQUIRED; exact HIGH |
| AR-HIGH-ABOVE | total A_AR; .2000→.3501; d=15.01pp | TRIGGERED / HIGH | REQUIRED; nearest higher HIGH boundary |

For both materiality rows, one positive SI due after baseline and strictly before current yields ratios 0→1 with a positive denominator at each cutoff; no need to split a into fractional overdue portions. a=0 is never a substitute below-floor AR case: current denominator 0 fails the method before policy. Exact WATCH/HIGH witnesses need no rounding reconstruction: independent published metric expectations equal the published 4dp values exactly.

## Exact AP cases

Define `A_AP=100*ceil(max(F_AP,q)/100)` VND and `D=4*A_AP`. Each threshold row can use two PI with one schedule each, both posted on/before as_of: amount N due D0 (or D30); amount D-N due D31. Both positive; N is D0–D30 and D includes both. Date edges, credits, duplicates and multi-schedule rejection are already METHOD GOLD facts; do not recreate that whole suite for a policy choice.

| Case ID / purpose | Exact inputs | Expected policy outcome after binding | Applicability |
|---|---|---|---|
| AP-MAT-ZERO | N=0,D=A_AP>0; all AP due D31 | BENIGN / BELOW_MATERIALITY_FLOOR if F_AP>0 | REQUIRED iff F_AP>0; at F_AP=0 the **below-floor predicate** is logically unreachable (N cannot be negative) |
| AP-MAT-POSITIVE-BELOW | `a=ceil(F_AP/q)*q-q`; N=D=a>0, share 1 | BENIGN / BELOW_MATERIALITY_FLOOR despite share>HIGH | REQUIRED iff F_AP>q; otherwise positive-below-floor N/A proof |
| AP-MAT-FIRST-ELIGIBLE | `a=max(q,ceil(F_AP/q)*q)`; N=D=a>0, share 1 | TRIGGERED / HIGH | REQUIRED; exact floor when aligned/positive, otherwise first eligible amount |
| AP-WATCH-BELOW | N=2A_AP-q,D=4A_AP; exact share `.50-q/(4A_AP)` | BENIGN | REQUIRED; benign below WATCH and nearest lower N at this D |
| AP-WATCH-EXACT | N=2A_AP,D=4A_AP; share .50 | TRIGGERED / WATCH | REQUIRED; exact WATCH |
| AP-WATCH-ONLY | N=2.5A_AP,D=4A_AP; share .625 | TRIGGERED / WATCH | REQUIRED; strict WATCH band |
| AP-HIGH-BELOW | N=3A_AP-q,D=4A_AP; exact share `.75-q/(4A_AP)` | TRIGGERED / WATCH | REQUIRED; nearest lower N at this D |
| AP-HIGH-EXACT | N=3A_AP,D=4A_AP; share .75 | TRIGGERED / HIGH | REQUIRED; exact HIGH |
| AP-HIGH-ABOVE | N=3A_AP+q,D=4A_AP; exact share `.75+q/(4A_AP)` | TRIGGERED / HIGH | REQUIRED; above HIGH with N<=D |

Every threshold row has N>=F_AP, D>0 and 0<=N<=D. These are exact numerator boundaries **for the fixed witness D**, not a universal minimum AP share quantum: D may vary, so there is no .0001 evaluation grid. With A_AP>=100, both below-boundary shares round to the respective threshold at 4dp while the exact comparison remains below it. Assert this explicitly to detect accidental display-before-comparison. The zero row uses a single denominator-only PI, and N=D rows use one window PI; never create zero-amount PIs.

## Reachability and N/A proof obligations

The table is a design registry of **17 planned predicates**, not 17 executed/passed cases. Threshold rows have mathematical witnesses for this conditional candidate. Materiality applicability remains unbound until floors/version are selected; do not put an invented applicability enum in a runtime manifest. After binding, record exactly REQUIRED with NOT_RUN/PASS/FAIL, or NOT_APPLICABLE with execution_status=NOT_APPLICABLE.

Every N/A entry must include actual domain_version, method_version, **approved policy_version**, exact predicate, proof_code and explanation. Pending policy/unknown numeric limits/missing fixture/runtime or implementation are never N/A.

| Conditional predicate | Approved V2.2 proof code / proof |
|---|---|
| Positive amount below F, if 0<=F<=q | NO_POSITIVE_REPRESENTABLE_VALUE_BELOW_FLOOR: all positive normalized a=kq, integer k>=1; therefore a>=q>=F |
| AP any nonnegative N below F, if F=0 | LOGICALLY_UNREACHABLE_BY_METHOD: N>=0, so N<0 is impossible. This does not excuse the ordinary benign N=0 evaluation |
| Exact AR threshold, if owner later chooses T off .01pp grid | EXACT_BOUNDARY_NOT_REPRESENTABLE for equality only; nearest valid below/above grid witnesses remain required |
| WATCH-only, if owner later chooses H=W | NO_SEPARATE_WATCH_BAND: HIGH is evaluated first; no x can satisfy x>=W and x<H |

Candidate 5/15 and .50/.75 have no unreachable exact threshold, separate-WATCH, benign-below-WATCH or above-HIGH predicates. If owner changes any threshold, recompute candidate-specific applicability rather than reuse the table blindly. For AR, `ceil(W/.01)*.01<H` plus represented source/materiality prerequisites is necessary for a WATCH witness. AP requires integer-money witnesses N=nq,D=dq with D>0,0<=N<=D,N>=F,W D<=N<H D; a failed fixture search is not proof. Owner selections H=1 or W=0 can make some AP above-HIGH/below-WATCH predicates impossible; use LOGICALLY_UNREACHABLE_BY_METHOD with the exact bound proof, not missing-fixture explanations.

## Minimal additional data and execution handoff

1. **Owner data, not fixture calibration:** both floors, company/segment scope, evidence rationale and approved policy version/record. This is the only missing numeric binding for candidate A; four threshold choices also need owner acceptance.
2. **Controlled transaction data:** paired AR cutoffs with the three amounts/due dates above (one SI suffices for either materiality case); AP window/future amounts with at most two single-schedule PI (one for N=0 or N=D). Existing native posting/rounding, supported COA-copy fixture setup and independent oracle are sufficient. Isolate each state's source totals using the existing case fixture conventions; reuse a cohort only if its ledger, dates and scope exactly meet the vector. Do not mutate the 66 accepted gold cases. No extra historical months, multi-schedule or allocation dataset is needed for these policy boundaries.
3. **No extra method-error fixtures:** reuse existing hashes/refs for missing baseline, zero-denominator failures, credits, duplicates/conflicts, dates, multi-schedules and security. No new AI003 environment, production engine, endpoint or cache is needed to prepare the vectors. Actual policy-engine acceptance waits for separately authorized implementation.

Record expected/actual typed fields, owner policy/domain/method versions, source/fixture hashes, boundary operands and applicability proofs in the existing controlled manifest conventions. Any REQUIRED NOT_RUN/FAIL blocks POLICY GOLD PASS; N/A stays visible and is excluded from both pass count and denominator.

## Preparation validation record — not a gold verdict

On 2026-10-02, host Python 3.13.7 checked these constructions with stdlib Fraction and the unchanged independent oracle's `rounded_fraction`; no DB/source provider/AI003 engine was called. All listed AR/AP threshold operands, posted-amount constructions, first eligible amounts, conditional positive-below-floor witnesses and AP zero predicates agreed with the inequalities above. The AP display-before-comparison traps were confirmed. Test-only floor operands 0, .005, .01, .015, .02, 99.99, 100, 100.001, 1234567.89 exercise zero, sub-quantum, aligned/nonaligned and scaling conditions; **none is a floor recommendation or an alternative candidate policy**. These spot checks support the construction; final source limits and actual policy binding remain outstanding.

An exact example at **test-only A=100,D=400**: N=199.99 gives share 19999/40000=.499975 and display .5000, but is below WATCH; N=299.99 gives share 29999/40000=.749975 and display .7500, but is below HIGH. N=200 and N=300 are exact threshold witnesses. This is mathematical evidence of comparator behavior, not business calibration or executed public-endpoint acceptance.

The preparation record above remains the derivation history. Its controlled ERP boundary vectors were subsequently executed for `AI003_DEMO_POLICY_V1`; all temporary transactions and companies were rolled back, while METHOD GOLD/source fingerprints remained unchanged. **POLICY GOLD: PASS for DEMO_ONLY.** Production policy remains pending. Next owner: ChatGPT Chat.
