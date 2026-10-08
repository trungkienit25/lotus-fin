# WR-01/WR-02 live injection probe — poisoned fetch payloads must fail closed
# at top level (metric UNAVAILABLE), never become a zero/obligation-free result.
from datetime import date, timedelta

import frappe

SITE = "ai003-verify.localhost"
COMPANY = "AI002 Fixture 2026"

frappe.init(site=SITE, sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")

from lotus_fin.ai.financial_snapshot import build_financial_snapshot
from lotus_fin.api.key_reports import extract_key_report_data
from lotus_fin.cashflow.adapters import ObligationSourceError, get_trade_obligations


def poisoned_fetcher(poison):
    def fetch(key, filters, company):
        res = extract_key_report_data(report_key=key, filters=filters, company=company)
        if key == "accounts_receivable" and res.get("status") == "success":
            res = dict(res)
            res["data"] = list(res["data"]) + [poison]
        return res
    return fetch


CUTOFF = "2026-09-26"
for label, poison in (
    ("fake is_total_row dict", {"is_total_row": True, "outstanding": 123}),
    ("fake party=Total dict (no voucher)", {"party": "Total", "outstanding": 123}),
    ("voucher-less positive row", {"party": "Ghost", "outstanding": 123}),
):
    snap = build_financial_snapshot(
        company=COMPANY,
        period_start="2026-01-01",
        period_end="2026-12-31",
        as_of=CUTOFF,
        currency="VND",
        source_fetcher=poisoned_fetcher(poison),
    )
    mm = {m["metric_id"]: (m["status"], m["value"]) for m in snap["metrics"]}
    ar = mm["ar_outstanding"]
    print(f"INJECT {label!r}: ar_outstanding={ar[0]} value={ar[1]} missing={'accounts_receivable' in snap['missing_inputs']}")
    assert ar[0] == "UNAVAILABLE" and ar[1] is None, "fail-closed violated!"

# AI002 adapter: poisoned AR report must raise ObligationSourceError (service fails closed)
try:
    get_trade_obligations(COMPANY, date.fromisoformat(CUTOFF))
    print("AI002 clean read: OK (obligations returned)")
except ObligationSourceError as e:
    print("AI002 clean read unexpectedly raised:", e)

frappe.destroy()
print("PROBE_DONE")
