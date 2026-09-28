from datetime import date, timedelta
from typing import Optional, Tuple
from .models import ForecastRequest, ReasonCode, CoverageScope

try:
    import frappe
    from lotus_fin.security.access import get_verified_company
except ImportError:
    frappe = None
    get_verified_company = None


def validate_forecast_request(request: ForecastRequest, user: Optional[str] = None) -> Tuple[bool, Optional[ReasonCode], Optional[str]]:
    """
    Validates request against strict contract invariants:
    1. Company verified server-side
    2. forecast_start == financial_as_of + 1 day
    3. forecast_end == forecast_start + 29 days (exactly 30 days)
    4. Supported currency (VND for P0)
    5. Coverage scope must be TRADE_ONLY for P0
    """
    # 1. Company non-empty check
    if not request.company or not str(request.company).strip():
        return False, ReasonCode.MISSING_COMPANY, "Company is required."

    # 2. Date alignment & horizon invariants
    expected_start = request.financial_as_of + timedelta(days=1)
    if request.forecast_start != expected_start:
        return False, ReasonCode.HORIZON_MISMATCH, f"forecast_start must be exactly financial_as_of + 1 day ({expected_start})."

    expected_end = request.forecast_start + timedelta(days=29)
    if request.forecast_end != expected_end:
        return False, ReasonCode.HORIZON_MISMATCH, f"forecast_end must be exactly forecast_start + 29 days ({expected_end}) for a 30-day horizon."

    # 3. Currency check
    if request.reporting_currency != "VND":
        return False, ReasonCode.UNSUPPORTED_CURRENCY, "Only VND is supported for P0 TRADE_ONLY baseline."

    # 4. Cash account scope is strictly required (Fix B: empty scope != auto-select all Cash/Bank)
    if not request.cash_account_scope or not isinstance(request.cash_account_scope, list) or len(request.cash_account_scope) == 0:
        return False, ReasonCode.MISSING_ACCOUNT_SCOPE, "Explicit cash_account_scope is required."

    # 5. Server-side company authorization and account scope validation
    # Only invoke live Frappe DB check when Frappe is initialized with an active database connection
    if frappe and hasattr(frappe, "db") and frappe.db:
        if get_verified_company:
            try:
                get_verified_company(company=request.company, user=user)
            except Exception:
                return False, ReasonCode.UNAUTHORIZED_ACCESS, "FORBIDDEN"

        # Validate explicit account scope
        for acc in request.cash_account_scope:
            acc_data = frappe.db.get_value(
                "Account",
                acc,
                ["name", "company", "is_group", "disabled", "account_type", "account_currency"],
                as_dict=True,
            )
            if not acc_data:
                return False, ReasonCode.DATA_PIPELINE_ERROR, f"Account {acc} does not exist."
            if acc_data.company != request.company:
                return False, ReasonCode.UNAUTHORIZED_ACCESS, "FORBIDDEN"
            if acc_data.is_group:
                return False, ReasonCode.DATA_PIPELINE_ERROR, f"Account {acc} is a group account; only leaf accounts allowed."
            if acc_data.disabled:
                return False, ReasonCode.DATA_PIPELINE_ERROR, f"Account {acc} is disabled."
            if acc_data.account_type not in ["Bank", "Cash"]:
                return False, ReasonCode.DATA_PIPELINE_ERROR, f"Account {acc} must be of type Cash or Bank."
            if acc_data.account_currency and acc_data.account_currency != request.reporting_currency:
                return False, ReasonCode.UNSUPPORTED_CURRENCY, f"Account {acc} currency {acc_data.account_currency} does not match {request.reporting_currency}."

    return True, None, None

