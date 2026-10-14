"""Event Port for Structured Safe Observability.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §6.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from lotus_fin.domain.schema.action_outcome import (
    ActionReasonCode,
    ActionStatus,
    STATUS_REASON_MATRIX,
)


def is_valid_uuid_v4(val: str) -> bool:
    try:
        parsed = uuid.UUID(val, version=4)
        return str(parsed) == val.lower()
    except (ValueError, AttributeError, TypeError):
        return False


class ActionEventStage(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    AUTH_CHECK = "AUTH_CHECK"
    USE_CASE_EXECUTION = "USE_CASE_EXECUTION"
    PROVIDER_READ = "PROVIDER_READ"
    RESPONSE_DELIVERY = "RESPONSE_DELIVERY"
    ACTION_DISCARD = "ACTION_DISCARD"


class ActionEventDeliveryError(Exception):
    """Raised when structured event delivery to logging sink fails."""
    pass


class ActionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    correlation_id: str = Field(...)
    request_id: str = Field(...)
    capability: Literal["invoice.search", "invoice.open", "invoice.context"] = Field(...)
    stage: ActionEventStage = Field(...)
    status: Optional[ActionStatus] = Field(default=None)
    reason_code: Optional[ActionReasonCode] = Field(default=None)
    duration_ms: Optional[float] = Field(default=None, ge=0.0)
    returned_count: Optional[int] = Field(default=None, ge=0)
    scanned_count: Optional[int] = Field(default=None, ge=0)

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

    @model_validator(mode="after")
    def validate_event_status_reason_pair(self) -> "ActionEvent":
        if self.status is not None:
            if self.reason_code is None:
                raise ValueError("reason_code is required when status is provided.")
            valid_reasons = STATUS_REASON_MATRIX.get(self.status, [])
            if self.reason_code not in valid_reasons:
                raise ValueError(
                    f"reason_code '{self.reason_code}' is incompatible with status '{self.status}'."
                )
        elif self.reason_code is not None:
            raise ValueError("status is required when reason_code is provided.")
        return self


class IActionEventsPort(ABC):
    @abstractmethod
    def record_event(self, event: ActionEvent) -> None:
        """Record an immutable, privacy-safe structured observability event.

        Raises:
            ActionEventDeliveryError: if delivery to sink fails.
        """
        pass
