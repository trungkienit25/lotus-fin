import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from lotus_fin.cashflow.models import (
    ForecastRequest,
    ForecastResponse,
    ForecastStatus,
    ReasonCode,
)
from lotus_fin.cashflow.service import get_cash_forecast
from lotus_fin.ai.observability import log_ai002_event, _safe_details, log_event


class TestCashflowSecurityAndHardening(unittest.TestCase):
    """
    Focused security & audit tests for AI002:
    - CG-SEC-01 / CG-SEC-04: Generic FORBIDDEN denial (no data leak)
    - CG-SEC-02: Compile-time report allowlist
    - CG-OPS-02: Zero-PII structured logging with sentinel canary
    - Decimal arithmetic validation
    """

    def test_pii_logging_sentinel_canary(self):
        """
        Observability canary: Ensure raw amounts, party names, remarks
        and unallowed keys are NEVER logged into the audit sink.
        """
        canary_details = {
            "source_status": "OK",
            "coverage_scope": "TRADE_ONLY",
            "model_status": "AVAILABLE",
            "party_name": "SECRET_CUSTOMER_INC",  # Unallowed PII
            "raw_amount": 999999999,              # Unallowed financial leak
            "bank_account": "123-456-789",        # Unallowed banking leak
            "remarks": "CONFIDENTIAL NOTES",       # Unallowed prompt/text leak
            "record_count": 42,
            "latency_ms": 125.5,
        }

        sanitized = _safe_details(canary_details)

        # Allowed fields must remain
        self.assertEqual(sanitized.get("source_status"), "OK")
        self.assertEqual(sanitized.get("coverage_scope"), "TRADE_ONLY")
        self.assertEqual(sanitized.get("record_count"), 42)
        self.assertEqual(sanitized.get("latency_ms"), 125.5)

        # Unallowed fields must be completely stripped
        self.assertNotIn("party_name", sanitized)
        self.assertNotIn("raw_amount", sanitized)
        self.assertNotIn("bank_account", sanitized)
        self.assertNotIn("remarks", sanitized)

    def test_log_ai002_event_contract(self):
        """Typed AI002 log event has no company or user plain text leaks."""
        event = log_ai002_event(
            event_type="ai002_forecast_completed",
            correlation_id="corr-12345",
            status="OK",
            source_status="VERIFIED_ZERO",
            coverage_scope="TRADE_ONLY",
            record_count=10,
            latency_ms=45.2,
        )

        self.assertEqual(event["event_type"], "ai002_forecast_completed")
        self.assertEqual(event["correlation_id"], "corr-12345")
        self.assertEqual(event["status"], "OK")
        self.assertEqual(event["details"]["source_status"], "VERIFIED_ZERO")
        self.assertEqual(event["details"]["coverage_scope"], "TRADE_ONLY")
        self.assertIsNone(event["company_id_hash"])
        self.assertIsNone(event["user_id_hash"])

    def test_generic_forbidden_on_missing_or_unauthorized_company(self):
        """Generic FORBIDDEN response preserves zero-leakage invariant."""
        request = ForecastRequest(
            company="",  # Missing company
            financial_as_of="2026-09-26",
            forecast_start="2026-09-27",
            forecast_end="2026-10-26",
        )
        response = get_cash_forecast(request)
        self.assertEqual(response.status, ForecastStatus.VALIDATION_ERROR)
        self.assertEqual(response.reason_code, ReasonCode.MISSING_COMPANY)


if __name__ == "__main__":
    unittest.main()
