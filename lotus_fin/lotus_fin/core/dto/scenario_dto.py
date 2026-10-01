from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioSimulateRequestDTO(BaseModel):
    """Input parameters for simulating a What-if financial stress or growth scenario."""
    company: str
    base_snapshot_id: Optional[str] = None
    sales_change_pct: float = 0.0
    collection_delay_days: int = 0
    supplier_due_shift_days: int = 0
    payroll_change_pct: float = 0.0
    opex_change_pct: float = 0.0
    one_off_expense: float = 0.0
    financing_amount: float = 0.0
    financing_term_months: int = 0
    financing_rate_annual: float = 0.0


class KPIResponseDTO(BaseModel):
    metric_id: str
    metric_name: str
    baseline: Optional[float] = None
    simulation: Optional[float] = None
    absolute_change: Optional[float] = None
    relative_change: Optional[float] = None
    unit: str
    status: str = "AVAILABLE"
    limitations: List[str] = Field(default_factory=list)


class ScenarioSimulateResponseDTO(BaseModel):
    """Output DTO of What-if Scenario 9-KPI Simulation."""
    scenario_id: str
    company: str
    base_snapshot_id: str
    data_mode: str = "simulation"
    parameters: Dict[str, Any]
    revenue: KPIResponseDTO
    gross_profit: KPIResponseDTO
    gross_margin: KPIResponseDTO
    ar_outstanding: KPIResponseDTO
    dso: KPIResponseDTO
    net_cash_flow: KPIResponseDTO
    ending_cash: KPIResponseDTO
    ccc: KPIResponseDTO
    cash_shortfall: KPIResponseDTO
    shortfall_events: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
