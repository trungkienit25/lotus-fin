from typing import Any, Dict, Optional
try:
    import frappe
except ImportError:
    frappe = None

from lotus_fin.security.access import get_verified_company, CompanyAccessError
from lotus_fin.api.key_reports import extract_key_report_data


class ERPNextGateway:
    """
    Adapter gateway providing clean, secure access to ERPNext accounting reports and company records.
    Decouples domain use cases from direct Frappe framework globals.
    """

    @staticmethod
    def verify_company(company: Optional[str]) -> str:
        """Enforces INV-01/INV-02 company authorization check."""
        return get_verified_company(company)

    @staticmethod
    def fetch_report_data(
        report_key: str,
        filters: Dict[str, Any],
        company: str
    ) -> Dict[str, Any]:
        """
        Executes verified ERPNext query report via extract_key_report_data.
        Clears transient message logs to prevent unwanted UI modals.
        """
        res = extract_key_report_data(report_key=report_key, filters=filters, company=company)
        if frappe and hasattr(frappe, "message_log") and isinstance(frappe.message_log, list):
            frappe.message_log.clear()
        return res

    @staticmethod
    def get_company_currency(company: str) -> str:
        """Retrieves default currency for the company."""
        if frappe and hasattr(frappe, "db"):
            curr = frappe.db.get_value("Company", company, "default_currency")
            return str(curr) if curr else "VND"
        return "VND"

