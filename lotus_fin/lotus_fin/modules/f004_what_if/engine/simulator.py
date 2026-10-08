from datetime import timedelta
from decimal import Decimal
from typing import List, Optional
import uuid

from lotus_fin.modules.f004_what_if.domain.models import (
    SimulatedCashEvent,
    ScenarioParameters,
    ScenarioResult,
    BaselineMetrics,
    SimulatedMetrics,
    quantize_currency
)
from lotus_fin.modules.f004_what_if.domain.enums import SimulationStatus
from lotus_fin.modules.f004_what_if.modifiers.factory import ModifierFactory
from lotus_fin.modules.f004_what_if.engine.pipeline import ModifierPipeline
from lotus_fin.modules.f004_what_if.engine.metrics import (
    compute_daily_timeline,
    extract_summary_metrics,
    compute_delta_metrics
)


class ScenarioSimulator:
    """
    Pure Deterministic Simulation Engine for AI-F004.
    Runs In-Memory O(N) delta simulation comparing Baseline vs What-If scenarios.
    Enforces INV-SIM-01 (Zero Mutation) and INV-SIM-02 (Simulation Stamping).
    """

    def simulate(
        self,
        opening_cash: Decimal,
        baseline_events: List[SimulatedCashEvent],
        params: ScenarioParameters,
        scenario_id: Optional[str] = None
    ) -> ScenarioResult:
        sid = scenario_id or f"SCEN-{uuid.uuid4().hex[:8].upper()}"
        start_date = params.as_of
        end_date = params.as_of + timedelta(days=params.horizon_days)

        # 1. Compute Baseline
        baseline_timeline = compute_daily_timeline(
            opening_cash=opening_cash,
            events=baseline_events,
            start_date=start_date,
            end_date=end_date
        )
        base_tuple = extract_summary_metrics(
            opening_cash=opening_cash,
            timeline=baseline_timeline,
            events=baseline_events,
            start_date=start_date,
            end_date=end_date
        )
        baseline_metrics = BaselineMetrics(
            opening_cash=base_tuple[0],
            closing_cash=base_tuple[1],
            minimum_cash=base_tuple[2],
            minimum_cash_date=base_tuple[3],
            has_shortfall=base_tuple[4],
            first_shortfall_date=base_tuple[5],
            runway_days=base_tuple[6],
            total_inflows=base_tuple[7],
            total_outflows=base_tuple[8]
        )

        # 2. Build Pipeline & Execute Strategies
        active_modifiers = ModifierFactory.get_active_modifiers(params)
        pipeline = ModifierPipeline(active_modifiers)
        simulated_events, descriptions = pipeline.execute(baseline_events, params)

        # 3. Compute Simulation
        simulated_timeline = compute_daily_timeline(
            opening_cash=opening_cash,
            events=simulated_events,
            start_date=start_date,
            end_date=end_date
        )
        sim_tuple = extract_summary_metrics(
            opening_cash=opening_cash,
            timeline=simulated_timeline,
            events=simulated_events,
            start_date=start_date,
            end_date=end_date
        )
        simulated_metrics = SimulatedMetrics(
            opening_cash=sim_tuple[0],
            closing_cash=sim_tuple[1],
            minimum_cash=sim_tuple[2],
            minimum_cash_date=sim_tuple[3],
            has_shortfall=sim_tuple[4],
            first_shortfall_date=sim_tuple[5],
            runway_days=sim_tuple[6],
            total_inflows=sim_tuple[7],
            total_outflows=sim_tuple[8]
        )

        # 4. Compute Deltas
        delta_metrics = compute_delta_metrics(baseline_metrics, simulated_metrics)

        return ScenarioResult(
            scenario_id=sid,
            scenario_name=params.scenario_name,
            company=params.company,
            as_of=params.as_of,
            horizon_days=params.horizon_days,
            parameters=params,
            status=SimulationStatus.SUCCESS,
            baseline_metrics=baseline_metrics,
            simulated_metrics=simulated_metrics,
            delta_metrics=delta_metrics,
            simulated_timeline=simulated_timeline,
            applied_modifier_descriptions=descriptions,
            data_mode="simulation"
        )
