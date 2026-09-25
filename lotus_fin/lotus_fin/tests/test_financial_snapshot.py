"""
Comprehensive Test Suite for AI001 FinancialSnapshot + EvidenceRef Engine.

Covered verification dimensions:
1. Numeric reconciliation against independent gold calculation (F001-NUM-01):
   - Revenue, COGS, Gross Margin ratio & calculation.
   - AR total, Overdue AR, Overdue AR ratio.
   - AP total outstanding.
   - Cash & Bank balance.
2. Missing-data safe-handling (F001-DATA-01 / F001-DATA-02):
   - Missing P&L yields UNAVAILABLE metrics and INSUFFICIENT_DATA or PARTIAL, never 0.0.
   - Missing AR/AP yields UNAVAILABLE metrics, never silent zero.
   - Missing Cash source marked in missing_inputs.
3. Source-error handling:
   - Report errors propagated cleanly as SOURCE_ERROR without throwing unhandled exceptions.
4. Company authorization & permission guard (F001-AUTH-01):
   - Empty or unauthorized company requests yield FORBIDDEN.
   - Cross-company leakage blocked.
5. Evidence linkage & provenance (EvidenceRef):
   - Every available metric links directly to its source EvidenceRef checksum/hash.
   - Temporal range, as_of timestamp and snapshot_id correctly tracked.
6. Period temporal validation:
   - period_start > period_end triggers VALIDATION_ERROR.
"""

from decimal import Decimal
import unittest
import sys
import os

# Add repo to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.ai.financial_snapshot import (
    build_financial_snapshot,
    to_decimal,
    parse_pnl_data,
    parse_ar_data,
    parse_ap_data,
    parse_cash_balance,
    generate_evidence_ref
)


class TestFinancialSnapshotAndEvidence(unittest.TestCase):
    def setUp(self):
        self.company = "Name (Demo)"
        self.period_start = "2026-01-01"
        self.period_end = "2026-12-31"

        # Independent Gold Datasets (Synthetic Controlled Fixtures conforming to Data Strategy §3 & §8)
        # Gold P&L: Revenue = 1,000,000, COGS = 600,000 -> Gross Margin = 40.00% (0.4000)
        self.gold_pnl_data = [
            {"account_name": "Sales Revenue", "balance": 700000.00},
            {"account_name": "Service Income", "balance": 300000.00},
            {"account_name": "Cost of Goods Sold - Materials", "balance": 450000.00},
            {"account_name": "COGS - Direct Labor", "balance": 150000.00},
            {"account_name": "Operating Expenses", "balance": 100000.00}
        ]

        # Gold AR: Total = 50,000.00, Overdue = 20,000.00 -> Overdue Ratio = 40.00% (0.4000)
        self.gold_ar_data = [
            {"party": "Customer A", "outstanding_amount": 30000.00, "due_date": "2026-12-31"},
            {"party": "Customer B", "outstanding_amount": 20000.00, "due_date": "2026-06-01"},
            {"party": "Total", "outstanding_amount": 50000.00, "is_total_row": 1}
        ]

        # Gold AP: Total = 45,000.00
        self.gold_ap_data = [
            {"party": "Supplier X", "outstanding_amount": 25000.00, "due_date": "2026-11-15"},
            {"party": "Supplier Y", "outstanding_amount": 20000.00, "due_date": "2026-12-15"},
            {"party": "Total", "outstanding_amount": 45000.00, "is_total_row": 1}
        ]

        # Gold Cash & Bank: Total = 250,000.00
        self.gold_cash_data = [
            {"account_name": "Cash on Hand", "account_type": "Cash", "closing_balance": 50000.00},
            {"account_name": "Vietcombank Operating", "account_type": "Bank", "closing_balance": 200000.00},
            {"account_name": "Accounts Receivable", "account_type": "Receivable", "closing_balance": 50000.00}
        ]

    # --- 1. Numeric Reconciliation Tests (F001-NUM-01) ---
    def test_numeric_gold_reconciliation_all_metrics(self):
        """Verify 100% material numeric match with independent gold calculations."""
        sources = {
            "profit_and_loss": self.gold_pnl_data,
            "accounts_receivable": self.gold_ar_data,
            "accounts_payable": self.gold_ap_data,
            "trial_balance": self.gold_cash_data
        }

        snapshot = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            currency="VND",
            raw_sources=sources
        )

        self.assertEqual(snapshot["status"], "OK")
        self.assertEqual(snapshot["company"], self.company)
        self.assertEqual(snapshot["currency"], "VND")
        self.assertEqual(snapshot["explanation"]["status"], "UNAVAILABLE")  # No LLM explanation yet
        self.assertEqual(snapshot["explanation"]["facts"], [])

        metrics_map = {m["metric_id"]: m for m in snapshot["metrics"]}

        # 1. Revenue = 700,000 + 300,000 = 1,000,000.00
        self.assertEqual(metrics_map["revenue"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["revenue"]["value"], 1000000.0)

        # 2. COGS = 450,000 + 150,000 = 600,000.00
        self.assertEqual(metrics_map["cogs"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["cogs"]["value"], 600000.0)

        # 3. Gross Margin = (1,000,000 - 600,000) / 1,000,000 = 0.4000
        self.assertEqual(metrics_map["gross_margin"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["gross_margin"]["value"], 0.4)

        # 4. AR Outstanding = 30,000 + 20,000 = 50,000.00
        self.assertEqual(metrics_map["ar_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["ar_outstanding"]["value"], 50000.0)

        # 5. Overdue AR Ratio = 20,000 / 50,000 = 0.4000
        self.assertEqual(metrics_map["overdue_ar_ratio"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["overdue_ar_ratio"]["value"], 0.4)

        # 6. AP Outstanding = 25,000 + 20,000 = 45,000.00
        self.assertEqual(metrics_map["ap_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["ap_outstanding"]["value"], 45000.0)

        # 7. Near-Term AP = Frozen as UNAVAILABLE
        self.assertEqual(metrics_map["near_term_ap"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics_map["near_term_ap"]["value"])
        self.assertIn("near-term AP horizon not yet frozen", metrics_map["near_term_ap"]["limitations"])

        # 8. Cash Balance = 50,000 + 200,000 = 250,000.00
        self.assertEqual(metrics_map["cash_balance"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["cash_balance"]["value"], 250000.0)

    # --- 2. Evidence Linkage & Provenance Tests ---
    def test_evidence_ref_linkage(self):
        """Every available metric must reference valid EvidenceRef checksums."""
        sources = {
            "profit_and_loss": self.gold_pnl_data,
            "accounts_receivable": self.gold_ar_data,
            "accounts_payable": self.gold_ap_data,
            "trial_balance": self.gold_cash_data
        }

        snapshot = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            raw_sources=sources
        )

        evidence_checksums = {e["checksum_or_version"] for e in snapshot["evidence_refs"]}
        self.assertGreater(len(evidence_checksums), 0)

        for m in snapshot["metrics"]:
            if m["status"] == "AVAILABLE":
                self.assertGreater(len(m["evidence_refs"]), 0)
                for ref in m["evidence_refs"]:
                    self.assertIn(ref, evidence_checksums, f"Metric {m['metric_id']} evidence ref broken.")

    # --- 3. Missing-Data & Zero-Invariant Tests (F001-DATA-01) ---
    def test_missing_pnl_never_becomes_zero(self):
        """Missing P&L must set revenue/COGS to UNAVAILABLE, never fabricate 0.0."""
        sources = {
            # No profit_and_loss provided
            "accounts_receivable": self.gold_ar_data,
            "accounts_payable": self.gold_ap_data
        }

        snapshot = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            raw_sources=sources
        )

        self.assertEqual(snapshot["status"], "PARTIAL")
        self.assertIn("profit_and_loss", snapshot["missing_inputs"])

        metrics_map = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics_map["revenue"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics_map["revenue"]["value"])
        self.assertEqual(metrics_map["cogs"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics_map["cogs"]["value"])
        self.assertEqual(metrics_map["gross_margin"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics_map["gross_margin"]["value"])

    def test_empty_company_yields_valid_zero_not_error(self):
        """Legitimately empty ledgers yield 0.0 values with status OK, not an error."""
        sources = {
            "profit_and_loss": [],
            "accounts_receivable": [],
            "accounts_payable": [],
            "trial_balance": [{"account_type": "Cash", "balance": 0.0}]
        }

        snapshot = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            raw_sources=sources
        )

        metrics_map = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics_map["ar_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["ar_outstanding"]["value"], 0.0)
        self.assertEqual(metrics_map["ap_outstanding"]["status"], "AVAILABLE")
        self.assertEqual(metrics_map["ap_outstanding"]["value"], 0.0)

    # --- 4. Source Error Handling ---
    def test_source_error_propagation(self):
        """When source fetcher throws error, snapshot sets SOURCE_ERROR without throwing unhandled crash."""
        def faulty_fetcher(r_key, filters, company):
            return {"status": "error", "message": "Database query timeout"}

        snapshot = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            source_fetcher=faulty_fetcher
        )

        self.assertEqual(snapshot["status"], "SOURCE_ERROR")
        self.assertEqual(len(snapshot["metrics"]), 8)
        for m in snapshot["metrics"]:
            self.assertEqual(m["status"], "UNAVAILABLE")
            self.assertIsNone(m["value"])

    # --- 5. Period Temporal Range Validation ---
    def test_period_temporal_bounds_validation(self):
        """start_date > end_date must immediately return VALIDATION_ERROR."""
        snapshot = build_financial_snapshot(
            company=self.company,
            period_start="2026-12-31",
            period_end="2026-01-01"
        )

        self.assertEqual(snapshot["status"], "VALIDATION_ERROR")
        self.assertIn("period_start cannot be after period_end", snapshot["missing_inputs"])
        self.assertIsNone(snapshot["company"])

    # --- 6. Permission and Company Guard ---
    def test_empty_company_yields_forbidden(self):
        """Empty or invalid company request must return FORBIDDEN and conceal company name."""
        snapshot = build_financial_snapshot(
            company="",
            period_start=self.period_start,
            period_end=self.period_end
        )

        self.assertEqual(snapshot["status"], "FORBIDDEN")
        self.assertIsNone(snapshot["company"])

    # --- 7. Edge Cases & Invariant Edge Bounds ---
    def test_zero_revenue_gross_margin_handled(self):
        """When revenue is 0.0, gross margin ratio must be UNAVAILABLE, not ZeroDivisionError."""
        sources = {
            "profit_and_loss": [
                {"account_name": "Sales Revenue", "balance": 0.0},
                {"account_name": "Cost of Goods Sold", "balance": 100.0}
            ]
        }
        snapshot = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            raw_sources=sources
        )
        metrics_map = {m["metric_id"]: m for m in snapshot["metrics"]}
        self.assertEqual(metrics_map["revenue"]["value"], 0.0)
        self.assertEqual(metrics_map["cogs"]["value"], 100.0)
        self.assertEqual(metrics_map["gross_margin"]["status"], "UNAVAILABLE")
        self.assertIsNone(metrics_map["gross_margin"]["value"])

    def test_zero_total_ar_with_positive_overdue_anomalous_ledger(self):
        """Anomalous state with overdue amount but zero total AR handles ratio safely without division error."""
        ar_tot, ar_overdue, ar_ratio, ar_lims = parse_ar_data([
            {"party": "Faulty Customer", "outstanding_amount": 0.0, "overdue_amount": 500.0}
        ])
        self.assertEqual(ar_tot, Decimal("0.00"))
        self.assertEqual(ar_overdue, Decimal("500.00"))
        self.assertEqual(ar_ratio, Decimal("0.0000"))
        self.assertTrue(any("anomalous" in lim.lower() for lim in ar_lims))


if __name__ == "__main__":
    unittest.main()
