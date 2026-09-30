from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from lotus_fin.ai004.domain.models import (
    SimulatedCashEvent,
    TimelinePoint,
    BaselineMetrics,
    SimulatedMetrics,
    DeltaMetrics,
    quantize_currency
)
from lotus_fin.ai004.domain.enums import CashFlowDirection


def compute_daily_timeline(
    opening_cash: Decimal,
    events: List[SimulatedCashEvent],
    start_date: date,
    end_date: date
) -> List[TimelinePoint]:
    """
    Computes an authoritative O(N) daily cash trajectory.
    Formula for day t:
    Cash(t) = Opening + Inflows(<= t) - Outflows(<= t)
    """
    # 1. Bucket events by date within the window
    events_by_date: Dict[date, List[SimulatedCashEvent]] = {}
    for ev in events:
        if start_date <= ev.date <= end_date:
            events_by_date.setdefault(ev.date, []).append(ev)

    timeline: List[TimelinePoint] = []
    running_balance = quantize_currency(opening_cash)
    current_date = start_date

    while current_date <= end_date:
        day_events = events_by_date.get(current_date, [])
        day_inflows = Decimal("0.00")
        day_outflows = Decimal("0.00")
        day_event_ids: List[str] = []

        for ev in day_events:
            day_event_ids.append(ev.id)
            if ev.direction == CashFlowDirection.INFLOW:
                day_inflows += ev.amount
            elif ev.direction == CashFlowDirection.OUTFLOW:
                day_outflows += ev.amount

        running_balance = quantize_currency(running_balance + day_inflows - day_outflows)

        timeline.append(
            TimelinePoint(
                date=current_date,
                cash_balance=running_balance,
                daily_inflow=quantize_currency(day_inflows),
                daily_outflow=quantize_currency(day_outflows),
                is_negative=(running_balance < Decimal("0.00")),
                event_ids=day_event_ids
            )
        )

        current_date += timedelta(days=1)

    return timeline


def extract_summary_metrics(
    opening_cash: Decimal,
    timeline: List[TimelinePoint],
    events: List[SimulatedCashEvent],
    start_date: date,
    end_date: date
) -> Tuple[Decimal, Decimal, Decimal, date, bool, Optional[date], int, Decimal, Decimal]:
    """Extracts summary KPIs from a timeline."""
    if not timeline:
        return (
            opening_cash,
            opening_cash,
            opening_cash,
            start_date,
            (opening_cash < Decimal("0.00")),
            (start_date if opening_cash < Decimal("0.00") else None),
            0,
            Decimal("0.00"),
            Decimal("0.00")
        )

    closing_cash = timeline[-1].cash_balance
    minimum_cash = opening_cash
    minimum_cash_date = start_date
    first_shortfall_date: Optional[date] = None
    has_shortfall = False
    runway_days = len(timeline)

    # Check opening cash shortfall
    if opening_cash < Decimal("0.00"):
        has_shortfall = True
        first_shortfall_date = start_date
        runway_days = 0

    for idx, point in enumerate(timeline):
        if point.cash_balance < minimum_cash:
            minimum_cash = point.cash_balance
            minimum_cash_date = point.date

        if point.cash_balance < Decimal("0.00") and first_shortfall_date is None:
            has_shortfall = True
            first_shortfall_date = point.date
            runway_days = idx

    # Calculate total inflows and outflows within the window
    total_inflows = Decimal("0.00")
    total_outflows = Decimal("0.00")
    for ev in events:
        if start_date <= ev.date <= end_date:
            if ev.direction == CashFlowDirection.INFLOW:
                total_inflows += ev.amount
            elif ev.direction == CashFlowDirection.OUTFLOW:
                total_outflows += ev.amount

    return (
        opening_cash,
        closing_cash,
        minimum_cash,
        minimum_cash_date,
        has_shortfall,
        first_shortfall_date,
        runway_days,
        quantize_currency(total_inflows),
        quantize_currency(total_outflows)
    )


def compute_delta_metrics(
    base: BaselineMetrics,
    sim: SimulatedMetrics
) -> DeltaMetrics:
    """Calculates deterministic deltas between baseline and simulation."""
    closing_delta = quantize_currency(sim.closing_cash - base.closing_cash)
    min_delta = quantize_currency(sim.minimum_cash - base.minimum_cash)
    runway_delta = sim.runway_days - base.runway_days
    inflow_delta = quantize_currency(sim.total_inflows - base.total_inflows)
    outflow_delta = quantize_currency(sim.total_outflows - base.total_outflows)

    new_shortfall = (not base.has_shortfall and sim.has_shortfall)
    worsened = (
        new_shortfall
        or (base.has_shortfall and sim.has_shortfall and sim.minimum_cash < base.minimum_cash)
        or (base.has_shortfall and sim.has_shortfall and sim.first_shortfall_date and base.first_shortfall_date and sim.first_shortfall_date < base.first_shortfall_date)
    )

    return DeltaMetrics(
        closing_cash_delta=closing_delta,
        minimum_cash_delta=min_delta,
        runway_delta_days=runway_delta,
        total_inflow_delta=inflow_delta,
        total_outflow_delta=outflow_delta,
        shortfall_worsened=worsened,
        new_shortfall_introduced=new_shortfall
    )
