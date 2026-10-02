"""Read-only contract feasibility evidence; no AI003 engine or ledger writes."""
import json
from decimal import Decimal
import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")
try:
    from lotus_fin.api.ai_insights import get_financial_snapshot
    from lotus_fin.api.key_reports import extract_key_report_data
    out = {"scope": "CONTROLLED_FIXTURE", "ar": [], "ap": {}}
    for cutoff in ("2026-09-20", "2026-09-26"):
        snap = get_financial_snapshot(company="AI003 Gold 2026", period_start="2026-01-01",
                                      period_end=cutoff, as_of=cutoff)
        metrics = {m["metric_id"]: m for m in snap["metrics"]}
        selected = {key: {k: metrics[key].get(k) for k in ("status", "value", "formula_version")}
                    for key in ("ar_outstanding", "overdue_ar_ratio")}
        out["ar"].append({"cutoff": cutoff, "contract_version": snap["contract_version"],
                          "envelope_status": snap["status"], "metrics": selected})
        assert all(m["status"] == "AVAILABLE" for m in selected.values())
    out["ar_delta_pp_oracle"] = str((Decimal(str(out["ar"][1]["metrics"]["overdue_ar_ratio"]["value"]))
                                    - Decimal(str(out["ar"][0]["metrics"]["overdue_ar_ratio"]["value"]))) * 100)
    filters = {"company": "AI003 Gold 2026", "report_date": "2026-09-26",
               "based_on_payment_terms": 0, "in_party_currency": 0,
               "show_future_payments": 0, "ageing_based_on": "Due Date", "age_as_on": "Report Date"}
    report = extract_key_report_data("accounts_payable", filters)
    assert report["status"] == "success"
    rows = report["data"]
    positive = [r for r in rows if Decimal(str(r["outstanding"])) > 0]
    out["ap"] = {"literal_report_key": report["report_key"], "status": report["status"],
        "filters_applied": report["filters_applied"], "row_count": len(rows),
        "positive_row_count": len(positive), "positive_total": str(sum((Decimal(str(r["outstanding"])) for r in positive), Decimal(0))),
        "distinct_voucher_count": len({(r["voucher_type"], r["voucher_no"]) for r in positive}),
        "account_key": "party_account", "missing_positive_due_dates": sum(not r.get("due_date") for r in positive),
        "missing_row_company": sum("company" not in r for r in rows), "multi_schedule_vouchers": 0,
        "schedule_read_permissions": {}}
    for r in positive:
        doc = frappe.get_doc(r["voucher_type"], r["voucher_no"])
        allowed = bool(doc.has_permission("read"))
        out["ap"]["schedule_read_permissions"][r["voucher_type"]] = allowed
        assert allowed
        out["ap"]["multi_schedule_vouchers"] += len(doc.get("payment_schedule") or []) > 1
    print(json.dumps(out, indent=2))
finally:
    frappe.db.rollback()
    frappe.destroy()
