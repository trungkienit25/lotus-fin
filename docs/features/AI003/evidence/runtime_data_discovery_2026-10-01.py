"""Read-only AI003 discovery. Output contains aggregates/schema, never raw invoices."""
import collections
import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import frappe
import erpnext
import lotus_fin

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")


def dec(value):
    return Decimal(str(value or 0))


def dates(values):
    parsed = []
    missing = malformed = 0
    for value in values:
        if not value:
            missing += 1
        else:
            try:
                parsed.append(date.fromisoformat(str(value)[:10]))
            except ValueError:
                malformed += 1
    return {"valid": len(parsed), "missing": missing, "malformed": malformed,
            "min": min(parsed) if parsed else None, "max": max(parsed) if parsed else None}


def report_summary(company, report, cutoff, terms=0):
    from frappe.desk.query_report import run
    filters = {"company": company, "report_date": cutoff, "based_on_payment_terms": terms,
               "ageing_based_on": "Due Date", "range": "30,60,90,120"}
    result = run(report, filters=filters, ignore_prepared_report=True)
    rows = [r for r in result.get("result", []) if isinstance(r, dict)]
    identities = collections.Counter((r.get("voucher_type"), r.get("voucher_no")) for r in rows)
    serialized = [json.dumps(r, sort_keys=True, default=str) for r in rows]
    amounts = [dec(r.get("outstanding")) for r in rows]
    return {"row_count": len(rows), "footer_rows": sum(not isinstance(r, dict) for r in result.get("result", [])),
            "column_fields": [c.get("fieldname") for c in result.get("columns", []) if isinstance(c, dict)],
            "row_keys": sorted({k for r in rows for k in r}),
            "field_present_count": {k: sum(r.get(k) is not None and r.get(k) != "" for r in rows)
                                    for k in ("voucher_no", "posting_date", "due_date", "outstanding", "currency", "company", "party", "status", "payment_term", "payment_terms", "party_account")},
            "due_dates": dates(r.get("due_date") for r in rows),
            "posting_dates": dates(r.get("posting_date") for r in rows),
            "currencies": sorted({str(r.get("currency")) for r in rows if r.get("currency")}),
            "net_outstanding": sum(amounts, Decimal(0)),
            "positive_outstanding": sum((a for a in amounts if a > 0), Decimal(0)),
            "negative_count": sum(a < 0 for a in amounts),
            "duplicate_voucher_groups": sum(n > 1 for n in identities.values()),
            "exact_duplicate_rows": len(serialized) - len(set(serialized)),
            "nested_payment_terms": {"parent_rows": sum(bool(r.get("payment_terms")) for r in rows),
                "term_count": sum(len(r.get("payment_terms") or []) for r in rows),
                "term_keys": sorted({k for r in rows for t in (r.get("payment_terms") or []) if isinstance(t, dict) for k in t})},
            "source_hash": hashlib.sha256(json.dumps(result.get("result", []), sort_keys=True, default=str).encode()).hexdigest()}


try:
    out = {"site": frappe.local.site, "app_path": lotus_fin.__file__,
           "versions": {"frappe": frappe.__version__, "erpnext": erpnext.__version__, "lotus_fin": lotus_fin.__version__},
           "installed_apps": frappe.get_installed_apps(),
           "timezone": frappe.db.get_single_value("System Settings", "time_zone"),
           "runtime_today": frappe.utils.nowdate(),
           "test_flags": {k: bool(getattr(frappe.flags, k, False)) for k in ("in_test", "ai002_use_fixture_source")},
           "metadata": {}, "companies": [], "reports": {}, "public_api": {}, "source_excerpts": {}}
    relevant_fields = {"name", "idx", "parent", "posting_date", "due_date", "outstanding_amount", "currency", "company", "customer", "supplier", "status", "docstatus", "is_return", "return_against", "amended_from", "payment_schedule", "payment_term", "invoice_portion", "payment_amount", "paid_amount", "discounted_amount", "payment_terms_template", "account", "account_currency", "amount", "amount_in_account_currency", "voucher_type", "voucher_no", "against_voucher_type", "against_voucher_no", "delinked", "finance_book"}
    for dt in ("Sales Invoice", "Purchase Invoice", "Payment Schedule", "Payment Ledger Entry", "GL Entry", "Company", "Version"):
        meta = frappe.get_meta(dt)
        out["metadata"][dt] = {"istable": meta.istable, "track_changes": meta.track_changes,
                               "fields": {f.fieldname: {"type": f.fieldtype, "options": f.options, "required": f.reqd}
                                          for f in meta.fields if f.fieldname in relevant_fields}}
    for report in ("Accounts Receivable", "Accounts Payable"):
        r = frappe.get_doc("Report", report)
        out["reports"][report] = {"type": r.report_type, "ref_doctype": r.ref_doctype,
                                  "is_standard": r.is_standard, "disabled": r.disabled,
                                  "administrator_permitted": bool(r.is_permitted())}
    companies = frappe.get_all("Company", fields=["name", "default_currency"])
    for company in companies:
        c = company.name
        summary = {"company_scope": c, "currency": company.default_currency, "invoices": {}, "report_cutoffs": {}}
        for dt in ("Sales Invoice", "Purchase Invoice"):
            records = frappe.get_all(dt, filters={"company": c}, fields=["name", "docstatus", "posting_date", "due_date", "currency", "outstanding_amount", "status", "is_return", "amended_from"])
            submitted = [r for r in records if r.docstatus == 1]
            children = frappe.get_all("Payment Schedule", filters={"parenttype": dt, "parent": ["in", [r.name for r in submitted]]}, fields=["parent", "name", "idx", "due_date", "payment_term", "payment_amount", "outstanding", "paid_amount"]) if submitted else []
            counts = collections.Counter(r.parent for r in children)
            summary["invoices"][dt] = {"count": len(records), "docstatus_counts": dict(collections.Counter(r.docstatus for r in records)),
                "submitted": len(submitted), "posting_dates": dates(r.posting_date for r in submitted),
                "due_dates": dates(r.due_date for r in submitted), "currencies": sorted({r.currency for r in submitted}),
                "statuses": dict(collections.Counter(r.status for r in submitted)), "returns": sum(bool(r.is_return) for r in submitted),
                "amended": sum(bool(r.amended_from) for r in submitted), "negative_outstanding": sum(dec(r.outstanding_amount) < 0 for r in submitted),
                "schedule_child_count": len(children), "invoices_with_multiple_schedule_rows": sum(n > 1 for n in counts.values()),
                "schedule_due_dates": dates(r.due_date for r in children), "schedule_term_present": sum(bool(r.payment_term) for r in children)}
        for cutoff in ("2026-01-31", "2026-06-30", "2026-08-31", "2026-09-20", "2026-09-26", "2026-09-30"):
            summary["report_cutoffs"][cutoff] = {}
            for report in out["reports"]:
                try:
                    summary["report_cutoffs"][cutoff][report] = report_summary(c, report, cutoff)
                except Exception as exc:
                    summary["report_cutoffs"][cutoff][report] = {"error_type": type(exc).__name__}
        summary["payment_term_reports"] = {report: report_summary(c, report, "2026-09-26", 1) for report in out["reports"]}
        summary["ledger_counts"] = {dt: frappe.db.count(dt, {"company": c}) for dt in ("GL Entry", "Payment Ledger Entry")}
        out["companies"].append(summary)
    from lotus_fin.api.ai_insights import get_financial_snapshot
    from lotus_fin.api.cashflow_api import get_ai002_cash_forecast
    company = "AI003 Gold 2026"
    snap = get_financial_snapshot(company=company, period_start="2026-01-01", period_end="2026-09-26", as_of="2026-09-26T00:00:00Z", comparison="PREVIOUS_PERIOD")
    out["public_api"]["AI001"] = {"status": snap.get("status"), "contract_version": snap.get("contract_version"),
        "metrics": [{k: m.get(k) for k in ("metric_id", "status", "value", "formula_version")} for m in snap.get("metrics", [])],
        "top_level_keys": sorted(snap), "comparison": snap.get("comparison")}
    forecast = get_ai002_cash_forecast(company=company, financial_as_of="2026-09-26", include_explanation=False)
    obligations = forecast.get("obligations", [])
    out["public_api"]["AI002"] = {k: forecast.get(k) for k in ("status", "reason_code", "contract_version", "method_version", "formula_version", "financial_as_of", "currency", "accounting_timezone", "coverage")}
    out["public_api"]["AI002"].update({"top_level_keys": sorted(forecast), "obligation_count": len(obligations),
        "obligation_fields": sorted({k for r in obligations for k in r}),
        "ap_count": sum(r.get("type") == "AP" for r in obligations), "ar_count": sum(r.get("type") == "AR" for r in obligations),
        "ap_amount": sum((dec(r.get("remaining_amount")) for r in obligations if r.get("type") == "AP"), Decimal(0)),
        "ar_amount": sum((dec(r.get("remaining_amount")) for r in obligations if r.get("type") == "AR"), Decimal(0)),
        "due_dates": dates(r.get("due_date") for r in obligations),
        "duplicate_document_refs": len(obligations) - len({r.get("source_ref") for r in obligations})})
    from lotus_fin.api.key_reports import extract_key_report_data
    out["public_api"]["report_contracts"] = {}
    for key in ("accounts_receivable", "accounts_payable"):
        report_data = extract_key_report_data(key, {"company": company, "report_date": "2026-09-26"})
        out["public_api"]["report_contracts"][key] = {"status": report_data.get("status"),
            "top_level_keys": sorted(report_data), "row_count": len(report_data.get("data", [])),
            "row_keys": sorted({k for r in report_data.get("data", []) if isinstance(r, dict) for k in r})}
    erp_root = Path(erpnext.__file__).parent
    for relative in ("accounts/report/accounts_receivable/accounts_receivable.py", "accounts/report/accounts_payable/accounts_payable.py"):
        p = erp_root / relative
        lines = p.read_text().splitlines()
        needles = ("report_date", "posting_date", "due_date", "payment_term", "delinked", "account_currency", "amended", "voucher_type", "outstanding", "company_currency", "get_currency", "return_against")
        out["source_excerpts"][relative] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "lines": [f"{i}: {line}" for i, line in enumerate(lines, 1) if any(n in line for n in needles)],
            "context": [f"{i}: {line}" for i, line in enumerate(lines, 1)
                        if relative.endswith("accounts_payable.py") or any(a <= i <= b for a, b in ((50, 92), (532, 643), (838, 888)))]}
    print(json.dumps(out, indent=2, default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
