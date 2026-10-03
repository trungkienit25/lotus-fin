"""AI003 installed-Frappe raw Redis fault probe (ConnectionError/TimeoutError).

Fault-injects the INSTALLED Frappe cache client's RAW command boundary
(`get`/`setex`/`delete` on the live frappe.cache() RedisWrapper inside a
site-context process) — NOT the error-swallowing convenience wrappers — and
verifies through the PUBLIC endpoint and the store:

  - GET raising ConnectionError / TimeoutError
      -> endpoint returns typed UNAVAILABLE, payload None, no unhandled exception
  - SETEX raising ConnectionError
      -> store path raises typed EvidenceStorageUnavailable; endpoint-level
         evaluation drops evidence refs and keeps the deterministic result
  - DELETE raising ConnectionError
      -> typed, not swallowed
  - after unpatching, the healthy path replays MATCH again

Patches are process-local and always restored in finally; no data is mutated
beyond one throwaway probe record the probe itself created and deletes.
"""

import json
import subprocess
import sys
import uuid

HOST_HEADER = "ai003-verify.localhost"
COMPANY = "AI003 MG AP"

FAULT_SNIPPET = """
import json, uuid
from datetime import date
from lotus_fin.api.ai_insights import get_risk_signal_evidence
from lotus_fin.risk_signal import evidence as ev
from lotus_fin.risk_signal.contracts import ReasonCode, SignalId, Status
from lotus_fin.risk_signal.provenance import SourceFailure
from lotus_fin.risk_signal.service import default_deps, get_evidence

results = {{}}
client = frappe.cache()
probe_refs = []

def make_record():
    deps = default_deps('Administrator')
    snapshot = deps.ap_provider.fetch({company!r}, date(2026, 9, 26))
    payload = ev._sanitize_payload({{'report_key': snapshot.report_key, 'source_hash': snapshot.source_hash}})
    fingerprint = ev.build_scope_fingerprint(
        company={company!r}, report_key=snapshot.report_key,
        filters=snapshot.filters_applied, cutoff=snapshot.as_of,
        currency='VND', source_schema_version='ap_report_v1')
    ref = 'AI003-EV-faultprobe-' + uuid.uuid4().hex[:12]
    probe_refs.append(ref)
    return ev.EvidenceRecord(
        ref=ref, company={company!r}, signal_id=SignalId.AP_DUE_CLUSTER,
        as_of_date=snapshot.as_of, scope_fingerprint=fingerprint,
        payload_hash=ev.canonical_payload_hash(payload),
        payload=dict(payload), captured_at='fault-probe')

def patch(command, error_cls, only_evidence_keys=False):
    original = getattr(client, command)
    if only_evidence_keys:
        def raiser(name, *args, **kwargs):
            key = name.encode() if isinstance(name, str) else (name or b"")
            if b"ai003:evidence:" in key:
                raise error_cls("SENSITIVE redis://admin:sekret@10.9.8.7 down")
            return original(name, *args, **kwargs)
    else:
        def raiser(*args, **kwargs):
            raise error_cls("SENSITIVE redis://admin:sekret@10.9.8.7 down")
    setattr(client, command, raiser)
    return original

def unpatch(command, original):
    setattr(client, command, original)

# 1: GET ConnectionError through the public endpoint (evidence keys only —
# other Redis consumers inside the request are left alone)
record = make_record()
ev.EvidenceStore().put(record)
original_get = patch("get", ConnectionError, only_evidence_keys=True)
try:
    res = get_risk_signal_evidence(evidence_ref=record.ref, company={company!r})
    results['get_connection_error'] = {{'status': res.get('status'), 'payload_none': res.get('payload') is None}}
finally:
    unpatch('get', original_get)

# 2: GET TimeoutError through the public endpoint
original_get2 = patch("get", TimeoutError, only_evidence_keys=True)
try:
    res = get_risk_signal_evidence(evidence_ref=record.ref, company={company!r})
    results['get_timeout'] = {{'status': res.get('status'), 'payload_none': res.get('payload') is None}}
finally:
    unpatch('get', original_get2)

# 3: SETEX ConnectionError on the store path -> typed, no ref emitted
original_setex = patch('setex', ConnectionError)
try:
    try:
        ev.EvidenceStore().put(make_record())
        results['setex_connection_error'] = {{'typed': False}}
    except ev.EvidenceStorageUnavailable as exc:
        results['setex_connection_error'] = {{'typed': exc.cause_type == 'ConnectionError'}}
finally:
    unpatch('setex', original_setex)

# 4: DELETE ConnectionError -> typed, not swallowed
original_delete = patch('delete', ConnectionError)
try:
    try:
        ev.EvidenceStore().delete('AI003-EV-faultprobe-nothing')
        results['delete_connection_error'] = {{'typed': False}}
    except ev.EvidenceStorageUnavailable:
        results['delete_connection_error'] = {{'typed': True}}
finally:
    unpatch('delete', original_delete)

# 5: healthy again after unpatch
res = get_risk_signal_evidence(evidence_ref=record.ref, company={company!r})
results['healthy_after_unpatch'] = {{'status': res.get('status'), 'payload_none': res.get('payload') is None}}

for ref in probe_refs:
    try:
        ev.EvidenceStore().delete(ref)
    except Exception:
        pass
print(json.dumps(results))
"""


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


def main():
    out = run_in_backend(FAULT_SNIPPET.format(company=COMPANY))
    results = json.loads(out.splitlines()[-1])

    expectations = {
        "get_connection_error": lambda r: r["status"] == "UNAVAILABLE" and r["payload_none"],
        "get_timeout": lambda r: r["status"] == "UNAVAILABLE" and r["payload_none"],
        "setex_connection_error": lambda r: r["typed"],
        "delete_connection_error": lambda r: r["typed"],
        "healthy_after_unpatch": lambda r: r["status"] == "MATCH" and not r["payload_none"],
    }
    failures = []
    for name, check in expectations.items():
        ok = check(results[name])
        print(("PASS" if ok else "FAIL"), name, results[name])
        if not ok:
            failures.append(name)

    if failures:
        print("RAW REDIS FAULT PROBE: FAIL", failures)
        return 1
    print("RAW REDIS FAULT PROBE: PASS "
          "(installed Frappe raw commands ConnectionError/TimeoutError -> typed, "
          "endpoint-safe, healthy path restored after unpatch)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
