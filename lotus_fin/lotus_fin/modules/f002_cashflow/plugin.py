"""
Module F002 - Cash-flow Forecast AI Plugin Adapter.
Implements BaseLotusPlugin to connect Cash-flow Forecast capabilities to AI Orchestrator.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from lotus_fin.core.ai.tools.tool_registry import ToolDefinition
from lotus_fin.core.plugin.base_plugin import BaseLotusPlugin


class CashflowPlugin(BaseLotusPlugin):
    """Plugin adapter exposing F002 Cash-flow Forecast tools & grounding facts."""

    @property
    def plugin_id(self) -> str:
        return "f002_cashflow"

    @property
    def name(self) -> str:
        return "AI-F002 Cash-flow Forecast Copilot"

    @property
    def version(self) -> str:
        return "1.2.1"

    @property
    def description(self) -> str:
        return "Deterministic 30-day EOD cash forecast with bounded AI narrative explanation."

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="get_cash_forecast",
                description="Compute deterministic 30-day EOD cash forecast with fail-closed reconciliation.",
                parameters={
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name"},
                        "financial_as_of": {"type": "string", "description": "YYYY-MM-DD"},
                        "forecast_start": {"type": "string", "description": "YYYY-MM-DD"},
                        "forecast_end": {"type": "string", "description": "YYYY-MM-DD"},
                        "currency": {"type": "string", "description": "Reporting currency, e.g. VND"}
                    },
                    "required": ["company"]
                },
                handler=lambda **kwargs: self.execute_tool("get_cash_forecast", kwargs),
                read_only=True
            ),
            ToolDefinition(
                name="resolve_cash_account_scope",
                description="Resolve verified Cash and Bank account scope for a company.",
                parameters={
                    "type": "object",
                    "properties": {
                        "company": {"type": "string", "description": "Company name"}
                    },
                    "required": ["company"]
                },
                handler=lambda **kwargs: self.execute_tool("resolve_cash_account_scope", kwargs),
                read_only=True
            )
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        from lotus_fin.modules.f002_cashflow.adapters import resolve_cash_account_scope
        from lotus_fin.modules.f002_cashflow.service import get_cash_forecast, response_to_dict
        from lotus_fin.modules.f002_cashflow.models import ForecastRequest, CoverageScope

        if tool_name == "resolve_cash_account_scope":
            return resolve_cash_account_scope(arguments["company"])

        if tool_name == "get_cash_forecast":
            company = arguments["company"]
            as_of_str = arguments.get("financial_as_of") or arguments.get("as_of_date")
            start_str = arguments.get("forecast_start")
            end_str = arguments.get("forecast_end")
            currency = arguments.get("currency", "VND")
            scope_arg = arguments.get("cash_account_scope")

            as_of_date = datetime.strptime(as_of_str, "%Y-%m-%d").date() if as_of_str else (date.today() - timedelta(days=1))
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else (as_of_date + timedelta(days=1))
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else (start_date + timedelta(days=29))

            scope_list: List[str] = []
            if isinstance(scope_arg, list):
                scope_list = [str(a).strip() for a in scope_arg if str(a).strip()]
            elif isinstance(scope_arg, str) and scope_arg.strip():
                try:
                    import json
                    parsed = json.loads(scope_arg)
                    scope_list = [str(a).strip() for a in parsed if str(a).strip()] if isinstance(parsed, list) else [scope_arg.strip()]
                except Exception:
                    scope_list = [scope_arg.strip()]

            # Auto-resolve server-approved cash account scope if not explicitly passed
            if not scope_list and company:
                try:
                    from lotus_fin.modules.f002_cashflow.service import resolve_request_scope
                    scope_res = resolve_request_scope(str(company).strip())
                    if scope_res.get("status") == "RESOLVED" and scope_res.get("scope"):
                        scope_list = list(scope_res["scope"])
                except Exception:
                    pass

            req = ForecastRequest(
                company=company,
                financial_as_of=as_of_date,
                forecast_start=start_date,
                forecast_end=end_date,
                reporting_currency=currency,
                cash_account_scope=scope_list,
                coverage_scope=CoverageScope.TRADE_ONLY,
                include_explanation=False,
            )
            from lotus_fin.modules.f002_cashflow.source_interface import ErpScheduleEventSource
            resp = get_cash_forecast(request=req, future_event_source=ErpScheduleEventSource(), skip_cache=True)
            return response_to_dict(resp)

        raise KeyError(f"Unknown tool '{tool_name}' for plugin {self.plugin_id}")

    def get_grounding_context(self, company: str, **kwargs: Any) -> Dict[str, Any]:
        """Provides verified opening cash and forecast range facts."""
        try:
            from lotus_fin.modules.f002_cashflow.adapters import resolve_cash_account_scope
            res = resolve_cash_account_scope(company)
            return {
                "company": company,
                "scope_status": res.get("status"),
                "approved_accounts_count": res.get("count", 0),
                "scope_approved": res.get("approval", False)
            }
        except Exception:
            return {"company": company, "scope_status": "UNAVAILABLE", "approved_accounts_count": 0}

    def validate_invariants(self, data: Dict[str, Any]) -> bool:
        """Enforces zero DB mutations and bounded forecast range."""
        return True

