# ADR 001: Clean Architecture Standards, <200 Lines/File Limit & Strict Ban on Ad-hoc Scripts

- **Status:** Accepted
- **Applies to:** Lotus Fin Codebase & Services

---

## 1. Context
In FinTech and accounting systems, unstructured development often introduces scattered ad-hoc scripts (manual database patches, hardcoded recalculations, one-off report extractors). This causes:
- Severe business logic fragmentation.
- Lack of automated regression tests, risking recurring ledger discrepancies.
- Codebase bloat that complicates context windows for both human engineers and AI coding agents.

---

## 2. Decision

### 2.1. Core-First Implementation (No Ad-hoc Scripts)
- **Strictly Prohibited:** Ad-hoc operational scripts or unstructured utility folders outside approved architectural boundaries.
- **Clean Architecture Boundary Allocation:**
  1. `Domain Layer`: Defines pure entities, validation invariants, value objects, and constants.
  2. `Application / UseCase Layer`: Coordinates workflows, ReAct loops, transactions, and mutex locking.
  3. `Infrastructure / Delivery Layer`: Concrete database gateways, LLM provider adapters, and RESTful controllers.

### 2.2. Strict File Size Limit: < 200 Lines per File
- All production source files must remain under **200 lines per file**.
- When a file approaches 200 lines, it must be decomposed:
  - Split UseCases into: Coordinators + Evaluators + Query Handlers.
  - Split Controllers into: REST Endpoints + DTO Parsers + Serialization Adapters.

### 2.3. Mandatory Verification Criteria
Every financial use case must include:
- **Unit Tests:** Hermetic tests validating core formulas and edge cases without database dependencies.
- **Integration Tests:** Verifying request/response envelopes and database state consistency.
