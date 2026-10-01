"""
Lotus Fin Domain - Accounting Period Value Object.
Guarantees temporal consistency and equal-length comparison bounds.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Tuple, Union


@dataclass(frozen=True)
class AccountingPeriod:
    start_date: date
    end_date: date

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError(f"Invalid period: start ({self.start_date}) > end ({self.end_date})")

    @classmethod
    def from_strings(cls, start_str: str, end_str: str) -> "AccountingPeriod":
        s = datetime.strptime(start_str.strip()[:10], "%Y-%m-%d").date()
        e = datetime.strptime(end_str.strip()[:10], "%Y-%m-%d").date()
        return cls(start_date=s, end_date=e)

    @classmethod
    def for_year(cls, year: Union[int, str]) -> "AccountingPeriod":
        y = int(year)
        return cls(start_date=date(y, 1, 1), end_date=date(y, 12, 31))

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def get_equal_previous_period(self) -> "AccountingPeriod":
        # Check if full calendar year (Jan 01 to Dec 31)
        if self.start_date.month == 1 and self.start_date.day == 1 and \
           self.end_date.month == 12 and self.end_date.day == 31 and \
           self.start_date.year == self.end_date.year:
            prev_year = self.start_date.year - 1
            return AccountingPeriod(start_date=date(prev_year, 1, 1), end_date=date(prev_year, 12, 31))

        # Generic equal-length span
        span_days = self.duration_days
        prev_end = self.start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=span_days - 1)
        return AccountingPeriod(start_date=prev_start, end_date=prev_end)

    def to_dict(self) -> dict:
        return {
            "start": self.start_date.isoformat(),
            "end": self.end_date.isoformat(),
            "duration_days": self.duration_days
        }
