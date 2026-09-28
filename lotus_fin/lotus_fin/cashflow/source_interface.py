from abc import ABC, abstractmethod
import json
import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from .models import CashEvent, CashEventDirection


class FutureEventSource(ABC):
    """Abstract interface for confirmed future cash events."""

    @abstractmethod
    def get_confirmed_events(
        self,
        company: str,
        start_date: date,
        end_date: date,
        currency: str = "VND",
        financial_as_of: Optional[date] = None,
    ) -> List[CashEvent]:
        pass


class FailClosedSource(FutureEventSource):
    """Production default: no verified production commitment source exists."""

    def get_confirmed_events(
        self,
        company: str,
        start_date: date,
        end_date: date,
        currency: str = "VND",
        financial_as_of: Optional[date] = None,
    ) -> List[CashEvent]:
        # Fail closed — returns empty list
        return []


class SyntheticFixtureSource(FutureEventSource):
    """
    Test-only fixture adapter.
    Classification: SYNTHETIC_TEST_ONLY.
    Loads confirmed commitments from JSON fixture.
    """

    def __init__(self, fixture_path: Optional[str] = None):
        self.fixture_path = fixture_path

    def get_confirmed_events(
        self,
        company: str,
        start_date: date,
        end_date: date,
        currency: str = "VND",
        financial_as_of: Optional[date] = None,
    ) -> List[CashEvent]:
        if not self.fixture_path or not os.path.exists(self.fixture_path):
            return []

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        events: List[CashEvent] = []
        raw_events = data.get("records") or data.get("direct_confirmed_commitments", [])
        for row in raw_events:
            ev_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            if start_date <= ev_date <= end_date:
                direction = CashEventDirection.INFLOW if row["direction"] == "inflow" else CashEventDirection.OUTFLOW
                amount = Decimal(str(row["amount"]))
                events.append(
                    CashEvent(
                        source_ref=row["source_ref"],
                        source_kind=row["source_kind"],
                        trust_state=row["trust_state"],
                        timing_basis=row["timing_basis"],
                        date=ev_date,
                        direction=direction,
                        amount=amount,
                        evidence_refs=row.get("evidence_refs", []),
                        obligation_id=row.get("obligation_id"),
                        assumption_id=row.get("assumption_id"),
                        company=company,
                        currency=currency,
                        financial_as_of=financial_as_of,
                    )
                )

        return events
