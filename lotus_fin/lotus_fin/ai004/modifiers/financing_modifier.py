from decimal import Decimal
from typing import List
import uuid
from lotus_fin.ai004.domain.models import SimulatedCashEvent, ScenarioParameters
from lotus_fin.ai004.domain.enums import CashFlowDirection, EventCategory
from .base import IScenarioModifier


class FinancingModifier(IScenarioModifier):
    """
    Strategy: Injects a simulated capital injection / financing drawdown into the cash timeline.
    """

    def is_active(self, params: ScenarioParameters) -> bool:
        return params.financing_amount > Decimal("0.00")

    def apply(
        self,
        events: List[SimulatedCashEvent],
        params: ScenarioParameters
    ) -> List[SimulatedCashEvent]:
        result = list(events)
        if params.financing_amount > Decimal("0.00"):
            injection_date = params.financing_date or params.as_of
            result.append(
                SimulatedCashEvent(
                    id=f"SYN-FIN-{uuid.uuid4().hex[:8]}",
                    category=EventCategory.FINANCING,
                    direction=CashFlowDirection.INFLOW,
                    amount=params.financing_amount,
                    date=injection_date,
                    description=f"Synthetic Financing Injection ({params.financing_amount:,.0f})",
                    source_ref="SIMULATION_INJECTION",
                    original_amount=Decimal("0.00"),
                    original_date=injection_date,
                    is_synthetic=True
                )
            )
        return result

    def get_description(self, params: ScenarioParameters) -> str:
        return f"Financing Modifier: Inject {params.financing_amount:,.0f} on {params.financing_date or params.as_of}"
