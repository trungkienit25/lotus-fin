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


def parse_ap_data(
    ap_data: List[Dict[str, Any]]
) -> Tuple[Optional[Decimal], List[str]]:
    """Extract Accounts Payable Total Outstanding."""
    if not ap_data:
        return Decimal("0.00"), []

    total_outstanding = Decimal("0.00")
    has_valid_row = False
    for row in ap_data:
        if not isinstance(row, dict):
            continue
        if row.get("is_total_row") or str(row.get("party") or "").lower() == "total":
            continue

        raw_outstanding = None
        for k in ("outstanding", "outstanding_amount", "amount", "invoiced_amount", "total_due"):
            if k in row and row[k] is not None:
                raw_outstanding = row[k]
                break

        outstanding = _to_decimal(raw_outstanding)
        if outstanding is not None:
            has_valid_row = True
            total_outstanding += outstanding

    if not has_valid_row:
        return Decimal("0.00"), ["No active payables found in period."]

    return total_outstanding.quantize(Decimal("0.01")), []


def parse_cash_balance(
    trial_balance_or_gl: List[Dict[str, Any]]
) -> Tuple[Optional[Decimal], List[str]]:
    """Extract verified cash & bank balances from Trial Balance or General Ledger."""
    if not trial_balance_or_gl:
        return None, ["No cash or bank ledger entries retrieved."]

    total_cash = Decimal("0.00")
    found_cash_account = False

    for row in trial_balance_or_gl:
        if not isinstance(row, dict):
            continue
        account_name = str(row.get("account_name") or row.get("account") or "").strip().lower()
        account_type = str(row.get("account_type") or "").strip().lower()

        is_cash_candidate = (
            account_type in ["cash", "bank"] or
            "cash" in account_name or 
            "bank" in account_name or 
            "tiền mặt" in account_name or 
            "tiền gửi" in account_name
        )

        if is_cash_candidate:
            raw_balance = None
            if "balance" in row and row["balance"] is not None:
                raw_balance = row["balance"]
            elif "closing_balance" in row and row["closing_balance"] is not None:
                raw_balance = row["closing_balance"]
            elif "closing_debit" in row or "closing_credit" in row:
                c_deb = _to_decimal(row.get("closing_debit")) or Decimal("0.00")
                c_crd = _to_decimal(row.get("closing_credit")) or Decimal("0.00")
                raw_balance = c_deb - c_crd

            balance = _to_decimal(raw_balance)
            if balance is not None:
                found_cash_account = True
                total_cash += balance

    if not found_cash_account:
        return None, ["No verified Bank or Cash account matched in chart of accounts."]

    return total_cash.quantize(Decimal("0.01")), []
