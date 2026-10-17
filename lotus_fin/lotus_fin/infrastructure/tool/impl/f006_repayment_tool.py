from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand


class RepaymentArgs(BaseModel):
    principal: float = Field(..., description="Loan principal amount in USD")
    annual_rate: float = Field(default=0.085, description="Annual nominal interest rate as decimal (e.g. 0.085 for 8.5%)")
    tenure_months: int = Field(default=12, description="Loan term in months")
    method: str = Field(default="EQUAL_INSTALLMENT", description="Amortization method: EQUAL_INSTALLMENT or EQUAL_PRINCIPAL")
    rate_shock_bps: int = Field(default=0, description="Interest rate stress shock in basis points (e.g. 200 for +2.0%)")


class CalculateRepaymentScheduleTool(IToolCommand):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calculate_repayment_schedule",
            description="Calculate bank loan repayment schedule (monthly installment, principal, interest amortization) and evaluate interest rate shock resistance.",
            parameters_schema=RepaymentArgs.model_json_schema()
        )

    def is_authorized(self, user: UserPrincipal) -> bool:
        return True

    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        from lotus_fin.modules.f006_repayment.models import LoanTerms, AmortizationMethod, StressScenarioParams, StressType
        from lotus_fin.modules.f006_repayment.engine import RepaymentEngine
        from lotus_fin.modules.f006_repayment.stress import StressSimulationEngine

        principal = float(arguments.get("principal", 1000000000.0))
        rate = float(arguments.get("annual_rate", 0.085))
        term = int(arguments.get("tenure_months", 12))
        method_str = arguments.get("method", "EQUAL_INSTALLMENT")
        method = AmortizationMethod.EQUAL_INSTALLMENT if method_str == "EQUAL_INSTALLMENT" else AmortizationMethod.EQUAL_PRINCIPAL
        shock_bps = int(arguments.get("rate_shock_bps", 0))

        terms = LoanTerms(
            principal=Decimal(str(principal)),
            annual_rate=Decimal(str(rate)),
            term_months=term,
            amortization_method=method
        )
        engine = RepaymentEngine()
        schedule_result = engine.calculate_schedule(terms)
        summary = schedule_result.summary

        shock_added_cost = 0.0
        if shock_bps > 0:
            stress_params = StressScenarioParams(
                stress_type=StressType.RATE_SHOCK,
                rate_shock_bps=shock_bps
            )
            stress_engine = StressSimulationEngine()
            stress_res = stress_engine.run_stress_test(terms, stress_params)
            base_total_int = float(stress_res.base_schedule_summary.get("total_interest", 0.0))
            stressed_total_int = float(stress_res.stressed_schedule_summary.get("total_interest", 0.0))
            shock_added_cost = max(0.0, stressed_total_int - base_total_int)

        data = {
            "principal": principal,
            "annual_rate": rate,
            "tenure_months": term,
            "method": method_str,
            "monthly_payment": float(summary.get("first_payment", 0.0)),
            "total_interest": float(summary.get("total_interest", 0.0)),
            "total_cost": float(summary.get("total_repayment", 0.0)),
            "shock_bps": shock_bps,
            "shock_added_interest": shock_added_cost,
            "periods": [
                {
                    "period": p.get("period", 1),
                    "payment": float(p.get("total_payment", 0.0)),
                    "principal": float(p.get("principal_payment", 0.0)),
                    "interest": float(p.get("interest_payment", 0.0)),
                    "remaining_balance": float(p.get("closing_balance", 0.0))
                }
                for p in schedule_result.payment_schedule[:12]
            ]
        }

        return ToolExecutionResult(
            tool_call_id="",
            tool_name="calculate_repayment_schedule",
            is_success=True,
            data=data,
            ui_widget={"type": "repayment_schedule", "data": data}
        )
