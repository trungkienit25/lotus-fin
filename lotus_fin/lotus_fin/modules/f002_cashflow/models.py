from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
from typing import List, Optional, Dict, Any
from enum import Enum


class ForecastStatus(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    FORECAST_UNAVAILABLE = "FORECAST_UNAVAILABLE"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SOURCE_ERROR = "SOURCE_ERROR"
    TIMEOUT = "TIMEOUT"
    INCONSISTENT_DATA = "INCONSISTENT_DATA"


class ReasonCode(str, Enum):
    NO_CONFIRMED_SETTLEMENT_EVENTS = "NO_CONFIRMED_SETTLEMENT_EVENTS"
    DATA_PIPELINE_ERROR = "DATA_PIPELINE_ERROR"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    MISSING_COMPANY = "MISSING_COMPANY"
    HORIZON_MISMATCH = "HORIZON_MISMATCH"
    UNSUPPORTED_CURRENCY = "UNSUPPORTED_CURRENCY"
    MISSING_ACCOUNT_SCOPE = "MISSING_ACCOUNT_SCOPE"


class BreachKind(str, Enum):
    INHERITED_FROM_OPENING = "INHERITED_FROM_OPENING"
    NEW_MODELED_DEFICIT = "NEW_MODELED_DEFICIT"


class CoverageScope(str, Enum):
    TRADE_ONLY = "TRADE_ONLY"


class CashEventDirection(str, Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


@dataclass
class ForecastRequest:
    company: str
    financial_as_of: date
    forecast_start: date
    forecast_end: date
    granularity: str = "daily"
    reporting_currency: str = "USD"
    cash_account_scope: List[str] = field(default_factory=list)
    coverage_scope: CoverageScope = CoverageScope.TRADE_ONLY
    finance_book: Optional[str] = None
    include_explanation: bool = False
    correlation_id: str = ""


@dataclass
class AccountBalance:
    account: str
    amount: Decimal
    currency: str
    deficit: bool  # True if amount < 0


@dataclass
class OpeningCash:
    aggregate_amount: Decimal
    reconciliation: str
    has_constituent_deficit: bool
    accounts: List[AccountBalance] = field(default_factory=list)


@dataclass
class Obligation:
    type: str  # AR / AP
    party_type: str
    party_hash: str  # SHA256(party)[:12]
    remaining_amount: Decimal
    due_date: Optional[date]
    source_ref: str
    currency: str


@dataclass
class CashEvent:
    source_ref: str
    source_kind: str
    trust_state: str
    timing_basis: str
    date: date
    direction: CashEventDirection
    amount: Decimal
    evidence_refs: List[str]
    obligation_id: Optional[str] = None
    assumption_id: Optional[str] = None
    company: str = ""
    currency: str = "USD"
    financial_as_of: Optional[date] = None


@dataclass
class ForecastPoint:
    date: date
    modeled_cash: Decimal
    status: str
    included_event_ids: List[str] = field(default_factory=list)


@dataclass
class ShortfallEvent:
    type: str  # NEGATIVE_MODELED_CASH
    first_date: date
    minimum_modeled_cash: Decimal
    minimum_date: date
    threshold: Decimal
    risk_level: Optional[str] = None
    breach_kind: Optional[BreachKind] = None


@dataclass
class Coverage:
    scope: CoverageScope
    completeness: str
    unverified_obligations: List[str] = field(default_factory=list)


@dataclass
class Explanation:
    status: str  # OK / UNAVAILABLE
    reason: Optional[str] = None
    error_code: Optional[str] = None
    facts: List[Dict[str, Any]] = field(default_factory=list)
    drivers: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    next_checks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ForecastResponse:
    status: ForecastStatus
    reason_code: Optional[ReasonCode] = None
    forecast_id: str = ""
    snapshot_id: str = ""
    contract_version: str = "1.2.1"
    method_version: str = "STRICT_BASELINE_V1"
    formula_version: str = "STRICT_BASELINE_V1"
    verified_company: str = ""
    financial_as_of: Optional[date] = None
    accounting_timezone: str = "Asia/Ho_Chi_Minh"
    forecast_start: Optional[date] = None
    forecast_end: Optional[date] = None
    currency: str = "USD"
    rounding: str = "Decimal"
    opening_cash: Optional[OpeningCash] = None
    opening_cash_deficit: bool = False
    obligations: List[Obligation] = field(default_factory=list)
    cash_events: List[CashEvent] = field(default_factory=list)
    unlisted_events_count: int = 0
    unlisted_events_amount: Decimal = Decimal("0")
    forecast_points: List[ForecastPoint] = field(default_factory=list)
    coverage: Optional[Coverage] = None
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    shortfall_threshold: Decimal = Decimal("0")
    shortfall_events: List[ShortfallEvent] = field(default_factory=list)
    explanation: Optional[Explanation] = None
    evidence_refs: List[str] = field(default_factory=list)
    correlation_id: str = ""
