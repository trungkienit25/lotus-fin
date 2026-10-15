"""
Lotus Fin API - Copilot Whitelisted Endpoints.
Clean Architecture Entrypoints delegating to Presentation Controller (CopilotController).
"""

import logging
from typing import Any, Dict, List, Optional
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


@whitelist(allow_guest=True)
def chat_copilot(
    query: str,
    company: Optional[str] = None,
    as_of_date: Optional[str] = None,
    session_id: Optional[str] = None
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
            "as_of_date": as_of_date,
            "session_id": session_id
        })
    except PermissionError:
        # Re-raise authentication / authorization failures fail-closed
        raise
    except Exception as e:
        _logger.warning("Clean architecture copilot routing failed, falling back to legacy: %s", str(e))
        return process_copilot_query(
            query=query,
            company=company,
            as_of_date=as_of_date
        )


@whitelist()
def get_chat_history(
    session_id: str,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves the persistent conversation message list from database / cache.
    Enforces multi-tenant ownership boundaries.
    """
    return CopilotController.handle_get_chat_history(
        session_id=session_id,
        company=company
    )


@whitelist()
def list_chat_sessions(
    company: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Lists conversation sessions for the current company/user.
    """
    return CopilotController.handle_list_chat_sessions(
        company=company,
        limit=limit
    )


@whitelist()
def reset_chat_session(
    session_id: str,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clears conversation history for the specified session.
    """
    return CopilotController.handle_reset_chat_session(
        session_id=session_id,
        company=company
    )


@whitelist()
def get_operation_logs(
    session_id: Optional[str] = None,
    company: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieves structured AI Sandbox operational audit logs for compliance review.
    """
    return CopilotController.handle_get_operation_logs(
        session_id=session_id,
        company=company,
        limit=limit
    )


@whitelist()
def export_operation_logs(
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exports full operation audit logs in JSON format for FinTechathon Item 06 evidence.
    """
    return CopilotController.handle_export_operation_logs(
        company=company
    )
