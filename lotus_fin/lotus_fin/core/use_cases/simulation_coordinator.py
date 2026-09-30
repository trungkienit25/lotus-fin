from decimal import Decimal
from typing import Any, Dict, Optional
from lotus_fin.core.domain.entities.scenario import ScenarioParameters, ScenarioSimulationResult
from lotus_fin.core.domain.calculators.scenario_calculator import ScenarioCalculator
from lotus_fin.core.dto.scenario_dto import ScenarioSimulateRequestDTO


class SimulationCoordinator:
    """
    Coordinates What-if simulation execution.
    Decoupled from REST transports and web frameworks.
    """

    def __init__(self, calculator: Optional[ScenarioCalculator] = None):
        self.calculator = calculator or ScenarioCalculator()

    def run_simulation(
        self,
        request: ScenarioSimulateRequestDTO,
        base_snapshot: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        params = ScenarioParameters(
            sales_change_pct=Decimal(str(request.sales_change_pct)),
            collection_delay_days=request.collection_delay_days,
            supplier_due_shift_days=request.supplier_due_shift_days,
            payroll_change_pct=Decimal(str(request.payroll_change_pct)),
            opex_change_pct=Decimal(str(request.opex_change_pct)),
            one_off_expense=Decimal(str(request.one_off_expense)),
            financing_amount=Decimal(str(request.financing_amount)),
            financing_term_months=request.financing_term_months,
            financing_rate_annual=Decimal(str(request.financing_rate_annual))
        )

        base = base_snapshot or {
            "snapshot_id": request.base_snapshot_id or "snap_base_001",
            "revenue": 1000000000,
            "cogs": 600000000,
            "ar_outstanding": 250000000,
            "ap_outstanding": 150000000,
            "inventory_value": 200000000,
            "opening_cash": 300000000,
            "payroll_expense": 120000000,
            "opex_expense": 80000000
        }

        res: ScenarioSimulationResult = self.calculator.simulate(
            base_snapshot=base,
            params=params,
            company=request.company
        )
        return res.to_dict()
