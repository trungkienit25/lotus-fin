from typing import Any, Dict
from pydantic import BaseModel, Field
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand


class HealthArgs(BaseModel):
    company: str = Field(..., description="Target company to inspect financial health")
    as_of_date: str = Field(default="2026-12-31", description="Cutoff date in YYYY-MM-DD")


class GetFinancialHealthTool(IToolCommand):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_financial_snapshot",
            description="Retrieve verified financial health snapshot (Revenue, COGS, Gross Profit, Cash Balance, AR, AP). Use whenever the user inquires about overall company performance or financial status.",
            parameters_schema=HealthArgs.model_json_schema()
        )

    def is_authorized(self, user: UserPrincipal) -> bool:
        return bool(user.company)

    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        from lotus_fin.core.plugin.registry import plugin_registry
        company = arguments.get("company") or user.company
        as_of_date = arguments.get("as_of_date") or user.as_of_date or "2026-12-31"

        res = plugin_registry.dispatch_tool("get_financial_snapshot", {
            "company": company,
            "as_of_date": as_of_date
        })

        return ToolExecutionResult(
            tool_call_id="",
            tool_name="get_financial_snapshot",
            is_success=True,
            data=res,
            ui_widget={"type": "financial_snapshot", "data": res}
        )

