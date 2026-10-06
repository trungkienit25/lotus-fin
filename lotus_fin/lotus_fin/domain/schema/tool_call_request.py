from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolCallRequest(BaseModel):
    id: str = Field(..., description="Unique ID of the tool call")
    tool_name: str = Field(..., description="Name of the tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Parsed arguments dictionary")
