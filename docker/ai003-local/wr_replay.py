# WR-01/WR-02 remediation live replay — isolated site ai003-verify.localhost
# Read-only: AI001 snapshot (live ERPNext fetcher) + AI002 forecast against the
# 2026-09-20 / 2026-09-26 oracle.
from datetime import date, timedelta

import frappe

SITE = "ai003-verify.localhost"
COMPANY = "AI002 Fixture 2026"

frappe.init(site=SITE, sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

from lotus_fin.ai.financial_snapshot import build_financial_snapshot
from lotus_fin.cashflow.adapters import resolve_cash_account_scope
from lotus_fin.cashflow.models import CoverageScope, ForecastRequest
from lotus_fin.cashflow.service import get_cash_forecast
from lotus_fin.cashflow.source_interface import FailClosedSource


def fetcher(key, filters, company):
    from lotus_fin.api.key_reports import extract_key_report_data
    return extract_key_report_data(report_key=key, filters=filters, company=company)


scope_res = resolve_cash_account_scope(COMPANY, user="Administrator")
print("SCOPE:", scope_res.get("status"), scope_res.get("approval"), scope_res.get("scope"))

for cutoff in ("2026-09-20", "2026-09-26"):
    snap = build_financial_snapshot(
        company=COMPANY,
        period_start="2026-01-01",
        period_end="2026-12-31",
        as_of=cutoff,
        currency="VND",
        source_fetcher=fetcher,
    )
    mm = {m["metric_id"]: (m["status"], m["value"]) for m in snap["metrics"]}
    print(f"AI001 {cutoff} status={snap['status']}")
    for k in ("revenue", "ar_outstanding", "overdue_ar_ratio", "ap_outstanding", "cash_balance", "cogs"):
        print(f"   {k}: {mm[k]}")

    scope = scope_res.get("scope") or ["Cash - A2F"]
    req = ForecastRequest(
        company=COMPANY,
        financial_as_of=date.fromisoformat(cutoff),
        forecast_start=date.fromisoformat(cutoff) + timedelta(days=1),
        forecast_end=date.fromisoformat(cutoff) + timedelta(days=30),
        reporting_currency="VND",
        cash_account_scope=scope,
        coverage_scope=CoverageScope.TRADE_ONLY,
    )
    fc = get_cash_forecast(request=req, user="Administrator", future_event_source=FailClosedSource())
    ar = sum((o.remaining_amount for o in fc.obligations if o.type == "AR"), 0)
    ap = sum((o.remaining_amount for o in fc.obligations if o.type == "AP"), 0)
    opening = fc.opening_cash.aggregate_amount if fc.opening_cash else None
    print(f"AI002 {cutoff} status={fc.status} opening={opening} obligations={len(fc.obligations)} (AR {ar} / AP {ap})")
    if fc.status.name == "VALIDATION_ERROR" or getattr(fc, "reason", None):
        print("   reason:", getattr(fc, "reason", None), getattr(fc, "message", None))

frappe.destroy()
print("REPLAY_DONE")
