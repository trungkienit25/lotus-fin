import frappe


def require_qualification():
    if (frappe.conf.get("lotus_erpnext_integration_qualified") is not True
            or "erpnext" not in frappe.get_installed_apps()):
        frappe.throw("ERP integration requires separate site qualification", frappe.ValidationError)
