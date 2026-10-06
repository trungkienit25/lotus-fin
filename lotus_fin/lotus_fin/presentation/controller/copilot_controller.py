import logging
from typing import Any, Dict, Optional
try:
    import frappe
except ImportError:
    frappe = None

from lotus_fin.application.service.copilot_service import CopilotService
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.infrastructure.llm.adapter.mock_llm_adapter import MockLLMAdapter
from lotus_fin.infrastructure.persistence.in_memory_session_repository import InMemorySessionRepository
from lotus_fin.infrastructure.tool.invoker.tool_invoker import ToolInvoker
from lotus_fin.infrastructure.tool.registry.default_tools import create_default_tool_registry
from lotus_fin.presentation.dto.chat_request import SendMessageDTO
from lotus_fin.presentation.dto.chat_response import ChatResponseDTO

try:
    from lotus_fin.security.access import get_verified_company
except ImportError:
    def get_verified_company(company=None):
        return company or "Wind Power LLC"

_logger = logging.getLogger("lotus_fin.presentation.controller.copilot")

# Singleton service instances for session reuse
_session_repo = InMemorySessionRepository()
_tool_registry = create_default_tool_registry()
_tool_invoker = ToolInvoker(_tool_registry)


def get_copilot_service(llm_provider=None) -> CopilotService:
    provider = llm_provider or MockLLMAdapter()
    return CopilotService(
        llm_provider=provider,
        tool_registry=_tool_registry,
        tool_invoker=_tool_invoker,
        session_repository=_session_repo
    )


class CopilotController:
    """
    Presentation controller orchestrating Frappe web requests into Clean Architecture.
    Validates inputs, sets up UserPrincipal security context, and delegates to CopilotService.
    """

    @classmethod
    def handle_send_message(cls, request_data: Dict[str, Any], service: Optional[CopilotService] = None) -> Dict[str, Any]:
        dto = SendMessageDTO(**request_data)
        if frappe and hasattr(frappe, "session") and frappe.session:
            verified_company = get_verified_company(dto.company)
            user_id = frappe.session.user or "Administrator"
            roles = frappe.get_roles(user_id) if hasattr(frappe, "get_roles") else ["System Manager"]
        else:
            verified_company = dto.company or "Wind Power LLC"
            user_id = "Administrator"
            roles = ["System Manager"]

        user = UserPrincipal(
            user_id=user_id,
            company=verified_company,
            roles=roles,
            as_of_date=dto.as_of_date or "2026-12-31"
        )

        session_id = dto.session_id or f"{user_id}_{verified_company}"
        copilot_svc = service or get_copilot_service()

        res_dict = copilot_svc.process_message(
            session_id=session_id,
            message=dto.message,
            user=user
        )

        # Validate through DTO
        response_dto = ChatResponseDTO(**res_dict)
        return response_dto.model_dump()
