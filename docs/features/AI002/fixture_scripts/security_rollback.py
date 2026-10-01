import frappe
import json
from lotus_fin.security.access import get_verified_company, check_report_permission
from lotus_fin.api.key_reports import extract_key_report_data

C = "AI002 Fixture 2026"
def probe(label, fn):
    try:
        value = fn()
        return {"check": label, "result": "ALLOW", "value": str(value)[:160]}
    except Exception as exc:
        return {"check": label, "result": "DENY", "exception": type(exc).__name__, "message": str(exc)[:160]}

frappe.set_user("Administrator")
finance = "ai002.finance@test.invalid"
denied = "ai002.denied@test.invalid"
try:
    for address, allowed_company in [(finance, C), (denied, "Name")]:
        if not frappe.db.exists("User", address):
            user = frappe.get_doc({"doctype": "User", "email": address, "first_name": "AI002 Test", "enabled": 1, "send_welcome_email": 0, "roles": [{"role": "Accounts User"}]})
            user.flags.no_welcome_mail = True
            user.insert(ignore_permissions=True)
        if not frappe.db.exists("User Permission", {"user": address, "allow": "Company", "for_value": allowed_company}):
            frappe.get_doc({"doctype": "User Permission", "user": address, "allow": "Company", "for_value": allowed_company, "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
    out = []
    ple = frappe.db.get_value("Payment Ledger Entry", {"company": C}, "name")
    for address in [finance, denied]:
        frappe.set_user(address)
        out.append({"user": address, "checks": [
            probe("company_fixture", lambda: get_verified_company(C)),
            probe("company_demo", lambda: get_verified_company("Name (Demo)")),
            probe("company_missing", lambda: get_verified_company("AI002 Does Not Exist")),
            probe("report_gl", lambda: check_report_permission("General Ledger")),
            probe("report_ar", lambda: check_report_permission("Accounts Receivable")),
            probe("report_ap", lambda: check_report_permission("Accounts Payable")),
            probe("invoice_fixture", lambda: frappe.has_permission("Sales Invoice", "read", doc="ACC-SINV-2026-00006")),
            probe("payment_fixture", lambda: frappe.has_permission("Payment Entry", "read", doc="ACC-PAY-2026-00006")),
            probe("payment_ledger_doctype", lambda: frappe.has_permission("Payment Ledger Entry", "read")),
            probe("payment_ledger_fixture", lambda: frappe.has_permission("Payment Ledger Entry", "read", doc=ple)),
            probe("ar_extract_fixture", lambda: (lambda r: {"status":r.get("status"), "rows":r.get("total_rows")})(extract_key_report_data("accounts_receivable", {"company": C, "report_date": "2026-09-26"}, C))),
            probe("ar_extract_tampered_company", lambda: extract_key_report_data("accounts_receivable", {"company": "Name (Demo)", "report_date": "2026-09-26"}, C).get("status")),
            probe("ar_extract_arbitrary_key", lambda: extract_key_report_data("arbitrary_report", {"company": C}, C).get("status")),
        ]})
    frappe.set_user("Administrator")
    print(json.dumps(out))
finally:
    frappe.set_user("Administrator")
    frappe.db.rollback()
