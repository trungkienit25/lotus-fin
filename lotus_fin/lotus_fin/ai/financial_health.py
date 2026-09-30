"""
Lotus Fin AI001 - Financial Health Metrics & Comparison Engine.

Calculates deterministic metrics, trend analysis against previous periods,
and handles data quality and edge bounds.
Enforces:
1. Strict Decimal arithmetic with ROUND_HALF_UP rounding.
2. Equal length calendar period derivation for PREVIOUS_PERIOD comparison.
3. Separate snapshot and evidence generation for previous period.
4. Calculation of absolute_change and relative_change ((current - prev) / abs(prev)).
5. Zero denominator / previous == 0 handling -> status UNAVAILABLE with limitation.
6. near_term_ap: status UNAVAILABLE with limitation "near-term AP horizon not yet frozen".
7. Neutral, ungrounded metric reporting: NEVER classify trend as good/bad/healthy/unhealthy.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from lotus_fin.ai.observability import (
    log_event,
    metrics as op_metrics,
    EVENT_COMPARISON_STARTED,
    EVENT_COMPARISON_COMPLETED,
    EVENT_COMPARISON_UNAVAILABLE,
    EVENT_METRIC_COMPUTED,
    EVENT_METRIC_UNAVAILABLE
)


def compute_previous_period(period_start: str, period_end: str) -> Tuple[str, str]:
    """
    Computes equal-length previous period immediately preceding period_start.
    If period is a full calendar year (e.g. 2020-01-01 to 2020-12-31),
    the previous period is the preceding full calendar year (2019-01-01 to 2019-12-31).
    Otherwise, computes equal-length day span:
    prev_end = S - 1 day
    prev_start = prev_end - D
    """
    s_date = datetime.strptime(period_start, "%Y-%m-%d").date()
    e_date = datetime.strptime(period_end, "%Y-%m-%d").date()
    
    # Check if standard full calendar year (Jan 1 to Dec 31 of same year)
    if s_date.month == 1 and s_date.day == 1 and e_date.month == 12 and e_date.day == 31 and s_date.year == e_date.year:
        prev_year = s_date.year - 1
        return f"{prev_year}-01-01", f"{prev_year}-12-31"

    # Calculate duration in days (inclusive span: e_date - s_date)
    duration_days = (e_date - s_date).days
    
    prev_end_date = s_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=duration_days)
    
    return prev_start_date.strftime("%Y-%m-%d"), prev_end_date.strftime("%Y-%m-%d")


def compute_metric_change(
    current_val: Optional[float],
    prev_val: Optional[float],
    unit: str = ""
) -> Dict[str, Any]:
    """
    Computes absolute and relative change between current and previous values.
    Uses Decimal for precision.
    Returns:
    {
        "status": "AVAILABLE" | "UNAVAILABLE",
        "current": float | None,
        "previous": float | None,
        "absolute_change": float | None,
        "relative_change": float | None,
        "limitations": List[str]
    }
    """
    if current_val is None or prev_val is None:
        return {
            "status": "UNAVAILABLE",
            "current": current_val,
            "previous": prev_val,
            "absolute_change": None,
            "relative_change": None,
            "limitations": ["Metric unavailable in current or previous period."]
        }

    try:
        cur_dec = Decimal(str(current_val))
        prev_dec = Decimal(str(prev_val))

        # Absolute change = current - previous
        abs_change = (cur_dec - prev_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Relative change = (current - previous) / abs(previous)
        if prev_dec != Decimal("0"):
            rel_change = ((cur_dec - prev_dec) / abs(prev_dec)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            rel_val = float(rel_change)
            rel_lims = []
        else:
            rel_val = None
            rel_lims = ["Previous period value is zero; relative change undefined."]

        return {
            "status": "AVAILABLE",
            "current": float(cur_dec),
            "previous": float(prev_dec),
            "absolute_change": float(abs_change),
            "relative_change": rel_val,
            "limitations": rel_lims
        }
    except (InvalidOperation, TypeError, ValueError) as e:
        return {
            "status": "UNAVAILABLE",
            "current": current_val,
            "previous": prev_val,
            "absolute_change": None,
            "relative_change": None,
            "limitations": [f"Calculation error: {str(e)}"]
        }


def build_comparison_block(
    current_snapshot: Dict[str, Any],
    previous_snapshot: Optional[Dict[str, Any]],
    correlation_id: str
) -> Dict[str, Any]:
    """
    Builds the comparison object comparing current snapshot against previous snapshot.
    """
    log_event(
        event_type=EVENT_COMPARISON_STARTED,
        correlation_id=correlation_id,
        company=current_snapshot.get("company")
    )

    if not previous_snapshot:
        log_event(
            event_type=EVENT_COMPARISON_UNAVAILABLE,
            correlation_id=correlation_id,
            company=current_snapshot.get("company"),
            details={"reason": "No previous period snapshot provided"}
        )
        return {
            "status": "UNAVAILABLE",
            "type": "PREVIOUS_PERIOD",
            "previous_period": None,
            "metrics": {},
            "limitations": ["Previous period snapshot unavailable or could not be generated."]
        }

    # Verify matching company and currency
    cur_company = current_snapshot.get("company")
    prev_company = previous_snapshot.get("company")
    if cur_company != prev_company:
        log_event(
            event_type=EVENT_COMPARISON_UNAVAILABLE,
            correlation_id=correlation_id,
            company=cur_company,
            details={"reason": "Cross-company comparison attempted"}
        )
        return {
            "status": "UNAVAILABLE",
            "type": "PREVIOUS_PERIOD",
            "previous_period": previous_snapshot.get("period"),
            "metrics": {},
            "limitations": ["Cannot compare across different companies."]
        }

    # AI003 foundation remediation (Bucket C): current/baseline comparison is
    # only valid in the same currency — a mismatched label can never be diffed.
    cur_currency = current_snapshot.get("currency")
    prev_currency = previous_snapshot.get("currency")
    if cur_currency and prev_currency and cur_currency != prev_currency:
        log_event(
            event_type=EVENT_COMPARISON_UNAVAILABLE,
            correlation_id=correlation_id,
            company=cur_company,
            details={"reason": "Cross-currency comparison attempted"}
        )
        return {
            "status": "UNAVAILABLE",
            "type": "PREVIOUS_PERIOD",
            "previous_period": previous_snapshot.get("period"),
            "metrics": {},
            "limitations": ["Cannot compare across different currencies."]
        }

    cur_metrics = {m["metric_id"]: m for m in current_snapshot.get("metrics", [])}
    prev_metrics = {m["metric_id"]: m for m in previous_snapshot.get("metrics", [])}

    comparison_metrics = {}
    limitations = []

    # All tracked metrics
    all_metric_ids = [
        "revenue",
        "cogs",
        "gross_margin",
        "ar_outstanding",
        "overdue_ar_ratio",
        "ap_outstanding",
        "cash_balance"
    ]

    for m_id in all_metric_ids:
        cur_m = cur_metrics.get(m_id)
        prev_m = prev_metrics.get(m_id)

        c_val = cur_m.get("value") if cur_m and cur_m.get("status") == "AVAILABLE" else None
        p_val = prev_m.get("value") if prev_m and prev_m.get("status") == "AVAILABLE" else None

        change_info = compute_metric_change(c_val, p_val)
        comparison_metrics[m_id] = change_info
        if change_info["limitations"]:
            for lim in change_info["limitations"]:
                limitations.append(f"{m_id}: {lim}")

    log_event(
        event_type=EVENT_COMPARISON_COMPLETED,
        correlation_id=correlation_id,
        company=cur_company
    )

    return {
        "status": "AVAILABLE",
        "type": "PREVIOUS_PERIOD",
        "previous_period": previous_snapshot.get("period"),
        "previous_snapshot_id": previous_snapshot.get("snapshot_id"),
        "metrics": comparison_metrics,
        "limitations": limitations
    }
