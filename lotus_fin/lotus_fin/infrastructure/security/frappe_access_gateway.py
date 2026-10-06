"""
Infrastructure implementation of IPermissionPolicy via Frappe & ERPNext.
"""

from typing import Any, Callable, Dict, Optional, Set
import sys

try:
    import frappe
    from frappe import _
    from frappe.permissions import has_permission
    _PermissionError = frappe.PermissionError
    _ValidationError = frappe.ValidationError
except ImportError:
    frappe = None
    def _(text, *args, **kwargs): return text
    def has_permission(*args, **kwargs): return True
    class _PermissionError(Exception): pass
    class _ValidationError(Exception): pass

from lotus_fin.domain.policy.permission_policy import IPermissionPolicy, ModuleSecurityPolicy


class CompanyAccessError(_PermissionError):
    """Raised when a user attempts to access data for an unauthorized company."""
    pass


# Dynamic Policy Registry for extensible modules (OCP)
MODULE_SECURITY_REGISTRY: Dict[str, ModuleSecurityPolicy] = {
    "f001": ModuleSecurityPolicy(
        module_id="f001",
        permitted_reports={"General Ledger", "Accounts Receivable", "Accounts Payable", "Trial Balance"},
        permitted_evidence_doctypes={"GL Entry", "Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"}
    ),
    "f002": ModuleSecurityPolicy(
        module_id="f002",
        permitted_reports={"General Ledger", "Accounts Receivable", "Accounts Payable", "Trial Balance"},
        permitted_evidence_doctypes={"GL Entry", "Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry"}
    ),
    "f003": ModuleSecurityPolicy(
        module_id="f003",
        permitted_reports={"Accounts Receivable", "Accounts Payable"},
        permitted_evidence_doctypes={"Sales Invoice", "Purchase Invoice", "Payment Entry"}
    ),
    "f004": ModuleSecurityPolicy(
        module_id="f004",
        permitted_reports={"General Ledger", "Accounts Receivable", "Accounts Payable"},
        permitted_evidence_doctypes={"GL Entry", "Sales Invoice", "Purchase Invoice"}
    ),
    "f005": ModuleSecurityPolicy(
        module_id="f005",
        permitted_reports={"General Ledger", "Trial Balance"},
        permitted_evidence_doctypes=set()
    ),
    "f006": ModuleSecurityPolicy(
        module_id="f006",
        permitted_reports=set(),
        permitted_evidence_doctypes=set()
    )
}


class FrappeAccessGateway(IPermissionPolicy):
    """Concrete implementation of IPermissionPolicy using Frappe Framework."""

    def __init__(
        self,
        registry: Optional[Dict[str, ModuleSecurityPolicy]] = None,
        frappe_provider: Optional[Callable[[], Any]] = None,
        has_permission_provider: Optional[Callable[..., bool]] = None,
    ):
        self.registry = registry or MODULE_SECURITY_REGISTRY
        self._frappe_provider = frappe_provider
        self._has_permission_provider = has_permission_provider

    def _get_frappe(self):
        if self._frappe_provider:
            return self._frappe_provider()
        return getattr(sys.modules.get("lotus_fin.security.access"), "frappe", frappe)

    def _get_has_permission(self):
        if self._has_permission_provider:
            return self._has_permission_provider()
        access_mod = sys.modules.get("lotus_fin.security.access")
        if access_mod and hasattr(access_mod, "has_permission"):
            return access_mod.has_permission
        return has_permission

    def verify_company(self, company: Optional[str] = None, user: Optional[str] = None) -> str:
        current_frappe = self._get_frappe()
        current_has_permission = self._get_has_permission()

        if current_frappe is None:
            if company is not None and not str(company).strip():
                raise _ValidationError("Company name cannot be empty.")
            return str(company) if company else "Test Company"

        active_user = user or (current_frappe.session.user if hasattr(current_frappe, "session") and current_frappe.session else None)

        if company is not None and not str(company).strip():
            current_frappe.throw(_("Company name cannot be empty."), exc=current_frappe.ValidationError)

        target_company = (
            company
            or (current_frappe.defaults.get_user_default("Company") if hasattr(current_frappe, "defaults") and current_frappe.defaults else None)
            or (current_frappe.db.get_single_value("Global Defaults", "default_company") if hasattr(current_frappe, "db") and current_frappe.db else None)
        )

        if not target_company:
            current_frappe.throw(_("Company is required and no default company is configured."), exc=current_frappe.ValidationError)

        if not current_frappe.db.exists("Company", target_company):
            current_frappe.throw(_("FORBIDDEN"), exc=CompanyAccessError)

        if not current_has_permission("Company", ptype="read", doc=target_company, user=active_user):
            current_frappe.throw(_("FORBIDDEN"), exc=CompanyAccessError)

        return target_company

    def check_report_permission(
        self,
        report_name: str,
        user: Optional[str] = None,
        module_id: Optional[str] = None
    ) -> None:
        current_frappe = self._get_frappe()
        if current_frappe is None:
            raise _PermissionError("FORBIDDEN")

        # 1. Enforce Module Allowlist Policy if module_id specified
        if module_id and module_id in self.registry:
            policy = self.registry[module_id]
            if report_name not in policy.permitted_reports:
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)

        # 2. Enforce ERPNext RBAC Check
        session_user = getattr(current_frappe.session, "user", None) if hasattr(current_frappe, "session") and current_frappe.session else None
        active_user = user or session_user
        if not active_user:
            raise _PermissionError("FORBIDDEN")

        if not current_frappe.db.exists("Report", report_name):
            current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)

        report_doc = current_frappe.get_doc("Report", report_name)
        if not self._report_permitted_for(report_doc, active_user, session_user, current_frappe):
            current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)

    def _report_permitted_for(self, report_doc, active_user: str, session_user: Optional[str], current_frappe) -> bool:
        if session_user == active_user:
            return bool(report_doc.is_permitted())
        current_frappe.set_user(active_user)
        try:
            return bool(report_doc.is_permitted())
        finally:
            current_frappe.set_user(session_user)

    def verify_evidence_access(
        self,
        evidence_ref: str,
        company: Optional[str] = None,
        user: Optional[str] = None,
        module_id: str = "f002"
    ) -> bool:
        current_frappe = self._get_frappe()
        current_has_permission = self._get_has_permission()

        active_user = user or (current_frappe.session.user if current_frappe and hasattr(current_frappe, "session") else None)

        if not company or not str(company).strip():
            if current_frappe:
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)
            raise _PermissionError("FORBIDDEN")

        if not evidence_ref or ":" not in evidence_ref:
            if current_frappe:
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)
            raise _PermissionError("FORBIDDEN")

        parts = evidence_ref.split(":", 1)
        doctype = parts[0].strip()
        docname = parts[1].strip()

        if not doctype or not docname:
            if current_frappe:
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)
            raise _PermissionError("FORBIDDEN")

        # Check Module Allowlist Policy
        policy = self.registry.get(module_id) or self.registry["f002"]
        if doctype not in policy.permitted_evidence_doctypes:
            if current_frappe:
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)
            raise _PermissionError("FORBIDDEN")

        if current_frappe and hasattr(current_frappe, "db") and current_frappe.db:
            if not current_frappe.db.exists(doctype, docname):
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)

            if not current_has_permission(doctype, ptype="read", doc=docname, user=active_user):
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)

            doc_company = current_frappe.db.get_value(doctype, docname, "company")
            if doc_company and doc_company != company:
                current_frappe.throw(_("FORBIDDEN"), exc=current_frappe.PermissionError)

        return True

    def get_company_accounting_currency(self, company: Optional[str]) -> Optional[str]:
        current_frappe = self._get_frappe()
        if current_frappe is None or not hasattr(current_frappe, "db") or not current_frappe.db:
            return None
        if not company or not str(company).strip():
            return None
        currency = current_frappe.db.get_value("Company", str(company).strip(), "default_currency")
        if currency is None or not str(currency).strip():
            return None
        return str(currency).strip()
