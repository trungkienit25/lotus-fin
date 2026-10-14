"""Deterministic Isolated Simulation Adapters for L5 Action Families."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict

from lotus_fin.domain.l5.models.contracts import (
    L5ActionFamily,
    L5AdapterCapabilityState,
    L5ProposalState,
)
from lotus_fin.domain.l5.models.proposals import L5Proposal


class L5ExecutionReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    success: bool
    status_code: str
    target_id: Optional[str] = None
    terminal_state: L5ProposalState
    error_message: Optional[str] = None
    simulated_receipt_data: Dict[str, Any] = {}


class IL5ActionAdapter(ABC):
    @property
    @abstractmethod
    def family(self) -> L5ActionFamily:
        pass

    @property
    @abstractmethod
    def capability_state(self) -> L5AdapterCapabilityState:
        pass

    @abstractmethod
    def execute(self, proposal: L5Proposal, simulation_fault: Optional[str] = None) -> L5ExecutionReceipt:
        pass


class ProductionBlockedAdapter(IL5ActionAdapter):
    """Guarantees real irreversible adapters remain fail-closed CAPABILITY_DISABLED."""

    def __init__(self, action_family: L5ActionFamily):
        self._family = action_family

    @property
    def family(self) -> L5ActionFamily:
        return self._family

    @property
    def capability_state(self) -> L5AdapterCapabilityState:
        return L5AdapterCapabilityState.CAPABILITY_DISABLED

    def execute(self, proposal: L5Proposal, simulation_fault: Optional[str] = None) -> L5ExecutionReceipt:
        return L5ExecutionReceipt(
            success=False,
            status_code="CAPABILITY_DISABLED",
            terminal_state=L5ProposalState.REJECTED,
            error_message=f"Live execution for family {self._family.value} is blocked and disabled in this release.",
        )


class BaseSimulatedL5Adapter(IL5ActionAdapter):
    """Deterministic in-memory simulation adapter for test qualification."""

    def __init__(self, action_family: L5ActionFamily):
        self._family = action_family

    @property
    def family(self) -> L5ActionFamily:
        return self._family

    @property
    def capability_state(self) -> L5AdapterCapabilityState:
        return L5AdapterCapabilityState.SIMULATION_QUALIFIED

    def execute(self, proposal: L5Proposal, simulation_fault: Optional[str] = None) -> L5ExecutionReceipt:
        # Check simulation faults for testing resilience and safety
        if simulation_fault == "CRASH_AFTER_POSSIBLE_COMMIT":
            return L5ExecutionReceipt(
                success=False,
                status_code="AMBIGUOUS_CRASH",
                terminal_state=L5ProposalState.UNKNOWN_OUTCOME,
                error_message="Simulated process crash after remote dispatch; outcome uncertain.",
            )
        if simulation_fault == "REMOTE_TIMEOUT":
            return L5ExecutionReceipt(
                success=False,
                status_code="DEADLINE_EXCEEDED",
                terminal_state=L5ProposalState.UNKNOWN_OUTCOME,
                error_message="Simulated remote gateway timeout.",
            )
        if simulation_fault == "TARGET_LOCK_FAILURE":
            return L5ExecutionReceipt(
                success=False,
                status_code="LOCK_ACQUISITION_FAILED",
                terminal_state=L5ProposalState.FAILED_ROLLED_BACK,
                error_message="Document lock acquisition failed on remote resource.",
            )
        if simulation_fault == "DOWNSTREAM_REJECTION":
            return L5ExecutionReceipt(
                success=False,
                status_code="REMOTE_REJECTED",
                terminal_state=L5ProposalState.FAILED_ROLLED_BACK,
                error_message="Target resource rejected state transition.",
            )

        # Normal successful simulation execution
        return self._simulate_success(proposal)

    @abstractmethod
    def _simulate_success(self, proposal: L5Proposal) -> L5ExecutionReceipt:
        pass


class SimulatedDocumentSubmitAdapter(BaseSimulatedL5Adapter):
    def __init__(self):
        super().__init__(L5ActionFamily.DOCUMENT_SUBMIT)

    def _simulate_success(self, proposal: L5Proposal) -> L5ExecutionReceipt:
        return L5ExecutionReceipt(
            success=True,
            status_code="DOCUMENT_SUBMITTED",
            target_id=proposal.target.doc_id,
            terminal_state=L5ProposalState.COMMITTED,
            simulated_receipt_data={
                "doctype": proposal.target.doctype,
                "doc_id": proposal.target.doc_id,
                "new_docstatus": 1,
                "submitted_at_epoch": 1776100000.0,
            },
        )


class SimulatedDocumentCancelAdapter(BaseSimulatedL5Adapter):
    def __init__(self):
        super().__init__(L5ActionFamily.DOCUMENT_CANCEL)

    def _simulate_success(self, proposal: L5Proposal) -> L5ExecutionReceipt:
        return L5ExecutionReceipt(
            success=True,
            status_code="DOCUMENT_CANCELLED",
            target_id=proposal.target.doc_id,
            terminal_state=L5ProposalState.COMMITTED,
            simulated_receipt_data={
                "doctype": proposal.target.doctype,
                "doc_id": proposal.target.doc_id,
                "new_docstatus": 2,
                "cancelled_at_epoch": 1776100000.0,
            },
        )


class SimulatedExternalEmailSendAdapter(BaseSimulatedL5Adapter):
    def __init__(self):
        super().__init__(L5ActionFamily.EXTERNAL_EMAIL_SEND)

    def _simulate_success(self, proposal: L5Proposal) -> L5ExecutionReceipt:
        recipient = proposal.parameters.get("recipient_email", "")
        return L5ExecutionReceipt(
            success=True,
            status_code="EMAIL_DISPATCHED",
            target_id=f"msg-{proposal.proposal_id[:8]}",
            terminal_state=L5ProposalState.COMMITTED,
            simulated_receipt_data={
                "recipient_email": recipient,
                "message_id": f"msg-sim-{proposal.proposal_id[:8]}",
                "simulated_delivery_verified": True,
            },
        )


class SimulatedPaymentRequestAdapter(BaseSimulatedL5Adapter):
    def __init__(self):
        super().__init__(L5ActionFamily.PAYMENT_REQUEST)

    def _simulate_success(self, proposal: L5Proposal) -> L5ExecutionReceipt:
        amount = proposal.parameters.get("amount", 0.0)
        currency = proposal.parameters.get("currency", "VND")
        return L5ExecutionReceipt(
            success=True,
            status_code="PAYMENT_REQUEST_GENERATED",
            target_id=f"PR-{proposal.proposal_id[:8]}",
            terminal_state=L5ProposalState.COMMITTED,
            simulated_receipt_data={
                "payment_request_id": f"PR-{proposal.proposal_id[:8]}",
                "amount": amount,
                "currency": currency,
                "is_actual_payment": False,  # Explicit invariant distinction
                "notice": "Payment Request record created; no funds transferred.",
            },
        )
