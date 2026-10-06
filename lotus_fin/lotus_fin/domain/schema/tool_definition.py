from typing import Any, Dict
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Purpose and execution guidelines for LLM")
    parameters_schema: Dict[str, Any] = Field(..., description="OpenAI / JSON Schema specification for input parameters")

    def to_openai_dict(self) -> Dict[str, Any]:
        """Formats into OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema
            }
        }
