"""
Lotus Fin Domain - Money Value Object.
Ensures immutable decimal precision and currency consistency.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Union


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "VND"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError(f"Invalid monetary amount: {self.amount}")

    @classmethod
    def from_val(cls, val: Union[int, float, str, Decimal], currency: str = "VND") -> "Money":
        return cls(amount=Decimal(str(val)), currency=currency)

    @classmethod
    def zero(cls, currency: str = "VND") -> "Money":
        return cls(amount=Decimal("0.0"), currency=currency)

    def add(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: Union[Decimal, float, int]) -> "Money":
        return Money(amount=self.amount * Decimal(str(factor)), currency=self.currency)

    def quantize(self, precision: str = "1.0") -> "Money":
        return Money(
            amount=self.amount.quantize(Decimal(precision), rounding=ROUND_HALF_UP),
            currency=self.currency
        )

    def to_float(self) -> float:
        return float(self.amount)

    def _check_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")
