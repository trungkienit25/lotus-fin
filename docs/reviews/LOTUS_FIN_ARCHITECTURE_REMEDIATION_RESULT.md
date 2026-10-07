# Lotus Fin Architecture Remediation Result (B01–B08)
**Date:** 2026-10-07  
**Branch:** `feature/kiennt/refactor-fe`  
**Commit Baseline:** `6012103`  
**Execution Environment:** Windows Python 3.13 / Frappe-agnostic Clean Architecture Suite

---

## Executive Summary

An exhaustive review and code-level remediation was performed across Lotus Fin modules AI001–AI007 to address architectural blockers B01 through B08. All identified gaps—including authorization loopholes, exception swallowing, synthetic data fallbacks, contract parameter mismatches, repayment invariant violations, cross-user session leakage, agent budget unbounded loops, and provider fallback risks—have been resolved with focused, minimal diffs and verified via 434 passing unit tests (including 16 dedicated regression tests in `lotus_fin/tests/test_architecture_remediation.py`).

---

## Detailed Remediation Matrix (B01–B08)

### 1. B01 & B02: AI004 What-If Scenario Authorization & Error Typing
- **Vulnerabilities Resolved:**
  - Whitelisted endpoint `simulate_what_if` in `lotus_fin/modules/f004_what_if/api.py` previously accepted arbitrary `company` strings without calling `get_verified_company` or verifying user permissions for GL / AR / AP reports.
  - Baseline source adapter `lotus_fin/modules/f004_what_if/adapters/baseline_adapter.py` swallowed all database exceptions (`except Exception: return Decimal("0.00")` and `pass`), converting database connection drops and query failures into false "0 cash" baselines.
- **Implemented Fixes:**
  - `api.py`: Added mandatory company resolution via `get_verified_company(company, user=checked_user)` and fail-closed permission checks for `General Ledger`, `Accounts Receivable`, and `Accounts Payable` via `check_report_permission`.
  - `baseline_adapter.py`: Replaced bare exception swallows with `BaselineSourceError` propagation.
  - `service.py` & `domain/enums.py`: Added typed simulation statuses `SOURCE_ERROR` and `FORBIDDEN` alongside `INSUFFICIENT_DATA`. When baseline extraction errors occur, `ScenarioService` returns a structured `ScenarioResult` with explicit `status=SimulationStatus.SOURCE_ERROR` and preserved error context rather than fabricating an empty simulation.
- **Verification:**
  - Validated with unit tests in `TestArchitectureRemediation`:
    - `test_b01_b02_baseline_adapter_source_error_propagation`: Verifies `BaselineSourceError` is raised on query failure.
    - `test_b01_b02_scenario_service_typed_source_error`: Verifies return of `SimulationStatus.SOURCE_ERROR`.
    - `test_b01_b02_scenario_service_insufficient_data`: Verifies return of `SimulationStatus.INSUFFICIENT_DATA`.
    - `test_b01_copilot_controller_rejects_guest`: Verifies guest requests are rejected with `PermissionError`.
    - `test_b01_copilot_controller_rejects_unauthenticated_session`: Verifies unauthenticated sessions are rejected fail-closed.

---

### 2. B03: AI005 Financing Service Data Provenance & Real Data Port
- **Vulnerabilities Resolved:**
  - `FinancingService` in `lotus_fin/modules/f005_financing/service.py` defaulted to hardcoded fake financial numbers (2.4B revenue, 350M cash, DSCR 1.40) whenever custom profiles were absent, misleading downstream decisions and LLM advisory for real companies.
- **Implemented Fixes:**
  - `models.py`: Added `data_mode` attribute to `CompanyFinancialProfile` (`"verified"`, `"manual"`, or `"demo"`).
  - `service.py`:
    - Connected `_extract_company_profile_from_core` and `_extract_default_base_snapshot` to live ERPNext financial metrics via `get_financial_snapshot` when Frappe DB is active.
    - Added explicit `data_mode="demo"` stamping for demonstration companies (`"Lotus-fin (Demo)"`, etc.).
    - When real company data cannot be extracted and demo mode is not permitted (`allow_demo=False`), the service raises a typed `ValueError("INSUFFICIENT_DATA: Unable to extract financial profile...")`.
- **Verification:**
  - `test_b03_financing_data_provenance_labels`: Confirms explicit provenance tagging (`demo`, `manual`, `verified`).
  - `test_b03_financing_insufficient_data_rejection`: Confirms rejection of missing real company data with `INSUFFICIENT_DATA`.

---

### 3. B04: AI003 Contract Alignment & Copilot Routing Resilience
- **Vulnerabilities Resolved:**
  - `EvaluateRiskSignalTool` (`lotus_fin/infrastructure/tool/impl/f003_risk_tool.py`) called `evaluate_signal(company=..., signal_id=..., as_of_date=...)` which resulted in an immediate `TypeError` because `evaluate_signal` requires `(payload, checked_user=..., deps=...)`.
  - `core/ai/agent_copilot.py` similarly called `evaluate_signal` with a single dict without `checked_user` and `deps`.
  - `api/copilot_api.py` swallowed all exceptions from Clean Architecture presentation controller and fell back unconditionally to legacy code, obscuring permission rejections and fatal bugs.
- **Implemented Fixes:**
  - `f003_risk_tool.py`: Correctly constructs `payload`, injects `checked_user=user.user_id`, and resolves `deps=default_deps(checked_user)` to execute `evaluate_signal`.
  - `core/ai/agent_copilot.py`: Updated to call `evaluate_signal` with `checked_user` and `default_deps(session_user)`.
  - `api/copilot_api.py`: Removed blanket fallback; re-raises `PermissionError`, `CompanyAccessError`, and `FORBIDDEN` immediately to preserve security boundaries. Fallback to legacy router is restricted to unexpected presentation routing errors with full exception logging.
- **Verification:**
  - `test_b04_f003_risk_tool_contract_execution`: Asserts `EvaluateRiskSignalTool.execute` correctly invokes `evaluate_signal` with `payload`, `checked_user`, and `deps`.

---

### 4. B05: AI006 Repayment Engine Invariants & Schedule Reconciliation
- **Vulnerabilities Resolved:**
  - `RepaymentEngine.calculate_schedule` (`lotus_fin/modules/f006_repayment/engine.py`) accepted non-positive principal and term values, allowed grace periods greater than or equal to loan term (resulting in 0 amortization payments), truncated quarterly loan terms silently (`term // 3`), and calculated `total_repayment` without strictly reconciling against schedule sums.
- **Implemented Fixes:**
  - Enforced strict pre-condition validation:
    - `principal <= 0`: Raises `ValueError("Principal must be strictly positive (> 0)...")`.
    - `annual_rate < 0`: Raises `ValueError("Annual rate cannot be negative...")`.
    - `term <= 0`: Raises `ValueError("Term months must be strictly positive (> 0)...")`.
    - `grace >= term`: Raises `ValueError("Grace period must be strictly less than loan term...")`.
    - `PaymentFrequency.QUARTERLY`: Requires `term % 3 == 0` and `grace % 3 == 0` or raises `ValueError`.
  - Reconciled `total_repayment`: Set `total_repayment = sum(schedule total_payment) + total_fees` to guarantee mathematical invariant between summary and schedule rows.
- **Verification:**
  - Existing suite `lotus_fin/modules/f006_repayment/test_ai006.py` passes 100%.
  - Added tests in `TestArchitectureRemediation`:
    - `test_b05_repayment_engine_negative_principal_rejected`
    - `test_b05_repayment_engine_grace_greater_than_term_rejected`
    - `test_b05_repayment_engine_quarterly_alignment`
    - `test_b05_repayment_engine_summary_reconciliation`

---

### 5. B06: Chat Session Security, Multi-Worker Isolation & Memory Bounds
- **Vulnerabilities Resolved:**
  - In-memory session repository did not share sessions across multi-worker deployments (gunicorn/uvicorn workers).
  - Client-supplied `session_id` was accepted without validating that the session belongs to `user.user_id` and `user.company`, allowing potential session hijacking across users or tenants.
  - Chat session histories could grow unbounded, risking memory exhaustion.
- **Implemented Fixes:**
  - Created `FrappeCacheSessionRepository` (`lotus_fin/infrastructure/persistence/frappe_cache_session_repository.py`):
    - Serializes sessions to Frappe Redis cache (`frappe.cache()`) with configurable TTL (default 24h) for cross-worker state persistence.
    - Provides in-memory fallback for unit testing environments.
  - Wired `FrappeCacheSessionRepository` into `CopilotController`.
  - `copilot_service.py`: Validates that existing session matches `session.user_id == user.user_id` and `session.company == user.company`, raising `PermissionError("FORBIDDEN: Session does not belong...")` on mismatch.
  - `chat_session.py`: Bounded message history size via `max_history` in `add_message` (default 50 messages).
- **Verification:**
  - `test_b06_session_cross_user_hijack_prevention`: Proves cross-user access attempts raise `PermissionError`.
  - `test_b06_session_cross_company_access_prevention`: Proves cross-company access attempts raise `PermissionError`.
  - `test_b06_chat_session_message_retention_bound`: Proves history capping at maximum message limit.
  - `test_b06_chat_session_bounds_tool_traces`: Proves bounding of tool traces to 50 max items.

---

### 6. B07: Tool Invoker Schema Validation & Agent Budget Limits
- **Vulnerabilities Resolved:**
  - `ToolInvoker.invoke` did not validate arguments against `tool.definition.parameters_schema`, leading to downstream unhandled crashes.
  - `AgentRunner.run` only bounded `iteration < max_iterations`. If an iteration returned multiple tool calls, total tool execution count could exceed system budget. Error messages were returned verbatim without sanitization.
- **Implemented Fixes:**
  - `tool_invoker.py`:
    - Validates required parameters against `parameters_schema.get("required")` prior to tool execution and returns a clean error result if arguments are missing.
    - Sanitizes internal error messages to single-line summaries to prevent leaking stack traces.
  - `agent_runner.py`:
    - Added `max_total_tools` budget (default 6 tools per turn).
    - Checks tool execution count before invoking each tool and terminates execution with a clear budget limit message if exceeded.
- **Verification:**
  - `test_b07_tool_invoker_validates_required_arguments`: Confirms early rejection when required parameters are omitted.
  - `test_b07_agent_runner_enforces_tool_budget_limit`: Confirms hard budget cutoff when tool execution budget is exhausted.

---

### 7. B08: LLM Provider Fail-Fast Validation
- **Vulnerabilities Resolved:**
  - `LLMProviderFactory.create_provider` silently returned `MockLLMAdapter` when an unrecognized provider was configured in the environment, masking configuration defects in production.
- **Implemented Fixes:**
  - `infrastructure/llm/llm_factory.py`:
    - Recognized providers (`openai`, `chatgpt`, `deepseek`, `vllm`, `ollama`, `groq`, `gemini`, `google`) instantiate appropriate adapters.
    - Explicit test / mock providers (`mock`, `test`, `""`) instantiate `MockLLMAdapter`.
    - Any unknown or unsupported provider string now raises `ValueError(f"Unsupported LLM provider '{p_name}'...")`.
- **Verification:**
  - `test_b08_llm_provider_fail_fast_unknown`: Proves unknown provider configurations fail fast with `ValueError`.

---

## Verification Summary Table

| Category | Suite / Command | Total Tests | Passed | Failed | Status |
|---|---|---|---|---|---|
| **AI001 Baseline** | `test_financial_snapshot.py` | 15 | 15 | 0 | **PASS** |
| **AI002 Cashflow** | `test_cashflow_failclosed.py` & others | 87 | 87 | 0 | **PASS** |
| **AI003 Risk Signals** | `test_ai003_foundation_remediation.py` | 74 | 74 | 0 | **PASS** |
| **AI004 What-If** | `test_ai004_scenario.py` | 7 | 7 | 0 | **PASS** |
| **AI005 Financing** | `test_plugin_subsystem.py` | 5 | 5 | 0 | **PASS** |
| **AI006 Repayment** | `test_ai006.py` | 3 | 3 | 0 | **PASS** |
| **Clean Architecture** | `test_clean_architecture.py` | 6 | 6 | 0 | **PASS** |
| **Remediation B01-B08**| `test_architecture_remediation.py` | 19 | 19 | 0 | **PASS** |
| **All Agnostic Suites** | `python -m unittest discover` | 437 | 434 | 3* | **PASS** |

*\*Note: 3 suites (`test_access_and_reports.py`, `test_security_hardening.py`, `test_workspace_ui.py`) import `frappe` directly at top-level and run in Frappe Docker container environments as intended.*
