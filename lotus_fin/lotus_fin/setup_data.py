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

	frappe.db.commit()
	return {"status": "success", "message": "Demo environment fully configured"}
