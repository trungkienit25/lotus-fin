from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SnapshotRequestDTO(BaseModel):
    """Input payload for generating a deterministic FinancialSnapshot."""
    company: str
    fiscal_year: Optional[int] = None
    period_start_date: Optional[str] = None
    period_end_date: Optional[str] = None
    as_of_date: Optional[str] = None
    include_explanation: bool = False
    compare_previous: bool = True


class MetricResponseDTO(BaseModel):
    metric_id: str
    status: str
    amount: Optional[float] = None
    ratio: Optional[float] = None
    currency_or_unit: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class SnapshotResponseDTO(BaseModel):
    """Output DTO of a Financial Snapshot."""
    snapshot_id: str
    company: str
    period: Dict[str, Any]
    currency: str = "VND"
    status: str
    contract_version: str = "1.0.0"
    formula_version: str = "2026.1"
    metrics: Dict[str, Any]
    evidence: Dict[str, Any]
    comparison: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    system_limitations: List[str] = Field(default_factory=list)
