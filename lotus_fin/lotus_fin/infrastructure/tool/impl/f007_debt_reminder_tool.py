import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.schema.tool_definition import ToolDefinition
from lotus_fin.domain.schema.tool_execution_result import ToolExecutionResult
from lotus_fin.infrastructure.tool.command.base_tool_command import IToolCommand


class DebtReminderArgs(BaseModel):
    company: Optional[str] = Field(default=None, description="Company name")
    invoice_id: Optional[str] = Field(default=None, description="Specific invoice ID if mentioned (e.g. ACC-SINV-2026-00001)")
    as_of_date: Optional[str] = Field(default="2026-12-31", description="Cutoff date in YYYY-MM-DD")


class PrepareDebtReminderTool(IToolCommand):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="prepare_debt_reminder",
            description="Prepare an executive, structured debt reminder letter and lookup actual customer invoice data. Use whenever the user asks to draft, prepare, or send a reminder for overdue receivables/invoices ('soạn thư nhắc nợ', 'thư đòi nợ', 'nhắc nợ khách hàng').",
            parameters_schema=DebtReminderArgs.model_json_schema()
        )

    def is_authorized(self, user: UserPrincipal) -> bool:
        return bool(user.company)

    def execute(self, arguments: Dict[str, Any], user: UserPrincipal) -> ToolExecutionResult:
        company = arguments.get("company") or user.company or "Lotus-fin (Demo)"
        as_of_date = arguments.get("as_of_date") or user.as_of_date or "2026-12-31"
        target_inv_id = arguments.get("invoice_id")

        try:
            from lotus_fin.api.copilot_api import get_real_overdue_invoices, search_real_invoices

            matched_inv = None
            if target_inv_id:
                inv_search = search_real_invoices(company=company, prefix=target_inv_id, limit=5)
                found = inv_search.get("invoices", [])
                if found:
                    matched_inv = found[0]

            if not matched_inv:
                overdue_res = get_real_overdue_invoices(company=company, as_of_date=as_of_date)
                overdue_items = overdue_res.get("items", [])
                if overdue_items:
                    matched_inv = overdue_items[0]

            inv_id = (matched_inv or {}).get("invoiceId") or "ACC-SINV-2026-00001"
            customer_name = (matched_inv or {}).get("customerName") or "Grant Plastics Ltd."
            due_date = (matched_inv or {}).get("finalDueDate") or (matched_inv or {}).get("dueDate") or "25/10/2026"
            amount_val = (matched_inv or {}).get("outstandingAmount") or (matched_inv or {}).get("grandTotal") or 67000.0
            amount_str = f"{int(amount_val):,} VND"
            recipient_email = f"accounting@{customer_name.lower().replace(' ', '').replace('.', '')}.com"

            data = {
                "invoiceId": inv_id,
                "customerName": customer_name,
                "dueDate": due_date,
                "amountText": amount_str,
                "recipientEmail": recipient_email,
                "company": company,
            }

            return ToolExecutionResult(
                tool_call_id="",
                tool_name="prepare_debt_reminder",
                is_success=True,
                data=data,
                ui_widget={"type": "l3_followup", "data": data}
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_call_id="",
                tool_name="prepare_debt_reminder",
                is_success=False,
                error_message=str(e)
            )
