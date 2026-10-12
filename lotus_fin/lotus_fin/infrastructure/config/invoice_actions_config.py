"""Invoice Actions Configuration - Strict Immutable Security Config.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §7.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ApprovedConnection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    product_id: str = Field(..., min_length=1)
    site_id: str = Field(..., min_length=1)
    connection_id: str = Field(..., min_length=1)
    connection_version: str = Field(..., min_length=1)
    allowed_companies: List[str] = Field(..., min_length=1)


class InvoiceActionsConfig(BaseModel):
    """Configuration for Invoice Actions foundation. Disabled by default."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    enabled: bool = Field(default=False)
    signing_key_id: str = Field(..., min_length=1, max_length=64)
    signing_secret: str = Field(..., min_length=32)
    reference_ttl_seconds: int = Field(default=300, ge=60, le=3600)  # default 5min
    deadline_ms: int = Field(default=5000, ge=1000, le=30000)
    page_size_default: int = Field(default=20, ge=1, le=50)
    page_size_max: int = Field(default=50, ge=1, le=50)
    allowed_capabilities: List[str] = Field(
        default_factory=lambda: ["invoice.context", "invoice.search", "invoice.open"]
    )
    connections: Dict[str, ApprovedConnection] = Field(default_factory=dict)
