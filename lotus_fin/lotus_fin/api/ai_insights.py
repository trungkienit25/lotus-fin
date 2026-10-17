"""
Lotus Fin API - AI Insights & Financial Health Whitelisted Endpoints.
"""

import warnings
from typing import Any, Dict, Optional, Union
import frappe
from frappe import _
from frappe.permissions import has_permission
from lotus_fin.api.key_reports import extract_key_report_data
from lotus_fin.security.access import get_verified_company

from lotus_fin.api.events import (
    on_sales_invoice_submit,
    on_payment_entry_submit,
    generate_daily_cashflow_digest,
    evaluate_sme_financial_health,
)

from lotus_fin.api.cashflow_api import (
    get_ai002_cash_account_scope,
    get_ai002_cash_forecast,
    get_ai002_evidence,
)
from lotus_fin.api.copilot_api import (
    chat_copilot,
    get_chat_history,
    list_chat_sessions,
    reset_chat_session,
    get_operation_logs,
    export_operation_logs,
)

__all__ = [
    "on_sales_invoice_submit",
    "on_payment_entry_submit",
    "generate_daily_cashflow_digest",
    "evaluate_sme_financial_health",
    "predict_cashflow",
    "analyze_invoice_risk",
    "get_financial_snapshot",
    "get_ai002_cash_account_scope",
    "get_ai002_cash_forecast",
    "get_ai002_evidence",
    "get_risk_signal",
    "get_risk_signal_evidence",
    "chat_copilot",
    "get_chat_history",
    "list_chat_sessions",
    "reset_chat_session",
    "get_operation_logs",
    "export_operation_logs",
]



@frappe.whitelist()
def predict_cashflow(days_ahead: int = 30, company: Optional[str] = None) -> Dict[str, Any]:
    """[DEPRECATED] AR-AP naive proxy preserved for backward compatibility."""
    warnings.warn(
        "predict_cashflow using AR-AP difference is deprecated.",
        DeprecationWarning,
        stacklevel=2
    )
    verified_company = get_verified_company(company)
    ar_data = extract_key_report_data("accounts_receivable", company=verified_company)
    ap_data = extract_key_report_data("accounts_payable", company=verified_company)

    if ar_data.get("status") == "error":
        return {
            "status": "error", "deprecated": True, "company": verified_company,
            "warning": "AR-AP difference is deprecated as cashflow logic.",
            "source_error": "accounts_receivable", "message": f"Failed: {ar_data.get('message')}"
        }

    if ap_data.get("status") == "error":
        return {
            "status": "error", "deprecated": True, "company": verified_company,
            "warning": "AR-AP difference is deprecated as cashflow logic.",
            "source_error": "accounts_payable", "message": f"Failed: {ap_data.get('message')}"
        }

    ar_rows = [row for row in ar_data.get("data", []) if isinstance(row, dict)]
    ap_rows = [row for row in ap_data.get("data", []) if isinstance(row, dict)]
    total_receivable = sum([row.get("outstanding", 0.0) or 0.0 for row in ar_rows])
    total_payable = sum([row.get("outstanding", 0.0) or 0.0 for row in ap_rows])
    net_predicted_change = total_receivable - total_payable

    return {
        "status": "success", "deprecated": True, "company": verified_company,
        "warning": "DEPRECATED: AR-AP difference is an accrual proxy, not realized cashflow.",
        "days_ahead": int(days_ahead),
        "summary": {
            "predicted_inflow": total_receivable, "predicted_outflow": total_payable,
            "net_cash_change": net_predicted_change,
            "liquidity_risk": "LOW" if net_predicted_change >= 0 else "WARNING"
        },
        "recommendation": (
            "Dòng tiền dự kiến dương trong 30 ngày tới. Doanh nghiệp có thể duy trì kế hoạch chi tiêu bình thường."
            if net_predicted_change >= 0 else
            "Cảnh báo: Khoản phải trả lớn hơn khoản phải thu dự kiến. Khuyến nghị thúc đẩy thu hồi công nợ sớm."
        )
    }


@frappe.whitelist()
def analyze_invoice_risk(invoice_name: str) -> Dict[str, Any]:
    """Invoice risk assessment endpoint with company authorization."""
    if not frappe.db.exists("Sales Invoice", invoice_name):
        frappe.throw(_(f"Hóa đơn {invoice_name} không tồn tại."), exc=frappe.DoesNotExistError)

    doc = frappe.get_doc("Sales Invoice", invoice_name)
    if not has_permission("Sales Invoice", ptype="read", doc=doc, user=frappe.session.user):
        frappe.throw(
            _("You do not have permission to access Sales Invoice {0}.").format(invoice_name),
            exc=frappe.PermissionError
        )
    get_verified_company(doc.company)

    customer, amount = doc.customer, doc.grand_total
    past_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"customer": customer, "company": doc.company, "docstatus": 1, "name": ["!=", invoice_name]},
        fields=["name", "status", "outstanding_amount"]
    )
    unpaid_count = len([inv for inv in past_invoices if inv.status in ["Overdue", "Unpaid"]])
    risk_level = "LOW" if unpaid_count == 0 else ("MEDIUM" if unpaid_count <= 2 else "HIGH")

    return {
        "status": "success", "invoice": invoice_name, "company": doc.company,
        "customer": customer, "amount": amount, "risk_level": risk_level,
        "analysis": f"Khách hàng '{customer}' có {len(past_invoices)} hóa đơn lịch sử ({unpaid_count} chưa thanh toán). Rủi ro: {risk_level}."
    }


@frappe.whitelist(allow_guest=True)
def get_financial_snapshot(
    company: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    currency: Optional[str] = None,
    as_of: Optional[str] = None,
    correlation_id: Optional[str] = None,
    comparison: Optional[str] = None,
    include_explanation: Union[bool, int, str] = False
) -> Dict[str, Any]:
    """Whitelisted financial snapshot endpoint for AI-F001 Financial Health."""
    from lotus_fin.ai.financial_snapshot import build_financial_snapshot
    from lotus_fin.security.access import get_company_accounting_currency
    p_end = period_end or "2020-12-31"
    p_start = period_start or "2020-01-01"
    target_currency = currency or get_company_accounting_currency(company) or "USD"

    want_exp = False
    if isinstance(include_explanation, bool):
        want_exp = include_explanation
    elif isinstance(include_explanation, (int, float)):
        want_exp = bool(include_explanation)
    elif isinstance(include_explanation, str):
        want_exp = include_explanation.strip().lower() in ["1", "true", "yes"]

    def frappe_report_fetcher(report_key: str, filters: Dict[str, Any], comp: str):
        res = extract_key_report_data(report_key=report_key, filters=filters, company=comp)
        if hasattr(frappe, "message_log") and isinstance(frappe.message_log, list):
            frappe.message_log.clear()
        return res
    res = build_financial_snapshot(
        company=company, period_start=p_start, period_end=p_end, as_of=as_of,
        currency=target_currency, correlation_id=correlation_id, comparison=comparison,
        source_fetcher=frappe_report_fetcher, user=frappe.session.user, include_explanation=want_exp
    )
    if hasattr(frappe, "message_log") and isinstance(frappe.message_log, list):
        frappe.message_log.clear()
    return res

# ---------------------------------------------------------------------------
# AI003 Risk Signal Agent (contract V2.2, DEMO_ONLY) — additive API

# Server owns financial values, policy, baseline, reports, filters, currency,
# method and authorization; the client passes scope/date/signal only.
# ---------------------------------------------------------------------------

_AI003_REQUEST_KEYS = frozenset(
    {"cmd", "company", "signal_id", "as_of_date", "correlation_id", "include_explanation"}
)


def _ai003_bool(value) -> bool:
    return value if isinstance(value, bool) else str(value).strip().lower() in ("1", "true", "yes", "y")


def _clear_leaked_server_messages() -> None:
    """Caught frappe.throw() calls inside the typed authorization paths leave
    entries in frappe.message_log; if not cleared they travel as
    ``_server_messages`` and pop a client dialog ON TOP of the typed envelope.
    Same cleanup the AI002 endpoint applies. No financial behavior changes."""
    if hasattr(frappe, "message_log") and isinstance(frappe.message_log, list):
        frappe.message_log.clear()


@frappe.whitelist(allow_guest=True)
def get_risk_signal(
    company: Optional[str] = None,
    signal_id: Optional[str] = None,
    as_of_date: Optional[str] = None,
    correlation_id: Optional[str] = None,
    include_explanation: Union[bool, int, str] = False,
) -> Dict[str, Any]:
    """
    AI003 deterministic risk-signal evaluation (AR_OVERDUE_SPIKE | AP_DUE_CLUSTER).

    Fail-closed typed envelope (V2.2): first-failed-stage A1..A11, no financial
    payload on FORBIDDEN/VALIDATION_ERROR/SOURCE_ERROR, LLM explanation-only.
    """
    from lotus_fin.modules.f003_risk_signal.agent import explain_result, next_check_actions
    from lotus_fin.modules.f003_risk_signal.contracts import (
        ReasonCode,
        SignalId,
        SignalResult,
        Status,
        result_to_dict,
    )
    from lotus_fin.modules.f003_risk_signal.service import default_deps, evaluate_signal

    checked_user = getattr(frappe.session, "user", None)
    unknown = set((frappe.form_dict or {}).keys()) - _AI003_REQUEST_KEYS
    if unknown:
        return {
            "feature_id": "AI003",
            "status": "VALIDATION_ERROR",
            "reason_code": "INVALID_REQUEST",
            "correlation_id": correlation_id if isinstance(correlation_id, str) else None,
            "stage_trace": ("A1_AUTH", "A2_STRUCTURE"),
            "explanation": {"status": "NOT_REQUESTED", "text": None, "reason_code": None},
        }

    def _run() -> Dict[str, Any]:
        result = evaluate_signal(
            {
                "company": company,
                "signal_id": signal_id,
                "as_of_date": as_of_date,
                "correlation_id": correlation_id,
            },
            checked_user=checked_user,
            deps=default_deps(checked_user),
            include_explanation=_ai003_bool(include_explanation),
            explain=explain_result,
        )
        wire = result_to_dict(result, include_debug=False)
        wire["next_check_actions"] = next_check_actions(result.signal_id.value, result.status.value)
        return wire

    try:
        wire = _run()
        _clear_leaked_server_messages()
        return wire
    except Exception:
        # Unexpected failure: sanitized typed envelope, no internals on the wire;
        # the full traceback stays server-side for debugging.
        frappe.log_error(message=frappe.get_traceback(), title="AI003 get_risk_signal failed")
        _clear_leaked_server_messages()
        return result_to_dict(
            SignalResult(
                signal_id=SignalId.AR_OVERDUE_SPIKE,
                status=Status.SOURCE_ERROR,
                reason_code=ReasonCode.SOURCE_UNAVAILABLE,
                correlation_id=correlation_id if isinstance(correlation_id, str) else None,
            ),
            include_debug=False,
        )


@frappe.whitelist()
def get_risk_signal_evidence(
    evidence_ref: Optional[str] = None,
    company: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    AI003 authorized evidence replay (MATCH/RESTATED/UNAVAILABLE/FORBIDDEN).
    The ref is an opaque server-side record id, never an authorization token;
    authorization is rechecked on every access.
    """
    from lotus_fin.modules.f003_risk_signal.service import default_deps, get_evidence
    from lotus_fin.security.access import get_verified_company

    checked_user = getattr(frappe.session, "user", None)
    if not checked_user or checked_user == "Guest":
        return {"status": "FORBIDDEN", "payload": None}
    try:
        verified_company = get_verified_company(company, user=checked_user)
    except Exception:
        return {"status": "FORBIDDEN", "payload": None}

    deps = default_deps(checked_user)

    def replay_factory(record):
        def replay():
            if not deps.report_permission("Accounts Payable"):
                from lotus_fin.modules.f003_risk_signal.provenance import SourceFailure, Status, ReasonCode
                raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "report permission denied")
            snapshot = deps.ap_provider.fetch(verified_company, record.as_of_date)
            return {"report_key": snapshot.report_key, "source_hash": snapshot.source_hash}

        return replay

    result = get_evidence(
        evidence_ref or "",
        checked_user=checked_user,
        verified_company=verified_company,
        replay_factory=replay_factory,
        correlation_id=correlation_id,
    )
    _clear_leaked_server_messages()
    return {
        "status": result.outcome,
        "payload": dict(result.fresh_payload) if result.fresh_payload else None,
    }

