import json
from typing import Any, Dict, List, Optional
import frappe
from frappe import _
from frappe.desk.query_report import run

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


@frappe.whitelist()
def get_available_key_reports() -> Dict[str, Any]:
	"""Trả về danh mục các Key Reports có sẵn trong Lotus Fin phục vụ AI Model."""
	return {
		"status": "success",
		"reports": KEY_REPORTS_REGISTRY
	}


@frappe.whitelist()
def extract_key_report_data(
	report_key: str,
	filters: Optional[Dict[str, Any]] = None,
	company: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Trích xuất dữ liệu chuẩn hóa từ một Key Report của ERPNext để nạp cho Model AI hoặc Client.
	
	:param report_key: Khóa của báo cáo trong KEY_REPORTS_REGISTRY (ví dụ: 'general_ledger', 'sales_analytics')
	:param filters: Bộ lọc đầu vào cho báo cáo (from_date, to_date, company, ...)
	:param company: Tên công ty (mặc định lấy default company nếu None)
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

	# Gán default company nếu chưa có trong filter
	if "company" not in filters:
		filters["company"] = company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

	try:
		# Chạy report engine nội bộ của Frappe
		report_result = run(report_name=report_name, filters=filters)
		columns = report_result.get("columns", [])
		result_data = report_result.get("result", [])

		# Chuẩn hóa dữ liệu đầu ra dạng tabular/features sạch
		return {
			"status": "success",
			"report_key": report_key,
			"report_name": report_name,
			"total_rows": len(result_data),
			"columns": columns,
			"data": result_data,
			"filters_applied": filters
		}
	except Exception as e:
		frappe.log_error(f"Error extracting key report {report_name}: {str(e)}")
		return {
			"status": "error",
			"report_key": report_key,
			"message": str(e)
		}


@frappe.whitelist()
def get_ai_training_dataset(
	company: Optional[str] = None,
	from_date: Optional[str] = None,
	to_date: Optional[str] = None
) -> Dict[str, Any]:
	"""
	Gói tổng hợp toàn bộ dữ liệu từ các Key Reports thành 1 Dataset hợp nhất
	để nạp vào mô hình AI (Cash flow forecasting, Credit scoring, Inventory optimization).
	"""
	default_company = company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
	base_filters = {"company": default_company}
	if from_date:
		base_filters["from_date"] = from_date
	if to_date:
		base_filters["to_date"] = to_date

	dataset = {
		"company": default_company,
		"exported_at": frappe.utils.now(),
		"modules": {}
	}

	for key, meta in KEY_REPORTS_REGISTRY.items():
		try:
			data = extract_key_report_data(report_key=key, filters=base_filters, company=default_company)
			if data.get("status") == "success":
				dataset["modules"][key] = {
					"name": meta["report_name"],
					"rows": data["data"]
				}
		except Exception as e:
			dataset["modules"][key] = {"error": str(e)}

	return dataset

