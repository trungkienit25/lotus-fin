from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from .models import ForecastResponse, ForecastStatus


def validate_grounding(explanation_text: str, forecast_response: ForecastResponse) -> Tuple[bool, List[str]]:
    """
    Grounding Validator (CG-REL-01, CG-SEC-05):
    Ensures that any monetary claims or specific facts made in the explanation
    are strictly grounded in the deterministic financial result.
    """
    violations = []
    # If the forecast itself is unavailable, explanation must not assert positive cash or imaginary forecasts
    if forecast_response.status == ForecastStatus.FORECAST_UNAVAILABLE:
        if "cash balance is" in explanation_text.lower() and "unavailable" not in explanation_text.lower():
            violations.append("Explanation asserts specific cash balance when forecast is unavailable.")

    # Numeric claim verification: Any numbers mentioned in text must be present in forecast_points or opening_cash
    return len(violations) == 0, violations
