"""AI003 Independent Verification Lead — Phase A live probes (2026-09-30).

Independent re-verification on isolated site ai003-verify.localhost of:
  PB-SEC-01  report-specific Custom Role revoke does not stop AI002 cache payload
  PB-DATA-01 AR overdue metric AVAILABLE with missing due-date information
  PB-DATA-02 exact duplicate AR/AP rows double-count
Plus runtime sync checks and independent gold oracle re-run.

Creates one transient probe user + one Custom Role and deletes them; fixture
data is read-only. Ends with cleanup asserts. No AI001/AI002 code is modified.
"""
from datetime import date, timedelta
import json

import frappe

SITE = "ai003-verify.localhost"
frappe.init(site=SITE, sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

C = "AI003 Gold 2026"           # Work's persistent synthetic gold fixture
CUTOFF = date(2026, 9, 26)
USER = "ai003-ivl-probe@verify.local"
OUT = []


def check(name, ok, detail):
    OUT.append({"case": name, "result": "OK" if ok else "DEFECT", "detail": str(detail)})
    print(("OK      " if ok else "DEFECT  ") + name + " :: " + str(detail))


# ---------------------------------------------------------------- A1 runtime sync
print("== A1 runtime sync ==")
check("MIGRATION_SCOPE_COLUMN", frappe.db.has_column("Company", "ai002_approved_cash_accounts"), "Company.ai002_approved_cash_accounts present")
tz = frappe.db.get_single_value("System Settings", "time_zone")
check("ISOLATED_SITE_TIMEZONE", tz == "Asia/Ho_Chi_Minh", f"time_zone={tz}")
scope_cfg = frappe.db.get_value("Company", C, "ai002_approved_cash_accounts")
check("A3G_APPROVED_SCOPE_CONFIG", bool(scope_cfg), f"A3G approved scope config present={bool(scope_cfg)}")

# ---------------------------------------------------------------- A2 PB-SEC-01
print("== A2 PB-SEC-01 (report-specific revoke vs reusable guard + cache) ==")
from frappe.desk.query_report import run as report_run
from lotus_fin.api.key_reports import extract_key_report_data
from lotus_fin.security.access import check_ai002_report_permission
from lotus_fin.cashflow.cache import _CACHE_STORE
from lotus_fin.cashflow.models import ForecastRequest
from lotus_fin.cashflow.service import get_cash_forecast
from lotus_fin.cashflow.source_interface import FailClosedSource

# remove leftovers from any prior probe
for dt, flt in (("Custom Role", {"report": "Accounts Receivable"}), ("User Permission", {"user": USER})):
    for nm in frappe.get_all(dt, filters=flt, pluck="name"):
        frappe.delete_doc(dt, nm, ignore_permissions=True)
if frappe.db.exists("User", USER):
    frappe.delete_doc("User", USER, ignore_permissions=True)

frappe.get_doc({"doctype": "User", "email": USER, "first_name": "AI003 IVL Probe",
                "send_welcome_email": 0, "user_type": "System User",
                "roles": [{"role": "Accounts User"}]}).insert(ignore_permissions=True)
frappe.get_doc({"doctype": "User Permission", "user": USER, "allow": "Company",
                "for_value": C, "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)

frappe.set_user(USER)
pre = extract_key_report_data(report_key="accounts_receivable",
                              filters={"report_date": str(CUTOFF), "company": C}, company=C)
check("PRE_RESTRICTION_REPORT_AUTHORIZED", pre.get("status") == "success",
      f"AR report rows={pre.get('total_rows')} for probe user before Custom Role restriction")

req = ForecastRequest(company=C, financial_as_of=CUTOFF,
                      forecast_start=CUTOFF + timedelta(days=1),
                      forecast_end=CUTOFF + timedelta(days=30),
                      reporting_currency="VND", cash_account_scope=["Cash - A3G"])
first = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
first_state = (str(first.forecast_id), len(first.obligations),
               str(first.opening_cash.aggregate_amount) if first.opening_cash else None)
second = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
check("CACHE_POPULATED_FOR_PROBE_USER", bool(_CACHE_STORE) and str(second.forecast_id) == first_state[0],
      f"status={first.status.value} forecast_id={first_state[0]} obligations={first_state[1]} opening={first_state[2]}")

ref_dt = frappe.db.get_value("Report", "Accounts Receivable", "ref_doctype")
custom = frappe.get_doc({"doctype": "Custom Role", "report": "Accounts Receivable",
                         "ref_doctype": ref_dt,
                         "roles": [{"role": "Accounts Manager"}]}).insert(ignore_permissions=True)
frappe.db.commit()

authoritative = frappe.get_doc("Report", "Accounts Receivable").is_permitted()
check("REPORT_IS_PERMITTED_FALSE", not authoritative, f"Report.is_permitted()={authoritative} under Custom Role restriction")
direct_denied = False
try:
    report_run(report_name="Accounts Receivable", filters={"company": C, "report_date": str(CUTOFF)})
except Exception:
    direct_denied = True
check("DIRECT_REPORT_DENIED", direct_denied, "direct query_report.run refuses the denied report")

guard_passes = True
try:
    check_ai002_report_permission("Accounts Receivable", user=USER)
except Exception as e:
    guard_passes = False
    print("   guard raised:", type(e).__name__, e)
check("PB_SEC_01_GUARD_BLIND", guard_passes,
      "reusable report guard passes while authoritative report permission denies" if guard_passes
      else "guard denied (PB-SEC-01 absent)")

revoked = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
leak = (str(revoked.forecast_id) == first_state[0] and len(revoked.obligations) == first_state[1]
        and revoked.opening_cash is not None)
check("PB_SEC_01_CACHE_STALE_PAYLOAD", leak,
      f"revoked-request status={revoked.status.value} same_forecast_id={str(revoked.forecast_id) == first_state[0]} "
      f"obligations={len(revoked.obligations)} opening_cash={revoked.opening_cash is not None} "
      f"(safe behavior would be FORBIDDEN with empty payload)")

frappe.delete_doc("Custom Role", custom.name, ignore_permissions=True)
frappe.db.commit()
restored_perm = frappe.get_doc("Report", "Accounts Receivable").is_permitted()
regranted = get_cash_forecast(req, user=USER, future_event_source=FailClosedSource())
check("REGRANT_RESTORES_AUTHORIZED", restored_perm and len(regranted.obligations) == first_state[1],
      f"is_permitted={restored_perm} obligations={len(regranted.obligations)} after Custom Role removal")

frappe.set_user("Administrator")
frappe.delete_doc("User Permission", frappe.get_all("User Permission", filters={"user": USER}, pluck="name")[0], ignore_permissions=True)
frappe.delete_doc("User", USER, ignore_permissions=True)
frappe.db.commit()
check("PROBE_CLEANUP", not frappe.db.exists("User", USER)
      and not frappe.get_all("Custom Role", filters={"report": "Accounts Receivable"}, pluck="name"),
      "probe user and Custom Role removed")

# ---------------------------------------------------------------- A3 PB-DATA-01
print("== A3 PB-DATA-01 (AR overdue basis with missing due-date info) ==")
from lotus_fin.ai.financial_snapshot import parse_ar_data

src = extract_key_report_data(report_key="accounts_receivable",
                              filters={"report_date": str(CUTOFF), "company": C}, company=C)
rows = [dict(r) for r in src["data"]]
base_tot, base_over, base_ratio, _ = parse_ar_data([dict(r) for r in rows], as_of_date=CUTOFF, company=C, currency="VND")
check("AR_BASELINE_GOLD", str(base_tot) == "565000.00" and str(base_over) == "65000.00",
      f"total={base_tot} overdue={base_over} ratio={base_ratio} (gold: 565000 / 65000 / 0.11504)")

amount_field = next((k for k in ("outstanding_amount", "outstanding") if k in rows[0]), None)
pos_idx = next(i for i, r in enumerate(rows) if r.get(amount_field) is not None and float(r[amount_field]) > 0)
poisoned = [dict(r) for r in rows]
for k in ("due_date", "overdue", "overdue_amount"):
    poisoned[pos_idx].pop(k, None)
p_tot, p_over, p_ratio, _ = parse_ar_data(poisoned, as_of_date=CUTOFF, company=C, currency="VND")
check("PB_DATA_01_MISSING_DUEDATE_AVAILABLE", p_tot == base_tot and p_over != base_over,
      f"after stripping due/overdue from positive row: total={p_tot} (unchanged) overdue={p_over} "
      f"ratio={p_ratio} STILL AVAILABLE (positive overdue lost, credit overdue counted)")

# ---------------------------------------------------------------- A4 PB-DATA-02
print("== A4 PB-DATA-02 (exact duplicate rows double-count) ==")
dup_ar = dict(rows[pos_idx])
d_tot, d_over, d_ratio, _ = parse_ar_data([dict(r) for r in rows] + [dup_ar], as_of_date=CUTOFF, company=C, currency="VND")
check("PB_DATA_02_AR_DUPLICATE", str(d_tot) == "640000.00",
      f"AR total with exact duplicate appended = {d_tot} (gold 565000 + 75000 double-counted), still AVAILABLE")

from lotus_fin.cashflow.adapters import _collect_obligations, get_trade_obligations
obl = get_trade_obligations(C, CUTOFF)
n0 = len(obl)
ap_src = extract_key_report_data(report_key="accounts_payable",
                                 filters={"report_date": str(CUTOFF), "company": C}, company=C)
ap_rows = [dict(r) for r in ap_src["data"]]
ap_amount_field = next((k for k in ("outstanding_amount", "outstanding") if k in ap_rows[0]), None)
ap_pos = next(r for r in ap_rows if r.get(ap_amount_field) is not None and float(r[ap_amount_field]) > 0)
obl_dup = _collect_obligations({"status": "success", "data": ap_rows + [dict(ap_pos)]}, "AP",
                               ("party", "supplier", "supplier_name"), "Purchase Invoice", "VND",
                               "Accounts Payable", company=C)
check("PB_DATA_02_AP_DUPLICATE", len(obl_dup) == n0 + 1,
      f"AP obligations {n0} -> {len(obl_dup)} with exact duplicate row appended (repeated source_ref)")

# ---------------------------------------------------------------- A5 independent gold oracle re-run
print("== A5 independent gold oracle (voucher/Payment Ledger, no AI001/AI002 imports) ==")
import sys
sys.path.insert(0, "/tmp")
from prebuild_oracle import voucher_oracle
from decimal import Decimal

expected = {
    date(2026, 9, 20): {"total_ar": "650000", "overdue_ar": "0", "ap_short": "1400000", "ap_horizon": "1950000"},
    date(2026, 9, 26): {"total_ar": "565000", "overdue_ar": "65000", "ap_short": "275000", "ap_horizon": "975000"},
}
for cutoff, exp in expected.items():
    o = voucher_oracle(frappe.db, C, cutoff)
    ok = all(Decimal(o[k]) == Decimal(v) for k, v in exp.items())
    check(f"GOLD_ORACLE_{cutoff.strftime('%Y%m%d')}", ok,
          f"total_ar={o['total_ar']} overdue={o['overdue_ar']} ap_short={o['ap_short']} ap_horizon={o['ap_horizon']} "
          f"positive_residual={o['ar_positive_residual']} unallocated_credit={o['ar_unallocated_credit']}")

frappe.db.rollback()
frappe.destroy()
print("PHASE_A_DONE", json.dumps(OUT))
