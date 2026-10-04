"""IVL cleanup pass 3 — final state: remove temp customer, prove gold numbers unchanged."""
import sys
from datetime import date
from decimal import Decimal
import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

# temp customer: only deletable if no submitted/linked docs remain
try:
    linked = frappe.get_all("Sales Invoice", filters={"customer": "AI003 IVL Temp Customer"}, pluck="name")
    if not linked and frappe.db.exists("Customer", "AI003 IVL Temp Customer"):
        frappe.delete_doc("Customer", "AI003 IVL Temp Customer", ignore_permissions=True)
        frappe.db.commit()
        print("temp_customer: deleted")
    else:
        print("temp_customer: kept (linked docs:", linked, ")")
except Exception as e:
    print("temp_customer: kept (", type(e).__name__, str(e)[:120], ")")

residue = frappe.get_all("Sales Invoice", filters={"remarks": ["like", "AI003_IVL%"]},
                         fields=["name", "docstatus", "customer", "remarks"])
print("residue:", [(r.name, r.docstatus) for r in residue])

sys.path.insert(0, "/tmp")
from prebuild_oracle import voucher_oracle
C = "AI003 Gold 2026"
expected = {
    date(2026, 9, 20): {"total_ar": "650000", "overdue_ar": "0", "ap_short": "1400000", "ap_horizon": "1950000"},
    date(2026, 9, 26): {"total_ar": "565000", "overdue_ar": "65000", "ap_short": "275000", "ap_horizon": "975000"},
}
for cutoff, exp in expected.items():
    o = voucher_oracle(frappe.db, C, cutoff)
    ok = all(Decimal(o[k]) == Decimal(v) for k, v in exp.items())
    print(f"GOLD_AFTER_CLEANUP_{cutoff.strftime('%Y%m%d')}: {'UNCHANGED' if ok else 'CHANGED'} "
          f"(total_ar={o['total_ar']} overdue={o['overdue_ar']} ap_short={o['ap_short']} ap_horizon={o['ap_horizon']})")
    assert ok, "GOLD CHANGED - cleanup must be reviewed"

users = frappe.get_all("User", filters={"email": ["like", "ai003-ivl%"]}, pluck="email")
print("probe_users:", users)
print("custom_roles:", frappe.get_all("Custom Role", filters={"report": "Accounts Receivable"}, pluck="name"))
frappe.db.rollback()
frappe.destroy()
print("FINAL_STATE_OK")
