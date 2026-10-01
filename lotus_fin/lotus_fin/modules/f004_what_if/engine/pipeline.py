from typing import List, Tuple
from lotus_fin.ai004.domain.models import SimulatedCashEvent, ScenarioParameters
from lotus_fin.ai004.modifiers.base import IScenarioModifier


class ModifierPipeline:
    """
    Pipeline Pattern: Sequentially processes SimulatedCashEvents through active Strategy Modifiers.
    Guarantees immutability and returns both the transformed events and descriptions of transformations.
    """

    def __init__(self, modifiers: List[IScenarioModifier]):
        self.modifiers = list(modifiers)

    def execute(
        self,
        events: List[SimulatedCashEvent],
        params: ScenarioParameters
    ) -> Tuple[List[SimulatedCashEvent], List[str]]:
        current_events = list(events)
        descriptions: List[str] = []

        for modifier in self.modifiers:
            current_events = modifier.apply(current_events, params)
            descriptions.append(modifier.get_description(params))

        return current_events, descriptions
