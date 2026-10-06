from typing import Any, Dict
from pydantic import BaseModel, Field
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand


class CashflowArgs(BaseModel):
    company: str = Field(..., description="Target company to forecast cash flow")
    as_of_date: str = Field(default="2026-12-31", description="Cutoff date in YYYY-MM-DD")
    horizon_days: int = Field(default=30, description="Forecast horizon in days (default 30)")


class GetCashflowForecastTool(IToolCommand):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_cash_forecast",
            description="Compute deterministic 30-day EOD cash forecast, account balances, and detect cash shortfall / deficit risks.",
            parameters_schema=CashflowArgs.model_json_schema()
        )

    def is_authorized(self, user: UserPrincipal) -> bool:
        return bool(user.company)

    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        from lotus_fin.core.plugin.registry import plugin_registry
        company = arguments.get("company") or user.company
        as_of_date = arguments.get("as_of_date") or user.as_of_date or "2026-12-31"

        res = plugin_registry.dispatch_tool("get_cash_forecast", {
            "company": company,
            "as_of_date": as_of_date
        })

        return ToolExecutionResult(
            tool_call_id="",
            tool_name="get_cash_forecast",
            is_success=True,
            data=res,
            ui_widget={"type": "cash_forecast", "data": res}
        )

