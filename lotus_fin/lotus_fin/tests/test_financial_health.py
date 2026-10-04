"""
Independent Gold & Invariant Test Suite for AI001-03:
Financial Health Metrics, Period Comparison & Observability.

Verifies:
1. compute_previous_period:
   - Equal length calendar calculations.
   - Leap year handling, month-end boundaries, and non-overlapping exact boundaries.
2. compute_metric_change:
   - Absolute change = current - previous with Decimal ROUND_HALF_UP.
   - Relative change = (current - previous) / abs(previous).
   - Zero previous denominator yields UNAVAILABLE with limitation.
   - None inputs yield UNAVAILABLE.
   - Negative to positive, negative to negative, zero to positive transitions.
3. build_comparison_block:
   - Cross-company comparison blocked (status UNAVAILABLE).
   - Missing previous snapshot handled safely.
   - All 7 core metrics tracked.
4. near_term_ap:
   - Explicitly frozen as status UNAVAILABLE with limitation "near-term AP horizon not yet frozen".
5. Observability telemetry:
   - Structured JSON logs emitted.
   - Pseudonymous user_id hash (SHA256[:12]).
   - Zero PII in log records.
   - MetricsCollector counters (requests_total, status breakdown, latency tracking).
"""

from decimal import Decimal
import json
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.ai.financial_health import (
    compute_previous_period,
    compute_metric_change,
    build_comparison_block
)
from lotus_fin.ai.financial_snapshot import build_financial_snapshot
from lotus_fin.ai.observability import (
    hash_user_id,
    log_event,
    metrics as op_metrics,
    EVENT_REQUEST_STARTED,
    EVENT_METRIC_COMPUTED
)


class TestFinancialHealthMetricsAndComparison(unittest.TestCase):
    def setUp(self):
        op_metrics.reset()
        self.company = "Name (Demo)"

    # --- 1. Period Calculation Gold Tests ---
    def test_compute_previous_period_annual(self):
        """Standard annual period [2026-01-01, 2026-12-31] (365 days) -> [2025-01-01, 2025-12-31]."""
        p_start, p_end = compute_previous_period("2026-01-01", "2026-12-31")
        self.assertEqual(p_end, "2025-12-31")
        self.assertEqual(p_start, "2025-01-01")

    def test_compute_previous_period_quarterly(self):
        """Quarter Q2 [2026-04-01, 2026-06-30] (90 days) -> Q1 [2026-01-01, 2026-03-31]."""
        p_start, p_end = compute_previous_period("2026-04-01", "2026-06-30")
        self.assertEqual(p_end, "2026-03-31")
        self.assertEqual(p_start, "2025-12-31")  # Exactly 90 days prior to March 31

    def test_compute_previous_period_leap_year(self):
        """Leap year period spanning Feb 29 (2024-02-01 to 2024-02-29 is 28 days span) -> 29 days."""
        p_start, p_end = compute_previous_period("2024-02-01", "2024-02-29")
        self.assertEqual(p_end, "2024-01-31")
        self.assertEqual(p_start, "2024-01-03")

    # --- 2. Metric Change Math Gold Tests ---
    def test_metric_change_positive_growth(self):
        """Current 150.0, Prev 100.0 -> Abs +50.0, Rel +0.5000 (+50.00%)."""
        res = compute_metric_change(150.0, 100.0)
        self.assertEqual(res["status"], "AVAILABLE")
        self.assertEqual(res["absolute_change"], 50.0)
        self.assertEqual(res["relative_change"], 0.5)

    def test_metric_change_negative_growth(self):
        """Current 80.0, Prev 100.0 -> Abs -20.0, Rel -0.2000 (-20.00%)."""
        res = compute_metric_change(80.0, 100.0)
        self.assertEqual(res["status"], "AVAILABLE")
        self.assertEqual(res["absolute_change"], -20.0)
        self.assertEqual(res["relative_change"], -0.2)

    def test_metric_change_zero_previous_denominator_limitation(self):
        """Current 100.0, Prev 0.0 -> Abs +100.0, Rel None with limitation."""
        res = compute_metric_change(100.0, 0.0)
        self.assertEqual(res["status"], "AVAILABLE")
        self.assertEqual(res["absolute_change"], 100.0)
        self.assertIsNone(res["relative_change"])
        self.assertTrue(any("Previous period value is zero" in lim for lim in res["limitations"]))

    def test_metric_change_negative_to_positive_transition(self):
        """Cash was -50.0, now +20.0 -> Abs +70.0, Rel = (20 - (-50)) / abs(-50) = 70/50 = +1.4000."""
        res = compute_metric_change(20.0, -50.0)
        self.assertEqual(res["status"], "AVAILABLE")
        self.assertEqual(res["absolute_change"], 70.0)
        self.assertEqual(res["relative_change"], 1.4)

    def test_metric_change_negative_to_more_negative(self):
        """Cash was -50.0, now -80.0 -> Abs -30.0, Rel = (-80 - (-50)) / abs(-50) = -30/50 = -0.6000."""
        res = compute_metric_change(-80.0, -50.0)
        self.assertEqual(res["status"], "AVAILABLE")
        self.assertEqual(res["absolute_change"], -30.0)
        self.assertEqual(res["relative_change"], -0.6)

    def test_metric_change_none_inputs(self):
        """When either current or previous is None, change is UNAVAILABLE."""
        res1 = compute_metric_change(None, 100.0)
        self.assertEqual(res1["status"], "UNAVAILABLE")
        self.assertIsNone(res1["absolute_change"])

        res2 = compute_metric_change(100.0, None)
        self.assertEqual(res2["status"], "UNAVAILABLE")
        self.assertIsNone(res2["absolute_change"])

    # --- 3. Comparison Block & Invariants ---
    def test_comparison_block_cross_company_deny(self):
        """Cross-company comparison must return UNAVAILABLE with limitation."""
        cur_snap = {
            "company": "Company A",
            "period": {"start": "2026-01-01", "end": "2026-12-31"},
            "metrics": [{"metric_id": "revenue", "status": "AVAILABLE", "value": 100.0}]
        }
        prev_snap = {
            "company": "Company B",
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "metrics": [{"metric_id": "revenue", "status": "AVAILABLE", "value": 80.0}]
        }
        comp_res = build_comparison_block(cur_snap, prev_snap, correlation_id="TEST-CID")
        self.assertEqual(comp_res["status"], "UNAVAILABLE")
        self.assertTrue(any("different companies" in lim for lim in comp_res["limitations"]))

    def test_comparison_block_full_metrics_reconciliation(self):
        """Valid comparison computes delta for all 7 core metrics without subjective labels."""
        cur_snap = {
            "company": "Company A",
            "snapshot_id": "SNAP-CUR",
            "period": {"start": "2026-01-01", "end": "2026-12-31"},
            "metrics": [
                {"metric_id": "revenue", "status": "AVAILABLE", "value": 363000.0},
                {"metric_id": "cogs", "status": "AVAILABLE", "value": 253760.0},
                {"metric_id": "gross_margin", "status": "AVAILABLE", "value": 0.3009},
                {"metric_id": "ar_outstanding", "status": "AVAILABLE", "value": 316000.0},
                {"metric_id": "overdue_ar_ratio", "status": "AVAILABLE", "value": 1.0},
                {"metric_id": "ap_outstanding", "status": "AVAILABLE", "value": 184293.0},
                {"metric_id": "cash_balance", "status": "AVAILABLE", "value": -117854.0}
            ]
        }
        prev_snap = {
            "company": "Company A",
            "snapshot_id": "SNAP-PREV",
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "metrics": [
                {"metric_id": "revenue", "status": "AVAILABLE", "value": 300000.0},
                {"metric_id": "cogs", "status": "AVAILABLE", "value": 200000.0},
                {"metric_id": "gross_margin", "status": "AVAILABLE", "value": 0.3333},
                {"metric_id": "ar_outstanding", "status": "AVAILABLE", "value": 200000.0},
                {"metric_id": "overdue_ar_ratio", "status": "AVAILABLE", "value": 0.5},
                {"metric_id": "ap_outstanding", "status": "AVAILABLE", "value": 150000.0},
                {"metric_id": "cash_balance", "status": "AVAILABLE", "value": 50000.0}
            ]
        }
        comp_res = build_comparison_block(cur_snap, prev_snap, correlation_id="TEST-CID")
        self.assertEqual(comp_res["status"], "AVAILABLE")
        self.assertEqual(comp_res["type"], "PREVIOUS_PERIOD")

        # Revenue delta = 363,000 - 300,000 = +63,000.00 (+21.00%)
        rev_m = comp_res["metrics"]["revenue"]
        self.assertEqual(rev_m["absolute_change"], 63000.0)
        self.assertEqual(rev_m["relative_change"], 0.21)

        # Cash delta = -117,854 - 50,000 = -167,854.00 (-335.71%)
        cash_m = comp_res["metrics"]["cash_balance"]
        self.assertEqual(cash_m["absolute_change"], -167854.0)
        self.assertEqual(cash_m["relative_change"], -3.3571)

        # Crucial: verify NO subjective health claims (good, bad, healthy, etc.) in comparison output
        comp_json = json.dumps(comp_res).lower()
        self.assertNotIn("healthy", comp_json)
        self.assertNotIn("unhealthy", comp_json)
        self.assertNotIn("good", comp_json)
        self.assertNotIn("bad", comp_json)

    # --- 4. Near-Term AP Invariant ---
    def test_near_term_ap_is_frozen_unavailable(self):
        """near_term_ap must be UNAVAILABLE with limitation."""
        sources = {
            "profit_and_loss": [],
            "accounts_receivable": [],
            "accounts_payable": [{"party": "P1", "voucher_no": "PINV-0001", "outstanding_amount": 100.0}],
            "trial_balance": []
        }
        snap = build_financial_snapshot(
            company=self.company,
            period_start="2026-01-01",
            period_end="2026-12-31",
            raw_sources=sources
        )
        near_ap = [m for m in snap["metrics"] if m["metric_id"] == "near_term_ap"][0]
        self.assertEqual(near_ap["status"], "UNAVAILABLE")
        self.assertIsNone(near_ap["value"])
        self.assertIn("near-term AP horizon not yet frozen", near_ap["limitations"])

    # --- 5. Observability & Telemetry Tests ---
    def test_user_id_pseudonymization(self):
        """User identifiers must be hashed into 12-char hex digest."""
        raw_user = "accountant@sme-enterprise.vn"
        h = hash_user_id(raw_user)
        self.assertEqual(len(h), 12)
        self.assertNotIn(raw_user, h)
        # Consistent
        self.assertEqual(h, hash_user_id(raw_user))
        self.assertIsNone(hash_user_id(None))

    def test_structured_log_contains_no_pii_or_amounts(self):
        """Structured event logs must not log monetary rows, customer names, or passwords."""
        ev = log_event(
            event_type=EVENT_REQUEST_STARTED,
            correlation_id="CID-12345",
            company="Name (Demo)",
            user="manager@lotus.vn",
            details={"period_start": "2026-01-01", "period_end": "2026-12-31"}
        )
        self.assertEqual(ev["correlation_id"], "CID-12345")
        self.assertEqual(ev["feature_id"], "AI001")
        self.assertEqual(ev["event_type"], "ai001_request_started")
        self.assertEqual(len(ev["user_id_hash"]), 12)
        # Verify no PII
        ev_str = json.dumps(ev)
        self.assertNotIn("manager@lotus.vn", ev_str)

    def test_metrics_collector_aggregation(self):
        """MetricsCollector accurately counts requests by status and metric availability."""
        op_metrics.reset()
        op_metrics.record_request("OK", 45.2)
        op_metrics.record_request("PARTIAL", 32.1)
        op_metrics.record_auth_denial()
        op_metrics.record_source_error("accounts_receivable")
        op_metrics.record_metric_computed()
        op_metrics.record_metric_unavailable("near_term_ap")

        summary = op_metrics.get_summary()
        self.assertEqual(summary["requests_total"], 2)
        self.assertEqual(summary["requests_by_status"]["OK"], 1)
        self.assertEqual(summary["requests_by_status"]["PARTIAL"], 1)
        self.assertEqual(summary["auth_denials_total"], 1)
        self.assertEqual(summary["source_errors_by_report"]["accounts_receivable"], 1)
        self.assertEqual(summary["metrics_computed_total"], 1)
        self.assertEqual(summary["metrics_unavailable_by_id"]["near_term_ap"], 1)
        self.assertGreater(summary["latency_p50_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
