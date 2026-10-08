from typing import List
from lotus_fin.modules.f004_what_if.domain.models import ScenarioParameters
from .base import IScenarioModifier
from .sales_modifier import SalesModifier
from .collection_modifier import CollectionModifier
from .payable_modifier import PayableModifier
from .expense_modifier import ExpenseModifier
from .financing_modifier import FinancingModifier


class ModifierFactory:
    """
    Factory responsible for instantiating and resolving active modifier strategies
    based on the given ScenarioParameters.
    Follows Open/Closed Principle.
    """

    _ALL_STRATEGIES: List[IScenarioModifier] = [
        SalesModifier(),
        CollectionModifier(),
        PayableModifier(),
        ExpenseModifier(),
        FinancingModifier(),
    ]

    @classmethod
    def get_active_modifiers(cls, params: ScenarioParameters) -> List[IScenarioModifier]:
        """Returns the list of active strategy modifiers for the scenario."""
        return [strat for strat in cls._ALL_STRATEGIES if strat.is_active(params)]
