from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

ZERO = Decimal("0.00")
TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")


def quantize_money(val: Optional[Decimal]) -> Optional[Decimal]:
    if val is None:
        return None
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def quantize_ratio(val: Optional[Decimal]) -> Optional[Decimal]:
    if val is None:
        return None
    return val.quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)


class KPICalculator:
    """
    Pure deterministic accounting formulas.
    Enforces Zero-is-not-error and explicit zero-division guard.
    """

    @staticmethod
    def gross_margin(
        revenue: Optional[Decimal],
        cogs: Optional[Decimal]
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Calculates Gross Profit (Revenue - COGS) and Gross Margin Ratio (Gross Profit / Revenue).
        Returns (gross_profit, gross_margin_ratio).
        """
        if revenue is None or cogs is None:
            return None, None
        gp = revenue - cogs
        if revenue == ZERO:
            return quantize_money(gp), quantize_ratio(ZERO)
        ratio = gp / revenue
        return quantize_money(gp), quantize_ratio(ratio)

    @staticmethod
    def overdue_ar_ratio(
        overdue_ar: Optional[Decimal],
        total_ar: Optional[Decimal]
    ) -> Optional[Decimal]:
        """Calculates Overdue Receivables Ratio (Overdue AR / Total AR)."""
        if overdue_ar is None or total_ar is None:
            return None
        if total_ar == ZERO:
            return quantize_ratio(ZERO)
        return quantize_ratio(overdue_ar / total_ar)

    @staticmethod
    def days_sales_outstanding(
        ar: Optional[Decimal],
        revenue: Optional[Decimal],
        period_days: int = 365
    ) -> Optional[Decimal]:
        """Calculates DSO = (AR / Revenue) * period_days."""
        if ar is None or revenue is None or revenue == ZERO or period_days <= 0:
            return None
        dso = (ar / revenue) * Decimal(str(period_days))
        return dso.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @staticmethod
    def days_payable_outstanding(
        ap: Optional[Decimal],
        cogs: Optional[Decimal],
        period_days: int = 365
    ) -> Optional[Decimal]:
        """Calculates DPO = (AP / COGS) * period_days."""
        if ap is None or cogs is None or cogs == ZERO or period_days <= 0:
            return None
        dpo = (ap / cogs) * Decimal(str(period_days))
        return dpo.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @staticmethod
    def cash_conversion_cycle(
        dso: Optional[Decimal],
        dio: Optional[Decimal],
        dpo: Optional[Decimal]
    ) -> Optional[Decimal]:
        """Calculates CCC = DSO + DIO - DPO."""
        if dso is None or dpo is None:
            return None
        dio_val = dio if dio is not None else ZERO
        ccc = dso + dio_val - dpo
        return ccc.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @staticmethod
    def variance(
        current: Optional[Decimal],
        previous: Optional[Decimal]
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Calculates Absolute Variance (current - previous) and Relative Change ((current - previous) / previous).
        Returns (abs_change, rel_change). If previous is 0 or None, rel_change is None.
        """
        if current is None or previous is None:
            return None, None
        abs_diff = quantize_money(current - previous)
        if previous == ZERO:
            return abs_diff, None
        rel_diff = quantize_ratio((current - previous) / abs(previous))
        return abs_diff, rel_diff
