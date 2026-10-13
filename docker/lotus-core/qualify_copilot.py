"""Actual HTTP builder qualification for the explicitly owned P6 loopback demo."""
import argparse
import hashlib
import http.cookiejar
import json
from pathlib import Path
import urllib.error
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--credentials", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.base != "http://127.0.0.1:8114":
        parser.error("This qualification targets only the P6 owned loopback stack at 8114")
    credentials = json.loads(Path(args.credentials).read_text(encoding="utf-8"))
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    receipts = []
    def probe(name, path, method="GET", data=None, token=None, expected=(200,)):
        headers = {"Content-Type": "application/json"}
        if token: headers["X-Frappe-CSRF-Token"] = token
        request = urllib.request.Request(args.base + path, method=method, headers=headers,
                    data=json.dumps(data).encode() if data is not None else None)
        try: response = client.open(request, timeout=20)
        except urllib.error.HTTPError as error: response = error
        raw = response.read()
        assert response.status in expected, f"{name}: HTTP {response.status}: {raw[:150]!r}"
        assert b"Traceback" not in raw
        receipts.append({"case": name, "status": response.status, "body_sha256": hashlib.sha256(raw).hexdigest()})
        return json.loads(raw) if "json" in response.headers.get("Content-Type", "") else raw
    endpoint = "/api/method/lotus_fin.api.copilot_integration_api.dispatch"
    probe("guest-denied", endpoint, "POST", {}, expected=(401, 403))
    probe("real-login", "/api/method/login", "POST", credentials)
    bootstrap = probe("real-session-csrf", "/copilot/session")
    assert bootstrap["user"] == credentials["usr"]
    token = bootstrap["csrf_token"]
    probe("authenticated-spa", "/copilot")
    probe("csrf-denied", endpoint, "POST", {"profile": "DEMO", "action": "past_final_due"}, expected=(400, 403))
    probe("get-denied", endpoint, expected=(403, 405))
    probe("core-unavailable", endpoint, "POST", {"profile": "CORE", "action": "past_final_due"}, token, (503,))
    v1 = probe("v1-demo-evaluator", endpoint, "POST", {"profile": "DEMO", "action": "past_final_due"}, token)["message"]
    assert [i["invoice_id"] for i in v1["data"]["items"]] == ["DEMO-INV-001", "DEMO-INV-002"]
    payload = {"request_id": str(uuid.uuid4()), "action_id": "lotus.task.create", "arguments": {
        "title": "Fictional follow-up", "description": "Reviewed local demo draft", "due_date": "2026-10-20"}}
    proposal = probe("l4-propose", endpoint, "POST", {"profile": "DEMO", "action": "l4_propose", "payload": payload}, token)["message"]["proposal"]
    assert proposal["session_id"] == "server-bound" and proposal["simulated"] is True
    confirm = {"request_id": str(uuid.uuid4()), "proposal_id": proposal["proposal_id"], "confirmation_challenge": proposal["confirmation_challenge"]}
    body = {"profile": "DEMO", "action": "l4_confirm", "payload": confirm}
    first = probe("l4-confirm-simulation", endpoint, "POST", body, token)["message"]["operation"]
    again = probe("l4-repeat-single-receipt", endpoint, "POST", body, token)["message"]["operation"]
    assert first["is_synthetic_demo"] and first["operation_id"] == again["operation_id"]
    assert again["execution_attempts"] == 1
    policy = probe("l5-no-side-effects", endpoint, "POST", {"profile": "DEMO", "action": "l5_review", "action_name": "l5.pay.execute_wire_transfer.v1"}, token)["message"]
    assert policy["status"] == "DENIED" and policy["reason_code"] == "CAPABILITY_DISABLED"
    probe("client-authority-rejected", endpoint, "POST", {"profile": "DEMO", "action": "l4_propose", "actor": "forged"}, token, (400,))
    probe("logout", "/api/method/logout", "POST", {}, token)
    probe("old-confirm-denied", endpoint, "POST", body, token, (401, 403))
    Path(args.output).write_text(json.dumps({"checks": receipts, "layer": "actual HTTP builder checks",
        "scope": "isolated fictional DEMO, native and real writes remain blocked"}, indent=2), encoding="utf-8")
    print(f"{len(receipts)} real HTTP builder checks passed; no native qualification")


if __name__ == "__main__":
    main()
