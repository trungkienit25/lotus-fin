import frappe
from frappe import _
from typing import Any, Dict, Optional
from lotus_fin.api.key_reports import extract_key_report_data


# --- Event Hooks ---

def on_sales_invoice_submit(doc, method=None):
	"""
	Triggered khi Sales Invoice được Submit.
	Tự động phân tích điểm rủi ro công nợ khách hàng hoặc dự báo ngày tiền về thực tế.
	"""
	try:
		# Log hoặc gọi AI Microservice / Local model
		customer = doc.customer
		outstanding = doc.outstanding_amount or doc.grand_total
		# Tạo notification hoặc ghi chú phân tích
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
	Chạy hàng ngày để tổng hợp dòng tiền 30 ngày tới dựa trên các khoản phải thu/phải trả.
	"""
	frappe.logger("lotus_fin_ai").info("[Lotus Fin AI] Running daily cash flow digest job.")


def evaluate_sme_financial_health():
	"""
	Chạy hàng tuần để chấm điểm sức khỏe tài chính của SME (Khả năng thanh toán, Vòng quay tồn kho, Biên lợi nhuận).
	"""
	frappe.logger("lotus_fin_ai").info("[Lotus Fin AI] Running weekly SME financial health evaluation.")


# --- Whitelisted REST Endpoints for Frontend / AI Client ---

@frappe.whitelist()
def predict_cashflow(days_ahead: int = 30, company: Optional[str] = None) -> Dict[str, Any]:
	"""
	Endpoint dự báo dòng tiền trong N ngày tới cho SME dựa trên Key Reports.
	"""
	default_company = company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
	
	# 1. Trích xuất dữ liệu công nợ phải thu (Receivables)
	ar_data = extract_key_report_data("accounts_receivable", company=default_company)
	# 2. Trích xuất dữ liệu công nợ phải trả (Payables)
	ap_data = extract_key_report_data("accounts_payable", company=default_company)

	# Mock logic tính toán dự báo thông minh từ dữ liệu thực tế
	total_receivable = sum([row.get("outstanding", 0) for row in ar_data.get("data", []) if isinstance(row, dict)])
	total_payable = sum([row.get("outstanding", 0) for row in ap_data.get("data", []) if isinstance(row, dict)])

	net_predicted_change = total_receivable - total_payable

	return {
		"status": "success",
		"company": default_company,
		"days_ahead": int(days_ahead),
		"summary": {
			"predicted_inflow": total_receivable,
			"predicted_outflow": total_payable,
			"net_cash_change": net_predicted_change,
			"liquidity_risk": "LOW" if net_predicted_change >= 0 else "WARNING"
		},
		"recommendation": "Dòng tiền dự kiến dương trong 30 ngày tới. Doanh nghiệp có thể duy trì kế hoạch chi tiêu bình thường." if net_predicted_change >= 0 else "Cảnh báo: Khoản phải trả lớn hơn khoản phải thu dự kiến. Khuyến nghị thúc đẩy thu hồi công nợ sớm."
	}


@frappe.whitelist()
def analyze_invoice_risk(invoice_name: str) -> Dict[str, Any]:
	"""
	Endpoint phân tích rủi ro thanh toán cho 1 hóa đơn cụ thể (gắn vào nút bấm trên giao diện Sales Invoice).
	"""
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_(f"Hóa đơn {invoice_name} không tồn tại."))

	doc = frappe.get_doc("Sales Invoice", invoice_name)
	customer = doc.customer
	amount = doc.grand_total

	# Đọc lịch sử quá khứ của khách hàng này
	past_invoices = frappe.get_all(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1, "name": ["!=", invoice_name]},
		fields=["name", "status", "outstanding_amount"]
	)
	
	unpaid_count = len([inv for inv in past_invoices if inv.status in ["Overdue", "Unpaid"]])
	risk_level = "LOW" if unpaid_count == 0 else ("MEDIUM" if unpaid_count <= 2 else "HIGH")

	return {
		"status": "success",
		"invoice": invoice_name,
		"customer": customer,
		"amount": amount,
		"risk_level": risk_level,
		"analysis": f"Khách hàng '{customer}' có {len(past_invoices)} hóa đơn lịch sử ({unpaid_count} hóa đơn chưa thanh toán/quá hạn). Mức độ rủi ro tín dụng: {risk_level}."
	}

