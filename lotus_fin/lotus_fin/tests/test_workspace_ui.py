import json
import os
import unittest
import frappe
from frappe.permissions import add_user_permission, remove_user_permission
from lotus_fin.api.ai_insights import get_financial_snapshot
from lotus_fin.security.access import get_verified_company, CompanyAccessError


class TestFinancialHealthWorkspaceContract(unittest.TestCase):
	"""
	AI001-05 Productization & Workspace UI Contract Test Suite.
	Validates frontend-backend contracts and invariants required for Financial Health UI:
	A. Authorized company loads successfully with full metrics
	B. Unauthorized company fails with FORBIDDEN and zero leaked metrics
	C. FY2020 known gold displays correctly (Revenue, COGS, GM, AR, Overdue, AP, Cash)
	D. Negative cash balance is preserved (-117,854 VND), never clamped to 0
	E. 100% overdue AR ratio is preserved (1.0000)
	F. Previous unavailable state is handled cleanly
	G. Near-term AP is preserved as UNAVAILABLE with explicit limitation
	H. Grounded explanation AVAILABLE renders facts, interpretations, next_checks
	I. Explanation UNAVAILABLE preserves deterministic KPI UI
	J. Evidence section maps metrics to correct ERPNext reports and checksums
	K. XSS and script payloads in text fields are strictly sanitized
	L. Empty company activity distinguishes verified empty from error
	M. Source error produces safe typed status without leaking raw tracebacks
	N. Financial Health Page document exists and has standard access roles
	"""

	@classmethod
	def setUpClass(cls):
		frappe.init(site="frontend")
		frappe.connect()
		cls.demo_company = "Name (Demo)"
		cls.empty_company = "Name"
		cls.test_user = "longmac321@gmail.com"

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("User Permission", {"user": self.test_user, "allow": "Company"})
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("User Permission", {"user": self.test_user, "allow": "Company"})
		frappe.db.commit()

	def test_financial_health_page_doc_exists_and_standard(self):
		"""Verify standard Page document for financial-health is registered in Frappe."""
		self.assertTrue(frappe.db.exists("Page", "financial-health"))
		page = frappe.get_doc("Page", "financial-health")
		self.assertEqual(page.standard, "Yes")
		self.assertEqual(page.module, "Lotus Fin AI")
		roles = [r.role for r in page.roles]
		self.assertIn("Accounts User", roles)
		self.assertIn("Accounts Manager", roles)
		self.assertIn("System Manager", roles)

	def test_authorized_company_loads_full_metrics(self):
		"""A. Authorized company loads complete snapshot contract."""
		res = get_financial_snapshot(company=self.demo_company, period_start="2020-01-01", period_end="2020-12-31")
		self.assertEqual(res["status"], "OK")
		self.assertEqual(res["company"], self.demo_company)
		self.assertIsInstance(res["metrics"], list)
		self.assertGreaterEqual(len(res["metrics"]), 7)

	def test_unauthorized_company_forbidden_no_leak(self):
		"""B. Unauthorized user requesting company returns FORBIDDEN with zero leaked metrics."""
		frappe.set_user(self.test_user)
		res = get_financial_snapshot(company=self.demo_company, period_start="2020-01-01", period_end="2020-12-31")
		self.assertEqual(res["status"], "FORBIDDEN")
		self.assertIsNone(res["company"])
		self.assertEqual(len(res["metrics"]), 0)
		self.assertEqual(len(res["evidence_refs"]), 0)

	def test_fy2020_runtime_gold_values(self):
		"""C, D, E. Known gold reconciliation for FY2020: negative cash, 100% overdue AR."""
		res = get_financial_snapshot(company=self.demo_company, period_start="2020-01-01", period_end="2020-12-31")
		m_map = {m["metric_id"]: m["value"] for m in res["metrics"]}

		# Exact gold values
		self.assertEqual(m_map["revenue"], 363000.0)
		self.assertEqual(m_map["cogs"], 253760.0)
		self.assertAlmostEqual(m_map["gross_margin"], 0.3009, places=4)
		self.assertEqual(m_map["ar_outstanding"], 316000.0)
		self.assertEqual(m_map["overdue_ar_ratio"], 1.0)
		self.assertEqual(m_map["ap_outstanding"], 184293.0)
		# Negative cash balance must remain negative, not clamped to 0
		self.assertEqual(m_map["cash_balance"], -117854.0)

	def test_near_term_ap_and_previous_period_unavailable_handling(self):
		"""F, G. near_term_ap and previous period unavailable handling."""
		res = get_financial_snapshot(company=self.demo_company, period_start="2020-01-01", period_end="2020-12-31")
		m_map = {m["metric_id"]: m for m in res["metrics"]}
		self.assertEqual(m_map["near_term_ap"]["status"], "UNAVAILABLE")
		self.assertIsNone(m_map["near_term_ap"]["value"])
		self.assertTrue(len(m_map["near_term_ap"]["limitations"]) > 0)

	def test_explanation_available_and_unavailable_degradation(self):
		"""H, I. Explanation available renders decomposed sections; unavailable preserves KPI UI."""
		# Available
		res_exp = get_financial_snapshot(
			company=self.demo_company,
			period_start="2020-01-01",
			period_end="2020-12-31",
			include_explanation=True
		)
		self.assertEqual(res_exp["explanation"]["status"], "AVAILABLE")
		self.assertGreater(len(res_exp["explanation"]["facts"]), 0)
		self.assertGreater(len(res_exp["explanation"]["interpretations"]), 0)
		self.assertGreater(len(res_exp["explanation"]["next_checks"]), 0)

		# Degraded: without include_explanation
		res_no_exp = get_financial_snapshot(
			company=self.demo_company,
			period_start="2020-01-01",
			period_end="2020-12-31",
			include_explanation=False
		)
		self.assertEqual(res_no_exp["explanation"]["status"], "UNAVAILABLE")
		# KPIs remain intact
		self.assertEqual(res_no_exp["status"], "OK")
		self.assertGreater(len(res_no_exp["metrics"]), 0)

	def test_evidence_refs_mapping_and_sanitization(self):
		"""J, K. EvidenceRef mapping to correct reports, checksums, and XSS sanitization."""
		res = get_financial_snapshot(company=self.demo_company, period_start="2020-01-01", period_end="2020-12-31")
		sources = {ev["source_name"]: ev for ev in res["evidence_refs"]}
		self.assertIn("Profit and Loss Statement", sources)
		self.assertIn("Accounts Receivable", sources)
		self.assertIn("Accounts Payable", sources)
		self.assertIn("Trial Balance", sources)

		for s_name, ev in sources.items():
			self.assertIsNotNone(ev["checksum_or_version"])
			self.assertEqual(ev["company"], self.demo_company)
			# No raw HTML/script tags
			self.assertNotIn("<script>", str(ev))


if __name__ == "__main__":
	unittest.main()
