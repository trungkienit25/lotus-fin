import unittest
from datetime import date
from decimal import Decimal

from lotus_fin.modules.f004_what_if.domain.models import (
    ScenarioParameters,
    SimulatedCashEvent,
    quantize_currency
)
from lotus_fin.modules.f004_what_if.domain.enums import (
    CashFlowDirection,
    EventCategory,
    ScenarioType,
    SimulationStatus
)
from lotus_fin.modules.f004_what_if.modifiers.sales_modifier import SalesModifier
from lotus_fin.modules.f004_what_if.modifiers.collection_modifier import CollectionModifier
from lotus_fin.modules.f004_what_if.modifiers.payable_modifier import PayableModifier
from lotus_fin.modules.f004_what_if.modifiers.expense_modifier import ExpenseModifier
from lotus_fin.modules.f004_what_if.modifiers.financing_modifier import FinancingModifier
from lotus_fin.modules.f004_what_if.modifiers.factory import ModifierFactory
from lotus_fin.modules.f004_what_if.engine.simulator import ScenarioSimulator
from lotus_fin.modules.f004_what_if.service import ScenarioService


class TestAI004WhatIfScenario(unittest.TestCase):
    """
    Comprehensive test suite for AI-F004 What-if Scenario Agent.
    Verifies SOLID compliance, Strategy execution, and Gold Fixtures.
    """

    def setUp(self):
        self.as_of = date(2026, 1, 1)
        self.opening_cash = Decimal("100000000.00") # 100M VND
        self.baseline_events = [
            SimulatedCashEvent(
                id="EV-001",
                category=EventCategory.AR_INVOICE,
                direction=CashFlowDirection.INFLOW,
                amount=Decimal("50000000.00"),
                date=date(2026, 1, 5),
                description="Sales Invoice Customer A"
            ),
            SimulatedCashEvent(
                id="EV-002",
                category=EventCategory.AR_INVOICE,
                direction=CashFlowDirection.INFLOW,
                amount=Decimal("80000000.00"),
                date=date(2026, 1, 15),
                description="Sales Invoice Customer B"
            ),
            SimulatedCashEvent(
                id="EV-003",
                category=EventCategory.AP_INVOICE,
                direction=CashFlowDirection.OUTFLOW,
                amount=Decimal("70000000.00"),
                date=date(2026, 1, 10),
                description="Purchase Invoice Supplier X"
            ),
            SimulatedCashEvent(
                id="EV-004",
                category=EventCategory.AP_INVOICE,
                direction=CashFlowDirection.OUTFLOW,
                amount=Decimal("110000000.00"),
                date=date(2026, 1, 20),
                description="Purchase Invoice Supplier Y"
            ),
        ]
        self.simulator = ScenarioSimulator()
        self.service = ScenarioService(simulator=self.simulator)

    def test_invariants_immutability_and_simulation_stamping(self):
        """Verify INV-SIM-01 (Zero Mutation) and INV-SIM-02 (Simulation Stamping)."""
        params = ScenarioParameters(
            company="Lotus-fin",
            as_of=self.as_of,
            sales_change_pct=Decimal("-0.20")
        )
        original_ev1_amount = self.baseline_events[0].amount

        result = self.service.run_scenario(
            params=params,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )

        # 1. Stamping invariant
        self.assertEqual(result.data_mode, "simulation")
        self.assertEqual(result.status, SimulationStatus.SUCCESS)

        # 2. Immutability invariant (Baseline events are untouched)
        self.assertEqual(self.baseline_events[0].amount, original_ev1_amount)
        self.assertEqual(self.baseline_events[0].amount, Decimal("50000000.00"))

    def test_gold_fixture_1_sales_drop_20(self):
        """Verify Gold Fixture: Sales Drop 20%."""
        params = ScenarioParameters(
            company="Lotus-fin",
            as_of=self.as_of,
            horizon_days=30,
            scenario_name="Sales Drop 20%",
            sales_change_pct=Decimal("-0.20")
        )

        result = self.service.run_scenario(
            params=params,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )

        # Baseline: 100M + 50M + 80M - 70M - 110M = 50M closing
        self.assertEqual(result.baseline_metrics.closing_cash, Decimal("50000000.00"))
        self.assertFalse(result.baseline_metrics.has_shortfall)

        # Simulated: 100M + 40M + 64M - 70M - 110M = 24M closing
        self.assertEqual(result.simulated_metrics.closing_cash, Decimal("24000000.00"))
        self.assertEqual(result.delta_metrics.closing_cash_delta, Decimal("-26000000.00"))
        self.assertFalse(result.simulated_metrics.has_shortfall)
        self.assertEqual(result.simulated_metrics.minimum_cash, Decimal("24000000.00"))

    def test_gold_fixture_2_collection_delay_10(self):
        """Verify Gold Fixture: Collection Delay 10 days introduces deficit."""
        params = ScenarioParameters(
            company="Lotus-fin",
            as_of=self.as_of,
            horizon_days=30,
            scenario_name="Collection Delay 10 Days",
            collection_delay_days=10
        )

        result = self.service.run_scenario(
            params=params,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )

        # On 2026-01-20, cash drops to -30M (Inflows delayed)
        self.assertTrue(result.simulated_metrics.has_shortfall)
        self.assertEqual(result.simulated_metrics.first_shortfall_date, date(2026, 1, 20))
        self.assertEqual(result.simulated_metrics.minimum_cash, Decimal("-30000000.00"))
        self.assertTrue(result.delta_metrics.new_shortfall_introduced)
        self.assertTrue(result.delta_metrics.shortfall_worsened)

    def test_gold_fixture_3_combined_shock(self):
        """Verify Gold Fixture: Combined Sales Drop 10%, Delay 5 days, Expense Shock 30M."""
        params = ScenarioParameters(
            company="Lotus-fin",
            as_of=self.as_of,
            horizon_days=30,
            scenario_name="Combined Shock",
            sales_change_pct=Decimal("-0.10"),
            collection_delay_days=5,
            one_off_expense=Decimal("30000000.00"),
            one_off_expense_date=date(2026, 1, 8)
        )

        result = self.service.run_scenario(
            params=params,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )

        # Inflows: 45M + 72M = 117M
        # Outflows: 70M + 110M + 30M = 210M
        # Closing: 100M + 117M - 210M = 7M
        self.assertEqual(result.simulated_metrics.closing_cash, Decimal("7000000.00"))
        self.assertEqual(result.delta_metrics.closing_cash_delta, Decimal("-43000000.00"))
        self.assertFalse(result.simulated_metrics.has_shortfall)
        self.assertEqual(result.simulated_metrics.minimum_cash, Decimal("7000000.00"))

    def test_payable_shift_mitigates_deficit(self):
        """Verify that shifting supplier payments out mitigates liquidity shortfall."""
        # 1. Base collection delay causes shortfall on day 20
        params_shortfall = ScenarioParameters(
            company="Lotus-fin",
            as_of=self.as_of,
            collection_delay_days=10
        )
        res1 = self.service.run_scenario(
            params=params_shortfall,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )
        self.assertTrue(res1.simulated_metrics.has_shortfall)

        # 2. Shift supplier payment by 15 days -> Deficit avoided!
        params_mitigated = ScenarioParameters(
            company="Lotus-fin",
            as_of=self.as_of,
            collection_delay_days=10,
            supplier_due_shift_days=15
        )
        res2 = self.service.run_scenario(
            params=params_mitigated,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )
        self.assertFalse(res2.simulated_metrics.has_shortfall)
        self.assertGreater(res2.simulated_metrics.minimum_cash, Decimal("0.00"))

    def test_financing_injection(self):
        """Verify capital injection improves closing cash exactly by financing_amount."""
        params = ScenarioParameters(
            company="Lotus-fin",
            as_of=self.as_of,
            financing_amount=Decimal("50000000.00"),
            financing_date=date(2026, 1, 12)
        )
        result = self.service.run_scenario(
            params=params,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )

        self.assertEqual(result.delta_metrics.closing_cash_delta, Decimal("50000000.00"))
        self.assertEqual(result.simulated_metrics.closing_cash, Decimal("100000000.00"))

    def test_to_dict_json_serialization(self):
        """Verify that result.to_dict() produces standard JSON dictionary."""
        params = ScenarioParameters(company="Lotus-fin", as_of=self.as_of)
        result = self.service.run_scenario(
            params=params,
            custom_baseline_events=self.baseline_events,
            custom_opening_cash=self.opening_cash
        )
        data = result.to_dict()

        self.assertIn("scenario_id", data)
        self.assertEqual(data["data_mode"], "simulation")
        self.assertEqual(data["company"], "Lotus-fin")
        self.assertIn("baseline_metrics", data)
        self.assertIn("simulated_metrics", data)
        self.assertIn("delta_metrics", data)
        self.assertIn("narrative_explanation", data)


if __name__ == "__main__":
    unittest.main()
