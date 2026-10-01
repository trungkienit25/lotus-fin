from datetime import date
from decimal import Decimal
from typing import List, Optional
from lotus_fin.ai004.domain.models import ScenarioParameters, ScenarioResult, SimulatedCashEvent
from lotus_fin.ai004.engine.simulator import ScenarioSimulator
from lotus_fin.ai004.adapters.baseline_adapter import BaselineSourceAdapter
from lotus_fin.ai004.adapters.llm_explainer import ScenarioExplainer


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
            opening_cash, baseline_events = self.baseline_adapter.get_baseline_data(
                company=params.company,
                as_of=params.as_of,
                horizon_days=params.horizon_days
            )

        # 2. Run simulation engine
        result = self.simulator.simulate(
            opening_cash=opening_cash,
            baseline_events=baseline_events,
            params=params
        )

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

