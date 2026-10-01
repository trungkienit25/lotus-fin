from abc import ABC, abstractmethod
import json
import os
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from .models import CashEvent, CashEventDirection


class FutureEventSource(ABC):
    """Abstract interface for confirmed future cash events."""

    source_mode: str = "LIVE"
    provider_version: str = "v1"

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

    source_mode: str = "LIVE"
    provider_version: str = "v1"

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

    source_mode: str = "FIXTURE"
    provider_version: str = "v1_synthetic"

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

        try:
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return []

        if not isinstance(data, dict):
            return []

        fixture_company = data.get("company")
        # Fail-closed: missing company metadata or mismatching company returns no events
        if not fixture_company or fixture_company != company:
            return []

        events: List[CashEvent] = []
        raw_events = data.get("records") or data.get("direct_confirmed_commitments", [])
        for row in raw_events:
            row_company = row.get("company")
            # If row has explicit company, it must match fixture_company and requested company
            if row_company and row_company != company:
                continue
            ev_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            if start_date <= ev_date <= end_date:
                direction = CashEventDirection.INFLOW if row["direction"] == "inflow" else CashEventDirection.OUTFLOW
                amount = Decimal(str(row["amount"]))
                events.append(
                    CashEvent(
                        source_ref=row["source_ref"],
                        source_kind="synthetic",
                        trust_state="FIXTURE_DECLARATION_ONLY",
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

