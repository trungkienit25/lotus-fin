"""AI003 legacy/corrupt evidence decode boundary — PUBLIC ENDPOINT probe.

Runs the whitelisted endpoint `get_risk_signal_evidence` in a separate process
WITH site context (frappe.init + connect + set_user), with legacy/corrupt
payloads injected directly into the installed Frappe Redis client under UNIQUE
probe refs (collision-checked; nothing existing is overwritten):

  parent-format pickle bytes | invalid UTF-8 | invalid JSON |
  valid JSON, wrong structure/type/date
    -> endpoint returns typed UNAVAILABLE with payload None
    -> NO unhandled exception ever escapes the endpoint
  healthy JSON record
    -> endpoint still returns MATCH (valid records unaffected)

No pickle.loads is ever called to read legacy data. Cleanup deletes only the
probe keys. Short-TTL/expiry semantics are covered by test_ttl_expiry_http.py.
"""

import json
import pickle
import subprocess
import sys
import uuid

HOST_HEADER = "ai003-verify.localhost"
COMPANY = "AI003 MG AP"
SENSITIVE = "SENSITIVE-legacy-payload-admin"

PICKLE_BYTES = pickle.dumps({"ref": "legacy", SENSITIVE: "raw-rows"}, protocol=4)
INVALID_UTF8 = b"\xff\xfe\x81" + SENSITIVE.encode("utf-16")
INVALID_JSON = b"{not-json"
WRONG_STRUCTURE = json.dumps({
    "ref": "PLACEHOLDER", "company": "c", "as_of_date": 20260926,
    "signal_id": "AP_DUE_CLUSTER", "payload": {},
}).encode()


def run_in_backend(py_code: str) -> str:
    cmd = [
        "docker", "exec", "-w", "/home/frappe/frappe-bench/sites",
        "frappe_docker-backend-1",
        "/home/frappe/frappe-bench/env/bin/python", "-c",
        f"import frappe; frappe.init('{HOST_HEADER}'); frappe.connect()\n" + py_code
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"backend snippet failed:\n{res.stderr}")
    return res.stdout.strip()


PROBE_SNIPPET = """
import json, pickle, uuid
from datetime import date
from lotus_fin.api.ai_insights import get_risk_signal_evidence
from lotus_fin.risk_signal import evidence as ev
from lotus_fin.risk_signal.contracts import SignalId
from lotus_fin.risk_signal.service import default_deps

SENSITIVE = {sensitive!r}
PICKLE_BYTES = pickle.dumps({{'ref': 'legacy', SENSITIVE: 'raw-rows'}}, protocol=4)
INVALID_UTF8 = b'\\xff\\xfe\\x81' + SENSITIVE.encode('utf-16')
INVALID_JSON = b'{{not-json'
WRONG_STRUCTURE = json.dumps({{
    'ref': 'PLACEHOLDER', 'company': 'c', 'as_of_date': 20260926,
    'signal_id': 'AP_DUE_CLUSTER', 'payload': {{}},
}}).encode()

client = frappe.cache()
results = {{}}
probe_refs = []

def probe_ref():
    ref = 'AI003-EV-decprobe-' + uuid.uuid4().hex[:12]
    probe_refs.append(ref)
    return ref

def inject(raw):
    ref = probe_ref()
    key = client.make_key(ev.EVIDENCE_KEY_PREFIX + ref)
    if client.get(key) is not None:
        raise RuntimeError('probe key collision — aborting')
    client.set(key, raw)  # raw bytes under the frozen prefix
    return ref

# 1..4: corrupt/legacy payloads through the PUBLIC endpoint
for name, raw in (
    ('parent_pickle', PICKLE_BYTES),
    ('invalid_utf8', INVALID_UTF8),
    ('invalid_json', INVALID_JSON),
    ('wrong_structure', WRONG_STRUCTURE),
):
    ref = inject(raw)
    res = get_risk_signal_evidence(evidence_ref=ref, company={company!r})
    results[name] = {{'status': res.get('status'), 'payload_none': res.get('payload') is None}}

# 5: healthy JSON record through the SAME endpoint still replays MATCH
deps = default_deps('Administrator')
snapshot = deps.ap_provider.fetch({company!r}, snapshot_date)
payload = ev._sanitize_payload({{'report_key': snapshot.report_key, 'source_hash': snapshot.source_hash}})
fingerprint = ev.build_scope_fingerprint(
    company={company!r}, report_key=snapshot.report_key,
    filters=snapshot.filters_applied, cutoff=snapshot.as_of,
    currency='VND', source_schema_version='ap_report_v1')
record = ev.EvidenceRecord(
    ref=probe_ref(), company={company!r}, signal_id=SignalId.AP_DUE_CLUSTER,
    as_of_date=snapshot.as_of, scope_fingerprint=fingerprint,
    payload_hash=ev.canonical_payload_hash(payload),
    payload=dict(payload), captured_at='decode-probe')
ev.EvidenceStore().put(record)
res = get_risk_signal_evidence(evidence_ref=record.ref, company={company!r})
results['healthy_match'] = {{'status': res.get('status'), 'payload_none': res.get('payload') is None}}

# cleanup: ONLY probe keys
for ref in probe_refs:
    try:
        ev.EvidenceStore().delete(ref)
    except Exception:
        pass
print(json.dumps(results))
"""


def main():
    ymd = "date(2026, 9, 26)"
    snippet = PROBE_SNIPPET.format(sensitive=SENSITIVE, company=COMPANY).replace(
        "snapshot_date", ymd
    )
    out = run_in_backend(snippet)
    results = json.loads(out.splitlines()[-1])

    failures = []
    for name in ("parent_pickle", "invalid_utf8", "invalid_json", "wrong_structure"):
        r = results[name]
        ok = r["status"] == "UNAVAILABLE" and r["payload_none"]
        print(("PASS" if ok else "FAIL"), f"endpoint_{name}", r)
        if not ok:
            failures.append(name)
    r = results["healthy_match"]
    ok = r["status"] == "MATCH" and not r["payload_none"]
    print(("PASS" if ok else "FAIL"), "endpoint_healthy_match_unchanged", r)
    if not ok:
        failures.append("healthy_match")

    if failures:
        print("DECODE BOUNDARY ENDPOINT PROBE: FAIL", failures)
        return 1
    print("DECODE BOUNDARY ENDPOINT PROBE: PASS "
          "(legacy pickle / corrupt bytes / malformed records -> typed UNAVAILABLE, "
          "payload null, no unhandled exception; healthy JSON replay unaffected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
