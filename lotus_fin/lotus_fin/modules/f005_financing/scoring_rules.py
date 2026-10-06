"""
Lotus Fin F005 - Scoring Rules.
Single-responsibility calculation functions for loan matching scoring.
"""

from decimal import Decimal, ROUND_HALF_UP
from .models import FinancingProduct, FundingRequest, FundingPurpose


def compute_cost_score(product_rate: Decimal, min_rate: Decimal, rate_range: Decimal) -> Decimal:
    """Computes interest cost competitiveness score (0 - 45 pts)."""
    cost_ratio = (product_rate - min_rate) / rate_range
    bounded_ratio = min(max(cost_ratio, Decimal("0")), Decimal("1.0"))
    return (Decimal("45.0") * (Decimal("1.0") - bounded_ratio)).quantize(Decimal("0.1"))


def compute_capacity_score(purpose: FundingPurpose, product_type: str) -> Decimal:
    """Computes purpose and product-type compatibility score (30 - 35 pts)."""
    fit = Decimal("30.0")
    if purpose in [FundingPurpose.WORKING_CAPITAL, FundingPurpose.INVOICE_RECOVERY] and product_type in ["UNSECURED_LOAN", "OVERDRAFT", "INVOICE_DISCOUNT"]:
        fit += Decimal("5.0")
    elif purpose == FundingPurpose.EQUIPMENT and product_type == "SECURED_LOAN":
        fit += Decimal("5.0")
    return fit.quantize(Decimal("0.1"))


def compute_speed_score(projected_shortfall_days: int, disbursement_speed_days: int) -> Decimal:
    """Computes disbursement turnaround match score (10 - 20 pts)."""
    speed = Decimal("15.0")
    if projected_shortfall_days <= 15 and disbursement_speed_days <= 3:
        speed = Decimal("20.0")
    elif disbursement_speed_days > 7:
        speed = Decimal("10.0")
    return speed.quantize(Decimal("0.1"))


def compute_estimated_monthly_interest(amount: Decimal, annual_rate: Decimal) -> float:
    """Computes simple initial monthly interest accrual in VND."""
    monthly_interest = (amount * annual_rate / Decimal("12.0")).quantize(Decimal("1.0"), rounding=ROUND_HALF_UP)
    return float(monthly_interest)
