"""Authorized Read Context - Strict Immutable Request-Local Model.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §4.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from datetime import datetime
from typing import Literal, Optional
import uuid
import zoneinfo
from pydantic import BaseModel, ConfigDict, Field, field_validator


def is_valid_uuid_v4(val: str) -> bool:
    try:
        parsed = uuid.UUID(val, version=4)
        return str(parsed) == val.lower()
    except (ValueError, AttributeError, TypeError):
        return False


class AuthorizedReadContext(BaseModel):
    """Immutable, server-derived request-local context for authorized actions."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    actor_id: str = Field(..., min_length=1, max_length=128)
    auth_session_binding: str = Field(..., min_length=1, max_length=128)
    site_id: str = Field(..., min_length=1, max_length=128)
    product_id: str = Field(..., min_length=1, max_length=128)
    connection_id: str = Field(..., min_length=1, max_length=128)
    connection_version: str = Field(..., min_length=1, max_length=64)
    company_id: str = Field(..., min_length=1, max_length=128)
    capability: Literal["invoice.search", "invoice.open", "invoice.context"] = Field(...)
    projection_version: Literal["invoice.min.v1"] = Field("invoice.min.v1")
    context_version: str = Field(..., min_length=1, max_length=128)
    observed_at_utc: str = Field(..., min_length=1, max_length=64)
    timezone: str = Field(..., min_length=1, max_length=64)
    deadline_at_utc: str = Field(..., min_length=1, max_length=64)
    correlation_id: str = Field(...)
    request_id: str = Field(...)
    adapter_mode: Literal["ERP_READ", "DEMO_ISOLATED"] = Field("ERP_READ")

    @field_validator("correlation_id")
    @classmethod
    def validate_cid(cls, v: str) -> str:
        if not is_valid_uuid_v4(v):
            raise ValueError(f"correlation_id '{v}' must be a valid UUID v4")
        return v

    @field_validator("request_id")
    @classmethod
    def validate_req_id(cls, v: str) -> str:
        if not is_valid_uuid_v4(v):
            raise ValueError(f"request_id '{v}' must be a valid UUID v4")
        return v

    @field_validator("observed_at_utc", "deadline_at_utc")
    @classmethod
    def validate_iso_timestamps(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            raise ValueError(f"Timestamp '{v}' must be a valid ISO 8601 string.")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_tz(cls, v: str) -> str:
        try:
            zoneinfo.ZoneInfo(v)
        except Exception:
            raise ValueError(f"Timezone '{v}' must be a valid IANA timezone.")
        return v
