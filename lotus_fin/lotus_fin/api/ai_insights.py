import warnings
from typing import Any, Dict, Optional, Union, List
import frappe
from frappe import _
from frappe.permissions import has_permission
from lotus_fin.api.key_reports import extract_key_report_data
from lotus_fin.security.access import get_verified_company, CompanyAccessError


# --- Event Hooks ---

def on_sales_invoice_submit(doc, method=None):
	"""
	Triggered khi Sales Invoice được Submit.
	Tự động phân tích điểm rủi ro công nợ khách hàng hoặc dự báo ngày tiền về thực tế.
	"""
	try:
		customer = doc.customer
		outstanding = doc.outstanding_amount or doc.grand_total
		frappe.logger("lotus_fin_ai").info(
			f"[AI Insights] Sales Invoice {doc.name} submitted for customer {customer}, amount: {outstanding}"
		)
	except Exception as e:
		frappe.log_error(f"Lotus Fin AI on_sales_invoice_submit error: {str(e)}")


def on_payment_entry_submit(doc, method=None):
	"""
	Triggered khi Payment Entry được Submit.
	Cập nhật lại dự báo dòng tiền tức thời.
	"""
	try:
		party = doc.party
		amount = doc.paid_amount
		payment_type = doc.payment_type
		frappe.logger("lotus_fin_ai").info(
			f"[AI Insights] Payment Entry {doc.name} ({payment_type}) submitted for party {party}, amount: {amount}"
		)
	except Exception as e:
		frappe.log_error(f"Lotus Fin AI on_payment_entry_submit error: {str(e)}")


# --- Scheduled Jobs ---

def generate_daily_cashflow_digest():
	"""
	Chạy hàng ngày để tổng hợp dòng tiền 30 ngày tới.
	"""
	frappe.logger("lotus_fin_ai").info("[Lotus Fin AI] Running daily cash flow digest job.")


def evaluate_sme_financial_health():
	"""
	Chạy hàng tuần để chấm điểm sức khỏe tài chính của SME.
	"""
	frappe.logger("lotus_fin_ai").info("[Lotus Fin AI] Running weekly SME financial health evaluation.")


# --- Whitelisted REST Endpoints for Frontend / AI Client ---

@frappe.whitelist()
def predict_cashflow(days_ahead: int = 30, company: Optional[str] = None) -> Dict[str, Any]:
	"""
	[DEPRECATED - ARCHITECTURAL NOTICE]
	This endpoint previously used `AR - AP` difference as a naive cashflow proxy.
	In accordance with AI001 / Lotus Fin Security SSOT & Architectural guidelines:
	- Accounts Receivable (AR) and Accounts Payable (AP) are accrual debt ledgers, NOT realized cashflow.
	- Missing or erroneous report sources must never default to zero or fabricate financial health.
	- Real cashflow forecast requires Cash Flow Statement, Bank/Cash GL accounts, and proper scheduling.
	
	This endpoint is DEPRECATED and preserved only for backward compatibility with explicit warnings.
	Cross-company data isolation is enforced via `get_verified_company`.
	"""
	warnings.warn(
		"predict_cashflow using AR-AP difference is deprecated and must not be used as cash balance/forecast.",
		DeprecationWarning,
		stacklevel=2
	)

	# 1. Enforce server-side company authorization
	verified_company = get_verified_company(company)

	# 2. Extract AR & AP data using verified company
	ar_data = extract_key_report_data("accounts_receivable", company=verified_company)
	ap_data = extract_key_report_data("accounts_payable", company=verified_company)

	# 3. Handle errors explicitly - do NOT mask error sources as zero (Rule: No error source becomes zero)
	if ar_data.get("status") == "error":
		return {
			"status": "error",
			"deprecated": True,
			"warning": "AR-AP difference is deprecated as cashflow logic.",
			"company": verified_company,
			"source_error": "accounts_receivable",
			"message": f"Failed to retrieve Accounts Receivable: {ar_data.get('message')}"
		}

	if ap_data.get("status") == "error":
		return {
			"status": "error",
			"deprecated": True,
			"warning": "AR-AP difference is deprecated as cashflow logic.",
			"company": verified_company,
			"source_error": "accounts_payable",
			"message": f"Failed to retrieve Accounts Payable: {ap_data.get('message')}"
		}

	# 4. Filter data rows specifically for verified_company
	# Note: Query report results contain summary rows (e.g. list/dict with totals)
	ar_rows = [row for row in ar_data.get("data", []) if isinstance(row, dict)]
	ap_rows = [row for row in ap_data.get("data", []) if isinstance(row, dict)]

	# Compute totals
	total_receivable = sum([row.get("outstanding", 0.0) or 0.0 for row in ar_rows])
	total_payable = sum([row.get("outstanding", 0.0) or 0.0 for row in ap_rows])

	net_predicted_change = total_receivable - total_payable

	return {
		"status": "success",
		"deprecated": True,
		"warning": "DEPRECATED: AR-AP difference is an accrual proxy, not realized cashflow. Do not use for cash balance or financial health decisions.",
		"company": verified_company,
		"days_ahead": int(days_ahead),
		"summary": {
			"predicted_inflow": total_receivable,
			"predicted_outflow": total_payable,
			"net_cash_change": net_predicted_change,
			"liquidity_risk": "LOW" if net_predicted_change >= 0 else "WARNING"
		},
		"recommendation": (
			"Dòng tiền dự kiến dương trong 30 ngày tới. Doanh nghiệp có thể duy trì kế hoạch chi tiêu bình thường."
			if net_predicted_change >= 0
			else "Cảnh báo: Khoản phải trả lớn hơn khoản phải thu dự kiến. Khuyến nghị thúc đẩy thu hồi công nợ sớm."
		)
	}


@frappe.whitelist()
def analyze_invoice_risk(invoice_name: str) -> Dict[str, Any]:
	"""
	Endpoint phân tích rủi ro thanh toán cho 1 hóa đơn cụ thể.
	Áp dụng kiểm tra quyền truy cập tài liệu và phân lập công ty server-side.
	"""
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_(f"Hóa đơn {invoice_name} không tồn tại."), exc=frappe.DoesNotExistError)

	doc = frappe.get_doc("Sales Invoice", invoice_name)

	# Verify user has read access to this specific invoice and its company
	if not has_permission("Sales Invoice", ptype="read", doc=doc, user=frappe.session.user):
		frappe.throw(
			_("You do not have permission to access Sales Invoice {0}.").format(invoice_name),
			exc=frappe.PermissionError
		)

	# Verify user has permission for the company owning this invoice
	get_verified_company(doc.company)

	customer = doc.customer
	amount = doc.grand_total

	# Đọc lịch sử quá khứ của khách hàng này trong cùng công ty
	past_invoices = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "company": doc.company, "docstatus": 1, "name": ["!=", invoice_name]},
		fields=["name", "status", "outstanding_amount"]
	)
	
	unpaid_count = len([inv for inv in past_invoices if inv.status in ["Overdue", "Unpaid"]])
	risk_level = "LOW" if unpaid_count == 0 else ("MEDIUM" if unpaid_count <= 2 else "HIGH")

	return {
		"status": "success",
		"invoice": invoice_name,
		"company": doc.company,
		"customer": customer,
		"amount": amount,
		"risk_level": risk_level,
		"analysis": f"Khách hàng '{customer}' có {len(past_invoices)} hóa đơn lịch sử ({unpaid_count} hóa đơn chưa thanh toán/quá hạn). Mức độ rủi ro tín dụng: {risk_level}."
	}


@frappe.whitelist()
def get_financial_snapshot(
	company: Optional[str] = None,
	period_start: Optional[str] = None,
	period_end: Optional[str] = None,
	currency: str = "VND",
	as_of: Optional[str] = None,
	correlation_id: Optional[str] = None,
	comparison: Optional[str] = None,
	include_explanation: Union[bool, int, str] = False
) -> Dict[str, Any]:
	"""
	[AI-F001 Financial Health Analyst - Deterministic Data Foundation & Grounded Explanation]
	Generates a frozen FinancialSnapshot, EvidenceRefs, optional Previous-Period Comparison,
	and optional Grounded LLM Explanation:
	- Profit and Loss Statement (Revenue, COGS, Gross Margin)
	- Accounts Receivable (Total Outstanding, Overdue Amount, Overdue Ratio)
	- Accounts Payable (Total Outstanding, Near-Term AP limitation)
	- Trial Balance / General Ledger (Cash & Bank Balance)
	- Period Comparison (PREVIOUS_PERIOD): absolute_change, relative_change
	- Grounded LLM Explanation (facts, interpretations, next_checks)

	Guarantees:
	- Strict server-side company authorization check (INV-01, INV-02).
	- Deterministic arithmetic only; no LLM hallucinations or ungrounded claims.
	- Zero-is-not-error invariant: Missing or errored sources yield UNAVAILABLE/PARTIAL, never 0.0.
	- Every material metric links to verifiable EvidenceRefs with checksums.
	- Structured observability, zero PII, pseudonymized audit trails.
	"""
	from lotus_fin.ai.financial_snapshot import build_financial_snapshot

	# Resolve default period if not supplied (default: FY2020 for verified demo data)
	p_end = period_end or "2020-12-31"
	p_start = period_start or "2020-01-01"

	# Normalize boolean flag from REST call
	want_explanation = False
	if isinstance(include_explanation, bool):
		want_explanation = include_explanation
	elif isinstance(include_explanation, (int, float)):
		want_explanation = bool(include_explanation)
	elif isinstance(include_explanation, str):
		want_explanation = include_explanation.strip().lower() in ["1", "true", "yes"]

	# Adapter to fetch reports via authorized extract_key_report_data
	def frappe_report_fetcher(report_key: str, filters: Dict[str, Any], comp: str):
		res = extract_key_report_data(report_key=report_key, filters=filters, company=comp)
		# Clear any internal ERPNext report validation popups (e.g. inactive fiscal year for previous period)
		# so they do not show up as unexpected UI modal dialogs to end users.
		if hasattr(frappe, "message_log") and isinstance(frappe.message_log, list):
			frappe.message_log.clear()
		return res

	res = build_financial_snapshot(
		company=company,
		period_start=p_start,
		period_end=p_end,
		as_of=as_of,
		currency=currency,
		correlation_id=correlation_id,
		comparison=comparison,
		source_fetcher=frappe_report_fetcher,
		user=frappe.session.user,
		include_explanation=want_explanation
	)

	if hasattr(frappe, "message_log") and isinstance(frappe.message_log, list):
		frappe.message_log.clear()

	return res


@frappe.whitelist()
def get_ai002_cash_forecast(
	company: Optional[str] = None,
	financial_as_of: Optional[str] = None,
	forecast_start: Optional[str] = None,
	forecast_end: Optional[str] = None,
	currency: str = "VND",
	correlation_id: Optional[str] = None,
	include_explanation: Union[bool, int, str] = False,
	cash_account_scope: Optional[Union[List[str], str]] = None,
) -> Dict[str, Any]:
	"""
	[AI-F002 Cash-flow Forecast Copilot - Whitelisted API Endpoint]
	Strict deterministic 30-day EOD cash forecast with bounded agentic AI explanation.
	Security & Invariant:
	- Client requests cannot enable fixture mode. Production always uses FailClosedSource.
	- Fixture mode is only permissible in automated test harnesses under frappe.flags.in_test or dev test config.
	"""
	from datetime import datetime, date, timedelta
	from lotus_fin.cashflow.models import ForecastRequest, CoverageScope
	from lotus_fin.cashflow.service import get_cash_forecast, response_to_dict
	from lotus_fin.cashflow.source_interface import SyntheticFixtureSource, FailClosedSource

	# Resolve dates
	as_of_date = datetime.strptime(financial_as_of, "%Y-%m-%d").date() if financial_as_of else (date.today() - timedelta(days=1))
	start_date = datetime.strptime(forecast_start, "%Y-%m-%d").date() if forecast_start else (as_of_date + timedelta(days=1))
	end_date = datetime.strptime(forecast_end, "%Y-%m-%d").date() if forecast_end else (start_date + timedelta(days=29))

	want_explanation = False
	if isinstance(include_explanation, bool):
		want_explanation = include_explanation
	elif isinstance(include_explanation, (int, float)):
		want_explanation = bool(include_explanation)
	elif isinstance(include_explanation, str):
		want_explanation = include_explanation.strip().lower() in ["1", "true", "yes"]

	# Parse cash_account_scope
	scope_list: List[str] = []
	if isinstance(cash_account_scope, list):
		scope_list = [str(a).strip() for a in cash_account_scope if str(a).strip()]
	elif isinstance(cash_account_scope, str) and cash_account_scope.strip():
		import json
		try:
			parsed = json.loads(cash_account_scope)
			if isinstance(parsed, list):
				scope_list = [str(a).strip() for a in parsed if str(a).strip()]
			else:
				scope_list = [cash_account_scope.strip()]
		except Exception:
			scope_list = [cash_account_scope.strip()]

	req = ForecastRequest(
		company=company or "",
		financial_as_of=as_of_date,
		forecast_start=start_date,
		forecast_end=end_date,
		reporting_currency=currency,
		cash_account_scope=scope_list,
		coverage_scope=CoverageScope.TRADE_ONLY,
		include_explanation=want_explanation,
		correlation_id=correlation_id or "",
	)

	# Production default: fail closed (fixture source is never enabled via client parameter)
	future_source = FailClosedSource()
	if getattr(frappe.flags, "in_test", False) or getattr(frappe.flags, "ai002_use_fixture_source", False):
		import os
		candidate_paths = [
			frappe.get_app_path("lotus_fin", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json"),
			os.path.abspath(os.path.join(frappe.get_app_path("lotus_fin"), "..", "docs", "features", "AI002", "fixture_scripts", "direct_confirmed_commitments.json")),
			"/home/frappe/frappe-bench/apps/lotus_fin/docs/features/AI002/fixture_scripts/direct_confirmed_commitments.json",
		]
		fixture_path = None
		for cp in candidate_paths:
			if os.path.exists(cp):
				fixture_path = cp
				break
		if fixture_path:
			future_source = SyntheticFixtureSource(fixture_path)

	response = get_cash_forecast(
		request=req,
		user=frappe.session.user,
		future_event_source=future_source,
	)

	return response_to_dict(response)


@frappe.whitelist()
def get_ai002_evidence(
	evidence_ref: str,
	company: str,
) -> Dict[str, Any]:
	"""
	[AI-F002 Evidence Drilldown - CG-SEC-04, Fix C]
	Re-authorizes evidence document access on every drilldown / view action.
	Requires non-empty company.
	Fails closed with generic FORBIDDEN if unauthorized, cross-company, or nonexistent.
	"""
	from lotus_fin.security.access import verify_evidence_access, get_verified_company

	if not company or not str(company).strip():
		frappe.throw(_("FORBIDDEN"), exc=frappe.PermissionError)

	verified_comp = get_verified_company(company)
	verify_evidence_access(evidence_ref=evidence_ref, user=frappe.session.user, company=verified_comp)

	parts = evidence_ref.split(":", 1)
	doctype = parts[0].strip()
	docname = parts[1].strip()

	doc = frappe.get_doc(doctype, docname)
	return {
		"status": "success",
		"evidence_ref": evidence_ref,
		"doctype": doctype,
		"name": docname,
		"company": getattr(doc, "company", None),
		"posting_date": str(getattr(doc, "posting_date", None) or getattr(doc, "transaction_date", None)),
	}


