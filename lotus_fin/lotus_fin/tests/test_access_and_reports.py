import unittest
from unittest.mock import patch
import frappe
from frappe.permissions import add_user_permission, remove_user_permission

from lotus_fin.security.access import get_verified_company, check_report_permission, CompanyAccessError
from lotus_fin.api.key_reports import extract_key_report_data, get_available_key_reports, get_ai_training_dataset
from lotus_fin.api.ai_insights import predict_cashflow, analyze_invoice_risk, get_financial_snapshot


class TestAccessAndReports(unittest.TestCase):
	"""
	Comprehensive test suite for Lotus Fin AI001 guard and report endpoints:
	1. Same-company allow
	2. Cross-company deny
	3. Report error handling (preserving error states, no silent conversion to zero)
	4. Empty result handling (distinguishing empty dataset from error)
	5. Unauthorized resource handling (invoice, report, company)
	6. AR-AP cashflow deprecation flags
	7. Preserve existing ERPNext report behavior
	"""

	@classmethod
	def setUpClass(cls):
		frappe.init(site="frontend")
		frappe.connect()
		demo_comp = frappe.db.get_value("GL Entry", {}, "company") or frappe.db.get_value("Company", {"name": ["like", "%Demo%"]}, "name")
		empty_comp = frappe.db.get_value("Company", {"name": ["not like", "%Demo%"]}, "name")
		cls.demo_company = demo_comp or "Lotus-fin (Demo)"
		cls.empty_company = empty_comp or "Lotus-fin"
		cls.test_user = "longmac321@gmail.com"

		sample_date = frappe.db.get_value("GL Entry", {"company": cls.demo_company}, "posting_date")
		cls.demo_year = str(sample_date)[:4] if sample_date else "2020"
		cls.p_start = f"{cls.demo_year}-01-01"
		cls.p_end = f"{cls.demo_year}-12-31"

		if not frappe.db.exists("User", cls.test_user):
			u = frappe.get_doc({
				"doctype": "User",
				"email": cls.test_user,
				"first_name": "Test User",
				"enabled": 1,
				"roles": [{"role": "Accounts User"}]
			})
			u.flags.ignore_permissions = True
			u.flags.ignore_password_policy = True
			u.insert()
			frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")
		# Clean any pre-existing user permissions for test_user on Company
		frappe.db.delete("User Permission", {"user": self.test_user, "allow": "Company"})
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("User Permission", {"user": self.test_user, "allow": "Company"})
		frappe.db.commit()

	# --- 1. Same-company allow ---
	def test_same_company_allow_as_admin(self):
		"""Admin should have access to both demo and empty company."""
		comp = get_verified_company(self.demo_company, user="Administrator")
		self.assertEqual(comp, self.demo_company)

		comp2 = get_verified_company(self.empty_company, user="Administrator")
		self.assertEqual(comp2, self.empty_company)

	def test_same_company_allow_restricted_user(self):
		"""Restricted user should have access only to their permitted company."""
		add_user_permission("Company", self.empty_company, self.test_user)
		frappe.db.commit()

		frappe.set_user(self.test_user)
		comp = get_verified_company(self.empty_company)
		self.assertEqual(comp, self.empty_company)

		# extract_key_report_data for allowed company succeeds
		res = extract_key_report_data("accounts_receivable", company=self.empty_company)
		self.assertEqual(res["status"], "success")
		self.assertEqual(res["company"], self.empty_company)
		self.assertEqual(res["total_rows"], 0)

	# --- 2. Cross-company deny ---
	def test_cross_company_deny(self):
		"""User restricted to Company 'Name' must be denied access to 'Name (Demo)'."""
		add_user_permission("Company", self.empty_company, self.test_user)
		frappe.db.commit()

		frappe.set_user(self.test_user)
		with self.assertRaises(CompanyAccessError):
			get_verified_company(self.demo_company)

		with self.assertRaises(CompanyAccessError):
			extract_key_report_data("accounts_receivable", company=self.demo_company)

		with self.assertRaises(CompanyAccessError):
			predict_cashflow(company=self.demo_company)

	def test_cross_company_via_filter_tampering_deny(self):
		"""User cannot bypass company restriction by passing company inside filters dict."""
		add_user_permission("Company", self.empty_company, self.test_user)
		frappe.db.commit()

		frappe.set_user(self.test_user)
		with self.assertRaises(CompanyAccessError):
			extract_key_report_data("accounts_receivable", filters={"company": self.demo_company})

	# --- 3. Report error handling (No error source becomes zero) ---
	def test_report_error_preserved_in_extract_key_report(self):
		"""When query report fails (e.g. mandatory filters missing), return status error and error message."""
		res = extract_key_report_data("general_ledger", company=self.demo_company)
		self.assertEqual(res["status"], "error")
		self.assertEqual(res["report_key"], "general_ledger")
		self.assertIn("mandatory", res["message"])

	def test_report_error_preserved_in_predict_cashflow(self):
		"""If AR or AP fails, predict_cashflow MUST NOT fabricate zero inflow/outflow, but return status error."""
		with patch("lotus_fin.api.ai_insights.extract_key_report_data") as mock_extract:
			mock_extract.return_value = {
				"status": "error",
				"message": "Database connection timeout or internal report error"
			}
			res = predict_cashflow(company=self.demo_company)
			self.assertEqual(res["status"], "error")
			self.assertEqual(res.get("source_error"), "accounts_receivable")
			self.assertIn("Database connection timeout", res["message"])
			# Crucial: summary should NOT be present with fabricated zero
			self.assertNotIn("summary", res)

	# --- 4. Empty result handling ---
	def test_empty_result_distinguished_from_error(self):
		"""Empty company yields status 'success' with total_rows = 0 and empty list, not an error."""
		res = extract_key_report_data("accounts_receivable", company=self.empty_company)
		self.assertEqual(res["status"], "success")
		self.assertEqual(res["total_rows"], 0)
		self.assertEqual(res["data"], [])

	def test_predict_cashflow_on_empty_company(self):
		"""Empty company with no transactions yields 0 inflow/outflow with success status and deprecated warning."""
		res = predict_cashflow(company=self.empty_company)
		self.assertEqual(res["status"], "success")
		self.assertTrue(res.get("deprecated"))
		self.assertEqual(res["summary"]["predicted_inflow"], 0.0)
		self.assertEqual(res["summary"]["predicted_outflow"], 0.0)
		self.assertEqual(res["summary"]["net_cash_change"], 0.0)

	# --- 5. Unauthorized resource handling ---
	def test_unauthorized_guest_denied_report(self):
		"""Guest user must be denied from extracting reports."""
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			check_report_permission("General Ledger")

	def test_nonexistent_company_raises_does_not_exist(self):
		"""Nonexistent company must raise CompanyAccessError (FORBIDDEN)."""
		with self.assertRaises(CompanyAccessError):
			get_verified_company("TotallyNonExistentCompany123")

	def test_nonexistent_report_key_raises_error(self):
		"""Requesting unknown report key must throw ValidationError."""
		with self.assertRaises(frappe.ValidationError):
			extract_key_report_data("non_existent_report_xyz", company=self.demo_company)

	def test_unauthorized_invoice_risk_analysis_deny(self):
		"""User restricted to Company 'Name' cannot analyze invoice belonging to 'Name (Demo)'."""
		add_user_permission("Company", self.empty_company, self.test_user)
		frappe.db.commit()

		frappe.set_user(self.test_user)
		with self.assertRaises(frappe.PermissionError):
			analyze_invoice_risk("ACC-SINV-2026-00003")

	# --- 6. Deprecation and Data Integrity ---
	def test_predict_cashflow_deprecation_flag(self):
		"""predict_cashflow output must include deprecation warning flag."""
		res = predict_cashflow(company=self.demo_company)
		self.assertEqual(res["status"], "success")
		self.assertTrue(res.get("deprecated"))
		self.assertIn("DEPRECATED", res.get("warning"))

	# --- 7. Preserve ERPNext report behavior ---
	def test_erpnext_report_execution_with_proper_filters(self):
		"""Standard ERPNext report execution produces expected columns and rows."""
		res = extract_key_report_data(
			"general_ledger",
			filters={"from_date": "2020-01-01", "to_date": "2020-12-31"},
			company=self.demo_company
		)
		self.assertEqual(res["status"], "success")
		self.assertGreater(res["total_rows"], 0)
		self.assertIsInstance(res["columns"], list)
		self.assertIsInstance(res["data"], list)

	def test_get_available_key_reports(self):
		"""Registry listing succeeds."""
		res = get_available_key_reports()
		self.assertEqual(res["status"], "success")
		self.assertIn("general_ledger", res["reports"])
		self.assertIn("accounts_receivable", res["reports"])
		self.assertIn("accounts_payable", res["reports"])

	def test_get_ai_training_dataset_preserves_module_errors(self):
		"""Dataset aggregation must capture module errors without crashing and apply company isolation."""
		dataset = get_ai_training_dataset(company=self.demo_company)
		self.assertEqual(dataset["status"], "success")
		self.assertEqual(dataset["company"], self.demo_company)
		self.assertIn("modules", dataset)
		# general_ledger without from_date/to_date should be an error module, not crash
		self.assertIn("general_ledger", dataset["modules"])
		self.assertEqual(dataset["modules"]["general_ledger"]["status"], "error")

	def test_analyze_invoice_risk_success(self):
		"""Admin or authorized user can successfully analyze a valid invoice."""
		res = analyze_invoice_risk("ACC-SINV-2026-00003")
		self.assertEqual(res["status"], "success")
		self.assertEqual(res["invoice"], "ACC-SINV-2026-00003")
		self.assertEqual(res["company"], self.demo_company)
		self.assertIn("risk_level", res)

	def test_unauthorized_guest_denied_company(self):
		"""Guest user must be denied company verification."""
		frappe.set_user("Guest")
		with self.assertRaises(CompanyAccessError):
			get_verified_company(self.demo_company)

	def test_get_financial_snapshot_endpoint_structure(self):
		"""get_financial_snapshot returns structured FinancialSnapshot and EvidenceRefs."""
		res = get_financial_snapshot(company=self.demo_company, period_start=self.p_start, period_end=self.p_end)
		self.assertEqual(res["status"], "OK")
		self.assertEqual(res["company"], self.demo_company)
		self.assertEqual(res["feature_id"], "AI001")
		self.assertEqual(res["contract_version"], "1.0.0")
		self.assertIsInstance(res["metrics"], list)
		self.assertIsInstance(res["evidence_refs"], list)
		self.assertEqual(res["explanation"]["status"], "UNAVAILABLE")

	def test_get_financial_snapshot_live_gold_reconciliation(self):
		"""Verify live ERPNext report execution matches known gold exactly for demo period."""
		res = get_financial_snapshot(company=self.demo_company, period_start=self.p_start, period_end=self.p_end)
		self.assertEqual(res["status"], "OK")

		metrics = {m["metric_id"]: m["value"] for m in res["metrics"]}
		self.assertEqual(metrics["revenue"], 363000.0)
		self.assertEqual(metrics["cogs"], 253760.0)
		self.assertAlmostEqual(metrics["gross_margin"], 0.3009, places=4)
		self.assertEqual(metrics["ar_outstanding"], 316000.0)
		self.assertEqual(metrics["overdue_ar_ratio"], 1.0)
		self.assertEqual(metrics["ap_outstanding"], 184293.0)
		self.assertEqual(metrics["cash_balance"], -117854.0)

		# Verify exact evidence refs filters
		ev_map = {e["source_name"]: e["filters"] for e in res["evidence_refs"]}
		self.assertIn("report_date", ev_map["Accounts Receivable"])
		self.assertEqual(ev_map["Accounts Receivable"]["report_date"], self.p_end)
		self.assertIn("report_date", ev_map["Accounts Payable"])
		self.assertEqual(ev_map["Accounts Payable"]["report_date"], self.p_end)
		self.assertIn("period_start_date", ev_map["Profit and Loss Statement"])
		self.assertIn("fiscal_year", ev_map["Trial Balance"])

	def test_get_financial_snapshot_as_of_prior_to_period_end_rule(self):
		"""When as_of is prior to period_end, report boundaries are restricted to as_of date."""
		as_of_dt = f"{self.demo_year}-03-31"
		res = get_financial_snapshot(
			company=self.demo_company,
			period_start=self.p_start,
			period_end=self.p_end,
			as_of=f"{as_of_dt}T00:00:00Z"
		)
		self.assertEqual(res["status"], "OK")
		ev_map = {e["source_name"]: e["filters"] for e in res["evidence_refs"]}
		self.assertEqual(ev_map["Accounts Receivable"]["report_date"], as_of_dt)
		self.assertEqual(ev_map["Accounts Payable"]["report_date"], as_of_dt)
		self.assertEqual(ev_map["Profit and Loss Statement"]["period_end_date"], as_of_dt)
		self.assertEqual(ev_map["Trial Balance"]["to_date"], as_of_dt)

	def test_get_financial_snapshot_near_term_ap_status(self):
		"""near_term_ap metric is present with UNAVAILABLE status and frozen limitation."""
		res = get_financial_snapshot(company=self.demo_company, period_start=self.p_start, period_end=self.p_end)
		self.assertEqual(res["status"], "OK")
		metrics = {m["metric_id"]: m for m in res["metrics"]}
		self.assertIn("near_term_ap", metrics)
		self.assertEqual(metrics["near_term_ap"]["status"], "UNAVAILABLE")
		self.assertIsNone(metrics["near_term_ap"]["value"])
		self.assertIn("near-term AP horizon not yet frozen", metrics["near_term_ap"]["limitations"])

	def test_get_financial_snapshot_previous_period_comparison_live(self):
		"""When comparison=PREVIOUS_PERIOD, comparison block is returned with accurate deltas."""
		res = get_financial_snapshot(
			company=self.demo_company,
			period_start=self.p_start,
			period_end=self.p_end,
			comparison="PREVIOUS_PERIOD"
		)
		self.assertEqual(res["status"], "OK")
		self.assertIsNotNone(res["comparison"])
		comp = res["comparison"]
		self.assertEqual(comp["status"], "AVAILABLE")
		self.assertEqual(comp["type"], "PREVIOUS_PERIOD")
		prev_year = str(int(self.demo_year) - 1)
		self.assertEqual(comp["previous_period"], {"start": f"{prev_year}-01-01", "end": f"{prev_year}-12-31"})
		self.assertIn("revenue", comp["metrics"])
		self.assertIn("cash_balance", comp["metrics"])
		self.assertIn("ar_outstanding", comp["metrics"])
		self.assertIn("ap_outstanding", comp["metrics"])

	def test_get_financial_snapshot_live_explanation(self):
		"""Whitelisted get_financial_snapshot supports include_explanation=True."""
		res = get_financial_snapshot(
			company=self.demo_company,
			period_start=self.p_start,
			period_end=self.p_end,
			include_explanation=True
		)
		self.assertEqual(res["status"], "OK")
		self.assertIsNotNone(res["explanation"])
		self.assertEqual(res["explanation"]["status"], "AVAILABLE")
		self.assertTrue(len(res["explanation"]["facts"]) > 0)
		self.assertTrue(len(res["explanation"]["next_checks"]) > 0)


if __name__ == "__main__":
	unittest.main()



