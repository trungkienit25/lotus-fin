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


def parse_pnl_data(
    pnl_data: List[Dict[str, Any]]
) -> Tuple[Optional[Decimal], Optional[Decimal], List[str]]:
    """
    Extract Revenue and COGS (Cost of Goods Sold) from Profit and Loss statement rows.
    Returns (revenue, cogs, limitations).
    """
    limitations: List[str] = []
    revenue: Optional[Decimal] = None
    cogs: Optional[Decimal] = None

    # First pass: check for root totals or standard summary rows
    for row in pnl_data:
        account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
        indent = row.get("indent")

        raw_amount = None
        for k in ("total", "amount", "balance", "net_amount"):
            if k in row and row[k] is not None:
                raw_amount = row[k]
                break

        dec_amount = _to_decimal(raw_amount)
        if dec_amount is None:
            continue

        if (
            ("parent_account" in row and row["parent_account"] == "" and "income" in account_name) or
            "total income" in account_name or
            (indent == 0.0 and row.get("is_group") == 1 and "income" in account_name)
        ):
            revenue = dec_amount
            break

    # If root group not found, sum leaf accounts
    if revenue is None:
        for row in pnl_data:
            account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
            if row.get("is_group"):
                continue

            raw_amount = None
            for k in ("total", "amount", "balance", "net_amount"):
                if k in row and row[k] is not None:
                    raw_amount = row[k]
                    break
            dec_amount = _to_decimal(raw_amount)
            if dec_amount is None:
                continue

            if "income" in account_name or "revenue" in account_name or "sales" in account_name:
                revenue = dec_amount if revenue is None else revenue + dec_amount

    # Extract COGS
    cogs_rows: List[Tuple[Dict[str, Any], Decimal]] = []
    for row in pnl_data:
        account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
        raw_amount = None
        for k in ("total", "amount", "balance", "net_amount"):
            if k in row and row[k] is not None:
                raw_amount = row[k]
                break
        dec_amount = _to_decimal(raw_amount)
        if dec_amount is None:
            continue

        if any(term in account_name for term in ["cost of goods sold", "cogs", "giá vốn"]):
            cogs_rows.append((row, dec_amount))

    if len(cogs_rows) == 1:
        cogs = cogs_rows[0][1]
    elif len(cogs_rows) > 1:
        has_group = any(r[0].get("is_group") for r in cogs_rows)
        if has_group:
            cogs = [r[1] for r in cogs_rows if r[0].get("is_group")][0]
        else:
            cogs = sum(r[1] for r in cogs_rows)

    if cogs is None:
        for row in pnl_data:
            account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
            raw_amount = None
            for k in ("total", "amount", "balance", "net_amount"):
                if k in row and row[k] is not None:
                    raw_amount = row[k]
                    break
            dec_amount = _to_decimal(raw_amount)
            if dec_amount is None:
                continue

            if any(term in account_name for term in ["cost of sales", "direct material", "direct labor"]):
                cogs = dec_amount if cogs is None else cogs + dec_amount

    if revenue is None:
        limitations.append("Revenue row could not be definitively isolated from P&L output.")
    if cogs is None:
        limitations.append("COGS row could not be definitively isolated from P&L output.")

    return revenue, cogs, limitations
