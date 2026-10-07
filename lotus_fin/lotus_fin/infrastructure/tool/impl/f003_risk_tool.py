from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand


class RiskSignalArgs(BaseModel):
    company: str = Field(..., description="Target company to evaluate")
    signal_type: str = Field(default="AR_OVERDUE_SPIKE", description="Signal ID: AR_OVERDUE_SPIKE or AP_DUE_CLUSTER")
    as_of_date: str = Field(default="2026-12-31", description="Cutoff date in YYYY-MM-DD")


class EvaluateRiskSignalTool(IToolCommand):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="evaluate_risk_signal",
            description="Evaluate accounts receivable (AR overdue spikes) or accounts payable (AP due clusters) risk signals with verified voucher evidence.",
            parameters_schema=RiskSignalArgs.model_json_schema()
        )

    def is_authorized(self, user: UserPrincipal) -> bool:
        return bool(user.company)

    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        from lotus_fin.modules.f003_risk_signal.service import evaluate_signal, default_deps
        company = arguments.get("company") or user.company
        as_of_date = arguments.get("as_of_date") or user.as_of_date or "2026-12-31"
        signal_type = arguments.get("signal_type") or "AR_OVERDUE_SPIKE"

        checked_user = user.user_id or "Administrator"
        deps = default_deps(checked_user)

        payload = {
            "company": company,
            "signal_id": signal_type,
            "as_of_date": as_of_date
        }

        try:
            res = evaluate_signal(
                payload=payload,
                checked_user=checked_user,
                deps=deps,
                include_explanation=True
            )
            res_dict = res.to_dict() if hasattr(res, "to_dict") else dict(res.__dict__)
            is_success = res.status.value in ["TRIGGERED", "BENIGN", "INCONCLUSIVE", "SUCCESS"] if hasattr(res, "status") else True
            err_msg = None if is_success else f"Risk signal evaluation status: {res.status.value}"

            return ToolExecutionResult(
                tool_call_id="",
                tool_name="evaluate_risk_signal",
                is_success=is_success,
                data=res_dict,
                error_message=err_msg,
                ui_widget={"type": "risk_signal", "data": res_dict}
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_call_id="",
                tool_name="evaluate_risk_signal",
                is_success=False,
                error_message=str(e),
                data={"error": str(e)}
            )

