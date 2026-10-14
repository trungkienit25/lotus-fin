"""Recheck qualification before each optional event, including scheduled jobs."""
import frappe


def _qualified_events():
    if (frappe.conf.get('lotus_erpnext_integration_qualified') is not True
            or not {'erpnext', 'lotus_erpnext'}.issubset(frappe.get_installed_apps())):
        frappe.throw('ERP integration qualification is unavailable', frappe.PermissionError)
    from lotus_fin.api import events
    return events


def sales_invoice_submit(doc, method=None):
    return _qualified_events().on_sales_invoice_submit(doc, method)


def payment_entry_submit(doc, method=None):
    return _qualified_events().on_payment_entry_submit(doc, method)


def daily_cashflow_digest():
    return _qualified_events().generate_daily_cashflow_digest()


def weekly_financial_health():
    return _qualified_events().evaluate_sme_financial_health()
