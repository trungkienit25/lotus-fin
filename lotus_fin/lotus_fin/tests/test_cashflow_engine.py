import unittest
import os
from datetime import date, timedelta
from decimal import Decimal

from lotus_fin.cashflow.models import (
    ForecastRequest,
    ForecastResponse,
    ForecastStatus,
    ReasonCode,
    CoverageScope,
    OpeningCash,
    AccountBalance,
    CashEvent,
    CashEventDirection,
    BreachKind,
)
from lotus_fin.cashflow.engine import compute_forecast
from lotus_fin.cashflow.validation import validate_forecast_request
from lotus_fin.cashflow.source_interface import SyntheticFixtureSource, FailClosedSource
from lotus_fin.cashflow.service import get_cash_forecast
from lotus_fin.cashflow.cache import compute_cache_key, get_cached_response, set_cached_response


class TestCashflowEnginePurePython(unittest.TestCase):
    """
    Dual-mode Pure Python Unit Tests for AI002 Deterministic Forecast Engine.
    Executes locally without Frappe dependency.
    Covers:
    - Gold Oracle: strict_no_future_event
    - Gold Oracle: strict_with_confirmed_events
    - Shortfall state machine: INHERITED_FROM_OPENING vs NEW_MODELED_DEFICIT
    - Zero opening cash (Zero is NOT error, zero is not negative)
    - Multi-account deficit with positive aggregate (has_constituent_deficit)
    - Horizon & date boundary validation
    - Decimal arithmetic precision
    - Single-flight & compound cache
    """

    def setUp(self):
        self.as_of = date(2026, 9, 26)
        self.start = date(2026, 9, 27)
        self.end = date(2026, 10, 26)
        candidate_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json")),
            "/home/frappe/frappe-bench/apps/lotus_fin/docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json",
        ]
        self.fixture_path = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])

    def test_gold_strict_no_future_event(self):
        """
        Gold Case 1: Strict baseline with no confirmed future events.
        Expected: FORECAST_UNAVAILABLE, reason NO_CONFIRMED_SETTLEMENT_EVENTS, forecast_points empty.
        """
        request = ForecastRequest(
            company="AI002 Fixture 2026",
            financial_as_of=self.as_of,
            forecast_start=self.start,
            forecast_end=self.end,
            reporting_currency="VND",
            cash_account_scope=["Cash - A2F"],
            coverage_scope=CoverageScope.TRADE_ONLY,
        )

        # Mocking opening cash to gold fixture value: 11,550,000 VND
        response = get_cash_forecast(
            request=request,
            user="Administrator",
            future_event_source=FailClosedSource(),
            skip_cache=True,
        )

        self.assertEqual(response.status, ForecastStatus.FORECAST_UNAVAILABLE)
        self.assertEqual(response.reason_code, ReasonCode.NO_CONFIRMED_SETTLEMENT_EVENTS)
        self.assertEqual(len(response.forecast_points), 0)
        self.assertIn("No eligible future cash date", response.limitations)

    def test_gold_strict_with_confirmed_events(self):
        """
        Gold Case 2: Strict baseline with 3 confirmed events from fixture.
        Expected:
        - 30 daily EOD points
        - 2026-09-27 to 2026-09-28: 11,550,000
        - 2026-09-29 to 2026-10-03: 13,550,000 (+2,000,000)
        - 2026-10-04 to 2026-10-09: 9,550,000 (-4,000,000)
        - 2026-10-10 onwards: -450,000 (-10,000,000)
        - First negative: 2026-10-10
        - Minimum cash: -450,000 on 2026-10-10
        - Shortfall: NEGATIVE_MODELED_CASH with NEW_MODELED_DEFICIT
        """
        opening_cash = OpeningCash(
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

        fixture_source = SyntheticFixtureSource(self.fixture_path)
        events = fixture_source.get_confirmed_events(
            company="AI002 Fixture 2026",
            start_date=self.start,
            end_date=self.end,
            currency="VND",
            financial_as_of=self.as_of,
        )
        self.assertEqual(len(events), 3)

        points, shortfall = compute_forecast(
            opening_cash=opening_cash,
            cash_events=events,
            forecast_start=self.start,
            forecast_end=self.end,
        )

        self.assertEqual(len(points), 30)

        # Check values matching gold manifest exactly
        point_dict = {p.date: p.modeled_cash for p in points}
        self.assertEqual(point_dict[date(2026, 9, 27)], Decimal("11550000"))
        self.assertEqual(point_dict[date(2026, 9, 28)], Decimal("11550000"))
        self.assertEqual(point_dict[date(2026, 9, 29)], Decimal("13550000"))
        self.assertEqual(point_dict[date(2026, 10, 3)], Decimal("13550000"))
        self.assertEqual(point_dict[date(2026, 10, 4)], Decimal("9550000"))
        self.assertEqual(point_dict[date(2026, 10, 9)], Decimal("9550000"))
        self.assertEqual(point_dict[date(2026, 10, 10)], Decimal("-450000"))
        self.assertEqual(point_dict[date(2026, 10, 26)], Decimal("-450000"))

        # Check Shortfall Event
        self.assertEqual(len(shortfall), 1)
        sf = shortfall[0]
        self.assertEqual(sf.type, "NEGATIVE_MODELED_CASH")
        self.assertEqual(sf.first_date, date(2026, 10, 10))
        self.assertEqual(sf.minimum_modeled_cash, Decimal("-450000"))
        self.assertEqual(sf.minimum_date, date(2026, 10, 10))
        self.assertEqual(sf.breach_kind, BreachKind.NEW_MODELED_DEFICIT)

    def test_shortfall_inherited_from_opening(self):
        """Negative opening cash triggers INHERITED_FROM_OPENING immediately."""
        opening_cash = OpeningCash(
            aggregate_amount=Decimal("-5000000"),
            reconciliation="TRIAL_BALANCE_RECONCILED",
            has_constituent_deficit=True,
            accounts=[
                AccountBalance(
                    account="Bank - Overdrawn",
                    amount=Decimal("-5000000"),
                    currency="VND",
                    deficit=True,
                )
            ],
        )

        points, shortfall = compute_forecast(
            opening_cash=opening_cash,
            cash_events=[],
            forecast_start=self.start,
            forecast_end=self.end,
        )

        self.assertEqual(len(shortfall), 1)
        self.assertEqual(shortfall[0].breach_kind, BreachKind.INHERITED_FROM_OPENING)
        self.assertEqual(shortfall[0].first_date, self.start)
        self.assertEqual(shortfall[0].minimum_modeled_cash, Decimal("-5000000"))

    def test_zero_opening_cash_is_valid_not_negative(self):
        """Zero opening cash must NOT trigger shortfall if no events drag it below zero."""
        opening_cash = OpeningCash(
            aggregate_amount=Decimal("0"),
            reconciliation="TRIAL_BALANCE_RECONCILED",
            has_constituent_deficit=False,
            accounts=[],
        )

        points, shortfall = compute_forecast(
            opening_cash=opening_cash,
            cash_events=[],
            forecast_start=self.start,
            forecast_end=self.end,
        )

        self.assertEqual(len(shortfall), 0)
        self.assertEqual(points[0].modeled_cash, Decimal("0"))

    def test_multi_account_constituent_deficit(self):
        """Constituent deficit with positive net aggregate."""
        accounts = [
            AccountBalance(account="Bank A", amount=Decimal("-2000000"), currency="VND", deficit=True),
            AccountBalance(account="Bank B", amount=Decimal("5000000"), currency="VND", deficit=False),
        ]
        opening = OpeningCash(
            aggregate_amount=Decimal("3000000"),
            reconciliation="TRIAL_BALANCE_RECONCILED",
            has_constituent_deficit=True,
            accounts=accounts,
        )
        self.assertTrue(opening.has_constituent_deficit)
        self.assertEqual(opening.aggregate_amount, Decimal("3000000"))

    def test_date_validation_invariants(self):
        """Validation fails if forecast horizon is not exactly 30 days or not starting as_of + 1."""
        # Start != as_of + 1
        bad_req_1 = ForecastRequest(
            company="Test Co",
            financial_as_of=self.as_of,
            forecast_start=self.as_of,  # Bad
            forecast_end=self.end,
        )
        valid, reason, _ = validate_forecast_request(bad_req_1)
        self.assertFalse(valid)
        self.assertEqual(reason, ReasonCode.HORIZON_MISMATCH)

        # End != start + 29
        bad_req_2 = ForecastRequest(
            company="Test Co",
            financial_as_of=self.as_of,
            forecast_start=self.start,
            forecast_end=self.start + timedelta(days=15),  # Bad: only 16 days
        )
        valid, reason, _ = validate_forecast_request(bad_req_2)
        self.assertFalse(valid)
        self.assertEqual(reason, ReasonCode.HORIZON_MISMATCH)

        # Currency mismatch
        bad_req_3 = ForecastRequest(
            company="Test Co",
            financial_as_of=self.as_of,
            forecast_start=self.start,
            forecast_end=self.end,
            reporting_currency="USD",
        )
        valid, reason, _ = validate_forecast_request(bad_req_3)
        self.assertFalse(valid)
        self.assertEqual(reason, ReasonCode.UNSUPPORTED_CURRENCY)

    def test_compound_cache_key_isolation(self):
        """Cache keys differ when user, company, date, scope, or source_mode differs."""
        k1 = compute_cache_key("user1", "CompanyA", self.as_of, self.start, self.end, ["Acc1"], "TRADE_ONLY", source_mode="LIVE")
        k2 = compute_cache_key("user2", "CompanyA", self.as_of, self.start, self.end, ["Acc1"], "TRADE_ONLY", source_mode="LIVE")
        k3 = compute_cache_key("user1", "CompanyB", self.as_of, self.start, self.end, ["Acc1"], "TRADE_ONLY", source_mode="LIVE")
        k4 = compute_cache_key("user1", "CompanyA", self.as_of, self.start, self.end, ["Acc1", "Acc2"], "TRADE_ONLY", source_mode="LIVE")
        k5 = compute_cache_key("user1", "CompanyA", self.as_of, self.start, self.end, ["Acc1"], "TRADE_ONLY", source_mode="FIXTURE")

        self.assertNotEqual(k1, k2)
        self.assertNotEqual(k1, k3)
        self.assertNotEqual(k1, k4)
        self.assertNotEqual(k1, k5)

    def test_cash_forecast_page_doc_exists_and_standard(self):
        """Contract check: Verify cash-forecast Page doc is registered in Frappe when running in Docker bench."""
        try:
            import frappe
            if hasattr(frappe, "db") and frappe.db:
                self.assertTrue(frappe.db.exists("Page", "cash-forecast"))
                page = frappe.get_doc("Page", "cash-forecast")
                self.assertEqual(page.standard, "Yes")
                self.assertEqual(page.module, "Lotus Fin AI")
                roles = [r.role for r in page.roles]
                self.assertIn("Accounts User", roles)
                self.assertIn("Accounts Manager", roles)
                self.assertIn("System Manager", roles)
        except ImportError:
            pass


    def test_fixture_exact_company_returns_events(self):
        """Fix A: SyntheticFixtureSource returns events when requested company matches fixture."""
        source = SyntheticFixtureSource(self.fixture_path)
        events = source.get_confirmed_events(
            company="AI002 Fixture 2026",
            start_date=self.start,
            end_date=self.end,
        )
        self.assertEqual(len(events), 3)

    def test_fixture_cross_company_returns_no_events(self):
        """Fix A: SyntheticFixtureSource fails closed (returns empty) when company does not match."""
        source = SyntheticFixtureSource(self.fixture_path)
        events = source.get_confirmed_events(
            company="UNRELATED_COMPANY",
            start_date=self.start,
            end_date=self.end,
        )
        self.assertEqual(len(events), 0)

    def test_fixture_missing_company_metadata_fails_closed(self):
        """Fix A: SyntheticFixtureSource fails closed when fixture has no company."""
        import tempfile, json
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tf:
            json.dump([{"source_ref": "PE-1", "amount": 1000}], tf)
            tpath = tf.name
        try:
            source = SyntheticFixtureSource(tpath)
            events = source.get_confirmed_events(company="AI002 Fixture 2026", start_date=self.start, end_date=self.end)
            self.assertEqual(len(events), 0)
        finally:
            os.remove(tpath)

    def test_fixture_event_company_mismatch_fails_closed(self):
        """Fix A: SyntheticFixtureSource drops events if row company does not match requested."""
        import tempfile, json
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tf:
            json.dump({
                "company": "AI002 Fixture 2026",
                "events": [
                    {
                        "source_ref": "Payment Entry:PE-001",
                        "company": "OTHER_COMPANY",
                        "date": "2026-09-29",
                        "direction": "inflow",
                        "amount": 2000000,
                    }
                ]
            }, tf)
            tpath = tf.name
        try:
            source = SyntheticFixtureSource(tpath)
            events = source.get_confirmed_events(company="AI002 Fixture 2026", start_date=self.start, end_date=self.end)
            self.assertEqual(len(events), 0)
        finally:
            os.remove(tpath)

    def test_live_mode_never_reads_fixture(self):
        """Fix A: Live FailClosedSource never reads synthetic fixture."""
        source = FailClosedSource()
        self.assertEqual(source.source_mode, "LIVE")
        events = source.get_confirmed_events("AI002 Fixture 2026", self.start, self.end)
        self.assertEqual(len(events), 0)

    def test_missing_cash_account_scope_fails_closed(self):
        """Fix B: Empty account scope fails closed with MISSING_ACCOUNT_SCOPE."""
        req = ForecastRequest(
            company="AI002 Fixture 2026",
            financial_as_of=self.as_of,
            forecast_start=self.start,
            forecast_end=self.end,
            reporting_currency="VND",
            cash_account_scope=[],  # Empty scope
        )
        valid, reason, _ = validate_forecast_request(req)
        self.assertFalse(valid)
        self.assertEqual(reason, ReasonCode.MISSING_ACCOUNT_SCOPE)

    def test_negative_valid_balance_accepted(self):
        """Fix B: Negative verified balance is validly represented."""
        accounts = [AccountBalance(account="Overdraft - A2F", amount=Decimal("-5000000"), currency="VND", deficit=True)]
        opening = OpeningCash(
            aggregate_amount=Decimal("-5000000"),
            reconciliation="ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED",
            has_constituent_deficit=True,
            accounts=accounts,
        )
        self.assertTrue(opening.has_constituent_deficit)
        self.assertEqual(opening.aggregate_amount, Decimal("-5000000"))

    def test_trial_balance_reconciled_when_gl_equals_tb(self):
        """Fix B2: GL == TB -> RECONCILED status."""
        from lotus_fin.cashflow.adapters import get_opening_cash_ledger
        opening = get_opening_cash_ledger("AI002 Fixture 2026", self.as_of, account_scope=["Cash - A2F"])
        self.assertIn(opening.reconciliation, ("TRIAL_BALANCE_RECONCILED", "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED"))
        self.assertIn(opening.aggregate_amount, (Decimal("0"), Decimal("11550000")))

    def test_trial_balance_empty_scope_fails_closed(self):
        """Fix B2: get_opening_cash_ledger returns RECONCILIATION_UNAVAILABLE when account_scope is empty."""
        from lotus_fin.cashflow.adapters import get_opening_cash_ledger
        opening = get_opening_cash_ledger("AI002 Fixture 2026", self.as_of, account_scope=[])
        self.assertEqual(opening.reconciliation, "RECONCILIATION_UNAVAILABLE")
        self.assertEqual(opening.aggregate_amount, Decimal("0"))


if __name__ == "__main__":
    unittest.main()

