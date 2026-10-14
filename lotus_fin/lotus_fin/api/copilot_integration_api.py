"""Authenticated POST-only integration endpoint; Frappe owns CSRF enforcement."""
import hashlib
import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from werkzeug.wrappers import Response

from lotus_fin.api.invoice_actions_api import frappe_whitelist
from lotus_fin.application.service.copilot_integration import CopilotIntegrationService
from lotus_fin.infrastructure.persistence.copilot_demo_store import CopilotDemoStore


class IntegrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    profile: Literal["CORE", "DEMO"]
    action: Literal["past_final_due", "l5_review", "l4_propose", "l4_confirm",
                    "l4_cancel", "l4_status", "l4_reconcile"]
    action_name: str | None = Field(default=None, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


def response(status, body):
    return Response(json.dumps({"message": body}, ensure_ascii=False), status=status,
                    mimetype="application/json", headers={"Cache-Control": "private, no-store",
                    "Vary": "Cookie", "X-Content-Type-Options": "nosniff"})


@frappe_whitelist(allow_guest=False, methods=["POST"])
def dispatch():
    import frappe
    from lotus_fin.runtime.boundary import validate_authenticated_principal
    user, sid = frappe.session.user, frappe.session.sid
    validate_authenticated_principal(user, sid)
    if frappe.request.method != "POST":
        return response(405, {"reason_code": "POST_REQUIRED"})
    if frappe.request.content_length and frappe.request.content_length > 16384:
        return response(413, {"reason_code": "REQUEST_TOO_LARGE"})
    try:
        body = IntegrationRequest.model_validate_json(frappe.request.get_data()).model_dump()
    except Exception:
        return response(400, {"reason_code": "INVALID_REQUEST"})
    # Independent server switch. A client profile flag can only request this simulator.
    demo_enabled = frappe.conf.get("lotus_copilot_demo_enabled") is True
    binding = hashlib.sha256(f"{frappe.local.site}:{user}:{sid}".encode()).hexdigest()
    store = CopilotDemoStore(frappe.get_site_path("private", "lotus-copilot-demo.sqlite3"))
    try:
        status, result = CopilotIntegrationService(store).dispatch(
            user, list(frappe.get_roles(user)), binding, frappe.local.site, demo_enabled, body)
    except Exception:
        # No operation receipt is returned if audit or transaction persistence failed.
        return response(503, {"reason_code": "AUDIT_OR_STORE_UNAVAILABLE", "availability": "UNAVAILABLE"})
    return response(status, result)
