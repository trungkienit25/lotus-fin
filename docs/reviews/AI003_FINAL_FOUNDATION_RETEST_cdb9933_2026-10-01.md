# Final Foundation Re-test — 2026-10-01

Independent verifier scope: latest PB-SEC-01 / PB-DATA-01 / PB-DATA-02 remediation only. AI004 and AI005 business logic excluded. No production edits, commits, pushes, merges, fixture rebuilds or shared frontend changes.

## Target and evidence

- HEAD: `cdb99334c7e9a13986afa24facfe88d8f95ad296`.
- Merge parents: AI001 `99b4388c570a120f369a59579520129d19af9c50`, AI002 `6c07e008622ac349dc972160862d76bc491ba84c`.
- Compared against previously reviewed `d8dd7c8`: 9 files, +1028/-55. Six production files and three test files. No uncommitted tracked production changes in `lotus_fin/lotus_fin`. Existing documentation, fixture-script and other working-tree changes were left untouched; `lotus_fin/.zcode/` and `.zcodeignore` are untracked outside the app package.
- Live Docker probe used current workspace code through a read-only mount and `PYTHONPATH=/review/lotus_fin`, isolated site `ai003-verify.localhost`. Permission mutations were rolled back. Probe user/Custom Role absent after rollback; source fingerprint unchanged.
- Unchanged harness SHA256: `1366688d890498524297915ff8938cfc589118c1ea55d1dbbf5d3ad06afdc4d0`.
- GitNexus index points at `86208f4`, hence stale. Following the requested fallback, inspected direct changed callers/tests; no stale LOW/UNKNOWN used as evidence and no full graph reindex.

| Area | Result | Evidence / remaining issue |
|---|---|---|
| Revision/diff | PASS | Verified target, parents, narrow 9-file remediation diff; app tree clean. |
| PB-SEC-01 | PASS | Real Report.is_permitted denial, checked-user guard under Administrator session, cached and fresh FORBIDDEN with empty payload, regrant restored. Cache-eviction branch inspected; focused revoke/TTL tests pass. |
| PB-DATA-01 | FAIL | Original missing/malformed/explicit/date cases pass. Additional valid datetime due_date causes unhandled TypeError in parser and public snapshot. See finding below. |
| PB-DATA-02 | PASS | Exact duplicates deduped, conflicting financial content rejected with typed errors, AR/AP totals and F002 obligations checked. Focused tests preserve payment-term/account splits numerically. |
| Live foundation probe | PASS | Unchanged 51-case harness: previous 12 failures → current 0; 51 PASS, 0 errors. Does not cover datetime due_date. |
| R1–R5 regression | PASS | 120 focused tests pass in one process; independent contracts/evidence/lifecycle probe and controlled broken-sibling import containment pass. Canonical alias code unchanged; import-order tests pass. |
| Public contracts | PASS | AI001 1.0.0 / 2026.1, AI002 1.2.1 / STRICT_BASELINE_V1 unchanged. No AI003 contract freeze or expansion of approved public boundaries. |
| Remaining runtime limitation | NOT_VERIFIED | Real ERPNext schedule/allocation identity remains unproven by these fixtures; simulated split preservation is not live allocation proof. |

## Smallest remediation finding for Zcode

**PB-DATA-01-DATETIME — valid due_date escapes the public snapshot as TypeError.**

Location: `lotus_fin/lotus_fin/core/domain/calculators/ar_extractor.py:90` and comparison at line 100.

`datetime` inherits from `date`. The expression `due_date_str if isinstance(due_date_str, date) else due_date_str.date()` retains a datetime object. Comparing it with the date cutoff raises `TypeError: '<' not supported between instances of 'datetime.datetime' and 'datetime.date'`. The new helper explicitly accepts datetime input, but does not normalize it. `MetricAssembler` catches `FinancialSourceDataError`, so this TypeError also escapes `build_financial_snapshot` rather than producing its typed contract response.

Minimal input:

```python
parse_ar_data(
    [{"voucher_no": "SI-RETEST", "outstanding": 100,
      "due_date": datetime(2026, 9, 20)}],
    as_of_date=date(2026, 9, 26),
)
```

Expected `(100.00, 100.00, 1.0000, [])`; actual unhandled TypeError. The same input with string `2026-09-20` or `date(2026, 9, 20)` succeeds, including the public snapshot (`OK`, overdue_ar_ratio AVAILABLE = 1.0).

Small remediation: normalize datetime to `.date()` before the date branch; add a regression for typed date/datetime through parser and public snapshot. Retain existing missing/malformed-basis behavior. No production change made by verifier.

This is reproduced hermetically on host Python 3.13 and Docker image Python 3.14; it is not claimed as an observed datetime row in the current live ERPNext fixture. The live 51-case pass remains valid for its covered inputs. The separate public-boundary exception prevents an unconditional foundation approval.

## Evidence files

All under `docs/reviews/evidence/final-cdb9933-2026-10-01/`:

- `live-foundation-probe.txt` and `live-foundation-probe.json`: unchanged live 51-case results.
- `targeted-combined.txt`: 120 tests, OK.
- `contracts.json`: public versions, zero COGS, evidence keys/scoping, lifecycle/correlation, source guards.
- `containment.json`: F001/F002 imports survive controlled F005 import failure.
- `due_date_type_probe.py`: independent repro, no DB/fixture writes.
- `due-date-types.json` and `due-date-types-docker.json`: string/date succeed; datetime parser and public snapshot fail. Docker edge probe intentionally excludes Frappe to remain hermetic.

FOUNDATION VERDICT: FOUNDATION_BLOCKED

AI003 TECHNICAL SCAFFOLD READINESS: AI003_TECHNICAL_SCAFFOLD_READY: NO

REMAINING BLOCKERS: PB-DATA-01-DATETIME only — normalize accepted datetime due_date and verify parser/public snapshot regression.
