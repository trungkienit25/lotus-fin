"""
Regression tests for foundation blockers PB-SEC-01 / PB-DATA-01 / PB-DATA-02
(AI001 surface: authoritative report permission, AR overdue basis, AR/AP
observation identity reconciliation).

Oracle: docs/features/AI003/evidence/final_foundation_probe.py —
- PB-SEC-01: cases PB_SEC_01_ACTIVE_GUARD_DENIED / _CACHE_REVOKED /
  _FRESH_REVOKED / _TRUSTED_EXPLICIT_USER (report-specific authorization via
  Report.is_permitted(), evaluated for the checked user);
- PB-DATA-01: cases AR_BASIS_MISSING_BOTH / AR_BASIS_MALFORMED_DATE /
  AR_BASIS_VALID_EXPLICIT / AR_BASIS_VALID_DATE /
  AR_BASIS_MALFORMED_DATE_VALID_EXPLICIT (missing basis != zero);
- PB-DATA-02: cases *_EXACT_DUPLICATE_AI001 / *_DUPLICATE_AI002_* /
  *_MISSING_IDENTITY_* / *_SIMULATED_TERM_SPLIT_PRESERVED.
"""

import os
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.ai.financial_snapshot import (
    build_financial_snapshot,
    parse_ap_data,
    parse_ar_data,
    FinancialSourceDataError,
)
from lotus_fin.modules.f002_cashflow.cache import _CACHE_STORE, _SINGLE_FLIGHT_LOCKS, compute_cache_key
from lotus_fin.modules.f002_cashflow.models import AccountBalance, ForecastRequest, ForecastStatus, OpeningCash
from lotus_fin.modules.f002_cashflow.service import get_cash_forecast
from lotus_fin.modules.f002_cashflow.source_interface import FailClosedSource
from lotus_fin.security import access as access_module


AS_OF = date(2026, 9, 26)

GOLD_PNL = [
    {"account_name": "Sales Revenue", "balance": 700000.00},
    {"account_name": "Service Income", "balance": 300000.00},
    {"account_name": "Cost of Goods Sold - Materials", "balance": 450000.00},
    {"account_name": "COGS - Direct Labor", "balance": 150000.00},
]
GOLD_TB = [
    {"account_name": "Cash on Hand", "account_type": "Cash", "closing_balance": 50000.00},
]


class _FakePermissionError(Exception):
    pass


def _fake_frappe(permitted=True, session_user="Administrator"):
    fake = MagicMock()
    fake.PermissionError = _FakePermissionError

    def _throw(msg, exc=None, **kwargs):
        raise exc if exc is not None else _FakePermissionError(msg)

    fake.throw.side_effect = _throw
    fake.db.exists.return_value = True
    report_doc = MagicMock()
    report_doc.is_permitted.return_value = permitted
    fake.get_doc.return_value = report_doc
    fake.session.user = session_user
    return fake


class TestPBSEC01AuthoritativeReportPermission(unittest.TestCase):
    """PB-SEC-01: report-specific authorization evaluated for the checked user."""

    def _guard(self, fake, report="Accounts Receivable", user=None):
        with patch("lotus_fin.security.access.frappe", fake):
            return access_module.check_report_permission(report, user=user)

    def test_session_user_denied_by_report_specific_permission(self):
        fake = _fake_frappe(permitted=False, session_user="restricted@x")
        with self.assertRaises(_FakePermissionError):
            self._guard(fake, user="restricted@x")
        fake.get_doc.return_value.is_permitted.assert_called_once()
        fake.set_user.assert_not_called()

    def test_session_user_permitted_passes(self):
        fake = _fake_frappe(permitted=True, session_user="restricted@x")
        self.assertIsNone(self._guard(fake, user="restricted@x"))
        fake.set_user.assert_not_called()

    def test_explicit_user_evaluated_under_target_context_not_session(self):
        """The Administrator session must never authorize on behalf of the
        checked user (probe case PB_SEC_01_TRUSTED_EXPLICIT_USER)."""
        fake = _fake_frappe(permitted=False, session_user="Administrator")
        with self.assertRaises(_FakePermissionError):
            self._guard(fake, user="restricted@x")
        fake.set_user.assert_has_calls([call("restricted@x"), call("Administrator")])
        fake.get_doc.return_value.is_permitted.assert_called_once()

    def test_explicit_user_context_restored_on_permission(self):
        fake = _fake_frappe(permitted=True, session_user="Administrator")
        self.assertIsNone(self._guard(fake, user="restricted@x"))
        fake.set_user.assert_has_calls([call("restricted@x"), call("Administrator")])

    def test_explicit_user_context_restored_on_denial(self):
        fake = _fake_frappe(permitted=False, session_user="Administrator")
        with self.assertRaises(_FakePermissionError):
            self._guard(fake, user="restricted@x")
        fake.set_user.assert_has_calls([call("restricted@x"), call("Administrator")])

    def test_missing_report_fails_closed(self):
        fake = _fake_frappe(permitted=True)
        fake.db.exists.return_value = False
        with self.assertRaises(_FakePermissionError):
            self._guard(fake, user="u@x")

    def test_allowlist_gate_denies_unknown_report_before_report_lookup(self):
        fake = _fake_frappe(permitted=True)
        with patch("lotus_fin.security.access.frappe", fake):
            with self.assertRaises(_FakePermissionError):
                access_module.check_ai002_report_permission("Secret Report", user="u@x")
        fake.get_doc.assert_not_called()

    def test_allowlisted_report_still_goes_through_authoritative_check(self):
        fake = _fake_frappe(permitted=False, session_user="u@x")
        with patch("lotus_fin.security.access.frappe", fake):
            with self.assertRaises(_FakePermissionError):
                access_module.check_ai002_report_permission("Accounts Receivable", user="u@x")

    def test_frappe_absent_fails_closed(self):
        with patch("lotus_fin.security.access.frappe", None):
            with self.assertRaises(access_module._PermissionError):
                access_module.check_report_permission("Accounts Receivable", user="u@x")


def _row_with_basis(updates):
    """A positive AR transaction row stripped of every overdue basis field,
    then re-fed with the variant under test (mirrors the probe's basis cases)."""
    row = {"party": "Cust A", "voucher_no": "SINV-0001", "outstanding": 100.0}
    for key in ("due_date", "overdue", "overdue_amount"):
        row.pop(key, None)
    row.update(updates)
    return [row]


class TestPBDATA01OverdueBasis(unittest.TestCase):
    """PB-DATA-01: missing/malformed overdue basis -> typed inconclusive,
    never a fabricated zero; a valid total stays available independently."""

    def test_missing_basis_overdue_unavailable_total_available(self):
        total, overdue, ratio, lims = parse_ar_data(_row_with_basis({}), as_of_date=AS_OF)
        self.assertEqual(total, Decimal("100.00"))
        self.assertIsNone(overdue)
        self.assertIsNone(ratio)
        self.assertTrue(any("inconclusive" in lim for lim in lims))

    def test_malformed_date_overdue_unavailable(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": "not-a-date"}), as_of_date=AS_OF
        )
        self.assertEqual(total, Decimal("100.00"))
        self.assertIsNone(overdue)
        self.assertIsNone(ratio)

    def test_due_date_as_string_counts_full_outstanding(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": "2026-09-01"}), as_of_date=AS_OF
        )
        self.assertEqual(
            (total, overdue, ratio, lims),
            (Decimal("100.00"), Decimal("100.00"), Decimal("1.0000"), []),
        )

    def test_due_date_as_date_object_counts_full_outstanding(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": date(2026, 9, 1)}), as_of_date=AS_OF
        )
        self.assertEqual(
            (total, overdue, ratio, lims),
            (Decimal("100.00"), Decimal("100.00"), Decimal("1.0000"), []),
        )

    def test_due_date_as_datetime_object_counts_full_outstanding(self):
        """PB-DATA-01-DATETIME: a datetime due_date must be normalized to a
        date before the as-of comparison — no TypeError, overdue verified."""
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": datetime(2026, 9, 1)}), as_of_date=AS_OF
        )
        self.assertEqual(
            (total, overdue, ratio, lims),
            (Decimal("100.00"), Decimal("100.00"), Decimal("1.0000"), []),
        )

    def test_datetime_due_date_oracle_retest_repro(self):
        """Exact independent-retest repro: datetime(2026, 9, 20) against
        as_of date(2026, 9, 26) — previously TypeError, now verified overdue."""
        total, overdue, ratio, lims = parse_ar_data(
            [{"voucher_no": "SI-RETEST", "outstanding": 100, "due_date": datetime(2026, 9, 20)}],
            as_of_date=date(2026, 9, 26),
        )
        self.assertEqual(
            (total, overdue, ratio, lims),
            (Decimal("100.00"), Decimal("100.00"), Decimal("1.0000"), []),
        )

    def test_datetime_due_date_after_as_of_not_overdue(self):
        total, overdue, ratio, lims = parse_ar_data(
            [{"voucher_no": "SI-RETEST", "outstanding": 100, "due_date": datetime(2026, 9, 27)}],
            as_of_date=date(2026, 9, 26),
        )
        self.assertEqual(
            (total, overdue, ratio, lims),
            (Decimal("100.00"), Decimal("0.00"), Decimal("0.0000"), []),
        )

    def test_snapshot_with_datetime_due_date_does_not_leak_typeerror(self):
        """Public snapshot: a datetime due_date must not leak a TypeError and
        must verify overdue (total 100, ratio 1.0, overall OK)."""
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources={
                "profit_and_loss": {"status": "success", "data": GOLD_PNL},
                "trial_balance": {"status": "success", "data": GOLD_TB},
                "accounts_receivable": {
                    "status": "success",
                    "data": [
                        {
                            "party": "A",
                            "voucher_no": "SI-RETEST",
                            "outstanding": 100.0,
                            "due_date": datetime(2026, 9, 20),
                        }
                    ],
                },
                "accounts_payable": {"status": "success", "data": []},
            },
        )
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ar_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics["ar_outstanding"]["value"], 100.0)
        self.assertEqual(metrics["overdue_ar_ratio"]["status"], "AVAILABLE")
        self.assertEqual(metrics["overdue_ar_ratio"]["value"], 1.0)
        self.assertEqual(snapshot["status"], "OK")

    def test_valid_explicit_overdue_amount(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"overdue_amount": 100.0}), as_of_date=AS_OF
        )
        self.assertEqual(total, Decimal("100.00"))
        self.assertEqual(overdue, Decimal("100.00"))
        self.assertEqual(ratio, Decimal("1.0000"))

    def test_malformed_date_with_explicit_basis_uses_explicit(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": "not-a-date", "overdue_amount": 40.0}), as_of_date=AS_OF
        )
        self.assertEqual(total, Decimal("100.00"))
        self.assertEqual(overdue, Decimal("40.00"))

    def test_valid_past_due_date_counts_full_outstanding(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": "2026-09-01"}), as_of_date=AS_OF
        )
        self.assertEqual(overdue, Decimal("100.00"))

    def test_due_exact_is_not_overdue(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": "2026-09-26"}), as_of_date=AS_OF
        )
        self.assertEqual(overdue, Decimal("0.00"))
        self.assertEqual(ratio, Decimal("0.0000"))

    def test_future_due_date_not_overdue(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"due_date": "2026-12-31"}), as_of_date=AS_OF
        )
        self.assertEqual(overdue, Decimal("0.00"))

    def test_malformed_explicit_overdue_is_unknown_basis(self):
        total, overdue, ratio, lims = parse_ar_data(
            _row_with_basis({"overdue_amount": "not-a-number"}), as_of_date=AS_OF
        )
        self.assertEqual(total, Decimal("100.00"))
        self.assertIsNone(overdue)
        self.assertIsNone(ratio)

    def test_credit_rows_with_dates_keep_net_gold(self):
        """Net formula unchanged: 75,000 past-due + (10,000) credit past-due
        + 200,000 due-exact -> 65,000 overdue (the live gold shape)."""
        rows = [
            {"party": "A", "voucher_no": "SINV-0001", "outstanding": 75000.0, "due_date": "2026-09-01"},
            {"party": "B", "voucher_no": "SINV-0002", "outstanding": 200000.0, "due_date": "2026-09-26"},
            {"party": "C", "voucher_no": "SINV-0003", "outstanding": -10000.0, "due_date": "2026-09-01"},
        ]
        total, overdue, ratio, lims = parse_ar_data(rows, as_of_date=AS_OF)
        self.assertEqual(total, Decimal("265000.00"))
        self.assertEqual(overdue, Decimal("65000.00"))
        self.assertEqual(ratio, Decimal("0.2453"))

    def test_zero_outstanding_without_basis_does_not_poison(self):
        rows = [
            {"party": "Z", "voucher_no": "SINV-0009", "outstanding": 0.0},
            {"party": "A", "voucher_no": "SINV-0001", "outstanding": 100.0, "due_date": "2026-09-01"},
        ]
        total, overdue, ratio, lims = parse_ar_data(rows, as_of_date=AS_OF)
        self.assertEqual(total, Decimal("100.00"))
        self.assertEqual(overdue, Decimal("100.00"))
        self.assertEqual(ratio, Decimal("1.0000"))

    def test_empty_list_is_verified_zero(self):
        total, overdue, ratio, lims = parse_ar_data([], as_of_date=AS_OF)
        self.assertEqual((total, overdue, ratio), (Decimal("0.00"), Decimal("0.00"), Decimal("0.00")))

    def test_snapshot_level_total_available_ratio_unavailable(self):
        """Contract level: missing != zero — ar_outstanding stays AVAILABLE
        while overdue_ar_ratio becomes UNAVAILABLE, never a fabricated ratio."""
        snapshot = build_financial_snapshot(
            company="Name (Demo)",
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources={
                "profit_and_loss": {"status": "success", "data": GOLD_PNL},
                "trial_balance": {"status": "success", "data": GOLD_TB},
                "accounts_receivable": {
                    "status": "success",
                    "data": [{"party": "A", "voucher_no": "SINV-0001", "outstanding": 100.0}],
                },
                "accounts_payable": {"status": "success", "data": []},
            },
        )
        metrics = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics["ar_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics["ar_outstanding"]["value"], 100.0)
        self.assertEqual(metrics["overdue_ar_ratio"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics["overdue_ar_ratio"]["value"])
        self.assertEqual(snapshot["status"], "PARTIAL")


class TestPBDATA02ObservationIdentityAI001(unittest.TestCase):
    """PB-DATA-02: exact duplicates count once; conflicting contents fail
    closed; legitimate payment-term/account allocations remain distinct."""

    def test_ar_exact_duplicate_deduplicated_not_double_counted(self):
        row = {"party": "A", "voucher_no": "SINV-0001", "outstanding": 100.0, "due_date": "2026-09-01"}
        total, overdue, ratio, lims = parse_ar_data([row, dict(row)], as_of_date=AS_OF)
        self.assertEqual(total, Decimal("100.00"))
        self.assertTrue(any("deduplicated" in lim for lim in lims))

    def test_ar_conflicting_duplicate_fails_closed(self):
        row = {"party": "A", "voucher_no": "SINV-0001", "outstanding": 100.0, "due_date": "2026-09-01"}
        conflict = dict(row)
        conflict["outstanding"] = 101.0
        with self.assertRaises(FinancialSourceDataError):
            parse_ar_data([row, conflict], as_of_date=AS_OF)

    def test_ar_payment_term_split_remains_distinct_and_reconciles(self):
        row = {"party": "A", "voucher_no": "SINV-0001", "outstanding": 100.0, "due_date": "2026-09-01"}
        first = dict(row)
        first["outstanding"] = 60.0
        first["payment_term"] = "TERM-A"
        second = dict(row)
        second["outstanding"] = 40.0
        second["payment_term"] = "TERM-B"
        total, overdue, ratio, lims = parse_ar_data([first, second], as_of_date=AS_OF)
        self.assertEqual(total, Decimal("100.00"))
        self.assertEqual(overdue, Decimal("100.00"))

    def test_ap_exact_duplicate_deduplicated(self):
        row = {"party": "S", "voucher_no": "PINV-0001", "outstanding": 250.0, "due_date": "2026-11-15"}
        total, lims = parse_ap_data([row, dict(row)])
        self.assertEqual(total, Decimal("250.00"))
        self.assertTrue(any("deduplicated" in lim for lim in lims))

    def test_ap_conflicting_duplicate_fails_closed(self):
        row = {"party": "S", "voucher_no": "PINV-0001", "outstanding": 250.0, "due_date": "2026-11-15"}
        conflict = dict(row)
        conflict["outstanding"] = 251.0
        with self.assertRaises(FinancialSourceDataError):
            parse_ap_data([row, conflict])

    def test_ap_account_allocation_remains_distinct(self):
        row = {"party": "S", "voucher_no": "PINV-0001", "outstanding": 250.0, "due_date": "2026-11-15"}
        first = dict(row)
        first["outstanding"] = 150.0
        first["party_account"] = "Accounts Payable - A"
        second = dict(row)
        second["outstanding"] = 100.0
        second["party_account"] = "Accounts Payable - B"
        total, lims = parse_ap_data([first, second])
        self.assertEqual(total, Decimal("250.00"))

    def test_ap_amount_conflict_with_distinct_accounts_is_allocation(self):
        """Same voucher, different account AND amount -> legitimate account
        allocation, stays distinct (sum preserved)."""
        row = {"party": "S", "voucher_no": "PINV-0001", "outstanding": 250.0, "due_date": "2026-11-15"}
        first = dict(row)
        first["outstanding"] = 150.0
        first["party_account"] = "Accounts Payable - A"
        second = dict(row)
        second["outstanding"] = 100.0
        second["party_account"] = "Accounts Payable - B"
        total, lims = parse_ap_data([first, second])
        self.assertEqual(total, Decimal("250.00"))


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


def _forecast_request():
    return ForecastRequest(
        company="AI002 Fixture 2026",
        financial_as_of=AS_OF,
        forecast_start=date(2026, 9, 27),
        forecast_end=date(2026, 10, 26),
        reporting_currency="VND",
        cash_account_scope=["Cash - A2F"],
    )


class TestPBSEC01CacheTTLRevokeRegrant(unittest.TestCase):
    """PB-SEC-01 end-to-end through the REAL authoritative guard: report
    permission revocation inside the cache TTL must yield a generic FORBIDDEN
    with no financial payload and evict the stale entry; regranting restores
    authorized behavior (probe cases PB_SEC_01_CACHE_REVOKED / REGRANT)."""

    def setUp(self):
        _CACHE_STORE.clear()
        _SINGLE_FLIGHT_LOCKS.clear()

    def test_revoked_report_permission_forbidden_evicted_regrant_restores(self):
        fake_access = _fake_frappe(permitted=True, session_user="perm-user@example.com")
        ctx = (
            patch(
                "lotus_fin.modules.f002_cashflow.service.validate_forecast_request",
                return_value=(True, None, None),
            ),
            patch(
                "lotus_fin.modules.f002_cashflow.service.get_opening_cash_ledger",
                MagicMock(return_value=_verified_opening()),
            ),
            patch(
                "lotus_fin.modules.f002_cashflow.service.get_trade_obligations",
                MagicMock(return_value=[]),
            ),
            patch("lotus_fin.modules.f002_cashflow.service.frappe", MagicMock()),
            patch("lotus_fin.security.access.frappe", fake_access),
        )

        def _run():
            return get_cash_forecast(
                request=_forecast_request(),
                user="perm-user@example.com",
                future_event_source=FailClosedSource(),
            )

        with ctx[0], ctx[1], ctx[2], ctx[3], ctx[4]:
            # 1. authorized call computes and populates the cache
            first = _run()
            self.assertEqual(first.status, ForecastStatus.FORECAST_UNAVAILABLE)
            self.assertIsNotNone(first.opening_cash)

            # 2. identical repeat is served from the cache (same forecast id)
            second = _run()
            self.assertEqual(second.forecast_id, first.forecast_id)

            # 3. report permission revoked inside the TTL: cached call must be
            #    a generic FORBIDDEN with no financial payload
            fake_access.get_doc.return_value.is_permitted.return_value = False
            revoked = _run()
            self.assertEqual(revoked.status, ForecastStatus.FORBIDDEN)
            self.assertIsNone(revoked.opening_cash)
            self.assertEqual(revoked.obligations, [])
            self.assertEqual(revoked.forecast_points, [])

            # 4. the stale authorized entry was evicted
            key = compute_cache_key(
                user_id="perm-user@example.com",
                company="AI002 Fixture 2026",
                as_of=AS_OF,
                forecast_start=date(2026, 9, 27),
                forecast_end=date(2026, 10, 26),
                account_scope=["Cash - A2F"],
                coverage_scope="TRADE_ONLY",
            )
            self.assertNotIn(key, _CACHE_STORE)

            # 5. regrant restores authorized behavior
            fake_access.get_doc.return_value.is_permitted.return_value = True
            restored = _run()
            self.assertNotEqual(restored.status, ForecastStatus.FORBIDDEN)
            self.assertEqual(restored.status, ForecastStatus.FORECAST_UNAVAILABLE)
            self.assertIsNotNone(restored.opening_cash)


if __name__ == "__main__":
    unittest.main()
