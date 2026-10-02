"""Independent narrow PB-DATA-01 probe; no DB, fixtures or production writes."""
import json
from datetime import date, datetime

from lotus_fin.ai.financial_snapshot import build_financial_snapshot
from lotus_fin.core.domain.calculators.ar_extractor import parse_ar_data

results = []
for due in ("2026-09-20", date(2026, 9, 20), datetime(2026, 9, 20)):
    row = {"voucher_no": "SI-RETEST", "outstanding": 100, "due_date": due}
    result = {"due_type": type(due).__name__, "expected_total": "100.00",
              "expected_overdue": "100.00", "expected_ratio": "1.0000"}
    try:
        result["parser"] = parse_ar_data([row], as_of_date=date(2026, 9, 26))
    except Exception as exc:
        result["parser_error"] = {"type": type(exc).__name__, "message": str(exc)}
    sources = {
        "profit_and_loss": [{"account_name": "Sales Revenue", "balance": 100},
                            {"account_name": "Cost of Goods Sold", "balance": 0}],
        "accounts_receivable": [row], "accounts_payable": [],
        "trial_balance": [{"account_type": "Cash", "balance": 100}],
    }
    try:
        snapshot = build_financial_snapshot(
            "SYNTHETIC_RETEST", "2026-01-01", "2026-12-31",
            raw_sources=sources, as_of="2026-09-26T00:00:00Z")
        result["snapshot_status"] = snapshot["status"]
        result["ar_metrics"] = [m for m in snapshot["metrics"]
                                if m["metric_id"] in ("total_ar", "overdue_ar", "overdue_ar_ratio", "ar_overdue_ratio")]
    except Exception as exc:
        result["snapshot_error"] = {"type": type(exc).__name__, "message": str(exc)}
    results.append(result)
print(json.dumps(results, indent=2, default=str))
