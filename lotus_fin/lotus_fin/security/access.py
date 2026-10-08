"""
Security Access Control Facade.

Delegates authorization, company verification, and report/evidence access
to FrappeAccessGateway and domain IPermissionPolicy while preserving
100% backward-compatible function signatures and global constants.
"""

from typing import Optional

from lotus_fin.domain.policy.permission_policy import IPermissionPolicy, ModuleSecurityPolicy
from lotus_fin.infrastructure.security.frappe_access_gateway import (
    FrappeAccessGateway,
    CompanyAccessError,
    MODULE_SECURITY_REGISTRY,
    _PermissionError,
    _ValidationError,
)

try:
    import frappe
    from frappe.permissions import has_permission
except ImportError:
    from unittest.mock import MagicMock
    frappe = MagicMock()
    def has_permission(*args, **kwargs):
        return True


# Re-export compile-time tuples for backward compatibility (derived from MODULE_SECURITY_REGISTRY)
AI002_PERMITTED_REPORTS = tuple(MODULE_SECURITY_REGISTRY["f002"].permitted_reports)
AI002_EVIDENCE_DOCTYPE_ALLOWLIST = tuple(MODULE_SECURITY_REGISTRY["f002"].permitted_evidence_doctypes)
AI003_PERMITTED_REPORTS = tuple(MODULE_SECURITY_REGISTRY["f003"].permitted_reports)

# Gateway instance
_default_gateway = FrappeAccessGateway()


def get_verified_company(company: Optional[str] = None, user: Optional[str] = None) -> str:
    """
    Verify server-side that the company exists and the user has permission to read it.
    Delegates to FrappeAccessGateway.
    """
    return _default_gateway.verify_company(company=company, user=user)


def check_report_permission(report_name: str, user: Optional[str] = None, module_id: Optional[str] = None) -> None:
    """
    Verify that the user has permission to access the specified Report.
    Delegates to FrappeAccessGateway.
    """
    _default_gateway.check_report_permission(report_name=report_name, user=user, module_id=module_id)


def check_ai002_report_permission(report_name: str, user: Optional[str] = None) -> None:
    """
    Enforce allowlist of permitted reports for AI002 / F002 Cashflow.
    """
    _default_gateway.check_report_permission(report_name=report_name, user=user, module_id="f002")


def check_ai003_report_permission(report_name: str, user: Optional[str] = None) -> None:
    """
    Enforce allowlist of permitted reports for AI003 / F003 Risk Signals.
    """
    _default_gateway.check_report_permission(report_name=report_name, user=user, module_id="f003")


def verify_evidence_access(
    evidence_ref: str,
    user: Optional[str] = None,
    company: Optional[str] = None,
    module_id: str = "f002"
) -> bool:
    """
    Re-authorize evidence access on every open/drilldown (CG-SEC-04).
    Delegates to FrappeAccessGateway.
    """
    return _default_gateway.verify_evidence_access(
        evidence_ref=evidence_ref,
        company=company,
        user=user,
        module_id=module_id
    )


def get_company_accounting_currency(company: Optional[str]) -> Optional[str]:
    """
    Retrieve server-authoritative accounting currency for a company.
    Delegates to FrappeAccessGateway.
    """
    return _default_gateway.get_company_accounting_currency(company=company)


__all__ = [
    "CompanyAccessError",
    "get_verified_company",
    "check_report_permission",
    "check_ai002_report_permission",
    "check_ai003_report_permission",
    "verify_evidence_access",
    "get_company_accounting_currency",
    "AI002_PERMITTED_REPORTS",
    "AI002_EVIDENCE_DOCTYPE_ALLOWLIST",
    "AI003_PERMITTED_REPORTS",
    "IPermissionPolicy",
    "ModuleSecurityPolicy",
    "FrappeAccessGateway",
]
