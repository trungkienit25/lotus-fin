import json
from lotus_fin.ai.observability import log_event

# Sentinel values only: no real party, amount or financial document.
event = log_event(
    "ai002_test_canary",
    "ai002-00b-canary",
    company="AI002 Fixture 2026",
    details={"party": "CANARY_AI002_PERSON", "amount": "987654321"},
)
encoded = json.dumps(event)
print(json.dumps({
    "sentinel_party_returned": "CANARY_AI002_PERSON" in encoded,
    "sentinel_amount_returned": "987654321" in encoded,
    "details_keys": sorted(event["details"].keys()),
}))
