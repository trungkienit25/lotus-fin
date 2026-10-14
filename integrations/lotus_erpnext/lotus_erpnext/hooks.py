app_name = "lotus_erpnext"
app_title = "Lotus ERPNext Integration"
app_publisher = "Lotus Fin Team"
app_email = "dev@lotusfin.vn"
app_license = "MIT"
required_apps = ["erpnext", "lotus_fin"]
before_install = "lotus_erpnext.install.require_qualification"
doc_events = {
    "Sales Invoice": {"on_submit": "lotus_erpnext.events.sales_invoice_submit"},
    "Payment Entry": {"on_submit": "lotus_erpnext.events.payment_entry_submit"},
}
scheduler_events = {
    "daily": ["lotus_erpnext.events.daily_cashflow_digest"],
    "weekly": ["lotus_erpnext.events.weekly_financial_health"],
}
persistent_cache_keys = ["ai003:evidence"]
fixtures = [{"doctype": "Custom Field",
             "filters": [["name", "=", "Company-ai002_approved_cash_accounts"]]}]
