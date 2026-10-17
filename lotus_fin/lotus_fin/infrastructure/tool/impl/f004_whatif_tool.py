from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand


class WhatIfArgs(BaseModel):
    company: str = Field(..., description="Target company")
    sales_change_pct: float = Field(default=-0.15, description="Sales shock % (e.g. -0.20 for -20%)")
    collection_delay_days: int = Field(default=15, description="Customer collection delay shift in days")
    supplier_due_shift_days: int = Field(default=0, description="Supplier payment extension in days")
    financing_amount: float = Field(default=0.0, description="Injected debt financing amount in USD")
    financing_term_months: int = Field(default=12, description="Loan term in months")
    financing_rate_annual: float = Field(default=0.095, description="Annual nominal interest rate")


class SimulateWhatIfTool(IToolCommand):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="simulate_what_if_scenario",
            description="Simulate multi-variable financial stress testing across 9 mission-critical business KPIs under revenue, collection delays, or debt financing shocks.",
            parameters_schema=WhatIfArgs.model_json_schema()
        )

    def is_authorized(self, user: UserPrincipal) -> bool:
        return bool(user.company)

    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        from lotus_fin.core.plugin.registry import plugin_registry
        company = arguments.get("company") or user.company

        args = dict(arguments)
        args["company"] = company
        res = plugin_registry.dispatch_tool("simulate_what_if_scenario", args)

        status = res.get("status") if isinstance(res, dict) else None
        is_success = status not in ["SOURCE_ERROR", "FORBIDDEN", "ERROR"]
        if not is_success:
            redacted_data = {k: v for k, v in res.items() if k != "error_message"} if isinstance(res, dict) else {}
            return ToolExecutionResult(
                tool_call_id="",
                tool_name="simulate_what_if_scenario",
                is_success=False,
                data=redacted_data,
                error_message="Simulation data source error.",
                ui_widget=None
            )

        return ToolExecutionResult(
            tool_call_id="",
            tool_name="simulate_what_if_scenario",
            is_success=True,
            data=res,
            ui_widget={"type": "what_if_simulation", "data": res}
        )
