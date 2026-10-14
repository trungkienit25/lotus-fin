"""Authenticated readiness using framework services, without business records."""
import importlib.util
import frappe


@frappe.whitelist(allow_guest=False, methods=["GET"])
def readiness():
    apps = frappe.get_installed_apps()
    if "erpnext" in apps or importlib.util.find_spec("erpnext") is not None:
        frappe.throw("Core runtime has an unexpected application", frappe.ValidationError)
    frappe.db.sql("select 1")
    frappe.cache.ping()
    return {"core_runtime": "ready", "apps": apps,
            "financial_capabilities": "unqualified"}
