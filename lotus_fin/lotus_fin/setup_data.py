import frappe

def setup_demo_environment():
	"""Ensure demo companies, test user, and fiscal years exist for full compatibility."""
	# 1. Ensure test user exists
	test_user = "longmac321@gmail.com"
	if not frappe.db.exists("User", test_user):
		u = frappe.get_doc({
			"doctype": "User",
			"email": test_user,
			"first_name": "Test User",
			"enabled": 1,
			"roles": [{"role": "Accounts User"}]
		})
		u.flags.ignore_permissions = True
		u.flags.ignore_password_policy = True
		u.insert()

	# 2. Ensure Name and Name (Demo) exist as company records if needed
	compat_companies = [
		("Lotus-fin", "VND", "Vietnam"),
		("Lotus-fin (Demo)", "VND", "Vietnam"),
		("Name", "VND", "Vietnam"),
		("Name (Demo)", "VND", "Vietnam")
	]
	for c_name, curr, country in compat_companies:
		if not frappe.db.exists("Company", c_name):
			comp = frappe.get_doc({
				"doctype": "Company",
				"company_name": c_name,
				"name": c_name,
				"default_currency": curr,
				"country": country
			})
			comp.flags.ignore_permissions = True
			comp.flags.ignore_mandatory = True
			comp.insert()

	# 3. Ensure fiscal years (2019, 2020, 2024, 2025, 2026) exist for all companies
	fiscal_years = [
		("2019", "2019-01-01", "2019-12-31"),
		("2020", "2020-01-01", "2020-12-31"),
		("2024", "2024-01-01", "2024-12-31"),
		("2025", "2025-01-01", "2025-12-31"),
		("2026", "2026-01-01", "2026-12-31"),
	]

	all_companies = frappe.get_all("Company", pluck="name")

	for year, start_date, end_date in fiscal_years:
		if not frappe.db.exists("Fiscal Year", year):
			fy = frappe.get_doc({
				"doctype": "Fiscal Year",
				"year": year,
				"year_start_date": start_date,
				"year_end_date": end_date,
				"disabled": 0,
				"companies": [{"company": c} for c in all_companies]
			})
			fy.flags.ignore_permissions = True
			fy.flags.ignore_mandatory = True
			fy.insert()
		else:
			fy = frappe.get_doc("Fiscal Year", year)
			existing = [row.company for row in fy.companies]
			changed = False
			for c in all_companies:
				if c not in existing:
					fy.append("companies", {"company": c})
					changed = True
			if changed:
				fy.flags.ignore_permissions = True
				fy.save()

	# 4. Ensure test item exists for non-stock service billing
	service_item = "SRV-CONSULTING"
	if not frappe.db.exists("Item", service_item):
		it = frappe.new_doc("Item")
		it.item_code = service_item
		it.item_name = "Dịch vụ Tư vấn Quản trị Tài chính"
		it.item_group = "All Item Groups"
		it.is_stock_item = 0
		it.flags.ignore_permissions = True
		it.flags.ignore_mandatory = True
		it.insert()

	# 5. Seed accounting records for Lotus-fin if empty
	if frappe.db.count("GL Entry", {"company": "Lotus-fin"}) == 0:
		# Approved cash accounts config
		frappe.db.set_value("Company", "Lotus-fin", "ai002_approved_cash_accounts", '["Cash - L"]')

		# Sales Invoice 1
		si = frappe.new_doc("Sales Invoice")
		si.company = "Lotus-fin"
		si.customer = "Grant Plastics Ltd."
		si.set_posting_time = 1
		si.posting_date = "2026-02-15"
		si.due_date = "2026-03-15"
		si.debit_to = "Debtors - L"
		si.append("items", {
			"item_code": service_item,
			"qty": 1,
			"rate": 50000000,
			"income_account": "Sales - L",
			"cost_center": "Main - L"
		})
		si.flags.ignore_permissions = True
		si.insert()
		si.submit()

		# Payment Entry (partial payment)
		pe = frappe.new_doc("Payment Entry")
		pe.company = "Lotus-fin"
		pe.payment_type = "Receive"
		pe.party_type = "Customer"
		pe.party = "Grant Plastics Ltd."
		pe.set_posting_time = 1
		pe.posting_date = "2026-03-01"
		pe.paid_from = "Debtors - L"
		pe.paid_to = "Cash - L"
		pe.paid_amount = 30000000
		pe.received_amount = 30000000
		pe.target_exchange_rate = 1.0
		pe.append("references", {
			"reference_doctype": "Sales Invoice",
			"reference_name": si.name,
			"total_amount": 50000000,
			"outstanding_amount": 50000000,
			"allocated_amount": 30000000
		})
		pe.flags.ignore_permissions = True
		pe.insert()
		pe.submit()

		# Purchase Invoice (AP obligation)
		pi = frappe.new_doc("Purchase Invoice")
		pi.company = "Lotus-fin"
		pi.supplier = "Summit Traders Ltd."
		pi.set_posting_time = 1
		pi.posting_date = "2026-03-01"
		pi.due_date = "2026-03-25"
		pi.credit_to = "Creditors - L"
		pi.append("items", {
			"item_code": service_item,
			"qty": 1,
			"rate": 15000000,
			"expense_account": "Administrative Expenses - L",
			"cost_center": "Main - L"
		})
		pi.flags.ignore_permissions = True
		pi.insert()
		pi.submit()

	frappe.db.commit()
	return {"status": "success", "message": "Demo environment fully configured"}
