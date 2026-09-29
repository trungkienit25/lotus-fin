import frappe
import json
from decimal import Decimal

C = "AI002 Fixture 2026"
frappe.set_user("Administrator")
gl = frappe.get_all("GL Entry", filters={"company": C, "is_cancelled": 0, "posting_date": ["<=", "2026-09-26"]}, fields=["account", "debit", "credit", "voucher_type", "voucher_no", "posting_date"], limit_page_length=1000)
cash = [r for r in gl if r.account == "Cash - A2F"]
cash_debit = sum(r.debit for r in cash)
cash_credit = sum(r.credit for r in cash)
si = frappe.get_all("Sales Invoice", filters={"company": C, "docstatus": 1}, fields=["name", "remarks", "posting_date", "due_date", "grand_total", "outstanding_amount"], order_by="remarks", limit_page_length=100)
pi = frappe.get_all("Purchase Invoice", filters={"company": C, "docstatus": 1}, fields=["name", "remarks", "posting_date", "due_date", "grand_total", "outstanding_amount"], order_by="remarks", limit_page_length=100)
schedule = frappe.get_all("Payment Schedule", filters={"parent": ["in", [r.name for r in si+pi]]}, fields=["parent", "parenttype", "due_date", "payment_amount", "outstanding"], limit_page_length=100)
payments = frappe.get_all("Payment Entry", filters={"company": C, "docstatus": 1}, fields=["name", "payment_type", "paid_amount", "received_amount", "posting_date"], limit_page_length=100)
trial = frappe.get_attr("erpnext.accounts.report.trial_balance.trial_balance.execute")(frappe._dict({"company": C, "fiscal_year": "2026", "from_date": "2026-09-01", "to_date": "2026-09-26", "show_zero_values": 0}))
trial_cash = [r for r in trial[1] if isinstance(r, dict) and r.get("account") == "Cash - A2F"]
print(json.dumps({"gl_count":len(gl), "cash_debit": str(cash_debit), "cash_credit": str(cash_credit), "cash_net": str(cash_debit-cash_credit), "cash_vouchers": cash, "trial_cash":trial_cash, "sales": si, "purchase": pi, "schedule": schedule, "payments": payments}, default=str))
