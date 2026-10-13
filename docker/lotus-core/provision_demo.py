"""Explicit P6-only fictional demo setup. Never called on startup or shared sites."""
import os
import re
import frappe


def main():
    site = os.environ["LOTUS_SITE"]
    if not re.fullmatch(r"core-p6-[a-z0-9-]+\.localhost", site):
        raise ValueError("Only explicitly owned P6 isolated sites may enable this demo")
    os.chdir("/home/frappe/frappe-bench/sites")
    frappe.init(site=site)
    try:
        frappe.connect()
        assert set(frappe.get_installed_apps()) == {"frappe", "lotus_fin"}
        assert not frappe.db.exists("DocType", "Sales Invoice")
        frappe.set_user("Administrator")  # Explicit demo provisioning, never request fallback.
        for role in ("Accounts User", "Lotus Core QA"):
            if not frappe.db.exists("Role", role):
                frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()
        for email in ("p6-alice@example.invalid", "p6-bob@example.invalid"):
            if frappe.db.exists("User", email):
                raise ValueError("Refusing to overwrite an existing account")
            frappe.get_doc({"doctype": "User", "email": email, "first_name": "Fictional P6 Demo",
                "enabled": 1, "user_type": "System User", "send_welcome_email": 0,
                "roles": [{"role": "Accounts User"}, {"role": "Lotus Core QA"}],
                "new_password": os.environ["LOTUS_DEMO_PASSWORD"]}).insert()
        frappe.db.commit()
        print("Two fictional demo accounts created; no invoice/business schema or records")
    finally:
        frappe.destroy()


if __name__ == "__main__":
    main()
