"""
Lotus Fin API - Copilot whitelisted endpoint.
"""

from typing import Any, Dict, Optional
import frappe
from lotus_fin.core.ai.agent_copilot import process_copilot_query


@frappe.whitelist()
def chat_copilot(
    query: str,
    company: Optional[str] = None,
    as_of_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Public whitelisted endpoint for Lotus Fin AI Copilot chat interface.
    Accepts natural language user query and routes to tool calling engine.
    """
    return process_copilot_query(
        query=query,
        company=company,
        as_of_date=as_of_date
    )
