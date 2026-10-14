"""Explicit isolated-test provisioning, never called by read-only smoke."""
import os
import re
import frappe

site = os.environ['LOTUS_SITE']
assert re.fullmatch(r'core-[a-z0-9-]+\.localhost', site)
os.chdir('/home/frappe/frappe-bench/sites')
frappe.init(site=site)
try:
    frappe.connect()
    assert set(frappe.get_installed_apps()) == {'frappe', 'lotus_fin'}
    assert not frappe.db.exists('User', 'qa-core@example.invalid')
    # Explicit operational bootstrap identity, never a business-request fallback.
    frappe.set_user('Administrator')
    if not frappe.db.exists('Role', 'Lotus Core QA'):
        frappe.get_doc({'doctype': 'Role', 'role_name': 'Lotus Core QA',
                        'desk_access': 1}).insert()
    user = frappe.get_doc({'doctype': 'User', 'email': 'qa-core@example.invalid',
        'first_name': 'Isolated QA', 'enabled': 1, 'user_type': 'System User',
        'roles': [{'role': 'Lotus Core QA'}],
        'send_welcome_email': 0, 'new_password': os.environ['LOTUS_QA_PASSWORD']})
    user.insert()
    frappe.db.commit()
    print('Ordinary isolated QA user provisioned; no business records created')
finally:
    frappe.destroy()
