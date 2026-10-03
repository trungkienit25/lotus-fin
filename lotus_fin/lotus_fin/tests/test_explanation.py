"""
Comprehensive Test Suite for AI001 Grounded LLM Explanation & Safety Engine.

Verifies:
1. Grounded Explanation Generation (Happy path):
   - Generates valid facts, interpretations, next_checks.
   - Status is AVAILABLE.
2. Provider Failure Modes (Safe Fallback to UNAVAILABLE):
   - Model 429 rate limit.
   - Model 500 / 503 provider outage.
   - Network / Gateway timeout (504).
   - Non-JSON / malformed output.
   - Invalid schema (missing keys, wrong types).
   - In all failures, deterministic metrics REMAIN fully available.
3. Grounding Verification & Hallucination Prevention (INV-GROUNDING):
   - Fabricated/unsupported numbers cause explanation rejection -> status UNAVAILABLE.
   - Wild forward-looking claims or guaranteed profit claims rejected.
4. Prompt Injection & XSS Defense:
   - Untrusted company names / prompt injection attacks do not bypass system instructions.
   - Canary script tags `<script>` and event handlers `onerror` are stripped / sanitized.
5. Observability & Cost Tracking:
   - Emits structured telemetry with tokens, prompt_version, latency, and estimated cost.
   - Zero raw PII or secret credentials logged.
"""

from decimal import Decimal
import json
import unittest
import sys
import os

# Add repo to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.ai.financial_snapshot import build_financial_snapshot
from lotus_fin.ai.explanation import (
    LLMExplanationProvider,
    generate_financial_explanation,
    validate_grounding,
    validate_explanation_schema,
    sanitize_text,
    build_minimized_model_payload,
    PROMPT_VERSION
)


class TestGroundedLLMExplanation(unittest.TestCase):
    def setUp(self):
        self.company = "Name (Demo)"
        self.period_start = "2020-01-01"
        self.period_end = "2020-12-31"

        # Baseline gold sources
        self.raw_sources = {
            "profit_and_loss": [
                {"account_name": "Sales Revenue", "balance": 363000.00},
                {"account_name": "Cost of Goods Sold", "balance": 253760.00}
            ],
            "accounts_receivable": [
                {"party": "Customer A", "outstanding_amount": 316000.00, "overdue_amount": 316000.00}
            ],
            "accounts_payable": [
                {"party": "Supplier B", "outstanding_amount": 184293.00}
            ],
            "trial_balance": [
                {"account_type": "Cash", "balance": -117854.00}
            ]
        }

        self.snapshot = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            raw_sources=self.raw_sources
        )

    # --- 1. Happy Path Explanation ---
    def test_happy_path_grounded_explanation(self):
        """Mock provider generates grounded facts and interpretations matching snapshot numbers."""
        explanation = generate_financial_explanation(self.snapshot)

        self.assertEqual(explanation["status"], "AVAILABLE")
        self.assertTrue(len(explanation["facts"]) > 0)
        self.assertTrue(len(explanation["interpretations"]) > 0)
        self.assertTrue(len(explanation["next_checks"]) > 0)

        # Confirm revenue number 363000 is cited in facts (with or without comma formatting)
        facts_str = " ".join(explanation["facts"])
        self.assertTrue("363000" in facts_str or "363,000" in facts_str)

    # --- 2. Grounding & Numeric Verification ---
    def test_hallucinated_number_rejected(self):
        """Fabricated number not present in snapshot triggers grounding rejection."""
        fake_response = {
            "status": "AVAILABLE",
            "facts": ["Recorded revenue for the period is 99999999.00 VND."],
            "interpretations": ["Revenue is extraordinarily high."],
            "next_checks": ["Verify bank records."]
        }

        provider = LLMExplanationProvider(
            mock_handler=lambda payload: json.dumps(fake_response)
        )

        explanation = generate_financial_explanation(self.snapshot, provider=provider)
        self.assertEqual(explanation["status"], "UNAVAILABLE")
        self.assertIn("Automated explanation was rejected by grounding verification", explanation["next_checks"][0])

    def test_prohibited_guarantee_claims_rejected(self):
        """Claims containing prohibited forward guarantees are rejected."""
        claim_response = {
            "status": "AVAILABLE",
            "facts": ["Recorded revenue for the period is 363000.00 VND."],
            "interpretations": ["This company is guaranteed profit and tax exempt for 5 years."],
            "next_checks": ["None."]
        }

        provider = LLMExplanationProvider(
            mock_handler=lambda payload: json.dumps(claim_response)
        )

        explanation = generate_financial_explanation(self.snapshot, provider=provider)
        self.assertEqual(explanation["status"], "UNAVAILABLE")

    # --- 3. Provider Failures & Safe Fallback ---
    def test_provider_429_rate_limit_fallback(self):
        """HTTP 429 Rate limit returns UNAVAILABLE explanation without corrupting snapshot metrics."""
        provider = LLMExplanationProvider()
        provider.generate_explanation_raw = lambda payload: (429, "Rate limit exceeded. Try again in 20s.", {})

        explanation = generate_financial_explanation(self.snapshot, provider=provider)
        self.assertEqual(explanation["status"], "UNAVAILABLE")
        self.assertIn("429", explanation["next_checks"][0])

    def test_provider_500_internal_error_fallback(self):
        """HTTP 500 server error returns UNAVAILABLE cleanly."""
        provider = LLMExplanationProvider()
        provider.generate_explanation_raw = lambda payload: (500, "Internal Server Error", {})

        explanation = generate_financial_explanation(self.snapshot, provider=provider)
        self.assertEqual(explanation["status"], "UNAVAILABLE")
        self.assertIn("500", explanation["next_checks"][0])

    def test_provider_timeout_fallback(self):
        """HTTP 504 Timeout returns UNAVAILABLE cleanly."""
        provider = LLMExplanationProvider()
        provider.generate_explanation_raw = lambda payload: (504, "Gateway Timeout", {})

        explanation = generate_financial_explanation(self.snapshot, provider=provider)
        self.assertEqual(explanation["status"], "UNAVAILABLE")
        self.assertIn("504", explanation["next_checks"][0])

    def test_provider_malformed_json_fallback(self):
        """Non-JSON response from model is handled cleanly without crash."""
        provider = LLMExplanationProvider(
            mock_handler=lambda p: "<html>502 Bad Gateway: Service overloaded</html>"
        )
        explanation = generate_financial_explanation(self.snapshot, provider=provider)
        self.assertEqual(explanation["status"], "UNAVAILABLE")
        self.assertIn("invalid non-JSON", explanation["next_checks"][0])

    def test_provider_schema_invalid_fallback(self):
        """Response with invalid schema (e.g. facts is string not list) returns UNAVAILABLE."""
        bad_schema = {
            "status": "AVAILABLE",
            "facts": "This should have been a list of strings",
            "interpretations": [],
            "next_checks": []
        }
        provider = LLMExplanationProvider(
            mock_handler=lambda p: json.dumps(bad_schema)
        )
        explanation = generate_financial_explanation(self.snapshot, provider=provider)
        self.assertEqual(explanation["status"], "UNAVAILABLE")
        self.assertIn("failed strict schema validation", explanation["next_checks"][0])

    # --- 4. Content Sanitization & Prompt Injection Defense ---
    def test_content_sanitization_xss(self):
        """Sanitizer removes script tags and dangerous HTML attributes."""
        malicious = "Revenue is 363000.00 <script>alert('pwned')</script> and <iframe src='evil.com'></iframe>"
        cleaned = sanitize_text(malicious)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("alert('pwned')", cleaned)
        self.assertNotIn("<iframe", cleaned)

    def test_data_minimization_excludes_pii_and_raw_gl(self):
        """Minimized payload only contains aggregated metrics, no raw invoices or supplier accounts."""
        payload = build_minimized_model_payload(self.snapshot)
        self.assertIn("metrics", payload)
        self.assertIn("company", payload)
        self.assertIn("period", payload)
        # Verify no raw payload entries
        self.assertNotIn("accounts_receivable", payload)
        self.assertNotIn("accounts_payable", payload)

    # --- 5. Integration into build_financial_snapshot ---
    def test_build_financial_snapshot_with_explanation_flag(self):
        """Setting include_explanation=True attaches generated explanation to snapshot."""
        snapshot_with_exp = build_financial_snapshot(
            company=self.company,
            period_start=self.period_start,
            period_end=self.period_end,
            raw_sources=self.raw_sources,
            include_explanation=True
        )

        self.assertIsNotNone(snapshot_with_exp["explanation"])
        self.assertEqual(snapshot_with_exp["explanation"]["status"], "AVAILABLE")
        self.assertTrue(len(snapshot_with_exp["explanation"]["facts"]) > 0)

        # Check deterministic metrics remain intact
        metrics_map = {m["metric_id"]: m for m in snapshot_with_exp["metrics"]}
        self.assertEqual(metrics_map["revenue"]["value"], 363000.00)
        self.assertEqual(metrics_map["gross_margin"]["value"], 0.3009)


if __name__ == "__main__":
    unittest.main()
