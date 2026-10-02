"""S4 evidence + observability tests (hermetic).

Pins:
- evidence record creation, scope fingerprint bindings, opaque refs,
- replay outcomes MATCH / RESTATED / UNAVAILABLE / FORBIDDEN,
- reauthorization on every access (nonexistence, cross-company -> generic
  FORBIDDEN; ref is never an auth token),
- payload sanitization (only authorized derived values survive),
- observability event allowlisting (unknown fields dropped, no PII, bounded
  latency/count values, fixed method/policy metadata).
"""

import json
import os
import sys
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.risk_signal import evidence as ev  # noqa: E402
from lotus_fin.risk_signal.contracts import ReasonCode, SignalId, Status  # noqa: E402
from lotus_fin.risk_signal.observability import hash_id, log_ai003_event  # noqa: E402
from lotus_fin.risk_signal.provenance import SourceFailure  # noqa: E402


def _make_record(company="AI003 Gold 2026", payload=None, signal=SignalId.AP_DUE_CLUSTER):
    return ev.create_evidence_record(
        company=company,
        signal_id=signal,
        as_of_date=date(2026, 9, 26),
        report_key="accounts_payable",
        filters={"report_date": "2026-09-26", "ageing_based_on": "Due Date"},
        currency="VND",
        source_schema_version="ap_report_v1",
        payload=payload
        or {
            "report_key": "accounts_payable",
            "numerator": Decimal("1000"),
            "denominator": Decimal("3000"),
            "display_share": Decimal("0.3333"),
            "numerator_voucher_count": 2,
            "denominator_voucher_count": 4,
            "source_hash": "a" * 64,
        },
        captured_at="2026-10-02T00:00:00.000Z",
    )


class EvidenceStoreTests(unittest.TestCase):
    def setUp(self):
        ev._STORE = ev.EvidenceStore()

    def test_record_created_with_bindings(self):
        record = _make_record()
        self.assertTrue(record.ref.startswith("AI003-EV-"))
        self.assertEqual(record.company, "AI003 Gold 2026")
        self.assertEqual(record.kind, "REPORT_SNAPSHOT")
        self.assertEqual(len(record.scope_fingerprint), 64)
        self.assertEqual(len(record.payload_hash), 64)

    def test_payload_sanitized(self):
        record = _make_record(
            payload={
                "report_key": "accounts_payable",
                "numerator": Decimal("1"),
                "denominator": Decimal("3"),
                "party_name": "Vendor A",  # must be dropped
                "raw_rows": [{"x": 1}],  # must be dropped
                "exception_text": "boom",  # must be dropped
            }
        )
        self.assertNotIn("party_name", record.payload)
        self.assertNotIn("raw_rows", record.payload)
        self.assertNotIn("exception_text", record.payload)
        self.assertIn("numerator", record.payload)

    def test_store_bounded_fifo(self):
        ev._STORE = ev.EvidenceStore(max_records=3)
        refs = [_make_record(payload={"numerator": Decimal(i)}).ref for i in range(5)]
        self.assertLessEqual(len(ev._STORE), 3)
        self.assertIsNone(ev._STORE.get(refs[0]))
        self.assertIsNotNone(ev._STORE.get(refs[-1]))


class ReplaySemanticsTests(unittest.TestCase):
    def setUp(self):
        ev._STORE = ev.EvidenceStore()
        self.record = _make_record()

    def test_match(self):
        result = ev.evidence_get(self.record.ref, "AI003 Gold 2026", lambda record: dict(self.record.payload))
        self.assertEqual(result.outcome, ev.ReplayOutcome.MATCH)
        self.assertEqual(result.fresh_payload, dict(self.record.payload))

    def test_restated(self):
        def replay(record):
            payload = dict(self.record.payload)
            payload["denominator"] = Decimal("4000")  # source actually changed
            return payload

        result = ev.evidence_get(self.record.ref, "AI003 Gold 2026", replay)
        self.assertEqual(result.outcome, ev.ReplayOutcome.RESTATED)
        self.assertEqual(result.fresh_payload["denominator"], Decimal("4000"))

    def test_source_unavailable(self):
        def replay(record):
            raise SourceFailure(Status.SOURCE_ERROR, ReasonCode.SOURCE_UNAVAILABLE, "down")

        result = ev.evidence_get(self.record.ref, "AI003 Gold 2026", replay)
        self.assertEqual(result.outcome, ev.ReplayOutcome.UNAVAILABLE)

    def test_revoked_access_forbidden(self):
        def replay(record):
            raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "denied")

        result = ev.evidence_get(self.record.ref, "AI003 Gold 2026", replay)
        self.assertEqual(result.outcome, ev.ReplayOutcome.FORBIDDEN)

    def test_unexpected_replay_failure_is_unavailable(self):
        def replay(record):
            raise RuntimeError("surprise")

        result = ev.evidence_get(self.record.ref, "AI003 Gold 2026", replay)
        self.assertEqual(result.outcome, ev.ReplayOutcome.UNAVAILABLE)

    def test_unknown_ref_generic_forbidden(self):
        result = ev.evidence_get("AI003-EV-does-not-exist", "AI003 Gold 2026", lambda record: {})
        self.assertEqual(result.outcome, ev.ReplayOutcome.FORBIDDEN)
        self.assertIsNone(result.record)  # no existence disclosure

    def test_cross_company_generic_forbidden(self):
        result = ev.evidence_get(self.record.ref, "Other Company", lambda record: dict(self.record.payload))
        self.assertEqual(result.outcome, ev.ReplayOutcome.FORBIDDEN)

    def test_malformed_ref_generic_forbidden(self):
        result = ev.evidence_get("custom:report/1", "AI003 Gold 2026", lambda record: {})
        self.assertEqual(result.outcome, ev.ReplayOutcome.FORBIDDEN)

    def test_scope_change_produces_different_ref(self):
        other = ev.create_evidence_record(
            company="AI003 Gold 2026",
            signal_id=SignalId.AP_DUE_CLUSTER,
            as_of_date=date(2026, 9, 25),  # different cutoff
            report_key="accounts_payable",
            filters={"report_date": "2026-09-25"},
            currency="VND",
            source_schema_version="ap_report_v1",
            payload={"report_key": "accounts_payable"},
            captured_at="2026-10-02T00:00:00.000Z",
        )
        self.assertNotEqual(other.ref, self.record.ref)


class ObservabilityTests(unittest.TestCase):
    def test_event_allowlisting(self):
        event = log_ai003_event(
            event_type="ai003_evaluate_completed",
            correlation_id="corr-1",
            status="OK",
            signal_type="AP_DUE_CLUSTER",
            stage="A10_EVALUATION",
            reason_code=None,
            policy_version="AI003_DEMO_POLICY_V1",
            data_mode="CONTROLLED_FIXTURE",
            record_count=4,
            latency_ms=12.3456,
        )
        self.assertEqual(event["feature_id"], "AI003")
        self.assertEqual(event["status"], "OK")
        self.assertEqual(event["method_version"], "V2.2_REVIEWED_METHOD_SPEC")
        self.assertEqual(event["latency_ms"], 12.35)
        serialized = json.dumps(event)
        self.assertNotIn("party", serialized)
        self.assertNotIn("amount", serialized)

    def test_unknown_fields_dropped(self):
        event = log_ai003_event(
            event_type="ai003_evaluate_completed",
            correlation_id="c",
            status="NOT_A_STATUS",
            signal_type="MADE_UP",
            stage="A99",
            reason_code="HACKED",
        )
        self.assertIsNone(event["status"])
        self.assertIsNone(event["signal_type"])
        self.assertIsNone(event["stage"])
        self.assertIsNone(event["reason_code"])

    def test_bounded_numeric_fields(self):
        event = log_ai003_event(
            event_type="e", correlation_id="c", latency_ms=10**12, record_count=-5
        )
        self.assertIsNone(event["latency_ms"])
        self.assertIsNone(event["record_count"])

    def test_hash_id_stable(self):
        self.assertEqual(hash_id("Administrator"), hash_id("Administrator"))
        self.assertEqual(len(hash_id("Administrator")), 12)
        self.assertIsNone(hash_id(None))


if __name__ == "__main__":
    unittest.main()
