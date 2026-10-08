import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest


class ChatMessage(BaseModel):
    role: MessageRole = Field(..., description="Message role (system, user, assistant, tool)")
    content: Optional[str] = Field(default="", description="Textual body")
    tool_calls: Optional[List[ToolCallRequest]] = Field(default=None, description="Tool calls issued by assistant")
    tool_call_id: Optional[str] = Field(default=None, description="Correlating ID when role is tool")

    def to_llm_dict(self) -> Dict[str, Any]:
        """Converts to standard provider dictionary."""
        d: Dict[str, Any] = {
            "role": self.role.value,
            "content": self.content or ""
        }
        if self.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.tool_name,
                        "arguments": tc.arguments if isinstance(tc.arguments, str) else json.dumps(tc.arguments)
                    }
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d
