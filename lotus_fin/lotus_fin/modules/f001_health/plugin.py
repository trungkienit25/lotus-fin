"""
Module F001 - Financial Health AI Plugin Adapter.
Implements BaseLotusPlugin to connect Financial Health capabilities to AI Orchestrator.
"""

from typing import Any, Dict, List, Optional
from lotus_fin.core.ai.tools.tool_registry import ToolDefinition
from lotus_fin.core.plugin.base_plugin import BaseLotusPlugin
from lotus_fin.modules.f001_health.service import HealthService


class HealthPlugin(BaseLotusPlugin):
    """Plugin adapter exposing F001 Financial Health tools & grounding facts."""

    def __init__(self, service: Optional[HealthService] = None):
        self._service = service or HealthService()

    @property
    def plugin_id(self) -> str:
        return "f001_health"

    @property
    def name(self) -> str:
        return "AI-F001 Financial Health Inspection"

    @property
    def version(self) -> str:
        return "2026.1.0"

    @property
    def description(self) -> str:
        return "Deterministic financial health inspection, KPI verification, and evidence auditing."

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="get_financial_snapshot",
                description="Retrieve verified financial health snapshot (Revenue, COGS, Cash, AR, AP).",
                parameters={
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name"},
                        "period_start": {"type": "string", "description": "YYYY-MM-DD"},
                        "period_end": {"type": "string", "description": "YYYY-MM-DD"}
                    },
                    "required": ["company", "period_start", "period_end"]
                },
                handler=lambda **kwargs: self._service.get_financial_snapshot(**kwargs),
                read_only=True
            )
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "get_financial_snapshot":
            return self._service.get_financial_snapshot(
                company=arguments["company"],
                period_start=arguments["period_start"],
                period_end=arguments["period_end"]
            )
        raise KeyError(f"Unknown tool '{tool_name}' for plugin {self.plugin_id}")

    def get_grounding_context(self, company: str, **kwargs) -> Dict[str, Any]:
        """Provides verified numeric facts for LLM prompt grounding."""
        p_start = kwargs.get("period_start", "2020-01-01")
        p_end = kwargs.get("period_end", "2020-12-31")
        snapshot = self._service.get_financial_snapshot(
            company=company,
            period_start=p_start,
            period_end=p_end
        )
        return {
            "feature": self.name,
            "company": company,
            "period": snapshot.get("period"),
            "status": snapshot.get("status"),
            "metrics": [
                {
                    "metric_id": m.get("metric_id"),
                    "status": m.get("status"),
                    "value": m.get("value"),
                    "currency_or_unit": m.get("currency_or_unit")
                }
                for m in snapshot.get("metrics", [])
            ],
            "limitations": snapshot.get("limitations", [])
        }
