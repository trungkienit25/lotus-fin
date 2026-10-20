# TECHNICAL DESIGN: CHAT PERSISTENCE & ENTERPRISE AUDIT LOGGING

> **Document Identifier:** `ARCH-04-PLAN`  
> **System:** Lotus Fin (2026 FinTechathon — Topic E: SME Financial AI Copilot)  
> **Version:** 2.0 (Refined with Database-backed Persistence & Chatbot Industry Standards)  
> **Status:** Detailed Engineering Blueprint  
> **Standards Alignment:** Clean/Hexagonal Architecture, SOLID, Design Patterns, OpenAI Assistant API v2, OpenTelemetry GenAI Semantic Conventions, Enterprise Multi-Tenant Isolation.  

---

## 1. Recognized Chatbot Engineering Standards

To deliver an enterprise-grade solution satisfying regulatory financial benchmarks, the conversation persistence and audit logging engine follows four industry standards:

### 1.1. OpenAI Assistant API v2 Specification (Thread – Message – Run Step Lifecycle)
* **Thread (Dialogue Session):** Encapsulates an ongoing conversation between user and AI. Represents an independent stateful boundary with unique ID, owner context (`company`, `user_id`), lifecycle status, and metadata.
* **Message (Interaction Unit):** Every exchange in a Thread is an append-only Message with a typed role (`user`, `assistant`, `system`, `tool`), ensuring cryptographic audit integrity.
* **Run Step / Tool Execution (Trace Evidence):** Each financial tool execution (F001–F007) captures invocation name, input arguments (JSON), structured result payload (JSON), execution latency (ms), and termination status.

### 1.2. OpenTelemetry GenAI Semantic Conventions (v1.27+)
* Standardization of observability telemetry:
  * `gen_ai.system`: AI platform identifier (`gemini`, `openai`, `lotus-react`).
  * `gen_ai.request.model`: Underlying model name (`gemini-flash-latest`, `gpt-4o`, `mock`).
  * `gen_ai.latency_ms`: Round-trip execution latency in milliseconds.
  * `trace_id` & `span_id`: Distributed trace identifiers linking Frontend -> Backend -> LLM -> Accounting Ledger -> Audit Trail.

### 1.3. LangChain / LangGraph Stateful Checkpointing & Memory
* **Stateful Dialogue Checkpoint:** In-database durable persistence of conversational checkpoints.
* **Buffer Window Memory:** Context window bounded to a rolling window (`max_messages = 8-10`) to optimize token expenditure and prevent context overflow, while **100% of historical records** remain preserved in the underlying database for review.

### 1.4. Enterprise Multi-Tenant Data Isolation (ISO/IEC 27001 & SOC 2)
* **Strict Tenant Boundary (`company` partition):** All database queries are indexed and filtered by tenant company. Cross-tenant session inspection is prevented at the database query abstraction layer.
* **Zero-PII Audit Trail:** Sensitive credentials and secrets are stripped prior to persistence.

---

## 2. Database Schema Architecture

Conversation data persists in the platform relational database (MariaDB) across two specialized DocTypes:

### 2.1. Lotus Chat Session (Parent Thread Header)
* `name`: Primary key (UUID string, e.g., `session-9b1deb4d-...`).
* `company`: Associated company identifier (Indexed).
* `user`: Authenticated user email (Indexed).
* `title`: Automated session title derived from the initial user query.
* `status`: Session lifecycle state (`ACTIVE`, `ARCHIVED`, `EXPIRED`).
* `created_at` / `updated_at`: Timestamps.

### 2.2. Lotus Chat Message (Child Message & Tool Execution Line)
* `session_id`: Foreign key link to parent Lotus Chat Session (Indexed).
* `role`: Message role (`user`, `assistant`, `system`, `tool`).
* `content`: Text body of message.
* `tool_name`: Associated tool command identifier (e.g., `get_cash_forecast`).
* `tool_input`: JSON representation of input arguments.
* `tool_output`: JSON representation of factual execution output.
* `ui_widget`: JSON representation of UI card or chart configuration.
* `execution_time_ms`: Execution latency in milliseconds.
* `trace_id`: Distributed tracing identifier.

---

## 3. High-Performance Multi-Tier Storage Topology

```text
  [ Presentation / User Request ]
                │
                ▼
  [ CompositeSessionRepository ]
       │                  │
       ▼ (Read Fast-path)  ▼ (Write-Through & Fallback)
  [ L1: Redis Cache ]   [ L2: MariaDB Database ]
```

* **L1 (Redis In-Memory Cache):** Delivers sub-millisecond session access for ongoing interactions.
* **L2 (MariaDB Persistence):** Guarantees ACID durability, long-term historical querying, and audit trail extraction.

---

## 4. Verification and Acceptance Criteria

### 4.1. Automated Test Coverage (`tests/test_chat_persistence_and_audit.py`)
1. `test_database_session_repository_save_and_retrieve`: Verifies lossless round-trip persistence of sessions.
2. `test_composite_repository_cache_hit_and_miss`: Verifies L1 cache hits and graceful fallback to L2 on cache eviction.
3. `test_chat_messages_preserve_tool_outputs_and_widgets`: Verifies data integrity of complex UI widget JSON structures.
4. `test_sandbox_operation_logging_jsonl`: Verifies structured JSON Lines export conformity and trace correlation.
5. `test_multi_tenant_company_isolation`: Asserts that cross-company session retrieval raises permission rejections.
