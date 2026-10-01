from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid


@dataclass(frozen=True)
class ScenarioParameters:
    """Input parameters defining a What-if financial stress or growth scenario."""
    sales_change_pct: Decimal = Decimal("0.0")
    collection_delay_days: int = 0
    supplier_due_shift_days: int = 0
    payroll_change_pct: Decimal = Decimal("0.0")
    opex_change_pct: Decimal = Decimal("0.0")
    one_off_expense: Decimal = Decimal("0.0")
    financing_amount: Decimal = Decimal("0.0")
    financing_term_months: int = 0
    financing_rate_annual: Decimal = Decimal("0.0")


@dataclass(frozen=True)
class ShortfallEvent:
    """Projected cash deficit event on a specific timeline date."""
    date: str
    projected_cash: float
    deficit_amount: float
    urgency_level: str  # "HIGH" | "CRITICAL" | "MODERATE"


@dataclass(frozen=True)
class KPIValue:
    """Standardized single KPI representation across baseline and simulation states."""
    metric_id: str
    metric_name: str
    baseline: Optional[float]
    simulation: Optional[float]
    absolute_change: Optional[float]
    relative_change: Optional[float]
    unit: str
    status: str = "AVAILABLE"
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "baseline": self.baseline,
            "simulation": self.simulation,
            "absolute_change": self.absolute_change,
            "relative_change": self.relative_change,
            "unit": self.unit,
            "status": self.status,
            "limitations": list(self.limitations)
        }


@dataclass(frozen=True)
class ScenarioSimulationResult:
    """Complete 9-KPI simulated financial state with explicit simulation data mode."""
    company: str
    base_snapshot_id: str
    scenario_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_mode: str = "simulation"
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 9 KPIs Layer
    revenue: KPIValue = field(default_factory=lambda: KPIValue("revenue", "Revenue", None, None, None, None, "VND"))
    gross_profit: KPIValue = field(default_factory=lambda: KPIValue("gross_profit", "Gross Profit", None, None, None, None, "VND"))
    gross_margin: KPIValue = field(default_factory=lambda: KPIValue("gross_margin", "Gross Margin", None, None, None, None, "%"))
    ar_outstanding: KPIValue = field(default_factory=lambda: KPIValue("ar_outstanding", "Accounts Receivable", None, None, None, None, "VND"))
    dso: KPIValue = field(default_factory=lambda: KPIValue("dso", "Days Sales Outstanding", None, None, None, None, "days"))
    net_cash_flow: KPIValue = field(default_factory=lambda: KPIValue("net_cash_flow", "Net Cash Flow", None, None, None, None, "VND"))
    ending_cash: KPIValue = field(default_factory=lambda: KPIValue("ending_cash", "Ending Cash Balance", None, None, None, None, "VND"))
    ccc: KPIValue = field(default_factory=lambda: KPIValue("ccc", "Cash Conversion Cycle", None, None, None, None, "days"))
    cash_shortfall: KPIValue = field(default_factory=lambda: KPIValue("cash_shortfall", "Cash Shortfall Deficit", None, None, None, None, "VND"))
    
    shortfall_events: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "company": self.company,
            "base_snapshot_id": self.base_snapshot_id,
            "data_mode": self.data_mode,
            "parameters": self.parameters,
            "revenue": self.revenue.to_dict(),
            "gross_profit": self.gross_profit.to_dict(),
            "gross_margin": self.gross_margin.to_dict(),
            "ar_outstanding": self.ar_outstanding.to_dict(),
            "dso": self.dso.to_dict(),
            "net_cash_flow": self.net_cash_flow.to_dict(),
            "ending_cash": self.ending_cash.to_dict(),
            "ccc": self.ccc.to_dict(),
            "cash_shortfall": self.cash_shortfall.to_dict(),
            "shortfall_events": list(self.shortfall_events),
            "limitations": list(self.limitations),
        }
