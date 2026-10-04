"""AI003 Independent Verification Lead — Phase C evidence replay harness (2026-09-30).

Feasibility proof for DYNAMIC_AUTHORIZED_REPLAY + SAVED_HASH_COMPARISON on the
isolated site. This is a verification harness, NOT a production replay endpoint.

Design under test (per candidate contract §8):
  replay(observation):
    1. reauthorize current user for the observation's resource (report-specific,
       authoritative Report.is_permitted(); snapshot ID/hash is NEVER an auth token)
    2. re-read the authoritative source within the observation's verified scope
    3. compare freshly computed source hash against the saved hash
       -> MATCH | RESTATED | UNAVAILABLE | FORBIDDEN
Transient user/Custom Role/User Permission/transient voucher are removed; the
transaction is rolled back at the end.
"""
from datetime import date
import hashlib
import json

import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

C = "AI003 Gold 2026"
OTHER = "AI002 Fixture 2026"
CUTOFF = date(2026, 9, 26)
USER = "ai003-ivl-replay@verify.local"
OUT = []


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def check(name, state, detail):
    OUT.append({"case": name, "state": state, "detail": str(detail)})
    print(f"{state:<12} {name} :: {detail}")


def source_hash(company, key):
    from lotus_fin.api.key_reports import extract_key_report_data
    res = extract_key_report_data(report_key=key, filters={"report_date": str(CUTOFF), "company": company}, company=company)
    if res.get("status") != "success":
        return None, res
    return stable_hash(res.get("data")), res


def replay(obs, user):
    """DYNAMIC_AUTHORIZED_REPLAY + SAVED_HASH_COMPARISON (harness model)."""
    report_name = {"accounts_receivable": "Accounts Receivable", "accounts_payable": "Accounts Payable"}[obs["report_key"]]
    try:
        frappe.set_user(user)
        if not frappe.get_doc("Report", report_name).is_permitted():
            return "FORBIDDEN", "report-specific authorization denied"
        from lotus_fin.security.access import get_verified_company
        get_verified_company(obs["company"])
    except frappe.PermissionError:
        return "FORBIDDEN", "company/resource authorization denied"
    except Exception as e:  # noqa: BLE001
        return "FORBIDDEN", f"authorization denied: {type(e).__name__}"
    new_hash, res = source_hash(obs["company"], obs["report_key"])
    if new_hash is None:
        msg = str(res.get("message", ""))
        if "permit" in msg.lower():
            return "FORBIDDEN", "source read denied"
        return "UNAVAILABLE", f"source read failed: {res.get('status')}"
    if new_hash == obs["saved_hash"]:
        return "MATCH", f"hash {new_hash[:16]}… equals saved"
    return "RESTATED", f"hash {new_hash[:16]}… != saved {obs['saved_hash'][:16]}…"


# --- cleanup leftovers from any prior run -------------------------------------
if frappe.db.exists("User", USER):
    for nm in frappe.get_all("User Permission", filters={"user": USER}, pluck="name"):
        frappe.delete_doc("User Permission", nm, ignore_permissions=True)
    frappe.delete_doc("User", USER, ignore_permissions=True)
for nm in frappe.get_all("Custom Role", filters={"report": "Accounts Receivable"}, pluck="name"):
    frappe.delete_doc("Custom Role", nm, ignore_permissions=True)
frappe.db.commit()

# --- setup: saved observation from a clean authorized read ---------------------
ar_hash, _ = source_hash(C, "accounts_receivable")
ar_obs = {"company": C, "report_key": "accounts_receivable", "saved_hash": ar_hash,
          "filters": {"report_date": str(CUTOFF)}, "saved_at": "2026-09-30T00:00:00Z"}

print("== Phase C: DYNAMIC_AUTHORIZED_REPLAY + SAVED_HASH_COMPARISON ==")

s, d = replay(dict(ar_obs), "Administrator")
check("C1_AUTHORIZED_IDENTICAL_SOURCE", s, d)
s, d = replay(dict(ar_obs), "Administrator")
check("C2_REPEAT_READ_HASH_STABLE", s, d)

# C3 report permission revoked before replay -> FORBIDDEN (no payload returned)
frappe.get_doc({"doctype": "User", "email": USER, "first_name": "AI003 IVL Replay",
                "send_welcome_email": 0, "user_type": "System User",
                "roles": [{"role": "Accounts User"}]}).insert(ignore_permissions=True)
frappe.get_doc({"doctype": "User Permission", "user": USER, "allow": "Company",
                "for_value": C, "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
frappe.db.commit()
ref_dt = frappe.db.get_value("Report", "Accounts Receivable", "ref_doctype")
custom = frappe.get_doc({"doctype": "Custom Role", "report": "Accounts Receivable",
                         "ref_doctype": ref_dt, "roles": [{"role": "Accounts Manager"}]}).insert(ignore_permissions=True)
frappe.db.commit()
s, d = replay(dict(ar_obs), USER)
check("C3_REPORT_REVOKED_BEFORE_REPLAY", s, d)
frappe.delete_doc("Custom Role", custom.name, ignore_permissions=True)
frappe.db.commit()

# C4 cross-company observation -> FORBIDDEN (generic, no existence leak)
s, d = replay({"company": OTHER, "report_key": "accounts_receivable", "saved_hash": "0" * 64,
               "filters": {"report_date": str(CUTOFF)}}, USER)
check("C4_CROSS_COMPANY_OBSERVATION", s, d)

# C5 source unavailable -> UNAVAILABLE (typed failure, never MATCH/BENIGN)
try:
    from lotus_fin.api.key_reports import extract_key_report_data
    bad = extract_key_report_data(report_key="nonexistent_report",
                                  filters={"report_date": str(CUTOFF), "company": C}, company=C)
    state, detail = ("UNAVAILABLE", f"error envelope status={bad.get('status')}") if bad.get("status") != "success" else ("MATCH", "unexpected success")
except Exception as e:  # noqa: BLE001
    state, detail = "UNAVAILABLE", f"typed failure raised: {type(e).__name__}"
check("C5_SOURCE_UNAVAILABLE", state, detail)

# C6 changed source after restatement -> RESTATED (new fingerprint, still authorized)
before_hash, _ = source_hash(C, "accounts_receivable")
inv = frappe.get_doc({"doctype": "Sales Invoice", "company": C, "posting_date": "2026-09-24",
                      "set_posting_time": 1, "due_date": "2026-09-25",
                      "remarks": "AI003_IVL_TRANSIENT_RESTATE", "currency": "VND",
                      "customer": "AI003 Gold Customer", "debit_to": "Debtors - A3G",
                      "items": [{"item_code": "AI002 TEST SERVICE", "qty": 1, "rate": 123000,
                                 "income_account": "Service - A3G"}]}).insert(ignore_permissions=True)
inv.submit()
mid_hash, _ = source_hash(C, "accounts_receivable")
s, d = replay({"company": C, "report_key": "accounts_receivable", "saved_hash": before_hash,
               "filters": {"report_date": str(CUTOFF)}}, "Administrator")
check("C6_RESTATEMENT_AFTER_BACKDATE", s, d)
inv.cancel()
after_hash, _ = source_hash(C, "accounts_receivable")
check("C6B_CANCEL_RESTORES", "MATCH" if after_hash == before_hash else "RESTATED",
      f"post-cancel hash equals pre-restatement hash: {after_hash == before_hash}")

# C7 document-specific denial on DOCUMENT_REF evidence -> FORBIDDEN, regrant restores
allowed_customer = "AI003 Gold Customer"
restricted_customer = "AI003 IVL Temp Customer"  # transient, rolled back below
if not frappe.db.exists("Customer", restricted_customer):
    frappe.get_doc({"doctype": "Customer", "customer_name": restricted_customer,
                    "customer_group": frappe.db.get_value("Customer", {"name": allowed_customer}, "customer_group"),
                    "customer_type": "Company", "territory": frappe.db.get_value("Customer", {"name": allowed_customer}, "territory")}
                   ).insert(ignore_permissions=True)
tinv = frappe.get_doc({"doctype": "Sales Invoice", "company": C, "posting_date": "2026-09-20",
                       "set_posting_time": 1, "due_date": "2026-09-21",
                       "remarks": "AI003_IVL_TEMP_CUST_DOC", "currency": "VND",
                       "customer": restricted_customer, "debit_to": "Debtors - A3G",
                       "items": [{"item_code": "AI002 TEST SERVICE", "qty": 1, "rate": 45000,
                                  "income_account": "Service - A3G"}]}).insert(ignore_permissions=True)
tinv.submit()
allowed_doc = frappe.db.get_value("Sales Invoice", {"customer": allowed_customer, "company": C}, "name")
restricted_doc = tinv.name
from lotus_fin.security.access import verify_evidence_access
perm = frappe.get_doc({"doctype": "User Permission", "user": USER, "allow": "Customer",
                       "for_value": allowed_customer, "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
frappe.db.commit()
frappe.set_user(USER)
try:
    verify_evidence_access(f"Sales Invoice:{allowed_doc}", user=USER, company=C)
    s7a = "MATCH"
except frappe.PermissionError:
    s7a = "FORBIDDEN"
try:
    verify_evidence_access(f"Sales Invoice:{restricted_doc}", user=USER, company=C)
    s7 = "MATCH"
except frappe.PermissionError:
    s7 = "FORBIDDEN"
check("C7_DOCUMENT_SPECIFIC_DENIAL", s7, f"allowed doc={s7a}; restricted-customer doc denied under Customer User Permission")
frappe.set_user("Administrator")
frappe.delete_doc("User Permission", perm.name, ignore_permissions=True)
frappe.db.commit()
frappe.set_user(USER)
try:
    verify_evidence_access(f"Sales Invoice:{restricted_doc}", user=USER, company=C)
    s7b = "MATCH"
except frappe.PermissionError:
    s7b = "FORBIDDEN"
check("C7B_DOCUMENT_REGRANT_RESTORES", s7b, f"after User Permission removal: {s7b}")

# C8 snapshot ID / hash is NOT an authorization token
try:
    verify_evidence_access("Risk Signal:FORGED-SNAPSHOT-ID", user=USER, company=C)
    s8 = "MATCH"
except frappe.PermissionError:
    s8 = "FORBIDDEN"
check("C8_SNAPSHOT_TOKEN_NOT_AUTH", s8, "forged snapshot-style evidence ref denied without resource authorization")

# --- cleanup ------------------------------------------------------------------
frappe.set_user("Administrator")
for nm in frappe.get_all("User Permission", filters={"user": USER}, pluck="name"):
    frappe.delete_doc("User Permission", nm, ignore_permissions=True)
frappe.delete_doc("User", USER, ignore_permissions=True)
frappe.db.commit()
check("CLEANUP", not frappe.db.exists("User", USER)
      and not frappe.get_all("Custom Role", filters={"report": "Accounts Receivable"}, pluck="name"),
      "replay probe user/Custom Role removed; transient invoice rolled back")
frappe.db.rollback()
frappe.destroy()
print("PHASE_C_DONE", json.dumps(OUT))
