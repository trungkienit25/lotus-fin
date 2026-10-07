"""
Lotus Fin API - Copilot whitelisted endpoint.
Clean Architecture Entrypoint delegating to Presentation Controller.
"""

import logging
from typing import Any, Dict, Optional
try:
    import frappe
    whitelist = frappe.whitelist
except ImportError:
    frappe = None
    def whitelist(*args, **kwargs):
        def decorator(f):
            return f
        return decorator if not args or callable(args[0]) is False else args[0]

from lotus_fin.core.ai.agent_copilot import process_copilot_query
from lotus_fin.presentation.controller.copilot_controller import CopilotController

_logger = logging.getLogger("lotus_fin.api.copilot")


@whitelist()
def chat_copilot(
    query: str,
    company: Optional[str] = None,
    as_of_date: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Public whitelisted endpoint for Lotus Fin AI Copilot chat interface.
    Delegates to Clean Architecture Presentation Controller (CopilotController).
    """
    try:
        return CopilotController.handle_send_message({
            "message": query,
            "company": company,
            "as_of_date": as_of_date,
            "session_id": session_id
        })
    except Exception as e:
        # If PermissionError or CompanyAccessError, fail-closed immediately
        err_type = type(e).__name__
        if "PermissionError" in err_type or "CompanyAccessError" in err_type or "FORBIDDEN" in str(e):
            _logger.error("Copilot access forbidden: %s", str(e))
            if frappe and hasattr(frappe, "throw"):
                frappe.throw(str(e), exc=type(e))
            raise

        _logger.exception("Clean architecture copilot routing failed: %s", str(e))
        # Attempt fallback to legacy agent router only for routing/adapter mismatches
        try:
            return process_copilot_query(
                query=query,
                company=company,
                as_of_date=as_of_date
            )
        except Exception as legacy_err:
            _logger.exception("Legacy copilot fallback also failed: %s", str(legacy_err))
            raise e
