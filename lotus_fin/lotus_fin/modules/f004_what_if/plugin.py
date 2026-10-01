"""
Module F004 - What-If Scenario AI Plugin Adapter.
Implements BaseLotusPlugin to connect What-If simulation capabilities to AI Orchestrator.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from lotus_fin.core.ai.tools.tool_registry import ToolDefinition
from lotus_fin.core.plugin.base_plugin import BaseLotusPlugin
from lotus_fin.modules.f004_what_if.service import ScenarioService
from lotus_fin.modules.f004_what_if.domain.models import ScenarioParameters


class WhatIfPlugin(BaseLotusPlugin):
    """Plugin adapter exposing F004 What-If simulation tools & grounding facts."""

    def __init__(self, service: Optional[ScenarioService] = None):
        self._service = service or ScenarioService()

    @property
    def plugin_id(self) -> str:
        return "f004_what_if"

    @property
    def name(self) -> str:
        return "AI-F004 What-If Cashflow Scenario Simulation"

    @property
    def version(self) -> str:
        return "2026.1.0"

    @property
    def description(self) -> str:
        return "Multi-variable cash flow stress testing and 9-KPI scenario simulation."

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="simulate_what_if_scenario",
                description="Simulate cash flow shock and get 9 deterministic financial KPIs.",
                parameters={
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name"},
                        "sales_change_pct": {"type": "number", "description": "e.g. -0.20 for -20%"},
                        "collection_delay_days": {"type": "integer", "description": "Delay in AR collection"},
                        "supplier_due_shift_days": {"type": "integer", "description": "Shift in AP due date"},
                        "financing_amount": {"type": "number", "description": "New financing injection amount"}
                    },
                    "required": ["company"]
                },
                handler=lambda **kwargs: self._service.run_simulation_for_company(**kwargs),
                read_only=True
            )
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "simulate_what_if_scenario":
            return self._service.run_simulation_for_company(
                company=arguments["company"],
                sales_change_pct=Decimal(str(arguments.get("sales_change_pct", 0.0))),
                collection_delay_days=int(arguments.get("collection_delay_days", 0)),
                supplier_due_shift_days=int(arguments.get("supplier_due_shift_days", 0)),
                financing_amount=Decimal(str(arguments.get("financing_amount", 0.0)))
            )
        raise KeyError(f"Unknown tool '{tool_name}' for plugin {self.plugin_id}")

    def get_grounding_context(self, company: str, **kwargs) -> Dict[str, Any]:
        """Provides verified simulation metrics for LLM prompt grounding."""
        try:
            res = self._service.run_simulation_for_company(
                company=company,
                sales_change_pct=Decimal(str(kwargs.get("sales_change_pct", 0.0))),
                collection_delay_days=int(kwargs.get("collection_delay_days", 0))
            )
            return {
                "feature": self.name,
                "company": company,
                "status": "AVAILABLE",
                "summary": res.get("summary", {}),
                "metrics": res.get("metrics", {})
            }
        except Exception as e:
            return {"feature": self.name, "company": company, "status": "UNAVAILABLE", "error": str(e)}
