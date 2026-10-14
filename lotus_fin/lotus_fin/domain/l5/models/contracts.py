"""L5 Action Contracts and Domain Enums - Lotus Fin P6-2."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class L5ActionFamily(str, Enum):
    DOCUMENT_SUBMIT = "DOCUMENT_SUBMIT"
    DOCUMENT_CANCEL = "DOCUMENT_CANCEL"
    EXTERNAL_EMAIL_SEND = "EXTERNAL_EMAIL_SEND"
    PAYMENT_REQUEST = "PAYMENT_REQUEST"
    PAYMENT_EXECUTION = "PAYMENT_EXECUTION"
    SCHEDULED_AUTONOMOUS_ACTION = "SCHEDULED_AUTONOMOUS_ACTION"


class L5RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class L5ApprovalLevel(str, Enum):
    SINGLE_USER_CONFIRM = "SINGLE_USER_CONFIRM"
    DUAL_CONTROL_M_OF_N = "DUAL_CONTROL_M_OF_N"
    FINANCE_OFFICER_GATE = "FINANCE_OFFICER_GATE"
    BOARD_OR_EXECUTIVE_GATE = "BOARD_OR_EXECUTIVE_GATE"
    BLOCKED_DISALLOWED = "BLOCKED_DISALLOWED"


class L5ProposalState(str, Enum):
    DRAFT_PROPOSED = "DRAFT_PROPOSED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    APPROVAL_RESERVED = "APPROVAL_RESERVED"
    EXECUTING = "EXECUTING"
    COMMITTED = "COMMITTED"
    FAILED_ROLLED_BACK = "FAILED_ROLLED_BACK"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    RECONCILED = "RECONCILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class L5AdapterCapabilityState(str, Enum):
    CAPABILITY_DISABLED = "CAPABILITY_DISABLED"
    SIMULATION_QUALIFIED = "SIMULATION_QUALIFIED"
    PRODUCTION_ACTIVE = "PRODUCTION_ACTIVE"  # MUST remain blocked in MVP / candidate


class L5PolicyDecision(str, Enum):
    PERMITTED = "PERMITTED"
    DENIED = "DENIED"
    REQUIRES_STEP_UP = "REQUIRES_STEP_UP"
    CAPABILITY_DISABLED = "CAPABILITY_DISABLED"


class L5PolicyEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    decision: L5PolicyDecision
    reason_code: str
    risk_level: L5RiskLevel
    required_approval_level: L5ApprovalLevel
    details: Dict[str, Any] = Field(default_factory=dict)
