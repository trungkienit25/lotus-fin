import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolExecutionResult(BaseModel):
    tool_call_id: str = Field(..., description="Correlating ID with ToolCallRequest")
    tool_name: str = Field(..., description="Tool name executed")
    is_success: bool = Field(True, description="Whether execution was successful")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Deterministic financial results or payload")
    error_message: Optional[str] = Field(default=None, description="Error reason if execution failed")
    ui_widget: Optional[Dict[str, Any]] = Field(default=None, description="Optional structured UI widget for Desk frontend")

    def to_json_string(self) -> str:
        """Serializes data for LLM context inclusion."""
        if not self.is_success:
            return json.dumps({"status": "error", "error": self.error_message or "Execution failed"}, default=str)
        return json.dumps(self.data or {}, default=str)

