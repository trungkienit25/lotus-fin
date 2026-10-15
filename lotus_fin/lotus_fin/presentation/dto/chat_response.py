from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolTraceDTO(BaseModel):
    tool_name: str
    is_success: bool
    summary: Optional[str] = None


class ChatResponseDTO(BaseModel):
    session_id: str
    reply: str
    tool_called: Optional[str] = None
    tool_label: Optional[str] = None
    tool_output: Optional[Dict[str, Any]] = None
    ui_widget: Optional[Dict[str, Any]] = None
    executed_tools: List[str] = Field(default_factory=list)
    tool_traces: List[Any] = Field(default_factory=list)
    status: str = Field(default="SUCCESS")
    trace_id: Optional[str] = None
    latency_ms: Optional[int] = None
