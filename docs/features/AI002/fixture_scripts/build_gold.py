"""Independent AI002-00C test oracle generator; never imports a forecast service."""

from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import json
import yaml

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "direct_confirmed_commitments.json"
DEST = HERE.parent / "AI002_GOLD_FIXTURE_MANIFEST.yaml"
raw_source = SOURCE.read_bytes()
source = json.loads(raw_source)
assert source["classification"] == "SYNTHETIC_TEST_ONLY"
assert source["production_source"] is False

opening = Decimal("12000000") + Decimal("600000") + Decimal("500000") - Decimal("800000") - Decimal("750000")
assert opening == Decimal("11550000")
start, end = date(2026, 9, 27), date(2026, 10, 26)
dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]
assert len(dates) == 30

events = []
for row in source["records"]:
    assert row["fixture_confirmation"] == "TEST_AUTHOR_DECLARED_CONFIRMED_DATE"
    assert row["timing_basis"] == "DIRECT_CONFIRMED_COMMITMENT"
    assert row["source_kind"] == "synthetic"
    assert row["trust_state"] == "trusted"
    assert row["evidence_refs"] and row["source_ref"] in row["evidence_refs"]
    assert row["obligation_id"] is None and row["assumption_id"] is None
    assert row["direction"] in {"inflow", "outflow"}
    assert start <= date.fromisoformat(row["date"]) <= end
    events.append({**row, "company": source["company"], "currency": source["currency"], "financial_as_of": source["financial_as_of"]})
assert any(e["direction"] == "inflow" for e in events)
assert any(e["direction"] == "outflow" for e in events)

def daily_points(eligible):
    balance = opening
    result = []
    for day in dates:
        ids = []
        for event in eligible:
            if date.fromisoformat(event["date"]) == day:
                amount = Decimal(event["amount"])
                balance += amount if event["direction"] == "inflow" else -amount
                ids.append(event["source_ref"])
        result.append({"date": day.isoformat(), "modeled_cash": str(balance), "included_event_ids": ids})
    return result

flat, changing = daily_points([]), daily_points(events)
assert flat[-1]["modeled_cash"] == "11550000"
assert next(p for p in changing if p["date"] == "2026-09-29")["modeled_cash"] == "13550000"
assert next(p for p in changing if p["date"] == "2026-10-04")["modeled_cash"] == "9550000"
assert next(p for p in changing if p["date"] == "2026-10-10")["modeled_cash"] == "-450000"
assert changing[-1]["modeled_cash"] == "-450000"

common = {
    "company": source["company"],
    "financial_as_of": source["financial_as_of"],
    "timezone": "Asia/Ho_Chi_Minh",
    "forecast_start": start.isoformat(),
    "forecast_end": end.isoformat(),
    "coverage": {"scope": "TRADE_ONLY", "approval_status": "FROZEN_P0_ENGINEERING_DEFAULT", "completeness": "PARTIAL"},
    "threshold": {
        "status": "FROZEN_TECHNICAL_RULE", "rule": "MODELED_CASH_BELOW_ZERO", "value": "0",
        "risk_bands": "DISABLED", "overdraft_facility_inference": "DISABLED",
    },
    "opening_cash_gold": {
        "amount": str(opening), "account_set": ["Cash - A2F"],
        "gl_debit": "13100000", "gl_credit": "1550000", "trial_balance_net": "11550000",
        "reconciliation": "ERP_GL_EQUALS_TRIAL_BALANCE_NOT_BANK_RECONCILED",
        "vouchers": ["ACC-JV-2026-00001", "ACC-PAY-2026-00006", "ACC-PAY-2026-00007", "ACC-PAY-2026-00008", "ACC-PAY-2026-00009"],
    },
    "excluded_events": [
        {"reason": "POSTED_ON_OR_BEFORE_CUTOFF_IN_OPENING", "vouchers": ["ACC-PAY-2026-00006", "ACC-PAY-2026-00007", "ACC-PAY-2026-00008", "ACC-PAY-2026-00009"]},
        {"reason": "CONTRACTUAL_DUE_DATE_ONLY", "vouchers": ["ACC-SINV-2026-00006", "ACC-SINV-2026-00007", "ACC-SINV-2026-00008", "ACC-SINV-2026-00009", "ACC-PINV-2026-00007", "ACC-PINV-2026-00008", "ACC-PINV-2026-00009", "ACC-PINV-2026-00010"]},
        {"reason": "SETTLED_INVOICE_POSITIVE_ORIGINAL_SCHEDULE", "vouchers": ["ACC-SINV-2026-00010", "ACC-PINV-2026-00011"]},
    ],
    "obligation_residuals": {
        "AR_IN": "3000000", "AR_OVERDUE": "2000000", "AR_BEYOND": "1000000", "AR_PARTIAL": "900000", "AR_SETTLED": "0",
        "AP_IN": "4000000", "AP_OVERDUE": "1250000", "AP_BEYOND": "1500000", "AP_PARTIAL": "1200000", "AP_SETTLED": "0",
    },
}

gold = {
    "schema_version": "ai002-00d-gold-1",
    "classification": "SYNTHETIC_TEST_ONLY",
    "business_truth": False,
    "currency": "VND",
    "amount_unit": "VND",
    "oracle_method": "Independent Python Decimal calculation from fixed submitted ERPNext voucher amounts and separate typed test commitments; no AI002 forecast implementation imported",
    "runtime_site": "frontend",
    "contract_accounting_timezone": "Asia/Ho_Chi_Minh",
    "runtime_timezone_mismatch": True,
    "future_source_fixture": {"path": "fixture_scripts/direct_confirmed_commitments.json", "sha256": sha256(raw_source).hexdigest(), "status": "TEST_ONLY_TYPED_SOURCE_NOT_RUNTIME_INTEGRATED"},
    "cases": {
        "strict_no_future_event": {
            **common,
            "case_id": "AI002-00C-STRICT-EMPTY-001",
            "eligible_cash_events": [],
            "expected_first_negative_modeled_cash_date": None,
            "internal_arithmetic_reference": {"opening_cash": str(opening), "daily_eod_cash": flat},
            "expected_api": {
                "status": "FORECAST_UNAVAILABLE", "forecast_points": [], "shortfall_events": [],
                "limitations": ["No eligible future cash date", "Business obligation coverage incomplete", "Synthetic test company, not real SME finances"],
            },
        },
        "strict_with_confirmed_events": {
            **common,
            "case_id": "AI002-00C-STRICT-DIRECT-001",
            "scenario_execution_scope": "CONTRACT_UNIT_ONLY_NOT_LIVE_RUNTIME",
            "eligible_cash_events": events,
            "expected_first_negative_modeled_cash_date": "2026-10-10",
            "internal_arithmetic_reference": {"opening_cash": str(opening), "daily_eod_cash": changing, "minimum_cash": "-450000", "minimum_date": "2026-10-10"},
            "expected_api": {
                "status": "PARTIAL", "forecast_points": changing,
                "shortfall_events": [{
                    "type": "NEGATIVE_MODELED_CASH", "first_date": "2026-10-10",
                    "minimum_modeled_cash": "-450000", "threshold": "0", "risk_level": None,
                }],
                "limitations": ["Future event source is synthetic fixture-only, not a verified production connector", "Business obligation coverage incomplete", "No subjective risk rating or liquidity buffer is approved", "Runtime timezone differs from Vietnam demo contract"],
            },
        },
    },
}

DEST.write_text(yaml.dump(gold, Dumper=NoAliasDumper, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
print(f"{DEST.name}: {len(flat)} empty-case dates, {len(changing)} changing-case dates, source SHA256 {gold['future_source_fixture']['sha256']}")
