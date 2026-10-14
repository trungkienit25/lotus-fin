"""L4 Ports: Strict interfaces for write adapters and ledger persistence.

SSOT: LOTUS FIN P6-1 — IMPLEMENT L4 CONFIRMED MUTATION ENGINE.
ADR001: Separation of concerns, test adapters, fail-closed production ports.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from lotus_fin.domain.model.l4_operation_record import L4ActionProposal, L4OperationRecord
from lotus_fin.domain.schema.l4_action_catalog import L4OperationState


class ILotusActionWritePort(ABC):
    """Narrow write port for allowlisted Lotus-native target entities."""

    @abstractmethod
    def prepare_check(self, proposal: L4ActionProposal) -> Tuple[bool, Optional[str]]:
        """Check target readiness and preconditions prior to execution."""
        pass

    @abstractmethod
    def execute_operation(self, proposal: L4ActionProposal, operation_id: str) -> Dict[str, Any]:
        """Execute the exact allowlisted mutation. Must raise on failure."""
        pass

    @abstractmethod
    def inspect_outcome(self, operation_id: str) -> Tuple[L4OperationState, Optional[Dict[str, Any]]]:
        """Inspect target or external store to check if mutation took effect."""
        pass

    @abstractmethod
    def reconcile(self, operation_id: str) -> Tuple[L4OperationState, Optional[str]]:
        """Attempt safe automated reconciliation when outcome is ambiguous."""
        pass

    @abstractmethod
    def verify_target(self, target_entity: str, record_id: str) -> bool:
        """Verify resulting record existence and schema conformances."""
        pass


class IL4OperationLedger(ABC):
    """Durable ledger for idempotent operation lifecycle management."""

    @abstractmethod
    def save_proposal(self, proposal: L4ActionProposal) -> None:
        """Store proposal for subsequent lookup and confirmation."""
        pass

    @abstractmethod
    def get_proposal(self, proposal_id: str) -> Optional[L4ActionProposal]:
        """Retrieve proposal by ID."""
        pass

    @abstractmethod
    def reserve_confirmation(
        self,
        proposal: L4ActionProposal,
        challenge: str,
        session_id: str,
    ) -> Tuple[bool, Optional[L4OperationRecord], Optional[str]]:
        """Atomically reserve challenge and initialize operation in CONFIRMED / EXECUTING state.
        
        Guarantees single-use challenge consumption and concurrency lock.
        """
        pass

    @abstractmethod
    def update_operation(self, record: L4OperationRecord) -> None:
        """Update operation record with transition outcome."""
        pass

    @abstractmethod
    def get_operation(self, operation_id: str) -> Optional[L4OperationRecord]:
        """Retrieve operation record by ID."""
        pass

    @abstractmethod
    def get_operation_by_proposal(self, proposal_id: str) -> Optional[L4OperationRecord]:
        """Retrieve operation record by proposal ID for idempotency query."""
        pass
