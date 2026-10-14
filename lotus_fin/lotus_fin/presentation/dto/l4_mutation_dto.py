"""L4 Mutation Presentation DTOs.

SSOT: LOTUS FIN P6-1 — IMPLEMENT L4 CONFIRMED MUTATION ENGINE.
ADR001: Strict typed boundary models.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from lotus_fin.domain.schema.l4_action_catalog import L4ActionId, L4OperationState
from lotus_fin.domain.model.l4_operation_record import L4ActionProposal, L4OperationRecord


class L4ProposeRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(..., min_length=1, max_length=64)
    action_id: L4ActionId
    arguments: Dict[str, Any]
    simulated: bool = False


class L4ProposeResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    success: bool
    proposal: Optional[L4ActionProposal] = None
    error_message: Optional[str] = None


class L4ConfirmRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_id: str = Field(..., min_length=1, max_length=64)
    proposal_id: str = Field(..., min_length=16, max_length=64)
    confirmation_challenge: str = Field(..., min_length=32, max_length=128)
    claimed_arguments: Optional[Dict[str, Any]] = None


class L4ConfirmResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    success: bool
    state: L4OperationState
    operation: Optional[L4OperationRecord] = None
    error_message: Optional[str] = None


class L4StatusRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_id: str = Field(..., min_length=1, max_length=64)
    operation_id: str = Field(..., min_length=16, max_length=64)


class L4StatusResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    success: bool
    operation: Optional[L4OperationRecord] = None
    error_message: Optional[str] = None


class L4CancelRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_id: str = Field(..., min_length=1, max_length=64)
    proposal_id: str = Field(..., min_length=16, max_length=64)


class L4CancelResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    success: bool
    error_message: Optional[str] = None


class L4ReconcileRequestDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_id: str = Field(..., min_length=1, max_length=64)
    operation_id: str = Field(..., min_length=16, max_length=64)


class L4ReconcileResponseDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    success: bool
    state: L4OperationState
    operation: Optional[L4OperationRecord] = None
    error_message: Optional[str] = None
