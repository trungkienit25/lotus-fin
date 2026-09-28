"""Check AI002 documentation links, gold shape, source hash and daily arithmetic."""

from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import json
import re
import yaml

ROOT = Path(__file__).resolve().parent.parent
broken = []
for doc in ROOT.rglob("*.md"):
    body = doc.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", body):
        path = target.split("#", 1)[0]
        if not path or "://" in path or path.startswith("mailto:"):
            continue
        if not (doc.parent / path).exists():
            broken.append(f"{doc.relative_to(ROOT)} -> {target}")
assert not broken, "Broken relative links:\n" + "\n".join(broken)

gold = yaml.safe_load((ROOT / "AI002_GOLD_FIXTURE_MANIFEST.yaml").read_text(encoding="utf-8"))
source_path = ROOT / gold["future_source_fixture"]["path"]
source_bytes = source_path.read_bytes()
source = json.loads(source_bytes)
assert sha256(source_bytes).hexdigest() == gold["future_source_fixture"]["sha256"]
assert source["classification"] == gold["classification"] == "SYNTHETIC_TEST_ONLY"
assert source["production_source"] is False and gold["business_truth"] is False
assert set(gold["cases"]) == {"strict_no_future_event", "strict_with_confirmed_events"}

for name, case in gold["cases"].items():
    assert case["coverage"]["scope"] == "TRADE_ONLY"
    assert case["coverage"]["approval_status"] == "FROZEN_P0_ENGINEERING_DEFAULT"
    assert case["timezone"] == gold["contract_accounting_timezone"] == "Asia/Ho_Chi_Minh"
    assert case["threshold"] == {
        "status": "FROZEN_TECHNICAL_RULE", "rule": "MODELED_CASH_BELOW_ZERO", "value": "0",
        "risk_bands": "DISABLED", "overdraft_facility_inference": "DISABLED",
    }
    days = case["internal_arithmetic_reference"]["daily_eod_cash"]
    assert len(days) == 30
    first = date.fromisoformat(case["forecast_start"])
    for offset, point in enumerate(days):
        assert point["date"] == (first + timedelta(days=offset)).isoformat()
    if name == "strict_no_future_event":
        assert case["eligible_cash_events"] == []
        assert case["expected_api"]["status"] == "FORECAST_UNAVAILABLE"
        assert case["expected_api"]["forecast_points"] == []
        assert case["expected_api"]["shortfall_events"] == []
        assert case["expected_first_negative_modeled_cash_date"] is None
        assert {p["modeled_cash"] for p in days} == {"11550000"}
    else:
        assert case["scenario_execution_scope"] == "CONTRACT_UNIT_ONLY_NOT_LIVE_RUNTIME"
        assert case["expected_api"]["status"] == "PARTIAL"
        assert case["expected_api"]["forecast_points"] == days
        assert case["expected_first_negative_modeled_cash_date"] == "2026-10-10"
        assert case["expected_api"]["shortfall_events"] == [{
            "type": "NEGATIVE_MODELED_CASH", "first_date": "2026-10-10",
            "minimum_modeled_cash": "-450000", "threshold": "0", "risk_level": None,
        }]
        assert Decimal(days[-1]["modeled_cash"]) == Decimal("-450000")
        events = case["eligible_cash_events"]
        assert len(events) == 3
        for event in events:
            assert event["source_kind"] == "synthetic"
            assert event["source_ref"] in event["evidence_refs"]
            assert event["company"] == case["company"]
            assert event["currency"] == gold["currency"]
            assert event["financial_as_of"] == case["financial_as_of"]

# Verify exactly one active human-readable SSOT claiming authoritative status
ssot_docs = [p for p in ROOT.glob("*.md") if "MASTER_SSOT" in p.name]
active_ssot = [p.name for p in ssot_docs if not p.read_text(encoding="utf-8").startswith("# SUPERSEDED")]
assert active_ssot == ["AI002_MASTER_SSOT_V1_2_1_REFINED.md"], f"Expected single active SSOT AI002_MASTER_SSOT_V1_2_1_REFINED.md, found: {active_ssot}"

archive = list((ROOT / "archive").glob("*.md"))
assert len(archive) >= 9
for doc in archive:
    assert doc.read_text(encoding="utf-8").startswith("# SUPERSEDED")
print(f"AI002 artifacts valid: single active SSOT (AI002_MASTER_SSOT_V1_2_1_REFINED.md), {len(archive)} archived docs, 2 gold cases, 30 dates each, all local links resolve")
