# AI003 POLICY GOLD evidence — DEMO_ONLY, 2026-10-02

**Verdict: POLICY_GOLD_VERIFIED — 17 REQUIRED PASS, 0 FAIL, 0 NOT_RUN; 4 NOT_APPLICABLE with V2.2 proofs.** This evidence binds only owner-approved `AI003_DEMO_POLICY_V1`: AR floor 0 VND, WATCH 5.00pp, HIGH 15.00pp; AP floor 0 VND, WATCH .50, HIGH .75. Scope is `DEMO_ONLY`, approver role Project Owner, approval date 2026-10-02, `production_calibrated=false`.

> **NOT APPROVED FOR PRODUCTION.** There is no automatic promotion path from DEMO_ONLY. Controlled values prove deterministic boundaries, not business calibration.

## Execution and independence

POLICY GOLD ran on isolated site `ai003-verify.localhost` at revision `8941cfb075d91a137686bb6b666bf2bb1f7432c5`. The three stopped existing DB/Redis containers were started without recreation, network/volume replacement or configuration edits. No shared frontend command ran.

The run reused the unchanged stdlib-only [METHOD GOLD oracle](AI003_METHOD_GOLD_ORACLE.py), public AI001 snapshot path, authorized AP report boundary and checked-user parent metadata convention. Expected posted-ledger arithmetic did not import a future AI003 engine. Policy evaluation lived only in a temporary execution harness; no endpoint, engine, UI, agent, cache, hook, migration or production configuration was created. The temporary harness was removed after evidence capture.

Two temporary controlled companies and all boundary invoices existed only inside the execution transaction. Every case rolled back to a savepoint; the full transaction then rolled back. A separate read-only hygiene query confirmed both temporary companies absent, zero temporary SI/PI, and all five METHOD GOLD fixture hashes unchanged.

The first completed attempt compared decimal strings lexically and marked equivalent values such as `10000`/`10000.0` as unequal. The harness was corrected to serialize money at 2dp, ratios at 4dp and PP at 2dp; method, policy constants, fixtures, expected financial values and oracle were unchanged. The final authoritative run is the manifest result: 17 PASS, 0 FAIL/NOT_RUN/error.

## Policy binding and reachability

The exact owner record is preserved in [the manifest](AI003_POLICY_GOLD_MANIFEST.yaml). V2.2 invariants pass: `15>=5>=0`, `1>=.75>=.50>=0`, both floors are 0. Exact WATCH/HIGH and separate WATCH bands are reachable for both signals.

Four materiality predicates are N/A:

- Positive AR/AP below floor 0: `NO_POSITIVE_REPRESENTABLE_VALUE_BELOW_FLOOR`; q=.01 and every positive normalized amount is `kq>=.01>0`.
- Exact AR total at floor 0: `LOGICALLY_UNREACHABLE_BY_METHOD`; current net AR 0 stops at the positive-denominator prerequisite before policy.
- Any AP numerator below floor 0: `LOGICALLY_UNREACHABLE_BY_METHOD`; valid AP requires `0<=N<=D`.

Each manifest N/A includes domain, method and policy versions, predicate, allowed proof code and proof. No missing fixture, runtime condition or implementation gap is classified N/A. AR's first eligible positive amount .01 passed; AP's exact floor `N=0,D=400` and first positive `N=D=.01` passed.

## Boundary results

| Signal | Boundary | Result |
|---|---|---|
| AR | 4.99pp | BENIGN |
| AR | 5.00pp | WATCH |
| AR | 10.00pp | WATCH-only |
| AR | 14.99pp | WATCH |
| AR | 15.00pp | HIGH |
| AR | 15.01pp | HIGH |
| AP | 199.99/400 = 19999/40000 | BENIGN; display 0.5000 |
| AP | 200/400 = .50 | WATCH |
| AP | 250/400 = .625 | WATCH-only |
| AP | 299.99/400 = 29999/40000 | WATCH; display 0.7500 |
| AP | 300/400 = .75 | HIGH |
| AP | 300.01/400 = 30001/40000 | HIGH |

AR used two public typed snapshots and published 4dp ratios; delta remained on the .01pp grid. Equality used `>=`, and HIGH ran before WATCH. AP used exact `N>=T*D`; the 4dp display was never an operand. Both display traps passed: values displayed at .5000/.7500 remained below the exact thresholds and produced BENIGN/WATCH respectively.

## Closed evidence reuse

[METHOD GOLD manifest](AI003_METHOD_GOLD_MANIFEST.yaml) remained 66 PASS / 0 FAIL / 0 NOT_RUN / 0 errors. Its manifest, oracle, runner and four consumed source hashes matched before fixture creation. Post-run hashes for all five METHOD GOLD fixture companies remained identical.

The binding adds only A9 policy values and does not alter the closed ordering or payload rules. Existing PASS evidence is reused for unauthenticated/forbidden suppression, source failure before policy, history/method inconclusive before policy, two-schedule fail-closed, and currency-before-identity. LLM non-authority remains a V2.2/G4A design invariant; this deterministic policy harness imported no model or explanation path.

```yaml
POLICY BINDING: PASS — AI003_DEMO_POLICY_V1 / DEMO_ONLY / Project Owner / 2026-10-02
AR POLICY GOLD: PASS — 7 REQUIRED
AP POLICY GOLD: PASS — 10 REQUIRED
N/A APPLICABILITY: PASS — 4 proved
EVIDENCE REUSE: PASS — METHOD GOLD 66/66 and fixture/source fingerprints unchanged
POLICY SCOPE SAFETY: PASS — production_calibrated=false; NOT APPROVED FOR PRODUCTION
POLICY GOLD: PASS
G1 RUNTIME: PASS
G2 CONTRACT: PASS
G3 DATA/METHOD/POLICY: PASS
G4A PRE-BUILD: PASS
REMAINING PRE-FREEZE BLOCKERS: NONE_FOR_DEMO_SCOPE
CURRENT VERDICT: POLICY_GOLD_VERIFIED
CONTRACT FREEZE: NOT_FROZEN
NEXT OWNER: ChatGPT Chat
```

PRE-BUILD DEMO-SCOPE G1/G2/G3/G4A COMPLETE.  
READY_FOR_CHAT_FREEZE_DECISION.
