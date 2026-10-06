"""
Lotus Fin F006 - Pure Financial Math Utilities.
Deterministic, isolated math calculations with zero I/O and strict Decimal arithmetic.
"""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple
from .models import PaymentFrequency

MONEY = Decimal("0.01")
RATE_PREC = Decimal("0.00000001")


def add_months_to_date(base_date: datetime, months: int) -> datetime:
    """Adds N months to base date, properly handling month-end overflow."""
    month = base_date.month - 1 + months
    year = base_date.year + month // 12
    month = month % 12 + 1
    day = min(base_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                               31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime(year, month, day)


def compute_periodic_rate(annual_rate: Decimal, frequency: PaymentFrequency) -> Decimal:
    """Computes periodic interest rate based on payment frequency."""
    freq_div = Decimal("12") if frequency == PaymentFrequency.MONTHLY else Decimal("4")
    return (annual_rate / freq_div).quantize(RATE_PREC, rounding=ROUND_HALF_UP)


def compute_equal_installment_pmt(principal: Decimal, periodic_rate: Decimal, remaining_periods: int) -> Decimal:
    """
    Computes equal monthly installment (PMT):
    PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
    """
    if remaining_periods <= 0:
        return Decimal("0.00")
    if periodic_rate == Decimal("0"):
        return (principal / Decimal(str(remaining_periods))).quantize(MONEY, rounding=ROUND_HALF_UP)

    rate_factor = (Decimal("1") + periodic_rate) ** remaining_periods
    numerator = principal * periodic_rate * rate_factor
    denominator = rate_factor - Decimal("1")
    return (numerator / denominator).quantize(MONEY, rounding=ROUND_HALF_UP)


def compute_grace_period_interest(balance: Decimal, periodic_rate: Decimal) -> Decimal:
    """Computes interest-only payment during loan grace periods."""
    return (balance * periodic_rate).quantize(MONEY, rounding=ROUND_HALF_UP)

