"""
Lotus Fin Domain - Metric Enums and Types.
Defines standardized metric identifiers and data availability states.
"""

from enum import Enum


class MetricStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    PARTIAL = "PARTIAL"


class MetricId(str, Enum):
    REVENUE = "revenue"
    COGS = "cogs"
    GROSS_MARGIN = "gross_margin"
    GROSS_PROFIT = "gross_profit"
    AR_OUTSTANDING = "ar_outstanding"
    OVERDUE_AR_RATIO = "overdue_ar_ratio"
    AP_OUTSTANDING = "ap_outstanding"
    NEAR_TERM_AP = "near_term_ap"
    CASH_BALANCE = "cash_balance"
    DSO = "dso"
    DPO = "dpo"
    CCC = "ccc"
    NET_CASH_FLOW = "net_cash_flow"
    ENDING_CASH = "ending_cash"
    CASH_SHORTFALL = "cash_shortfall"


class SnapshotStatus(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SOURCE_ERROR = "SOURCE_ERROR"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
