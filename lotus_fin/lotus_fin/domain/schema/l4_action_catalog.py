"""L4 Action Catalog: Strict typed definitions for Lotus-owned confirmed mutations.

SSOT: LOTUS FIN P6-1 — L4 CONFIRMED MUTATION ENGINE.
ADR001: Clean Architecture, strict Pydantic models, no dynamic tools, no ERPNext tables.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class L4ActionId(str, Enum):
    TASK_CREATE = "lotus.task.create"
    NOTE_CREATE = "lotus.note.create"
    DRAFT_RECORD_PREPARE = "lotus.draft_record.prepare"


class L4TargetEntity(str, Enum):
    LOTUS_TASK = "LotusTask"
    LOTUS_NOTE = "LotusNote"
    LOTUS_DRAFT_RECORD = "LotusDraftRecord"


class L4OperationState(str, Enum):
    PROPOSED = "PROPOSED"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CONFIRMED = "CONFIRMED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    RECONCILING = "RECONCILING"


class L4TaskArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str = Field(..., min_length=1, max_length=140)
    description: str = Field(..., min_length=1, max_length=2000)
    due_date: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priority: str = Field("MEDIUM", pattern=r"^(LOW|MEDIUM|HIGH|URGENT)$")


class L4NoteArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str = Field(..., min_length=1, max_length=140)
    content: str = Field(..., min_length=1, max_length=5000)
    category: str = Field("GENERAL", pattern=r"^(GENERAL|FOLLOWUP|AUDIT|MEETING)$")


class L4DraftRecordArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    record_type: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_\.]+$")
    payload_summary: str = Field(..., min_length=1, max_length=500)
    target_reference: Optional[str] = Field(None, max_length=128)


class L4ActionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action_id: L4ActionId
    version: str = "v1"
    target_entity: L4TargetEntity
    required_roles: List[str]
    allowed_side_effects: List[str]
    is_financial_mutation: bool = False
    feature_flag_key: str
    description: str


L4_ACTION_CATALOG: Dict[L4ActionId, L4ActionMetadata] = {
    L4ActionId.TASK_CREATE: L4ActionMetadata(
        action_id=L4ActionId.TASK_CREATE,
        version="v1",
        target_entity=L4TargetEntity.LOTUS_TASK,
        required_roles=["Accounts User", "Accounts Manager", "System Manager"],
        allowed_side_effects=["AUDIT_LOG_ENTRY", "LOTUS_TASK_INSERT"],
        is_financial_mutation=False,
        feature_flag_key="enable_l4_task_actions",
        description="Create a Lotus-owned follow-up Task in an isolated Lotus table/store",
    ),
    L4ActionId.NOTE_CREATE: L4ActionMetadata(
        action_id=L4ActionId.NOTE_CREATE,
        version="v1",
        target_entity=L4TargetEntity.LOTUS_NOTE,
        required_roles=["Accounts User", "Accounts Manager", "System Manager"],
        allowed_side_effects=["AUDIT_LOG_ENTRY", "LOTUS_NOTE_INSERT"],
        is_financial_mutation=False,
        feature_flag_key="enable_l4_note_actions",
        description="Create a Lotus-owned Note in an isolated Lotus table/store",
    ),
    L4ActionId.DRAFT_RECORD_PREPARE: L4ActionMetadata(
        action_id=L4ActionId.DRAFT_RECORD_PREPARE,
        version="v1",
        target_entity=L4TargetEntity.LOTUS_DRAFT_RECORD,
        required_roles=["Accounts Manager", "System Manager"],
        allowed_side_effects=["AUDIT_LOG_ENTRY", "LOTUS_DRAFT_STAGE"],
        is_financial_mutation=False,
        feature_flag_key="enable_l4_draft_actions",
        description="Prepare a draft record in an approved Lotus-owned target stage",
    ),
}
