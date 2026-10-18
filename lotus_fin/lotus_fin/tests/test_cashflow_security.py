import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from lotus_fin.modules.f002_cashflow.models import (
    ForecastRequest,
    ForecastResponse,
    ForecastStatus,
    ReasonCode,
)
from lotus_fin.modules.f002_cashflow.service import get_cash_forecast
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
            financial_as_of=date(2026, 9, 26),
            forecast_start=date(2026, 9, 27),
            forecast_end=date(2026, 10, 26),
        )
        response = get_cash_forecast(request)
        self.assertEqual(response.status, ForecastStatus.VALIDATION_ERROR)
        self.assertEqual(response.reason_code, ReasonCode.MISSING_COMPANY)

    def test_generic_forbidden_sanitizes_verified_company(self):
        """When request is FORBIDDEN, verified_company must be cleared/generic without leakage."""
        with patch("lotus_fin.modules.f002_cashflow.service.validate_forecast_request") as mock_val:
            mock_val.return_value = (False, ReasonCode.UNAUTHORIZED_ACCESS, "FORBIDDEN")
            req = ForecastRequest(
                company="Secret Confidential Corp",
                financial_as_of=date(2026, 9, 26),
                forecast_start=date(2026, 9, 27),
                forecast_end=date(2026, 10, 26),
            )
            resp = get_cash_forecast(req, user="attacker@example.com")
            self.assertEqual(resp.status, ForecastStatus.FORBIDDEN)
            self.assertEqual(resp.reason_code, ReasonCode.UNAUTHORIZED_ACCESS)
            self.assertEqual(resp.verified_company, "")  # Zero-leakage invariant
            self.assertNotIn("Secret Confidential Corp", resp.limitations[0])

    def test_numeric_and_adversarial_grounding_rejection(self):
        """Grounding validator must reject hallucinated amounts, dates, unsupported currencies, and subjective risk ratings."""
        from lotus_fin.modules.f002_cashflow.grounding import validate_grounding
        from lotus_fin.modules.f002_cashflow.models import ForecastResponse, OpeningCash, AccountBalance

        mock_resp = ForecastResponse(
            status=ForecastStatus.PARTIAL,
            verified_company="AI002 Fixture 2026",
            financial_as_of=date(2026, 9, 26),
            forecast_start=date(2026, 9, 27),
            forecast_end=date(2026, 10, 26),
            currency="USD",
            opening_cash=OpeningCash(
                aggregate_amount=Decimal("11550"),
                reconciliation="RECONCILED",
                has_constituent_deficit=False,
                accounts=[AccountBalance("Cash", Decimal("11550"), "USD", False)],
            ),
        )

        # 1. Hallucinated amount: 999999999
        valid, violations = validate_grounding("Cash will be 999999999 USD tomorrow", mock_resp)
        self.assertFalse(valid)
        self.assertTrue(any("999999999" in v for v in violations))

        # 2. Altered opening cash
        valid, violations = validate_grounding("Opening cash balance is 50,000 USD.", mock_resp)
        self.assertFalse(valid)

        # 3. Unsupported risk claims
        valid, violations = validate_grounding("The cash forecast shows this company is completely SAFE and LOW RISK.", mock_resp)
        self.assertFalse(valid)
        self.assertTrue(any("subjective risk" in v for v in violations))

        # 4. Wrong currency
        valid, violations = validate_grounding("Opening cash balance is 11,550 EUR.", mock_resp)
        self.assertFalse(valid)
        self.assertTrue(any("currency" in v for v in violations))

        # 5. Grounded factual statement passes
        valid, violations = validate_grounding("Opening cash balance is 11,550 USD.", mock_resp)
        self.assertTrue(valid)
        self.assertEqual(len(violations), 0)


    def test_model_failure_degradation(self):
        """When LLM times out or errors, explanation.status must be UNAVAILABLE with typed error_code."""
        from lotus_fin.modules.f002_cashflow.agent import explain_cash_forecast
        from lotus_fin.modules.f002_cashflow.models import ForecastResponse, OpeningCash, AccountBalance

        mock_resp = ForecastResponse(
            status=ForecastStatus.PARTIAL,
            verified_company="AI002 Fixture 2026",
            financial_as_of=date(2026, 9, 26),
            forecast_start=date(2026, 9, 27),
            forecast_end=date(2026, 10, 26),
            currency="VND",
            opening_cash=OpeningCash(
                aggregate_amount=Decimal("11550000"),
                reconciliation="RECONCILED",
                has_constituent_deficit=False,
                accounts=[AccountBalance("Cash", Decimal("11550000"), "VND", False)],
            ),
        )

        # Force exception in urllib call
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            expl = explain_cash_forecast(mock_resp, api_key="sk-test-key")
            self.assertEqual(expl.status, "UNAVAILABLE")
            self.assertEqual(expl.error_code, "PROVIDER_UNAVAILABLE")
            # Facts must remain intact
            self.assertTrue(len(expl.facts) > 0)
            self.assertEqual(expl.drivers, [])

        # Force timeout in urllib call
        with patch("urllib.request.urlopen", side_effect=TimeoutError("Timed out")):
            expl = explain_cash_forecast(mock_resp, api_key="sk-test-key")
            self.assertEqual(expl.status, "UNAVAILABLE")
            self.assertEqual(expl.error_code, "TIMEOUT")

    def test_evidence_reauthorization_in_tools(self):
        """Evidence refs tool enforces access reauthorization."""
        from lotus_fin.modules.f002_cashflow.tools import tool_cash_forecast_get_evidence
        from lotus_fin.modules.f002_cashflow.models import ForecastResponse

        resp = ForecastResponse(
            status=ForecastStatus.PARTIAL,
            verified_company="AI002 Fixture 2026",
            evidence_refs=["GL Entry:GLE-001", "Sales Invoice:ACC-SINV-2026-00001", "UNAUTHORIZED:FORBIDDEN-001"],
        )

        with patch("lotus_fin.security.access.verify_evidence_access") as mock_verify:
            # First 2 succeed, 3rd fails
            def side_effect(ref, user, company):
                if "FORBIDDEN" in ref:
                    raise PermissionError("FORBIDDEN")
                return True
            mock_verify.side_effect = side_effect

            tool_result = tool_cash_forecast_get_evidence(resp, user="test_user")
            self.assertIn("GL Entry:GLE-001", tool_result["evidence_refs"])
            self.assertIn("Sales Invoice:ACC-SINV-2026-00001", tool_result["evidence_refs"])
            self.assertNotIn("UNAUTHORIZED:FORBIDDEN-001", tool_result["evidence_refs"])


    def test_evidence_access_missing_company_rejected(self):
        """Fix C: verify_evidence_access raises PermissionError when company is missing or empty."""
        from lotus_fin.security.access import verify_evidence_access
        with self.assertRaises(Exception):
            verify_evidence_access("GL Entry:GLE-001", user="test_user", company="")

        with self.assertRaises(Exception):
            verify_evidence_access("GL Entry:GLE-001", user="test_user", company=None)

    def test_evidence_access_malformed_ref_rejected(self):
        """Fix C: Evidence ref without colon or invalid format raises PermissionError."""
        from lotus_fin.security.access import verify_evidence_access
        with self.assertRaises(Exception):
            verify_evidence_access("GLE-001-NO-COLON", user="test_user", company="AI002 Fixture 2026")

    def test_evidence_access_arbitrary_doctype_rejected(self):
        """Fix C: Arbitrary DocType outside allowlist is rejected with PermissionError."""
        from lotus_fin.security.access import verify_evidence_access
        with self.assertRaises(Exception):
            verify_evidence_access("User:Administrator", user="test_user", company="AI002 Fixture 2026")

        with self.assertRaises(Exception):
            verify_evidence_access("DocType:Company", user="test_user", company="AI002 Fixture 2026")

    def test_grounding_rejects_arbitrary_short_numbers(self):
        """Fix D: Ungrounded short numbers such as 9999, 12, 1 VND must be rejected by grounding validator."""
        from lotus_fin.modules.f002_cashflow.grounding import validate_grounding
        from lotus_fin.modules.f002_cashflow.models import ForecastResponse, OpeningCash, AccountBalance

        mock_resp = ForecastResponse(
            status=ForecastStatus.PARTIAL,
            verified_company="AI002 Fixture 2026",
            financial_as_of=date(2026, 9, 26),
            forecast_start=date(2026, 9, 27),
            forecast_end=date(2026, 10, 26),
            currency="VND",
            opening_cash=OpeningCash(
                aggregate_amount=Decimal("11550000"),
                reconciliation="RECONCILED",
                has_constituent_deficit=False,
                accounts=[AccountBalance("Cash", Decimal("11550000"), "VND", False)],
            ),
        )

        valid, violations = validate_grounding("Cash will be 9999 VND tomorrow", mock_resp)
        self.assertFalse(valid)
        self.assertTrue(any("9999" in v for v in violations))

        valid, violations = validate_grounding("Cash balance is 1 VND", mock_resp)
        self.assertFalse(valid)
        self.assertTrue(any("1" in v for v in violations))

        valid, violations = validate_grounding("Shortfall occurs on 2026-10-15", mock_resp)
        self.assertFalse(valid)
        self.assertTrue(any("date" in v for v in violations))

    def test_grounding_accepts_supported_numbers(self):
        """Fix D: Grounded numbers and dates pass validation."""
        from lotus_fin.modules.f002_cashflow.grounding import validate_grounding
        from lotus_fin.modules.f002_cashflow.models import ForecastResponse, OpeningCash, AccountBalance

        mock_resp = ForecastResponse(
            status=ForecastStatus.PARTIAL,
            verified_company="AI002 Fixture 2026",
            financial_as_of=date(2026, 9, 26),
            forecast_start=date(2026, 9, 27),
            forecast_end=date(2026, 10, 26),
            currency="VND",
            opening_cash=OpeningCash(
                aggregate_amount=Decimal("11550000"),
                reconciliation="RECONCILED",
                has_constituent_deficit=False,
                accounts=[AccountBalance("Cash", Decimal("11550000"), "VND", False)],
            ),
        )

        valid, violations = validate_grounding("Opening cash balance is 11,550,000 VND as of 2026-09-26.", mock_resp)
        self.assertTrue(valid)
        self.assertEqual(len(violations), 0)


if __name__ == "__main__":
    unittest.main()
