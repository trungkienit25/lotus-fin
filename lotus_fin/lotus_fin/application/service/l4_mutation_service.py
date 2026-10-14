"""L4 Mutation Engine Application Service.

SSOT: LOTUS FIN P6-1 — IMPLEMENT L4 CONFIRMED MUTATION ENGINE.
ADR001: Strict clean architecture, zero ERPNext dependencies, authenticated confirmation.
"""

from datetime import datetime, timezone, timedelta
import secrets
import threading
from typing import Any, Dict, List, Optional, Tuple
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.l4_action_catalog import (
    L4_ACTION_CATALOG,
    L4ActionId,
    L4DraftRecordArgs,
    L4NoteArgs,
    L4OperationState,
    L4TargetEntity,
    L4TaskArgs,
)
from lotus_fin.domain.model.l4_operation_record import (
    L4ActionProposal,
    L4FieldDiff,
    L4OperationRecord,
    compute_canonical_digest,
)
from lotus_fin.application.port.i_l4_mutation_port import (
    IL4OperationLedger,
    ILotusActionWritePort,
)


class L4MutationService:
    """Core domain service orchestrating proposal, confirmation, execution and reconciliation."""

    def __init__(
        self,
        ledger: IL4OperationLedger,
        write_adapter: ILotusActionWritePort,
        proposal_ttl_seconds: int = 300,
        enable_demo_fallback: bool = True,
    ) -> None:
        self._ledger = ledger
        self._adapter = write_adapter
        self._ttl_seconds = proposal_ttl_seconds
        self._enable_demo = enable_demo_fallback

    def validate_action_args(self, action_id: L4ActionId, raw_args: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Validate arguments strictly against allowlist for the requested action."""
        try:
            if action_id == L4ActionId.TASK_CREATE:
                validated = L4TaskArgs(**raw_args).model_dump()
                return True, validated, None
            elif action_id == L4ActionId.NOTE_CREATE:
                validated = L4NoteArgs(**raw_args).model_dump()
                return True, validated, None
            elif action_id == L4ActionId.DRAFT_RECORD_PREPARE:
                validated = L4DraftRecordArgs(**raw_args).model_dump()
                return True, validated, None
            else:
                return False, None, f"Unsupported action ID: {action_id}"
        except Exception as e:
            return False, None, f"Argument validation failed: {str(e)}"

    def check_authorization(self, principal: UserPrincipal, action_id: L4ActionId) -> Tuple[bool, Optional[str]]:
        """Verify principal has authenticated rights and role assignment."""
        if not principal or not principal.user_id:
            return False, "Unauthenticated principal"
        if principal.user_id.lower() in ("guest", "anonymous"):
            return False, "Guest user prohibited from L4 actions"

        catalog_entry = L4_ACTION_CATALOG.get(action_id)
        if not catalog_entry:
            return False, f"Unknown action: {action_id}"

        user_roles = set(principal.roles or [])
        required = set(catalog_entry.required_roles)
        if not user_roles.intersection(required):
            return False, f"Missing required roles: {catalog_entry.required_roles}"

        return True, None

    def propose_action(
        self,
        principal: UserPrincipal,
        session_id: str,
        site_id: str,
        action_id: L4ActionId,
        arguments: Dict[str, Any],
        is_simulated: bool = False,
    ) -> Tuple[bool, Optional[L4ActionProposal], Optional[str]]:
        """Phase 1: Generate immutable proposal with single-use challenge."""
        # 1. Authorize principal
        auth_ok, auth_err = self.check_authorization(principal, action_id)
        if not auth_ok:
            return False, None, auth_err

        # 2. Validate arguments strictly
        val_ok, validated_args, val_err = self.validate_action_args(action_id, arguments)
        if not val_ok or validated_args is None:
            return False, None, val_err

        # 3. Build digest & timestamps
        digest = compute_canonical_digest(validated_args)
        now_dt = datetime.now(timezone.utc)
        exp_dt = now_dt + timedelta(seconds=self._ttl_seconds)

        proposal_id = f"prop_{secrets.token_hex(16)}"
        challenge = f"chal_{secrets.token_hex(24)}"

        catalog_entry = L4_ACTION_CATALOG[action_id]
        diffs = [
            L4FieldDiff(
                field_name=k,
                old_value=None,
                new_value=str(v),
                description=f"Set {k} on new {catalog_entry.target_entity.value}",
            )
            for k, v in validated_args.items()
        ]

        proposal = L4ActionProposal(
            proposal_id=proposal_id,
            action_id=action_id,
            target_entity=catalog_entry.target_entity,
            arguments=validated_args,
            canonical_args_digest=digest,
            actor_id=principal.user_id,
            session_id=session_id,
            tenant_id=principal.company,
            site_id=site_id,
            source_version="v1",
            policy_version="p6.l4.v1",
            issued_at_utc=now_dt.isoformat(),
            expires_at_utc=exp_dt.isoformat(),
            confirmation_challenge=challenge,
            preview_title=f"{catalog_entry.description} ({proposal_id[:8]})",
            preview_diff=diffs,
            simulated=is_simulated,
        )

        # 4. Save to durable ledger
        self._ledger.save_proposal(proposal)
        return True, proposal, None

    def confirm_action(
        self,
        principal: UserPrincipal,
        session_id: str,
        proposal_id: str,
        challenge: str,
        claimed_args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[L4OperationState, Optional[L4OperationRecord], Optional[str]]:
        """Phase 2: Authenticated one-use confirmation, idempotency reservation and execution."""
        # 1. Fetch proposal
        proposal = self._ledger.get_proposal(proposal_id)
        if not proposal:
            return L4OperationState.REJECTED, None, "Proposal not found"

        # 2. Check tamper / integrity
        if not proposal.verify_integrity():
            return L4OperationState.REJECTED, None, "Proposal tampering detected"

        if claimed_args is not None:
            if compute_canonical_digest(claimed_args) != proposal.canonical_args_digest:
                return L4OperationState.REJECTED, None, "Altered arguments in confirmation"

        # 3. Check expiration
        if proposal.is_expired():
            return L4OperationState.EXPIRED, None, "Proposal has expired"

        # 4. Bindings verification (actor, session, tenant)
        if proposal.actor_id != principal.user_id:
            return L4OperationState.REJECTED, None, "Actor mismatch on confirmation"

        if proposal.session_id != session_id:
            return L4OperationState.REJECTED, None, "Session binding mismatch"

        if proposal.tenant_id != principal.company:
            return L4OperationState.REJECTED, None, "Tenant/company scope mismatch"

        # 5. Fresh server-side permissions recheck
        auth_ok, auth_err = self.check_authorization(principal, proposal.action_id)
        if not auth_ok:
            return L4OperationState.REJECTED, None, f"Fresh authorization check failed: {auth_err}"

        # 6. Check existing idempotent operation for this proposal
        existing = self._ledger.get_operation_by_proposal(proposal_id)
        if existing:
            if existing.state in (L4OperationState.REJECTED, L4OperationState.EXPIRED, L4OperationState.FAILED):
                return existing.state, existing, f"Proposal cannot be confirmed in state: {existing.state.value}"
            # Operation already initiated
            return existing.state, existing, None

        # 7. Reserve confirmation atomically in ledger (consumes challenge)
        reserved, record, res_err = self._ledger.reserve_confirmation(proposal, challenge, session_id)
        if not reserved or not record:
            return L4OperationState.REJECTED, None, res_err or "Challenge already used or invalid"

        # 8. Check target eligibility via adapter
        check_ok, check_msg = self._adapter.prepare_check(proposal)
        if not check_ok:
            record.state = L4OperationState.FAILED
            record.error_code = "PRECHECK_FAILED"
            record.error_message = check_msg
            record.updated_at_utc = datetime.now(timezone.utc).isoformat()
            self._ledger.update_operation(record)
            return record.state, record, check_msg

        # 9. Execute mutation through narrow adapter
        record.state = L4OperationState.EXECUTING
        record.execution_attempts += 1
        record.updated_at_utc = datetime.now(timezone.utc).isoformat()
        self._ledger.update_operation(record)

        try:
            res_data = self._adapter.execute_operation(proposal, record.operation_id)
            record.state = L4OperationState.SUCCEEDED
            record.result_data = res_data
            record.completed_at_utc = datetime.now(timezone.utc).isoformat()
            record.updated_at_utc = record.completed_at_utc
            self._ledger.update_operation(record)
            return record.state, record, None
        except TimeoutError as te:
            # Ambiguous outcome! Must transition to UNKNOWN_OUTCOME
            record.state = L4OperationState.UNKNOWN_OUTCOME
            record.error_code = "TIMEOUT_POSSIBLE_COMMIT"
            record.error_message = str(te)
            record.updated_at_utc = datetime.now(timezone.utc).isoformat()
            self._ledger.update_operation(record)
            return record.state, record, "Operation timed out; outcome ambiguous"
        except Exception as exc:
            record.state = L4OperationState.FAILED
            record.error_code = "EXECUTION_EXCEPTION"
            record.error_message = str(exc)
            record.updated_at_utc = datetime.now(timezone.utc).isoformat()
            self._ledger.update_operation(record)
            return record.state, record, f"Execution failed: {str(exc)}"

    def reconcile_operation(
        self,
        principal: UserPrincipal,
        operation_id: str,
    ) -> Tuple[L4OperationState, Optional[L4OperationRecord], Optional[str]]:
        """Phase 3: Inspect and reconcile an ambiguous UNKNOWN_OUTCOME operation."""
        record = self._ledger.get_operation(operation_id)
        if not record:
            return L4OperationState.REJECTED, None, "Operation not found"

        if record.actor_id != principal.user_id or record.tenant_id != principal.company:
            return L4OperationState.REJECTED, None, "Unauthorized to reconcile this operation"

        if record.state not in (L4OperationState.UNKNOWN_OUTCOME, L4OperationState.EXECUTING):
            return record.state, record, f"Operation is already in terminal state: {record.state}"

        record.state = L4OperationState.RECONCILING
        record.updated_at_utc = datetime.now(timezone.utc).isoformat()
        self._ledger.update_operation(record)

        new_state, notes = self._adapter.reconcile(operation_id)
        record.state = new_state
        record.reconciliation_notes = notes
        record.updated_at_utc = datetime.now(timezone.utc).isoformat()
        if new_state == L4OperationState.SUCCEEDED:
            record.completed_at_utc = record.updated_at_utc

        self._ledger.update_operation(record)
        return record.state, record, notes

    def get_operation_status(
        self,
        principal: UserPrincipal,
        operation_id: str,
    ) -> Tuple[Optional[L4OperationRecord], Optional[str]]:
        """Retry-safe query of operation status."""
        record = self._ledger.get_operation(operation_id)
        if not record:
            return None, "Operation not found"

        if record.actor_id != principal.user_id or record.tenant_id != principal.company:
            return None, "Unauthorized access to operation record"

        return record, None

    def cancel_pending_proposal(
        self,
        principal: UserPrincipal,
        session_id: str,
        proposal_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """Cancel an unconfirmed proposal before expiration."""
        proposal = self._ledger.get_proposal(proposal_id)
        if not proposal:
            return False, "Proposal not found"

        if proposal.actor_id != principal.user_id or proposal.session_id != session_id:
            return False, "Unauthorized to cancel proposal"

        existing = self._ledger.get_operation_by_proposal(proposal_id)
        if existing and existing.state not in (L4OperationState.PROPOSED, L4OperationState.AWAITING_CONFIRMATION):
            return False, f"Cannot cancel proposal in state: {existing.state}"

        # Record cancellation
        now_iso = datetime.now(timezone.utc).isoformat()
        cancelled_op = L4OperationRecord(
            operation_id=f"op_cancel_{proposal_id[:16]}",
            proposal_id=proposal_id,
            action_id=proposal.action_id,
            target_entity=proposal.target_entity,
            actor_id=principal.user_id,
            tenant_id=principal.company,
            site_id=proposal.site_id,
            session_id=session_id,
            state=L4OperationState.REJECTED,
            canonical_args_digest=proposal.canonical_args_digest,
            challenge_used=True,
            created_at_utc=now_iso,
            updated_at_utc=now_iso,
            error_code="USER_CANCELLED",
            error_message="Proposal explicitly rejected or cancelled by user",
        )
        self._ledger.update_operation(cancelled_op)
        if hasattr(self._ledger, "_proposal_to_operation"):
            with getattr(self._ledger, "_lock", threading.Lock()):
                self._ledger._proposal_to_operation[proposal_id] = cancelled_op.operation_id
        return True, None
