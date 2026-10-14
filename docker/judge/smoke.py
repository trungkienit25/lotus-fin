"""Read-only smoke in the installed bench environment; failures exit nonzero."""
import importlib
import json
import os
import sys
import frappe
import lotus_fin

MODULES = (
    'lotus_fin.hooks', 'lotus_fin.api.ai_insights', 'lotus_fin.api.copilot_api',
    'lotus_fin.modules.f001_health.service', 'lotus_fin.modules.f002_cashflow.service',
    'lotus_fin.modules.f003_risk_signal.service', 'lotus_fin.modules.f004_what_if.service',
    'lotus_fin.modules.f005_financing.service', 'lotus_fin.modules.f006_repayment.service',
    'lotus_fin.modules.f007_copilot.service', 'lotus_fin.AI005.service',
    'lotus_fin.AI006.service', 'lotus_fin.AI007.service',
)
site = os.environ['LOTUS_SITE']
# Frappe's logging paths are relative to the sites working directory.
os.chdir('/home/frappe/frappe-bench/sites')
frappe.init(site=site)
try:
    frappe.connect()
    apps = frappe.get_installed_apps()
    if 'lotus_fin' not in apps:
        raise RuntimeError(f'lotus_fin is not installed on site {site}; run setup first')
    for module in MODULES:
        importlib.import_module(module)
    print(json.dumps({'pass': True, 'site': site, 'python': sys.executable,
                      'package': lotus_fin.__file__, 'apps': apps, 'imports': list(MODULES)}))
finally:
    frappe.destroy()
