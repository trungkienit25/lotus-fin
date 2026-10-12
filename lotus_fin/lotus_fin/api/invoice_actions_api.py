"""Frappe HTTP Endpoint Declarations for Invoice Actions.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3, §8.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Any, Dict
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
from lotus_fin.presentation.response.action_response import ActionResponseBuilder


def frappe_whitelist(*args, **kwargs):
    def decorator(fn):
        try:
            import frappe  # type: ignore
            if hasattr(frappe, "whitelist"):
                return frappe.whitelist(*args, **kwargs)(fn)
        except Exception:
            pass
        return fn
    return decorator


def _frappe_post_handler(capability: str) -> Dict[str, Any]:
    """Helper ensuring Frappe POST-only, authenticated fail-closed delivery."""
    req_data: Dict[str, Any] = {}
    try:
        import frappe  # type: ignore
        if getattr(frappe, "request", None) and getattr(frappe.request, "json", None):
            req_data = dict(frappe.request.json)
        elif getattr(frappe, "form_dict", None):
            req_data = dict(frappe.form_dict)

        if getattr(frappe, "request", None) and getattr(frappe.request, "method", None) != "POST":
            if hasattr(frappe, "response"):
                frappe.response.status_code = 405
            return {"error": "Method Not Allowed. POST required."}
        user = getattr(frappe.session, "user", None) if hasattr(frappe, "session") else None
        if not user or user == "Guest":
            if hasattr(frappe, "response"):
                frappe.response.status_code = 401
            return {"error": "Authentication Required"}
    except Exception:
        pass

    client_req_id = req_data.get("request_id")
    outcome = ActionResponseBuilder.build_failure_outcome(
        status=ActionStatus.NOT_AVAILABLE,
        reason_code=ActionReasonCode.CAPABILITY_DISABLED,
        capability=capability,
        client_request_id=client_req_id,
    )
    status_code, headers, body = ActionResponseBuilder.serialize_response(outcome)
    try:
        import frappe  # type: ignore
        if hasattr(frappe, "response"):
            frappe.response.status_code = status_code
            for k, v in headers.items():
                frappe.response.headers[k] = v
    except Exception:
        pass
    return {"message": body}


# Explicit method exports with disabled defaults and guest forbidden


@frappe_whitelist(allow_guest=False, methods=["POST"])
def get_context() -> Dict[str, Any]:
    """POST /api/method/lotus_fin.api.invoice_actions_api.get_context"""
    return _frappe_post_handler("invoice.context")


@frappe_whitelist(allow_guest=False, methods=["POST"])
def search_invoices() -> Dict[str, Any]:
    """POST /api/method/lotus_fin.api.invoice_actions_api.search_invoices"""
    return _frappe_post_handler("invoice.search")


@frappe_whitelist(allow_guest=False, methods=["POST"])
def open_invoice() -> Dict[str, Any]:
    """POST /api/method/lotus_fin.api.invoice_actions_api.open_invoice"""
    return _frappe_post_handler("invoice.open")
