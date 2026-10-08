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
    as_of_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Public whitelisted endpoint for Lotus Fin AI Copilot chat interface.
    Delegates to Clean Architecture Presentation Controller (CopilotController).
    Falls back gracefully to legacy router to guarantee zero regression.
    """
    try:
        return CopilotController.handle_send_message({
            "message": query,
            "company": company,
            "as_of_date": as_of_date
        })
    except Exception as e:
        _logger.warning("Clean architecture copilot routing failed, falling back to legacy: %s", str(e))
        return process_copilot_query(
            query=query,
            company=company,
            as_of_date=as_of_date
        )
