"""AI003 TTL-expiry HTTP probe (isolated probe key, expiry-mechanism check).

NOT a 3600-second wall-clock test: a DEDICATED evidence record is stored under
a UNIQUE probe ref (distinct from every production ref) with a SHORT TTL (4s)
through the production EvidenceStore boundary against the site's Redis, then
replayed over live HTTP:
  1. probe fresh            -> MATCH
  2. probe expired          -> generic FORBIDDEN (expired key is a clean miss,
     not an outage/UNAVAILABLE)
  3. existing production evidence record is untouched: distinct key, same
     value, TTL only naturally decayed, still replays MATCH after the probe.

The probe ref never collides with production refs (production refs are
hex-scope/hash; the probe ref carries a reserved "probe" marker + run uuid)
and the probe key's absence is asserted BEFORE any write — the probe aborts
rather than overwrite anything.
"""

import http.cookiejar
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid

HOST_HEADER = "ai003-verify.localhost"
BASE_URL = "http://127.0.0.1:8080"
USER = "Administrator"
PASSWORD = "admin"
COMPANY = "AI003 MG AP"
AS_OF = "2026-09-26"
SHORT_TTL_SECONDS = 4

y, m, d = int(AS_OF[:4]), int(AS_OF[5:7]), int(AS_OF[8:10])


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


def http_login():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    login_req = urllib.request.Request(
        f"{BASE_URL}/api/method/login",
        data=urllib.parse.urlencode({"usr": USER, "pwd": PASSWORD}).encode(),
        headers={"Host": HOST_HEADER},
    )
    assert opener.open(login_req).status == 200
    return opener


def http_evaluate(opener):
    req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal",
        data=urllib.parse.urlencode({
            "company": COMPANY, "signal_id": "AP_DUE_CLUSTER", "as_of_date": AS_OF,
        }).encode(),
        headers={"Host": HOST_HEADER},
    )
    body = json.loads(opener.open(req).read().decode())["message"]
    assert body["status"] == "OK" and body.get("evidence"), body
    return body["evidence"][0]["ref"]


def http_replay(opener, ref):
    req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal_evidence",
        data=urllib.parse.urlencode({"evidence_ref": ref, "company": COMPANY}).encode(),
        headers={"Host": HOST_HEADER},
    )
    return json.loads(opener.open(req).read().decode())["message"]


def store_probe_record():
    """Store the short-TTL probe record under a UNIQUE, non-colliding ref.
    Aborts if the key already exists (never overwrite). Returns probe ref."""
    probe_ref = f"AI003-EV-probe-{uuid.uuid4().hex[:12]}"
    out = run_in_backend(f"""
import json
from datetime import date
from lotus_fin.risk_signal import evidence as ev
from lotus_fin.risk_signal.contracts import SignalId
from lotus_fin.risk_signal.service import default_deps

PROBE_REF = {probe_ref!r}
client = frappe.cache()
key = client.make_key(ev.EVIDENCE_KEY_PREFIX + PROBE_REF)
if client.get(key) is not None:
    raise RuntimeError('probe key collision — aborting, nothing overwritten')

deps = default_deps('Administrator')
snapshot = deps.ap_provider.fetch({COMPANY!r}, date({y}, {m}, {d}))
payload = ev._sanitize_payload({{
    'report_key': snapshot.report_key,
    'source_hash': snapshot.source_hash,
}})
payload_hash = ev.canonical_payload_hash(payload)
fingerprint = ev.build_scope_fingerprint(
    company={COMPANY!r},
    report_key=snapshot.report_key,
    filters=snapshot.filters_applied,
    cutoff=snapshot.as_of,
    currency='VND',
    source_schema_version='ap_report_v1',
)
record = ev.EvidenceRecord(
    ref=PROBE_REF,
    company={COMPANY!r},
    signal_id=SignalId.AP_DUE_CLUSTER,
    as_of_date=snapshot.as_of,
    scope_fingerprint=fingerprint,
    payload_hash=payload_hash,
    payload=dict(payload),
    captured_at='http-ttl-probe',
)
ev.EvidenceStore(ttl_seconds={SHORT_TTL_SECONDS}).put(record)
print(json.dumps({{'stored': True}}))
""")
    assert json.loads(out.splitlines()[-1])["stored"]
    return probe_ref


def existing_record_state(ref):
    """Value hash + TTL of an existing record's key (read-only)."""
    out = run_in_backend(f"""
import json
client = frappe.cache()
key = client.make_key('ai003:evidence:' + {ref!r})
raw = client.get(key)
print(json.dumps({{
    'present': raw is not None,
    'value_sha': __import__('hashlib').sha256(raw).hexdigest() if raw else None,
    'ttl': client.ttl(key) if raw else None,
}}))
""")
    return json.loads(out.splitlines()[-1])


def delete_probe_key(ref):
    run_in_backend(f"""
from lotus_fin.risk_signal import evidence as ev
try:
    ev.EvidenceStore().delete({ref!r})
except Exception:
    pass
print('DELETED')
""")


def main():
    opener = http_login()

    print("1. Obtaining a normal production evidence record via HTTP evaluation...")
    existing_ref = http_evaluate(opener)
    before = existing_record_state(existing_ref)
    assert before["present"], "no existing record to protect"
    print(f"   Existing ref: {existing_ref} (ttl={before['ttl']}s)")

    probe_ref = store_probe_record()
    print(f"2. Probe ref: {probe_ref} (distinct from existing: {probe_ref != existing_ref})")
    assert probe_ref != existing_ref
    try:
        body = http_replay(opener, probe_ref)
        print(f"3. Probe fresh replay status: {body.get('status')}")
        assert body.get("status") == "MATCH", body

        time.sleep(SHORT_TTL_SECONDS + 2)
        body = http_replay(opener, probe_ref)
        print(f"4. Probe post-expiry replay status: {body.get('status')}")
        assert body.get("status") == "FORBIDDEN", body
        assert body.get("payload") is None

        after = existing_record_state(existing_ref)
        print(f"6. Existing record after probe: present={after['present']} ttl={after['ttl']}s "
              f"(before ttl={before['ttl']}s)")
        assert after["present"], "existing record was deleted by the probe!"
        assert after["value_sha"] == before["value_sha"], "existing record value changed!"
        # TTL only naturally decayed — never reset/truncated to the probe TTL.
        assert after["ttl"] <= before["ttl"], "existing TTL was extended/reset"
        assert after["ttl"] > before["ttl"] - 300, "existing TTL was truncated abnormally"
        body = http_replay(opener, existing_ref)
        print(f"5. Existing record still replays: {body.get('status')}")
        assert body.get("status") == "MATCH", body
    finally:
        delete_probe_key(probe_ref)

    print("TTL EXPIRY MECHANISM OVER HTTP: PASS "
          f"(isolated probe key, short-TTL={SHORT_TTL_SECONDS}s, expiry mechanism only, "
          "NOT a 3600s wall-clock verification; existing record untouched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
