"""L5 Workflow Engine - Prepare -> Approve -> Execute with Reconciliation."""

import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional

from lotus_fin.domain.l5.adapters.simulation import (
    IL5ActionAdapter,
    L5ExecutionReceipt,
    ProductionBlockedAdapter,
    SimulatedDocumentCancelAdapter,
    SimulatedDocumentSubmitAdapter,
    SimulatedExternalEmailSendAdapter,
    SimulatedPaymentRequestAdapter,
)
from lotus_fin.domain.l5.models.contracts import (
    L5ActionFamily,
    L5AdapterCapabilityState,
    L5ApprovalLevel,
    L5PolicyDecision,
    L5ProposalState,
    L5RiskLevel,
)
from lotus_fin.domain.l5.models.proposals import (
    L5AuditRecord,
    L5LedgerEntry,
    L5Proposal,
    L5TargetSpec,
    compute_canonical_hash,
)
from lotus_fin.domain.l5.policy.engine import (
    L5PolicyContext,
    L5PolicyEngine,
)


class L5WorkflowService:
    """End-to-End Orchestrator for L5 Actions."""

    def __init__(self, policy_engine: Optional[L5PolicyEngine] = None, use_simulation: bool = True):
        self.policy_engine = policy_engine or L5PolicyEngine()
        self.use_simulation = use_simulation

        # In-memory stores (in real Frappe deployment, backed by DB table with unique locks)
        self.proposals: Dict[str, L5Proposal] = {}
        self.ledger: Dict[str, L5LedgerEntry] = {}
        self.audit_log: List[L5AuditRecord] = []

        # Qualified adapters map
        self.adapters: Dict[L5ActionFamily, IL5ActionAdapter] = {}
        if self.use_simulation:
            self.adapters[L5ActionFamily.DOCUMENT_SUBMIT] = SimulatedDocumentSubmitAdapter()
            self.adapters[L5ActionFamily.DOCUMENT_CANCEL] = SimulatedDocumentCancelAdapter()
            self.adapters[L5ActionFamily.EXTERNAL_EMAIL_SEND] = SimulatedExternalEmailSendAdapter()
            self.adapters[L5ActionFamily.PAYMENT_REQUEST] = SimulatedPaymentRequestAdapter()
            # These two families are permanently blocked in MVP even in simulation test
            self.adapters[L5ActionFamily.PAYMENT_EXECUTION] = ProductionBlockedAdapter(L5ActionFamily.PAYMENT_EXECUTION)
            self.adapters[L5ActionFamily.SCHEDULED_AUTONOMOUS_ACTION] = ProductionBlockedAdapter(
                L5ActionFamily.SCHEDULED_AUTONOMOUS_ACTION
            )
        else:
            # All production adapters are blocked until individually qualified
            for fam in L5ActionFamily:
                self.adapters[fam] = ProductionBlockedAdapter(fam)

    def _record_audit(
        self,
        actor: str,
        session_id: str,
        site: str,
        company: str,
        family: L5ActionFamily,
        action_name: str,
        proposal_id: str,
        event_type: str,
        risk_level: L5RiskLevel,
        outcome_state: L5ProposalState,
        operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        rec = L5AuditRecord(
            audit_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4())[:8],
            timestamp_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            actor=actor,
            session_id=session_id,
            site=site,
            company=company,
            family=family,
            action_name=action_name,
            proposal_id=proposal_id,
            operation_id=operation_id,
            event_type=event_type,
            risk_level=risk_level,
            outcome_state=outcome_state,
            details=details or {},
        )
        self.audit_log.append(rec)

    # -------------------------------------------------------------
    # 1. PREPARE
    # -------------------------------------------------------------
    def prepare_proposal(
        self,
        action_name: str,
        actor: str,
        actor_roles: List[str],
        session_id: str,
        site: str,
        tenant_id: str,
        authorized_company: str,
        target: L5TargetSpec,
        parameters: Dict[str, Any],
        current_resource_version: str,
        current_docstatus: int,
        ttl_seconds: float = 120.0,
    ) -> Dict[str, Any]:
        """Validate intent against policy, create immutable proposal, generate review challenge."""
        ctx = L5PolicyContext(
            actor=actor,
            actor_roles=actor_roles,
            tenant_id=tenant_id,
            site=site,
            authorized_company=authorized_company,
            target=target,
            parameters=parameters,
            current_resource_version=current_resource_version,
            current_docstatus=current_docstatus,
        )

        eval_result = self.policy_engine.evaluate_intent(action_name, ctx)
        if eval_result.decision != L5PolicyDecision.PERMITTED:
            return {
                "status": "DENIED",
                "reason_code": eval_result.reason_code,
                "risk_level": eval_result.risk_level.value,
                "details": eval_result.details,
            }

        action_def = self.policy_engine.catalog[action_name]
        now = time.time()
        proposal_id = f"prop-{uuid.uuid4().hex[:16]}"
        raw_challenge = f"chal-{uuid.uuid4().hex}"
        challenge_hash = hashlib.sha256(raw_challenge.encode("utf-8")).hexdigest()

        canonical_data = {
            "proposal_id": proposal_id,
            "action_name": action_name,
            "family": action_def.family.value,
            "actor": actor,
            "session_id": session_id,
            "site": site,
            "company": authorized_company,
            "target": target.model_dump(),
            "parameters": parameters,
            "risk_level": eval_result.risk_level.value,
        }
        canonical_hash = compute_canonical_hash(canonical_data)

        proposal = L5Proposal(
            proposal_id=proposal_id,
            family=action_def.family,
            action_name=action_name,
            actor=actor,
            session_id=session_id,
            site=site,
            company=authorized_company,
            target=target,
            parameters=parameters,
            risk_level=eval_result.risk_level,
            required_approval_level=eval_result.required_approval_level,
            consequence_description=action_def.description,
            is_reversible=action_def.is_reversible,
            state=L5ProposalState.APPROVAL_PENDING,
            canonical_hash=canonical_hash,
            review_challenge_hash=challenge_hash,
            created_at_epoch=now,
            expires_at_epoch=now + ttl_seconds,
        )

        self.proposals[proposal_id] = proposal
        self._record_audit(
            actor=actor,
            session_id=session_id,
            site=site,
            company=authorized_company,
            family=action_def.family,
            action_name=action_name,
            proposal_id=proposal_id,
            event_type="PROPOSAL_CREATED",
            risk_level=eval_result.risk_level,
            outcome_state=L5ProposalState.APPROVAL_PENDING,
            details={"parameters": parameters, "target": target.model_dump()},
        )

        return {
            "status": "PROPOSAL_READY",
            "proposal_id": proposal_id,
            "action_name": action_name,
            "family": action_def.family.value,
            "risk_level": eval_result.risk_level.value,
            "required_approval_level": eval_result.required_approval_level.value,
            "consequence_description": action_def.description,
            "is_reversible": action_def.is_reversible,
            "review_challenge": raw_challenge,  # Given to client for one-use confirmation binding
            "target": target.model_dump(),
            "expires_in_seconds": ttl_seconds,
        }

    # -------------------------------------------------------------
    # 2. APPROVE
    # -------------------------------------------------------------
    def submit_ui_approval(
        self,
        proposal_id: str,
        actor: str,
        session_id: str,
        review_challenge: str,
        additional_approvals: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Validates user confirmation and additional required gates (e.g. Dual Control / Finance Officer)."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"status": "DENIED", "reason_code": "PROPOSAL_NOT_FOUND"}

        now = time.time()
        if now >= proposal.expires_at_epoch:
            proposal.state = L5ProposalState.EXPIRED
            return {"status": "DENIED", "reason_code": "PROPOSAL_EXPIRED"}

        if proposal.state != L5ProposalState.APPROVAL_PENDING:
            return {"status": "DENIED", "reason_code": "INVALID_PROPOSAL_STATE", "current_state": proposal.state.value}

        # Validate actor and session binding
        if proposal.actor != actor or proposal.session_id != session_id:
            return {"status": "DENIED", "reason_code": "ACTOR_SESSION_MISMATCH"}

        # Validate review challenge
        challenge_hash = hashlib.sha256(review_challenge.encode("utf-8")).hexdigest()
        if challenge_hash != proposal.review_challenge_hash:
            return {"status": "DENIED", "reason_code": "INVALID_REVIEW_CHALLENGE"}

        # Check approval level gates
        if proposal.required_approval_level == L5ApprovalLevel.DUAL_CONTROL_M_OF_N:
            approvals = additional_approvals or []
            # Must have at least one additional independent approver
            independent = [a for a in approvals if a.get("approver") != actor and a.get("role") in ["Accounts Manager", "Director"]]
            if not independent:
                return {
                    "status": "APPROVAL_GATE_PENDING",
                    "reason_code": "DUAL_CONTROL_REQUIRED",
                    "message": "Action requires independent 2nd approver confirmation.",
                }
            proposal.additional_approvals = independent

        elif proposal.required_approval_level == L5ApprovalLevel.FINANCE_OFFICER_GATE:
            approvals = additional_approvals or []
            officer = [a for a in approvals if a.get("role") in ["Finance Officer", "Accounts Manager", "Treasurer"]]
            # If the current actor already possesses this role, it can satisfy single user gate if allowed, otherwise gate check
            if not officer:
                return {
                    "status": "APPROVAL_GATE_PENDING",
                    "reason_code": "FINANCE_OFFICER_SIGN_OFF_REQUIRED",
                    "message": "Action requires Finance Officer sign-off.",
                }
            proposal.additional_approvals = officer

        proposal.state = L5ProposalState.APPROVED
        self._record_audit(
            actor=actor,
            session_id=session_id,
            site=proposal.site,
            company=proposal.company,
            family=proposal.family,
            action_name=proposal.action_name,
            proposal_id=proposal_id,
            event_type="PROPOSAL_APPROVED",
            risk_level=proposal.risk_level,
            outcome_state=L5ProposalState.APPROVED,
        )

        return {"status": "APPROVED", "proposal_id": proposal_id}

    # -------------------------------------------------------------
    # 3. EXECUTE
    # -------------------------------------------------------------
    def execute_proposal(
        self,
        proposal_id: str,
        actor: str,
        actor_roles: List[str],
        session_id: str,
        idempotency_key: str,
        current_resource_version: str,
        current_docstatus: int,
        simulation_fault: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Atomically reserves ledger, re-authorizes, checks idempotency, and executes adapter."""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return {"status": "DENIED", "reason_code": "PROPOSAL_NOT_FOUND"}

        now = time.time()
        if now >= proposal.expires_at_epoch:
            proposal.state = L5ProposalState.EXPIRED
            return {"status": "DENIED", "reason_code": "PROPOSAL_EXPIRED"}

        # Idempotency check: Has this operation already been reserved or committed?
        existing_op = None
        for op in self.ledger.values():
            if op.idempotency_key == idempotency_key or op.proposal_id == proposal_id:
                existing_op = op
                break

        if existing_op:
            if existing_op.state == L5ProposalState.COMMITTED:
                return {
                    "status": "ALREADY_COMMITTED",
                    "operation_id": existing_op.operation_id,
                    "receipt": existing_op.terminal_receipt,
                    "target_identity": existing_op.target_identity,
                }
            if existing_op.state == L5ProposalState.EXECUTING:
                return {
                    "status": "IN_PROGRESS",
                    "operation_id": existing_op.operation_id,
                    "message": "Operation is currently executing.",
                }
            if existing_op.state == L5ProposalState.UNKNOWN_OUTCOME:
                return {
                    "status": "UNKNOWN_OUTCOME",
                    "operation_id": existing_op.operation_id,
                    "message": "Previous attempt resulted in UNKNOWN_OUTCOME. Reconciliation required.",
                }
            # For replay with changed params or wrong proposal state
            if existing_op.proposal_id != proposal_id:
                return {"status": "DENIED", "reason_code": "IDEMPOTENCY_KEY_REPLAY_CONFLICT"}

        if proposal.state != L5ProposalState.APPROVED:
            return {"status": "DENIED", "reason_code": "PROPOSAL_NOT_APPROVED", "current_state": proposal.state.value}

        # Step 8 Re-authorize policy and target freshness before write
        ctx = L5PolicyContext(
            actor=actor,
            actor_roles=actor_roles,
            tenant_id="tenant-1",
            site=proposal.site,
            authorized_company=proposal.company,
            target=proposal.target,
            parameters=proposal.parameters,
            current_resource_version=current_resource_version,
            current_docstatus=current_docstatus,
        )
        eval_result = self.policy_engine.evaluate_intent(proposal.action_name, ctx)
        if eval_result.decision != L5PolicyDecision.PERMITTED:
            proposal.state = L5ProposalState.REVOKED
            return {
                "status": "DENIED",
                "reason_code": "REAUTHORIZATION_FAILED",
                "sub_code": eval_result.reason_code,
                "details": eval_result.details,
            }

        # Step 9: Reserve durable operation identity in ledger
        operation_id = f"op-{uuid.uuid4().hex[:16]}"
        ledger_entry = L5LedgerEntry(
            operation_id=operation_id,
            proposal_id=proposal_id,
            family=proposal.family,
            action_name=proposal.action_name,
            site=proposal.site,
            company=proposal.company,
            actor=actor,
            session_id=session_id,
            idempotency_key=idempotency_key,
            state=L5ProposalState.EXECUTING,
            attempt_count=1,
            fencing_lease_expires_at=now + 30.0,
            created_at_epoch=now,
            updated_at_epoch=now,
        )
        self.ledger[operation_id] = ledger_entry
        proposal.state = L5ProposalState.EXECUTING

        self._record_audit(
            actor=actor,
            session_id=session_id,
            site=proposal.site,
            company=proposal.company,
            family=proposal.family,
            action_name=proposal.action_name,
            proposal_id=proposal_id,
            operation_id=operation_id,
            event_type="OPERATION_RESERVED",
            risk_level=proposal.risk_level,
            outcome_state=L5ProposalState.EXECUTING,
        )

        # Step 10: Execute narrow adapter
        adapter = self.adapters.get(proposal.family)
        if not adapter:
            ledger_entry.state = L5ProposalState.FAILED_ROLLED_BACK
            ledger_entry.failure_reason = "ADAPTER_NOT_FOUND"
            proposal.state = L5ProposalState.FAILED_ROLLED_BACK
            return {"status": "FAILED", "reason_code": "ADAPTER_NOT_FOUND"}

        receipt: L5ExecutionReceipt = adapter.execute(proposal, simulation_fault=simulation_fault)

        # Step 11: Update ledger & outcome
        now_post = time.time()
        ledger_entry.updated_at_epoch = now_post

        if receipt.terminal_state == L5ProposalState.COMMITTED:
            ledger_entry.state = L5ProposalState.COMMITTED
            ledger_entry.target_identity = receipt.target_id
            ledger_entry.terminal_receipt = receipt.simulated_receipt_data
            proposal.state = L5ProposalState.COMMITTED
            proposal.consumed_at_epoch = now_post

            self._record_audit(
                actor=actor,
                session_id=session_id,
                site=proposal.site,
                company=proposal.company,
                family=proposal.family,
                action_name=proposal.action_name,
                proposal_id=proposal_id,
                operation_id=operation_id,
                event_type="OPERATION_COMMITTED",
                risk_level=proposal.risk_level,
                outcome_state=L5ProposalState.COMMITTED,
                details={"target_id": receipt.target_id, "receipt": receipt.simulated_receipt_data},
            )

            return {
                "status": "COMMITTED",
                "operation_id": operation_id,
                "target_identity": receipt.target_id,
                "receipt": receipt.simulated_receipt_data,
            }

        elif receipt.terminal_state == L5ProposalState.UNKNOWN_OUTCOME:
            ledger_entry.state = L5ProposalState.UNKNOWN_OUTCOME
            ledger_entry.failure_reason = receipt.error_message
            proposal.state = L5ProposalState.UNKNOWN_OUTCOME

            self._record_audit(
                actor=actor,
                session_id=session_id,
                site=proposal.site,
                company=proposal.company,
                family=proposal.family,
                action_name=proposal.action_name,
                proposal_id=proposal_id,
                operation_id=operation_id,
                event_type="OPERATION_UNKNOWN_OUTCOME",
                risk_level=proposal.risk_level,
                outcome_state=L5ProposalState.UNKNOWN_OUTCOME,
                details={"error": receipt.error_message},
            )

            return {
                "status": "UNKNOWN_OUTCOME",
                "operation_id": operation_id,
                "reason_code": receipt.status_code,
                "message": receipt.error_message,
                "reconciliation_required": True,
            }

        else:
            ledger_entry.state = L5ProposalState.FAILED_ROLLED_BACK
            ledger_entry.failure_reason = receipt.error_message
            proposal.state = L5ProposalState.FAILED_ROLLED_BACK

            self._record_audit(
                actor=actor,
                session_id=session_id,
                site=proposal.site,
                company=proposal.company,
                family=proposal.family,
                action_name=proposal.action_name,
                proposal_id=proposal_id,
                operation_id=operation_id,
                event_type="OPERATION_FAILED",
                risk_level=proposal.risk_level,
                outcome_state=L5ProposalState.FAILED_ROLLED_BACK,
                details={"error": receipt.error_message},
            )

            return {
                "status": "FAILED",
                "operation_id": operation_id,
                "reason_code": receipt.status_code,
                "message": receipt.error_message,
            }

    # -------------------------------------------------------------
    # 4. RECONCILE UNKNOWN_OUTCOME
    # -------------------------------------------------------------
    def reconcile_operation(
        self,
        operation_id: str,
        actor: str,
        session_id: str,
        verified_external_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Safe non-blind status reconciliation for ambiguous outcomes."""
        op = self.ledger.get(operation_id)
        if not op:
            return {"status": "DENIED", "reason_code": "OPERATION_NOT_FOUND"}

        # Scoping check
        if op.actor != actor or op.session_id != session_id:
            return {"status": "DENIED", "reason_code": "ACTOR_SESSION_MISMATCH"}

        if op.state != L5ProposalState.UNKNOWN_OUTCOME:
            return {
                "status": "ALREADY_RESOLVED",
                "current_state": op.state.value,
                "receipt": op.terminal_receipt,
            }

        now = time.time()
        op.updated_at_epoch = now

        if verified_external_status == "VERIFIED_COMMITTED":
            op.state = L5ProposalState.RECONCILED
            op.terminal_receipt = {"reconciliation_resolution": "COMMITTED_CONFIRMED"}
            self._record_audit(
                actor=actor,
                session_id=session_id,
                site=op.site,
                company=op.company,
                family=op.family,
                action_name=op.action_name,
                proposal_id=op.proposal_id,
                operation_id=operation_id,
                event_type="RECONCILIATION_RESOLVED_COMMITTED",
                risk_level=L5RiskLevel.HIGH,
                outcome_state=L5ProposalState.RECONCILED,
            )
            return {"status": "RECONCILED", "resolved_state": "COMMITTED"}

        elif verified_external_status == "VERIFIED_NOT_COMMITTED":
            op.state = L5ProposalState.FAILED_ROLLED_BACK
            op.terminal_receipt = {"reconciliation_resolution": "ABORTED_NO_SIDE_EFFECTS"}
            self._record_audit(
                actor=actor,
                session_id=session_id,
                site=op.site,
                company=op.company,
                family=op.family,
                action_name=op.action_name,
                proposal_id=op.proposal_id,
                operation_id=operation_id,
                event_type="RECONCILIATION_RESOLVED_ROLLEDBACK",
                risk_level=L5RiskLevel.HIGH,
                outcome_state=L5ProposalState.FAILED_ROLLED_BACK,
            )
            return {"status": "RECONCILED", "resolved_state": "FAILED_ROLLED_BACK"}

        return {
            "status": "RECONCILIATION_PENDING",
            "message": "Independent verification required. Blind retry strictly disallowed.",
        }
