# P6 L4 TECHNICAL DOCUMENTATION: CONFIRMED MUTATION ENGINE

**Role**: Principal FinTech Backend Engineer, Distributed Systems Engineer & Application Security Engineer  
**Scope**: P6-1 L4 Confirmed Mutation Engine  
**Repository**: `E:/lotus-fin`  
**Date**: 2026-10-13  

---

## 1. System Overview & Architecture Boundary

The Lotus Fin L4 Confirmed Mutation Engine is designed according to **Clean Architecture** (ADR001) and strictly adheres to **zero ERPNext application dependencies**:
- **Allowed Infrastructure**: Pure Frappe Framework primitives (for routing, session authentication, CSRF validation, caching).
- **Forbidden**: Direct ERPNext DocTypes, ERPNext accounting tables, generic SQL/RPC execution, or Administrator fallback permissions.
- **Data Authority Protection**: N0 financial data authority remains **BLOCKED**. No direct production business-write is performed. The production write adapter is hardwired to **fail-closed** (`ProductionLotusActionWritePort`).
- **Isolation Guarantee**: All executable mutations are isolated to Lotus-owned entities (`LotusTask`, `LotusNote`, `LotusDraftRecord`) or executed against a visibly synthetic test adapter (`IsolatedTestLotusActionWritePort`).

```mermaid
flowchart TD
    User([Authenticated User in UI]) -->|1. Request Action| LLM([Intent Classifier / LLM])
    LLM -->|2. Propose with Typed Fields| Service([L4MutationService])
    Service -->|3. Validate Args & Auth| Catalog[L4 Action Catalog]
    Service -->|4. Generate Challenge & Digest| Ledger[(L4 Operation Ledger)]
    Service -->|5. Return Immutable Proposal| UIReview[L4ProposalReviewCard]
    UIReview -->|6. Explicit User Click + CSRF| Confirm[confirm_action]
    Confirm -->|7. Verify Bindings & State| Service
    Service -->|8. Atomic Challenge Reservation| Ledger
    Service -->|9. Delegate Execution| AdapterPort[ILotusActionWritePort]
    AdapterPort -->|Fail-Closed| ProdAdapter[Production Port (BLOCKED)]
    AdapterPort -->|Synthetic Demo| TestAdapter[Isolated Test Target]
    Service -->|10. Reconciliation on Timeout| ReconcileFlow[reconcile_operation]
```

---

## 2. Component Structure

1. **Domain Layer**:
   - `lotus_fin/lotus_fin/domain/schema/l4_action_catalog.py`: Defines allowlisted actions (`lotus.task.create`, `lotus.note.create`, `lotus.draft_record.prepare`), strict Pydantic schemas (`L4TaskArgs`, `L4NoteArgs`, `L4DraftRecordArgs`), and operation states (`PROPOSED`, `AWAITING_CONFIRMATION`, `CONFIRMED`, `EXECUTING`, `SUCCEEDED`, `FAILED`, `UNKNOWN_OUTCOME`, `RECONCILING`).
   - `lotus_fin/lotus_fin/domain/model/l4_operation_record.py`: Contains immutable `L4ActionProposal` with canonical SHA-256 digest computation, single-use confirmation challenge, and durable `L4OperationRecord`.
2. **Port & Application Layer**:
   - `lotus_fin/lotus_fin/application/port/i_l4_mutation_port.py`: Defines `ILotusActionWritePort` and `IL4OperationLedger`.
   - `lotus_fin/lotus_fin/application/service/l4_mutation_service.py`: Implements two-phase proposal/confirmation workflow, atomic reservation, challenge single-use enforcement, timeout classification, and idempotent replay.
3. **Infrastructure & Persistence Layer**:
   - `lotus_fin/lotus_fin/infrastructure/persistence/l4_mutation_adapters.py`:
     - `ProductionLotusActionWritePort`: Complete fail-closed production write port that raises `PermissionError` and rejects mutations.
     - `IsolatedTestLotusActionWritePort`: Thread-safe isolated test/demo adapter with explicit synthetic data tagging (`is_synthetic_demo: True`).
     - `InMemoryL4OperationLedger`: Thread-safe ledger guaranteeing atomic challenge consumption and concurrent reservation locks.
4. **Presentation Layer**:
   - `lotus_fin/lotus_fin/presentation/dto/l4_mutation_dto.py`: Strict input/output DTOs for `propose`, `confirm`, `status`, `cancel`, and `reconcile`.
   - `lotus_fin/lotus_fin/presentation/controller/l4_mutation_controller.py`: HTTP controller providing typed endpoints complying with Clean Architecture (< 200 lines).
5. **Frontend Handoff**:
   - `frontend/src/pages/copilot/actions/l4MutationContracts.ts`: TypeScript contracts for proposal review, diffs, and execution states.
   - `frontend/src/pages/copilot/actions/L4MutationPanel.tsx`: Isolated, unmounted React components (`L4ProposalReviewCard`, `L4ExecutionStatusPanel`) with visible synthetic demo badges and reconciliation triggers.
