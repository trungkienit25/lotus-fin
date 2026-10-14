"""Strict P1 outcome schema — MASTER SSOT §3; ADR001."""

from datetime import datetime
from math import isfinite
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import zoneinfo
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ActionStatus(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    FORBIDDEN = "FORBIDDEN"
    SOURCE_ERROR = "SOURCE_ERROR"
    TIMEOUT = "TIMEOUT"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ActionReasonCode(str, Enum):
    RESULTS_FOUND = "RESULTS_FOUND"
    EMPTY_RESULT = "EMPTY_RESULT"
    DOCUMENT_READY = "DOCUMENT_READY"
    CONTEXT_READY = "CONTEXT_READY"
    COVERAGE_INCOMPLETE = "COVERAGE_INCOMPLETE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    CSRF_OR_ORIGIN_DENIED = "CSRF_OR_ORIGIN_DENIED"
    COMPANY_DENIED = "COMPANY_DENIED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    ACCESS_DENIED = "ACCESS_DENIED"
    SOURCE_FAILURE = "SOURCE_FAILURE"
    INVALID_PROVIDER_RESPONSE = "INVALID_PROVIDER_RESPONSE"
    DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"
    INVALID_REQUEST = "INVALID_REQUEST"
    CONTEXT_REQUIRED = "CONTEXT_REQUIRED"
    CONTEXT_CHANGED = "CONTEXT_CHANGED"
    STALE_SELECTION = "STALE_SELECTION"
    STALE_CURSOR = "STALE_CURSOR"
    DOCUMENT_UNAVAILABLE = "DOCUMENT_UNAVAILABLE"
    PROJECTION_UNAVAILABLE = "PROJECTION_UNAVAILABLE"
    TARGET_UNQUALIFIED = "TARGET_UNQUALIFIED"
    CAPABILITY_DISABLED = "CAPABILITY_DISABLED"
    UNSUPPORTED_INTENT = "UNSUPPORTED_INTENT"
    INVALID_OUTCOME = "INVALID_OUTCOME"


STATUS_REASON_MATRIX: Dict[ActionStatus, List[ActionReasonCode]] = {
    ActionStatus.OK: [
        ActionReasonCode.RESULTS_FOUND,
        ActionReasonCode.EMPTY_RESULT,
        ActionReasonCode.DOCUMENT_READY,
        ActionReasonCode.CONTEXT_READY,
    ],
    ActionStatus.PARTIAL: [
        ActionReasonCode.COVERAGE_INCOMPLETE,
    ],
    ActionStatus.FORBIDDEN: [
        ActionReasonCode.AUTH_REQUIRED,
        ActionReasonCode.CSRF_OR_ORIGIN_DENIED,
        ActionReasonCode.COMPANY_DENIED,
        ActionReasonCode.CAPABILITY_DENIED,
        ActionReasonCode.ACCESS_DENIED,
    ],
    ActionStatus.SOURCE_ERROR: [
        ActionReasonCode.SOURCE_FAILURE,
        ActionReasonCode.INVALID_PROVIDER_RESPONSE,
    ],
    ActionStatus.TIMEOUT: [
        ActionReasonCode.DEADLINE_EXCEEDED,
    ],
    ActionStatus.NOT_AVAILABLE: [
        ActionReasonCode.INVALID_REQUEST,
        ActionReasonCode.CONTEXT_REQUIRED,
        ActionReasonCode.CONTEXT_CHANGED,
        ActionReasonCode.STALE_SELECTION,
        ActionReasonCode.STALE_CURSOR,
        ActionReasonCode.DOCUMENT_UNAVAILABLE,
        ActionReasonCode.PROJECTION_UNAVAILABLE,
        ActionReasonCode.TARGET_UNQUALIFIED,
        ActionReasonCode.CAPABILITY_DISABLED,
        ActionReasonCode.UNSUPPORTED_INTENT,
        ActionReasonCode.INVALID_OUTCOME,
    ],
}


class SourceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    mode: Literal["ERP_READ", "DEMO_ISOLATED"] = Field(...)
    verification: Literal["AUTHORIZED_READ"] = Field("AUTHORIZED_READ")
    product_ref: str = Field(..., min_length=1, max_length=128)
    site_ref: str = Field(..., min_length=1, max_length=128)
    connection_ref: str = Field(..., min_length=1, max_length=128)
    connection_version: str = Field(..., min_length=1, max_length=64)
    projection_version: Literal["invoice.min.v1"] = Field("invoice.min.v1")
    observed_at: str = Field(..., min_length=1, max_length=64)
    timezone: str = Field(..., min_length=1, max_length=64)
    coverage: Literal["PAGE_COMPLETE", "INCOMPLETE"] = Field(...)
    consistency: Literal["LIVE_KEYSET"] = Field("LIVE_KEYSET")

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at_format(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            raise ValueError(f"observed_at '{v}' must be a valid ISO 8601 timestamp.")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone_format(cls, v: str) -> str:
        try:
            zoneinfo.ZoneInfo(v)
        except Exception:
            raise ValueError(f"timezone '{v}' must be a valid IANA timezone.")
        return v


def scan_for_nested_denial(obj: Any) -> bool:
    pending, remaining = [(obj, 0)], 4096
    forbidden = STATUS_REASON_MATRIX[ActionStatus.FORBIDDEN]
    while pending:
        node, depth = pending.pop()
        remaining -= 1
        if depth > 16 or remaining < 0 or (isinstance(node, (dict, list)) and len(node) > remaining):
            raise ValueError("Unsupported nested outcome shape or size.")
        if isinstance(node, dict):
            status, reason = node.get("status"), node.get("reason_code")
            if status in [ActionStatus.FORBIDDEN, *forbidden] or reason in forbidden:
                return True
            if (("status" in node and status not in list(ActionStatus))
                    or ("reason_code" in node and reason not in list(ActionReasonCode))
                    or (status is not None and reason is not None
                        and reason not in STATUS_REASON_MATRIX[ActionStatus(status)])):
                raise ValueError("Unsupported nested outcome shape.")
            pending.extend((value, depth + 1) for value in node.values())
        elif isinstance(node, list):
            pending.extend((value, depth + 1) for value in node)
        elif node is not None and (type(node) not in (str, bool, int, float)
                                  or (type(node) is float and not isfinite(node))):
            raise ValueError("Unsupported nested outcome shape.")
    return False


def scan_for_selection_ref(obj: Any) -> bool:
    if isinstance(obj, dict):
        if obj.get("selection_ref") is not None:
            return True
        return any(scan_for_selection_ref(v) for v in obj.values())
    if isinstance(obj, list):
        return any(scan_for_selection_ref(item) for item in obj)
    return False


class ActionOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    contract_version: Literal["p1.invoice.v1"] = Field("p1.invoice.v1")
    status: ActionStatus = Field(...)
    reason_code: ActionReasonCode = Field(...)
    correlation_id: str = Field(..., min_length=1, max_length=64)
    request_id: str = Field(..., min_length=1, max_length=64)
    capability: Literal["invoice.search", "invoice.open", "invoice.context"] = Field(...)
    source: Optional[SourceEvidence] = Field(default=None)
    context_version: Optional[str] = Field(default=None, max_length=128)
    data: Optional[Any] = Field(default=None)
    user_message: str = Field(..., min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_outcome_consistency(self) -> "ActionOutcome":
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
                raise ValueError(f"Data must be null for status '{self.status}'.")
            if self.source is not None:
                raise ValueError(f"Source evidence must be null for failure status '{self.status}'.")
        if self.status == ActionStatus.OK:
            if self.source is None:
                raise ValueError("OK status requires valid source evidence.")
            if self.source.coverage != "PAGE_COMPLETE":
                raise ValueError("OK status requires source coverage='PAGE_COMPLETE'.")
            if scan_for_nested_denial(self.data):
                raise ValueError("OK outcome cannot contain recognized nested denial.")
        if self.status == ActionStatus.PARTIAL:
            if self.source is None or self.source.coverage != "INCOMPLETE":
                raise ValueError("PARTIAL status requires source coverage='INCOMPLETE'.")
            if scan_for_nested_denial(self.data):
                raise ValueError("PARTIAL outcome cannot contain recognized nested denial.")
            if scan_for_selection_ref(self.data):
                raise ValueError("PARTIAL outcome cannot issue selection_ref.")
        return self
