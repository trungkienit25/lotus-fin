import frappe
import json
import traceback

C = "AI002 Fixture 2026"
ITEM = "AI002 TEST SERVICE"
try:
    frappe.set_user("Administrator")
    if not frappe.db.exists("Item", ITEM):
        frappe.get_doc({
            "doctype": "Item", "item_code": ITEM, "item_name": "AI002 test-only service",
            "item_group": "Services", "stock_uom": "Nos", "is_stock_item": 0,
            "include_item_in_manufacturing": 0,
        }).insert(ignore_permissions=True)
    out = []
    if not frappe.db.exists("Journal Entry", {"company": C, "user_remark": "AI002 fixture opening capital"}):
        je = frappe.get_doc({
            "doctype": "Journal Entry", "company": C, "voucher_type": "Journal Entry",
            "posting_date": "2026-09-01", "user_remark": "AI002 fixture opening capital",
            "accounts": [
                {"account": "Cash - A2F", "debit_in_account_currency": 12000000},
                {"account": "Opening Balance Equity - A2F", "credit_in_account_currency": 12000000},
            ],
        })
        je.insert(ignore_permissions=True)
        je.submit()
        out.append({"kind": "Journal Entry", "name": je.name, "amount": 12000000})
    cases = [
        ("Sales Invoice", "AR_IN", "Palmer Productions Ltd.", "2026-09-10", "2026-10-02", 3000000),
        ("Sales Invoice", "AR_OVERDUE", "West View Software Ltd.", "2026-09-05", "2026-09-20", 2000000),
        ("Sales Invoice", "AR_BEYOND", "Grant Plastics Ltd.", "2026-09-12", "2026-11-15", 1000000),
        ("Sales Invoice", "AR_PARTIAL", "Palmer Productions Ltd.", "2026-09-11", "2026-10-10", 1500000),
        ("Sales Invoice", "AR_SETTLED", "West View Software Ltd.", "2026-09-06", "2026-10-06", 500000),
        ("Purchase Invoice", "AP_IN", "Zuckerman Security Ltd.", "2026-09-10", "2026-10-04", 4000000),
        ("Purchase Invoice", "AP_OVERDUE", "MA Inc.", "2026-09-05", "2026-09-19", 1250000),
        ("Purchase Invoice", "AP_BEYOND", "Summit Traders Ltd.", "2026-09-13", "2026-11-18", 1500000),
        ("Purchase Invoice", "AP_PARTIAL", "Zuckerman Security Ltd.", "2026-09-12", "2026-10-12", 2000000),
        ("Purchase Invoice", "AP_SETTLED", "MA Inc.", "2026-09-07", "2026-10-08", 750000),
    ]
    for doctype, tag, party, posting, due, amount in cases:
        existing = frappe.db.get_value(doctype, {"company": C, "remarks": tag}, "name")
        if existing:
            out.append({"kind": doctype, "tag": tag, "name": existing, "existing": True})
            continue
        d = {
            "doctype": doctype, "company": C, "posting_date": posting, "set_posting_time": 1, "due_date": due,
            "remarks": tag, "currency": "VND", "items": [{"item_code": ITEM, "qty": 1, "rate": amount}],
        }
        if doctype == "Sales Invoice":
            d.update({"customer": party, "debit_to": "Debtors - A2F"})
            d["items"][0]["income_account"] = "Service - A2F"
        else:
            d.update({"supplier": party, "credit_to": "Creditors - A2F"})
            d["items"][0]["expense_account"] = "Office Maintenance Expenses - A2F"
        doc = frappe.get_doc(d)
        doc.insert(ignore_permissions=True)
        doc.submit()
        out.append({"kind": doctype, "tag": tag, "name": doc.name, "amount": amount, "due": due})
    frappe.db.commit()
    print(json.dumps(out))
except Exception:
    frappe.db.rollback()
    traceback.print_exc()
    raise
