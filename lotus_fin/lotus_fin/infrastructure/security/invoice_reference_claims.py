"""Purpose-specific and Versioned Reference Claims.

SSOT: CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md Â§3, Â§5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class SelectionClaimsV2(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    binding_version: Literal["ref.v2"] = Field("ref.v2")
    purpose: Literal["invoice.open"] = Field("invoice.open")
    contract_version: Literal["p1.invoice.v1"] = Field("p1.invoice.v1")
    query_fingerprint: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    key_id: str = Field(..., min_length=1, max_length=64)
    actor_id: str = Field(..., pattern=r"^aref_[0-9a-f]{64}$")
    auth_session_binding: str = Field(..., min_length=1, max_length=128)
    site_id: str = Field(..., min_length=1, max_length=128)
    product_id: str = Field(..., min_length=1, max_length=128)
    connection_id: str = Field(..., min_length=1, max_length=128)
    connection_version: str = Field(..., min_length=1, max_length=64)
    company_id: str = Field(..., min_length=1, max_length=128)
    context_version: str = Field(..., min_length=1, max_length=128)
    projection_version: Literal["invoice.min.v1"] = Field(...)
    doc_type: Literal["Sales Invoice"] = Field("Sales Invoice")
    doc_id: str = Field(..., min_length=1, max_length=128)
    record_version: str = Field(..., min_length=1, max_length=64)
    issued_at: int = Field(..., ge=0)
    expires_at: int = Field(..., ge=0)


class CursorClaimsV2(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    binding_version: Literal["ref.v2"] = Field("ref.v2")
    purpose: Literal["invoice.cursor"] = Field("invoice.cursor")
    key_id: str = Field(..., min_length=1, max_length=64)
    actor_id: str = Field(..., pattern=r"^aref_[0-9a-f]{64}$")
    auth_session_binding: str = Field(..., min_length=1, max_length=128)
    site_id: str = Field(..., min_length=1, max_length=128)
    product_id: str = Field(..., min_length=1, max_length=128)
    connection_id: str = Field(..., min_length=1, max_length=128)
    connection_version: str = Field(..., min_length=1, max_length=64)
    company_id: str = Field(..., min_length=1, max_length=128)
    context_version: str = Field(..., min_length=1, max_length=128)
    projection_version: Literal["invoice.min.v1"] = Field(...)
    last_id: str = Field(..., min_length=1, max_length=128)
    upper_id: str = Field(..., min_length=1, max_length=128)
    page_size: int = Field(..., ge=1, le=50)
    order: Literal["name ASC"] = Field("name ASC")
    contract_version: Literal["p1.invoice.v1"] = Field("p1.invoice.v1")
    page_index: int = Field(..., ge=1, le=5)
    query_fingerprint: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    issued_at: int = Field(..., ge=0)
    expires_at: int = Field(..., ge=0)
