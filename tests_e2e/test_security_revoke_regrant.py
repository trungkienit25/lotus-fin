"""AI003 HTTP permission revoke/regrant live verification.

Verifies:
1. Restricted user with company permission and Accounts User role logs in via HTTP
2. Evaluates AP_DUE_CLUSTER, obtains evidence ref
3. Authorized evidence replay -> MATCH, valid payload
4. Revoke report permission via Custom Role (Accounts Payable restricted to Accounts Manager)
5. Replay evidence -> FORBIDDEN, payload is None, no financial leakage
6. Restore report permission (delete Custom Role)
7. Replay evidence -> MATCH restored
8. Clean up test user and roles
"""

import http.cookiejar
import json
import subprocess
import sys
import urllib.parse
import urllib.request

HOST_HEADER = "ai003-verify.localhost"
BASE_URL = "http://127.0.0.1:8080"
TEST_USER = "ai003_sec_user@example.com"
TEST_PASS = "LotusFinSecurity2026!#Strong"
COMPANY = "AI003 MG AP"

# Name of the Custom Role THIS harness created (if any). Only this exact doc
# is ever deleted; pre-existing Custom Roles/Users are snapshotted and never
# touched (no blanket AP Custom Role cleanup).
CREATED_ROLE = None
PREEXISTING_AP_ROLES = []


def run_in_backend(py_code: str) -> str:
    cmd = [
        "docker", "exec", "-w", "/home/frappe/frappe-bench/sites",
        "frappe_docker-backend-1",
        "/home/frappe/frappe-bench/env/bin/python", "-c",
        f"import frappe; frappe.init('{HOST_HEADER}'); frappe.connect()\n" + py_code
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def snapshot_ap_custom_roles():
    """Record pre-existing Custom Role docs for report='Accounts Payable' so
    the harness can prove it preserved them (it never deletes them)."""
    global PREEXISTING_AP_ROLES
    out = run_in_backend("""
import json
roles = []
for name in frappe.get_all('Custom Role', filters={'report': 'Accounts Payable'}, pluck='name'):
    doc = frappe.get_doc('Custom Role', name)
    roles.append({
        'name': name,
        'ref_doctype': doc.ref_doctype,
        'roles': sorted(r.role for r in doc.roles),
    })
print(json.dumps(roles))
""")
    PREEXISTING_AP_ROLES = json.loads(out)
    if PREEXISTING_AP_ROLES:
        print(f"   Snapshot: {len(PREEXISTING_AP_ROLES)} pre-existing AP Custom Role(s) preserved: "
              + ", ".join(r["name"] for r in PREEXISTING_AP_ROLES))
    else:
        print("   Snapshot: no pre-existing AP Custom Role on this site")
    return PREEXISTING_AP_ROLES


def setup_test_user():
    code = f"""
from frappe.utils.password import update_password
USER = '{TEST_USER}'
C = '{COMPANY}'
if frappe.db.exists('User', USER):
    frappe.delete_doc('User', USER, ignore_permissions=True)
frappe.db.commit()

user = frappe.get_doc({{
    'doctype': 'User',
    'email': USER,
    'first_name': 'AI003 Security Test',
    'send_welcome_email': 0,
    'user_type': 'System User',
    'roles': [{{'role': 'Accounts User'}}],
}}).insert(ignore_permissions=True)
update_password(USER, '{TEST_PASS}')

frappe.get_doc({{
    'doctype': 'User Permission',
    'user': USER,
    'allow': 'Company',
    'for_value': C,
    'apply_to_all_doctypes': 1,
}}).insert(ignore_permissions=True)
frappe.db.commit()
print('USER_CREATED')
"""
    return run_in_backend(code)


def revoke_report_permission():
    global CREATED_ROLE
    if PREEXISTING_AP_ROLES:
        raise RuntimeError(
            "pre-existing AP Custom Role(s) present; refusing to create a "
            "conflicting permission state or delete them — resolve manually"
        )
    out = run_in_backend("""
cr = frappe.get_doc({
    'doctype': 'Custom Role',
    'report': 'Accounts Payable',
    'ref_doctype': 'Purchase Invoice',
    'roles': [{'role': 'Accounts Manager'}],
}).insert(ignore_permissions=True)
frappe.db.commit()
print(cr.name)
""")
    CREATED_ROLE = out.splitlines()[-1]
    print(f"   Created test Custom Role: {CREATED_ROLE}")
    return "REVOKED"


def restore_report_permission():
    if not CREATED_ROLE:
        return "RESTORED_NOTHING_CREATED"
    run_in_backend(f"""
if frappe.db.exists('Custom Role', {CREATED_ROLE!r}):
    frappe.delete_doc('Custom Role', {CREATED_ROLE!r}, ignore_permissions=True)
frappe.db.commit()
print('DELETED_OWN_ROLE')
""")
    return "RESTORED"


def cleanup():
    global CREATED_ROLE
    # Never blanket-delete: only the artifacts this harness created.
    run_in_backend(f"""
import json
USER = {TEST_USER!r}
if frappe.db.exists('User', USER):
    frappe.delete_doc('User', USER, ignore_permissions=True)
if {CREATED_ROLE!r} and frappe.db.exists('Custom Role', {CREATED_ROLE!r}):
    frappe.delete_doc('Custom Role', {CREATED_ROLE!r}, ignore_permissions=True)
frappe.db.commit()
remaining = frappe.get_all('Custom Role', filters={{'report': 'Accounts Payable'}}, pluck='name')
print('REMAINING=' + json.dumps(sorted(remaining)))
""")
    CREATED_ROLE = None
    return "CLEANED"


def main():
    print("1. Snapshotting pre-existing AP Custom Roles and setting up restricted test user...")
    snapshot_ap_custom_roles()
    setup_test_user()

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    print("2. Logging in as restricted user via HTTP...")
    login_req = urllib.request.Request(
        f"{BASE_URL}/api/method/login",
        data=urllib.parse.urlencode({"usr": TEST_USER, "pwd": TEST_PASS}).encode(),
        headers={"Host": HOST_HEADER},
    )
    login_res = opener.open(login_req)
    assert login_res.status == 200, f"Login failed: {login_res.status}"

    print("3. Evaluating AP_DUE_CLUSTER to obtain evidence ref...")
    eval_req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal",
        data=urllib.parse.urlencode({
            "company": COMPANY,
            "signal_id": "AP_DUE_CLUSTER",
            "as_of_date": "2026-09-26",
        }).encode(),
        headers={"Host": HOST_HEADER},
    )
    eval_res = opener.open(eval_req)
    eval_body = json.loads(eval_res.read().decode())["message"]
    assert eval_body["status"] == "OK", f"Eval not OK: {eval_body}"
    ev_ref = eval_body["evidence"][0]["ref"]
    print(f"   Evidence ref obtained: {ev_ref}")

    print("4. Testing authorized evidence replay (expected MATCH)...")
    replay_req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal_evidence",
        data=urllib.parse.urlencode({"evidence_ref": ev_ref, "company": COMPANY}).encode(),
        headers={"Host": HOST_HEADER},
    )
    rep_res = opener.open(replay_req)
    rep_body = json.loads(rep_res.read().decode())["message"]
    print(f"   Authorized replay status: {rep_body['status']}")
    assert rep_body["status"] == "MATCH"
    assert rep_body["payload"] is not None

    print("5. Revoking report permission (Custom Role -> Accounts Manager)...")
    revoke_report_permission()

    print("6. Testing evidence replay while revoked (expected FORBIDDEN, no payload)...")
    rep_res_revoked = opener.open(replay_req)
    rep_body_revoked = json.loads(rep_res_revoked.read().decode())["message"]
    print(f"   Revoked replay status: {rep_body_revoked['status']}")
    assert rep_body_revoked["status"] == "FORBIDDEN"
    assert rep_body_revoked.get("payload") is None, "Payload MUST be None on FORBIDDEN!"

    print("7. Restoring report permission (deleting Custom Role)...")
    restore_report_permission()

    print("8. Testing evidence replay after restore (expected MATCH)...")
    rep_res_restored = opener.open(replay_req)
    rep_body_restored = json.loads(rep_res_restored.read().decode())["message"]
    print(f"   Restored replay status: {rep_body_restored['status']}")
    assert rep_body_restored["status"] == "MATCH"
    assert rep_body_restored["payload"] is not None

    print("9. Cleaning up...")
    cleanup()

    print("SECURITY REPLAY FLOW: PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR:", e)
        cleanup()
        sys.exit(1)
