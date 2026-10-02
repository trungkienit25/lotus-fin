"""Narrow independent regression probes; no database or production writes."""
import copy
import importlib
import importlib.abc
import json
import logging
import subprocess
import sys


def normalized(value):
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items() if k not in ("snapshot_id", "retrieved_at")}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    return value


def contracts():
    from lotus_fin.ai.financial_snapshot import build_financial_snapshot, parse_ar_data, parse_ap_data, CONTRACT_VERSION, FORMULA_VERSION
    from lotus_fin.cashflow.adapters import _collect_obligations
    from lotus_fin.cashflow.models import ForecastRequest, ForecastResponse, ForecastStatus
    from datetime import date
    events = []
    class Capture(logging.Handler):
        def emit(self, record):
            try:
                event = json.loads(record.getMessage())
                events.append({"event_type": event["event_type"], "correlation_id": event["correlation_id"]})
            except (ValueError, KeyError):
                pass
    logger = logging.getLogger("lotus_fin.ai001")
    logger.setLevel(logging.INFO)
    logger.addHandler(Capture())
    raw = {
        "profit_and_loss": [{"account_name": "Sales Revenue", "balance": 100}, {"account_name": "Cost of Goods Sold", "balance": 0}],
        "accounts_receivable": [], "accounts_payable": [],
        "trial_balance": [{"account_type": "Cash", "balance": 100}],
    }
    def snapshot(sources=None, **kwargs):
        kwargs.setdefault("as_of", "2026-12-31T00:00:00Z")
        return build_financial_snapshot("SYNTHETIC_RETEST", "2026-01-01", "2026-12-31",
                                        correlation_id="retest-cid", raw_sources=sources, **kwargs)
    happy = snapshot(copy.deepcopy(raw))
    margin = next(m for m in happy["metrics"] if m["metric_id"] == "gross_margin")
    assert margin["status"] == "AVAILABLE" and margin["value"] == 1.0
    happy_events = copy.deepcopy(events)
    assert all(e["correlation_id"] == "retest-cid" for e in happy_events)
    required = {"ai001_request_started", "ai001_authorization_passed", "ai001_snapshot_started",
                "ai001_metric_computed", "ai001_snapshot_completed", "ai001_request_completed"}
    assert required <= {e["event_type"] for e in happy_events}
    assert all("source_record_id" in e and e["source_record_id"] is None and e["filters"].get("company") == "SYNTHETIC_RETEST" for e in happy["evidence_refs"])
    gold = copy.deepcopy(raw)
    gold["profit_and_loss"] = [{"account_name": "Sales Revenue", "balance": 1000000}, {"account_name": "Cost of Goods Sold", "balance": 600000}]
    gold["accounts_receivable"] = [{"voucher_no": "SINV-1", "outstanding": 50000, "overdue_amount": 20000}]
    gold["accounts_payable"] = [{"voucher_no": "PINV-1", "outstanding": 45000}]
    gold_snap = snapshot(gold)
    source_error = snapshot(source_fetcher=lambda *args: (_ for _ in ()).throw(RuntimeError("controlled source failure")))
    assert source_error["status"] == "SOURCE_ERROR"
    assert all(m["value"] is None for m in source_error["metrics"])
    # Approved SOURCE lifecycle is emitted when previous-snapshot construction
    # raises. Ordinary report failures are represented by typed metrics/status.
    from unittest.mock import patch
    module = importlib.import_module("lotus_fin.ai.financial_snapshot")
    if hasattr(module, "SnapshotCoordinator"):
        cls = module.SnapshotCoordinator
        original = cls.build_snapshot
        def previous_failure(self, *args, **kwargs):
            if str(kwargs.get("correlation_id", "")).endswith("-PREV"):
                raise RuntimeError("controlled previous snapshot failure")
            return original(self, *args, **kwargs)
        boundary = patch.object(cls, "build_snapshot", previous_failure)
    else:
        original = module.build_financial_snapshot
        def previous_failure(*args, **kwargs):
            if str(kwargs.get("correlation_id", "")).endswith("-PREV"):
                raise RuntimeError("controlled previous snapshot failure")
            return original(*args, **kwargs)
        boundary = patch.object(module, "build_financial_snapshot", previous_failure)
    with boundary:
        comparison_failure = snapshot(source_fetcher=lambda *args: [], comparison="PREVIOUS_PERIOD")
    assert "ai001_source_error" in {e["event_type"] for e in events}
    missing = snapshot({"accounts_receivable": [], "accounts_payable": []})
    assert next(m for m in missing["metrics"] if m["metric_id"] == "revenue")["value"] is None
    def outcome(fn):
        try:
            return {"accepted": True, "result": fn()}
        except Exception as exc:
            return {"accepted": False, "exception": type(exc).__name__, "message": str(exc)}
    rows = [{"party": "Total", "is_total_row": 1, "outstanding": 0}]
    guards = {
        "summary_ar": outcome(lambda: parse_ar_data(rows)),
        "summary_ap": outcome(lambda: parse_ap_data(rows)),
        "malformed_ar": outcome(lambda: parse_ar_data([{"voucher_no": "SINV-1", "outstanding": "broken"}])),
        "voucherless_ar": outcome(lambda: parse_ar_data([{"outstanding": 0}])),
        "summary_ai002": outcome(lambda: _collect_obligations({"status": "success", "company": "SYNTHETIC_RETEST", "data": rows}, "AR", ("party",), "Sales Invoice", "VND", "Accounts Receivable", company="SYNTHETIC_RETEST")),
    }
    assert all(not g["accepted"] for g in guards.values())
    req = ForecastRequest("SYNTHETIC_RETEST", date(2026, 9, 26), date(2026, 9, 27), date(2026, 10, 26), cash_account_scope=["synthetic"])
    response = ForecastResponse(status=ForecastStatus.FORECAST_UNAVAILABLE)
    assert CONTRACT_VERSION == "1.0.0" and FORMULA_VERSION == "2026.1"
    assert response.contract_version == "1.2.1" and response.method_version == response.formula_version == "STRICT_BASELINE_V1"
    return normalized({"zero_cogs": happy, "gold": gold_snap, "source_error": source_error,
                       "missing": missing, "comparison_failure": comparison_failure,
                       "invalid_asof": snapshot(raw, as_of="invalid"),
                       "guards": guards, "events": events,
                       "versions": [CONTRACT_VERSION, FORMULA_VERSION, response.contract_version, response.method_version, response.formula_version]})


def containment():
    class BrokenSibling(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.startswith(("lotus_fin.modules.f005_financing", "lotus_fin.AI005")):
                raise ImportError("independent controlled F005 import failure")
    sys.meta_path.insert(0, BrokenSibling())
    from lotus_fin.ai.financial_snapshot import build_financial_snapshot
    from lotus_fin.modules.f001_health.plugin import HealthPlugin
    from lotus_fin.cashflow.service import get_cash_forecast
    from lotus_fin.cashflow.models import ForecastRequest
    return {"F005_broken_F001_F002_foundation_imports_survive": True}


def import_order():
    order = sys.argv[2]
    f001 = "lotus_fin.ai.financial_snapshot"
    f002 = "lotus_fin.cashflow.service"
    for name in ([f001, f002] if order == "f001-first" else [f002, f001]):
        importlib.import_module(name)
    results = {}
    for child in ("adapters", "agent", "cache", "engine", "grounding", "models", "service", "source_interface", "tools", "validation", "plugin"):
        legacy = importlib.import_module("lotus_fin.cashflow." + child)
        canonical = importlib.import_module("lotus_fin.modules.f002_cashflow." + child)
        assert legacy is canonical
        results[child] = True
    return {"order": order, "identities": results}


if __name__ == "__main__":
    mode = sys.argv[1]
    result = {"contracts": contracts, "containment": containment, "import-order": import_order}[mode]()
    print(json.dumps(result, indent=2, default=str))
