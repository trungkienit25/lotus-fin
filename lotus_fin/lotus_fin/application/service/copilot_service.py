import logging
import time
from typing import Any, Dict, Optional
from lotus_fin.application.agent.agent_runner import AgentRunner
from lotus_fin.application.agent.prompt_engine import PromptEngine
from lotus_fin.application.port.i_chat_service import IChatService
from lotus_fin.application.port.i_llm_provider import ILLMProvider
from lotus_fin.application.port.i_operation_log_service import IOperationLogService
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
        agent_runner: Optional[AgentRunner] = None,
        log_service: Optional[IOperationLogService] = None
    ):
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.tool_invoker = tool_invoker
        self.session_repository = session_repository
        self.agent_runner = agent_runner or AgentRunner(llm_provider, tool_invoker)
        self.log_service = log_service

    def process_message(
        self,
        session_id: str,
        message: str,
        user: UserPrincipal
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # 1. Retrieve or initialize chat session with strict tenant & ownership boundary checks
        session = self.session_repository.get_session(session_id)
        if not session:
            session = ChatSession(
                id=session_id,
                user_id=user.user_id,
                company=user.company
            )
        else:
            if session.user_id != user.user_id:
                raise PermissionError(f"FORBIDDEN: Session {session_id} does not belong to user {user.user_id}")
            if session.company != user.company:
                raise PermissionError(f"FORBIDDEN: Session {session_id} belongs to company {session.company}, not {user.company}")

        # 2. Add incoming user message (bounded to prevent memory overflow)
        session.add_message(ChatMessage(role=MessageRole.USER, content=message), max_history=60)

        # 3. Assemble dynamic system prompt
        system_prompt = PromptEngine.assemble_system_prompt(user)

        # 4. Resolve authorized tool definitions
        tools = self.tool_registry.get_available_tools(user)

        # 5. Execute ReAct Loop
        agent_res = self.agent_runner.run(session, system_prompt, tools, user)

        # 6. Persist updated session to database / cache repository
        self.session_repository.save_session(session)

        # 7. Audit log operation for FinTechathon Item 06 compliance
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        trace_id = None
        if self.log_service:
            try:
                log_entry = self.log_service.log_operation(
                    session_id=session_id,
                    user=user,
                    prompt=message,
                    reply=agent_res.reply,
                    tool_called=agent_res.tool_called,
                    tool_inputs=agent_res.tool_output.get("_inputs") if isinstance(agent_res.tool_output, dict) else None,
                    tool_output=agent_res.tool_output,
                    latency_ms=latency_ms,
                    status="SUCCESS",
                    llm_provider=getattr(self.llm_provider, "provider_name", "llm"),
                    model_name=getattr(self.llm_provider, "model_name", None)
                )
                trace_id = log_entry.log_id
            except Exception as e:
                _logger.warning("Audit logging failed in copilot service: %s", e)

        # 8. Format clean payload for presentation layer
        return {
            "session_id": session_id,
            "reply": agent_res.reply,
            "tool_called": agent_res.tool_called,
            "tool_label": agent_res.tool_called.replace("_", " ").title() if agent_res.tool_called else None,
            "tool_output": agent_res.tool_output,
            "ui_widget": agent_res.ui_widget,
            "executed_tools": agent_res.executed_tools,
            "trace_id": trace_id,
            "latency_ms": latency_ms
        }


