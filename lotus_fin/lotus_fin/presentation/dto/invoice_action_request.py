"""Invoice Action Request DTOs.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Dict, Literal, Optional
from datetime import date, datetime
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


class ContextDataDTO(BaseModel):
    """Public ContextData; authenticated token expiry is supplied by the controller."""
    model_config = ConfigDict(extra="forbid", strict=True)
    context_ref: str = Field(..., min_length=1, max_length=2048)
    context_version: str = Field(..., min_length=1, max_length=128)
    company_label: str = Field(..., min_length=1, max_length=128)
    allowed_filters: tuple[Literal["invoice_name_prefix"], Literal["posting_date"], Literal["docstatus"]] = (
        "invoice_name_prefix", "posting_date", "docstatus")
    default_posting_from: date
    default_posting_to: date
    expires_at: datetime

    @field_validator("default_posting_from", "default_posting_to", mode="before")
    @classmethod
    def json_date(cls, value):
        if value is None:
            raise ValueError("Posting dates cannot be null")
        if isinstance(value, str):
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError("Noncanonical date")
            return parsed
        return value

    @field_validator("expires_at", mode="before")
    @classmethod
    def json_datetime(cls, value):
        if value is None:
            raise ValueError("expires_at cannot be null")
        if isinstance(value, str):
            v = value.replace("Z", "+00:00") if value.endswith("Z") else value
            parsed = datetime.fromisoformat(v)
            return parsed
        return value


class SearchRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    request_id: str = Field(...)
    context_ref: str = Field(..., min_length=1, max_length=2048)
    expected_context_version: str = Field(..., min_length=1, max_length=128)
    invoice_type: Literal["SALES"] = Field("SALES")
    filters: InvoiceReadFilters = Field(...)
    page_size: int = Field(default=20, ge=1, le=50)
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
