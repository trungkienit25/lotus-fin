"""Action Outcome Presentation DTO.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import uuid
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from lotus_fin.domain.schema.action_outcome import (
    ActionOutcome,
    ActionReasonCode,
    ActionStatus,
    SourceEvidence,
    STATUS_REASON_MATRIX,
    scan_for_nested_denial,
    scan_for_selection_ref,
)


def is_valid_uuid_v4(val: str) -> bool:
    try:
        parsed = uuid.UUID(val, version=4)
        return str(parsed) == val.lower()
    except (ValueError, AttributeError, TypeError):
        return False


class ActionOutcomeDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    contract_version: Literal["p1.invoice.v1"] = Field("p1.invoice.v1")
    status: ActionStatus = Field(...)
    reason_code: ActionReasonCode = Field(...)
    correlation_id: str = Field(...)
    request_id: str = Field(...)
    capability: Literal["invoice.search", "invoice.open", "invoice.context"] = Field(...)
    source: Optional[Dict[str, Any]] = Field(default=None)
    context_version: Optional[str] = Field(default=None)
    data: Optional[Any] = Field(default=None)
    user_message: str = Field(...)

    @field_validator("correlation_id")
    @classmethod
    def validate_correlation_id(cls, v: str) -> str:
        if not is_valid_uuid_v4(v):
            raise ValueError(f"correlation_id '{v}' must be a valid UUID v4")
        return v

    @field_validator("request_id")
    @classmethod
    def validate_request_id(cls, v: str) -> str:
        if not is_valid_uuid_v4(v):
            raise ValueError(f"request_id '{v}' must be a valid UUID v4")
        return v

    @model_validator(mode="after")
    def validate_dto_invariants(self) -> "ActionOutcomeDTO":
        valid_reasons = STATUS_REASON_MATRIX.get(self.status, [])
        if self.reason_code not in valid_reasons:
            raise ValueError(
                f"Reason code '{self.reason_code}' is incompatible with status '{self.status}'."
            )
        if self.status in {
            ActionStatus.FORBIDDEN, ActionStatus.SOURCE_ERROR,
            ActionStatus.TIMEOUT, ActionStatus.NOT_AVAILABLE,
        }:
            if self.data is not None:
                raise ValueError(f"Data must be null for non-successful status '{self.status}'.")
            if self.source is not None:
                raise ValueError(f"Source evidence must be null for failure status '{self.status}'.")
        if self.status == ActionStatus.OK:
            if not self.source:
                raise ValueError("OK status requires valid source evidence.")
            SourceEvidence(**self.source)
            if self.source.get("coverage") != "PAGE_COMPLETE":
                raise ValueError("OK status requires source coverage='PAGE_COMPLETE'.")
            if scan_for_nested_denial(self.data):
                raise ValueError("OK outcome cannot contain recognized nested denial.")
        if self.status == ActionStatus.PARTIAL:
            if not self.source:
                raise ValueError("PARTIAL status requires source evidence.")
            SourceEvidence(**self.source)
            if self.source.get("coverage") != "INCOMPLETE":
                raise ValueError("PARTIAL status requires source coverage='INCOMPLETE'.")
            if scan_for_nested_denial(self.data):
                raise ValueError("PARTIAL outcome cannot contain recognized nested denial.")
            if scan_for_selection_ref(self.data):
                raise ValueError("PARTIAL outcome cannot issue selection_ref.")
        return self

    @classmethod
    def from_domain(cls, outcome: ActionOutcome) -> "ActionOutcomeDTO":
        source_dict = outcome.source.model_dump(mode="json") if outcome.source else None
        return cls(
            contract_version=outcome.contract_version,
            status=outcome.status,
            reason_code=outcome.reason_code,
            correlation_id=outcome.correlation_id,
            request_id=outcome.request_id,
            capability=outcome.capability,
            source=source_dict,
            context_version=outcome.context_version,
            data=outcome.data,
            user_message=outcome.user_message,
        )

    def to_domain(self) -> ActionOutcome:
        source_obj = SourceEvidence(**self.source) if self.source else None
        return ActionOutcome(
            contract_version=self.contract_version,
            status=self.status,
            reason_code=self.reason_code,
            correlation_id=self.correlation_id,
            request_id=self.request_id,
            capability=self.capability,
            source=source_obj,
            context_version=self.context_version,
            data=self.data,
            user_message=self.user_message,
        )
