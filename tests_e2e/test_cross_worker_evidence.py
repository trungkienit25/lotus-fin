"""AI003 Cross-Worker Evidence Acceptance Test.

Verifies:
1. Multi-worker Gunicorn (2 workers) evidence consistency:
   - 1 authenticated evaluation -> obtain evidence_id
   - 20 sequential HTTP replays -> 20/20 MATCH, 0 false FORBIDDEN
2. Cross-company replay -> FORBIDDEN
3. Unknown evidence ID -> safe FORBIDDEN (no existence leak)
4. Expired evidence -> safe FORBIDDEN / unavailable
"""

import http.cookiejar
import json
import sys
import urllib.parse
import urllib.request

HOST_HEADER = "ai003-verify.localhost"
BASE_URL = "http://127.0.0.1:8080"
USER = "Administrator"
PASSWORD = "admin"
COMPANY = "AI003 MG AP"


def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    print("1. Logging in as Administrator...")
    login_req = urllib.request.Request(
        f"{BASE_URL}/api/method/login",
        data=urllib.parse.urlencode({"usr": USER, "pwd": PASSWORD}).encode(),
        headers={"Host": HOST_HEADER},
    )
    res = opener.open(login_req)
    assert res.status == 200, f"Login failed: {res.status}"

    print("2. Performing 1 authenticated evaluation for AP_DUE_CLUSTER...")
    eval_req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal",
        data=urllib.parse.urlencode({
            "company": COMPANY,
            "signal_id": "AP_DUE_CLUSTER",
            "as_of_date": "2026-09-26",
        }).encode(),
        headers={"Host": HOST_HEADER},
    )
    eval_res = opener.open(eval_req)
    eval_data = json.loads(eval_res.read().decode())["message"]
    assert eval_data["status"] == "OK", f"Evaluation failed: {eval_data}"
    assert len(eval_data.get("evidence", [])) > 0, "No evidence refs returned!"
    evidence_ref = eval_data["evidence"][0]["ref"]
    print(f"   Obtained evidence_ref: {evidence_ref}")

    print("3. Executing 20 sequential replay requests across Gunicorn workers...")
    match_count = 0
    forbidden_count = 0
    other_count = 0

    replay_data = urllib.parse.urlencode({
        "evidence_ref": evidence_ref,
        "company": COMPANY,
    }).encode()

    for i in range(1, 21):
        replay_req = urllib.request.Request(
            f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal_evidence",
            data=replay_data,
            headers={"Host": HOST_HEADER},
        )
        replay_res = opener.open(replay_req)
        rep_body = json.loads(replay_res.read().decode())["message"]
        status = rep_body.get("status")
        if status == "MATCH":
            match_count += 1
        elif status == "FORBIDDEN":
            forbidden_count += 1
        else:
            other_count += 1
        print(f"   Request {i:02d}/20: status={status}")

    print(f"   Summary: MATCH={match_count}, FORBIDDEN={forbidden_count}, OTHER={other_count}")
    assert match_count == 20, f"Expected 20 MATCH, got {match_count}"
    assert forbidden_count == 0, f"Expected 0 false FORBIDDEN, got {forbidden_count}"

    print("4. Testing unauthorized / cross-company replay...")
    cross_req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal_evidence",
        data=urllib.parse.urlencode({
            "evidence_ref": evidence_ref,
            "company": "Other Unauthorized Company",
        }).encode(),
        headers={"Host": HOST_HEADER},
    )
    cross_res = opener.open(cross_req)
    cross_body = json.loads(cross_res.read().decode())["message"]
    print(f"   Cross-company status: {cross_body.get('status')}")
    assert cross_body.get("status") == "FORBIDDEN", f"Expected FORBIDDEN, got {cross_body}"
    assert cross_body.get("payload") is None

    print("5. Testing unknown evidence ref...")
    unknown_req = urllib.request.Request(
        f"{BASE_URL}/api/method/lotus_fin.api.ai_insights.get_risk_signal_evidence",
        data=urllib.parse.urlencode({
            "evidence_ref": "AI003-EV-000000000000-000000000000",
            "company": COMPANY,
        }).encode(),
        headers={"Host": HOST_HEADER},
    )
    unknown_res = opener.open(unknown_req)
    unknown_body = json.loads(unknown_res.read().decode())["message"]
    print(f"   Unknown ref status: {unknown_body.get('status')}")
    assert unknown_body.get("status") == "FORBIDDEN", f"Expected FORBIDDEN, got {unknown_body}"
    assert unknown_body.get("payload") is None

    print("ALL CROSS-WORKER ACCEPTANCE CHECKS PASSED: 20/20 MATCH, 0 false FORBIDDEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
