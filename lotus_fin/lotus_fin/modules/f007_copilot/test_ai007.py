"""
Unit tests for AI007 Financial Copilot Orchestrator.
"""

import unittest

# Import orchestrator
try:
    from lotus_fin.modules.f007_copilot.models import CopilotRequest, IntentType
    from lotus_fin.modules.f007_copilot.orchestrator import CopilotOrchestrator
except ImportError:
    from lotus_fin.AI007.models import CopilotRequest, IntentType
    from lotus_fin.AI007.orchestrator import CopilotOrchestrator


class TestAI007CopilotOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = CopilotOrchestrator()
        
    def test_routing_financing(self):
        """Test luồng hội thoại yêu cầu tìm gói vay."""
        req = CopilotRequest(message="Tôi cần tìm gói vay 500 triệu cho công ty", session_id="test1")
        resp = self.orchestrator.process_request(req)
        
        self.assertEqual(resp.intent, IntentType.FINANCING_SUPPORT)
        
        # Nếu AI005 khả dụng, nó sẽ có widget
        if resp.ui_widgets:
            widget = resp.ui_widgets[0]
            self.assertEqual(widget["widget_type"], "FINANCING_TABLE")

    def test_routing_stress_test(self):
        """Test luồng hội thoại yêu cầu mô phỏng trả nợ và stress test."""
        req = CopilotRequest(message="Lập lịch trả nợ nếu lãi suất tăng 2% nhé", session_id="test2")
        resp = self.orchestrator.process_request(req)
        
        self.assertEqual(resp.intent, IntentType.REPAYMENT_STRESS)
        
        # Nếu AI006 khả dụng, nó sẽ có widget STRESS_COMPARISON
        if resp.ui_widgets:
            widget = resp.ui_widgets[0]
            self.assertEqual(widget["widget_type"], "STRESS_COMPARISON")

    def test_routing_fallback(self):
        """Test câu hỏi không rõ ràng."""
        req = CopilotRequest(message="Xin chào, bạn làm được gì?", session_id="test3")
        resp = self.orchestrator.process_request(req)
        
        self.assertEqual(resp.intent, IntentType.GENERAL_QA)
        self.assertTrue("Tôi là Trợ lý Tài chính" in resp.reply_message)


if __name__ == "__main__":
    unittest.main()
