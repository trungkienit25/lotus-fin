from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any
from .enums import ScenarioType, CashFlowDirection, EventCategory, SimulationStatus


def quantize_currency(value: Any) -> Decimal:
    """Safely converts and quantizes any numeric candidate to Decimal with 2 decimal places."""
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ScenarioParameters:
    """
    Immutable parameters defining a What-if scenario.
    All percentage and amount values are stored as Decimal.
    """
    company: str
    as_of: date
    horizon_days: int = 30
    scenario_name: str = "What-if Scenario"
    scenario_type: ScenarioType = ScenarioType.CUSTOM
    
    # 1. Sales modification (-1.00 to +5.00, e.g. -0.20 for -20%)
    sales_change_pct: Decimal = Decimal("0.00")
    
    # 2. Timing shifts
    collection_delay_days: int = 0
    supplier_due_shift_days: int = 0
    
    # 3. Expense modifications
    payroll_change_pct: Decimal = Decimal("0.00")
    opex_change_pct: Decimal = Decimal("0.00")
    one_off_expense: Decimal = Decimal("0.00")
    one_off_expense_date: Optional[date] = None
    
    # 4. Financing injection
    financing_amount: Decimal = Decimal("0.00")
    financing_date: Optional[date] = None
    
    def __post_init__(self):
        # Auto-quantize all Decimal fields to preserve mathematical invariants
        object.__setattr__(self, "sales_change_pct", quantize_currency(self.sales_change_pct))
        object.__setattr__(self, "payroll_change_pct", quantize_currency(self.payroll_change_pct))
        object.__setattr__(self, "opex_change_pct", quantize_currency(self.opex_change_pct))
        object.__setattr__(self, "one_off_expense", quantize_currency(self.one_off_expense))
        object.__setattr__(self, "financing_amount", quantize_currency(self.financing_amount))


@dataclass(frozen=True)
class SimulatedCashEvent:
    """
    Represents a cash flow event within a simulation timeline.
    Immutable to guarantee Zero DB Mutation.
    """
    id: str
    category: EventCategory
    direction: CashFlowDirection
    amount: Decimal
    date: date
    description: str = ""
    source_ref: Optional[str] = None
    original_amount: Optional[Decimal] = None
    original_date: Optional[date] = None
    is_synthetic: bool = False

    def __post_init__(self):
        object.__setattr__(self, "amount", quantize_currency(self.amount))
        if self.original_amount is not None:
            object.__setattr__(self, "original_amount", quantize_currency(self.original_amount))
        else:
            object.__setattr__(self, "original_amount", self.amount)
        if self.original_date is None:
            object.__setattr__(self, "original_date", self.date)


@dataclass(frozen=True)
class TimelinePoint:
    """Daily cash point in a simulation timeline."""
    date: date
    cash_balance: Decimal
    daily_inflow: Decimal
    daily_outflow: Decimal
    is_negative: bool
    event_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BaselineMetrics:
    opening_cash: Decimal
    closing_cash: Decimal
    minimum_cash: Decimal
    minimum_cash_date: date
    has_shortfall: bool
    first_shortfall_date: Optional[date]
    runway_days: int
    total_inflows: Decimal
    total_outflows: Decimal


@dataclass(frozen=True)
class SimulatedMetrics:
    opening_cash: Decimal
    closing_cash: Decimal
    minimum_cash: Decimal
    minimum_cash_date: date
    has_shortfall: bool
    first_shortfall_date: Optional[date]
    runway_days: int
    total_inflows: Decimal
    total_outflows: Decimal


@dataclass(frozen=True)
class DeltaMetrics:
    closing_cash_delta: Decimal
    minimum_cash_delta: Decimal
    runway_delta_days: int
    total_inflow_delta: Decimal
    total_outflow_delta: Decimal
    shortfall_worsened: bool
    new_shortfall_introduced: bool


@dataclass(frozen=True)
class ScenarioResult:
    """
    Authoritative result of a What-If Scenario simulation.
    Strictly stamped with data_mode = 'simulation' (INV-SIM-02).
    """
    scenario_id: str
    scenario_name: str
    company: str
    as_of: date
    horizon_days: int
    parameters: ScenarioParameters
    status: SimulationStatus
    baseline_metrics: BaselineMetrics
    simulated_metrics: SimulatedMetrics
    delta_metrics: DeltaMetrics
    simulated_timeline: List[TimelinePoint]
    applied_modifier_descriptions: List[str]
    narrative_explanation: str = ""
    data_mode: str = "simulation" # Invariant: Never changes from 'simulation'
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary for REST API."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "company": self.company,
            "as_of": self.as_of.isoformat(),
            "horizon_days": self.horizon_days,
            "data_mode": self.data_mode,
            "status": self.status.value,
            "version": self.version,
            "baseline_metrics": {
                "opening_cash": str(self.baseline_metrics.opening_cash),
                "closing_cash": str(self.baseline_metrics.closing_cash),
                "minimum_cash": str(self.baseline_metrics.minimum_cash),
                "minimum_cash_date": self.baseline_metrics.minimum_cash_date.isoformat(),
                "has_shortfall": self.baseline_metrics.has_shortfall,
                "first_shortfall_date": self.baseline_metrics.first_shortfall_date.isoformat() if self.baseline_metrics.first_shortfall_date else None,
                "runway_days": self.baseline_metrics.runway_days,
                "total_inflows": str(self.baseline_metrics.total_inflows),
                "total_outflows": str(self.baseline_metrics.total_outflows),
            },
            "simulated_metrics": {
                "opening_cash": str(self.simulated_metrics.opening_cash),
                "closing_cash": str(self.simulated_metrics.closing_cash),
                "minimum_cash": str(self.simulated_metrics.minimum_cash),
                "minimum_cash_date": self.simulated_metrics.minimum_cash_date.isoformat(),
                "has_shortfall": self.simulated_metrics.has_shortfall,
                "first_shortfall_date": self.simulated_metrics.first_shortfall_date.isoformat() if self.simulated_metrics.first_shortfall_date else None,
                "runway_days": self.simulated_metrics.runway_days,
                "total_inflows": str(self.simulated_metrics.total_inflows),
                "total_outflows": str(self.simulated_metrics.total_outflows),
            },
            "delta_metrics": {
                "closing_cash_delta": str(self.delta_metrics.closing_cash_delta),
                "minimum_cash_delta": str(self.delta_metrics.minimum_cash_delta),
                "runway_delta_days": self.delta_metrics.runway_delta_days,
                "total_inflow_delta": str(self.delta_metrics.total_inflow_delta),
                "total_outflow_delta": str(self.delta_metrics.total_outflow_delta),
                "shortfall_worsened": self.delta_metrics.shortfall_worsened,
                "new_shortfall_introduced": self.delta_metrics.new_shortfall_introduced,
            },
            "applied_modifiers": self.applied_modifier_descriptions,
            "narrative_explanation": self.narrative_explanation,
            "timeline_sample_count": len(self.simulated_timeline)
        }
