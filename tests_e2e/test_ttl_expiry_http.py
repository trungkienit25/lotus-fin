"""AI003 TTL-expiry HTTP probe (expiry-mechanism check).

NOT a 3600-second wall-clock test: a dedicated evidence record is stored with
a SHORT TTL (4s) through the production EvidenceStore boundary against the
site's Redis, then replayed over live HTTP:
  1. fresh record  -> MATCH
  2. after expiry  -> generic FORBIDDEN (expired key is a clean miss, not an
     outage/UNAVAILABLE)
The 3600s production TTL value itself is pinned by unit test (SET with
time=3600) and by Frappe's own SETEX semantics.
"""

import http.cookiejar
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request

HOST_HEADER = "ai003-verify.localhost"
BASE_URL = "http://127.0.0.1:8080"
USER = "Administrator"
PASSWORD = "admin"
COMPANY = "AI003 MG AP"
AS_OF = "2026-09-26"
SHORT_TTL_SECONDS = 4


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


def store_short_ttl_record():
    y, m, d = int(AS_OF[:4]), int(AS_OF[5:7]), int(AS_OF[8:10])
    out = run_in_backend(f"""
import json
from datetime import date
from lotus_fin.risk_signal import evidence as ev
from lotus_fin.risk_signal.contracts import SignalId
from lotus_fin.risk_signal.service import default_deps

deps = default_deps('Administrator')
snapshot = deps.ap_provider.fetch('{COMPANY}', date({y}, {m}, {d}))
payload = ev._sanitize_payload({{
    'report_key': snapshot.report_key,
    'source_hash': snapshot.source_hash,
}})
fingerprint = ev.build_scope_fingerprint(
    company='{COMPANY}',
    report_key=snapshot.report_key,
    filters=snapshot.filters_applied,
    cutoff=snapshot.as_of,
    currency='VND',
    source_schema_version='ap_report_v1',
)
record = ev.EvidenceRecord(
    ref=ev.make_evidence_ref(fingerprint, ev.canonical_payload_hash(payload)),
    company='{COMPANY}',
    signal_id=SignalId.AP_DUE_CLUSTER,
    as_of_date=snapshot.as_of,
    scope_fingerprint=fingerprint,
    payload_hash=ev.canonical_payload_hash(payload),
    payload={{'report_key': snapshot.report_key, 'source_hash': snapshot.source_hash}},
    captured_at='http-ttl-probe',
)
ref = ev.EvidenceStore(ttl_seconds={SHORT_TTL_SECONDS}).put(record)
print(json.dumps({{'ref': ref}}))
""")
    return json.loads(out.splitlines()[-1])["ref"]


def delete_probe_key(ref):
    run_in_backend(f"""
from lotus_fin.risk_signal import evidence as ev
try:
    ev.EvidenceStore().delete({ref!r})
except Exception:
    pass
print('DELETED')
""")


def http_replay(opener, ref):
    req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal_evidence",
        data=urllib.parse.urlencode({"evidence_ref": ref, "company": COMPANY}).encode(),
        headers={"Host": HOST_HEADER},
    )
    res = opener.open(req)
    return json.loads(res.read().decode())["message"]


def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    login_req = urllib.request.Request(
        f"{BASE_URL}/api/method/login",
        data=urllib.parse.urlencode({"usr": USER, "pwd": PASSWORD}).encode(),
        headers={"Host": HOST_HEADER},
    )
    assert opener.open(login_req).status == 200

    ref = store_short_ttl_record()
    print(f"Short-TTL record stored (ttl={SHORT_TTL_SECONDS}s): {ref}")
    try:
        body = http_replay(opener, ref)
        print(f"Fresh replay status: {body.get('status')}")
        assert body.get("status") == "MATCH", body

        time.sleep(SHORT_TTL_SECONDS + 2)
        body = http_replay(opener, ref)
        print(f"Post-expiry replay status: {body.get('status')}")
        assert body.get("status") == "FORBIDDEN", body
        assert body.get("payload") is None
    finally:
        delete_probe_key(ref)

    print("TTL EXPIRY MECHANISM OVER HTTP: PASS "
          f"(short-TTL={SHORT_TTL_SECONDS}s dedicated record; expiry mechanism only, "
          "NOT a 3600s wall-clock verification)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
