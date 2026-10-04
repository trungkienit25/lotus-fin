"""Independent retest against the existing isolated verification site only."""
import importlib
import json
import sys
import unittest
from pathlib import Path

SITE = "ai003-verify.localhost"
SITES = "/home/frappe/frappe-bench/sites"


def init_isolated():
    import frappe
    original = frappe.init
    calls = []
    def isolated_init(site=None, *args, **kwargs):
        if site not in (None, "frontend", SITE):
            raise RuntimeError("Unexpected site requested")
        calls.append({"requested": site, "actual": SITE})
        kwargs["sites_path"] = SITES
        return original(SITE, *args, **kwargs)
    frappe.init = isolated_init
    frappe.init(SITE)
    frappe.connect()
    assert frappe.local.site == SITE
    frappe.set_user("Administrator")
    import lotus_fin
    assert str(Path(lotus_fin.__file__).resolve()).startswith("/review/")
    return frappe, calls


def environment():
    frappe, calls = init_isolated()
    try:
        print(json.dumps({
            "site": frappe.local.site, "python": sys.version,
            "installed_apps": frappe.get_installed_apps(),
            "companies": frappe.get_all("Company", pluck="name"),
            "demo_invoice_present": bool(frappe.db.exists("Sales Invoice", "ACC-SINV-2026-00003")),
            "page_present": bool(frappe.db.exists("Page", "financial-health")),
            "gl_company_years": frappe.db.sql("select company,year(posting_date),count(*) from `tabGL Entry` group by company,year(posting_date)", as_list=True),
            "scope_column": frappe.db.has_column("Company", "ai002_approved_cash_accounts"),
            "init_calls": calls,
        }, indent=2, default=str))
    finally:
        frappe.db.rollback()
        frappe.destroy()


def suites(current_tests=False):
    frappe, calls = init_isolated()
    try:
        names = ["lotus_fin.tests.test_access_and_reports", "lotus_fin.tests.test_security_hardening",
                 "lotus_fin.tests.test_workspace_ui"]
        if current_tests:
            # Compare the same test source against approved-baseline production.
            import importlib.util
            for name in names:
                file = Path("/review/lotus_fin/lotus_fin/tests") / (name.rsplit(".", 1)[-1] + ".py")
                spec = importlib.util.spec_from_file_location(name, file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromNames(names)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        print(json.dumps({"site": SITE, "init_calls": calls, "tests": result.testsRun,
                          "failures": len(result.failures), "errors": len(result.errors),
                          "skipped": len(result.skipped)}))
        return int(not result.wasSuccessful())
    finally:
        frappe.db.rollback()
        frappe.destroy()


def public_smoke():
    frappe, calls = init_isolated()
    from unittest.mock import patch
    from lotus_fin.api.ai_insights import get_financial_snapshot
    from lotus_fin.api.cashflow_api import get_ai002_cash_account_scope
    company = "AI003 Gold 2026"
    try:
        def controlled(report_key, filters=None, company=None):
            rows = {"profit_and_loss": [{"account_name": "Sales Revenue", "balance": 100},
                                        {"account_name": "Cost of Goods Sold", "balance": 0}],
                    "accounts_receivable": [], "accounts_payable": [],
                    "trial_balance": [{"account_type": "Cash", "balance": 100}]}
            return {"status": "success", "company": company, "data": rows[report_key]}
        with patch("lotus_fin.api.ai_insights.extract_key_report_data", side_effect=controlled):
            zero = get_financial_snapshot(company=company, period_start="2026-01-01",
                period_end="2026-12-31", as_of="2026-09-26", correlation_id="public-zero-cogs")
        margin = next(m for m in zero["metrics"] if m["metric_id"] == "gross_margin")
        assert zero["status"] == "OK" and margin["status"] == "AVAILABLE" and margin["value"] == 1.0
        assert zero["contract_version"] == "1.0.0" and zero["correlation_id"] == "public-zero-cogs"
        assert all(e["filters"].get("company") == company and "source_record_id" in e for e in zero["evidence_refs"])
        assert all(m["formula_version"] == "2026.1" for m in zero["metrics"])
        live = get_financial_snapshot(company=company, period_start="2026-01-01", period_end="2026-12-31", as_of="2026-09-26")
        scope = get_ai002_cash_account_scope(company=company)
        print(json.dumps({"site": frappe.local.site, "app_file": __import__('lotus_fin').__file__,
            "controlled_public_zero_cogs": {"status": zero["status"], "margin": margin["value"]},
            "live_snapshot": {"status": live["status"], "contract_version": live["contract_version"],
                              "metrics": [{k:m.get(k) for k in ("metric_id","status","value","limitations")} for m in live["metrics"]],
                              "limitations": live["limitations"]},
            "live_cash_scope": scope, "init_calls": calls}, indent=2, default=str))
        return 0
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == "__main__":
    mode = sys.argv[1]
    sys.exit(public_smoke() if mode == "public-smoke" else suites(mode == "same-tests") if mode in ("suites", "same-tests") else environment())
