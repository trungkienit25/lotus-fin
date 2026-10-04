"""IVL cleanup pass 4 — cancel submitted transient invoices, verify gold restored."""
import sys
from datetime import date
from decimal import Decimal
import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

for row in frappe.get_all("Sales Invoice", filters={"remarks": ["like", "AI003_IVL%"], "docstatus": 1},
                          fields=["name", "remarks"]):
    doc = frappe.get_doc("Sales Invoice", row.name)
    doc.cancel()
    print("cancelled:", row.name, row.remarks)
frappe.db.commit()

sys.path.insert(0, "/tmp")
from prebuild_oracle import voucher_oracle
C = "AI003 Gold 2026"
expected = {
    date(2026, 9, 20): {"total_ar": "650000", "overdue_ar": "0", "ap_short": "1400000", "ap_horizon": "1950000"},
    date(2026, 9, 26): {"total_ar": "565000", "overdue_ar": "65000", "ap_short": "275000", "ap_horizon": "975000"},
}
all_ok = True
for cutoff, exp in expected.items():
    o = voucher_oracle(frappe.db, C, cutoff)
    ok = all(Decimal(o[k]) == Decimal(v) for k, v in exp.items())
    all_ok = all_ok and ok
    print(f"GOLD_{cutoff.strftime('%Y%m%d')}: {'RESTORED' if ok else 'CHANGED'} "
          f"(total_ar={o['total_ar']} overdue={o['overdue_ar']} ap_short={o['ap_short']} ap_horizon={o['ap_horizon']})")

residue = frappe.get_all("Sales Invoice", filters={"remarks": ["like", "AI003_IVL%"]}, fields=["name", "docstatus"])
submitted_left = [r.name for r in residue if r.docstatus == 1]
print("residue_cancelled_docs:", [(r.name, r.docstatus) for r in residue])
print("probe_users:", frappe.get_all("User", filters={"email": ["like", "ai003-ivl%"]}, pluck="email"))
print("custom_roles:", frappe.get_all("Custom Role", filters={"report": "Accounts Receivable"}, pluck="name"))
print("submitted_transient_left:", submitted_left)
print("FINAL_STATE_OK" if all_ok and not submitted_left else "FINAL_STATE_INCOMPLETE")
frappe.db.rollback()
frappe.destroy()
