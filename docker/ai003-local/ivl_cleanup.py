"""IVL cleanup — remove committed probe artifacts from ai003-verify.localhost and verify absence."""
import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

USER = "ai003-ivl-replay@verify.local"
for nm in frappe.get_all("User Permission", filters={"user": USER}, pluck="name"):
    frappe.delete_doc("User Permission", nm, ignore_permissions=True)
frappe.db.commit()
if frappe.db.exists("User", USER):
    frappe.delete_doc("User", USER, ignore_permissions=True)
    frappe.db.commit()

checks = {
    "replay_user_absent": not frappe.db.exists("User", USER),
    "phase_a_user_absent": not frappe.db.exists("User", "ai003-ivl-probe@verify.local"),
    "custom_role_absent": not frappe.get_all("Custom Role", filters={"report": "Accounts Receivable"}, pluck="name"),
    "user_permissions_absent": not frappe.get_all("User Permission", filters={"user": ["like", "ai003-ivl%"]}, pluck="name"),
    "transient_ivl_vouchers_absent": not frappe.get_all("Sales Invoice", filters={"remarks": ["like", "AI003_IVL%"]}, pluck="name"),
    "transient_customer_absent": not frappe.db.exists("Customer", "AI003 IVL Temp Customer"),
    "gold_company_intact": frappe.db.count("Sales Invoice", {"company": "AI003 Gold 2026", "docstatus": 1}),
    "a2f_fixture_intact": frappe.db.count("Sales Invoice", {"company": "AI002 Fixture 2026", "docstatus": 1}),
}
for k, v in checks.items():
    print(f"{k}: {v}")
assert all(v for k, v in checks.items() if k.endswith("_absent"))
frappe.db.rollback()
frappe.destroy()
print("CLEANUP_OK")
