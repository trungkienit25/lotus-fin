"""Corrected PB-DATA-02 AP measurement: AP-only baseline vs AP-only + exact duplicate."""
from datetime import date
import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

C = "AI003 Gold 2026"
CUTOFF = date(2026, 9, 26)

from lotus_fin.api.key_reports import extract_key_report_data
from lotus_fin.cashflow.adapters import _collect_obligations

ap_src = extract_key_report_data(report_key="accounts_payable",
                                 filters={"report_date": str(CUTOFF), "company": C}, company=C)
ap_rows = [dict(r) for r in ap_src["data"]]
field = next((k for k in ("outstanding_amount", "outstanding") if k in ap_rows[0]), None)
pos = next(r for r in ap_rows if r.get(field) is not None and float(r[field]) > 0)

base = _collect_obligations({"status": "success", "data": ap_rows}, "AP",
                            ("party", "supplier", "supplier_name"), "Purchase Invoice", "VND",
                            "Accounts Payable", company=C)
dup = _collect_obligations({"status": "success", "data": ap_rows + [dict(pos)]}, "AP",
                           ("party", "supplier", "supplier_name"), "Purchase Invoice", "VND",
                           "Accounts Payable", company=C)
refs = [o.source_ref for o in dup]
dup_ref = next(o.source_ref for o in dup if refs.count(o.source_ref) > 1)
print(f"AP_BASELINE={len(base)} AP_WITH_EXACT_DUPLICATE={len(dup)} REPEATED_SOURCE_REF={dup_ref}")
print("PB_DATA_02_AP_CONFIRMED" if len(dup) == len(base) + 1 else "PB_DATA_02_AP_NOT_REPRODUCED")
frappe.db.rollback()
frappe.destroy()
