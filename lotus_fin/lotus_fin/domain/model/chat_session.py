from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatSession(BaseModel):
    id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="Owner user ID")
    company: str = Field(..., description="Company boundary")
    messages: List[ChatMessage] = Field(default_factory=list, description="Ordered conversation history")
    tool_traces: List[ToolExecutionResult] = Field(default_factory=list, description="Executed tools traces in session")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)
        self.updated_at = utc_now()

    def add_tool_trace(self, trace: ToolExecutionResult) -> None:
        self.tool_traces.append(trace)
        self.updated_at = utc_now()

    def get_context_window(self, max_messages: int = 10) -> List[ChatMessage]:
        """Returns the most recent messages up to window size."""
        if len(self.messages) <= max_messages:
            return list(self.messages)
        return list(self.messages[-max_messages:])
