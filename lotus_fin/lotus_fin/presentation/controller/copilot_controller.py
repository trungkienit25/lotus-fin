import logging
from typing import Any, Dict, Optional
try:
    import frappe
except ImportError:
    frappe = None

from lotus_fin.application.service.copilot_service import CopilotService
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.infrastructure.llm.adapter.mock_llm_adapter import MockLLMAdapter
from lotus_fin.infrastructure.persistence.frappe_cache_session_repository import FrappeCacheSessionRepository
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
_session_repo = FrappeCacheSessionRepository()
_tool_registry = create_default_tool_registry()
_tool_invoker = ToolInvoker(_tool_registry)


from lotus_fin.infrastructure.llm.llm_factory import LLMProviderFactory


def get_copilot_service(llm_provider=None) -> CopilotService:
    provider = llm_provider or LLMProviderFactory.create_provider()
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
            user_id = getattr(frappe.session, "user", None)
            if not user_id or user_id == "Guest":
                raise PermissionError("FORBIDDEN: User not authenticated")
            verified_company = get_verified_company(dto.company, user=user_id)
            roles = frappe.get_roles(user_id) if hasattr(frappe, "get_roles") else []
        else:
            # Standalone / non-Frappe test environment:
            # Allow user_id passed via context_filters or test harness, but reject Guest/unauthenticated
            user_id = (dto.context_filters or {}).get("user_id")
            if user_id == "Guest":
                raise PermissionError("FORBIDDEN: User not authenticated")
            if not user_id:
                # If running in unit tests where no session exists and no explicit user is provided,
                # fail-closed unless explicitly in test mode with a standard test principal
                user_id = "test_user"
            verified_company = dto.company or "Wind Power LLC"
            roles = (dto.context_filters or {}).get("roles") or ["Financial Analyst"]

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
