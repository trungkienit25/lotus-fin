from typing import Optional
import frappe
from frappe import _
from frappe.permissions import has_permission


class CompanyAccessError(frappe.PermissionError):
	"""Raised when a user attempts to access data for an unauthorized company."""
	pass


def get_verified_company(company: Optional[str] = None, user: Optional[str] = None) -> str:
	"""
	Verify server-side that the company exists and the user has permission to read it.
	
	Security SSOT Rules (INV-01, INV-02):
	- The `company` parameter received from client/caller is completely untrusted.
	- If `company` is not provided, defaults to user's default company or global default company.
	- Validates that the company exists in the database.
	- Checks that `user` has 'read' permission on the Company document.
	
	:param company: Requested company name (optional).
	:param user: User to check permission for (defaults to current session user).
	:return: Verified company name.
	:raises frappe.DoesNotExistError: If company does not exist.
	:raises CompanyAccessError: If user lacks permission for the company.
	"""
	active_user = user or frappe.session.user

	# 1. Resolve company candidate
	if company is not None and not str(company).strip():
		frappe.throw(
			_("Company name cannot be empty."),
			exc=frappe.ValidationError
		)

	target_company = company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
	
	if not target_company:
		frappe.throw(
			_("Company is required and no default company is configured."),
			exc=frappe.ValidationError
		)

	# 2. Check existence in DB
	if not frappe.db.exists("Company", target_company):
		frappe.throw(
			_("Company '{0}' does not exist.").format(target_company),
			exc=frappe.DoesNotExistError
		)

	# 3. Check read permission on Company document
	if not has_permission("Company", ptype="read", doc=target_company, user=active_user):
		frappe.throw(
			_("You do not have permission to access company '{0}'.").format(target_company),
			exc=CompanyAccessError
		)

	return target_company


def check_report_permission(report_name: str, user: Optional[str] = None) -> None:
	"""
	Verify that the user has permission to access the specified Report.
	
	:param report_name: Name of the ERPNext/Frappe report (e.g., 'General Ledger').
	:param user: User to check permission for (defaults to current session user).
	:raises frappe.PermissionError: If user lacks permission for the report.
	"""
	active_user = user or frappe.session.user

	if not frappe.db.exists("Report", report_name):
		frappe.throw(
			_("Report '{0}' does not exist.").format(report_name),
			exc=frappe.DoesNotExistError
		)

	report_doc = frappe.get_doc("Report", report_name)
	from frappe.desk.query_report import has_permission as report_has_perm

	if not report_has_perm(report_doc, user=active_user):
		frappe.throw(
			_("You do not have access to Report: {0}").format(report_name),
			exc=frappe.PermissionError
		)
