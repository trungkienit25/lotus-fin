"""Module F005 - Financing Decision Support & Copilot."""

from .models import (
    CompanyFinancialProfile,
    FundingRequest,
    FundingPurpose,
    FinancingProduct,
    ScoreBreakdown,
    MatchedOption,
    DisqualifiedOption,
    FinancingDecisionResult,
    KPIValue,
    ScenarioParameters,
    ScenarioSimulationResult,
    ShortfallEvent
)
from .catalog import get_catalog, get_active_catalog
from .matcher import FinancingDecisionEngine
from .scenario_engine import WhatIfScenarioEngine
from .advisor import FinancingIntentParser, FinancingAIAdvisor
from .service import FinancingService
from .plugin import FinancingPlugin

__all__ = [
    "CompanyFinancialProfile",
    "FundingRequest",
    "FundingPurpose",
    "FinancingProduct",
    "ScoreBreakdown",
    "MatchedOption",
    "DisqualifiedOption",
    "FinancingDecisionResult",
    "KPIValue",
    "ScenarioParameters",
    "ScenarioSimulationResult",
    "ShortfallEvent",
    "get_catalog",
    "get_active_catalog",
    "FinancingDecisionEngine",
    "WhatIfScenarioEngine",
    "FinancingIntentParser",
    "FinancingAIAdvisor",
    "FinancingService",
    "FinancingPlugin"
]
