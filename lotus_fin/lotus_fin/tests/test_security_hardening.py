"""Narrow regression tests for shared pre-build security primitives."""

import json
import unittest
from unittest.mock import patch

import frappe

from lotus_fin.security.access import CompanyAccessError, check_report_permission, get_verified_company
from lotus_fin.ai.observability import log_ai002_event, log_event


class TestSecurityHardening(unittest.TestCase):
    def test_missing_and_forbidden_company_have_identical_public_denial(self):
        with patch("lotus_fin.security.access.frappe.db.exists", return_value=False):
            with self.assertRaisesRegex(CompanyAccessError, "^FORBIDDEN$"):
                get_verified_company("AI002 missing company", user="test@example.invalid")

        with patch("lotus_fin.security.access.frappe.db.exists", return_value=True):
            with patch("lotus_fin.security.access.has_permission", return_value=False):
                with self.assertRaisesRegex(CompanyAccessError, "^FORBIDDEN$"):
                    get_verified_company("AI002 private company", user="test@example.invalid")

    def test_missing_report_has_generic_denial(self):
        with patch("lotus_fin.security.access.frappe.db.exists", return_value=False):
            with self.assertRaisesRegex(frappe.PermissionError, "^FORBIDDEN$"):
                check_report_permission("AI002 secret report", user="test@example.invalid")

    def test_legacy_logger_drops_fake_pii_and_amount(self):
        event = log_event(
            "ai001_test_canary",
            "CID-12345",
            company="CANARY_AI002_COMPANY",
            user="canary@test.invalid",
            details={"party": "CANARY_AI002_PERSON", "amount": "987654321", "record_count": 2},
        )
        encoded = json.dumps(event)
        self.assertNotIn("CANARY_AI002_COMPANY", encoded)
        self.assertNotIn("CANARY_AI002_PERSON", encoded)
        self.assertNotIn("987654321", encoded)
        self.assertNotIn("canary@test.invalid", encoded)
        self.assertEqual(event["details"], {"record_count": 2})

    def test_ai002_logger_accepts_typed_metadata_only(self):
        event = log_ai002_event(
            event_type="ai002_source_read",
            correlation_id="CID-12345",
            status="PARTIAL",
            source_status="OK",
            coverage_scope="TRADE_ONLY",
            record_count=3,
        )
        self.assertEqual(event["feature_id"], "AI002")
        self.assertEqual(event["details"], {"source_status": "OK", "coverage_scope": "TRADE_ONLY", "record_count": 3})
        with self.assertRaises(TypeError):
            log_ai002_event(event_type="ai002_source_read", correlation_id="CID-12345", status="OK", party="CANARY_AI002_PERSON")


if __name__ == "__main__":
    unittest.main()
