from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FinancingMatchRequestDTO(BaseModel):
    """Input payload for deterministic banking product matching."""
    company: str
    amount: float
    term_months: int
    purpose: str = "WORKING_CAPITAL"
    has_collateral: bool = False
    collateral_types: List[str] = Field(default_factory=list)


class CopilotQueryRequestDTO(BaseModel):
    """Input payload for natural language AI Copilot advisory."""
    company: str
    query: str


class MatchedProductDTO(BaseModel):
    product_id: str
    provider: str
    product_name: str
    product_type: str
    match_score: float
    score_breakdown: Dict[str, float]
    nominal_rate_annual: float
    estimated_monthly_interest: float
    disbursement_speed_days: int
    requires_collateral: bool
    source_ref: str
    source_as_of: str
    is_stale: bool
    matched_reasons: List[str] = Field(default_factory=list)
    missing_criteria: List[str] = Field(default_factory=list)


class FinancingDecisionResponseDTO(BaseModel):
    status: str
    request_summary: Dict[str, Any]
    matched_options_count: int
    matched_products: List[MatchedProductDTO] = Field(default_factory=list)
    disqualified_products_count: int
    disqualified_summary: List[Dict[str, Any]] = Field(default_factory=list)
    policy_declaration: Dict[str, Any] = Field(default_factory=dict)


class CopilotResponseDTO(BaseModel):
    parsed_intent: Dict[str, Any]
    deterministic_matching_result: Dict[str, Any]
    ai_advice: Dict[str, Any]
