from typing import Optional

try:
	import frappe
	from frappe import _
	from frappe.permissions import has_permission
	_PermissionError = frappe.PermissionError
	_ValidationError = frappe.ValidationError
except ImportError:
	frappe = None
	def _(text, *args, **kwargs):
		return text
	def has_permission(*args, **kwargs):
		return True
	class _PermissionError(Exception):
		pass
	class _ValidationError(Exception):
		pass


class CompanyAccessError(_PermissionError):
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
	:raises CompanyAccessError: If company does not exist or user lacks access.
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
		frappe.throw(_("FORBIDDEN"), exc=CompanyAccessError)

	# 3. Check read permission on Company document
	if not has_permission("Company", ptype="read", doc=target_company, user=active_user):
		frappe.throw(_("FORBIDDEN"), exc=CompanyAccessError)

	return target_company


def check_report_permission(report_name: str, user: Optional[str] = None) -> None:
	"""
	Verify that the user has permission to access the specified Report.

	PB-SEC-01: the previous primitive (`frappe.desk.query_report.has_permission`)
	only checks DocType-level read access on the Report document and ignores
	report-specific restrictions (Custom Role "allowed report" / report roles),
	so a revoked report stayed callable. The authoritative ERPNext semantics
	are `Report.is_permitted()`, and they must be evaluated FOR THE CHECKED
	USER: when the checked user differs from the ambient session user (e.g.
	Administrator authorizing on behalf of someone), the check runs under a
	scoped user context that is always restored.

	:param report_name: Name of the ERPNext/Frappe report (e.g., 'General Ledger').
	:param user: User to check permission for (defaults to current session user).
	:raises frappe.PermissionError: If report does not exist or user lacks access.
	"""
	if frappe is None:
		# Fail closed: report authorization cannot be evaluated outside Frappe.
		raise _PermissionError("FORBIDDEN")

	session_user = None
	if hasattr(frappe, "session") and frappe.session:
		session_user = getattr(frappe.session, "user", None)
	active_user = user or session_user
	if not active_user:
		# No checked user can be established — never authorize anonymously.
		raise _PermissionError("FORBIDDEN")

	if not frappe.db.exists("Report", report_name):
		frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

	report_doc = frappe.get_doc("Report", report_name)
	if not _report_permitted_for(report_doc, active_user, session_user):
		frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)


def _report_permitted_for(report_doc, active_user: str, session_user: Optional[str]) -> bool:
	"""PB-SEC-01: evaluate the authoritative report permission as the checked user."""
	if session_user == active_user:
		return bool(report_doc.is_permitted())
	frappe.set_user(active_user)
	try:
		return bool(report_doc.is_permitted())
	finally:
		frappe.set_user(session_user)


def get_company_accounting_currency(company: Optional[str]) -> Optional[str]:
    """
    AI003 foundation remediation (Bucket C): server-authoritative accounting
    currency for a company, read from Company.default_currency.

    Returns None when the currency cannot be determined — callers must fail
    closed (typed VALIDATION_ERROR), never relabel metrics in a client-chosen
    currency. No FX conversion is performed anywhere.
    """
    if frappe is None or not hasattr(frappe, "db") or not frappe.db:
        return None
    if not company or not str(company).strip():
        return None
    currency = frappe.db.get_value("Company", str(company).strip(), "default_currency")
    if currency is None or not str(currency).strip():
        return None
    return str(currency).strip()


AI002_PERMITTED_REPORTS = ("General Ledger", "Accounts Receivable", "Accounts Payable", "Trial Balance")# P0 Evidence DocType allowlist containing only the actual evidence types needed by AI002
AI002_EVIDENCE_DOCTYPE_ALLOWLIST = ("GL Entry", "Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry")


def check_ai002_report_permission(report_name: str, user: Optional[str] = None) -> None:
	"""
	Enforce compile-time allowlist of permitted reports for AI002 (CG-SEC-02).
	Fails closed with generic FORBIDDEN if report is outside allowlist or user lacks permission.
	"""
	if report_name not in AI002_PERMITTED_REPORTS:
		frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
	check_report_permission(report_name, user=user)


AI003_PERMITTED_REPORTS = ("Accounts Receivable", "Accounts Payable")


def check_ai003_report_permission(report_name: str, user: Optional[str] = None) -> None:
	"""
	Enforce compile-time allowlist of permitted reports for AI003 risk signals.
	Additive AI003 boundary following the AI002 allowlist pattern (CG-SEC-02):
	fails closed with generic FORBIDDEN when the report is outside the allowlist
	or the checked user lacks report permission.
	"""
	if report_name not in AI003_PERMITTED_REPORTS:
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise _PermissionError("FORBIDDEN")
	check_report_permission(report_name, user=user)


def verify_evidence_access(evidence_ref: str, user: Optional[str] = None, company: Optional[str] = None) -> bool:
	"""
	Re-authorize evidence access on every open/drilldown (CG-SEC-04).
	Format of evidence_ref: 'DocType:docname' (e.g. 'GL Entry:GLE-001' or 'Sales Invoice:ACC-SINV-2026-00001').
	Requirements (Fix C):
	- company is mandatory (reject None, empty)
	- format must be DocType:docname with colon
	- DocType must belong to explicit AI002_EVIDENCE_DOCTYPE_ALLOWLIST
	- Fails closed with generic FORBIDDEN if unauthorized, cross-company, or nonexistent.
	"""
	active_user = user or (frappe.session.user if frappe and hasattr(frappe, "session") else None)

	# 1. Company is mandatory
	if not company or not str(company).strip():
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise _PermissionError("FORBIDDEN")

	# 2. Ref validation (DocType:docname)
	if not evidence_ref or ":" not in evidence_ref:
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise _PermissionError("FORBIDDEN")

	parts = evidence_ref.split(":", 1)
	doctype = parts[0].strip()
	docname = parts[1].strip()

	if not doctype or not docname:
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise _PermissionError("FORBIDDEN")

	# 3. Allowlist validation
	if doctype not in AI002_EVIDENCE_DOCTYPE_ALLOWLIST:
		if frappe:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)
		raise _PermissionError("FORBIDDEN")

	if frappe and hasattr(frappe, "db") and frappe.db:
		if not frappe.db.exists(doctype, docname):
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

		if not has_permission(doctype, ptype="read", doc=docname, user=active_user):
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

		doc_company = frappe.db.get_value(doctype, docname, "company")
		if doc_company and doc_company != company:
			frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

	return True


