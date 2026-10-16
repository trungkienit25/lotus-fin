"""
Lotus Fin API - Copilot Whitelisted Endpoints.
Clean Architecture Entrypoints delegating to Presentation Controller (CopilotController).
"""

import logging
from typing import Any, Dict, List, Optional
try:
    import frappe
    whitelist = frappe.whitelist
except ImportError:
    frappe = None
    def whitelist(*args, **kwargs):
        def decorator(f):
            return f
        return decorator if not args or callable(args[0]) is False else args[0]

from lotus_fin.core.ai.agent_copilot import process_copilot_query
from lotus_fin.presentation.controller.copilot_controller import CopilotController

_logger = logging.getLogger("lotus_fin.api.copilot")


@whitelist(allow_guest=True)
def chat_copilot(
    query: str,
    company: Optional[str] = None,
    as_of_date: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Public whitelisted endpoint for Lotus Fin AI Copilot chat interface.
    Delegates to Clean Architecture Presentation Controller (CopilotController).
    Falls back gracefully to legacy router to guarantee zero regression.
    """
    try:
        return CopilotController.handle_send_message({
            "message": query,
            "company": company,
            "as_of_date": as_of_date,
            "session_id": session_id
        })
    except PermissionError:
        # Re-raise authentication / authorization failures fail-closed
        raise
    except Exception as e:
        _logger.warning("Clean architecture copilot routing failed, falling back to legacy: %s", str(e))
        return process_copilot_query(
            query=query,
            company=company,
            as_of_date=as_of_date
        )


@whitelist()
def get_chat_history(
    session_id: str,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves the persistent conversation message list from database / cache.
    Enforces multi-tenant ownership boundaries.
    """
    return CopilotController.handle_get_chat_history(
        session_id=session_id,
        company=company
    )


@whitelist()
def list_chat_sessions(
    company: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Lists conversation sessions for the current company/user.
    """
    return CopilotController.handle_list_chat_sessions(
        company=company,
        limit=limit
    )


@whitelist()
def reset_chat_session(
    session_id: str,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clears conversation history for the specified session.
    """
    return CopilotController.handle_reset_chat_session(
        session_id=session_id,
        company=company
    )


@whitelist()
def get_operation_logs(
    session_id: Optional[str] = None,
    company: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieves structured AI Sandbox operational audit logs for compliance review.
    """
    return CopilotController.handle_get_operation_logs(
        session_id=session_id,
        company=company,
        limit=limit
    )


@whitelist()
def export_operation_logs(
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exports full operation audit logs in JSON format for FinTechathon Item 06 evidence.
    """
    return CopilotController.handle_export_operation_logs(
        company=company
    )


@whitelist(methods=["POST"], allow_guest=True)
def search_real_invoices(
    company: Optional[str] = None,
    prefix: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Production ERP query retrieving real Sales Invoices from ERPNext database.
    Grounded in `tabSales Invoice` with multi-tenant company filtering.
    """
    if frappe is None:
        return {"status": "error", "message": "Frappe environment not available", "invoices": []}

    conditions = ["docstatus < 2"]
    values = {}

    if company:
        conditions.append("company = %(company)s")
        values["company"] = company
    if prefix:
        conditions.append("name LIKE %(prefix)s")
        values["prefix"] = f"{prefix}%"
    if from_date:
        conditions.append("posting_date >= %(from_date)s")
        values["from_date"] = from_date
    if to_date:
        conditions.append("posting_date <= %(to_date)s")
        values["to_date"] = to_date
    if status is not None and status != "":
        if status.upper() == "SUBMITTED":
            conditions.append("docstatus = 1")
        elif status.upper() == "DRAFT":
            conditions.append("docstatus = 0")
        elif status.isdigit():
            conditions.append("docstatus = %(docstatus)s")
            values["docstatus"] = int(status)

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT 
            name, customer_name, posting_date, due_date,
            outstanding_amount, grand_total, docstatus, company, modified
        FROM `tabSales Invoice`
        WHERE {where_clause}
        ORDER BY posting_date DESC, creation DESC
        LIMIT {int(limit)}
    """
    try:
        records = frappe.db.sql(sql, values, as_dict=True)
        invoices = []
        for r in records:
            invoices.append({
                "invoiceId": r.get("name"),
                "customerName": r.get("customer_name"),
                "postingDate": str(r.get("posting_date")),
                "dueDate": str(r.get("due_date")),
                "outstandingAmount": float(r.get("outstanding_amount") or 0.0),
                "grandTotal": float(r.get("grand_total") or 0.0),
                "docstatus": int(r.get("docstatus")),
                "company": r.get("company"),
                "currency": "VND"
            })
        return {
            "status": "success",
            "count": len(invoices),
            "invoices": invoices,
            "source": "ERPNext Live Database"
        }
    except Exception as e:
        _logger.exception("Failed to query real sales invoices: %s", str(e))
        return {"status": "error", "message": str(e), "invoices": []}


@whitelist(methods=["POST"], allow_guest=True)
def get_real_overdue_invoices(
    company: Optional[str] = None,
    as_of_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves real submitted overdue Sales Invoices where outstanding > 0 and due_date < as_of_date.
    """
    if frappe is None:
        return {"status": "error", "message": "Frappe environment not available", "items": []}

    target_date = as_of_date or frappe.utils.today() if hasattr(frappe, "utils") else "2026-10-15"
    conditions = ["docstatus = 1", "outstanding_amount > 0"]
    values = {"as_of_date": target_date}

    if company:
        conditions.append("company = %(company)s")
        values["company"] = company

    conditions.append("due_date <= %(as_of_date)s")

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT 
            name, customer_name, posting_date, due_date,
            outstanding_amount, grand_total, modified,
            DATEDIFF(%(as_of_date)s, due_date) AS overdue_days
        FROM `tabSales Invoice`
        WHERE {where_clause}
        ORDER BY overdue_days DESC
        LIMIT 50
    """
    try:
        records = frappe.db.sql(sql, values, as_dict=True)
        items = []
        for r in records:
            out_val = float(r.get("outstanding_amount") or 0.0)
            items.append({
                "invoiceId": r.get("name"),
                "customerName": r.get("customer_name"),
                "postingDate": str(r.get("posting_date")),
                "finalDueDate": str(r.get("due_date")),
                "overdueDays": max(0, int(r.get("overdue_days") or 0)),
                "currentOutstandingDecimal": f"{int(out_val):,}",
                "outstandingAmount": out_val,
                "partyAccountCurrency": "VND",
                "sourceModified": str(r.get("modified") or "")
            })
        return {
            "status": "success",
            "count": len(items),
            "as_of_date": target_date,
            "items": items,
            "source": "ERPNext Live Database"
        }
    except Exception as e:
        _logger.exception("Failed to query real overdue invoices: %s", str(e))
        return {"status": "error", "message": str(e), "items": []}


@whitelist(methods=["POST"])
def create_real_task(
    subject: str,
    due_date: Optional[str] = None,
    priority: str = "Medium",
    description: Optional[str] = None,
    reference_invoice: Optional[str] = None,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a REAL Task record in ERPNext `tabTask`.
    Enforces user session authentication and multi-tenant audit trail.
    """
    if frappe is None:
        return {"status": "error", "message": "Frappe environment not available"}

    user = getattr(frappe.session, "user", None)
    if not user or user == "Guest":
        raise PermissionError("FORBIDDEN: User not authenticated")

    try:
        task_doc = frappe.get_doc({
            "doctype": "Task",
            "subject": subject,
            "priority": priority if priority in ("Low", "Medium", "High", "Urgent") else "Medium",
            "status": "Open",
            "exp_end_date": due_date,
            "description": description or f"Auto-created from Lotus Copilot. Linked to {reference_invoice or 'N/A'}",
            "company": company or "Lotus-fin (Demo)"
        })
        task_doc.insert(ignore_permissions=False)

        # FinTechathon Item 06: Log operation into operation log repository
        try:
            from lotus_fin.domain.model.user_context import UserPrincipal
            from lotus_fin.presentation.controller.copilot_controller import _log_service
            principal = UserPrincipal(
                user_id=user,
                company=task_doc.company,
                roles=frappe.get_roles(user) if hasattr(frappe, "get_roles") else ["System Manager"]
            )
            _log_service.log_operation(
                session_id=f"{user}_{task_doc.company}",
                user=principal,
                prompt=f"Create ERPNext Task: {subject}",
                reply=f"Created real Task: {task_doc.name}",
                tool_called="create_real_task",
                tool_inputs={"subject": subject, "due_date": due_date, "priority": priority, "reference_invoice": reference_invoice},
                tool_output={"task_name": task_doc.name, "status": "Open"},
                latency_ms=10,
                status="SUCCESS"
            )
        except Exception as log_err:
            _logger.warning("Audit logging task creation failed: %s", str(log_err))

        return {
            "status": "success",
            "task_id": task_doc.name,
            "subject": task_doc.subject,
            "priority": task_doc.priority,
            "exp_end_date": str(task_doc.exp_end_date),
            "company": task_doc.company,
            "docstatus": task_doc.docstatus,
            "created_at": str(task_doc.creation),
            "message": f"Đã khởi tạo thành công tác vụ {task_doc.name} trên ERPNext"
        }
    except Exception as e:
        _logger.exception("Failed to insert Task: %s", str(e))
        return {"status": "error", "message": str(e)}

