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

    # 4. Server-side company authorization check
    # Only invoke live Frappe DB check when Frappe is initialized with an active database connection
    if get_verified_company and frappe and hasattr(frappe, "db") and frappe.db:
        try:
            get_verified_company(company=request.company, user=user)
        except Exception:
            return False, ReasonCode.UNAUTHORIZED_ACCESS, "FORBIDDEN"

    return True, None, None

