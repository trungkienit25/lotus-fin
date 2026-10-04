# AI003 Foundation Work Verification Remediation Report

**Date:** 2026-09-30  
**Target Features:** AI001 (Financial Health Analyst) & AI002 (Cash Flow Forecast Copilot)  
**Verification Environment:** Docker `frappe_docker-backend-1` / isolated site `ai003-verify.localhost`  
**Status:** REMEDIATED & DEEPLY VERIFIED  

---

## 1. Executive Summary

During foundational work verification of the AI003 copilot stack, critical foundation blockers and safety vulnerabilities were identified and remediated across AI001 (`financial_snapshot.py`, `key_reports.py`) and AI002 (`adapters.py`, `service.py`, `validation.py`):

1. **WV-01 (Report Footer Boundary Normalization):**  
   Standard Frappe `query_report.run` appends a summary footer row as a raw Python `list` at index `-1` when `add_total_row=True` and `skip_total_row=0`. Both AI001 and AI002 originally enforced rigid type checks requiring all rows in `data` to be `dict` instances. When encountering the footer, AI001 rejected the entire report as malformed (`UNAVAILABLE` metrics, `PARTIAL` snapshot), while AI002 failed closed with `DATA_PIPELINE_ERROR` (`SOURCE_ERROR`).
   - Hardened `is_valid_frappe_report_footer` to validate column alignment, ensure descriptive columns (dates, voucher numbers, po numbers, cost centers) remain empty strings, accept string-formatted Frappe column specs, and reject all-empty or invalid candidate footers.

2. **WV-02 (Party Type Master & Semantic Identity / Document Verification):**  
   Neither AI001 nor AI002 validated ERPNext `Party Type` master configuration prior to processing trade obligations, nor did they enforce strict cross-leg party/voucher checks on individual rows.
   - Added preflight master data checks verifying `Customer -> Receivable` and `Supplier -> Payable`.
   - Closed critical safety hole: added full live DB validation for `Payment Entry` vouchers in both AR and AP (rejecting non-existent, unsubmitted, company mismatch, and cross-leg entries like Supplier payments in AR).
   - Added `party_account` existence, company match, and account_type (`Receivable` vs `Payable`) verification.
   - Enforced row-level currency matching in AI001 to prevent foreign currency contamination.
   - Enforced strict envelope verification rejecting report name / key / company mismatches.

3. **WV-03 (Preservation of Fail-Closed Boundaries):**  
   All boundaries remain strictly fail-closed: unisolated COGS yields typed `UNAVAILABLE`, `as_known_at` historical replay limitation is preserved, and cache hits strictly re-authorize user permissions.

---

## 2. Root Cause Analysis & Review Audit

### WV-01: Frappe Total Footer Malformed Rejection
- In ERPNext / Frappe v16, `query_report.run` appends a summary footer row formatted as a `list` representing column totals matching the report `columns` schema.
- At the ingestion boundary:
  - `lotus_fin/api/key_reports.py:extract_key_report_data`: returned raw rows directly without normalizing the footer.
  - `lotus_fin/ai/financial_snapshot.py:validate_source_payload`: iterated over `data` and failed validation if `not isinstance(row, dict)`.
  - `lotus_fin/cashflow/adapters.py:_parse_report_rows`: failed with `ObligationSourceError(f"{source_label} payload contains malformed rows.")`.
- Result: Completely valid ERPNext reports were rejected as corrupted data.

### WV-02: Missing Preflight, Cross-Leg Contamination & Unchecked Payment Entries
- Prior review attempts addressed Sales Invoice and Purchase Invoice checks, but left **`Payment Entry` completely unchecked**. Live Docker testing confirmed that a Supplier payment entry (`ACC-PAY-2026-00004`) was silently accepted into AR obligations.
- `party_account` was not validated against the `Account` doctype: missing accounts or accounts belonging to different companies were ignored if `acc_type` was `None`.
- Row currency was ignored in AI001 `parse_ar_data` and `parse_ap_data`, allowing foreign currencies to contaminate totals.
- Report envelopes did not cross-check `report_name` or `company`, creating ingestion mismatch risks.

---

## 3. Implementation Details

### 3.1. `lotus_fin/api/key_reports.py`
- Hardened `is_valid_frappe_report_footer`:
  - Supports robust boolean coercion (`skip_total_row in (0, "0", False, "false", None, "")` and `add_total_row in (1, "1", True, "true")`).
  - Supports string-formatted Frappe column specs (`"Label:FieldType/Options:Width"`).
  - Enforces strict descriptive column cleanliness (dates, cost centers, projects, territory, po_no, voucher numbers must be empty strings or `None`).
  - Recognizes `NUMERIC_FIELDNAMES` and `isinstance(cell, (int, float, Decimal))` fallback for numeric aggregate cells.
  - Rejects candidate footers that have no non-empty aggregate/total values.
- `normalize_frappe_report_footer`:
  - Normalizes only the terminal row (`rows[-1]`). Intermediate list rows or multiple list rows fail closed.

### 3.2. `lotus_fin/ai/financial_snapshot.py`
- Uses module-level `frappe` safely decoupled from mock environments.
- Added `_has_active_db()` and `_should_validate_db_voucher(company)`.
- Updated `validate_source_payload`:
  - Added `expected_company` parameter, enforced `report_key`, `report_name`, and `company` mismatch rejections.
- Updated `parse_ar_data` and `parse_ap_data`:
  - Added `currency` parameter (default "VND"); foreign currency rows fail closed with `FinancialSourceDataError`.
  - Added live DB check for `Payment Entry`: rejects non-existent, unsubmitted, company mismatch, and cross-leg (`Supplier/Pay` in AR, `Customer/Receive` in AP).
  - Added live DB check for `party_account`: verifies existence in `Account`, company match, and account_type match (`Receivable` in AR, `Payable` in AP).
- Updated `build_financial_snapshot`:
  - Master Party Type preflight check runs whenever `_has_active_db()` is true.
  - Passes `expected_company=verified_company` to all `validate_source_payload` calls.
  - Passes `currency=currency` to `parse_ar_data` and `parse_ap_data`.

### 3.3. `lotus_fin/cashflow/adapters.py`
- Updated `_parse_report_rows`:
  - Added `report_name` and `report_key` mismatch detection.
  - Calls `normalize_frappe_report_footer`.
- Updated `_collect_obligations`:
  - Added row currency validation.
  - Added `Payment Entry` live DB validation (rejects non-existent, unsubmitted, company mismatch, cross-leg `Supplier/Pay` in AR, `Customer/Receive` in AP).
  - Added `party_account` existence, company, and account_type verification.
  - Generates canonical `source_ref` (`Payment Entry:voucher_no`).

---

## 4. Verification Record

### 4.1. Unit Test Suite (Local & Docker)

#### Local Unit Suite (182 tests across 7 test suites):
```powershell
python -m unittest -v `
  lotus_fin.tests.test_financial_snapshot `
  lotus_fin.tests.test_financial_health `
  lotus_fin.tests.test_explanation `
  lotus_fin.tests.test_cashflow_engine `
  lotus_fin.tests.test_cashflow_security `
  lotus_fin.tests.test_cashflow_failclosed `
  lotus_fin.tests.test_ai003_foundation_remediation
```
**Result:** `Ran 182 tests in 0.476s - OK`

#### Full Docker Unit Suite (218 tests):
```bash
docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 \
  /home/frappe/frappe-bench/env/bin/python -m unittest discover \
  -s /home/frappe/frappe-bench/apps/lotus_fin/lotus_fin/tests
```
**Result:** `Ran 218 tests in 7.639s - OK`  
`[AI001 EVALUATION] Successfully evaluated 15/15 scenarios. Pass rate: 100%.`

### 4.2. Live ERPNext Docker Replay (`ai003-verify.localhost` / `AI002 Fixture 2026`)

#### Replay Point 1: Cutoff `2026-09-20`
- **AI001 (`build_financial_snapshot`):**
  - Revenue: `8,000,000.0` VND (`AVAILABLE`)
  - AR Outstanding: `8,000,000.0` VND (`AVAILABLE`)
  - Overdue AR Ratio: `0.0` (`AVAILABLE`)
  - AP Outstanding: `9,500,000.0` VND (`AVAILABLE`)
  - Cash Balance: `12,000,000.0` VND (`AVAILABLE`)
  - COGS: `UNAVAILABLE` (Fail-closed limitation preserved per WV-03)
- **AI002 (`get_cash_forecast`):**
  - Status: `FORECAST_UNAVAILABLE` (Reason: `NO_CONFIRMED_SETTLEMENT_EVENTS`)
  - Opening Cash: `12,000,000.0` VND
  - Obligations Count: `10` (5 AR + 5 AP)
  - AR Sum: `8,000,000.0` VND; AP Sum: `9,500,000.0` VND

#### Replay Point 2: Cutoff `2026-09-26`
- **AI001 (`build_financial_snapshot`):**
  - Revenue: `8,000,000.0` VND (`AVAILABLE`)
  - AR Outstanding: `6,900,000.0` VND (`AVAILABLE`)
  - Overdue AR Ratio: `0.2899` (`AVAILABLE`, 2M overdue / 6.9M total)
  - AP Outstanding: `7,950,000.0` VND (`AVAILABLE`)
  - Cash Balance: `11,550,000.0` VND (`AVAILABLE`)
  - COGS: `UNAVAILABLE` (Fail-closed limitation preserved per WV-03)
- **AI002 (`get_cash_forecast`):**
  - Status: `FORECAST_UNAVAILABLE` (Reason: `NO_CONFIRMED_SETTLEMENT_EVENTS`)
  - Opening Cash: `11,550,000.0` VND
  - Obligations Count: `8` (4 AR + 4 AP)
  - AR Sum: `6,900,000.0` VND; AP Sum: `7,950,000.0` VND

#### Live Voucher & Party Security Checks in Docker:
- Non-existent `Payment Entry` row rejected (`FinancialSourceDataError: references non-existent Payment Entry`).
- Cross-leg `Payment Entry` (`ACC-PAY-2026-00004` Supplier payment injected into AR) rejected in `parse_ar_data` (`FinancialSourceDataError: references Supplier/Pay Payment Entry`).
- Cross-leg `Payment Entry` rejected in `_collect_obligations` (`ObligationSourceError: references Supplier/Pay Payment Entry 'ACC-PAY-2026-00004' in AR`).

### 4.3. GitNexus Graph Analysis
```powershell
node .gitnexus/run.cjs detect-changes --scope all --repo .
```
**Result:** `10 files, 11 symbols, 2 affected processes, risk level: medium`. Clean run (`partial: false, truncated: false`).

---

## 5. Limitations Preserved (WV-03)

In accordance with WV-03 guidelines, no unverified behaviors or synthetic numbers were fabricated:
1. P&L COGS isolation remains marked as limitation when accounts are not categorized under standard COGS group.
2. Near-term AP metric remains `UNAVAILABLE` pending frozen horizon specification.
3. Historical backdating (`as_known_at` historical point-in-time) remains explicitly documented as unsupported (posting-date semantics only).
4. AI002 future cash date settlement source remains fail-closed (`NO_CONFIRMED_SETTLEMENT_EVENTS`) rather than fabricating speculative payment dates.
5. AI003 Master SSOT status is NOT declared PASS; foundation blockers WV-01 and WV-02 are cleared, paving the way for complete AI003 copilot verification.
