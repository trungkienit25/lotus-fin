from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SendMessageDTO(BaseModel):
    message: str = Field(..., description="Natural language inquiry from user")
    company: Optional[str] = Field(default=None, description="Optional target company parameter")
    session_id: Optional[str] = Field(default=None, description="Client session ID")
    as_of_date: Optional[str] = Field(default=None, description="Optional cutoff date")
    context_filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context metadata")
