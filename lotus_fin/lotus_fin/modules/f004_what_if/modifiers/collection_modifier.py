from datetime import timedelta
from typing import List
from lotus_fin.ai004.domain.models import SimulatedCashEvent, ScenarioParameters
from lotus_fin.ai004.domain.enums import CashFlowDirection, EventCategory
from .base import IScenarioModifier


class CollectionModifier(IScenarioModifier):
    """
    Strategy: Shifts AR cash collection dates by a specified number of delay/acceleration days.
    Equation: new_date = original_date + timedelta(days=collection_delay_days)
    """

    def is_active(self, params: ScenarioParameters) -> bool:
        return params.collection_delay_days != 0

    def apply(
        self,
        events: List[SimulatedCashEvent],
        params: ScenarioParameters
    ) -> List[SimulatedCashEvent]:
        shift = timedelta(days=params.collection_delay_days)
        result: List[SimulatedCashEvent] = []

        for ev in events:
            if ev.direction == CashFlowDirection.INFLOW and ev.category in (EventCategory.AR_INVOICE, EventCategory.OTHER):
                new_date = ev.date + shift
                result.append(
                    SimulatedCashEvent(
                        id=ev.id,
                        category=ev.category,
                        direction=ev.direction,
                        amount=ev.amount,
                        date=new_date,
                        description=f"{ev.description} (Collection {params.collection_delay_days:+d}d)",
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
        return f"Collection Delay Modifier: Shift AR due dates by {params.collection_delay_days:+d} days"
