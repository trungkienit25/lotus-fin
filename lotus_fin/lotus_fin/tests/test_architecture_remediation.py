"""
Comprehensive Remediation Test Suite for Lotus Fin Blockers B01–B08.
Tests:
- B01 & B02: AI004 What-If Permission check, BaselineSourceError propagation, typed statuses (SOURCE_ERROR, INSUFFICIENT_DATA).
- B03: AI005 Financing Service data provenance, explicit demo vs verified profile, no silent fake data.
- B04: Copilot routing error propagation and AI003 EvaluateRiskSignalTool contract compliance.
- B05: AI006 Repayment Engine invariants, input validation, and schedule reconciliation.
- B06: Chat session security, multi-worker isolation, ownership check, and message retention limit.
- B07: ToolInvoker schema validation and AgentRunner tool budget enforcement.
- B08: LLMProviderFactory provider fail-fast validation.
"""

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult

from lotus_fin.modules.f004_what_if.domain.enums import SimulationStatus
from lotus_fin.modules.f004_what_if.domain.models import ScenarioParameters
from lotus_fin.modules.f004_what_if.service import ScenarioService
from lotus_fin.modules.f004_what_if.adapters.baseline_adapter import BaselineSourceAdapter, BaselineSourceError

from lotus_fin.modules.f005_financing.service import FinancingService
from lotus_fin.modules.f005_financing.models import CompanyFinancialProfile

from lotus_fin.modules.f006_repayment.engine import RepaymentEngine
from lotus_fin.modules.f006_repayment.models import LoanTerms, AmortizationMethod, PaymentFrequency

from lotus_fin.infrastructure.persistence.frappe_cache_session_repository import FrappeCacheSessionRepository
from lotus_fin.application.service.copilot_service import CopilotService
from lotus_fin.application.agent.agent_runner import AgentRunner
from lotus_fin.application.port.i_llm_provider import LLMResponse
from lotus_fin.infrastructure.tool.impl.f001_health_tool import GetFinancialHealthTool
from lotus_fin.infrastructure.tool.impl.f004_whatif_tool import SimulateWhatIfTool
from lotus_fin.domain.repository.i_session_repository import StorageUnavailable
from lotus_fin.infrastructure.tool.invoker.tool_invoker import ToolInvoker
from lotus_fin.infrastructure.tool.registry.tool_registry import ToolRegistry
from lotus_fin.infrastructure.tool.impl.f003_risk_tool import EvaluateRiskSignalTool
from lotus_fin.infrastructure.llm.llm_factory import LLMProviderFactory


class TestArchitectureRemediation(unittest.TestCase):

    # -------------------------------------------------------------
    # B01 & B02: AI004 What-If Scenario Permission & Error Typing
    # -------------------------------------------------------------
    def test_b01_b02_baseline_adapter_source_error_propagation(self):
        """BaselineSourceAdapter raises BaselineSourceError instead of swallowing exceptions."""
        adapter = BaselineSourceAdapter(checked_user="test_user")
        with patch("lotus_fin.modules.f004_what_if.adapters.baseline_adapter.frappe") as mock_frappe:
            mock_frappe.db.sql.side_effect = RuntimeError("Database connection timed out")
            with self.assertRaises(BaselineSourceError):
                adapter._get_opening_cash("Test Company", date(2026, 1, 1))

    def test_b01_b02_scenario_service_typed_source_error(self):
        """ScenarioService returns SOURCE_ERROR status when adapter raises BaselineSourceError."""
        mock_adapter = MagicMock()
        mock_adapter.get_baseline_data.side_effect = BaselineSourceError("DB failure")
        service = ScenarioService(baseline_adapter=mock_adapter)

        params = ScenarioParameters(
            company="FailCompany",
            as_of=date(2026, 1, 1)
        )
        res = service.run_scenario(params)
        self.assertEqual(res.status, SimulationStatus.SOURCE_ERROR)
        self.assertIn("DB failure", res.error_message)

    def test_b01_b02_scenario_service_insufficient_data(self):
        """ScenarioService flags INSUFFICIENT_DATA when baseline cash is 0 and events are empty."""
        mock_adapter = MagicMock()
        mock_adapter.get_baseline_data.return_value = (Decimal("0.00"), [])
        service = ScenarioService(baseline_adapter=mock_adapter)

        params = ScenarioParameters(company="EmptyCompany", as_of=date(2026, 1, 1))
        res = service.run_scenario(params)
        self.assertEqual(res.status, SimulationStatus.INSUFFICIENT_DATA)

    # -------------------------------------------------------------
    # B03: AI005 Financing Service Data Provenance & No Silent Fakes
    # -------------------------------------------------------------
    def test_b03_financing_data_provenance_labels(self):
        """Financing service stamps data_mode='demo' or 'verified' explicitly."""
        svc = FinancingService(ai_provider="mock")
        demo_profile = svc._extract_company_profile_from_core("Lotus-fin (Demo)")
        self.assertEqual(demo_profile.data_mode, "demo")

        custom_profile = svc._build_profile("CustomComp", {"annual_revenue": "5000000000", "data_mode": "manual"})
        self.assertEqual(custom_profile.data_mode, "manual")

    def test_b03_financing_insufficient_data_rejection(self):
        """Financing service raises ValueError if real company data is absent and allow_demo is False."""
        svc = FinancingService(ai_provider="mock")
        with self.assertRaises(ValueError) as ctx:
            svc._extract_company_profile_from_core("RealUnregisteredCompanyXYZ", allow_demo=False)
        self.assertIn("INSUFFICIENT_DATA", str(ctx.exception))

    # -------------------------------------------------------------
    # B04: AI003 Contract Alignment & Copilot Routing
    # -------------------------------------------------------------
    def test_b04_f003_risk_tool_contract_execution(self):
        """EvaluateRiskSignalTool invokes evaluate_signal with payload, checked_user, and deps."""
        tool = EvaluateRiskSignalTool()
        user = UserPrincipal(user_id="analyst@lotus.vn", company="Lotus-fin")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"signal_id": "AR_OVERDUE_SPIKE", "status": "BENIGN"}
        mock_result.status.value = "BENIGN"

        with patch("lotus_fin.modules.f003_risk_signal.service.evaluate_signal", return_value=mock_result) as mock_eval, \
             patch("lotus_fin.security.access._default_gateway.verify_company", return_value="Lotus-fin"):
            exec_res = tool.execute({"signal_type": "AR_OVERDUE_SPIKE"}, user)
            self.assertTrue(exec_res.is_success)
            mock_eval.assert_called_once()
            args, kwargs = mock_eval.call_args
            self.assertEqual(kwargs["checked_user"], "analyst@lotus.vn")
            self.assertIn("deps", kwargs)
            self.assertEqual(kwargs["payload"]["company"], "Lotus-fin")

    # -------------------------------------------------------------
    # B05: AI006 Repayment Engine Invariants & Reconciliation
    # -------------------------------------------------------------
    def test_b05_repayment_engine_negative_principal_rejected(self):
        """RepaymentEngine strictly rejects non-positive principal."""
        engine = RepaymentEngine()
        terms = LoanTerms(
            principal=Decimal("-1000"),
            annual_rate=Decimal("0.10"),
            term_months=12
        )
        with self.assertRaises(ValueError) as ctx:
            engine.calculate_schedule(terms)
        self.assertIn("Principal must be strictly positive", str(ctx.exception))

    def test_b05_repayment_engine_grace_greater_than_term_rejected(self):
        """RepaymentEngine rejects grace_period >= term_months."""
        engine = RepaymentEngine()
        terms = LoanTerms(
            principal=Decimal("100000000"),
            annual_rate=Decimal("0.10"),
            term_months=12,
            grace_period_months=12
        )
        with self.assertRaises(ValueError) as ctx:
            engine.calculate_schedule(terms)
        self.assertIn("must be strictly less than loan term", str(ctx.exception))

    def test_b05_repayment_engine_quarterly_alignment(self):
        """RepaymentEngine requires quarterly term to be divisible by 3."""
        engine = RepaymentEngine()
        terms = LoanTerms(
            principal=Decimal("100000000"),
            annual_rate=Decimal("0.10"),
            term_months=10,  # Not divisible by 3
            payment_frequency=PaymentFrequency.QUARTERLY
        )
        with self.assertRaises(ValueError) as ctx:
            engine.calculate_schedule(terms)
        self.assertIn("divisible by 3", str(ctx.exception))

    def test_b05_repayment_engine_summary_reconciliation(self):
        """total_repayment in summary strictly equals sum(schedule total_payment) + total_fees."""
        engine = RepaymentEngine()
        terms = LoanTerms(
            principal=Decimal("500000000"),
            annual_rate=Decimal("0.095"),
            term_months=24,
            amortization_method=AmortizationMethod.EQUAL_INSTALLMENT,
            processing_fee_pct=Decimal("0.015")
        )
        res = engine.calculate_schedule(terms)
        sum_schedule_payments = sum(Decimal(str(r["total_payment"])) for r in res.payment_schedule)
        total_fees = Decimal(str(res.summary["total_fees"]))
        expected_total = (sum_schedule_payments + total_fees).quantize(Decimal("0.01"))
        self.assertEqual(Decimal(str(res.summary["total_repayment"])), expected_total)

    # -------------------------------------------------------------
    # B06: Session Security, Ownership Isolation, Message Retention
    # -------------------------------------------------------------
    def test_b06_session_cross_user_hijack_prevention(self):
        """CopilotService rejects access if session belongs to another user."""
        repo = FrappeCacheSessionRepository()
        prior_session = ChatSession(id="sess_1", user_id="user_alice", company="Company A")
        repo.save_session(prior_session)

        copilot_svc = CopilotService(
            llm_provider=MagicMock(),
            tool_registry=MagicMock(),
            tool_invoker=MagicMock(),
            session_repository=repo
        )
        malicious_user = UserPrincipal(user_id="user_bob", company="Company A")

        with self.assertRaises(PermissionError) as ctx:
            copilot_svc.process_message("sess_1", "Show me sensitive reports", malicious_user)
        self.assertIn("FORBIDDEN", str(ctx.exception))

    def test_b06_session_cross_company_access_prevention(self):
        """CopilotService rejects access if session belongs to another company context."""
        repo = FrappeCacheSessionRepository()
        prior_session = ChatSession(id="sess_2", user_id="user_alice", company="Company A")
        repo.save_session(prior_session)

        copilot_svc = CopilotService(
            llm_provider=MagicMock(),
            tool_registry=MagicMock(),
            tool_invoker=MagicMock(),
            session_repository=repo
        )
        switched_user = UserPrincipal(user_id="user_alice", company="Company B")

        with self.assertRaises(PermissionError) as ctx:
            copilot_svc.process_message("sess_2", "Query financials", switched_user)
        self.assertIn("FORBIDDEN", str(ctx.exception))

    def test_b06_chat_session_message_retention_bound(self):
        """ChatSession bounds history size to prevent unbounded memory exhaustion."""
        session = ChatSession(id="sess_bound", user_id="user", company="comp")
        for i in range(70):
            session.add_message(ChatMessage(role=MessageRole.USER, content=f"Msg {i}"), max_history=50)
        self.assertEqual(len(session.messages), 50)
        self.assertEqual(session.messages[-1].content, "Msg 69")

    # -------------------------------------------------------------
    # B07: Tool Invoker Schema Validation & AgentRunner Tool Budget
    # -------------------------------------------------------------
    def test_b07_tool_invoker_validates_required_arguments(self):
        """ToolInvoker fails early when required parameter schema is violated."""
        mock_tool = MagicMock()
        mock_tool.is_authorized.return_value = True
        mock_tool.definition.name = "dummy_tool"
        mock_tool.definition.parameters_schema = {
            "type": "object",
            "required": ["company", "as_of_date"],
            "properties": {"company": {"type": "string"}, "as_of_date": {"type": "string"}}
        }

        registry = ToolRegistry()
        registry.register(mock_tool)

        invoker = ToolInvoker(registry)
        user = UserPrincipal(user_id="admin", company="comp")

        # Call missing 'as_of_date'
        call = ToolCallRequest(id="call_1", tool_name="dummy_tool", arguments={"company": "Lotus"})
        res = invoker.invoke(call, user)

        self.assertFalse(res.is_success)
        self.assertIn("Missing required parameter(s): as_of_date", res.error_message)

    def test_b07_agent_runner_enforces_tool_budget_limit(self):
        """AgentRunner cuts off tool execution when max_total_tools limit is reached."""
        mock_invoker = MagicMock()
        mock_invoker.invoke.return_value = ToolExecutionResult(
            tool_call_id="call", tool_name="dummy", is_success=True, data={"res": 1}
        )

        mock_llm = MagicMock()
        # Simulate LLM returning 3 tool calls per iteration
        call_req = ToolCallRequest(id="c1", tool_name="dummy", arguments={})
        res_with_calls = MagicMock()
        res_with_calls.has_tool_calls = True
        res_with_calls.tool_calls = [call_req, call_req, call_req]
        res_with_calls.content = None

        res_final = MagicMock()
        res_final.has_tool_calls = False
        res_final.content = "All done"

        mock_llm.generate.side_effect = [res_with_calls, res_with_calls, res_final]

        runner = AgentRunner(mock_llm, mock_invoker, max_iterations=4, max_total_tools=4)
        session = ChatSession(id="s_budget", user_id="u", company="c")
        user = UserPrincipal(user_id="u", company="c")

        agent_res = runner.run(session, "prompt", [], user)
        # Should execute at most 4 calls before budget cut-off
        self.assertEqual(mock_invoker.invoke.call_count, 4)

    # -------------------------------------------------------------
    # B08: LLM Provider Fail-Fast Validation
    # -------------------------------------------------------------
    def test_b08_llm_provider_fail_fast_unknown(self):
        """LLMProviderFactory raises ValueError on unknown provider rather than silent fallback."""
        with self.assertRaises(ValueError) as ctx:
            LLMProviderFactory.create_provider(provider_name="nonexistent_llm_provider")
    # -------------------------------------------------------------
    # Security Hardening & Fail-Closed Guardrails
    # -------------------------------------------------------------
    def test_b01_copilot_controller_rejects_guest(self):
        """CopilotController rejects Guest user fail-closed."""
        from lotus_fin.presentation.controller.copilot_controller import CopilotController
        with patch("lotus_fin.presentation.controller.copilot_controller.frappe") as mock_frappe:
            mock_frappe.session.user = "Guest"
            with self.assertRaises(PermissionError):
                CopilotController.handle_send_message({
                    "message": "What is the cash balance?",
                    "company": "Wind Power LLC"
                })

    def test_b01_copilot_controller_rejects_unauthenticated_session(self):
        """CopilotController rejects None or empty user in session."""
        from lotus_fin.presentation.controller.copilot_controller import CopilotController
        with patch("lotus_fin.presentation.controller.copilot_controller.frappe") as mock_frappe:
            mock_frappe.session.user = None
            with self.assertRaises(PermissionError):
                CopilotController.handle_send_message({
                    "message": "What is the cash balance?",
                    "company": "Wind Power LLC"
                })

    def test_b06_chat_session_bounds_tool_traces(self):
        """ChatSession bounds tool_traces to prevent unbounded memory growth."""
        session = ChatSession(id="s_traces", user_id="u", company="c")
        for i in range(70):
            session.add_tool_trace(ToolExecutionResult(
                tool_call_id=f"c_{i}",
                tool_name="test_tool",
                is_success=True,
                data={"idx": i}
            ))
        self.assertEqual(len(session.tool_traces), 50)
        self.assertEqual(session.tool_traces[-1].data["idx"], 69)
        self.assertEqual(session.tool_traces[0].data["idx"], 20)


    # -------------------------------------------------------------
    # Round 3 Findings F01-F10 Regression Tests (N01-N15 Probes)
    # -------------------------------------------------------------
    def test_f01_n01_session_concurrent_barrier_retains_both_turns(self):
        """F01 / N01: Concurrent sessions retain both turns or report conflict with stable IDs."""
        data = {}
        cache = MagicMock()
        cache.get_value.side_effect = lambda k: data.get(k)
        cache.set_value.side_effect = lambda k, v, **kw: data.__setitem__(k, v)
        cache.delete_value.side_effect = lambda k: data.pop(k, None)
        def mock_set(k, v, nx=False, ex=None):
            if nx:
                if k in data:
                    return False
                data[k] = v
                return True
            data[k] = v
            return True
        cache.set.side_effect = mock_set
        cache.eval.side_effect = lambda script, numkeys, key, token: data.pop(key, None) if data.get(key) == token else 0
        fake_frappe = MagicMock()
        fake_frappe.cache.return_value = cache

        with patch("lotus_fin.infrastructure.persistence.frappe_cache_session_repository.frappe", fake_frappe):
            repo1 = FrappeCacheSessionRepository()
            repo2 = FrappeCacheSessionRepository()
            repo1.save_session(ChatSession(id="race_n01", user_id="u", company="c"))

            a = repo1.get_session("race_n01")
            b = repo2.get_session("race_n01")
            a.add_message(ChatMessage(role=MessageRole.USER, content="TURN_A"))
            b.add_message(ChatMessage(role=MessageRole.USER, content="TURN_B"))
            repo1.save_session(a)
            repo2.save_session(b)
            final = repo1.get_session("race_n01")

        contents = [m.content for m in final.messages]
        self.assertIn("TURN_A", contents)
        self.assertIn("TURN_B", contents)

    def test_f01_n02_repeated_user_text_preserves_both_messages(self):
        """F01 / N02: Repeated user messages with identical content are not deduplicated."""
        repo = FrappeCacheSessionRepository()
        session = ChatSession(id="n02_repeat", user_id="u", company="c")
        session.add_message(ChatMessage(role=MessageRole.USER, content="What is revenue?"))
        session.add_message(ChatMessage(role=MessageRole.USER, content="What is revenue?"))
        self.assertEqual(len(session.messages), 2)
        # Message IDs must be unique
        self.assertNotEqual(session.messages[0].message_id, session.messages[1].message_id)

    def test_f04_n03_storage_unavailable_raised_on_connection_error(self):
        """F04 / N03: Redis connection error raises StorageUnavailable rather than silent fallback."""
        from lotus_fin.domain.repository.i_session_repository import StorageUnavailable
        fake_frappe = MagicMock()
        fake_frappe.cache.side_effect = ConnectionError("Redis connection refused")

        with patch("lotus_fin.infrastructure.persistence.frappe_cache_session_repository.frappe", fake_frappe):
            repo = FrappeCacheSessionRepository()
            with self.assertRaises(StorageUnavailable):
                repo.get_session("sess_outage")
            with self.assertRaises(StorageUnavailable):
                repo.save_session(ChatSession(id="sess_outage", user_id="u", company="c"))

    def test_f08_n04_missing_server_session_fails_closed(self):
        """F08 / N04: Missing frappe.session fails closed without client auth bypass."""
        from lotus_fin.presentation.controller.copilot_controller import CopilotController
        fake_frappe = MagicMock()
        fake_frappe.session = None

        with patch("lotus_fin.presentation.controller.copilot_controller.frappe", fake_frappe):
            with self.assertRaises(PermissionError):
                CopilotController.handle_send_message({
                    "message": "probe",
                    "company": "Company A",
                    "context_filters": {"test_mode": True, "user_id": "admin", "roles": ["System Manager"]}
                })

    def test_f02_n05_zero_financial_values_preserved_not_replaced(self):
        """F02 / N05: 0.0 financial metrics are valid data and not replaced with sample defaults."""
        svc = FinancingService(ai_provider="mock")
        zero_metrics = [
            {"metric_id": "revenue", "status": "AVAILABLE", "value": 0.0},
            {"metric_id": "cash_balance", "status": "AVAILABLE", "value": 0.0},
            {"metric_id": "cogs", "status": "AVAILABLE", "value": 0.0},
            {"metric_id": "ar_balance", "status": "AVAILABLE", "value": 0.0},
            {"metric_id": "ap_balance", "status": "AVAILABLE", "value": 0.0},
        ]
        snapshot = svc._extract_default_base_snapshot("ZeroCorp", raw_metrics=zero_metrics)
        self.assertEqual(snapshot["revenue"], 0.0)
        self.assertEqual(snapshot["opening_cash"], 0.0)
        self.assertNotEqual(snapshot["revenue"], 1_000_000_000.0)

    def test_f02_n06_missing_source_for_real_company_does_not_silently_fallback_to_demo(self):
        """F02 / N06: Missing source for real company returns insufficient mode, never demo."""
        svc = FinancingService(ai_provider="mock")
        # Empty metrics simulates missing ERP data for real company
        snapshot = svc._extract_default_base_snapshot("RealCorpWithoutData", raw_metrics=[])
        self.assertEqual(snapshot["data_mode"], "insufficient")
        self.assertNotEqual(snapshot["data_mode"], "demo")

    def test_f03_n07_partial_profile_not_promoted_to_verified(self):
        """F03 / N07: Profile with only 2 metrics is marked partial/manual, not verified."""
        svc = FinancingService(ai_provider="mock")
        mock_snapshot = {
            "status": "OK",
            "company": "PartialCorp",
            "metrics": [
                {"metric_id": "revenue", "status": "AVAILABLE", "value": 500000000},
                {"metric_id": "cash_balance", "status": "AVAILABLE", "value": 100000000}
            ]
        }
        fake_api = MagicMock()
        fake_api.get_financial_snapshot.return_value = mock_snapshot
        fake_runtime = MagicMock(db=object())
        with patch.dict("sys.modules", {"frappe": fake_runtime, "lotus_fin.api.ai_insights": fake_api}):
            profile = svc._extract_company_profile_from_core("PartialCorp")
        self.assertNotEqual(profile.data_mode, "verified")

    def test_f03_n08_client_data_mode_cannot_self_claim_verified_or_audited(self):
        """F03 / N08: Client input claiming verified/audited is demoted to manual."""
        svc = FinancingService(ai_provider="mock")
        profile = svc._build_profile("SelfClaimCorp", {
            "annual_revenue": "1000000000",
            "data_mode": "verified"
        })
        self.assertEqual(profile.data_mode, "manual")

        profile_audited = svc._build_profile("SelfClaimCorp", {
            "annual_revenue": "1000000000",
            "data_mode": "audited"
        })
        self.assertEqual(profile_audited.data_mode, "manual")

    def test_f06_n09_tool_invoker_validates_nested_and_typed_schemas(self):
        """F06 / N09: ToolInvoker enforces recursive schema constraints (types, nested, arrays)."""
        mock_tool = MagicMock()
        mock_tool.is_authorized.return_value = True
        mock_tool.definition.name = "nested_schema_tool"
        mock_tool.definition.parameters_schema = {
            "type": "object",
            "required": ["config", "amounts"],
            "properties": {
                "config": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}}
                },
                "amounts": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "integer"}
                }
            }
        }
        registry = ToolRegistry()
        registry.register(mock_tool)
        invoker = ToolInvoker(registry)
        user = UserPrincipal(user_id="analyst", company="Lotus")

        # 1. Missing nested required field 'name'
        res1 = invoker.invoke(ToolCallRequest(
            id="c1", tool_name="nested_schema_tool",
            arguments={"config": {}, "amounts": [10]}
        ), user)
        self.assertFalse(res1.is_success)

        # 2. Empty array violates minItems: 1
        res2 = invoker.invoke(ToolCallRequest(
            id="c2", tool_name="nested_schema_tool",
            arguments={"config": {"name": "test"}, "amounts": []}
        ), user)
        self.assertFalse(res2.is_success)

        # 3. Item wrong type (string instead of integer)
        res3 = invoker.invoke(ToolCallRequest(
            id="c3", tool_name="nested_schema_tool",
            arguments={"config": {"name": "test"}, "amounts": ["not_int"]}
        ), user)
        self.assertFalse(res3.is_success)

    def test_f05_n10_generic_error_redaction_prevents_secret_leaks(self):
        """F05 / N10: Error redaction removes arbitrary sensitive tokens, not just blacklisted keywords."""
        tool = MagicMock()
        tool.definition = ToolDefinition(name="sensitive_tool", description="test", parameters_schema={})
        tool.is_authorized.return_value = True
        tool.execute.side_effect = RuntimeError("FATAL_POSTGRES_PASSWORD_998877 at internal_cluster_node_2")
        registry = ToolRegistry()
        registry.register(tool)
        invoker = ToolInvoker(registry)
        user = UserPrincipal(user_id="user", company="Lotus")

        res = invoker.invoke(ToolCallRequest(id="c_err", tool_name="sensitive_tool", arguments={}), user)
        self.assertFalse(res.is_success)
        self.assertNotIn("FATAL_POSTGRES_PASSWORD_998877", res.error_message)
        self.assertIn("Internal processing error occurred.", res.error_message)

    def test_f05_n11_whatif_error_redacts_raw_exception_in_payload_and_widget(self):
        """F05 / N11: What-If tool redacts raw exception from payload, clearing widget."""
        tool = SimulateWhatIfTool()
        user = UserPrincipal(user_id="analyst", company="Lotus")
        mock_dispatch_res = {
            "status": "SOURCE_ERROR",
            "error_message": "RAW_INTERNAL_DB_ERROR_XYZ",
            "ui_widget": {"chart": "data"}
        }

        with patch("lotus_fin.core.plugin.registry.plugin_registry.dispatch_tool", return_value=mock_dispatch_res), \
             patch("lotus_fin.security.access.get_verified_company", return_value="Lotus"):
            res = tool.execute({"company": "Lotus", "as_of": "2026-01-01"}, user)

        self.assertFalse(res.is_success)
        self.assertNotIn("RAW_INTERNAL_DB_ERROR_XYZ", str(res.data))
        self.assertIsNone(res.ui_widget)

    def test_f07_n12_budget_exceeded_status_propagated_to_response_dto(self):
        """F07 / N12: Agent budget exceeded preserves BUDGET_EXCEEDED status in ChatResponseDTO."""
        from lotus_fin.presentation.dto.chat_response import ChatResponseDTO
        llm = MagicMock()
        inv = MagicMock()
        llm.generate.return_value = LLMResponse(content="", tool_calls=[
            ToolCallRequest(id="a", tool_name="p", arguments={}),
            ToolCallRequest(id="b", tool_name="p", arguments={})
        ])
        inv.invoke.return_value = ToolExecutionResult(tool_call_id="a", tool_name="p", is_success=True, data={})
        runner = AgentRunner(llm, inv, max_iterations=2, max_total_tools=1)
        session = ChatSession(id="s_n12", user_id="u", company="c")
        user = UserPrincipal(user_id="u", company="c")

        agent_res = runner.run(session, "prompt", [], user)
        self.assertEqual(agent_res.status, "BUDGET_EXCEEDED")

        dto = ChatResponseDTO(
            session_id=session.id,
            reply=agent_res.reply,
            tool_traces=[],
            status=agent_res.status
        )
        self.assertEqual(dto.status, "BUDGET_EXCEEDED")

    def test_f07_n13_business_error_statuses_mark_tool_success_false(self):
        """F07 / N13: Business errors (SOURCE_ERROR, FORBIDDEN) set is_success=False on tools."""
        tool = GetFinancialHealthTool()
        user = UserPrincipal(user_id="u", company="Lotus")

        with patch("lotus_fin.core.plugin.registry.plugin_registry.dispatch_tool",
                   return_value={"status": "SOURCE_ERROR", "error_message": "DB failed"}), \
             patch("lotus_fin.security.access.get_verified_company", return_value="Lotus"):
            res = tool.execute({"company": "Lotus"}, user)
            self.assertFalse(res.is_success)

    def test_f09_n14_llm_factory_supports_lotus_llm_api_key_alias_for_gemini(self):
        """F09 / N14: LLMProviderFactory honors LOTUS_LLM_API_KEY alias for Gemini."""
        with patch.dict("os.environ", {"LOTUS_LLM_API_KEY": "test_alias_key_123"}, clear=True), \
             patch("lotus_fin.infrastructure.llm.llm_factory._ensure_env_loaded"):
            provider = LLMProviderFactory.create_provider("gemini")
            self.assertEqual(provider.api_key, "test_alias_key_123")

    def test_f09_n14_empty_provider_fails_fast_in_production(self):
        """F09 / N14: Empty or missing provider fails fast instead of falling back to MockLLMAdapter."""
        with self.assertRaises(ValueError):
            LLMProviderFactory.create_provider(provider_name="")

    def test_batch_d_n15_positive_control_valid_profile_and_repayment(self):
        """Batch D / N15: Positive control for valid inputs (repayment calculation & clean profile)."""
        engine = RepaymentEngine()
        terms = LoanTerms(
            principal=Decimal("100000000"),
            annual_rate=Decimal("0.10"),
            term_months=12
        )
        res = engine.calculate_schedule(terms)
        self.assertEqual(len(res.payment_schedule), 12)
        self.assertEqual(Decimal(str(res.summary["principal"])), Decimal("100000000"))


if __name__ == "__main__":
    unittest.main()
