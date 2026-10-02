"""IVL cleanup pass 2 — cancel+delete committed transient vouchers, then re-verify."""
import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

junk = frappe.get_all("Sales Invoice", filters={"remarks": ["like", "AI003_IVL%"]},
                      fields=["name", "docstatus", "remarks"], order_by="name")
for row in junk:
    print("junk:", row.name, "docstatus", row.docstatus, row.remarks)
    doc = frappe.get_doc("Sales Invoice", row.name)
    if doc.docstatus == 1:
        doc.cancel()
    frappe.delete_doc("Sales Invoice", row.name, ignore_permissions=True)
frappe.db.commit()

if frappe.db.exists("Customer", "AI003 IVL Temp Customer"):
    frappe.delete_doc("Customer", "AI003 IVL Temp Customer", ignore_permissions=True)
    frappe.db.commit()

checks = {
    "transient_ivl_vouchers_absent": not frappe.get_all("Sales Invoice", filters={"remarks": ["like", "AI003_IVL%"]}, pluck="name"),
    "transient_customer_absent": not frappe.db.exists("Customer", "AI003 IVL Temp Customer"),
    "replay_user_absent": not frappe.db.exists("User", "ai003-ivl-replay@verify.local"),
    "phase_a_user_absent": not frappe.db.exists("User", "ai003-ivl-probe@verify.local"),
    "custom_role_absent": not frappe.get_all("Custom Role", filters={"report": "Accounts Receivable"}, pluck="name"),
    "ivl_user_permissions_absent": not frappe.get_all("User Permission", filters={"user": ["like", "ai003-ivl%"]}, pluck="name"),
    "gold_company_si_count": frappe.db.count("Sales Invoice", {"company": "AI003 Gold 2026"}),
    "a2f_fixture_si_count": frappe.db.count("Sales Invoice", {"company": "AI002 Fixture 2026"}),
    "gold_company_submitted_si": frappe.db.count("Sales Invoice", {"company": "AI003 Gold 2026", "docstatus": 1}),
}
for k, v in checks.items():
    print(f"{k}: {v}")
ok = (checks["transient_ivl_vouchers_absent"] and checks["transient_customer_absent"]
      and checks["replay_user_absent"] and checks["phase_a_user_absent"]
      and checks["custom_role_absent"] and checks["ivl_user_permissions_absent"])
print("CLEANUP_OK" if ok else "CLEANUP_INCOMPLETE")
frappe.db.rollback()
frappe.destroy()
