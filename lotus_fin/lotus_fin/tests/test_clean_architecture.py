import unittest
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_call_request import ToolCallRequest
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.llm.adapter.mock_llm_adapter import MockLLMAdapter
from lotus_fin.infrastructure.persistence.in_memory_session_repository import InMemorySessionRepository
from lotus_fin.infrastructure.tool.registry.default_tools import create_default_tool_registry
from lotus_fin.infrastructure.tool.invoker.tool_invoker import ToolInvoker
from lotus_fin.application.agent.agent_runner import AgentRunner
from lotus_fin.application.service.copilot_service import CopilotService
from lotus_fin.presentation.dto.chat_request import SendMessageDTO
from lotus_fin.presentation.dto.chat_response import ChatResponseDTO
from lotus_fin.presentation.controller.copilot_controller import CopilotController


class TestCleanArchitectureDomainAndInfrastructure(unittest.TestCase):
    def setUp(self):
        self.user = UserPrincipal(
            user_id="test_admin@example.com",
            company="Wind Power LLC",
            roles=["System Manager"],
            as_of_date="2026-12-31"
        )
        self.registry = create_default_tool_registry()
        self.invoker = ToolInvoker(self.registry)
        self.session_repo = InMemorySessionRepository()

    def test_domain_model_creation_and_context_window(self):
        session = ChatSession(id="sess_1", user_id="u1", company="Wind Power LLC")
        for i in range(15):
            session.add_message(ChatMessage(role=MessageRole.USER, content=f"Msg {i}"))

        self.assertEqual(len(session.messages), 15)
        window = session.get_context_window(max_messages=5)
        self.assertEqual(len(window), 5)
        self.assertEqual(window[-1].content, "Msg 14")

    def test_tool_registry_discovers_all_6_tools(self):
        tools = self.registry.get_available_tools(self.user)
        tool_names = {t.name for t in tools}
        expected = {
            "get_financial_snapshot",
            "get_cash_forecast",
            "evaluate_risk_signal",
            "simulate_what_if_scenario",
            "match_financing_products",
            "calculate_repayment_schedule"
        }
        self.assertTrue(expected.issubset(tool_names), f"Missing tools: {expected - tool_names}")

    def test_repayment_tool_execution(self):
        call = ToolCallRequest(
            id="call_f006",
            tool_name="calculate_repayment_schedule",
            arguments={"principal": 500000000.0, "annual_rate": 0.08, "tenure_months": 12, "rate_shock_bps": 200}
        )
        res = self.invoker.invoke(call, self.user)
        self.assertTrue(res.is_success)
        self.assertIsNotNone(res.data)
        self.assertIn("monthly_payment", res.data)
        self.assertIn("shock_added_interest", res.data)
        self.assertGreater(res.data["shock_added_interest"], 0)
        self.assertIsNotNone(res.ui_widget)
        self.assertEqual(res.ui_widget["type"], "repayment_schedule")

    def test_agent_runner_react_loop_with_tool_call(self):
        canned_call = ToolCallRequest(
            id="call_mock_1",
            tool_name="calculate_repayment_schedule",
            arguments={"principal": 1000000000.0, "annual_rate": 0.09, "tenure_months": 12}
        )
        mock_provider = MockLLMAdapter(
            canned_tool_call=canned_call,
            canned_response="Grounded analysis: Loan monthly installment is calculated precisely."
        )

        runner = AgentRunner(
            llm_provider=mock_provider,
            tool_invoker=self.invoker,
            max_iterations=4
        )

        session = ChatSession(id="sess_react", user_id=self.user.user_id, company=self.user.company)
        session.add_message(ChatMessage(role=MessageRole.USER, content="Calculate loan schedule for 1B VND at 9%"))

        tools = self.registry.get_available_tools(self.user)
        result = runner.run(session, "System Instructions", tools, self.user)

        self.assertEqual(result.tool_called, "calculate_repayment_schedule")
        self.assertIsNotNone(result.tool_output)
        self.assertIn("Grounded analysis", result.reply)
        self.assertIn("calculate_repayment_schedule", result.executed_tools)

    def test_copilot_service_end_to_end(self):
        canned_call = ToolCallRequest(
            id="call_mock_f005",
            tool_name="calculate_repayment_schedule",
            arguments={"principal": 1000000000.0, "annual_rate": 0.085, "tenure_months": 12}
        )
        mock_provider = MockLLMAdapter(
            canned_tool_call=canned_call,
            canned_response="Repayment schedule generated successfully."
        )

        service = CopilotService(
            llm_provider=mock_provider,
            tool_registry=self.registry,
            tool_invoker=self.invoker,
            session_repository=self.session_repo
        )

        resp_dict = service.process_message(
            session_id="session_test_123",
            message="Please build repayment schedule for 1B VND",
            user=self.user
        )

        self.assertEqual(resp_dict["session_id"], "session_test_123")
        self.assertEqual(resp_dict["tool_called"], "calculate_repayment_schedule")
        self.assertIn("Repayment schedule", resp_dict["reply"])

        # Check DTO serialization
        dto = ChatResponseDTO(**resp_dict)
        self.assertEqual(dto.session_id, "session_test_123")

        # Verify session persistence
        saved_session = self.session_repo.get_session("session_test_123")
        self.assertIsNotNone(saved_session)
        self.assertEqual(len(saved_session.messages), 2)  # 1 User + 1 Assistant
        self.assertEqual(len(saved_session.tool_traces), 1)

    def test_copilot_controller_presentation_layer(self):
        canned_call = ToolCallRequest(
            id="call_ctrl_1",
            tool_name="calculate_repayment_schedule",
            arguments={"principal": 1000000000.0, "annual_rate": 0.085, "tenure_months": 12}
        )
        mock_provider = MockLLMAdapter(
            canned_tool_call=canned_call,
            canned_response="Controller executed cleanly through Presentation Layer."
        )
        service = CopilotService(
            llm_provider=mock_provider,
            tool_registry=self.registry,
            tool_invoker=self.invoker,
            session_repository=self.session_repo
        )

        res = CopilotController.handle_send_message(
            request_data={
                "message": "Loan inquiry via DTO",
                "company": "Wind Power LLC",
                "session_id": "test_ctrl_session"
            },
            service=service
        )

        self.assertIn("session_id", res)
        self.assertEqual(res["session_id"], "test_ctrl_session")
        self.assertEqual(res["tool_called"], "calculate_repayment_schedule")
        self.assertIn("Controller executed cleanly", res["reply"])
        self.assertIsNotNone(res["ui_widget"])

