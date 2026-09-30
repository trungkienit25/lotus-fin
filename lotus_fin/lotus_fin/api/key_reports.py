import json
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

try:
	import frappe
	from frappe import _
	from frappe.desk.query_report import run
	whitelist = frappe.whitelist
except (ImportError, AttributeError):
	frappe = None
	_ = lambda s: s
	run = None
	def whitelist(*args, **kwargs):
		def decorator(fn):
			return fn
		return decorator

from lotus_fin.security.access import get_verified_company, check_report_permission

# Danh sách ánh xạ các Key Reports tiêu chuẩn của ERPNext
KEY_REPORTS_REGISTRY = {
	# 1. Accounting Key Reports
	"general_ledger": {
		"report_name": "General Ledger",
		"description": "Toàn bộ phát sinh Nợ/Có của các tài khoản kế toán theo thời gian."
	},
	"accounts_receivable": {
		"report_name": "Accounts Receivable",
		"description": "Chi tiết công nợ phải thu từ khách hàng, tuổi nợ (aging) và hạn thanh toán."
	},
	"accounts_payable": {
		"report_name": "Accounts Payable",
		"description": "Chi tiết công nợ phải trả cho nhà cung cấp."
	},
	"profit_and_loss": {
		"report_name": "Profit and Loss Statement",
		"description": "Báo cáo kết quả hoạt động kinh doanh (Doanh thu, Giá vốn COGS, Chi phí, Lợi nhuận)."
	},
	"trial_balance": {
		"report_name": "Trial Balance",
		"description": "Bảng cân đối thử tổng hợp số dư Nợ/Có của toàn bộ hệ thống tài khoản kế toán."
	},
	"cash_flow": {
		"report_name": "Cash Flow",
		"description": "Báo cáo lưu chuyển tiền tệ (Kinh doanh, Đầu tư, Tài chính)."
	},
	"financial_analytics": {
		"report_name": "Financial Analytics",
		"description": "Phân tích tài chính tổng hợp theo chu kỳ tháng/quý."
	},
	# 2. Selling Key Reports
	"sales_analytics": {
		"report_name": "Sales Analytics",
		"description": "Phân tích doanh số bán hàng theo khách hàng, sản phẩm, nhóm hàng."
	},
	"sales_order_analysis": {
		"report_name": "Sales Order Analysis",
		"description": "Phân tích tình trạng thực hiện và giao hàng của các đơn đặt hàng."
	},
	# 3. Buying Key Reports
	"purchase_analytics": {
		"report_name": "Purchase Analytics",
		"description": "Phân tích chi phí mua hàng và biến động giá từ các nhà cung cấp."
	},
	# 4. Assets Key Reports
	"asset_depreciation_ledger": {
		"report_name": "Asset Depreciation Ledger",
		"description": "Sổ chi tiết khấu hao tài sản cố định qua từng kỳ."
	},
	# 5. Stock / Subcontracting Key Reports
	"stock_balance": {
		"report_name": "Stock Balance",
		"description": "Số dư tồn kho tức thời và giá trị tồn kho theo từng kho hàng."
	},
	"subcontracted_item_to_receive": {
		"report_name": "Subcontracted Item To Be Received",
		"description": "Báo cáo theo dõi hàng hóa gia công ngoài đang chờ nhận về."
	}
}


@whitelist()
def get_available_key_reports() -> Dict[str, Any]:
	"""Trả về danh mục các Key Reports có sẵn trong Lotus Fin phục vụ AI Model."""
	return {
		"status": "success",
		"reports": KEY_REPORTS_REGISTRY
	}


def is_valid_frappe_report_footer(
	report_key_or_name: str,
	columns: List[Any],
	candidate_footer: Any,
	add_total_row: Any,
	skip_total_row: Any,
) -> bool:
	"""
	Validates whether candidate_footer is a legitimate ERPNext Frappe-generated
	total footer row for Accounts Receivable / Accounts Payable reports (WV-01).

	Requirements:
	1. Report must be Accounts Receivable or Accounts Payable.
	2. add_total_row must be truthy (1, True, "1", "true") and skip_total_row must be falsy (0, False, "0", "false", None, "").
	3. candidate_footer must be a list/tuple whose length exactly matches len(columns).
	4. Non-numeric / identifier columns (voucher_no, voucher_type, party_account, name, bill_no)
	   must be empty strings or None. They must NEVER contain a transaction ID.
	5. Party/customer/supplier column must be empty or 'Total' (case-insensitive).
	6. Numeric columns (currency, float, int, percent, duration) must be numeric or empty string.
	7. Descriptive / non-aggregate columns (dates, cost centers, projects, territory, etc.)
	   must be empty strings or None, strictly reflecting Frappe's add_total_row initialization.
	8. The candidate footer must contain at least one non-empty total value (numeric, currency, or 'Total' label)
	   to distinguish it from an arbitrary empty list row.
	"""
	norm_name = str(report_key_or_name or "").strip().lower()
	if norm_name not in (
		"accounts_receivable",
		"accounts_payable",
		"accounts receivable",
		"accounts payable",
	):
		return False

	# Coerce add_total_row and skip_total_row safely
	is_skip = not (skip_total_row in (0, "0", False, "false", "False", None, ""))
	is_add = bool(add_total_row) and add_total_row not in (0, "0", False, "false", "False", None, "")

	if not is_add or is_skip:
		return False

	if not isinstance(columns, (list, tuple)) or not columns:
		return False

	if not isinstance(candidate_footer, (list, tuple)):
		return False

	if len(candidate_footer) != len(columns):
		return False

	has_non_empty_aggregate = False

	# Inspect cells against columns
	for idx, col in enumerate(columns):
		options = ""
		if isinstance(col, dict):
			fieldname = str(col.get("fieldname") or "").strip().lower()
			fieldtype = str(col.get("fieldtype") or "").strip().lower()
			options = str(col.get("options") or "").strip().lower()
		elif isinstance(col, str):
			parts = col.split(":")
			label = parts[0].strip().lower()
			fieldname = label.replace(" ", "_")
			fieldtype_opt = parts[1].strip() if len(parts) > 1 else ""
			if "/" in fieldtype_opt:
				ft, opt = fieldtype_opt.split("/", 1)
				fieldtype = ft.strip().lower()
				options = opt.strip().lower()
			else:
				fieldtype = fieldtype_opt.lower()
		else:
			fieldname = ""
			fieldtype = ""

		cell = candidate_footer[idx]

		# Identifier columns MUST NOT contain actual transaction IDs
		if fieldname in ("voucher_no", "voucher_type", "party_account", "name", "bill_no"):
			if cell not in ("", None):
				return False

		# Party column: either empty or 'Total'
		if fieldname in ("party", "customer", "supplier"):
			if cell not in ("", None):
				if str(cell).strip().lower() != "total":
					return False
				has_non_empty_aggregate = True

		# Numeric columns: in Frappe add_total_row they are float/int or empty string
		elif (
			fieldtype in ("currency", "float", "int", "percent", "duration")
			or fieldname in (
				"invoiced", "invoiced_amount", "paid", "paid_amount", "credit_note",
				"credit_note_amount", "outstanding", "outstanding_amount", "total_due",
				"age", "balance", "net_amount", "amount", "total"
			)
			or fieldname.startswith("range")
			or (not fieldtype and isinstance(cell, (int, float, Decimal)))
		):
			if cell not in ("", None):
				try:
					float(cell)
					has_non_empty_aggregate = True
				except (ValueError, TypeError):
					return False

		# Currency link column: Frappe copies currency code from first row
		elif (fieldtype == "link" and options == "currency") or fieldname == "currency":
			if cell not in ("", None):
				if not isinstance(cell, str) or len(cell.strip()) > 10:
					return False
				has_non_empty_aggregate = True

		# First column: Frappe may write "Total" if first column type is not unsupported
		elif idx == 0:
			if cell not in ("", None):
				if "total" not in str(cell).strip().lower():
					return False
				has_non_empty_aggregate = True

		# ALL OTHER COLUMNS (dates, cost center, project, territory, po_no, groups, remarks, etc.)
		# Frappe add_total_row initializes them to "" and never populates them.
		else:
			if cell not in ("", None):
				return False

	return has_non_empty_aggregate


def normalize_frappe_report_footer(
	report_key_or_name: str,
	columns: List[Any],
	rows: List[Any],
	add_total_row: bool,
	skip_total_row: bool,
) -> Tuple[List[Dict[str, Any]], Optional[List[Any]], bool]:
	"""
	Identifies and separates the Frappe v16 query_report total footer from data rows (WV-01).

	Returns: (clean_rows, total_row, has_total_row)
	- If a valid Frappe total footer is found as the last row and all preceding rows are dicts:
	  clean_rows = rows[:-1], total_row = rows[-1], has_total_row = True
	- If rows only contains the valid footer:
	  clean_rows = [], total_row = rows[-1], has_total_row = True (verified empty)
	- If rows does NOT have a valid footer (or has malformed lists in middle/start, or two footers):
	  clean_rows = rows, total_row = None, has_total_row = False
	"""
	if not isinstance(rows, list) or not rows:
		return rows if isinstance(rows, list) else [], None, False

	last_row = rows[-1]
	if is_valid_frappe_report_footer(
		report_key_or_name, columns, last_row, add_total_row, skip_total_row
	):
		# All preceding rows MUST be dicts
		if all(isinstance(r, dict) for r in rows[:-1]):
			return rows[:-1], last_row, True

	return rows, None, False


@whitelist()
def extract_key_report_data(
	report_key: str,
	filters: Optional[Dict[str, Any]] = None,
	company: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Trích xuất dữ liệu chuẩn hóa từ một Key Report của ERPNext để nạp cho Model AI hoặc Client.
	Áp dụng server-side company authorization guard và report permission check.
	
	:param report_key: Khóa của báo cáo trong KEY_REPORTS_REGISTRY (ví dụ: 'general_ledger', 'sales_analytics')
	:param filters: Bộ lọc đầu vào cho báo cáo (from_date, to_date, company, ...)
	:param company: Tên công ty (untrusted param, validated server-side)
	"""
	if report_key not in KEY_REPORTS_REGISTRY:
		frappe.throw(_(f"Report key '{report_key}' không tồn tại trong Lotus Fin Key Reports Registry."))

	report_meta = KEY_REPORTS_REGISTRY[report_key]
	report_name = report_meta["report_name"]

	# Parse filters nếu truyền dạng chuỗi JSON
	if isinstance(filters, str):
		filters = json.loads(filters)
	elif filters is None:
		filters = {}
	else:
		filters = dict(filters)

	# 1. Server-side company authorization guard (INV-01, INV-02)
	# filters['company'] or company param are both untrusted.
	requested_company = filters.get("company") or company
	verified_company = get_verified_company(requested_company)
	filters["company"] = verified_company

	# 2. Report permission check
	check_report_permission(report_name)

	try:
		# Chạy report engine nội bộ của Frappe
		report_result = run(report_name=report_name, filters=filters)
		columns = report_result.get("columns", [])
		result_data = report_result.get("result", [])
		add_total_row = bool(report_result.get("add_total_row"))
		skip_total_row = bool(report_result.get("skip_total_row"))

		clean_data, total_row, has_total_row = normalize_frappe_report_footer(
			report_key, columns, result_data, add_total_row, skip_total_row
		)

		# Chuẩn hóa dữ liệu đầu ra dạng tabular/features sạch
		return {
			"status": "success",
			"report_key": report_key,
			"report_name": report_name,
			"company": verified_company,
			"total_rows": len(clean_data),
			"columns": columns,
			"data": clean_data,
			"total_row": total_row,
			"has_total_row": has_total_row,
			"add_total_row": add_total_row,
			"skip_total_row": skip_total_row,
			"filters_applied": filters
		}
	except Exception as e:
		if frappe and hasattr(frappe, "log_error"):
			frappe.log_error(f"Error extracting key report {report_name}: {str(e)}")
		return {
			"status": "error",
			"report_key": report_key,
			"report_name": report_name,
			"company": verified_company,
			"message": str(e)
		}


@whitelist()
def get_ai_training_dataset(
	company: Optional[str] = None,
	from_date: Optional[str] = None,
	to_date: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Gói tổng hợp toàn bộ dữ liệu từ các Key Reports thành 1 Dataset hợp nhất
	để nạp vào mô hình AI. Áp dụng server-side company authorization guard.
	"""
	verified_company = get_verified_company(company)
	base_filters = {"company": verified_company}
	if from_date:
		base_filters["from_date"] = from_date
	if to_date:
		base_filters["to_date"] = to_date

	dataset = {
		"status": "success",
		"company": verified_company,
		"exported_at": frappe.utils.now(),
		"modules": {}
	}

	for key, meta in KEY_REPORTS_REGISTRY.items():
		try:
			data = extract_key_report_data(report_key=key, filters=base_filters, company=verified_company)
			if data.get("status") == "success":
				dataset["modules"][key] = {
					"status": "success",
					"name": meta["report_name"],
					"total_rows": data.get("total_rows", 0),
					"rows": data.get("data", [])
				}
			else:
				dataset["modules"][key] = {
					"status": "error",
					"name": meta["report_name"],
					"error": data.get("message", "Unknown error")
				}
		except Exception as e:
			dataset["modules"][key] = {
				"status": "error",
				"name": meta["report_name"],
				"error": str(e)
			}

	return dataset
