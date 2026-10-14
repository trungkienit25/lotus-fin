"""Frappe HTTP Endpoint Declarations for Invoice Actions.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3, §8.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import json
from werkzeug.wrappers import Response
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
from lotus_fin.presentation.response.action_response import ActionResponseBuilder
from lotus_fin.presentation.dto.invoice_action_http_request import (
    RequestTooLarge, parse_invoice_http_request,
)


def frappe_whitelist(*args, **kwargs):
    def decorator(fn):
        try:
            import frappe  # type: ignore
        except ImportError:
            return fn  # Offline import only; no HTTP server exists without Frappe.
        return frappe.whitelist(*args, **kwargs)(fn)
        return fn
    return decorator


def _failure_response(capability, reason, request_id=None, http_status=None):
    status = ActionStatus.FORBIDDEN if reason == ActionReasonCode.AUTH_REQUIRED else ActionStatus.NOT_AVAILABLE
    outcome = ActionResponseBuilder.build_failure_outcome(
        status=status, reason_code=reason, capability=capability, client_request_id=request_id)
    status_code, headers, body = ActionResponseBuilder.serialize_response(outcome)
    headers["Cache-Control"] = "private, " + headers["Cache-Control"]
    # Frappe passes Response objects through; returning a dict adds another message.
    return Response(json.dumps({"message": body}, ensure_ascii=False),
                    status=http_status or status_code, headers=headers)


def _frappe_post_handler(capability: str):
    """Strict denied/disabled HTTP boundary until N0 native composition qualifies."""
    try:
        import frappe  # type: ignore
    except ImportError:
        # Preserve the direct, no-framework offline denial contract. This cannot
        # be served as authenticated HTTP and never produces successful data.
        return _failure_response(capability, ActionReasonCode.CAPABILITY_DISABLED).get_json()
    user = getattr(getattr(frappe, "session", None), "user", None)
    if not isinstance(user, str) or not user or user == "Guest":
        return _failure_response(capability, ActionReasonCode.AUTH_REQUIRED)
    request = getattr(frappe, "request", None)
    if request is None or request.method != "POST":
        return _failure_response(capability, ActionReasonCode.INVALID_REQUEST, http_status=405)
    try:
        body = parse_invoice_http_request(request, capability)
    except RequestTooLarge:
        return _failure_response(capability, ActionReasonCode.INVALID_REQUEST, http_status=413)
    except Exception:
        return _failure_response(capability, ActionReasonCode.INVALID_REQUEST)
    return _failure_response(capability, ActionReasonCode.CAPABILITY_DISABLED, body["request_id"])


# Explicit method exports with disabled defaults and guest forbidden


@frappe_whitelist(allow_guest=False, methods=["POST"])
def get_context():
    """POST /api/method/lotus_fin.api.invoice_actions_api.get_context"""
    return _frappe_post_handler("invoice.context")


@frappe_whitelist(allow_guest=False, methods=["POST"])
def search_invoices():
    """POST /api/method/lotus_fin.api.invoice_actions_api.search_invoices"""
    return _frappe_post_handler("invoice.search")


@frappe_whitelist(allow_guest=False, methods=["POST"])
def open_invoice():
    """POST /api/method/lotus_fin.api.invoice_actions_api.open_invoice"""
    return _frappe_post_handler("invoice.open")
