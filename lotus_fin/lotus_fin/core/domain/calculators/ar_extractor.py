from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple


def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        d = Decimal(str(val))
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return None


def parse_ar_data(
    ar_data: List[Dict[str, Any]],
    as_of_date: Optional[date] = None
) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal], List[str]]:
    """
    Extract Accounts Receivable Total Outstanding, Overdue Amount, and Overdue Ratio.
    Returns (total_ar, overdue_ar, overdue_ratio, limitations).
    """
    limitations: List[str] = []
    if not ar_data:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), []

    total_outstanding = Decimal("0.00")
    total_overdue = Decimal("0.00")
    ref_date = as_of_date or datetime.now(timezone.utc).date()
    has_valid_row = False

    for row in ar_data:
        if not isinstance(row, dict):
            continue
        if row.get("is_total_row") or str(row.get("party") or "").lower() == "total":
            continue

        raw_outstanding = None
        for k in ("outstanding", "outstanding_amount", "invoiced_amount", "amount", "total_due"):
            if k in row and row[k] is not None:
                raw_outstanding = row[k]
                break

        outstanding = _to_decimal(raw_outstanding)
        if outstanding is None:
            continue

        has_valid_row = True
        total_outstanding += outstanding

        raw_overdue = None
        for k in ("overdue_amount", "overdue"):
            if k in row and row[k] is not None:
                raw_overdue = row[k]
                break

        overdue = _to_decimal(raw_overdue)
        if overdue is not None:
            total_overdue += overdue
        else:
            due_date_str = row.get("due_date")
            if due_date_str:
                try:
                    if isinstance(due_date_str, (datetime, date)):
                        row_due = due_date_str if isinstance(due_date_str, date) else due_date_str.date()
                    else:
                        row_due = datetime.strptime(str(due_date_str)[:10], "%Y-%m-%d").date()
                    if row_due < ref_date:
                        total_overdue += outstanding
                except Exception:
                    pass

    if not has_valid_row:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), ["No active receivables found in period."]

    if total_outstanding > Decimal("0.00"):
        overdue_ratio = (total_overdue / total_outstanding).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    else:
        overdue_ratio = Decimal("0.0000")
        if total_outstanding == Decimal("0.00") and total_overdue > Decimal("0.00"):
            limitations.append("Overdue AR exists while total outstanding is zero; anomalous ledger state.")

    return (
        total_outstanding.quantize(Decimal("0.01")),
        total_overdue.quantize(Decimal("0.01")),
        overdue_ratio,
        limitations
    )
