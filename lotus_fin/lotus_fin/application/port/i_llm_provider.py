from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_definition import ToolDefinition


class LLMResponse(BaseModel):
    content: Optional[str] = Field(default="", description="Textual response generated")
    tool_calls: Optional[List[ToolCallRequest]] = Field(default=None, description="Tool calls requested by LLM")

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls and len(self.tool_calls) > 0)


class ILLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[ChatMessage], tools: List[ToolDefinition]) -> LLMResponse:
        """Invokes provider with conversation history and available tool specifications."""
        pass
