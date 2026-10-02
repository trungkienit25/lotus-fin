# AI003 METHOD GOLD — independent Work evidence, 2026-10-02

**Verdict: METHOD_GOLD_VERIFIED — 66 PASS, 0 FAIL, 0 NOT_RUN, 0 execution errors.**

Authority is Contract V2.2's reviewed method/ordering deltas, with V2/V2.1's unchanged rules. Contract remains NOT_FROZEN; all six production policy values remain PENDING_APPROVAL. This is pre-build method acceptance using real ERP transactions and a test-only method/security adapter. No production AI003 engine, endpoint, cache, hook, migration, or policy configuration was implemented.

## Evidence and independence

- [Authoritative manifest](AI003_METHOD_GOLD_MANIFEST.yaml): JSON-formatted YAML 1.2; every required case, inputs, expected/actual values/state, fixture references/hashes, result, scope and evidence kind. No METHOD GOLD case uses N/A to hide execution gaps.
- [Independent oracle](AI003_METHOD_GOLD_ORACLE.py): stdlib only; direct submitted vouchers and posted Payment Ledger Entry attribution. Expected balances never come from report/candidate output. Expected 4dp HALF_UP rounding uses integer Fraction arithmetic. No AI003 engine/provider imports.
- [Replay runner](evidence/method_gold_runner.py): creates labelled fixture objects idempotently, calls public AI001 snapshot and report APIs, and explicitly authorizes parent metadata. Method/state adapter is confined to this document's evidence folder. Expected values are calculated by the separate oracle, not the candidate adapter. It is not a production endpoint.
- [Final execution log](evidence/method_gold_execution_2026-10-02.log), [independent post-run hygiene read](evidence/method_gold_hygiene_2026-10-02.json), [earlier diagnostic attempts](evidence/method_gold_initial_setup_failure_2026-10-02.json). The final manifest supersedes earlier failed setup/assertion attempts.

## Runtime recovery

Root cause: `frappe_docker-db-1`, `frappe_docker-redis-cache-1` and `frappe_docker-redis-queue-1` were stopped. Backend was running on `frappe_docker_frappe_network`. The stopped DB retained the intended alias `db`, but had no active network endpoint/IP, so the configured hostname did not resolve.

Read-only diagnosis used container state/network listing and selected inspect fields: status, network aliases, volume names and destinations. No credentials or full environment were printed. Recovery action:

```text
docker start frappe_docker-db-1 frappe_docker-redis-cache-1 frappe_docker-redis-queue-1
```

All three original containers are running. No recreation, network replacement, site-config edit or volume reset. Preserved `frappe_docker_db-data`, `frappe_docker_sites`, `frappe_docker_logs`, existing Redis cache volume and `frappe_docker_redis-queue-data`. Backend stayed running; no shared frontend command/site mutation was performed. Queue-worker containers were not started by this task.

Runtime used exclusively `ai003-verify.localhost`; DB `select 1` succeeds, `db` resolves, installed apps are frappe/erpnext/lotus_fin, timezone is Asia/Ho_Chi_Minh, site date is 2026-10-02. Revision is `8941cfb075d91a137686bb6b666bf2bb1f7432c5`. Disposable probe processes force current workspace app source through the read-only mount and PYTHONPATH; manifest records app path and public-boundary/source hashes. No source files were changed in the app tree.

Replay invocation:

```text
docker run --rm --network frappe_docker_frappe_network
  --volumes-from frappe_docker-backend-1
  --mount type=bind,source=E:\lotus-fin,target=/review,readonly
  --env PYTHONPATH=/review/lotus_fin
  --workdir /home/frappe/frappe-bench/sites
  --entrypoint /home/frappe/frappe-bench/env/bin/python
  lotus-fin:ai003-local
  /review/docs/features/AI003/evidence/method_gold_runner.py
```

Operational limitation recorded, not concealed: new Company creation through Standard Template raises `ModuleNotFoundError: lotus_fin.lotus_fin` while ERPNext syncs financial-report templates. No production shim or monkeypatch bypass was added. Fixtures use ERPNext's supported Existing Company chart-copy option from the pre-existing synthetic Gold company; native ERPNext skips template resync on that path and creates separate accounts for each new company. The unused Standard Template path remains unresolved and is outside this METHOD GOLD acceptance.

GitNexus query/context was used for public boundaries. Index remains six commits behind; context has unresolved caller boundaries, and new evidence-runner symbols return UNKNOWN/not indexed. These graph results are not a clean production-impact claim. Explicit text checks found runner/oracle references only in the new document-side harness; no app symbols were edited or committed.

## Numeric domain

| Boundary | Verified domain | Evidence |
|---|---|---|
| Company/source currency | VND | Server-resolved Company and report row checks |
| ERP AR/AP report money | Scale2; Q_MONEY=.01 | Actual backend `get_currency_precision() or 2`, normalization source, plus submitted SI/PI with posted/report outstanding .01 |
| AI001 monetary metric | Scale2; Q_MONEY=.01 | Current source quantize(.01, HALF_UP), source hash and public metric/report observations |
| AI001 overdue ratio | Scale4, HALF_UP | Independent 75/275 oracle rounds to .2727; public snapshot emits .2727; source quantize(.0001, HALF_UP) |
| AR method delta | .01 percentage-point quantum | Difference of published scale4 current/baseline ratios multiplied by100 |

Default invoice currency rounding can make posted PLE balances differ from item rate/grand_total. For example the original method fixture posts whole-money balances even with fractional input rates. Oracle therefore follows posted attribution. Two additional explicitly labelled .01 invoices use ERPNext's native `disable_rounded_total=1` to prove the minimum positive normalized source quantum. Existing invoices were not rewritten to obtain a green result.

Earlier failures in two assertions were harness mistakes: a hard-coded gross-based ratio and string equality for `3` versus `3.0`. The oracle and production formula were unchanged; the final checks compare independent posted arithmetic using numeric equality. Replay Payment Entry creation checks posted outstanding, because ERPNext regenerates payment remarks. No duplicate payment was created.

## AR method gold

Public path: authenticated company/report authorization, then `lotus_fin.api.ai_insights.get_financial_snapshot` separately for current and baseline cutoff, explicit Jan1 period_start/cutoff period_end/as_of, VND, comparison=None, include_explanation=False. No internal class, rounded comparison output or reconstructed exact ratio replaces the published typed metric.

Each calendar/numeric case independently records current and baseline total AR, overdue AR, published ratio and delta. Overdue amounts are also reconciled against the authorized public AR report; AI001 does not publish a separate overdue-amount metric. Calendar checks cover same-day, May31→Apr30, Mar31→Feb28, leap Mar31→Feb29, and Jan15→Dec15 across years.

Main current/baseline example: current total275, overdue275, published ratio1; baseline total275, overdue75, published ratio.2727; delta72.73PP. Negative case: current1200/275/.2292 vs baseline275/75/.2727, delta−4.35PP. Zero means zero **published-method** delta; the oracle applies AI001's specified scale4 before PP arithmetic.

Remaining cases prove net credit arithmetic, verified baseline denominator0 vs missing observation, current denominator0 after a real Payment Entry, future-posting exclusion, malformed source before missing policy, and real report permission denial. Baseline source corruption also wins over a valid current source with denominator0: both sources are validated before method prerequisites.

## AP method gold and schedule proof

Public path: `lotus_fin.api.key_reports.extract_key_report_data('accounts_payable', ...)`, terms disabled, company-currency source, Report Date/Due Date ageing, explicit report cutoff. Parent type is fixed to Purchase Invoice. `get_doc` is followed by explicit checked-user read authorization and verified company equality; no child get_all permission bypass or allocation identity invention.

Posted eligible future-positive denominator is9; D0+D30 numerator is3. D31 and long-dated positive vouchers are denominator-only. Past-due vouchers, including the .01 precision voucher, and negative credit are excluded from both/counts. Distinct voucher counts are2 numerator and4 denominator. Duplicate rows preserve amounts/counts; same observation identity with conflicting amount/date fails typed; unproved additional account scope is INCONCLUSIVE; missing positive due date is INCONCLUSIVE and malformed date is SOURCE_ERROR.

Real submitted credit PI has zero child schedules and is processed safely before credit exclusion; positive eligible PIs have one schedule. An additional zero-schedule metadata perturbation on a real positive parent was checked under a savepoint and rolled back, with ledger hash unchanged. It is explicitly labelled and is not asserted to be ordinary ERP-produced positive-PI metadata.

Mandatory real multi-schedule PI is submitted on the separate controlled company with **two Payment Schedule children**. Terms-disabled public report returns one flattened voucher row. Parent preflight reads both authorized children and returns **INCONCLUSIVE / UNSUPPORTED_MULTI_SCHEDULE**, all finding/trigger/severity null. Cross-company and checked-user parent-metadata denials return generic FORBIDDEN with result null.

## Exact fraction and ordering

Controlled transactions give exact N=3, D=9, N/D=1/3; display at4dp HALF_UP is.3333. A labelled **TEST_ONLY_NOT_APPROVED_POLICY** operand T=.33332 gives T×D=2.99988. Exact `N>=T×D` is true, while comparing display .3333>=T is false; independent Fraction arithmetic agrees with the exact comparison. Decimal precision50 is sufficient for these finite test operands, not a general production numeric limit. T appears only in method evidence/harness, never a production policy artifact.

Currency mismatch is rejected before identity, dedupe/conflict and aggregation; contradictory source currency metadata maps separately to SOURCE_ERROR/INCONSISTENT_DATA. Instrumented adapter traces confirm identity/aggregation was not entered, so neither case becomes CONFLICTING_OBSERVATION.

First-failed-stage cases A–F produce FORBIDDEN, VALIDATION_ERROR, FORBIDDEN, SOURCE_ERROR, INCONCLUSIVE, POLICY_PENDING respectively. A/B stop before company lookup, C stops before future-date semantics, source/method defects never reach policy resolution. These are harness-level application-order proofs with real company/report/parent guards and public source providers; they are not an implemented AI003 HTTP endpoint or full G4B pentest.

## Hygiene and retained objects

All writes were restricted to the isolated site. Intentionally retained: five `AI003 MG` companies and their native accounts/warehouses/cost centres, seven submitted Sales Invoices, eight submitted Purchase Invoices, one submitted Payment Entry, one Customer/two Suppliers with dedicated non-group masters, and required fiscal-year coverage/company links. The manifest records durable company/voucher refs and source hashes. These are synthetic method fixtures, not policy calibration data.

Temporary users, their User Permissions and AR Custom Role restrictions were rolled back. Independent post-run query confirms zero temporary users/permissions/AR restrictions; positive-parent schedule deletion was restored to one row; the durable multi-schedule PI still has two children. Protected prior non-MG company voucher/PLE hashes and final MG fixture hashes are unchanged after probes. Checked-user session restores Administrator. No production/shared-site write was issued; no AI004/AI005 logic was modified/reviewed.

## Gates

| Area | Passed | Failed | Not Run |
|---|---:|---:|---:|
| Runtime | 2 | 0 | 0 |
| Numeric/fraction/currency ordering | 6 | 0 | 0 |
| AR | 15 | 0 | 0 |
| AP | 21 | 0 | 0 |
| First-failed-stage | 7 | 0 | 0 |
| Security | 12 | 0 | 0 |
| Hygiene | 3 | 0 | 0 |
| Total | 66 | 0 | 0 |

```yaml
G2 CONTRACT: PASS
G3 METHOD GOLD: PASS
G4A PRE-BUILD RUNTIME/EVAL: PASS
METHOD GOLD BLOCKERS: NONE
POLICY VALUES: PENDING_APPROVAL
CURRENT VERDICT: METHOD_GOLD_VERIFIED
CONTRACT FREEZE: NOT_FROZEN
NEXT OWNER: ChatGPT Chat
```

**METHOD DESIGN + METHOD GOLD CLOSED. NEXT PHASE = POLICY APPROVAL + POLICY GOLD.** Production endpoint/engine/G4B acceptance remains future implementation work and is not inferred from this pre-build result.
