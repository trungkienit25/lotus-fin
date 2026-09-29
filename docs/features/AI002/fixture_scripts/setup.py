import frappe
import json
import traceback

COMPANY = "AI002 Fixture 2026"
try:
    frappe.set_user("Administrator")
    if not frappe.db.exists("Company", COMPANY):
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": COMPANY,
            "abbr": "A2F",
            "country": "Vietnam",
            "default_currency": "VND",
            "chart_of_accounts": "Standard",
        })
        company.insert(ignore_permissions=True)
    if not frappe.db.exists("Fiscal Year", "2026"):
        fiscal = frappe.get_doc({
            "doctype": "Fiscal Year",
            "year": "2026",
            "year_start_date": "2026-01-01",
            "year_end_date": "2026-12-31",
        })
        fiscal.append("companies", {"company": COMPANY})
        fiscal.insert(ignore_permissions=True)
    else:
        fiscal = frappe.get_doc("Fiscal Year", "2026")
        if COMPANY not in [r.company for r in fiscal.companies]:
            fiscal.append("companies", {"company": COMPANY})
            fiscal.save(ignore_permissions=True)
    accounts = frappe.get_all("Account", filters={"company": COMPANY, "is_group": 0}, fields=["name", "account_type", "root_type"])
    frappe.db.commit()
    print(json.dumps({"company": COMPANY, "fiscal_year": "2026", "accounts": accounts}))
except Exception:
    frappe.db.rollback()
    traceback.print_exc()
    raise
