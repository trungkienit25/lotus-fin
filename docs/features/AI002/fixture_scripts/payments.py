import frappe
import json
import traceback
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

C = "AI002 Fixture 2026"
cases = [
    ("Sales Invoice", "AR_PARTIAL", 600000),
    ("Sales Invoice", "AR_SETTLED", 500000),
    ("Purchase Invoice", "AP_PARTIAL", 800000),
    ("Purchase Invoice", "AP_SETTLED", 750000),
]
try:
    frappe.set_user("Administrator")
    out = []
    for dt, tag, amount in cases:
        invoice_name = frappe.db.get_value(dt, {"company": C, "remarks": tag}, "name")
        if not invoice_name:
            raise ValueError("Missing invoice " + tag)
        existing = frappe.db.get_value("Payment Entry Reference", {"reference_doctype": dt, "reference_name": invoice_name, "allocated_amount": amount}, "parent")
        if existing:
            out.append({"invoice_tag": tag, "payment": existing, "existing": True})
            continue
        pe = get_payment_entry(dt, invoice_name)
        pe.posting_date = "2026-09-22"
        pe.set_posting_time = 1
        if dt == "Sales Invoice":
            pe.paid_to = "Cash - A2F"
        else:
            pe.paid_from = "Cash - A2F"
        pe.paid_amount = amount
        pe.received_amount = amount
        for ref in pe.references:
            ref.allocated_amount = amount if ref.reference_name == invoice_name else 0
        pe.insert(ignore_permissions=True)
        pe.submit()
        out.append({"invoice_tag": tag, "payment": pe.name, "amount": amount, "payment_type": pe.payment_type})
    frappe.db.commit()
    print(json.dumps(out))
except Exception:
    frappe.db.rollback()
    traceback.print_exc()
    raise
