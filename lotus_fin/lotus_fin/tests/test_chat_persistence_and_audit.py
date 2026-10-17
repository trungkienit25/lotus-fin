# -*- coding: utf-8 -*-
"""
Test Suite for Persistent Chat Storage and AI Sandbox Operational Audit Logging.
Verifies compliance with:
- OpenAI Assistant API v2 Thread/Message Standard
- OpenTelemetry GenAI Semantic Conventions (trace_id, latency_ms)
- FinTechathon 2026 Item 06 Execution Evidence
- Two-tier Composite Session Repository (L1 Cache + L2 Database)
- Enterprise Multi-tenant Isolation Boundaries
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from lotus_fin.application.service.copilot_service import CopilotService
from lotus_fin.application.service.operation_log_service import OperationLogService
from lotus_fin.domain.model.chat_message import ChatMessage
from lotus_fin.domain.model.chat_session import ChatSession
from lotus_fin.domain.model.message_role import MessageRole
from lotus_fin.domain.model.operation_log import SandboxOperationLogEntry
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.llm.adapter.mock_llm_adapter import MockLLMAdapter
from lotus_fin.infrastructure.observability.jsonlines_operation_log_repository import JsonLinesOperationLogRepository
from lotus_fin.infrastructure.persistence.composite_session_repository import CompositeSessionRepository
from lotus_fin.infrastructure.persistence.frappe_cache_session_repository import FrappeCacheSessionRepository
from lotus_fin.infrastructure.persistence.frappe_database_session_repository import FrappeDatabaseSessionRepository
from lotus_fin.presentation.controller.copilot_controller import (
    CopilotController,
    _session_repo,
    get_copilot_service
)


class TestChatPersistenceAndAuditLogging(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test_operation_logs.jsonl")
        self.mock_llm = MockLLMAdapter()
        self.service = get_copilot_service(llm_provider=self.mock_llm)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. ChatMessage & ChatSession Domain Invariants
    # -------------------------------------------------------------------------
    def test_chat_message_generates_unique_id_and_timestamp(self):
        """ChatMessage auto-assigns unique message_id and ISO UTC timestamp."""
        m1 = ChatMessage(role=MessageRole.USER, content="Hello")
        m2 = ChatMessage(role=MessageRole.USER, content="Hello")

        self.assertIsNotNone(m1.message_id)
        self.assertIsNotNone(m2.message_id)
        self.assertNotEqual(m1.message_id, m2.message_id)
        self.assertIsInstance(m1.timestamp, datetime)

    def test_chat_session_bounds_messages_and_tool_traces(self):
        """ChatSession strictly bounds message history and tool traces to prevent OOM."""
        session = ChatSession(id="test_bound", user_id="u1", company="Lotus")
        for i in range(70):
            session.add_message(ChatMessage(role=MessageRole.USER, content=f"msg_{i}"), max_history=40)
            session.add_tool_trace(ToolExecutionResult(
                tool_call_id=f"c_{i}",
                tool_name="test_tool",
                is_success=True,
                data={"idx": i}
            ), max_traces=30)

        self.assertEqual(len(session.messages), 40)
        self.assertEqual(session.messages[-1].content, "msg_69")
        self.assertEqual(len(session.tool_traces), 30)
        self.assertEqual(session.tool_traces[-1].data["idx"], 69)

    # -------------------------------------------------------------------------
    # 2. Database & Composite Session Repository
    # -------------------------------------------------------------------------
    def test_frappe_database_session_repository_crud(self):
        """FrappeDatabaseSessionRepository persists, retrieves, and clears sessions."""
        repo = FrappeDatabaseSessionRepository()
        session = ChatSession(id="sess_db_01", user_id="analyst@lotus.vn", company="Lotus-fin")
        session.add_message(ChatMessage(role=MessageRole.USER, content="What is our cash balance?"))
        session.add_message(ChatMessage(role=MessageRole.ASSISTANT, content="Your cash balance is 300M VND."))

        repo.save_session(session)
        loaded = repo.get_session("sess_db_01")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, "sess_db_01")
        self.assertEqual(loaded.company, "Lotus-fin")
        self.assertEqual(len(loaded.messages), 2)
        self.assertEqual(loaded.messages[1].content, "Your cash balance is 300M VND.")

        # Test listing
        listed = repo.list_sessions(company="Lotus-fin", user_id="analyst@lotus.vn")
        self.assertTrue(len(listed) >= 1)
        self.assertEqual(listed[0]["session_id"], "sess_db_01")
        self.assertEqual(listed[0]["id"], "sess_db_01")

        # Test clear
        repo.clear_session("sess_db_01")
        self.assertIsNone(repo.get_session("sess_db_01"))

    def test_composite_session_repository_l1_cache_promotion(self):
        """Composite repository promotes database session into L1 cache upon cache miss."""
        l1_cache = FrappeCacheSessionRepository()
        l2_db = FrappeDatabaseSessionRepository()
        composite = CompositeSessionRepository(l1_cache=l1_cache, l2_persistent=l2_db)

        # Directly save to L2 database (simulating background worker write)
        db_session = ChatSession(id="sess_promote", user_id="u2", company="CompX")
        db_session.add_message(ChatMessage(role=MessageRole.USER, content="Query 1"))
        l2_db.save_session(db_session)

        # L1 cache does not have it initially
        self.assertIsNone(l1_cache.get_session("sess_promote"))

        # Read through composite: should fetch from L2 and warm L1 cache
        fetched = composite.get_session("sess_promote")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, "sess_promote")

        # Now L1 cache must be populated
        self.assertIsNotNone(l1_cache.get_session("sess_promote"))

    # -------------------------------------------------------------------------
    # 3. AI Sandbox Operation Log Repository & Service
    # -------------------------------------------------------------------------
    def test_jsonlines_operation_log_append_and_query(self):
        """JsonLinesOperationLogRepository records structured audit trails in .jsonl format."""
        repo = JsonLinesOperationLogRepository(log_file_path=self.log_file)
        service = OperationLogService(repo)

        user = UserPrincipal(user_id="auditor@fintech.vn", company="Lotus-fin", roles=["Auditor"])

        entry = service.log_operation(
            session_id="sess_audit_01",
            user=user,
            prompt="Kiểm tra tín hiệu rủi ro quá hạn",
            reply="Đã phân tích 12 hóa đơn. Không phát hiện rủi ro.",
            tool_called="evaluate_risk_signal",
            tool_inputs={"signal_type": "AR_OVERDUE_SPIKE"},
            tool_output={"status": "BENIGN", "severity": "LOW"},
            latency_ms=142,
            status="SUCCESS",
            llm_provider="gemini",
            model_name="gemini-2.5-flash"
        )

        self.assertIsNotNone(entry.log_id)
        self.assertTrue(os.path.exists(self.log_file))

        # Query recent logs
        logs = service.get_recent_logs(company="Lotus-fin", session_id="sess_audit_01")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["log_id"], entry.log_id)
        self.assertEqual(logs[0]["tool_called"], "evaluate_risk_signal")
        self.assertEqual(logs[0]["agent_intent"], "F003_RISK_SIGNAL")
        self.assertIn("Sales Invoice", logs[0]["accounting_ledger_accessed"])
        self.assertEqual(logs[0]["latency_ms"], 142)

    # -------------------------------------------------------------------------
    # 4. CopilotController & Multi-Tenant Security
    # -------------------------------------------------------------------------
    def test_copilot_controller_returns_trace_id_and_latency(self):
        """CopilotController includes trace_id and latency_ms in ChatResponseDTO."""
        res = CopilotController.handle_send_message({
            "message": "Kiểm tra sức khỏe tài chính công ty",
            "company": "Lotus-fin (Demo)",
            "context_filters": {
                "user_id": "test_analyst",
                "roles": ["Accounts Manager"]
            }
        }, service=self.service)

        self.assertIn("reply", res)
        self.assertIn("latency_ms", res)
        self.assertTrue(res["latency_ms"] >= 0)
        self.assertIn("trace_id", res)
        self.assertIsNotNone(res["trace_id"])

    def test_copilot_controller_multi_tenant_session_isolation(self):
        """CopilotController prevents cross-tenant session hijacking."""
        # Save a session belonging to user_alice into the active session repository
        session = ChatSession(id="sess_alice_private", user_id="alice@comp.vn", company="CompA")
        session.add_message(ChatMessage(role=MessageRole.USER, content="Confidential Financial Plan"))
        _session_repo.save_session(session)

        # Bob attempts to read Alice's chat history
        with self.assertRaises(PermissionError) as ctx:
            CopilotController.handle_get_chat_history(
                session_id="sess_alice_private",
                company="CompA",
                user_id="bob@comp.vn"
            )
        self.assertIn("FORBIDDEN", str(ctx.exception))

    def test_copilot_controller_history_and_reset(self):
        """CopilotController retrieves ordered history and resets session cleanly."""
        session_id = "sess_history_test"
        # Send a message
        CopilotController.handle_send_message({
            "message": "Dự báo dòng tiền 30 ngày tới",
            "company": "Lotus-fin (Demo)",
            "session_id": session_id,
            "context_filters": {"user_id": "test_user", "roles": ["System Manager"]}
        }, service=self.service)

        # Retrieve history
        history = CopilotController.handle_get_chat_history(
            session_id=session_id,
            company="Lotus-fin (Demo)",
            user_id="test_user"
        )
        self.assertTrue(history["total"] >= 2)  # User prompt + Copilot response
        self.assertEqual(history["messages"][0]["role"], "user")
        self.assertEqual(history["messages"][1]["role"], "assistant")

        # Reset session
        reset_res = CopilotController.handle_reset_chat_session(
            session_id=session_id,
            company="Lotus-fin (Demo)"
        )
        self.assertEqual(reset_res["status"], "success")

        # History should now be empty
        empty_history = CopilotController.handle_get_chat_history(
            session_id=session_id,
            company="Lotus-fin (Demo)",
            user_id="test_user"
        )
        self.assertEqual(empty_history["total"], 0)


if __name__ == "__main__":
    unittest.main()

