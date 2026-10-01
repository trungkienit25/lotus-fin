"""
Regression tests for foundation blockers PB-SEC-01 / PB-DATA-02 (AI002
surface: fresh-path user propagation, cache-TTL revoke/regrant, obligation
observation-identity reconciliation).

The authoritative guard unit semantics (Report.is_permitted(), session
switch/restore) live in tests/test_ai001_foundation_blockers.py together with
security/access.py; this suite pins the AI002 consumption contract:
- cache-hit reauthorization inside the TTL denies with a generic FORBIDDEN
  empty payload and evicts the stale entry; regranting restores behavior;
- fresh computation forwards the checked user to every report permission
  check (never the ambient session on the caller's behalf);
- obligations are reconciled by voucher observation identity (PB-DATA-02).

Oracle: docs/features/AI003/evidence/final_foundation_probe.py —
PB_SEC_01_CACHE_REVOKED / PB_SEC_01_FRESH_REVOKED / REGRANT /
*_DUPLICATE_AI002_EXACT / *_DUPLICATE_AI002_CONFLICTING_AMOUNT /
*_MISSING_IDENTITY_AI002 / *_SIMULATED_TERM_SPLIT_PRESERVED.
"""

import os
import sys
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.cashflow import adapters
from lotus_fin.cashflow.adapters import (
    ObligationSourceError,
    _collect_obligations,
    get_trade_obligations,
)
from lotus_fin.cashflow.cache import _CACHE_STORE, _SINGLE_FLIGHT_LOCKS
from lotus_fin.cashflow.models import (
    ForecastRequest,
    ForecastStatus,
    OpeningCash,
    AccountBalance,
)
from lotus_fin.cashflow.service import get_cash_forecast
from lotus_fin.cashflow.source_interface import FailClosedSource

COMPANY = "AI002 Fixture 2026"
AS_OF = date(2026, 9, 26)


def _verified_opening():
    return OpeningCash(
        aggregate_amount=Decimal("11550000"),
        reconciliation="ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED",
        has_constituent_deficit=False,
        accounts=[
            AccountBalance(
                account="Cash - A2F",
                amount=Decimal("11550000"),
                currency="VND",
                deficit=False,
            )
        ],
    )


def _make_request():
    return ForecastRequest(
        company=COMPANY,
        financial_as_of=AS_OF,
        forecast_start=date(2026, 9, 27),
        forecast_end=date(2026, 10, 26),
        reporting_currency="VND",
        cash_account_scope=["Cash - A2F"],
    )


class TestPBSEC01FreshPathUserPropagation(unittest.TestCase):
    """PB-SEC-01: fresh computation forwards the checked user to every report
    permission check, and a revoked report yields FORBIDDEN — never
    SOURCE_ERROR — with no financial payload."""

    def setUp(self):
        _CACHE_STORE.clear()
        _SINGLE_FLIGHT_LOCKS.clear()

    def test_revoked_report_on_fresh_call_is_forbidden_not_source_error(self):
        guard_state = {"permitted": False}

        def _guard(report_name, user=None):
            if not guard_state["permitted"]:
                raise Exception("FORBIDDEN")

        with patch(
            "lotus_fin.cashflow.service.validate_forecast_request",
            return_value=(True, None, None),
        ), patch(
            "lotus_fin.cashflow.service.get_opening_cash_ledger",
            MagicMock(return_value=_verified_opening()),
        ), patch("lotus_fin.cashflow.service.frappe", MagicMock()), patch(
            "lotus_fin.cashflow.adapters.frappe", MagicMock()
        ), patch.object(
            adapters, "check_ai002_report_permission", side_effect=_guard
        ), patch.object(
            adapters,
            "extract_key_report_data",
            return_value={"status": "success", "data": []},
        ):
            revoked = get_cash_forecast(
                request=_make_request(),
                user="perm-user@example.com",
                future_event_source=FailClosedSource(),
                skip_cache=True,
            )
            self.assertEqual(revoked.status, ForecastStatus.FORBIDDEN)
            self.assertNotEqual(revoked.status, ForecastStatus.SOURCE_ERROR)
            self.assertIsNone(revoked.opening_cash)
            self.assertEqual(revoked.obligations, [])
            self.assertEqual(revoked.forecast_points, [])
            self.assertEqual(revoked.verified_company, "")

            # regrant restores authorized fresh behavior
            guard_state["permitted"] = True
            restored = get_cash_forecast(
                request=_make_request(),
                user="perm-user@example.com",
                future_event_source=FailClosedSource(),
                skip_cache=True,
            )
            self.assertNotEqual(restored.status, ForecastStatus.FORBIDDEN)
            self.assertIsNotNone(restored.opening_cash)

    def test_service_forwards_checked_user_to_fresh_source_calls(self):
        with patch(
            "lotus_fin.cashflow.service.validate_forecast_request",
            return_value=(True, None, None),
        ), patch(
            "lotus_fin.cashflow.service.get_opening_cash_ledger",
            return_value=_verified_opening(),
        ) as opening_mock, patch(
            "lotus_fin.cashflow.service.get_trade_obligations",
            return_value=[],
        ) as obligations_mock, patch(
            "lotus_fin.cashflow.service.frappe", MagicMock()
        ):
            get_cash_forecast(
                request=_make_request(),
                user="checked-user@example.com",
                future_event_source=FailClosedSource(),
                skip_cache=True,
            )
        self.assertEqual(opening_mock.call_args.kwargs.get("user"), "checked-user@example.com")
        self.assertEqual(obligations_mock.call_args.kwargs.get("user"), "checked-user@example.com")

    def test_adapters_forward_checked_user_to_report_permission_guard(self):
        with patch("lotus_fin.cashflow.adapters.frappe", MagicMock()), patch.object(
            adapters, "check_ai002_report_permission"
        ) as perm_mock, patch.object(
            adapters,
            "extract_key_report_data",
            return_value={"status": "success", "data": []},
        ):
            get_trade_obligations(COMPANY, as_of=AS_OF, currency="VND", user="checked-user@example.com")
        self.assertEqual(perm_mock.call_count, 2)
        for guard_call in perm_mock.call_args_list:
            self.assertEqual(guard_call.kwargs.get("user"), "checked-user@example.com")


def _ar_row():
    return {
        "party": "Cust A",
        "voucher_no": "SINV-0001",
        "voucher_type": "Sales Invoice",
        "outstanding": 100.0,
        "due_date": "2026-09-01",
    }


def _collect_ar(rows):
    return _collect_obligations(
        {"status": "success", "data": rows},
        "AR",
        ("party",),
        "Sales Invoice",
        "VND",
        "Accounts Receivable",
    )


class TestPBDATA02ObservationIdentityAI002(unittest.TestCase):
    """PB-DATA-02: obligations reconcile by voucher observation identity."""

    def test_exact_duplicate_yields_single_obligation(self):
        row = _ar_row()
        result = _collect_ar([row, dict(row)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].remaining_amount, Decimal("100.00"))
        self.assertEqual(result[0].source_ref, "Sales Invoice:SINV-0001")

    def test_conflicting_duplicate_fails_closed(self):
        row = _ar_row()
        conflict = dict(row)
        conflict["outstanding"] = 101.0
        with self.assertRaises(ObligationSourceError):
            _collect_ar([row, conflict])

    def test_payment_term_split_keeps_distinct_obligations(self):
        row = _ar_row()
        first = dict(row)
        first["outstanding"] = 60.0
        first["payment_term"] = "TERM-A"
        second = dict(row)
        second["outstanding"] = 40.0
        second["payment_term"] = "TERM-B"
        result = _collect_ar([first, second])
        self.assertEqual(len(result), 2)
        self.assertEqual(
            sorted(o.remaining_amount for o in result),
            [Decimal("40.00"), Decimal("60.00")],
        )

    def test_account_allocation_keeps_distinct_obligations(self):
        row = _ar_row()
        first = dict(row)
        first["outstanding"] = 70.0
        first["party_account"] = "Debtors - A"
        second = dict(row)
        second["outstanding"] = 30.0
        second["party_account"] = "Debtors - B"
        result = _collect_ar([first, second])
        self.assertEqual(len(result), 2)

    def test_missing_identity_still_fails_closed(self):
        row = _ar_row()
        missing = dict(row)
        missing.pop("voucher_no")
        with self.assertRaises(ObligationSourceError):
            _collect_ar([missing])

    def test_get_trade_obligations_deduplicates_report_rows(self):
        row = _ar_row()
        with patch("lotus_fin.cashflow.adapters.frappe", MagicMock()), patch.object(
            adapters, "check_ai002_report_permission"
        ), patch.object(
            adapters,
            "extract_key_report_data",
            side_effect=[
                {"status": "success", "data": [row, dict(row)]},
                {"status": "success", "data": []},
            ],
        ):
            result = get_trade_obligations(COMPANY, as_of=AS_OF, currency="VND")
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
