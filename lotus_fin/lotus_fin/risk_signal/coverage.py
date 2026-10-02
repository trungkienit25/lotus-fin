"""AI003 coverage: baseline resolution and AP window selection (S2).

Pure date/eligibility math — no I/O, no Frappe. Semantics pinned by the
METHOD GOLD oracle (AI003_METHOD_GOLD_ORACLE.py):
- AR baseline: previous calendar month, same calendar day, month-end clamp
  (resolver PREV_MONTH_SAME_DAY_CLAMP_V1, SSOT §17.4).
- AP numerator N: positive future AP with due_date in [as_of, as_of+30]
  (D0..D30 inclusive, W is a day offset — SSOT §16.8/V2).
- AP denominator D: positive future AP with due_date >= as_of.
- Past-due and nonpositive (credit) rows are excluded from N, D and counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, localcontext
from typing import Dict, Iterable, Mapping, Optional, Tuple

BASELINE_RESOLVER_VERSION = "PREV_MONTH_SAME_DAY_CLAMP_V1"
AP_WINDOW_DAYS = 30  # contract constant W=30 (D0..D30 inclusive); not a policy value


def previous_month_same_day(as_of: date) -> date:
    """Previous calendar month, same day, clamped to that month's last day.

    Gold-pinned cases: 03-31 -> 02-28 (02-29 in leap years); 01-31 -> 12-31.
    """
    first_of_month = as_of.replace(day=1)
    last_of_prev_month = first_of_month - timedelta(days=1)
    day = min(as_of.day, last_of_prev_month.day)
    return last_of_prev_month.replace(day=day)


def ap_window(as_of: date) -> Tuple[date, date]:
    """[D0, D30] inclusive; W is an offset, so the window spans 31 dates."""
    return as_of, as_of + timedelta(days=AP_WINDOW_DAYS)


class DueDateCoverage:
    """Classification of one row's due date relative to the cutoff."""

    PAST_DUE = "PAST_DUE"          # due_date < as_of
    IN_WINDOW = "IN_WINDOW"        # as_of <= due_date <= as_of + 30
    FUTURE_BEYOND = "FUTURE_BEYOND"  # due_date > as_of + 30


def classify_due(due_date: date, as_of: date) -> str:
    if due_date < as_of:
        return DueDateCoverage.PAST_DUE
    if due_date <= as_of + timedelta(days=AP_WINDOW_DAYS):
        return DueDateCoverage.IN_WINDOW
    return DueDateCoverage.FUTURE_BEYOND


@dataclass(frozen=True)
class APSelection:
    """Eligibility outcome over reconciled, schedule-cleared observations.

    Amount aggregation (N, D) is computed by the caller via ``sum_amounts``.
    """

    numerator: tuple = ()
    denominator: tuple = ()
    excluded_past_due_count: int = 0
    excluded_credit_count: int = 0
    numerator_voucher_count: int = 0
    denominator_voucher_count: int = 0


def select_ap_observations(
    observations,
    as_of: date,
    resolved_due_dates: Optional[Mapping[str, date]] = None,
) -> APSelection:
    """Select numerator/denominator observations from reconciled rows.

    ``observations`` are provenance.ReconciledObservation (positive selection
    happens here; nonpositive rows only count as excluded credits). Rows with
    a missing due date must have been resolved upstream (schedule metadata
    fallback) or they never reach this function.
    """
    resolved = resolved_due_dates or {}
    numerator: list = []
    denominator: list = []
    past_due = 0
    credits = 0
    for obs in observations:
        amount = obs.amount
        if amount <= 0:
            credits += 1
            continue
        due = resolved.get(obs.voucher_no, obs.due_date)
        if not isinstance(due, date):
            # Positive row without a valid date can never reach selection.
            raise ValueError("positive observation %s lacks a valid due date" % obs.voucher_no)
        classification = classify_due(due, as_of)
        if classification == DueDateCoverage.PAST_DUE:
            past_due += 1
            continue
        denominator.append((obs, due))
        if classification == DueDateCoverage.IN_WINDOW:
            numerator.append((obs, due))
    return APSelection(
        numerator=tuple(numerator),
        denominator=tuple(denominator),
        excluded_past_due_count=past_due,
        excluded_credit_count=credits,
        numerator_voucher_count=len({obs.count_key for obs, _ in numerator}),
        denominator_voucher_count=len({obs.count_key for obs, _ in denominator}),
    )


def sum_amounts(pairs: Iterable) -> Decimal:
    """Exact Decimal sum of observation amounts from (observation, due_date) pairs."""
    total = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = 60
        for obs, _due in pairs:
            total += obs.amount
        return +total


def resolve_due_dates(
    observations,
    metadata_by_voucher: Mapping[str, object],
) -> Tuple[Dict[str, date], list]:
    """Resolve each positive observation's due date via the schedule preflight.

    Returns (resolved map voucher_no -> effective date, list of coverage gaps).
    The schedule preflight (SSOT §17.4) supplies the authoritative invoice-level
    due date; the report row's date is only a fallback for the approved
    zero-schedule case. Disagreement between one child schedule, header and
    report date is a coverage gap, never silently resolved.
    """
    resolved: Dict[str, date] = {}
    gaps: list = []
    for obs in observations:
        if obs.amount <= 0:
            continue
        meta = metadata_by_voucher.get(obs.voucher_no)
        if meta is None:
            gaps.append((obs.voucher_no, "NO_METADATA"))
            continue
        header = meta.header_due_date
        children = [d for d in meta.child_due_dates if d is not None]
        row_due = obs.due_date
        if meta.schedule_count == 1 and children:
            child = children[0]
            if header is not None and child != header:
                gaps.append((obs.voucher_no, "CHILD_HEADER_DISAGREEMENT"))
                continue
            if row_due is not None and child != row_due:
                gaps.append((obs.voucher_no, "CHILD_REPORT_DISAGREEMENT"))
                continue
            resolved[obs.voucher_no] = child
        elif meta.schedule_count == 0:
            # Approved fallback: verified invoice/report due date, never fabricated.
            if row_due is not None and header is not None and row_due != header:
                gaps.append((obs.voucher_no, "HEADER_REPORT_DISAGREEMENT"))
                continue
            effective = header or row_due
            if effective is None:
                gaps.append((obs.voucher_no, "NO_VALID_DUE_DATE"))
                continue
            resolved[obs.voucher_no] = effective
        else:
            gaps.append((obs.voucher_no, "UNSUPPORTED_MULTI_SCHEDULE"))
    return resolved, gaps
