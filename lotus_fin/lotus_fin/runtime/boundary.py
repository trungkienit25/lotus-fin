"""Authoritative request boundary: principal authentication, session revocation, and error hardening."""
import hmac
import json
import frappe  # type: ignore

CORE_METHODS = frozenset({
    "lotus_fin.api.copilot_integration_api.dispatch",
    "lotus_fin.runtime.health.readiness",
    "lotus_fin.api.invoice_actions_api.get_context",
    "lotus_fin.api.invoice_actions_api.search_invoices",
    "lotus_fin.api.invoice_actions_api.open_invoice",
    "lotus_fin.api.copilot_api.chat_copilot",
    "lotus_fin.api.copilot_api.get_chat_history",
    "lotus_fin.api.copilot_api.list_chat_sessions",
    "lotus_fin.api.copilot_api.reset_chat_session",
    "lotus_fin.api.copilot_api.get_operation_logs",
    "lotus_fin.api.copilot_api.export_operation_logs",
    "lotus_fin.api.copilot_api.search_real_invoices",
    "lotus_fin.api.copilot_api.get_real_overdue_invoices",
    "lotus_fin.api.copilot_api.create_real_task",
    "lotus_fin.api.ai_insights.get_financial_snapshot",
    "lotus_fin.api.ai_insights.get_ai002_cash_forecast",
    "lotus_fin.api.ai_insights.get_risk_signal",
    "lotus_fin.modules.f005_financing.service.simulate_what_if",
})

POST_ONLY_CORE_METHODS = frozenset({
    "lotus_fin.api.copilot_integration_api.dispatch",
    "lotus_fin.api.invoice_actions_api.get_context",
    "lotus_fin.api.invoice_actions_api.search_invoices",
    "lotus_fin.api.invoice_actions_api.open_invoice",
    "lotus_fin.api.copilot_api.chat_copilot",
    "lotus_fin.api.copilot_api.search_real_invoices",
    "lotus_fin.api.copilot_api.get_real_overdue_invoices",
    "lotus_fin.api.copilot_api.create_real_task",
})


def _is_user_enabled(user: str) -> bool:
    """Authoritative check of persisted enabled state in database; fails closed."""
    db = getattr(frappe, "db", None)
    if db is None:
        return False
    try:
        # cache=False bypasses stale per-process grant cache
        val = db.get_value("User", user, "enabled", cache=False)
        return val is not None and int(val) == 1
    except Exception:
        return False


def _is_session_active(user: str, sid: str) -> bool:
    """Validate session is active in Frappe's tabSessions table; fails closed."""
    db = getattr(frappe, "db", None)
    if db is None:
        return False
    try:
        records = db.sql(
            "SELECT status FROM tabSessions WHERE sid = %s AND user = %s",
            (sid, user),
            as_dict=True,
        )
        if not records:
            return False
        return records[0].get("status") == "Active"
    except Exception:
        return False


def validate_authenticated_principal(user: str, sid: str | None = None) -> None:
    """Validate that the caller is an active, enabled principal with a valid session."""
    if not isinstance(user, str) or not user or user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)

    # Validate authoritative persisted user status
    if not _is_user_enabled(user):
        frappe.throw("User account is disabled or missing", frappe.AuthenticationError)

    # Validate session state if a session ID is present
    if sid and sid != "Guest":
        if not _is_session_active(user, sid):
            frappe.throw("Session is revoked or expired", frappe.AuthenticationError)


def enforce_request_boundary():
    """Enforce request boundary before Frappe resolves/dispatches RPCs."""
    # 1. Error boundary: suppress stacktrace disclosure across serving surface
    try:
        flags = getattr(frappe.local, "flags", None)
        if flags is not None:
            flags.disable_traceback = True
    except Exception:
        pass

    methods = [frappe.form_dict.get("cmd", "")]
    path = getattr(frappe.request, "path", "")
    for prefix in ("/api/method/", "/api/v2/method/"):
        if path.startswith(prefix):
            methods.append(path[len(prefix):].replace("/", "."))

    for method in methods:
        if not isinstance(method, str) or not method.startswith("lotus_fin."):
            continue

        session = getattr(frappe, "session", None)
        user = getattr(session, "user", None) if session else None
        sid = getattr(session, "sid", None) if session else None

        # Authoritative principal & session verification
        validate_authenticated_principal(user, sid)

        if method in CORE_METHODS:
            req_method = getattr(frappe.request, "method", "")
            if method in POST_ONLY_CORE_METHODS and req_method != "POST":
                frappe.throw("POST method required", frappe.PermissionError)

            if req_method == "POST":
                local_session = getattr(getattr(frappe, "local", None), "session", None)
                data = getattr(local_session, "data", {}) if local_session else {}
                saved = data.get("csrf_token") if isinstance(data, dict) else None
                headers = getattr(frappe.request, "headers", {})
                supplied = headers.get("X-Frappe-CSRF-Token")
                if (not isinstance(saved, str) or not saved
                        or not isinstance(supplied, str)
                        or not hmac.compare_digest(saved, supplied)):
                    frappe.throw("CSRF verification failed", frappe.CSRFTokenError)
            continue

        apps = frappe.get_installed_apps()
        qualified = (
            frappe.conf.get("lotus_erpnext_integration_qualified") is True
            and "erpnext" in apps and "lotus_erpnext" in apps
        )
        if not qualified:
            frappe.throw("Legacy Lotus capability is unavailable", frappe.PermissionError)


def sanitize_error_response(request=None, response=None):
    """Error boundary: scrub stacktrace / internal paths from error responses."""
    if response is None:
        return response
    data_bytes = getattr(response, "data", None)
    if not data_bytes or not isinstance(data_bytes, (bytes, bytearray)):
        return response
    headers = getattr(response, "headers", {})
    content_type = headers.get("Content-Type", "") if hasattr(headers, "get") else ""
    if "application/json" not in content_type:
        return response
    try:
        payload = json.loads(data_bytes.decode("utf-8"))
        if not isinstance(payload, dict):
            return response
        modified = False
        if "exc" in payload:
            del payload["exc"]
            modified = True
        if "exception" in payload and isinstance(payload["exception"], str) and "Traceback" in payload["exception"]:
            del payload["exception"]
            modified = True
        if "errors" in payload and isinstance(payload["errors"], list):
            for err in payload["errors"]:
                if isinstance(err, dict) and "exception" in err:
                    if "Traceback" in str(err["exception"]):
                        del err["exception"]
                        modified = True
        if modified:
            response.data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except Exception:
        pass
    return response
