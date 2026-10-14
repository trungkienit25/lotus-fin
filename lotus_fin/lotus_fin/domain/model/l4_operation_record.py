"""L4 Proposal and Ledger Domain Models.

SSOT: LOTUS FIN P6-1 — IMPLEMENT L4 CONFIRMED MUTATION ENGINE.
ADR001: Strict immutability, canonical digests, isolated ledger state tracking.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from lotus_fin.domain.schema.l4_action_catalog import (
    L4ActionId,
    L4OperationState,
    L4TargetEntity,
)


def compute_canonical_digest(data: Dict[str, Any]) -> str:
    """Deterministic SHA-256 digest of JSON-serialized dictionary."""
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class L4FieldDiff(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    field_name: str
    old_value: Optional[str] = None
    new_value: str
    description: str


class L4ActionProposal(BaseModel):
    """Immutable proposal for an L4 action."""
    model_config = ConfigDict(extra="forbid", strict=True)

    proposal_id: str = Field(..., min_length=16, max_length=64)
    action_id: L4ActionId
    target_entity: L4TargetEntity
    arguments: Dict[str, Any]
    canonical_args_digest: str = Field(..., min_length=64, max_length=64)

    actor_id: str = Field(..., min_length=1, max_length=128)
    session_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field(..., min_length=1, max_length=128)
    site_id: str = Field(..., min_length=1, max_length=128)

    source_version: str = Field("v1", min_length=1, max_length=32)
    policy_version: str = Field("p6.l4.v1", min_length=1, max_length=32)

    issued_at_utc: str = Field(..., min_length=19, max_length=32)
    expires_at_utc: str = Field(..., min_length=19, max_length=32)
    confirmation_challenge: str = Field(..., min_length=32, max_length=128)

    preview_title: str = Field(..., min_length=1, max_length=140)
    preview_diff: List[L4FieldDiff] = Field(default_factory=list)
    simulated: bool = False

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        now = current_time or datetime.now(timezone.utc)
        exp = datetime.fromisoformat(self.expires_at_utc)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now >= exp

    def verify_integrity(self) -> bool:
        """Verify that arguments match the canonical digest."""
        computed = compute_canonical_digest(self.arguments)
        return computed == self.canonical_args_digest


class L4OperationRecord(BaseModel):
    """Durable record in the L4 operation ledger."""
    model_config = ConfigDict(extra="forbid", strict=True)

    operation_id: str = Field(..., min_length=16, max_length=64)
    proposal_id: str = Field(..., min_length=16, max_length=64)
    action_id: L4ActionId
    target_entity: L4TargetEntity
    actor_id: str
    tenant_id: str
    site_id: str
    session_id: str

    state: L4OperationState
    canonical_args_digest: str
    challenge_used: bool = False

    created_at_utc: str
    updated_at_utc: str
    confirmed_at_utc: Optional[str] = None
    completed_at_utc: Optional[str] = None

    execution_attempts: int = 0
    result_data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    is_synthetic_demo: bool = False
    reconciliation_notes: Optional[str] = None
