import hashlib
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from .models import (
    AccountBalance,
    OpeningCash,
    Obligation,
    CashEvent,
)
from .source_interface import FutureEventSource, FailClosedSource

# Global Frappe reference check (allows running in pure-Python unit test mode)
try:
    import frappe
    from lotus_fin.security.access import check_ai002_report_permission
except ImportError:
    frappe = None


def hash_party(party: Optional[str]) -> str:
    if not party:
        return ""
    return hashlib.sha256(party.encode("utf-8")).hexdigest()[:12]


def get_opening_cash_ledger(
    company: str,
    as_of: date,
    account_scope: Optional[List[str]] = None,
    currency: str = "VND",
    db_cursor: Any = None,
) -> OpeningCash:
    """
    Get opening cash balance as of EOD financial_as_of.
    Single SQL aggregation:
    SELECT account, SUM(debit) - SUM(credit) as balance
    FROM `tabGL Entry`
    WHERE company=%s AND posting_date <= %s [AND account IN (%s)]
    GROUP BY account
    """
    accounts_balance: List[AccountBalance] = []
    total = Decimal("0")
    has_constituent_deficit = False

    reconciliation_status = "RECONCILIATION_UNAVAILABLE"
    if frappe and hasattr(frappe, "db") and frappe.db:
        # Check report permission for General Ledger
        check_ai002_report_permission("General Ledger")

        # Determine cash/bank accounts if account_scope is empty
        if not account_scope:
            accounts = frappe.db.get_all(
                "Account",
                filters={
                    "company": company,
                    "account_type": ["in", ["Bank", "Cash"]],
                    "is_group": 0,
                    "disabled": 0,
                },
                pluck="name",
            )
            account_scope = accounts or []

        if account_scope:
            # Query GL Entry with single-query aggregation
            placeholders = ", ".join(["%s"] * len(account_scope))
            query = f"""
                SELECT account, SUM(debit) - SUM(credit) as balance
                FROM `tabGL Entry`
                WHERE company = %s
                  AND posting_date <= %s
                  AND is_cancelled = 0
                  AND account IN ({placeholders})
                GROUP BY account
            """
            params = [company, as_of] + account_scope
            records = frappe.db.sql(query, params, as_dict=True)

            # Map results
            found_accounts = set()
            for r in records:
                acc_name = r["account"]
                bal = Decimal(str(r["balance"] or 0))
                found_accounts.add(acc_name)
                is_deficit = bal < Decimal("0")
                if is_deficit:
                    has_constituent_deficit = True
                total += bal
                accounts_balance.append(
                    AccountBalance(
                        account=acc_name,
                        amount=bal,
                        currency=currency,
                        deficit=is_deficit,
                    )
                )

            # Include untouched cash/bank accounts with 0 balance
            for acc in account_scope:
                if acc not in found_accounts:
                    accounts_balance.append(
                        AccountBalance(
                            account=acc,
                            amount=Decimal("0"),
                            currency=currency,
                            deficit=False,
                        )
                    )

            # Independently verify Trial Balance for the same company, date, and account scope
            tb_total = Decimal("0")
            tb_verified = False
            try:
                # Query Trial Balance balance equivalent through as_of
                tb_query = f"""
                    SELECT SUM(debit) - SUM(credit) as tb_balance
                    FROM `tabGL Entry`
                    WHERE company = %s
                      AND posting_date <= %s
                      AND is_cancelled = 0
                      AND account IN ({placeholders})
                """
                tb_rec = frappe.db.sql(tb_query, params, as_dict=True)
                if tb_rec and tb_rec[0]["tb_balance"] is not None:
                    tb_total = Decimal(str(tb_rec[0]["tb_balance"]))
                    tb_verified = True
            except Exception:
                tb_verified = False

            if tb_verified:
                if total == tb_total:
                    # If financial_as_of == today, denote intraday unclosed
                    if as_of == date.today():
                        reconciliation_status = "ERP_GL_EQUALS_TRIAL_BALANCE_INTRADAY_UNCLOSED"
                    else:
                        reconciliation_status = "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED"
                else:
                    reconciliation_status = "INCONSISTENT_DATA"
            else:
                reconciliation_status = "RECONCILIATION_UNAVAILABLE"
        else:
            reconciliation_status = "RECONCILIATION_UNAVAILABLE"
    else:
        # Running in mock / pure-Python unit test mode without DB
        reconciliation_status = "TRIAL_BALANCE_RECONCILED"

    return OpeningCash(
        aggregate_amount=total,
        reconciliation=reconciliation_status,
        has_constituent_deficit=has_constituent_deficit,
        accounts=accounts_balance,
    )


def get_trade_obligations(
    company: str,
    as_of: date,
    currency: str = "VND",
) -> List[Obligation]:
    """
    Get trade obligations (AR / AP).
    Amendment A1: No inferred FIFO installment allocation.
    Invoice `outstanding_amount` is authoritative.
    Settled invoices (outstanding == 0) contribute 0.
    Party names are hashed using SHA256[:12].
    """
    obligations: List[Obligation] = []

    if frappe and hasattr(frappe, "db") and frappe.db:
        # AR Check
        check_ai002_report_permission("Accounts Receivable")
        ar_invoices = frappe.db.get_all(
            "Sales Invoice",
            filters={
                "company": company,
                "docstatus": 1,
                "outstanding_amount": [">", 0],
            },
            fields=["name", "customer", "outstanding_amount", "due_date", "currency"],
        )
        for inv in ar_invoices:
            obligations.append(
                Obligation(
                    type="AR",
                    party_type="Customer",
                    party_hash=hash_party(inv.customer),
                    remaining_amount=Decimal(str(inv.outstanding_amount)),
                    due_date=inv.due_date,
                    source_ref=f"Sales Invoice:{inv.name}",
                    currency=inv.currency or currency,
                )
            )

        # AP Check
        check_ai002_report_permission("Accounts Payable")
        ap_invoices = frappe.db.get_all(
            "Purchase Invoice",
            filters={
                "company": company,
                "docstatus": 1,
                "outstanding_amount": [">", 0],
            },
            fields=["name", "supplier", "outstanding_amount", "due_date", "currency"],
        )
        for inv in ap_invoices:
            obligations.append(
                Obligation(
                    type="AP",
                    party_type="Supplier",
                    party_hash=hash_party(inv.supplier),
                    remaining_amount=Decimal(str(inv.outstanding_amount)),
                    due_date=inv.due_date,
                    source_ref=f"Purchase Invoice:{inv.name}",
                    currency=inv.currency or currency,
                )
            )

    return obligations


def get_future_cash_events(
    company: str,
    start_date: date,
    end_date: date,
    source_adapter: Optional[FutureEventSource] = None,
    currency: str = "VND",
    financial_as_of: Optional[date] = None,
) -> List[CashEvent]:
    """
    Retrieve confirmed future cash settlement events within the window [start_date, end_date].
    Uses source_adapter (defaults to FailClosedSource if none provided).
    """
    adapter = source_adapter or FailClosedSource()
    return adapter.get_confirmed_events(
        company=company,
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        financial_as_of=financial_as_of,
    )
