from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict
from .models import (
    OpeningCash,
    CashEvent,
    CashEventDirection,
    ForecastPoint,
    ShortfallEvent,
    BreachKind,
)


def compute_forecast(
    opening_cash: OpeningCash,
    cash_events: List[CashEvent],
    forecast_start: date,
    forecast_end: date,
) -> Tuple[List[ForecastPoint], List[ShortfallEvent]]:
    """
    Strict deterministic baseline:
    modeled_cash(EOD t) = opening + Sigma inflows(<=t) - Sigma outflows(<=t)

    O(N) in-memory Python Decimal running sum. No per-day SQL queries.
    Shortfall state machine:
    - INHERITED_FROM_OPENING if opening_cash.aggregate_amount < 0
    - NEW_MODELED_DEFICIT if opening_cash >= 0 and modeled_cash crosses below 0
    """
    # 1. Index events by date
    events_by_date: Dict[date, List[CashEvent]] = {}
    for event in cash_events:
        if forecast_start <= event.date <= forecast_end:
            events_by_date.setdefault(event.date, []).append(event)

    # 2. Running sum over 30 days
    points: List[ForecastPoint] = []
    running = opening_cash.aggregate_amount
    first_negative_date: Optional[date] = None
    minimum_cash = running
    minimum_date = forecast_start
    current = forecast_start

    while current <= forecast_end:
        day_events = events_by_date.get(current, [])
        day_event_ids: List[str] = []
        for ev in day_events:
            if ev.direction == CashEventDirection.INFLOW:
                running += ev.amount
            elif ev.direction == CashEventDirection.OUTFLOW:
                running -= ev.amount
            day_event_ids.append(ev.source_ref)

        points.append(
            ForecastPoint(
                date=current,
                modeled_cash=running,
                status="OK",
                included_event_ids=day_event_ids,
            )
        )

        if running < minimum_cash:
            minimum_cash = running
            minimum_date = current

        if running < Decimal("0") and first_negative_date is None:
            first_negative_date = current

        current += timedelta(days=1)

    # 3. Shortfall state machine
    shortfall_events: List[ShortfallEvent] = []
    if opening_cash.aggregate_amount < Decimal("0"):
        shortfall_events.append(
            ShortfallEvent(
                type="NEGATIVE_MODELED_CASH",
                first_date=forecast_start,
                minimum_modeled_cash=minimum_cash,
                minimum_date=minimum_date,
                threshold=Decimal("0"),
                breach_kind=BreachKind.INHERITED_FROM_OPENING,
            )
        )
    elif first_negative_date is not None:
        shortfall_events.append(
            ShortfallEvent(
                type="NEGATIVE_MODELED_CASH",
                first_date=first_negative_date,
                minimum_modeled_cash=minimum_cash,
                minimum_date=minimum_date,
                threshold=Decimal("0"),
                breach_kind=BreachKind.NEW_MODELED_DEFICIT,
            )
        )

    return points, shortfall_events
