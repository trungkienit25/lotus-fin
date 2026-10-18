"""
Module F005 - Financing AI Plugin Adapter.
Implements BaseLotusPlugin to connect Financing Decision Support to AI Orchestrator.
"""

from typing import Any, Dict, List, Optional
from lotus_fin.core.ai.tools.tool_registry import ToolDefinition
from lotus_fin.core.plugin.base_plugin import BaseLotusPlugin
from lotus_fin.modules.f005_financing.service import FinancingService


class FinancingPlugin(BaseLotusPlugin):
    """Plugin adapter exposing F005 Financing Decision tools & grounding facts."""

    def __init__(self, service: Optional[FinancingService] = None):
        self._service = service or FinancingService()

    @property
    def plugin_id(self) -> str:
        return "f005_financing"

    @property
    def name(self) -> str:
        return "AI-F005 Financing Copilot & Decision Support"

    @property
    def version(self) -> str:
        return "2026.1.0"

    @property
    def description(self) -> str:
        return "SME loan product matching, 3-tier eligibility scoring, and financing advisory."

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="match_financing_products",
                description="Match SME funding requests with banking loan catalog via 3-tier scoring.",
                parameters={
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name"},
                        "amount": {"type": "number", "description": "Funding amount in USD"},
                        "term_months": {"type": "integer", "description": "Loan tenor in months"},
                        "purpose": {"type": "string", "enum": ["WORKING_CAPITAL", "EQUIPMENT", "INVOICE_RECOVERY", "EXPANSION"]}
                    },
                    "required": ["company", "amount", "term_months"]
                },
                handler=lambda **kwargs: self._service.match_financing_for_company(**kwargs),
                read_only=True
            ),
            ToolDefinition(
                name="ask_financing_copilot",
                description="Natural language SME financing inquiry and loan recommendation synthesis.",
                parameters={
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name"},
                        "user_query": {"type": "string", "description": "Natural language financing inquiry"}
                    },
                    "required": ["company", "user_query"]
                },
                handler=lambda **kwargs: self._service.ask_financing_copilot(**kwargs),
                read_only=True
            )
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name == "match_financing_products":
            return self._service.match_financing_for_company(
                company=arguments["company"],
                amount=float(arguments["amount"]),
                term_months=int(arguments["term_months"]),
                purpose=arguments.get("purpose", "WORKING_CAPITAL")
            )
        elif tool_name == "ask_financing_copilot":
            return self._service.ask_financing_copilot(
                company=arguments["company"],
                user_query=arguments["user_query"]
            )
        raise KeyError(f"Unknown tool '{tool_name}' for plugin {self.plugin_id}")

    def get_grounding_context(self, company: str, **kwargs) -> Dict[str, Any]:
        """Provides verified financing eligibility facts for LLM prompt grounding."""
        try:
            profile = self._service._extract_company_profile_from_core(company)
            return {
                "feature": self.name,
                "company": company,
                "status": "AVAILABLE",
                "operating_months": profile.operating_months,
                "annual_revenue": float(profile.annual_revenue),
                "current_cash_balance": float(profile.current_cash_balance),
                "current_dscr": float(profile.current_dscr),
                "has_collateral": profile.has_collateral
            }
        except Exception as e:
            return {"feature": self.name, "company": company, "status": "UNAVAILABLE", "error": str(e)}
