"""AI003 HTTP permission revoke/regrant live verification (state-preserving).

Verifies:
1. A per-run restricted user (unique email) with company permission and
   Accounts User role logs in via HTTP
2. Evaluates AP_DUE_CLUSTER, obtains evidence ref
3. Authorized evidence replay -> MATCH, valid payload
4. Revoke report permission via Custom Role (Accounts Payable -> Accounts Manager)
5. Replay evidence -> FORBIDDEN, payload is None, no financial leakage
6. Restore report permission (delete ONLY the role this run created)
7. Replay evidence -> MATCH restored
8. Cleanup deletes ONLY artifacts this run created (user, role, permission),
   inside a finally block; pre-existing users/roles are snapshotted before any
   mutation and asserted unchanged afterwards.

If a pre-existing AP Custom Role is present, the harness ABORTS before any
mutation (conflict detected up front) instead of forcing the site state.
No blanket clear-cache and no blanket deletions are ever issued.
"""

import http.cookiejar
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import uuid

HOST_HEADER = "ai003-verify.localhost"
BASE_URL = "http://127.0.0.1:8080"
COMPANY = "AI003 MG AP"

# Unique per run — a pre-existing user with any email is never touched.
TEST_PASS = "LotusFinSecurity2026!#Strong"
RUN_ID = uuid.uuid4().hex[:10]
TEST_USER = f"ai003_sec_{RUN_ID}@example.com"

# Artifacts created by THIS run, in creation order (names from the backend).
CREATED = {"user": None, "perm": None, "role": None}
# Site state snapshotted before any mutation.
PRE_STATE = {"ap_custom_roles": [], "user_existed": False}
CLEANED = False


class HarnessAbort(Exception):
    """Raised BEFORE any mutation when pre-existing state conflicts."""


def run_in_backend(py_code: str) -> str:
    cmd = [
        "docker", "exec", "-w", "/home/frappe/frappe-bench/sites",
        "frappe_docker-backend-1",
        "/home/frappe/frappe-bench/env/bin/python", "-c",
        f"import frappe; frappe.init('{HOST_HEADER}'); frappe.connect()\n" + py_code
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"backend snippet failed:\n{res.stderr}")
    return res.stdout.strip()


def snapshot_and_check_preconditions():
    """Record pre-existing state and abort (no mutation) on conflict."""
    global PRE_STATE
    out = run_in_backend("""
import json
roles = []
for name in frappe.get_all('Custom Role', filters={'report': 'Accounts Payable'}, pluck='name'):
    doc = frappe.get_doc('Custom Role', name)
    roles.append({'name': name, 'ref_doctype': doc.ref_doctype,
                  'roles': sorted(r.role for r in doc.roles)})
print(json.dumps({
    'ap_custom_roles': roles,
    'user_existed': bool(frappe.db.exists('User', %r)),
}))
""" % TEST_USER)
    PRE_STATE = json.loads(out.splitlines()[-1])
    if PRE_STATE["ap_custom_roles"]:
        raise HarnessAbort(
            "pre-existing AP Custom Role(s) present: "
            + ", ".join(r["name"] for r in PRE_STATE["ap_custom_roles"])
            + " — harness aborted BEFORE any mutation; resolve manually"
        )
    if PRE_STATE["user_existed"]:
        raise HarnessAbort(f"user {TEST_USER} unexpectedly exists; harness aborted BEFORE any mutation")
    print(f"   Pre-state: no AP Custom Role, user {TEST_USER} absent — safe to proceed")


def create_test_user():
    """Create THIS run's restricted user + company permission; track names."""
    out = run_in_backend(f"""
import json
from frappe.utils.password import update_password
USER = {TEST_USER!r}
C = {COMPANY!r}
if frappe.db.exists('User', USER):
    raise RuntimeError('refusing to reuse an existing user')
user = frappe.get_doc({{
    'doctype': 'User',
    'email': USER,
    'first_name': 'AI003 Security Test {RUN_ID}',
    'send_welcome_email': 0,
    'user_type': 'System User',
    'roles': [{{'role': 'Accounts User'}}],
}}).insert(ignore_permissions=True)
update_password(USER, {TEST_PASS!r})
perm = frappe.get_doc({{
    'doctype': 'User Permission',
    'user': USER,
    'allow': 'Company',
    'for_value': C,
    'apply_to_all_doctypes': 1,
}}).insert(ignore_permissions=True)
frappe.db.commit()
print(json.dumps({{'user': user.name, 'perm': perm.name}}))
""")
    created = json.loads(out.splitlines()[-1])
    CREATED["user"] = created["user"]
    CREATED["perm"] = created["perm"]
    print(f"   Created user {CREATED['user']} + permission {CREATED['perm']}")


def revoke_report_permission():
    """Revoke: insert one Custom Role for THIS run only."""
    out = run_in_backend("""
import json
cr = frappe.get_doc({
    'doctype': 'Custom Role',
    'report': 'Accounts Payable',
    'ref_doctype': 'Purchase Invoice',
    'roles': [{'role': 'Accounts Manager'}],
}).insert(ignore_permissions=True)
frappe.db.commit()
print(json.dumps({'role': cr.name}))
""")
    CREATED["role"] = json.loads(out.splitlines()[-1])["role"]
    print(f"   Created test Custom Role: {CREATED['role']}")
    return "REVOKED"


def restore_report_permission():
    """Restore: delete ONLY the role this run created."""
    if not CREATED["role"]:
        return "RESTORED_NOTHING_CREATED"
    run_in_backend(f"""
if frappe.db.exists('Custom Role', {CREATED['role']!r}):
    frappe.delete_doc('Custom Role', {CREATED['role']!r}, ignore_permissions=True)
frappe.db.commit()
print('DELETED_OWN_ROLE')
""")
    CREATED["role"] = None
    return "RESTORED"


def cleanup():
    """Delete ONLY artifacts this run created; verify pre-existing state back.
    Idempotent — safe to call from finally and on error paths."""
    global CLEANED
    if CLEANED:
        return
    CLEANED = True
    out = run_in_backend(f"""
import json
user, perm, role = {CREATED['user']!r}, {CREATED['perm']!r}, {CREATED['role']!r}
if perm and frappe.db.exists('User Permission', perm):
    frappe.delete_doc('User Permission', perm, ignore_permissions=True)
if user and frappe.db.exists('User', user):
    frappe.delete_doc('User', user, ignore_permissions=True)
if role and frappe.db.exists('Custom Role', role):
    frappe.delete_doc('Custom Role', role, ignore_permissions=True)
frappe.db.commit()
# Targeted per-user cache refresh only (no blanket clear-cache).
frappe.clear_cache(user=user) if user else None
print(json.dumps({{
    'user_gone': not frappe.db.exists('User', user) if user else True,
    'perm_gone': not frappe.db.exists('User Permission', perm) if perm else True,
    'role_gone': not frappe.db.exists('Custom Role', role) if role else True,
    'ap_roles_remaining': sorted(frappe.get_all('Custom Role', filters={{'report': 'Accounts Payable'}}, pluck='name')),
}}))
""")
    result = json.loads(out.splitlines()[-1])
    assert result["user_gone"] and result["perm_gone"] and result["role_gone"], result
    assert result["ap_roles_remaining"] == sorted(r["name"] for r in PRE_STATE["ap_custom_roles"]), result
    print(f"   Cleanup: own artifacts removed; AP Custom Roles match pre-state {result['ap_roles_remaining']}")


def verify_pre_state_unchanged():
    """Post-run assertion: pre-existing AP Custom Roles are byte-identical."""
    out = run_in_backend("""
import json
roles = []
for name in frappe.get_all('Custom Role', filters={'report': 'Accounts Payable'}, pluck='name'):
    doc = frappe.get_doc('Custom Role', name)
    roles.append({'name': name, 'ref_doctype': doc.ref_doctype,
                  'roles': sorted(r.role for r in doc.roles)})
print(json.dumps(roles))
""")
    now = json.loads(out.splitlines()[-1])
    assert now == PRE_STATE["ap_custom_roles"], (
        f"pre-existing AP Custom Roles changed!\nbefore={PRE_STATE['ap_custom_roles']}\nafter={now}"
    )
    print("   Pre-existing AP Custom Roles unchanged (before == after)")


def main():
    snapshot_and_check_preconditions()
    create_test_user()
    try:
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

        print("7. Restoring report permission (deleting only this run's Custom Role)...")
        restore_report_permission()

        print("8. Testing evidence replay after restore (expected MATCH)...")
        rep_res_restored = opener.open(replay_req)
        rep_body_restored = json.loads(rep_res_restored.read().decode())["message"]
        print(f"   Restored replay status: {rep_body_restored['status']}")
        assert rep_body_restored["status"] == "MATCH"
        assert rep_body_restored["payload"] is not None

        print("SECURITY REPLAY FLOW: PASS")
        return 0
    finally:
        try:
            cleanup()
            verify_pre_state_unchanged()
        except Exception as exc:
            print(f"CLEANUP VERIFICATION ERROR: {exc}")
            raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except HarnessAbort as e:
        print(f"HARNESS ABORT (no mutation performed): {e}")
        sys.exit(2)
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
