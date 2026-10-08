from typing import Callable, List, Optional
from lotus_fin.application.port.i_llm_provider import ILLMProvider, LLMResponse
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_definition import ToolDefinition


class MockLLMAdapter(ILLMProvider):
    """
    Mock adapter that simulates function calling and final synthesis
    for unit testing without external network calls.
    """
    def __init__(
        self,
        canned_tool_call: Optional[ToolCallRequest] = None,
        canned_response: str = "This is a mock LLM answer based on grounded financial data."
    ):
        self.canned_tool_call = canned_tool_call
        self.canned_response = canned_response
        self.invocations: List[List[ChatMessage]] = []

    def generate(self, messages: List[ChatMessage], tools: List[ToolDefinition]) -> LLMResponse:
        self.invocations.append(list(messages))

        # Check if the last message is a TOOL execution result
        last_msg = messages[-1] if messages else None
        if last_msg and last_msg.role == MessageRole.TOOL:
            # LLM has already received the tool output, now synthesizes final response
            return LLMResponse(content=self.canned_response)

        # If we have a canned tool call and it hasn't been executed yet, issue it
        if self.canned_tool_call:
            # Verify the tool requested is in tools
            tool_names = [t.name for t in tools]
            if self.canned_tool_call.tool_name in tool_names:
                return LLMResponse(
                    content="",
                    tool_calls=[self.canned_tool_call]
                )

        return LLMResponse(content=self.canned_response)

