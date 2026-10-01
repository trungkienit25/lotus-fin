"""
Test Suite for Lotus Fin AI Plugin Subsystem and Domain Modules.
Verifies:
1. Plugin Registry registration and tool schema export.
2. Intermediary strategy dispatching to domain modules (F001, F004, F005).
3. Grounding context gathering across plugins.
4. AI Agent Orchestrator with Grounding Guard.
"""

import unittest
from decimal import Decimal

from lotus_fin.core.plugin.registry import LotusPluginRegistry
from lotus_fin.core.ai.agent_orchestrator import AgentOrchestrator
from lotus_fin.modules.f001_health.plugin import HealthPlugin
from lotus_fin.modules.f004_what_if.plugin import WhatIfPlugin
from lotus_fin.modules.f005_financing.plugin import FinancingPlugin


class TestPluginSubsystem(unittest.TestCase):

    def setUp(self):
        self.registry = LotusPluginRegistry()
        self.health_plugin = HealthPlugin()
        self.what_if_plugin = WhatIfPlugin()
        self.financing_plugin = FinancingPlugin()

        self.registry.register(self.health_plugin)
        self.registry.register(self.what_if_plugin)
        self.registry.register(self.financing_plugin)

    def test_plugin_registration_and_listing(self):
        plugins = self.registry.list_plugins()
        self.assertEqual(len(plugins), 3)
        plugin_ids = [p["plugin_id"] for p in plugins]
        self.assertIn("f001_health", plugin_ids)
        self.assertIn("f004_what_if", plugin_ids)
        self.assertIn("f005_financing", plugin_ids)

    def test_export_all_tool_schemas(self):
        schemas = self.registry.export_all_tool_schemas()
        self.assertGreater(len(schemas), 0)
        tool_names = [s["function"]["name"] for s in schemas]
        self.assertIn("get_financial_snapshot", tool_names)
        self.assertIn("simulate_what_if_scenario", tool_names)
        self.assertIn("match_financing_products", tool_names)

    def test_tool_dispatching_strategy(self):
        # 1. Dispatch Financing Matcher
        res_fin = self.registry.dispatch_tool(
            "match_financing_products",
            {"company": "Lotus-fin (Demo)", "amount": 500000000.0, "term_months": 12}
        )
        self.assertIn(res_fin["status"], ["SUCCESS", "NO_MATCH"])
        self.assertIn("policy_declaration", res_fin)

        # 2. Dispatch What-If Simulation
        res_sim = self.registry.dispatch_tool(
            "simulate_what_if_scenario",
            {"company": "Lotus-fin (Demo)", "sales_change_pct": -0.15, "collection_delay_days": 10}
        )
        self.assertIn("simulated_metrics", res_sim)
        self.assertEqual(res_sim["data_mode"], "simulation")


    def test_gather_grounding_context(self):
        context = self.registry.gather_grounding_context("Lotus-fin (Demo)")
        self.assertIn("f001_health", context)
        self.assertIn("f004_what_if", context)
        self.assertIn("f005_financing", context)
        self.assertEqual(context["f005_financing"]["status"], "AVAILABLE")

    def test_agent_orchestrator_grounded_task(self):
        orchestrator = AgentOrchestrator(provider_name="mock")
        result = orchestrator.run_grounded_task(
            company="Lotus-fin (Demo)",
            user_prompt="Assess borrowing capacity and explain financial risks"
        )
        self.assertIn(result["status"], ["AVAILABLE", "UNAVAILABLE"])
        self.assertIn("model", result)


if __name__ == "__main__":
    unittest.main()
