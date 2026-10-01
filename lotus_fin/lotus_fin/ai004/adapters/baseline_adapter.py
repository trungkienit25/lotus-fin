from datetime import date, timedelta
from decimal import Decimal
from typing import List, Tuple, Optional

try:
    import frappe
except ImportError:
    frappe = None

from lotus_fin.ai004.domain.models import SimulatedCashEvent, quantize_currency
from lotus_fin.ai004.domain.enums import CashFlowDirection, EventCategory


class BaselineSourceAdapter:
    """
    Read-Only Adapter: Extracts real/trusted operational baseline data from ERPNext.
    Strictly non-invasive (Zero DB Mutation).
    """

    def get_baseline_data(
        self,
        company: str,
        as_of: date,
        horizon_days: int = 30
    ) -> Tuple[Decimal, List[SimulatedCashEvent]]:
        """
        Extracts Opening Cash balance and all pending AR/AP due events within the horizon.
        """
        start_date = as_of
        end_date = as_of + timedelta(days=horizon_days)

        opening_cash = self._get_opening_cash(company, start_date)
        events = self._get_pending_events(company, start_date, end_date)

        return opening_cash, events

    def _get_opening_cash(self, company: str, as_of: date) -> Decimal:
        """Retrieves total liquid cash & bank balances as of start date."""
        if frappe is None or not hasattr(frappe, "db") or frappe.db is None:
            return Decimal("0.00")

        try:
            gl_entries = frappe.db.sql(
                """
                SELECT SUM(debit - credit) as balance
                FROM `tabGL Entry`
                WHERE company = %s
                  AND posting_date < %s
                  AND is_cancelled = 0
                  AND account IN (
                      SELECT name FROM `tabAccount`
                      WHERE company = %s AND account_type IN ('Bank', 'Cash')
                  )
                """,
                (company, as_of.isoformat(), company),
                as_dict=True
            )
            balance = gl_entries[0].get("balance") if gl_entries else None
            return quantize_currency(balance or Decimal("0.00"))
        except Exception:
            return Decimal("0.00")

    def _get_pending_events(
        self,
        company: str,
        start_date: date,
        end_date: date
    ) -> List[SimulatedCashEvent]:
        """Retrieves outstanding AR Sales Invoices and AP Purchase Invoices."""
        events: List[SimulatedCashEvent] = []

        if frappe is None or not hasattr(frappe, "db") or frappe.db is None:
            return events

        try:
            # 1. AR Sales Invoices (Inflows)
            sales_invoices = frappe.db.sql(
                """
                SELECT name, customer, due_date, outstanding_amount
                FROM `tabSales Invoice`
                WHERE company = %s
                  AND docstatus = 1
                  AND outstanding_amount > 0
                  AND due_date BETWEEN %s AND %s
                ORDER BY due_date ASC
                """,
                (company, start_date.isoformat(), end_date.isoformat()),
                as_dict=True
            )
            for inv in sales_invoices:
                events.append(
                    SimulatedCashEvent(
                        id=f"AR-{inv['name']}",
                        category=EventCategory.AR_INVOICE,
                        direction=CashFlowDirection.INFLOW,
                        amount=quantize_currency(inv["outstanding_amount"]),
                        date=inv["due_date"] if isinstance(inv["due_date"], date) else date.fromisoformat(str(inv["due_date"])),
                        description=f"Sales Invoice {inv['name']} ({inv['customer']})",
                        source_ref=inv["name"]
                    )
                )

            # 2. AP Purchase Invoices (Outflows)
            purchase_invoices = frappe.db.sql(
                """
                SELECT name, supplier, due_date, outstanding_amount
                FROM `tabPurchase Invoice`
                WHERE company = %s
                  AND docstatus = 1
                  AND outstanding_amount > 0
                  AND due_date BETWEEN %s AND %s
                ORDER BY due_date ASC
                """,
                (company, start_date.isoformat(), end_date.isoformat()),
                as_dict=True
            )
            for pinv in purchase_invoices:
                events.append(
                    SimulatedCashEvent(
                        id=f"AP-{pinv['name']}",
                        category=EventCategory.AP_INVOICE,
                        direction=CashFlowDirection.OUTFLOW,
                        amount=quantize_currency(pinv["outstanding_amount"]),
                        date=pinv["due_date"] if isinstance(pinv["due_date"], date) else date.fromisoformat(str(pinv["due_date"])),
                        description=f"Purchase Invoice {pinv['name']} ({pinv['supplier']})",
                        source_ref=pinv["name"]
                    )
                )
        except Exception:
            pass

        return events
