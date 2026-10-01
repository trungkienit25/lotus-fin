from abc import ABC, abstractmethod
from typing import List
from lotus_fin.ai004.domain.models import SimulatedCashEvent, ScenarioParameters

class IScenarioModifier(ABC):
    """
    Contract for Strategy Modifiers in AI004 What-If simulation.
    Follows Open/Closed and Liskov Substitution principles.
    """

    @abstractmethod
    def is_active(self, params: ScenarioParameters) -> bool:
        """Determines if this modifier should be included in the simulation pipeline."""
        pass

    @abstractmethod
    def apply(
        self,
        events: List[SimulatedCashEvent],
        params: ScenarioParameters
    ) -> List[SimulatedCashEvent]:
        """
        Transforms or injects SimulatedCashEvents based on scenario parameters.
        Must return a new list without mutating input objects.
        """
        pass

    @abstractmethod
    def get_description(self, params: ScenarioParameters) -> str:
        """Returns a human-readable description of the applied change."""
        pass
