"""Invoice Action Request DTOs.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Dict, Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


def is_valid_uuid_v4(val: str) -> bool:
    try:
        parsed = uuid.UUID(val, version=4)
        return str(parsed) == val.lower()
    except (ValueError, AttributeError, TypeError):
        return False


class ContextRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str = Field(...)
    company_candidate: str = Field(..., min_length=1, max_length=128)

    @field_validator("request_id")
    @classmethod
    def validate_req_id(cls, v: str) -> str:
        if not is_valid_uuid_v4(v):
            raise ValueError(f"request_id '{v}' must be a valid UUID v4")
        return v


from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters


class SearchRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str = Field(...)
    context_ref: str = Field(..., min_length=1, max_length=2048)
    expected_context_version: str = Field(..., min_length=1, max_length=128)
    invoice_type: Literal["SALES"] = Field("SALES")
    filters: Optional[InvoiceReadFilters] = Field(default=None)
    page_size: Optional[int] = Field(default=20, ge=1, le=50)
    cursor: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("request_id")
    @classmethod
    def validate_req_id(cls, v: str) -> str:
        if not is_valid_uuid_v4(v):
            raise ValueError(f"request_id '{v}' must be a valid UUID v4")
        return v


class OpenRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str = Field(...)
    context_ref: str = Field(..., min_length=1, max_length=2048)
    expected_context_version: str = Field(..., min_length=1, max_length=128)
    selection_ref: str = Field(..., min_length=1, max_length=2048)

    @field_validator("request_id")
    @classmethod
    def validate_req_id(cls, v: str) -> str:
        if not is_valid_uuid_v4(v):
            raise ValueError(f"request_id '{v}' must be a valid UUID v4")
        return v
