"""Read-only framework qualification; no business records or Administrator fallback."""
import importlib
import importlib.util
import json
import os
import pathlib
import frappe

os.chdir('/home/frappe/frappe-bench/sites')
frappe.init(site=os.environ['LOTUS_SITE'])
try:
    frappe.connect()
    apps = frappe.get_installed_apps()
    assert set(apps) == {'frappe', 'lotus_fin'}, apps
    assert importlib.util.find_spec('erpnext') is None
    for module in ('lotus_fin.hooks', 'lotus_fin.runtime.boundary',
                   'lotus_fin.runtime.health', 'lotus_fin.api.invoice_actions_api',
                   'lotus_fin.application.service.search_invoices',
                   'lotus_fin.application.service.open_authorized_invoice'):
        importlib.import_module(module)
    assert frappe.get_hooks('doc_events', app_name='lotus_fin') == {}
    assert frappe.get_hooks('scheduler_events', app_name='lotus_fin') == {}
    assert not frappe.db.exists('DocType', 'Sales Invoice')
    assert not frappe.db.exists('DocType', 'Company')
    frappe.db.sql('select 1')
    frappe.cache.ping()
    assert pathlib.Path(frappe.get_app_path('lotus_fin', 'templates', 'lotus_spa.html')).is_file()
    assert not pathlib.Path('assets/lotus_fin/core/index.html').exists()
    assert list(pathlib.Path('assets/lotus_fin/core/assets').glob('*.js'))
    print(json.dumps({'apps': apps, 'frappe_only': True, 'core_checks': 'PASS',
                      'business_independence': 'NOT_QUALIFIED'}))
finally:
    frappe.destroy()
