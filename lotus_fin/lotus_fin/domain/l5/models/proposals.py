"""L5 Proposal, Ledger and Evidence Schemas - Lotus Fin P6-2."""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from lotus_fin.domain.l5.models.contracts import (
    L5ActionFamily,
    L5ApprovalLevel,
    L5ProposalState,
    L5RiskLevel,
)


def compute_canonical_hash(data: Dict[str, Any]) -> str:
    """Deterministic canonical JSON SHA-256 hash."""
    canonical_str = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


class L5TargetSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    doctype: str = Field(..., min_length=1, max_length=128)
    doc_id: str = Field(..., min_length=1, max_length=128)
    expected_docstatus: Optional[int] = Field(default=None)
    resource_version: str = Field(..., min_length=1, max_length=128)
    company: str = Field(..., min_length=1, max_length=128)


class L5Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    proposal_id: str = Field(..., min_length=1, max_length=64)
    schema_version: Literal["l5.action.v1"] = "l5.action.v1"
    family: L5ActionFamily
    action_name: str = Field(..., min_length=1, max_length=128)
    
    actor: str = Field(..., min_length=1, max_length=128)
    session_id: str = Field(..., min_length=1, max_length=128)
    site: str = Field(..., min_length=1, max_length=128)
    company: str = Field(..., min_length=1, max_length=128)
    
    target: L5TargetSpec
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    risk_level: L5RiskLevel
    required_approval_level: L5ApprovalLevel
    consequence_description: str = Field(..., min_length=1, max_length=512)
    is_reversible: bool = False
    
    state: L5ProposalState = L5ProposalState.DRAFT_PROPOSED
    
    canonical_hash: str = Field(..., min_length=64, max_length=64)
    review_challenge_hash: Optional[str] = Field(default=None, max_length=64)
    
    created_at_epoch: float
    expires_at_epoch: float
    consumed_at_epoch: Optional[float] = None
    
    additional_approvals: List[Dict[str, Any]] = Field(default_factory=list)


class L5LedgerEntry(BaseModel):
    """Operation Ledger record for durable idempotency and status reconciliation."""
    model_config = ConfigDict(extra="forbid", strict=True)
    operation_id: str = Field(..., min_length=1, max_length=64)
    proposal_id: str = Field(..., min_length=1, max_length=64)
    family: L5ActionFamily
    action_name: str = Field(..., min_length=1, max_length=128)
    
    site: str
    company: str
    actor: str
    session_id: str
    
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    state: L5ProposalState
    
    attempt_count: int = Field(default=0, ge=0)
    fencing_lease_expires_at: Optional[float] = None
    
    target_identity: Optional[str] = None
    terminal_receipt: Optional[Dict[str, Any]] = None
    failure_reason: Optional[str] = None
    
    created_at_epoch: float
    updated_at_epoch: float


class L5AuditRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    audit_id: str
    correlation_id: str
    timestamp_iso: str
    actor: str
    session_id: str
    site: str
    company: str
    family: L5ActionFamily
    action_name: str
    proposal_id: str
    operation_id: Optional[str] = None
    event_type: str
    risk_level: L5RiskLevel
    outcome_state: L5ProposalState
    details: Dict[str, Any] = Field(default_factory=dict)
