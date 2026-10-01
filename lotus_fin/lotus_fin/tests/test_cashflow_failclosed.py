"""
AI002 Fail-Closed Regression Suite (Remediation Round 3)

Proves by behavior (not type checks) that:
  Fix A — AR/AP source errors, unknown statuses, malformed payloads, timeouts and
          permission denials become typed errors; they are never converted into a
          zero/empty-leg result, never cached, and a later call re-reads the source.
  Fix B — Opening cash reconciles against the independent Trial Balance for the
          FULL authorized account set (a missing/duplicate TB row fails closed);
          genuine zero balances reconcile only when the account is present in TB;
          no-DB runs are never labeled reconciled; the service computes no
          forecast points/shortfall from unverified opening cash.
  Fix C — Account scope is resolved server-side with no 50-account cap, restricted
          cash is never auto-included, empty scope is NEEDS_REVIEW, and client
          supplied restricted accounts are rejected.

All financial fixtures here are synthetic test constructs (SYNTHETIC_TEST_ONLY),
not real SME data.
"""
import os
import unittest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from lotus_fin.modules.f002_cashflow import adapters
from lotus_fin.modules.f002_cashflow.adapters import (
    ObligationSourceError,
    ObligationPermissionError,
    get_opening_cash_ledger,
    get_trade_obligations,
    resolve_cash_account_scope,
)
from lotus_fin.modules.f002_cashflow.models import (
    ForecastRequest,
    ForecastStatus,
    ReasonCode,
    OpeningCash,
    AccountBalance,
)
from lotus_fin.modules.f002_cashflow.service import get_cash_forecast, resolve_request_scope
from lotus_fin.modules.f002_cashflow.source_interface import SyntheticFixtureSource, FailClosedSource
from lotus_fin.modules.f002_cashflow.validation import validate_forecast_request


COMPANY = "AI002 Fixture 2026"
AS_OF = date(2026, 9, 26)
START = date(2026, 9, 27)
END = date(2026, 10, 26)

AR_SUCCESS_ZERO = {"status": "success", "company": COMPANY, "data": []}
AP_SUCCESS_ZERO = {"status": "success", "company": COMPANY, "data": []}
AR_SUCCESS_ROWS = {
    "status": "success",
    "company": COMPANY,
    "data": [
        {"voucher_no": "SINV-0001", "party": "Customer A", "outstanding": 3000000, "due_date": "2026-10-01", "currency": "VND"},
        {"voucher_no": "SINV-0002", "party": "Customer B", "outstanding": 2000000, "due_date": "2026-09-20", "currency": "VND"},
        {"voucher_no": "SINV-0003", "party": "Customer C", "outstanding": 0, "due_date": "2026-09-25", "currency": "VND"},
    ],
}
AP_SUCCESS_ROWS = {
    "status": "success",
    "company": COMPANY,
    "data": [
        {"voucher_no": "PINV-0001", "party": "Supplier Z", "outstanding": 1000000, "due_date": "2026-10-05", "currency": "VND"},
    ],
}


def verified_opening_cash():
    return OpeningCash(
        aggregate_amount=Decimal("11550000"),
        reconciliation="ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED",
        has_constituent_deficit=False,
        accounts=[
            AccountBalance(account="Cash - A2F", amount=Decimal("11550000"), currency="VND", deficit=False)
        ],
    )


def make_request(scope=None):
    return ForecastRequest(
        company=COMPANY,
        financial_as_of=AS_OF,
        forecast_start=START,
        forecast_end=END,
        reporting_currency="VND",
        cash_account_scope=scope if scope is not None else ["Cash - A2F"],
    )


class TestObligationFailClosed(unittest.TestCase):
    """Fix A: every non-success AR/AP outcome raises a typed error."""

    def _run(self, extract_side_effect=None, extract_return=None, perm_side_effect=None):
        with patch("lotus_fin.modules.f002_cashflow.adapters.frappe"), patch.object(
            adapters, "check_ai002_report_permission", side_effect=perm_side_effect
        ) as perm_mock, patch.object(
            adapters,
            "extract_key_report_data",
            side_effect=extract_side_effect,
            return_value=extract_return,
        ) as extract_mock:
            result, error = None, None
            try:
                result = get_trade_obligations(COMPANY, as_of=AS_OF)
            except (ObligationSourceError, ObligationPermissionError) as e:
                error = e
        return result, error, extract_mock, perm_mock

    def test_ar_ap_success_zero_records_is_verified_zero(self):
        """A successful, correctly scoped read with zero rows returns [] — and the
        test proves BOTH report sources were actually read (not silently skipped)."""
        result, error, extract_mock, _ = self._run(
            extract_side_effect=[AR_SUCCESS_ZERO, AP_SUCCESS_ZERO]
        )
        self.assertIsNone(error)
        self.assertEqual(result, [])
        self.assertEqual(extract_mock.call_count, 2)

    def test_ar_error_status_raises_typed(self):
        result, error, _, _ = self._run(extract_side_effect=[{"status": "error", "message": "internal detail"}])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)
        self.assertIn("Accounts Receivable", str(error))
        # No sensitive payload text in the error message
        self.assertNotIn("internal detail", str(error))

    def test_ar_unknown_status_raises_typed(self):
        result, error, _, _ = self._run(
            extract_side_effect=[{"status": "partial", "data": [{"voucher_no": "SINV-1", "outstanding": 10}]}]
        )
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_ar_none_response_raises_typed(self):
        result, error, _, _ = self._run(extract_side_effect=[None])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_ar_missing_data_key_raises_typed(self):
        result, error, _, _ = self._run(extract_side_effect=[{"status": "success"}])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_ar_non_list_data_raises_typed(self):
        result, error, _, _ = self._run(extract_side_effect=[{"status": "success", "data": {"rows": []}}])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_ar_exception_raises_typed_without_leak(self):
        result, error, _, _ = self._run(extract_side_effect=[Exception("raw db traceback 42")])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)
        self.assertNotIn("raw db traceback 42", str(error))

    def test_ar_permission_denied_raises_typed(self):
        result, error, _, perm_mock = self._run(perm_side_effect=Exception("FORBIDDEN"))
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationPermissionError)
        perm_mock.assert_called_once_with("Accounts Receivable")

    def test_malformed_row_missing_outstanding_raises_typed(self):
        payload = {"status": "success", "company": COMPANY, "data": [{"voucher_no": "SINV-0001", "party": "X"}]}
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_positive_outstanding_without_voucher_raises_typed(self):
        payload = {"status": "success", "company": COMPANY, "data": [{"party": "X", "outstanding": 500}]}
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_malformed_due_date_raises_typed(self):
        payload = {
            "status": "success",
            "company": COMPANY,
            "data": [{"voucher_no": "SINV-0001", "party": "X", "outstanding": 100, "due_date": "01/10/2026"}],
        }
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_non_dict_row_fails_closed(self):
        """Round 4: a success payload with ANY non-dict row must fail closed —
        malformed rows are never silently dropped."""
        payload = {
            "status": "success",
            "company": COMPANY,
            "data": [{"voucher_no": "SINV-0001", "party": "X", "outstanding": 100}, "garbage-row"],
        }
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_payload_company_mismatch_fails_closed(self):
        payload = {
            "status": "success",
            "company": "OTHER COMPANY",
            "data": [{"voucher_no": "SINV-0001", "party": "X", "outstanding": 100, "currency": "VND"}],
        }
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_row_currency_mismatch_fails_closed(self):
        payload = {
            "status": "success",
            "company": COMPANY,
            "data": [{"voucher_no": "SINV-0001", "party": "X", "outstanding": 100, "currency": "USD"}],
        }
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_non_numeric_amount_fails_closed(self):
        payload = {
            "status": "success",
            "company": COMPANY,
            "data": [{"voucher_no": "SINV-0001", "party": "X", "outstanding": "not-a-number", "currency": "VND"}],
        }
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_nan_amount_fails_closed(self):
        payload = {
            "status": "success",
            "company": COMPANY,
            "data": [{"voucher_no": "SINV-0001", "party": "X", "outstanding": "NaN", "currency": "VND"}],
        }
        result, error, _, _ = self._run(extract_side_effect=[payload])
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_ap_exception_after_ar_success_fails_closed(self):
        """AR read succeeds, then AP fails: the whole read fails closed — a failed
        leg is never reported as a complete/zero leg."""
        result, error, extract_mock, _ = self._run(
            extract_side_effect=[AR_SUCCESS_ROWS, Exception("AP source down")]
        )
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)
        self.assertIn("Accounts Payable", str(error))
        self.assertEqual(extract_mock.call_count, 2)

    def test_ap_error_status_after_ar_success_fails_closed(self):
        result, error, extract_mock, _ = self._run(
            extract_side_effect=[AR_SUCCESS_ROWS, {"status": "error", "message": "x"}]
        )
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)
        self.assertEqual(extract_mock.call_count, 2)

    def test_rows_parsed_with_hash_and_zero_rows_skipped(self):
        result, error, _, _ = self._run(extract_side_effect=[AR_SUCCESS_ROWS, AP_SUCCESS_ROWS])
        self.assertIsNone(error)
        ar = [o for o in result if o.type == "AR"]
        ap = [o for o in result if o.type == "AP"]
        self.assertEqual(len(ar), 2)  # zero-outstanding row contributes no obligation
        self.assertEqual(len(ap), 1)
        self.assertEqual(ar[0].source_ref, "Sales Invoice:SINV-0001")
        self.assertEqual(ar[0].remaining_amount, Decimal("3000000"))
        self.assertEqual(ar[0].due_date, date(2026, 10, 1))
        self.assertEqual(ap[0].party_hash, adapters.hash_party("Supplier Z"))
        self.assertNotIn("Supplier Z", str(ap[0].party_hash))  # pseudonymized


class TestOpeningCashReconciliation(unittest.TestCase):
    """Fix B: independent Trial Balance reconciliation over the full account set."""

    def _run(self, gl_rows, tb_return=None, tb_side_effect=None, scope=None, perm_side_effect=None):
        with patch("lotus_fin.modules.f002_cashflow.adapters.frappe") as frappe_mock, patch.object(
            adapters, "check_ai002_report_permission", side_effect=perm_side_effect
        ), patch.object(
            adapters,
            "extract_key_report_data",
            side_effect=tb_side_effect,
            return_value=tb_return,
        ):
            frappe_mock.db.sql.return_value = gl_rows
            result, error = None, None
            try:
                result = get_opening_cash_ledger(COMPANY, AS_OF, account_scope=scope or ["Cash - A2F"])
            except (ObligationSourceError, ObligationPermissionError) as e:
                error = e
        return result, error

    def test_gl_equals_tb_full_scope_reconciled(self):
        tb = {
            "status": "success",
            "company": COMPANY,
            "data": [{"account": "Cash - A2F", "closing_debit": 11550000, "closing_credit": 0}],
        }
        opening, error = self._run(
            gl_rows=[{"account": "Cash - A2F", "balance": 11550000}], tb_return=tb
        )
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED")
        self.assertEqual(opening.aggregate_amount, Decimal("11550000"))

    def test_tb_missing_scope_account_is_inconsistent(self):
        """TB succeeds but one scope account has no TB row: fail closed even if a
        naive totals comparison could look acceptable."""
        tb = {"status": "success", "company": COMPANY, "data": []}
        opening, error = self._run(
            gl_rows=[{"account": "Cash - A2F", "balance": 1000}],
            tb_return=tb,
            scope=["Cash - A2F", "Bank - A2F"],
        )
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "INCONSISTENT_DATA")

    def test_duplicate_tb_rows_are_inconsistent(self):
        """Duplicate TB rows for one scope account make the totals ambiguous.
        Old code summed duplicates and could reconcile; new code fails closed."""
        tb = {
            "status": "success",
            "company": COMPANY,
            "data": [
                {"account": "Cash - A2F", "closing_debit": 500, "closing_credit": 0},
                {"account": "Cash - A2F", "closing_debit": 500, "closing_credit": 0},
            ],
        }
        opening, error = self._run(gl_rows=[{"account": "Cash - A2F", "balance": 1000}], tb_return=tb)
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "INCONSISTENT_DATA")

    def test_tb_total_mismatch_is_inconsistent(self):
        tb = {
            "status": "success",
            "company": COMPANY,
            "data": [{"account": "Cash - A2F", "closing_debit": 999, "closing_credit": 0}],
        }
        opening, error = self._run(gl_rows=[{"account": "Cash - A2F", "balance": 11550000}], tb_return=tb)
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "INCONSISTENT_DATA")

    def test_offsetting_accounts_with_zeroed_tb_are_inconsistent(self):
        """Round 4: GL A=100, B=-100 (net 0) vs TB A=0, B=0 — totals match but the
        per-account balances disagree. Old code compared totals only and would
        have labeled this reconciled."""
        tb = {
            "status": "success",
            "company": COMPANY,
            "data": [
                {"account": "Bank A", "closing_debit": 0, "closing_credit": 0},
                {"account": "Bank B", "closing_debit": 0, "closing_credit": 0},
            ],
        }
        opening, error = self._run(
            gl_rows=[
                {"account": "Bank A", "balance": 100},
                {"account": "Bank B", "balance": -100},
            ],
            tb_return=tb,
            scope=["Bank A", "Bank B"],
        )
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "INCONSISTENT_DATA")

    def test_tb_error_is_reconciliation_unavailable(self):
        opening, error = self._run(
            gl_rows=[{"account": "Cash - A2F", "balance": 11550000}],
            tb_side_effect=Exception("tb engine failure"),
        )
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "RECONCILIATION_UNAVAILABLE")

    def test_tb_error_status_is_reconciliation_unavailable(self):
        opening, error = self._run(
            gl_rows=[{"account": "Cash - A2F", "balance": 11550000}],
            tb_return={"status": "error", "message": "x"},
        )
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "RECONCILIATION_UNAVAILABLE")

    def test_tb_wrong_company_is_reconciliation_unavailable(self):
        tb = {
            "status": "success",
            "company": "OTHER COMPANY",
            "data": [{"account": "Cash - A2F", "closing_debit": 11550000, "closing_credit": 0}],
        }
        opening, error = self._run(
            gl_rows=[{"account": "Cash - A2F", "balance": 11550000}], tb_return=tb
        )
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "RECONCILIATION_UNAVAILABLE")

    def test_valid_zero_balance_reconciles_when_account_present_in_tb(self):
        """Genuine zero: GL has no entries and the account IS present in TB with a
        zero balance. The account must be listed with 0 and fully reconciled —
        not merely two zeros compared."""
        tb = {
            "status": "success",
            "company": COMPANY,
            "data": [{"account": "Cash - A2F", "closing_debit": 0, "closing_credit": 0}],
        }
        opening, error = self._run(gl_rows=[], tb_return=tb)
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED")
        self.assertEqual(opening.aggregate_amount, Decimal("0"))
        self.assertEqual(len(opening.accounts), 1)
        self.assertEqual(opening.accounts[0].account, "Cash - A2F")
        self.assertEqual(opening.accounts[0].amount, Decimal("0"))
        self.assertFalse(opening.accounts[0].deficit)

    def test_zero_without_tb_row_is_inconsistent(self):
        """GL=0 with the account absent from TB must fail closed — the account set
        was never verified (the core Fix B zero-case)."""
        tb = {"status": "success", "company": COMPANY, "data": []}
        opening, error = self._run(gl_rows=[], tb_return=tb)
        self.assertIsNone(error)
        self.assertEqual(opening.reconciliation, "INCONSISTENT_DATA")

    def test_opening_permission_denied_raises_typed(self):
        with patch("lotus_fin.modules.f002_cashflow.adapters.frappe"), patch.object(
            adapters, "check_ai002_report_permission", side_effect=Exception("FORBIDDEN")
        ), patch.object(adapters, "extract_key_report_data"):
            with self.assertRaises(ObligationPermissionError):
                get_opening_cash_ledger(COMPANY, AS_OF, account_scope=["Cash - A2F"])

    def test_gl_query_failure_raises_typed(self):
        with patch("lotus_fin.modules.f002_cashflow.adapters.frappe") as frappe_mock, patch.object(
            adapters, "check_ai002_report_permission"
        ), patch.object(adapters, "extract_key_report_data"):
            frappe_mock.db.sql.side_effect = Exception("db down")
            with self.assertRaises(ObligationSourceError):
                get_opening_cash_ledger(COMPANY, AS_OF, account_scope=["Cash - A2F"])

    def test_empty_scope_returns_unavailable_without_selection(self):
        opening = get_opening_cash_ledger(COMPANY, AS_OF, account_scope=[])
        self.assertEqual(opening.reconciliation, "RECONCILIATION_UNAVAILABLE")
        self.assertEqual(opening.aggregate_amount, Decimal("0"))
        self.assertEqual(opening.accounts, [])

    def test_intraday_label_when_as_of_is_today(self):
        tb = {
            "status": "success",
            "company": COMPANY,
            "data": [{"account": "Cash - A2F", "closing_debit": 1000, "closing_credit": 0}],
        }
        with patch("lotus_fin.modules.f002_cashflow.adapters.frappe") as frappe_mock, patch.object(
            adapters, "check_ai002_report_permission"
        ), patch.object(adapters, "extract_key_report_data", return_value=tb):
            frappe_mock.db.sql.return_value = [{"account": "Cash - A2F", "balance": 1000}]
            opening = get_opening_cash_ledger(COMPANY, date.today(), account_scope=["Cash - A2F"])
        self.assertEqual(opening.reconciliation, "ERP_GL_EQUALS_TRIAL_BALANCE_INTRADAY_UNCLOSED")


class TestServiceFailClosed(unittest.TestCase):
    """Service-level fail-closed contract: typed statuses, no financial payload on
    errors, no forecast points from unverified opening cash, errors not cached."""

    def setUp(self):
        from lotus_fin.modules.f002_cashflow import cache
        cache._CACHE_STORE.clear()
        cache._SINGLE_FLIGHT_LOCKS.clear()

        # Service-level tests target orchestration behavior; request validation
        # (including the approved-scope check against the live DB) is exercised
        # separately in TestAccountScopeResolution.
        self._validation_patcher = patch(
            "lotus_fin.modules.f002_cashflow.service.validate_forecast_request",
            return_value=(True, None, None),
        )
        self._validation_patcher.start()
        self.addCleanup(self._validation_patcher.stop)

        candidate_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json")),
            "/home/frappe/frappe-bench/apps/lotus_fin/docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json",
        ]
        self.fixture_path = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])

    def _fixture_source(self):
        return SyntheticFixtureSource(self.fixture_path)

    def test_source_error_response_and_recovery_after_retry(self):
        """AR/AP failure returns typed SOURCE_ERROR with no financial payload and is
        NOT cached: the immediate next call re-reads the source and succeeds."""
        request = make_request()
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger", return_value=verified_opening_cash()
        ), patch(
            "lotus_fin.modules.f002_cashflow.service.get_trade_obligations",
            side_effect=[ObligationSourceError("Accounts Receivable report source failed."), []],
        ) as obligations_mock:
            first = get_cash_forecast(request, user="tester", future_event_source=self._fixture_source(), skip_cache=True)
            second = get_cash_forecast(request, user="tester", future_event_source=self._fixture_source(), skip_cache=False)

        self.assertEqual(first.status, ForecastStatus.SOURCE_ERROR)
        self.assertEqual(first.reason_code, ReasonCode.DATA_PIPELINE_ERROR)
        self.assertEqual(first.obligations, [])
        self.assertEqual(first.forecast_points, [])
        self.assertIsNone(first.opening_cash)
        self.assertEqual(first.verified_company, COMPANY)

        # Recovery: second call re-read the source (obligations adapter called twice)
        self.assertEqual(obligations_mock.call_count, 2)
        self.assertEqual(second.status, ForecastStatus.PARTIAL)
        self.assertEqual(len(second.forecast_points), 30)

    def test_permission_error_returns_forbidden_without_payload(self):
        request = make_request()
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger", return_value=verified_opening_cash()
        ), patch(
            "lotus_fin.modules.f002_cashflow.service.get_trade_obligations",
            side_effect=ObligationPermissionError("Permission denied accessing Accounts Receivable."),
        ):
            resp = get_cash_forecast(request, user="tester", future_event_source=self._fixture_source(), skip_cache=True)

        self.assertEqual(resp.status, ForecastStatus.FORBIDDEN)
        self.assertEqual(resp.reason_code, ReasonCode.UNAUTHORIZED_ACCESS)
        self.assertEqual(resp.verified_company, "")
        self.assertEqual(resp.obligations, [])
        self.assertEqual(resp.forecast_points, [])
        self.assertIsNone(resp.opening_cash)

    def test_reconciliation_unavailable_blocks_computation(self):
        """Events exist but opening cash was never reconciled: no forecast points,
        no shortfall — the old path computed a full 30-day forecast anyway."""
        unverified = OpeningCash(
            aggregate_amount=Decimal("11550000"),
            reconciliation="RECONCILIATION_UNAVAILABLE",
            has_constituent_deficit=False,
            accounts=[],
        )
        request = make_request()
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger", return_value=unverified
        ), patch("lotus_fin.modules.f002_cashflow.service.get_trade_obligations", return_value=[]):
            resp = get_cash_forecast(request, user="tester", future_event_source=self._fixture_source(), skip_cache=True)

        self.assertEqual(resp.status, ForecastStatus.INSUFFICIENT_DATA)
        self.assertEqual(resp.reason_code, ReasonCode.DATA_PIPELINE_ERROR)
        self.assertEqual(resp.forecast_points, [])
        self.assertEqual(resp.shortfall_events, [])

    def test_inconsistent_reconciliation_blocks_computation(self):
        inconsistent = OpeningCash(
            aggregate_amount=Decimal("11550000"),
            reconciliation="INCONSISTENT_DATA",
            has_constituent_deficit=False,
            accounts=[],
        )
        request = make_request()
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger", return_value=inconsistent
        ), patch("lotus_fin.modules.f002_cashflow.service.get_trade_obligations", return_value=[]):
            resp = get_cash_forecast(request, user="tester", future_event_source=self._fixture_source(), skip_cache=True)

        self.assertEqual(resp.status, ForecastStatus.INCONSISTENT_DATA)
        self.assertEqual(resp.forecast_points, [])
        self.assertEqual(resp.shortfall_events, [])

    def test_unknown_reconciliation_label_fails_closed(self):
        """Any reconciliation label outside the verified set is unverified."""
        stale = OpeningCash(
            aggregate_amount=Decimal("11550000"),
            reconciliation="TRIAL_BALANCE_RECONCILED",
            has_constituent_deficit=False,
            accounts=[],
        )
        request = make_request()
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger", return_value=stale
        ), patch("lotus_fin.modules.f002_cashflow.service.get_trade_obligations", return_value=[]):
            resp = get_cash_forecast(request, user="tester", future_event_source=self._fixture_source(), skip_cache=True)

        self.assertNotEqual(resp.status, ForecastStatus.PARTIAL)
        self.assertEqual(resp.forecast_points, [])

    def test_verified_reconciliation_allows_forecast(self):
        """Control case: verified opening + events -> PARTIAL with 30 points.
        Fixture events: +2,000,000 on 2026-09-29, so the first day (2026-09-27)
        still carries the opening 11,550,000."""
        request = make_request()
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger", return_value=verified_opening_cash()
        ), patch("lotus_fin.modules.f002_cashflow.service.get_trade_obligations", return_value=[]):
            resp = get_cash_forecast(request, user="tester", future_event_source=self._fixture_source(), skip_cache=True)

        self.assertEqual(resp.status, ForecastStatus.PARTIAL)
        self.assertEqual(len(resp.forecast_points), 30)
        self.assertEqual(resp.forecast_points[0].date, START)
        self.assertEqual(resp.forecast_points[0].modeled_cash, Decimal("11550000"))
        self.assertEqual(resp.forecast_points[2].date, date(2026, 9, 29))
        self.assertEqual(resp.forecast_points[2].modeled_cash, Decimal("13550000"))

    def test_unverified_opening_with_no_events_is_not_valid_baseline(self):
        """Fix B (round 4): with no future events AND unverified opening cash the
        response must fail closed — the old path returned/cached FORECAST_UNAVAILABLE
        carrying unverified opening cash as if it were a valid baseline."""
        unverified = OpeningCash(
            aggregate_amount=Decimal("11550000"),
            reconciliation="RECONCILIATION_UNAVAILABLE",
            has_constituent_deficit=False,
            accounts=[],
        )
        request = make_request()
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger", return_value=unverified
        ), patch("lotus_fin.modules.f002_cashflow.service.get_trade_obligations", return_value=[]):
            resp = get_cash_forecast(
                request, user="tester", future_event_source=FailClosedSource(), skip_cache=True
            )

        self.assertNotEqual(resp.status, ForecastStatus.FORECAST_UNAVAILABLE)
        self.assertEqual(resp.status, ForecastStatus.INSUFFICIENT_DATA)
        self.assertEqual(resp.forecast_points, [])
        self.assertEqual(resp.shortfall_events, [])
        self.assertIsNone(resp.opening_cash)  # fail-closed: no unverified financial payload


class TestAccountScopeResolution(unittest.TestCase):
    """Round 5: approved-scope model. Account read permission enforced with a
    permission-aware paginated query; partial visibility fails closed; the
    approved Company configuration is the only authorization; missing/invalid/
    stale configuration blocks the forecast."""

    def _run_resolver(
        self,
        leaf_names,
        total_count=None,
        config_raw=None,
        has_permission=True,
        get_list_batches=None,
        get_value_exception=False,
        page_length=None,
    ):
        scope_page_patcher = (
            patch.object(adapters, "SCOPE_PAGE_LENGTH", page_length)
            if page_length is not None
            else None
        )
        if scope_page_patcher:
            scope_page_patcher.start()
        try:
            with patch("lotus_fin.modules.f002_cashflow.adapters.frappe") as frappe_mock:
                frappe_mock.has_permission.return_value = has_permission
                if get_list_batches is None:
                    get_list_batches = [[{"name": n} for n in leaf_names]]
                frappe_mock.get_list.side_effect = list(get_list_batches)
                frappe_mock.db.count.return_value = (
                    len(leaf_names) if total_count is None else total_count
                )
                if get_value_exception:
                    frappe_mock.db.get_value.side_effect = Exception("db error")
                else:
                    frappe_mock.db.get_value.return_value = config_raw
                result, error = None, None
                try:
                    result = resolve_cash_account_scope(COMPANY, user="tester")
                except (ObligationSourceError, ObligationPermissionError) as e:
                    error = e
                return result, error, frappe_mock
        finally:
            if scope_page_patcher:
                scope_page_patcher.stop()

    def test_scope_approved_resolved_without_cap(self):
        """Round 5: the approved scope is returned in full — no 50-account cap —
        and only the permission-aware get_list is used (never get_all)."""
        names = [f"Bank - {i:03d}" for i in range(55)]
        config = '["' + '", "'.join(names) + '"]'
        result, error, frappe_mock = self._run_resolver(names, config_raw=config)

        self.assertIsNone(error)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["approval"], "APPROVED")
        self.assertEqual(result["count"], 55)
        self.assertEqual(result["scope"], names)
        self.assertEqual(result["unapproved_excluded"], [])
        frappe_mock.get_list.assert_called()  # permission-aware query used
        frappe_mock.get_all.assert_not_called()  # get_all is not authorization evidence

    def test_scope_uses_full_pagination(self):
        """Round 5: listing pages through the permission-aware query until
        exhausted (page size forced to 10; 25 accounts over 3 pages)."""
        names = [f"Bank - {i:03d}" for i in range(25)]
        config = '["' + '", "'.join(names) + '"]'
        batches = [[{"name": n} for n in names[i:i + 10]] for i in range(0, 25, 10)]
        result, error, frappe_mock = self._run_resolver(
            names,
            config_raw=config,
            get_list_batches=batches,
            page_length=10,
        )

        self.assertIsNone(error)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(len(result["scope"]), 25)
        self.assertEqual(frappe_mock.get_list.call_count, 3)

    def test_scope_no_account_read_permission_fails_closed(self):
        """User can read the Company but not the Account doctype: typed permission
        failure, no account query, no account names in the error."""
        result, error, frappe_mock = self._run_resolver(
            ["Cash - A2F"], has_permission=False, config_raw='["Cash - A2F"]'
        )
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationPermissionError)
        self.assertEqual(str(error), "Access Denied")
        frappe_mock.get_list.assert_not_called()

    def test_scope_partial_account_visibility_fails_closed(self):
        """User reads only part of the company's accounts (3 visible of 5
        existing): a partial scope is never returned — typed permission error."""
        result, error, _ = self._run_resolver(
            ["Cash - A2F", "Bank - A2F", "Tien - A2F"], total_count=5
        )
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationPermissionError)
        self.assertEqual(str(error), "Access Denied")

    def test_scope_cross_company_visibility_denied(self):
        """User with Account permissions for another company sees zero accounts
        of this one: permission failure, not a valid empty scope."""
        result, error, _ = self._run_resolver([], total_count=4)
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationPermissionError)

    def test_scope_read_error_is_typed_not_empty(self):
        """A read error must fail closed with a typed error — never become an
        empty-but-valid scope or NEEDS_REVIEW."""
        result, error, _ = self._run_resolver(
            ["Cash - A2F"],
            get_list_batches=[Exception("listing failed")],
        )
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_scope_zero_accounts_is_needs_review(self):
        """Successful read with genuinely zero accounts: valid NEEDS_REVIEW state
        (distinct from a permission failure)."""
        result, error, _ = self._run_resolver([], total_count=0, config_raw=None)
        self.assertIsNone(error)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["approval"], "MISSING_CONFIG")
        self.assertEqual(result["scope"], [])
        self.assertEqual(result["unapproved_excluded"], [])

    def test_scope_missing_config_needs_review_blocks(self):
        """Accounts exist but no approved configuration: NEEDS_REVIEW with the
        full unapproved list for display — never an auto-selected scope."""
        result, error, _ = self._run_resolver(
            ["Cash - A2F", "Bank - A2F"], config_raw=None
        )
        self.assertIsNone(error)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["approval"], "MISSING_CONFIG")
        self.assertEqual(result["scope"], [])
        self.assertEqual(result["unapproved_excluded"], ["Bank - A2F", "Cash - A2F"])

    def test_scope_invalid_config_needs_review(self):
        result, error, _ = self._run_resolver(
            ["Cash - A2F"], config_raw="not-json{{"
        )
        self.assertIsNone(error)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["approval"], "INVALID_CONFIG")
        self.assertEqual(result["scope"], [])

    def test_scope_vietnamese_named_account_requires_approval(self):
        """An account named in Vietnamese ('Tiền ký quỹ') enters the scope only
        through the approved configuration; otherwise it is displayed as excluded."""
        leaves = ["Cash - A2F", "Tiền ký quỹ - A2F"]
        result, error, _ = self._run_resolver(leaves, config_raw='["Cash - A2F"]')
        self.assertIsNone(error)
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["scope"], ["Cash - A2F"])
        self.assertEqual(result["unapproved_excluded"], ["Tiền ký quỹ - A2F"])

    def test_scope_stale_config_needs_review(self):
        """Config references an account that no longer exists/is no longer an
        enabled leaf Bank/Cash account: NEEDS_REVIEW, forecast blocked."""
        result, error, _ = self._run_resolver(
            ["Cash - A2F"],
            config_raw='["Cash - A2F", "Tiền ký quỹ - A2F"]',
        )
        self.assertIsNone(error)
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["approval"], "STALE_CONFIG")
        self.assertEqual(result["scope"], [])
        self.assertEqual(result["stale_accounts_count"], 1)

    def test_scope_config_read_error_is_typed(self):
        """The approved configuration cannot be read (e.g. fixture not migrated):
        typed error, not a silently empty scope."""
        result, error, _ = self._run_resolver(
            ["Cash - A2F"], config_raw='["Cash - A2F"]', get_value_exception=True
        )
        self.assertIsNone(result)
        self.assertIsInstance(error, ObligationSourceError)

    def test_scope_requires_db(self):
        with patch("lotus_fin.modules.f002_cashflow.adapters.frappe", None):
            with self.assertRaises(ObligationSourceError):
                resolve_cash_account_scope(COMPANY)

    def test_validation_accepts_matching_approved_scope(self):
        with patch("lotus_fin.modules.f002_cashflow.validation.frappe") as frappe_mock, patch(
            "lotus_fin.modules.f002_cashflow.validation.get_verified_company", return_value=COMPANY
        ), patch(
            "lotus_fin.modules.f002_cashflow.validation.resolve_cash_account_scope",
            return_value={"status": "RESOLVED", "approval": "APPROVED", "scope": ["Cash - A2F"], "unapproved_excluded": []},
        ):
            frappe_mock.db.get_value.return_value = SimpleNamespace(
                name="Cash - A2F",
                company=COMPANY,
                is_group=0,
                disabled=0,
                account_type="Cash",
                account_currency="VND",
            )
            request = make_request(scope=["Cash - A2F"])
            valid, reason, msg = validate_forecast_request(request, user="tester")

        self.assertTrue(valid)
        self.assertIsNone(reason)

    def test_validation_rejects_scope_not_matching_approved(self):
        """The client cannot silently drop approved accounts or add unapproved
        ones: the requested scope must equal the approved scope."""
        with patch("lotus_fin.modules.f002_cashflow.validation.frappe") as frappe_mock, patch(
            "lotus_fin.modules.f002_cashflow.validation.get_verified_company", return_value=COMPANY
        ), patch(
            "lotus_fin.modules.f002_cashflow.validation.resolve_cash_account_scope",
            return_value={"status": "RESOLVED", "approval": "APPROVED", "scope": ["Cash - A2F"], "unapproved_excluded": []},
        ):
            request = make_request(scope=["Cash - A2F", "Ghost - A2F"])
            valid, reason, msg = validate_forecast_request(request, user="tester")

        self.assertFalse(valid)
        self.assertEqual(reason, ReasonCode.DATA_PIPELINE_ERROR)
        self.assertIn("approved scope", msg)

    def test_validation_forbidden_when_account_read_denied(self):
        with patch("lotus_fin.modules.f002_cashflow.validation.frappe"), patch(
            "lotus_fin.modules.f002_cashflow.validation.get_verified_company", return_value=COMPANY
        ), patch(
            "lotus_fin.modules.f002_cashflow.validation.resolve_cash_account_scope",
            side_effect=ObligationPermissionError("Access Denied"),
        ):
            request = make_request()
            valid, reason, msg = validate_forecast_request(request, user="tester")

        self.assertFalse(valid)
        self.assertEqual(reason, ReasonCode.UNAUTHORIZED_ACCESS)
        self.assertEqual(msg, "FORBIDDEN")

    def test_validation_needs_review_when_scope_unapproved(self):
        with patch("lotus_fin.modules.f002_cashflow.validation.frappe"), patch(
            "lotus_fin.modules.f002_cashflow.validation.get_verified_company", return_value=COMPANY
        ), patch(
            "lotus_fin.modules.f002_cashflow.validation.resolve_cash_account_scope",
            return_value={"status": "NEEDS_REVIEW", "approval": "MISSING_CONFIG", "scope": [], "unapproved_excluded": ["Cash - A2F"]},
        ):
            request = make_request()
            valid, reason, msg = validate_forecast_request(request, user="tester")

        self.assertFalse(valid)
        self.assertEqual(reason, ReasonCode.DATA_PIPELINE_ERROR)
        self.assertIn("not configured", msg)


class TestScopeAuthorizationOrdering(unittest.TestCase):
    """Round 4, Fix D: company authorization happens BEFORE any account-scope
    query; authorization failure is generic and never leaks names."""

    def test_permission_failure_blocks_scope_query(self):
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_verified_company",
            side_effect=Exception("FORBIDDEN"),
        ) as verify_mock, patch(
            "lotus_fin.modules.f002_cashflow.service.resolve_cash_account_scope"
        ) as resolve_mock:
            with self.assertRaises(ObligationPermissionError):
                resolve_request_scope("Secret Company", user="tester")

        verify_mock.assert_called_once_with("Secret Company", user="tester")
        resolve_mock.assert_not_called()  # no data queried for an unauthorized company

    def test_scope_resolved_for_verified_company_only(self):
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_verified_company",
            return_value="Verified Company",
        ) as verify_mock, patch(
            "lotus_fin.modules.f002_cashflow.service.resolve_cash_account_scope",
            return_value={"status": "RESOLVED", "approval": "APPROVED", "scope": ["Cash - A2F"], "unapproved_excluded": []},
        ) as resolve_mock:
            res = resolve_request_scope("Requested Company", user="tester")

        verify_mock.assert_called_once_with("Requested Company", user="tester")
        resolve_mock.assert_called_once_with("Verified Company", user="tester")  # resolver sees the VERIFIED name
        self.assertEqual(res["status"], "RESOLVED")
        self.assertEqual(res["scope"], ["Cash - A2F"])

    def test_resolution_failure_is_typed_source_error(self):
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_verified_company",
            return_value="Verified Company",
        ), patch(
            "lotus_fin.modules.f002_cashflow.service.resolve_cash_account_scope",
            side_effect=ObligationSourceError("scope query failed"),
        ):
            with self.assertRaises(ObligationSourceError):
                resolve_request_scope("Requested Company", user="tester")

    def test_scope_permission_failure_not_swallowed(self):
        """Round 5: an Account permission failure inside the resolver keeps its
        typed identity (generic FORBIDDEN upstream) — it is never converted to
        a source error or an empty scope."""
        with patch(
            "lotus_fin.modules.f002_cashflow.service.get_verified_company",
            return_value="Verified Company",
        ), patch(
            "lotus_fin.modules.f002_cashflow.service.resolve_cash_account_scope",
            side_effect=ObligationPermissionError("Access Denied"),
        ):
            with self.assertRaises(ObligationPermissionError):
                resolve_request_scope("Requested Company", user="tester")


if __name__ == "__main__":
    unittest.main()
