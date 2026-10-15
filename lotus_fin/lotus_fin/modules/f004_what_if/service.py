from datetime import date
from decimal import Decimal
from typing import List, Optional
from lotus_fin.modules.f004_what_if.domain.models import ScenarioParameters, ScenarioResult, SimulatedCashEvent
from lotus_fin.modules.f004_what_if.engine.simulator import ScenarioSimulator
from lotus_fin.modules.f004_what_if.adapters.baseline_adapter import BaselineSourceAdapter
from lotus_fin.modules.f004_what_if.adapters.llm_explainer import ScenarioExplainer


class ScenarioService:
    """
    Application Service Façade for AI-F004 What-If Scenario Agent.
    Coordinates between Baseline Data Extraction, Deterministic Simulation, and Grounded Explanation.
    """

    def __init__(
        self,
        baseline_adapter: Optional[BaselineSourceAdapter] = None,
        simulator: Optional[ScenarioSimulator] = None,
        explainer: Optional[ScenarioExplainer] = None
    ):
        self.baseline_adapter = baseline_adapter or BaselineSourceAdapter()
        self.simulator = simulator or ScenarioSimulator()
        self.explainer = explainer or ScenarioExplainer()

    def run_scenario(
        self,
        params: ScenarioParameters,
        custom_baseline_events: Optional[List[SimulatedCashEvent]] = None,
        custom_opening_cash: Optional[Decimal] = None
    ) -> ScenarioResult:
        """
        Executes a complete What-If simulation run.
        """
        # 1. Fetch baseline if not explicitly supplied
        if custom_baseline_events is not None and custom_opening_cash is not None:
            opening_cash = custom_opening_cash
            baseline_events = custom_baseline_events
        else:
            try:
                opening_cash, baseline_events = self.baseline_adapter.get_baseline_data(
                    company=params.company,
                    as_of=params.as_of,
                    horizon_days=params.horizon_days
                )
            except Exception as e:
                from lotus_fin.modules.f004_what_if.domain.enums import SimulationStatus
                from lotus_fin.modules.f004_what_if.domain.models import BaselineMetrics, SimulatedMetrics, DeltaMetrics
                is_forbidden = "FORBIDDEN" in str(e) or "PermissionError" in type(e).__name__ or "CompanyAccessError" in type(e).__name__
                status = SimulationStatus.FORBIDDEN if is_forbidden else SimulationStatus.SOURCE_ERROR
                zero = Decimal("0.00")
                empty_baseline = BaselineMetrics(
                    opening_cash=zero, closing_cash=zero, minimum_cash=zero,
                    minimum_cash_date=params.as_of, has_shortfall=False,
                    first_shortfall_date=None, runway_days=0, total_inflows=zero, total_outflows=zero
                )
                empty_simulated = SimulatedMetrics(
                    opening_cash=zero, closing_cash=zero, minimum_cash=zero,
                    minimum_cash_date=params.as_of, has_shortfall=False,
                    first_shortfall_date=None, runway_days=0, total_inflows=zero, total_outflows=zero
                )
                empty_delta = DeltaMetrics(
                    closing_cash_delta=zero, minimum_cash_delta=zero, runway_delta_days=0,
                    total_inflow_delta=zero, total_outflow_delta=zero,
                    shortfall_worsened=False, new_shortfall_introduced=False
                )
                return ScenarioResult(
                    scenario_id="ERROR",
                    scenario_name=params.scenario_name,
                    company=params.company,
                    as_of=params.as_of,
                    horizon_days=params.horizon_days,
                    parameters=params,
                    status=status,
                    baseline_metrics=empty_baseline,
                    simulated_metrics=empty_simulated,
                    delta_metrics=empty_delta,
                    simulated_timeline=[],
                    applied_modifier_descriptions=[],
                    narrative_explanation="",
                    error_message=str(e),
                    data_mode="simulation"
                )

        # Check if baseline data is completely absent (insufficient data)
        # Note: If opening_cash == 0 and baseline_events == [], it could be INSUFFICIENT_DATA or a completely empty company.
        # 2. Run simulation engine
        result = self.simulator.simulate(
            opening_cash=opening_cash,
            baseline_events=baseline_events,
            params=params
        )

        # If company has 0 cash and 0 events, mark as INSUFFICIENT_DATA if appropriate
        if opening_cash == Decimal("0.00") and not baseline_events:
            from dataclasses import replace
            from lotus_fin.modules.f004_what_if.domain.enums import SimulationStatus
            result = replace(result, status=SimulationStatus.INSUFFICIENT_DATA)

        # 3. Generate grounded narrative
        narrative = self.explainer.explain(result)

        # 4. Attach narrative to result (using replace to preserve frozen invariant)
        from dataclasses import replace
        final_result = replace(result, narrative_explanation=narrative)

        return final_result

    def run_simulation_for_company(
        self,
        company: str,
        sales_change_pct: Decimal = Decimal("0.00"),
        collection_delay_days: int = 0,
        supplier_due_shift_days: int = 0,
        financing_amount: Decimal = Decimal("0.00"),
        as_of: Optional[date] = None,
        horizon_days: int = 30
    ):
        params = ScenarioParameters(
            company=company,
            as_of=as_of or date.today(),
            horizon_days=horizon_days,
            sales_change_pct=sales_change_pct,
            collection_delay_days=collection_delay_days,
            supplier_due_shift_days=supplier_due_shift_days,
            financing_amount=financing_amount
        )
        return self.run_scenario(params).to_dict()

