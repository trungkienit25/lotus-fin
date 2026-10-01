"""
Lotus Fin AI005 - Models and Type Definitions for Financing Decision Support.
Enforces Decimal arithmetic, type safety, and read-only invariants.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class ProductType(str, Enum):
    UNSECURED_LOAN = "UNSECURED_LOAN"          # Vay tín chấp
    SECURED_LOAN = "SECURED_LOAN"              # Vay thế chấp
    OVERDRAFT = "OVERDRAFT"                    # Thấu chi doanh nghiệp
    FACTORING = "FACTORING"                    # Bao thanh toán / Mua bán nợ
    INVOICE_DISCOUNTING = "INVOICE_DISCOUNT"   # Chiết khấu hóa đơn
    SUPPLY_CHAIN_FINANCE = "SCF"               # Tài trợ chuỗi cung ứng


class RateType(str, Enum):
    FIXED = "FIXED"
    FLOATING = "FLOATING"


class FundingPurpose(str, Enum):
    WORKING_CAPITAL = "WORKING_CAPITAL"
    EQUIPMENT = "EQUIPMENT"
    INVOICE_RECOVERY = "INVOICE_RECOVERY"
    EXPANSION = "EXPANSION"


@dataclass
class FinancingProduct:
    product_id: str
    provider: str
    product_name: str
    product_type: ProductType
    amount_min: Decimal
    amount_max: Decimal
    currency: str = "VND"
    rate_type: RateType = RateType.FIXED
    nominal_rate_annual: Decimal = Decimal("0.10")
    rate_spread_range: str = "9.0% - 12.0%/năm"
    term_min_months: int = 3
    term_max_months: int = 36
    disbursement_speed_days: int = 5
    min_operating_months: int = 12
    min_annual_revenue: Decimal = Decimal("1000000000")
    min_dscr_threshold: Optional[Decimal] = Decimal("1.20")
    requires_collateral: bool = False
    accepted_collaterals: List[str] = field(default_factory=lambda: ["REAL_ESTATE", "VEHICLE", "DEPOSIT"])
    requires_audited_financials: bool = False
    source_ref: str = "https://bank.example.com/rates"
    source_as_of: str = "2026-09-01"
    verified_at: str = "2026-09-15"
    ttl_days: int = 30
    status: str = "ACTIVE"


@dataclass
class CompanyFinancialProfile:
    company_name: str
    operating_months: int
    annual_revenue: Decimal
    current_cash_balance: Decimal
    current_dscr: Decimal
    has_collateral: bool = False
    collateral_types: List[str] = field(default_factory=list)
    projected_shortfall_days: int = 999
    has_audited_financials: bool = False
    as_of_date: str = "2026-09-30"


@dataclass
class FundingRequest:
    amount: Decimal
    term_months: int
    purpose: FundingPurpose = FundingPurpose.WORKING_CAPITAL
    currency: str = "VND"


@dataclass
class ScoreBreakdown:
    cost_score: Decimal
    capacity_fit_score: Decimal
    speed_score: Decimal
    total_score: Decimal


@dataclass
class MatchedOption:
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
    matched_reasons: List[str]
    missing_criteria: List[str]


@dataclass
class DisqualifiedOption:
    product_id: str
    provider: str
    product_name: str
    reasons: List[str]


@dataclass
class FinancingDecisionResult:
    status: str
    request_summary: Dict[str, Any]
    matched_options_count: int
    matched_products: List[Dict[str, Any]]
    disqualified_products_count: int
    disqualified_summary: List[Dict[str, Any]]
    policy_declaration: Dict[str, Any]


@dataclass
class KPIValue:
    metric_id: str
    metric_name: str
    baseline: Optional[float]
    simulation: Optional[float]
    absolute_change: Optional[float]
    relative_change: Optional[float]
    unit: str
    status: str = "AVAILABLE"
    limitations: List[str] = field(default_factory=list)


@dataclass
class ScenarioParameters:
    sales_change_pct: Decimal = Decimal("0.0")
    collection_delay_days: int = 0
    supplier_due_shift_days: int = 0
    payroll_change_pct: Decimal = Decimal("0.0")
    opex_change_pct: Decimal = Decimal("0.0")
    one_off_expense: Decimal = Decimal("0.0")
    financing_amount: Decimal = Decimal("0.0")
    financing_term_months: int = 0
    financing_rate_annual: Decimal = Decimal("0.0")


@dataclass
class ShortfallEvent:
    date: str
    projected_cash: float
    deficit_amount: float
    urgency_level: str


@dataclass
class ScenarioSimulationResult:
    scenario_id: str
    company: str
    base_snapshot_id: str
    data_mode: str = "simulation"
    parameters: Dict[str, Any] = field(default_factory=dict)
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
