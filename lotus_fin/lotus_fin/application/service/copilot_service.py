import logging
from typing import Any, Dict, Optional
from lotus_fin.application.agent.agent_runner import AgentRunner
from lotus_fin.application.agent.prompt_engine import PromptEngine
from lotus_fin.application.port.i_chat_service import IChatService
from lotus_fin.application.port.i_llm_provider import ILLMProvider
from lotus_fin.application.port.i_tool_invoker import IToolInvoker
from lotus_fin.application.port.i_tool_registry import IToolRegistry
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.repository.i_session_repository import ISessionRepository

_logger = logging.getLogger("lotus_fin.application.service.copilot")


class CopilotService(IChatService):
    def __init__(
        self,
        llm_provider: ILLMProvider,
        tool_registry: IToolRegistry,
        tool_invoker: IToolInvoker,
        session_repository: ISessionRepository,
        agent_runner: Optional[AgentRunner] = None
    ):
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.tool_invoker = tool_invoker
        self.session_repository = session_repository
        self.agent_runner = agent_runner or AgentRunner(llm_provider, tool_invoker)

    def process_message(
        self,
        session_id: str,
        message: str,
        user: UserPrincipal
    ) -> Dict[str, Any]:
        # 1. Retrieve or initialize chat session
        session = self.session_repository.get_session(session_id)
        if not session:
            session = ChatSession(
                id=session_id,
                user_id=user.user_id,
                company=user.company
            )
        else:
            # Enforce multi-tenant and session ownership isolation
            if session.user_id != user.user_id:
                _logger.warning("Session security violation: session user %s != caller %s", session.user_id, user.user_id)
                raise PermissionError("FORBIDDEN: Session does not belong to the current authenticated user.")
            if session.company != user.company:
                _logger.warning("Session boundary violation: session company %s != user company %s", session.company, user.company)
                raise PermissionError("FORBIDDEN: Session does not belong to the active company context.")

        # 2. Add incoming user message
        session.add_message(ChatMessage(role=MessageRole.USER, content=message))

        # 3. Assemble dynamic system prompt
        system_prompt = PromptEngine.assemble_system_prompt(user)

        # 4. Resolve authorized tool definitions
        tools = self.tool_registry.get_available_tools(user)

        # 5. Execute ReAct Loop
        agent_res = self.agent_runner.run(session, system_prompt, tools, user)

        # 6. Persist updated session
        self.session_repository.save_session(session)

        # 7. Format clean payload for presentation layer
        return {
            "session_id": session_id,
            "reply": agent_res.reply,
            "tool_called": agent_res.tool_called,
            "tool_label": agent_res.tool_called.replace("_", " ").title() if agent_res.tool_called else None,
            "tool_output": agent_res.tool_output,
            "ui_widget": agent_res.ui_widget,
            "executed_tools": agent_res.executed_tools
        }

