from decimal import Decimal
from typing import List
from lotus_fin.modules.f004_what_if.domain.models import SimulatedCashEvent, ScenarioParameters, quantize_currency
from lotus_fin.modules.f004_what_if.domain.enums import CashFlowDirection, EventCategory
from .base import IScenarioModifier


class SalesModifier(IScenarioModifier):
    """
    Strategy: Modifies sales / AR cash inflows by a percentage change factor.
    Equation: new_amount = original_amount * (1 + sales_change_pct)
    """

    def is_active(self, params: ScenarioParameters) -> bool:
        return params.sales_change_pct != Decimal("0.00")

    def apply(
        self,
        events: List[SimulatedCashEvent],
        params: ScenarioParameters
    ) -> List[SimulatedCashEvent]:
        multiplier = Decimal("1.00") + params.sales_change_pct
        if multiplier < Decimal("0.00"):
            multiplier = Decimal("0.00") # Floor at zero, cannot have negative inflow amount

        result: List[SimulatedCashEvent] = []
        for ev in events:
            if ev.direction == CashFlowDirection.INFLOW and ev.category in (EventCategory.AR_INVOICE, EventCategory.OTHER):
                modified_amount = quantize_currency(ev.amount * multiplier)
                result.append(
                    SimulatedCashEvent(
                        id=ev.id,
                        category=ev.category,
                        direction=ev.direction,
                        amount=modified_amount,
                        date=ev.date,
                        description=f"{ev.description} (Sales {params.sales_change_pct * 100:+.0f}%)",
                        source_ref=ev.source_ref,
                        original_amount=ev.original_amount or ev.amount,
                        original_date=ev.original_date or ev.date,
                        is_synthetic=ev.is_synthetic
                    )
                )
            else:
                result.append(ev)
        return result

    def get_description(self, params: ScenarioParameters) -> str:
        return f"Sales Modifier: Adjust AR inflows by {params.sales_change_pct * 100:+.1f}%"
