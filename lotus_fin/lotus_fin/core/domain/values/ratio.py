"""
Lotus Fin Domain - Ratio Value Object.
Encapsulates financial ratios, percentages, and zero-denominator safety.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, Union


@dataclass(frozen=True)
class Ratio:
    value: Decimal

    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            try:
                object.__setattr__(self, "value", Decimal(str(self.value)))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError(f"Invalid ratio value: {self.value}")

    @classmethod
    def from_val(cls, val: Union[int, float, str, Decimal]) -> "Ratio":
        return cls(value=Decimal(str(val)))

    @classmethod
    def safe_divide(
        cls,
        numerator: Union[Decimal, float, int],
        denominator: Union[Decimal, float, int],
        precision: str = "0.0001"
    ) -> Optional["Ratio"]:
        num = Decimal(str(numerator))
        den = Decimal(str(denominator))
        if den == Decimal("0.0"):
            return None
        res = (num / den).quantize(Decimal(precision), rounding=ROUND_HALF_UP)
        return cls(value=res)

    def to_percentage(self, precision: int = 2) -> float:
        pct = (self.value * Decimal("100")).quantize(Decimal(f"0.{'0' * precision}"), rounding=ROUND_HALF_UP)
        return float(pct)

    def to_float(self) -> float:
        return float(self.value)
