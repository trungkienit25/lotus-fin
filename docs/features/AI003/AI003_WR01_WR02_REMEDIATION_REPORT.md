# AI003 — WR-01/WR-02 Remediation Report (Zcode/Antigravity, 2026-09-30)

Scope: implements `AI003_WORK_RECHECK_WR01_WR02_ANTIGRAVITY_PROMPT.md` on the AI001/AI002 foundation only. No SSOT gate changes, no `frontend` changes, no fixture changes to make numbers match. **No Work PASS and no contract freeze is declared here.** All pre-existing working-tree changes were preserved.

---

## 1. Root cause

**WR-01 — untrusted dict summary rows were silently skipped.**
The verified Frappe v16 `query_report.run` output shape (verified on the isolated site, see `evidence/AI003_WORK_VERIFICATION_2026-09-30.md`) appends the total footer as a **list row** (`add_total_row=true`, `skip_total_row=0`, footer length = column count), and that footer is separated at the envelope boundary by `normalize_frappe_report_footer`. A **dict** row carrying `is_total_row` (or a voucher-less `party="Total"`) is therefore *not* a provable Frappe output shape — yet `parse_ar_data`/`parse_ap_data` skipped any truthy `is_total_row` dict and skipped a trailing voucher-less `party="Total"` dict, and `_parse_report_rows` skipped `party="Total"` without voucher at *any* position. A fake summary dict could collapse a report into an apparent verified zero (`success + data=[]` is a verified zero; a fake summary is not).

**WR-02 — AI001 summed voucher-less rows.**
`parse_ar_data`/`parse_ap_data` only ran DB voucher verification when `voucher_no`/`name` existed, but summed every parseable row regardless, so `{"outstanding": 123}` became `AVAILABLE 123`. ERPNext AR/AP reports are built from voucher-backed GL entries: every transaction row on the live reports carries `voucher_no` (confirmed on the isolated site: 4 AR + 4 AP dict rows, all voucher-backed; the only non-dict row is the list footer). A valid transaction row cannot lack voucher identity → typed reject (mirrors the AI002 adapter, which already rejected positive obligations without a voucher).

Frappe/ERPNext official web sources were **not needed**: the installed container/site code and the prior live evidence answered both the footer shape and voucher-identity questions. No external crawl was performed.

## 2. Files changed

| File | Change |
| --- | --- |
| `lotus_fin/ai/financial_snapshot.py` | `parse_ar_data` — WR-01: unverified dict summary rows (`is_total_row` marker, or voucher-less `party="Total"` at any position) raise `FinancialSourceDataError` (lines ~376–394); WR-02: rows without voucher identity raise regardless of amount sign (lines ~543–551); docstring updated (~350). `parse_ap_data` — same two rules (WR-01 ~625–643, WR-02 ~792–800, docstring ~609). |
| `lotus_fin/cashflow/adapters.py` | `_parse_report_rows` — WR-01: dict summary rows raise `ObligationSourceError` instead of being silently filtered (lines ~346–361); docstring updated (~302). |
| `lotus_fin/tests/test_financial_snapshot.py` | Gold AR/AP fixtures conformed to the verified row shape (voucher identity added, fake dict total rows removed — numbers unchanged); anomalous-ledger fixture carries voucher identity; suite made hermetic via `patch("lotus_fin.ai.financial_snapshot.frappe", None)` in `setUp` (see §5 regression note). |
| `lotus_fin/tests/test_ai003_foundation_remediation.py` | Old `test_summary_row_dict_filtered_without_raising` rewritten as `test_summary_row_dict_fails_closed` (trailing + mid-report); new `TestWR01WR02UntrustedSummaryAndVoucherlessRows` class with 15 regressions incl. both recheck repros and top-level acceptance paths. |
| `lotus_fin/tests/test_explanation.py`, `lotus_fin/tests/test_financial_health.py` | AR/AP fixture rows given voucher identity (numbers unchanged). |

## 3. Before → after (repro results)

| Probe | Before | After |
| --- | --- | --- |
| `parse_ar_data([{"is_total_row": True, "outstanding": 123}])` | `(0, 0, 0)` apparent verified zero | `FinancialSourceDataError` |
| `parse_ap_data([{"party": "Total", "outstanding": 123}])` (any position) | trailing skipped / mid raised | `FinancialSourceDataError` |
| `_parse_report_rows({"status": "success", "data": [{"is_total_row": True, "outstanding": 123}]}, "Accounts Receivable")` | `[]` → fake empty obligation set | `ObligationSourceError` |
| `parse_ar_data([{"outstanding": 123}])` (WR-02 repro) | `AVAILABLE 123` | `FinancialSourceDataError` (same for `parse_ap_data`) |
| `build_financial_snapshot` with poisoned AR source | zero/partial metric | `ar_outstanding` **UNAVAILABLE**, source listed in `missing_inputs` |
| `{"party": "Total"}` **with** voucher identity | processed | still processed as a transaction row — the party string alone is never summary authority; the voucher is DB-verified when a DB is active |

Contract decisions (evidence-based):
- The only proven footer shape (list row via `normalize_frappe_report_footer`) is unchanged and continues to be handled at the envelope boundary.
- Every AR/AP transaction row must carry `voucher_no` or `name`; voucher-less rows raise typed regardless of amount sign (strictly stronger than AI002's adapter, which skips `amount <= 0` before the voucher check because such rows cannot affect the obligation set — noted for Work).
- `success + data=[]` remains the only legitimate verified zero.
- All-summary, mixed valid+fake, fake truthy markers (`1`, `"1"`, `"true"`, `"yes"`), malformed amounts all raise typed.

## 4. Test commands and real results

```
# Local (7 AI001/AI002 suites)
python -m pytest lotus_fin/tests/test_financial_snapshot.py lotus_fin/tests/test_financial_health.py \
  lotus_fin/tests/test_explanation.py lotus_fin/tests/test_ai003_foundation_remediation.py \
  lotus_fin/tests/test_cashflow_failclosed.py lotus_fin/tests/test_cashflow_engine.py \
  lotus_fin/tests/test_cashflow_security.py -q
→ 197 passed (baseline 182 + 15 new WR regressions)

# Docker backend (same 7 suites)
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 \
  /home/frappe/frappe-bench/env/bin/python -m unittest -q \
  lotus_fin.tests.test_financial_snapshot lotus_fin.tests.test_financial_health \
  lotus_fin.tests.test_explanation lotus_fin.tests.test_cashflow_engine \
  lotus_fin.tests.test_cashflow_security lotus_fin.tests.test_cashflow_failclosed \
  lotus_fin.tests.test_ai003_foundation_remediation
→ Ran 197 tests — OK

# Docker full discovery
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 \
  /home/frappe/frappe-bench/env/bin/python -m unittest discover \
  -s /home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/tests
→ Ran 233 tests — OK (baseline 218 + 15); [AI001 EVALUATION] 15/15, pass rate 100%
```

**Regression note (discovered and fixed during Docker discovery):** the full run initially failed 2 tests in `test_financial_snapshot.py` — `test_access_and_reports.py:setUpClass` connects frappe to site `frontend` and runs first alphabetically, so the new voucher-identity validation routed fixture vouchers against the live site (where they do not exist), degrading the snapshots to `PARTIAL`. Fix: the raw_sources suite is now hermetic (`frappe` patched to `None` in `setUp`). The pre-existing pollution itself (site suites never destroying the frappe context for later suites) is a test-hygiene issue **left for Work** — not touched this round.

## 5. Live replay — isolated site `ai003-verify.localhost` (Frappe 16.34.0 / ERPNext 16.35.0, Administrator, read-only)

Scope preflight: `resolve_cash_account_scope` → `RESOLVED / APPROVED`, scope `["Cash - A2F"]`.

| Check | Cutoff 2026-09-20 | Cutoff 2026-09-26 | Oracle |
| --- | --- | --- | --- |
| AI001 revenue | AVAILABLE 8,000,000 | AVAILABLE 8,000,000 | 8,000,000 ✓ |
| AI001 ar_outstanding | AVAILABLE 8,000,000 | AVAILABLE 6,900,000 | 8,000,000 / 6,900,000 ✓ |
| AI001 overdue_ar_ratio | AVAILABLE 0.0 | AVAILABLE 0.2899 | 0.0 / 0.2899 ✓ |
| AI001 ap_outstanding | AVAILABLE 9,500,000 | AVAILABLE 7,950,000 | 9,500,000 / 7,950,000 ✓ |
| AI001 cash_balance | AVAILABLE 12,000,000 | AVAILABLE 11,550,000 | 12,000,000 / 11,550,000 ✓ |
| AI001 COGS | UNAVAILABLE | UNAVAILABLE | WV-03 limitation preserved ✓ |
| AI001 overall | PARTIAL | PARTIAL | same as prior recheck ✓ |
| AI002 opening cash | 12,000,000 | 11,550,000 | ✓ |
| AI002 obligations | 10 (5 AR + 5 AP), AR 8m / AP 9.5m | 8 (4 AR + 4 AP), AR 6.9m / AP 7.95m | ✓ |
| AI002 status | FORECAST_UNAVAILABLE (fail-closed future events) | FORECAST_UNAVAILABLE | ✓ |

**All oracle numbers match with the new fail-closed code live** — the legitimate Frappe list footer and voucher-backed rows pass through the new checks unchanged.

**Live injection probe** (poison appended to the live AR fetch boundary; script `docker/ai003-local/wr_inject_probe.py`):
- fake `is_total_row` dict → `ar_outstanding UNAVAILABLE`, `accounts_receivable` in `missing_inputs` ✓
- fake `party="Total"` dict (no voucher) → UNAVAILABLE ✓
- voucher-less positive row → UNAVAILABLE ✓ (asserts enforced in-script)
- AI002 clean read on the same site still returns obligations (legitimate path unaffected) ✓

Replay script: `docker/ai003-local/wr_replay.py` (AI001 via `source_fetcher=extract_key_report_data`; AI002 windows `financial_as_of+1..+30d`).

Container note: the `lotus-fin:ai003-local` image has no bind mount, so the 14 working-tree files were synced with `docker cp` into the running backend for the Docker runs; the image must be rebuilt to bake the changes permanently.

## 6. GitNexus results

- `impact parse_ar_data --direction upstream` → `build_financial_snapshot` → `get_financial_snapshot` (index **10 commits behind** — staleness caveat noted by the tool).
- `impact _parse_report_rows` → `risk: UNKNOWN`; per protocol resolved by code search: only production caller is `_collect_obligations` (`cashflow/adapters.py:402`) plus tests.
- `impact parse_ap_data` → `risk: LOW`; callers `build_financial_snapshot` + tests.
- `detect-changes --scope all` → **13 files, 11 symbols, 2 affected execution flows, risk level: medium**; clean run (no `partial`/`truncated` flag). Because the index is stale, graph output was treated as supporting evidence; regression safety is carried by the 197/233 test runs and the live oracle replay.

## 7. Limits and handoff

1. **WV-03 untouched:** COGS mapping, `as_known_at` temporal semantics, gold signal/threshold/severity, and live cache-revocation replay remain open.
2. AI003 engine, thresholds, severity and signal gold are out of scope this round.
3. The voucher-less `amount <= 0` asymmetry between AI001 (typed reject) and AI002 adapter (skip before voucher check, cannot affect obligations) is documented in §3 — flagging for Work to confirm the intended consistency bar.
4. Test-order pollution by site suites (see §4) is a pre-existing hygiene issue left for Work.
5. **Gate status is unchanged by this report**: Work must re-run the adversarial + live verification pass; Chat decides contract freeze. Nothing here claims PASS.
