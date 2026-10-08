from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand


class FinancingArgs(BaseModel):
    company: str = Field(..., description="Target company")
    amount: float = Field(..., description="Desired loan capital need in VND")
    term_months: int = Field(default=12, description="Desired repayment tenure in months")
    purpose: str = Field(default="WORKING_CAPITAL", description="Funding purpose: WORKING_CAPITAL, MACHINERY, EXPANSION, INVOICE_DISCOUNTING")
    collateral_value: float = Field(default=0.0, description="Available collateral security value in VND")


class MatchFinancingProductsTool(IToolCommand):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="match_financing_products",
            description="Match SME financing and bank loan packages against corporate eligibility criteria, calculating match scores and interest expenses.",
            parameters_schema=FinancingArgs.model_json_schema()
        )

    def is_authorized(self, user: UserPrincipal) -> bool:
        return bool(user.company)

    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        from lotus_fin.core.plugin.registry import plugin_registry
        company = arguments.get("company") or user.company

        args = dict(arguments)
        args["company"] = company
        res = plugin_registry.dispatch_tool("match_financing_products", args)

        return ToolExecutionResult(
            tool_call_id="",
            tool_name="match_financing_products",
            is_success=True,
            data=res,
            ui_widget={"type": "financing_products", "data": res}
        )

