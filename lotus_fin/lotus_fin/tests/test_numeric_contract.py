"""
Numeric contract regression for AI001 snapshot metrics (architecture-refactor
remediation R1).

Locks the approved foundation numeric behavior (86208f4):
- Revenue=100, COGS=0  -> gross_margin = 1.0 AVAILABLE (zero-COGS is a verified
  zero, never a missing value; guards against Decimal truthiness regressions).
- Revenue=0            -> gross_margin UNAVAILABLE with the explicit
  "Revenue is zero or negative" limitation.
- Missing COGS row     -> gross_margin UNAVAILABLE with the explicit
  "Requires both Revenue and COGS" limitation.
- Gold P&L ratio quantization to 4 decimal places (ROUND_HALF_UP).
"""

import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.ai.financial_snapshot import build_financial_snapshot
from lotus_fin.core.use_cases.metric_assembler import MetricAssembler


PERIOD = {"start": "2026-01-01", "end": "2026-12-31"}


def _assemble(pnl_rows, extra_sources=None):
    sources = {"profit_and_loss": {"status": "success", "data": pnl_rows}}
    sources.update(extra_sources or {})
    metrics, _, _, _ = MetricAssembler.assemble(
        "Test Co", PERIOD["start"], PERIOD["end"], "2026-01-01T00:00:00Z",
        "VND", "SNAP-TEST", dict(PERIOD), sources, {}, {}
    )
    return {m["metric_id"]: m for m in metrics}


def _snapshot(pnl_rows, extra_sources=None):
    sources = {"profit_and_loss": {"status": "success", "data": pnl_rows}}
    sources.update(extra_sources or {})
    return build_financial_snapshot(
        company="Test Co",
        period_start=PERIOD["start"],
        period_end=PERIOD["end"],
        raw_sources=sources,
    )


class TestGrossMarginZeroCogsContract(unittest.TestCase):
    """R1: zero-COGS regression — the metric gate must stay AVAILABLE."""

    def test_revenue_100_cogs_0_is_margin_one_available(self):
        """The exact SSOT controlled replay: Revenue=100, COGS=0 -> 1.0."""
        row = _assemble([
            {"account_name": "Sales Revenue", "balance": 100.0},
            {"account_name": "Cost of Goods Sold", "balance": 0.0},
        ])
        gm = row["gross_margin"]
        self.assertEqual(gm["status"], "AVAILABLE")
        self.assertEqual(gm["value"], 1.0)
        self.assertEqual(gm["limitations"], [])
        self.assertEqual(row["cogs"]["status"], "AVAILABLE")
        self.assertEqual(row["cogs"]["value"], 0.0)

    def test_zero_cogs_via_public_snapshot_envelope(self):
        """End-to-end through build_financial_snapshot: zero-COGS stays
        AVAILABLE and the overall status remains OK."""
        snap = _snapshot(
            [
                {"account_name": "Sales Revenue", "balance": 100.0},
                {"account_name": "Cost of Goods Sold", "balance": 0.0},
            ],
            extra_sources={
                "accounts_receivable": [],
                "accounts_payable": [],
                "trial_balance": [{"account_name": "Cash on Hand", "account_type": "Cash", "closing_balance": 50000.0}],
            },
        )
        metrics = {m["metric_id"]: m for m in snap["metrics"]}
        self.assertEqual(metrics["gross_margin"]["status"], "AVAILABLE")
        self.assertEqual(metrics["gross_margin"]["value"], 1.0)
        self.assertEqual(snap["status"], "OK")


class TestGrossMarginNumericBoundaries(unittest.TestCase):
    """Foundation limitation branches and Decimal quantization contract."""

    def test_gold_margin_quantized_to_four_places(self):
        row = _assemble([
            {"account_name": "Sales Revenue", "balance": 1000000.0},
            {"account_name": "Cost of Goods Sold", "balance": 600000.0},
        ])
        gm = row["gross_margin"]
        self.assertEqual(gm["status"], "AVAILABLE")
        self.assertEqual(gm["value"], 0.4)
        self.assertEqual(Decimal(str(gm["value"])).as_tuple().exponent >= -4, True)

    def test_zero_revenue_is_unavailable_with_explicit_limitation(self):
        row = _assemble([
            {"account_name": "Sales Revenue", "balance": 0.0},
            {"account_name": "Cost of Goods Sold", "balance": 10.0},
        ])
        gm = row["gross_margin"]
        self.assertEqual(gm["status"], "UNAVAILABLE")
        self.assertIsNone(gm["value"])
        self.assertEqual(
            gm["limitations"],
            ["Revenue is zero or negative; gross margin ratio undefined."],
        )

    def test_missing_cogs_row_is_unavailable_with_explicit_limitation(self):
        row = _assemble([{"account_name": "Sales Revenue", "balance": 100.0}])
        gm = row["gross_margin"]
        self.assertEqual(gm["status"], "UNAVAILABLE")
        self.assertIsNone(gm["value"])
        self.assertEqual(
            gm["limitations"],
            ["Requires both Revenue and COGS to calculate gross margin."],
        )

    def test_missing_pnl_source_yields_typed_unavailable_metrics(self):
        row = _assemble([], extra_sources={})
        for m_id in ("revenue", "cogs", "gross_margin"):
            self.assertEqual(row[m_id]["status"], "UNAVAILABLE")

    def test_negative_margin_survives_truthiness_guards(self):
        """COGS > Revenue is a legitimate verified ratio (negative margin)."""
        row = _assemble([
            {"account_name": "Sales Revenue", "balance": 100.0},
            {"account_name": "Cost of Goods Sold", "balance": 150.0},
        ])
        gm = row["gross_margin"]
        self.assertEqual(gm["status"], "AVAILABLE")
        self.assertEqual(gm["value"], -0.5)


if __name__ == "__main__":
    unittest.main()
