"""AI003 live API smoke probe — runs inside the backend container.

Site: ai003-verify.localhost (isolated verification site, tz Asia/Ho_Chi_Minh).
Administrator session proves authorized wiring; restricted-user permission
proofs remain covered by METHOD/POLICY GOLD live evidence and hermetic suites.
Read-only: no business data is written; no fixture mutation; no cleanup needed.

Run (from E:\\lotus-fin, after image rebuild + recreate):
  docker cp docker\\ai003-local\\ai003_smoke_probe.py frappe_docker-backend-1:/tmp/
  docker exec -w /home/frappe/frappe-bench/sites frappe_docker-backend-1 \\
    /home/frappe/frappe-bench/env/bin/python /tmp/ai003_smoke_probe.py
"""

import json
import sys

import frappe

frappe.init(site="ai003-verify.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

from lotus_fin.api.ai_insights import get_risk_signal, get_risk_signal_evidence  # noqa: E402

results = []


def record(name, ok, detail):
    results.append({"case": name, "ok": bool(ok), "detail": detail})


def eval_risk(company, signal, as_of):
    frappe.set_user("Administrator")
    return get_risk_signal(company=company, signal_id=signal, as_of_date=as_of, include_explanation=True)


# 1. Unauthenticated -> FORBIDDEN / UNAUTHORIZED_ACCESS (A1 before A2: bad signal too)
frappe.set_user("Guest")
r = get_risk_signal(company="NoSuchCompany", signal_id="NOT_A_SIGNAL", as_of_date="bad-date")
record("UNAUTH_FORBIDDEN", r.get("status") == "FORBIDDEN" and r.get("reason_code") == "UNAUTHORIZED_ACCESS",
       {"status": r.get("status"), "reason_code": r.get("reason_code")})

# 2. Authorized + unknown company -> generic FORBIDDEN, no company/financial payload
r = eval_risk("NoSuchCompany", "AR_OVERDUE_SPIKE", "2026-09-26")
record("UNKNOWN_COMPANY_FORBIDDEN",
       r.get("status") == "FORBIDDEN" and "company" not in r and "observed" not in r,
       {"status": r.get("status"), "reason_code": r.get("reason_code")})

# 3. AR METHOD GOLD pair: current ratio 1.0000 (2026-09-26) vs baseline .2727
#    (2026-08-26) -> delta 72.73pp -> HIGH (AR_SAME_DAY + AR_POSITIVE_DELTA facts)
r = eval_risk("AI003 MG AR", "AR_OVERDUE_SPIKE", "2026-09-26")
record("AR_GOLD_HIGH",
       r.get("status") == "OK" and r.get("finding") == "TRIGGERED" and r.get("severity") == "HIGH"
       and r.get("delta_pp") == "72.73"
       and (r.get("observed") or {}).get("value") == "1.0000"
       and (r.get("baseline") or {}).get("value") == "0.2727",
       {k: r.get(k) for k in ("status", "finding", "severity", "delta_pp", "reason_code")})

# 4. AP METHOD GOLD oracle: N=3 D=9 display 0.3333, counts 2/4 -> BENIGN
r = eval_risk("AI003 MG AP", "AP_DUE_CLUSTER", "2026-09-26")
ev_refs = r.get("evidence") or []
record("AP_GOLD_BENIGN",
       r.get("status") == "OK" and r.get("finding") == "BENIGN"
       and (r.get("observed") or {}).get("value") == "0.3333"
       and r.get("count_positive_vouchers") == 4 and r.get("count_due_vouchers") == 2
       and len(ev_refs) == 1,
       {"status": r.get("status"), "finding": r.get("finding"),
        "observed": (r.get("observed") or {}).get("value"),
        "counts": [r.get("count_positive_vouchers"), r.get("count_due_vouchers")],
        "evidence": len(ev_refs)})

# 5. Evidence replay: MATCH on unchanged fixtures
if ev_refs:
    frappe.set_user("Administrator")
    er = get_risk_signal_evidence(evidence_ref=ev_refs[0]["ref"], company="AI003 MG AP")
    record("EVIDENCE_REPLAY_MATCH", er.get("status") == "MATCH", {"status": er.get("status")})
else:
    record("EVIDENCE_REPLAY_MATCH", False, "no evidence ref on AP result")

# 6. Real two-schedule parent (flattened report row) -> INCONCLUSIVE/UNSUPPORTED_MULTI_SCHEDULE
r = eval_risk("AI003 MG Multi", "AP_DUE_CLUSTER", "2026-09-26")
record("MULTI_SCHEDULE_FAIL_CLOSED",
       r.get("status") == "INCONCLUSIVE" and r.get("reason_code") == "UNSUPPORTED_MULTI_SCHEDULE"
       and r.get("finding") is None,
       {"status": r.get("status"), "reason_code": r.get("reason_code")})

# 7. Demo disclosures on the wire: DEMO_ONLY scope, production_calibrated=false
r = eval_risk("AI003 MG AP", "AP_DUE_CLUSTER", "2026-09-26")
record("DEMO_DISCLOSURE",
       r.get("policy_scope") == "DEMO_ONLY" and r.get("production_calibrated") is False
       and r.get("policy_version") == "AI003_DEMO_POLICY_V1",
       {"policy_scope": r.get("policy_scope"),
        "production_calibrated": r.get("production_calibrated")})

passed = all(x["ok"] for x in results)
print(json.dumps({"pass": passed, "results": results}, indent=2, default=str))
sys.exit(0 if passed else 1)
