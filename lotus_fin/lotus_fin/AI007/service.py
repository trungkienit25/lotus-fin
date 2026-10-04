"""
Lotus Fin AI007 — Service Layer for Financial Copilot.
Exposes Frappe whitelisted endpoints for frontend chat interfaces.
"""

import frappe
import json

from .models import CopilotRequest
from .orchestrator import CopilotOrchestrator


@frappe.whitelist()
def chat(message: str, session_id: str, context: str = "{}"):
    """
    API endpoint chính cho Copilot.
    Frontend gửi message, Backend xử lý NLP và routing tới các module tài chính.
    """
    try:
        req_context = json.loads(context) if isinstance(context, str) else context
        
        request = CopilotRequest(
            message=message,
            session_id=session_id,
            context=req_context
        )
        
        orchestrator = CopilotOrchestrator()
        response = orchestrator.process_request(request)
        
        return {
            "status": "success",
            "data": {
                "session_id": response.session_id,
                "intent": response.intent.value,
                "reply": response.reply_message,
                "suggested_actions": response.suggested_next_steps,
                "ui_widgets": response.ui_widgets,
                "data_mode": response.data_mode
            }
        }
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="AI007 Copilot Chat Error")
        return {"status": "error", "message": str(e)}
