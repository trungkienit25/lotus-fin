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


AI002_PERMITTED_REPORTS = ("General Ledger", "Accounts Receivable", "Accounts Payable", "Trial Balance")

AI002_EVIDENCE_DOCTYPE_ALLOWLIST = ("GL Entry", "Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry")


def check_ai002_report_permission(report_name: str, user: Optional[str] = None) -> None:
	"""Enforce compile-time allowlist of permitted reports for AI002 (CG-SEC-02)."""
	if report_name not in AI002_PERMITTED_REPORTS:
		frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
	check_report_permission(report_name, user=user)


def verify_evidence_access(evidence_ref: str, user: Optional[str] = None, company: Optional[str] = None) -> bool:
	"""
	Re-authorize evidence access on every open/drilldown (CG-SEC-04).
	Format of evidence_ref: 'DocType:docname'.
	"""
	active_user = user or (frappe.session.user if frappe and hasattr(frappe, "session") else None)

	if not company or not str(company).strip():
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise frappe.PermissionError("FORBIDDEN")

	if not evidence_ref or ":" not in evidence_ref:
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise frappe.PermissionError("FORBIDDEN")

	parts = evidence_ref.split(":", 1)
	doctype = parts[0].strip()
	docname = parts[1].strip()

	if not doctype or not docname or doctype not in AI002_EVIDENCE_DOCTYPE_ALLOWLIST:
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise frappe.PermissionError("FORBIDDEN")

	if frappe and hasattr(frappe, "db") and frappe.db:
		if not frappe.db.exists(doctype, docname):
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

		if not has_permission(doctype, ptype="read", doc=docname, user=active_user):
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

		doc_company = frappe.db.get_value(doctype, docname, "company")
		if doc_company and doc_company != company:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

	return True

