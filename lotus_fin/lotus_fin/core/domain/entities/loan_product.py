from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class ProductType(str, Enum):
    UNSECURED_LOAN = "UNSECURED_LOAN"
    SECURED_LOAN = "SECURED_LOAN"
    OVERDRAFT = "OVERDRAFT"
    FACTORING = "FACTORING"
    INVOICE_DISCOUNTING = "INVOICE_DISCOUNT"
    SUPPLY_CHAIN_FINANCE = "SCF"


class RateType(str, Enum):
    FIXED = "FIXED"
    FLOATING = "FLOATING"


class FundingPurpose(str, Enum):
    WORKING_CAPITAL = "WORKING_CAPITAL"
    EQUIPMENT = "EQUIPMENT"
    INVOICE_RECOVERY = "INVOICE_RECOVERY"
    EXPANSION = "EXPANSION"


@dataclass(frozen=True)
class FinancingProduct:
    """Specification of a verified institutional financing product."""
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


@dataclass(frozen=True)
class CompanyFinancialProfile:
    """Financial profile extracted deterministically from Core FinancialSnapshot."""
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


@dataclass(frozen=True)
class FundingRequest:
    """User capital requirement parameters."""
    amount: Decimal
    term_months: int
    purpose: FundingPurpose = FundingPurpose.WORKING_CAPITAL
    currency: str = "VND"


@dataclass(frozen=True)
class ScoreBreakdown:
    """100-point transparent scoring breakdown."""
    cost_score: Decimal
    capacity_fit_score: Decimal
    speed_score: Decimal
    total_score: Decimal


@dataclass(frozen=True)
class MatchedOption:
    """Evaluated financing option with objective scoring."""
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


@dataclass(frozen=True)
class DisqualifiedOption:
    """Disqualified option with hard rule failure rationale."""
    product_id: str
    provider: str
    product_name: str
    reasons: List[str]


@dataclass(frozen=True)
class FinancingDecisionResult:
    """Complete output of deterministic financing decision support."""
    status: str
    request_summary: Dict[str, Any]
    matched_options_count: int
    matched_products: List[Dict[str, Any]]
    disqualified_products_count: int
    disqualified_summary: List[Dict[str, Any]]
    policy_declaration: Dict[str, Any]

