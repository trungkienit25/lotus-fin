"""L4 Presentation Controller.

SSOT: LOTUS FIN P6-1 — IMPLEMENT L4 CONFIRMED MUTATION ENGINE.
ADR001: Strict Clean Architecture, < 200 lines, fail-closed handling.
"""

from typing import Any, Dict, Optional, Tuple
from lotus_fin.application.service.l4_mutation_service import L4MutationService
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.l4_action_catalog import L4OperationState
from lotus_fin.presentation.dto.l4_mutation_dto import (
    L4CancelRequestDTO,
    L4CancelResponseDTO,
    L4ConfirmRequestDTO,
    L4ConfirmResponseDTO,
    L4ProposeRequestDTO,
    L4ProposeResponseDTO,
    L4ReconcileRequestDTO,
    L4ReconcileResponseDTO,
    L4StatusRequestDTO,
    L4StatusResponseDTO,
)


class L4MutationController:
    """Controller handling L4 proposed/confirmed mutations."""

    def __init__(self, service: L4MutationService) -> None:
        self._service = service

    def propose_action(
        self,
        principal: UserPrincipal,
        session_id: str,
        site_id: str,
        raw_body: Dict[str, Any],
    ) -> Tuple[int, Dict[str, Any]]:
        try:
            req = L4ProposeRequestDTO(**raw_body)
        except Exception as e:
            return 400, L4ProposeResponseDTO(success=False, error_message=f"Invalid request: {e}").model_dump()

        ok, proposal, err = self._service.propose_action(
            principal=principal,
            session_id=session_id,
            site_id=site_id,
            action_id=req.action_id,
            arguments=req.arguments,
            is_simulated=req.simulated,
        )
        if not ok or not proposal:
            return 403 if "role" in (err or "").lower() or "unauth" in (err or "").lower() else 400, \
                L4ProposeResponseDTO(success=False, error_message=err).model_dump()

        return 200, L4ProposeResponseDTO(success=True, proposal=proposal).model_dump()

    def confirm_action(
        self,
        principal: UserPrincipal,
        session_id: str,
        raw_body: Dict[str, Any],
    ) -> Tuple[int, Dict[str, Any]]:
        try:
            req = L4ConfirmRequestDTO(**raw_body)
        except Exception as e:
            return 400, L4ConfirmResponseDTO(
                success=False,
                state=L4OperationState.REJECTED,
                error_message=f"Invalid confirmation request: {e}",
            ).model_dump()

        state, op, err = self._service.confirm_action(
            principal=principal,
            session_id=session_id,
            proposal_id=req.proposal_id,
            challenge=req.confirmation_challenge,
            claimed_args=req.claimed_arguments,
        )
        success = state == L4OperationState.SUCCEEDED
        status_code = 200 if success or state in (L4OperationState.CONFIRMED, L4OperationState.UNKNOWN_OUTCOME) else 400
        return status_code, L4ConfirmResponseDTO(
            success=success,
            state=state,
            operation=op,
            error_message=err,
        ).model_dump()

    def get_operation_status(
        self,
        principal: UserPrincipal,
        raw_body: Dict[str, Any],
    ) -> Tuple[int, Dict[str, Any]]:
        try:
            req = L4StatusRequestDTO(**raw_body)
        except Exception as e:
            return 400, L4StatusResponseDTO(success=False, error_message=f"Invalid status request: {e}").model_dump()

        op, err = self._service.get_operation_status(principal=principal, operation_id=req.operation_id)
        if not op:
            return 404, L4StatusResponseDTO(success=False, error_message=err).model_dump()

        return 200, L4StatusResponseDTO(success=True, operation=op).model_dump()

    def cancel_pending_proposal(
        self,
        principal: UserPrincipal,
        session_id: str,
        raw_body: Dict[str, Any],
    ) -> Tuple[int, Dict[str, Any]]:
        try:
            req = L4CancelRequestDTO(**raw_body)
        except Exception as e:
            return 400, L4CancelResponseDTO(success=False, error_message=f"Invalid cancel request: {e}").model_dump()

        ok, err = self._service.cancel_pending_proposal(
            principal=principal,
            session_id=session_id,
            proposal_id=req.proposal_id,
        )
        if not ok:
            return 400, L4CancelResponseDTO(success=False, error_message=err).model_dump()

        return 200, L4CancelResponseDTO(success=True).model_dump()

    def reconcile_operation(
        self,
        principal: UserPrincipal,
        raw_body: Dict[str, Any],
    ) -> Tuple[int, Dict[str, Any]]:
        try:
            req = L4ReconcileRequestDTO(**raw_body)
        except Exception as e:
            return 400, L4ReconcileResponseDTO(
                success=False,
                state=L4OperationState.REJECTED,
                error_message=f"Invalid reconcile request: {e}",
            ).model_dump()

        state, op, err = self._service.reconcile_operation(principal=principal, operation_id=req.operation_id)
        success = state == L4OperationState.SUCCEEDED
        return 200 if op else 400, L4ReconcileResponseDTO(
            success=success,
            state=state,
            operation=op,
            error_message=err,
        ).model_dump()
