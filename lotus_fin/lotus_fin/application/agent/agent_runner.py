import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from lotus_fin.application.port.i_llm_provider import ILLMProvider
from lotus_fin.application.port.i_tool_invoker import IToolInvoker
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult

_logger = logging.getLogger("lotus_fin.application.agent.agent_runner")


class AgentExecutionResult(BaseModel):
    reply: str = Field(..., description="Final natural language response for user")
    tool_called: Optional[str] = Field(default=None, description="Primary tool executed if any")
    tool_output: Optional[Dict[str, Any]] = Field(default=None, description="Raw deterministic data returned by tool")
    ui_widget: Optional[Dict[str, Any]] = Field(default=None, description="UI Widget payload for frontend rendering")
    executed_tools: List[str] = Field(default_factory=list, description="List of all tools invoked in session")
    status: str = Field(default="SUCCESS", description="Execution status e.g. SUCCESS, BUDGET_EXCEEDED")


import re

def sanitize_executive_reply(text: str) -> str:
    """
    Automated Presentation Gate (English-First Standard):
    Enforces that internal DB columns, raw boolean flags, implementation version keys,
    and technical artifacts are stripped or converted to natural executive English
    before persisting or presenting to users.
    """
    if not text:
        return text

    # 1. Strip raw boolean tags and keys in parentheses or standalone
    # e.g. (has_constituent_deficit: false), (has_constituent_deficit: true), has_constituent_deficit: false
    text = re.sub(r'\(?\bhas_constituent_deficit:\s*(?:true|false|None)\)?\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(?\bconstituent_deficit:\s*(?:true|false|None)\)?\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(?\bopening_cash_deficit:\s*(?:true|false|None)\)?\.?', '', text, flags=re.IGNORECASE)

    # 2. Strip raw shortfall events array or keys
    # e.g. (shortfall_events: []), shortfall_events: []
    text = re.sub(r'\(?\bshortfall_events:\s*\[\s*\]\)?\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(?\bshortfall_events\b\)?', '', text, flags=re.IGNORECASE)

    # 3. Strip internal methodology / contract version tags
    # e.g. (STRICT_BASELINE_V1), STRICT_BASELINE_V1
    text = re.sub(r'\(?\bSTRICT_BASELINE_V1\)?\.?', '', text)
    text = re.sub(r'\(?\bTRADE_ONLY\)?\.?', '', text)
    text = re.sub(r'\(?\bNO_CONFIRMED_SETTLEMENT_EVENTS\)?\.?', '', text)
    text = re.sub(r'\(?\bFORECAST_UNAVAILABLE\)?\.?', '', text)
    text = re.sub(r'\(?\bVALIDATION_ERROR\)?\.?', '', text)
    text = re.sub(r'\(?\bINCONSISTENT_DATA\)?\.?', '', text)

    # 4. Clean up trailing double spaces, empty parentheses (), and orphaned punctuation
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\s+\.', '.', text)
    text = re.sub(r'\s+,', ',', text)

    return text.strip()


class AgentRunner:
    """
    Controlled ReAct Agent Loop:
    1. Injects grounded system prompt and user query.
    2. Calls LLM with strict Whitelist Tools.
    3. If tool requested: invokes tool deterministically via IToolInvoker, appends Tool message to context, repeats.
    4. Enforces max_iterations = 4 to guarantee termination and prevent infinite loops.
    """
    def __init__(
        self,
        llm_provider: ILLMProvider,
        tool_invoker: IToolInvoker,
        max_iterations: int = 4,
        max_total_tools: int = 6
    ):
        self.llm_provider = llm_provider
        self.tool_invoker = tool_invoker
        self.max_iterations = max_iterations
        self.max_total_tools = max_total_tools

    def run(
        self,
        session: ChatSession,
        system_prompt: str,
        tools: List[ToolDefinition],
        user: UserPrincipal
    ) -> AgentExecutionResult:
        # Build working context for the current turn
        working_context: List[ChatMessage] = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)
        ] + session.get_context_window(max_messages=8)

        iteration = 0
        total_tools_executed = 0
        is_budget_exceeded = False
        executed_tool_name: Optional[str] = None
        executed_tool_output: Optional[Dict[str, Any]] = None
        executed_ui_widget: Optional[Dict[str, Any]] = None
        executed_tools_list: List[str] = []

        while iteration < self.max_iterations:
            iteration += 1
            _logger.debug("AgentRunner iteration %d with %d messages", iteration, len(working_context))

            response = self.llm_provider.generate(working_context, tools)

            # Case A: LLM produced final answer with no further tool calls
            if not response.has_tool_calls:
                final_content = response.content or "Analysis completed."
                # Automation Gate: Sanitize executive reply before persistence and return
                final_content = sanitize_executive_reply(final_content)
                session.add_message(ChatMessage(role=MessageRole.ASSISTANT, content=final_content))
                return AgentExecutionResult(
                    reply=final_content,
                    tool_called=executed_tool_name,
                    tool_output=executed_tool_output,
                    ui_widget=executed_ui_widget,
                    executed_tools=executed_tools_list,
                    status="BUDGET_EXCEEDED" if is_budget_exceeded else "SUCCESS"
                )

            # Case B: LLM requested tool invocation(s)
            working_context.append(ChatMessage(
                role=MessageRole.ASSISTANT,
                content=response.content or "",
                tool_calls=response.tool_calls
            ))

            for call in response.tool_calls or []:
                if total_tools_executed >= self.max_total_tools:
                    _logger.warning("AgentRunner total tool budget reached (%d tools)", self.max_total_tools)
                    budget_err = ToolExecutionResult(
                        tool_call_id=call.id,
                        tool_name=call.tool_name,
                        is_success=False,
                        error_message=f"Tool budget limit reached ({self.max_total_tools} calls per turn)."
                    )
                    session.add_tool_trace(budget_err)
                    working_context.append(ChatMessage(
                        role=MessageRole.TOOL,
                        content=budget_err.to_json_string(),
                        tool_call_id=call.id
                    ))
                    is_budget_exceeded = True
                    break

                _logger.info("AgentRunner dispatching tool: %s (%s)", call.tool_name, call.id)
                tool_res: ToolExecutionResult = self.tool_invoker.invoke(call, user)
                total_tools_executed += 1
                session.add_tool_trace(tool_res)

                executed_tool_name = call.tool_name
                executed_tools_list.append(call.tool_name)
                if tool_res.data:
                    executed_tool_output = tool_res.data
                if tool_res.ui_widget:
                    executed_ui_widget = tool_res.ui_widget

                # Append tool result into context for next ReAct cycle
                working_context.append(ChatMessage(
                    role=MessageRole.TOOL,
                    content=tool_res.to_json_string(),
                    tool_call_id=call.id
                ))

        # Safeguard fallback if iteration limit is reached
        fallback_msg = "Complex financial operation analyzed. Please review the extracted metrics below."
        session.add_message(ChatMessage(role=MessageRole.ASSISTANT, content=fallback_msg))
        return AgentExecutionResult(
            reply=fallback_msg,
            tool_called=executed_tool_name,
            tool_output=executed_tool_output,
            ui_widget=executed_ui_widget,
            executed_tools=executed_tools_list,
            status="BUDGET_EXCEEDED" if is_budget_exceeded else "SUCCESS"
        )
