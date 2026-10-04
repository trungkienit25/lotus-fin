"""Read-only, sanitized isolated-site alignment evidence."""
import json
from pathlib import Path
import frappe
import erpnext
import lotus_fin

frappe.init(site='ai003-verify.localhost', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()
try:
    result = {
        'site': frappe.local.site,
        'versions': {'frappe': frappe.__version__, 'erpnext': erpnext.__version__, 'lotus_fin': lotus_fin.__version__},
        'installed_apps': frappe.get_installed_apps(),
        'timezone': frappe.db.get_single_value('System Settings', 'time_zone'),
        'scope_column': frappe.db.has_column('Company', 'ai002_approved_cash_accounts'),
        'gold_currency': frappe.db.get_value('Company','AI003 Gold 2026','default_currency'),
        'gold_cash_scope': frappe.db.get_value('Company','AI003 Gold 2026','ai002_approved_cash_accounts'),
        'site_config': {'developer_mode': frappe.conf.get('developer_mode'), 'db_type': frappe.conf.get('db_type')},
        'gold_counts': {dt: frappe.db.count(dt,{'company':'AI003 Gold 2026','docstatus':1})
                        for dt in ('Sales Invoice','Purchase Invoice','Payment Entry','Journal Entry')},
    }
    Path('/tmp/AI003_FINAL_ENVIRONMENT_2026-09-30.json').write_text(json.dumps(result,indent=2,default=str))
    print(json.dumps(result,default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
