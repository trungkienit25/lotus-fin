"""L4 Adapters: In-memory/Isolated test adapter, Production fail-closed adapter, and In-memory Ledger.

SSOT: LOTUS FIN P6-1 — IMPLEMENT L4 CONFIRMED MUTATION ENGINE.
ADR001: Clean Architecture, isolated DEMO target, fail-closed production adapter, atomic ledger locks.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, Optional, Tuple
from lotus_fin.application.port.i_l4_mutation_port import (
    IL4OperationLedger,
    ILotusActionWritePort,
)
from lotus_fin.domain.model.l4_operation_record import (
    L4ActionProposal,
    L4OperationRecord,
)
from lotus_fin.domain.schema.l4_action_catalog import L4OperationState


class ProductionLotusActionWritePort(ILotusActionWritePort):
    """Production write adapter: strictly disabled / fail-closed until schema and authority approved."""

    def prepare_check(self, proposal: L4ActionProposal) -> Tuple[bool, Optional[str]]:
        # Fail closed: N0 business write blocked
        return False, "Production Lotus write port is disabled. Target schema and authority unapproved."

    def execute_operation(self, proposal: L4ActionProposal, operation_id: str) -> Dict[str, Any]:
        raise PermissionError("Production mutation blocked: N0 authority unapproved.")

    def inspect_outcome(self, operation_id: str) -> Tuple[L4OperationState, Optional[Dict[str, Any]]]:
        return L4OperationState.FAILED, None

    def reconcile(self, operation_id: str) -> Tuple[L4OperationState, Optional[str]]:
        return L4OperationState.FAILED, "Production port disabled; cannot reconcile."

    def verify_target(self, target_entity: str, record_id: str) -> bool:
        return False


class IsolatedTestLotusActionWritePort(ILotusActionWritePort):
    """Deterministic isolated TEST/DEMO target adapter. Visible synthetic mutations."""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._simulate_timeout_once: bool = False
        self._simulate_precheck_failure: bool = False
        self._lock = threading.Lock()

    def set_simulate_timeout(self, enable: bool) -> None:
        self._simulate_timeout_once = enable

    def set_simulate_precheck_failure(self, enable: bool) -> None:
        self._simulate_precheck_failure = enable

    def prepare_check(self, proposal: L4ActionProposal) -> Tuple[bool, Optional[str]]:
        if self._simulate_precheck_failure:
            return False, "Target precheck simulated failure: entity lock conflict"
        return True, None

    def execute_operation(self, proposal: L4ActionProposal, operation_id: str) -> Dict[str, Any]:
        with self._lock:
            if self._simulate_timeout_once:
                self._simulate_timeout_once = False
                # Still store the record to simulate commit that timed out on wire
                target_key = f"{proposal.target_entity.value}_{operation_id}"
                self._store[target_key] = {
                    "id": target_key,
                    "operation_id": operation_id,
                    "target_entity": proposal.target_entity.value,
                    "arguments": proposal.arguments,
                    "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    "is_synthetic": True,
                }
                raise TimeoutError("Network timeout while awaiting backend commit ack")

            target_key = f"{proposal.target_entity.value}_{operation_id}"
            record_data = {
                "id": target_key,
                "operation_id": operation_id,
                "target_entity": proposal.target_entity.value,
                "arguments": proposal.arguments,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "is_synthetic": True,
            }
            self._store[target_key] = record_data
            return {
                "created_record_id": target_key,
                "target_entity": proposal.target_entity.value,
                "is_synthetic_demo": True,
                "audit_logged": True,
            }

    def inspect_outcome(self, operation_id: str) -> Tuple[L4OperationState, Optional[Dict[str, Any]]]:
        with self._lock:
            for k, rec in self._store.items():
                if rec.get("operation_id") == operation_id:
                    return L4OperationState.SUCCEEDED, rec
            return L4OperationState.FAILED, None

    def reconcile(self, operation_id: str) -> Tuple[L4OperationState, Optional[str]]:
        state, rec = self.inspect_outcome(operation_id)
        if state == L4OperationState.SUCCEEDED:
            return L4OperationState.SUCCEEDED, f"Reconciled: Found synthetic record {rec.get('id') if rec else ''}"
        return L4OperationState.FAILED, "Reconciled: Target record not found; marked FAILED."

    def verify_target(self, target_entity: str, record_id: str) -> bool:
        with self._lock:
            return record_id in self._store


class InMemoryL4OperationLedger(IL4OperationLedger):
    """Thread-safe in-memory ledger for tests and isolated environments."""

    def __init__(self) -> None:
        self._proposals: Dict[str, L4ActionProposal] = {}
        self._operations: Dict[str, L4OperationRecord] = {}
        self._proposal_to_operation: Dict[str, str] = {}
        self._consumed_challenges: set[str] = set()
        self._lock = threading.Lock()

    def save_proposal(self, proposal: L4ActionProposal) -> None:
        with self._lock:
            self._proposals[proposal.proposal_id] = proposal

    def get_proposal(self, proposal_id: str) -> Optional[L4ActionProposal]:
        with self._lock:
            return self._proposals.get(proposal_id)

    def reserve_confirmation(
        self,
        proposal: L4ActionProposal,
        challenge: str,
        session_id: str,
    ) -> Tuple[bool, Optional[L4OperationRecord], Optional[str]]:
        with self._lock:
            # 1. Challenge match
            if proposal.confirmation_challenge != challenge:
                return False, None, "Challenge token mismatch"

            # 2. Challenge single-use
            if challenge in self._consumed_challenges:
                return False, None, "Challenge already consumed"

            # 3. Check if proposal already reserved
            if proposal.proposal_id in self._proposal_to_operation:
                return False, None, "Proposal already reserved"

            # Consume challenge atomically
            self._consumed_challenges.add(challenge)

            now_iso = datetime.now(timezone.utc).isoformat()
            operation_id = f"op_{proposal.proposal_id[5:]}"
            op_record = L4OperationRecord(
                operation_id=operation_id,
                proposal_id=proposal.proposal_id,
                action_id=proposal.action_id,
                target_entity=proposal.target_entity,
                actor_id=proposal.actor_id,
                tenant_id=proposal.tenant_id,
                site_id=proposal.site_id,
                session_id=session_id,
                state=L4OperationState.CONFIRMED,
                canonical_args_digest=proposal.canonical_args_digest,
                challenge_used=True,
                created_at_utc=now_iso,
                updated_at_utc=now_iso,
                confirmed_at_utc=now_iso,
                is_synthetic_demo=proposal.simulated,
            )

            self._operations[operation_id] = op_record
            self._proposal_to_operation[proposal.proposal_id] = operation_id
            return True, op_record, None

    def update_operation(self, record: L4OperationRecord) -> None:
        with self._lock:
            self._operations[record.operation_id] = record

    def get_operation(self, operation_id: str) -> Optional[L4OperationRecord]:
        with self._lock:
            return self._operations.get(operation_id)

    def get_operation_by_proposal(self, proposal_id: str) -> Optional[L4OperationRecord]:
        with self._lock:
            op_id = self._proposal_to_operation.get(proposal_id)
            if op_id:
                return self._operations.get(op_id)
            return None
