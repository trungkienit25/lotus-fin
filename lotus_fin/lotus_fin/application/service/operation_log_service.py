# -*- coding: utf-8 -*-
import logging
import uuid
from typing import Any, Dict, List, Optional

from lotus_fin.application.port.i_operation_log_service import IOperationLogService
from lotus_fin.domain.model.operation_log import SandboxOperationLogEntry
from lotus_fin.domain.model.user_context import UserPrincipal
from lotus_fin.domain.repository.i_operation_log_repository import IOperationLogRepository

_logger = logging.getLogger("lotus_fin.application.service.operation_log_service")

# Map of tools to accounting ledgers accessed for audit transparency
TOOL_LEDGER_MAP: Dict[str, List[str]] = {
    "get_financial_health": ["GL Entry", "Account", "Company", "Fiscal Year"],
    "get_cashflow_forecast": ["GL Entry", "Sales Invoice", "Payment Entry", "Purchase Invoice"],
    "evaluate_risk_signal": ["Sales Invoice", "Purchase Invoice", "Payment Entry", "Customer", "Supplier"],
    "simulate_what_if": ["Sales Invoice", "GL Entry", "Payment Entry"],
    "match_financing_products": ["GL Entry", "Company", "Bank Account"],
    "calculate_repayment_schedule": ["Loan", "Payment Schedule", "Interest Rate Benchmark"]
}

TOOL_INTENT_MAP: Dict[str, str] = {
    "get_financial_health": "F001_FINANCIAL_HEALTH",
    "get_cashflow_forecast": "F002_CASHFLOW_FORECAST",
    "evaluate_risk_signal": "F003_RISK_SIGNAL",
    "simulate_what_if": "F004_WHAT_IF_STUDIO",
    "match_financing_products": "F005_FINANCING_COPILOT",
    "calculate_repayment_schedule": "F006_DEBT_REPAYMENT"
}


class OperationLogService(IOperationLogService):
    """
    Application Service managing the lifecycle of AI operational audit logs.
    """

    def __init__(self, log_repository: IOperationLogRepository):
        self.log_repository = log_repository

    def log_operation(
        self,
        session_id: str,
        user: UserPrincipal,
        prompt: str,
        reply: str,
        tool_called: Optional[str] = None,
        tool_inputs: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Dict[str, Any]] = None,
        latency_ms: int = 0,
        status: str = "SUCCESS",
        llm_provider: str = "unknown",
        model_name: Optional[str] = None,
    ) -> SandboxOperationLogEntry:
        log_id = f"op_{uuid.uuid4().hex[:12]}"

        # Infer intent and ledgers accessed
        intent = TOOL_INTENT_MAP.get(tool_called, "GENERAL_COPILOT_QA") if tool_called else "GENERAL_COPILOT_QA"
        ledgers = TOOL_LEDGER_MAP.get(tool_called, ["Frappe Bench Session", "Company"]) if tool_called else ["Frappe Bench Session"]

        # Build clean summary
        summary = reply[:240] + ("..." if len(reply) > 240 else "")

        entry = SandboxOperationLogEntry(
            log_id=log_id,
            environment="SANDBOX",
            user_principal=user.user_id,
            user_roles=user.roles or ["Accounts User"],
            company=user.company,
            session_id=session_id,
            prompt_query=prompt,
            agent_intent=intent,
            tool_called=tool_called,
            tool_inputs=tool_inputs or {},
            accounting_ledger_accessed=ledgers,
            execution_status=status,
            latency_ms=max(1, latency_ms),
            llm_provider=llm_provider,
            model_name=model_name or "gemini-flash-lite-latest",
            summary_output=summary
        )

        try:
            self.log_repository.append_log(entry)
        except Exception as e:
            _logger.error("Failed saving audit log entry %s: %s", log_id, e)

        return entry

    def get_recent_logs(
        self,
        company: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        try:
            entries = self.log_repository.query_logs(company=company, session_id=session_id, limit=limit)
            return [e.model_dump() for e in entries]
        except Exception as e:
            _logger.error("Error retrieving audit logs: %s", e)
            return []

    def clear_logs(self, company: Optional[str] = None) -> None:
        try:
            self.log_repository.clear_logs(company=company)
        except Exception as e:
            _logger.error("Error clearing audit logs: %s", e)

