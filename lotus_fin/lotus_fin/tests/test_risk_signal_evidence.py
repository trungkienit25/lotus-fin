"""S4 evidence + observability tests (hermetic).

Pins:
- evidence record creation, scope fingerprint bindings, opaque refs,
- replay outcomes MATCH / RESTATED / UNAVAILABLE / FORBIDDEN,
- reauthorization on every access (nonexistence, cross-company -> generic
  FORBIDDEN; ref is never an auth token),
- payload sanitization (only authorized derived values survive),
- observability event allowlisting (unknown fields dropped, no PII, bounded
  latency/count values, fixed method/policy metadata),
- G4B remediation: raw Redis command boundary (make_key/setex/get/delete),
  errors surfaced as typed EvidenceStorageUnavailable, no process-local
  fallback, TTL 3600, Decimal/date round-trip, correlation-id diagnostics
  with zero sensitive error text.

Hermetic stores are ALWAYS constructed with an explicitly injected client —
the runtime resolves Frappe's cache and must never fall back to a local dict.
"""

import json
import os
import pickle
import sys
import unittest
import unittest.mock as mock
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.risk_signal import evidence as ev  # noqa: E402
from lotus_fin.risk_signal.contracts import ReasonCode, SignalId, Status  # noqa: E402
from lotus_fin.risk_signal.observability import hash_id, log_ai003_event  # noqa: E402
from lotus_fin.risk_signal.provenance import SourceFailure  # noqa: E402


# Sensitive marker injected into fake Redis errors — must never reach the
# structured events or any client-facing payload.
SENSITIVE_ERROR_TEXT = "SENSITIVE redis://admin:sekret@10.0.0.42:6379 auth-failed"


class FakeFrappeRedis:
    """Models the RAW redis command boundary exposed by Frappe's RedisWrapper
    (make_key/setex/get/delete) — NOT the error-swallowing convenience methods
    (set_value/get_value), which is the exact defect class under remediation.
    Commands fail with an injected exception when listed in ``fail_on``."""

    def __init__(self, fail_on=(), error=None):
        self.data = {}
        self.ttls = {}
        self.fail_on = set(fail_on)
        self.error = error or ConnectionError(SENSITIVE_ERROR_TEXT)

    def make_key(self, key):
        return f"testsite|{key}"

    def setex(self, name, time, value):
        if "setex" in self.fail_on:
            raise self.error
        self.data[name] = value
        self.ttls[name] = time

    def get(self, name):
        if "get" in self.fail_on:
            raise self.error
        return self.data.get(name)

    def delete(self, name):
        if "delete" in self.fail_on:
            raise self.error
        self.data.pop(name, None)
        self.ttls.pop(name, None)


def _make_store(client=None):
    return ev.EvidenceStore(client=client if client is not None else FakeFrappeRedis())


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
        ev._STORE = _make_store()

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
        self.assertNotEqual(other.ref, _make_record().ref)


class ReplaySemanticsTests(unittest.TestCase):
    def setUp(self):
        ev._STORE = _make_store()
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


class StorageBoundaryTests(unittest.TestCase):
    """G4B remediation — the Redis boundary is exercised directly: failures
    surface as typed EvidenceStorageUnavailable and never fall back to a
    process-local store."""

    def test_1_connection_error_surfaces_on_set_and_get(self):
        # Real-wrapper shape: raw commands raise ConnectionError on outage.
        put_store = ev.EvidenceStore(client=FakeFrappeRedis(fail_on={"setex"}))
        with self.assertRaises(ev.EvidenceStorageUnavailable) as ctx:
            put_store.put(_make_record(), correlation_id="conn-corr")
        self.assertEqual(ctx.exception.cause_type, "ConnectionError")

        get_store = ev.EvidenceStore(client=FakeFrappeRedis(fail_on={"get"}))
        with self.assertRaises(ev.EvidenceStorageUnavailable) as ctx:
            get_store.get("AI003-EV-anything", correlation_id="conn-corr")
        self.assertEqual(ctx.exception.cause_type, "ConnectionError")

    def test_2_timeout_surfaces_as_typed_failure(self):
        store = ev.EvidenceStore(
            client=FakeFrappeRedis(fail_on={"setex", "get"}, error=TimeoutError(SENSITIVE_ERROR_TEXT))
        )
        with self.assertRaises(ev.EvidenceStorageUnavailable) as ctx:
            store.put(_make_record(), correlation_id="timeout-corr")
        self.assertEqual(ctx.exception.cause_type, "TimeoutError")

        with self.assertRaises(ev.EvidenceStorageUnavailable):
            store.get("AI003-EV-anything", correlation_id="timeout-corr")

    def test_3_set_failure_emits_no_ref(self):
        # Store path: a failed SET must not hand out an un-persisted ref —
        # the typed error propagates and the service drops evidence refs.
        ev._STORE = ev.EvidenceStore(client=FakeFrappeRedis(fail_on={"setex"}))
        with self.assertRaises(ev.EvidenceStorageUnavailable):
            ev.create_evidence_record(
                company="AI003 Gold 2026",
                signal_id=SignalId.AP_DUE_CLUSTER,
                as_of_date=date(2026, 9, 26),
                report_key="accounts_payable",
                filters={},
                currency="VND",
                source_schema_version="ap_report_v1",
                payload={"report_key": "accounts_payable"},
                captured_at="2026-10-02T00:00:00.000Z",
            )
        # Deterministic result keeps frozen-contract behavior: no refs, no crash.
        from lotus_fin.risk_signal.service import _ap_evidence

        dummy_snapshot = mock.MagicMock()
        dummy_snapshot.report_key = "accounts_payable"
        dummy_snapshot.source_hash = "h" * 64
        dummy_snapshot.filters_applied = {}
        refs, ref = _ap_evidence(
            dummy_snapshot, (), "AI003 Gold 2026", date(2026, 9, 26), "2026-10-02T00:00:00Z",
            correlation_id="set-fail-corr"
        )
        self.assertEqual(refs, ())
        self.assertIsNone(ref)

    def test_4_get_failure_distinct_from_missing_key(self):
        # Redis failure on GET -> typed error -> evidence_get maps to UNAVAILABLE.
        ev._STORE = ev.EvidenceStore(client=FakeFrappeRedis(fail_on={"get"}))
        result = ev.evidence_get("AI003-EV-x", "AI003 Gold 2026", lambda record: {}, correlation_id="gf")
        self.assertEqual(result.outcome, ev.ReplayOutcome.UNAVAILABLE)
        self.assertIsNone(result.fresh_payload)

        # Healthy GET on missing/expired key -> None -> generic FORBIDDEN.
        ev._STORE = _make_store()
        result = ev.evidence_get("AI003-EV-never-stored", "AI003 Gold 2026", lambda record: {})
        self.assertEqual(result.outcome, ev.ReplayOutcome.FORBIDDEN)
        self.assertIsNone(result.record)

    def test_5_cross_worker_healthy_path(self):
        shared = FakeFrappeRedis()
        worker_a = ev.EvidenceStore(client=shared)
        worker_b = ev.EvidenceStore(client=shared)
        record = _make_record()
        ref = worker_a.put(record, correlation_id="cw")
        self.assertEqual(ref, record.ref)

        # Site-namespaced key with the frozen prefix.
        self.assertTrue(
            all(k.startswith("testsite|ai003:evidence:") for k in shared.data),
            f"unexpected keys: {list(shared.data)}",
        )

        retrieved = worker_b.get(ref)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.ref, record.ref)
        self.assertEqual(retrieved.company, record.company)
        self.assertEqual(retrieved.as_of_date, record.as_of_date)
        self.assertEqual(retrieved.payload["numerator"], Decimal("1000"))

    def test_6_no_runtime_local_fallback(self):
        store = ev.EvidenceStore(client=FakeFrappeRedis(fail_on={"setex"}))
        self.assertFalse(hasattr(store, "_local_records"))
        self.assertFalse(hasattr(store, "_local_order"))
        with self.assertRaises(ev.EvidenceStorageUnavailable):
            store.put(_make_record(), correlation_id="lf")
        # Nothing landed anywhere: after the client heals, the ref is absent.
        store._client.fail_on.clear()
        self.assertIsNone(store.get("AI003-EV-never-persisted"))
        # A store with no resolvable client and no injection fails closed too.
        with mock.patch.dict(sys.modules, {"frappe": None}):
            orphan = ev.EvidenceStore()
            with self.assertRaises(ev.EvidenceStorageUnavailable):
                orphan.get("AI003-EV-x", correlation_id="lf")

    def test_7_ttl_and_decimal_date_roundtrip(self):
        shared = FakeFrappeRedis()
        worker_a = ev.EvidenceStore(client=shared)
        worker_b = ev.EvidenceStore(client=shared)
        record = _make_record()
        worker_a.put(record)
        (blob,) = shared.ttls.values()
        self.assertEqual(blob, 3600)  # frozen TTL bound

        restored = worker_b.get(record.ref)
        self.assertEqual(restored.as_of_date, date(2026, 9, 26))
        self.assertEqual(restored.payload["numerator"], Decimal("1000"))
        self.assertEqual(restored.payload["display_share"], Decimal("0.3333"))
        self.assertEqual(restored.payload["numerator_voucher_count"], 2)
        # Canonical hash semantics survive the round trip (MATCH basis).
        self.assertEqual(
            worker_b.get(record.ref).payload_hash, record.payload_hash
        )

    def test_8_diagnostics_correlation_no_sensitive_text(self):
        logged = []
        store = ev.EvidenceStore(client=FakeFrappeRedis(fail_on={"setex", "get"}))
        with mock.patch(
            "lotus_fin.risk_signal.evidence.log_ai003_event",
            side_effect=lambda **kw: logged.append(kw) or {},
        ):
            with self.assertRaises(ev.EvidenceStorageUnavailable):
                store.put(_make_record(), correlation_id="corr-boundary-8")
            with self.assertRaises(ev.EvidenceStorageUnavailable):
                store.get("AI003-EV-x", correlation_id="corr-boundary-8")

        put_events = [e for e in logged if e.get("operation") == "evidence_cache_set"]
        get_events = [e for e in logged if e.get("operation") == "evidence_cache_get"]
        self.assertEqual(len(put_events), 1)
        self.assertEqual(len(get_events), 1)
        self.assertEqual(put_events[0]["correlation_id"], "corr-boundary-8")
        self.assertEqual(get_events[0]["correlation_id"], "corr-boundary-8")
        self.assertEqual(put_events[0]["exception_type"], "ConnectionError")

        serialized = json.dumps(logged, default=str)
        self.assertNotIn("SENSITIVE", serialized)
        self.assertNotIn("sekret", serialized)
        self.assertNotIn("redis://", serialized)
        self.assertNotIn("10.0.0.42", serialized)


class DecodeBoundaryTests(unittest.TestCase):
    """Legacy/corrupt cache payloads (e.g. parent-format pickle bytes from
    117d7e5) must fail CLOSED with exactly one sanitized diagnostic — never an
    unhandled endpoint exception, never pickle.loads, never content logging."""

    SENSITIVE = "SENSITIVE-pickle-payload-admin-token"

    def setUp(self):
        self.client = FakeFrappeRedis()
        self.store = ev.EvidenceStore(client=self.client)
        ev._STORE = self.store

    def _seed_raw(self, ref, raw):
        self.client.data[f"testsite|{ev.EVIDENCE_KEY_PREFIX}{ref}"] = raw

    def _logged(self):
        logged = []
        patcher = mock.patch(
            "lotus_fin.risk_signal.evidence.log_ai003_event",
            side_effect=lambda **kw: logged.append(kw) or {},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return logged

    def test_valid_json_still_round_trips_with_hash_semantics(self):
        record = _make_record()
        self.store.put(record)
        restored = ev.EvidenceStore(client=self.client).get(record.ref, correlation_id="dec-valid")
        self.assertEqual(restored.payload_hash, record.payload_hash)
        self.assertEqual(restored.payload["numerator"], Decimal("1000"))
        self.assertEqual(restored.as_of_date, date(2026, 9, 26))

    def test_parent_pickle_bytes_typed(self):
        self._seed_raw(
            "AI003-EV-legacy01",
            pickle.dumps({"ref": "AI003-EV-legacy01", self.SENSITIVE: "x"}, protocol=4),
        )
        with self.assertRaises(ev.EvidenceStorageUnavailable) as ctx:
            self.store.get("AI003-EV-legacy01", correlation_id="dec-pickle")
        self.assertEqual(ctx.exception.cause_type, "UnicodeDecodeError")
        result = ev.evidence_get("AI003-EV-legacy01", "AI003 Gold 2026", lambda r: {}, correlation_id="dec-pickle")
        self.assertEqual(result.outcome, ev.ReplayOutcome.UNAVAILABLE)
        self.assertIsNone(result.fresh_payload)
        self.assertIsNone(result.record)

    def test_invalid_utf8_typed(self):
        self._seed_raw("AI003-EV-badutf8", b"\xff\xfe\x81" + self.SENSITIVE.encode("utf-16"))
        with self.assertRaises(ev.EvidenceStorageUnavailable) as ctx:
            self.store.get("AI003-EV-badutf8", correlation_id="dec-utf8")
        self.assertEqual(ctx.exception.cause_type, "UnicodeDecodeError")
        self.assertEqual(
            ev.evidence_get("AI003-EV-badutf8", "AI003 Gold 2026", lambda r: {}).outcome,
            ev.ReplayOutcome.UNAVAILABLE,
        )

    def test_invalid_json_typed(self):
        self._seed_raw("AI003-EV-badjson", b"{not-json")
        with self.assertRaises(ev.EvidenceStorageUnavailable) as ctx:
            self.store.get("AI003-EV-badjson", correlation_id="dec-json")
        self.assertEqual(ctx.exception.cause_type, "JSONDecodeError")
        self.assertEqual(
            ev.evidence_get("AI003-EV-badjson", "AI003 Gold 2026", lambda r: {}).outcome,
            ev.ReplayOutcome.UNAVAILABLE,
        )

    def test_valid_json_wrong_structure_typed(self):
        for ref, raw in (
            ("AI003-EV-arr", b"[1, 2, 3]"),
            ("AI003-EV-scalar", b"123"),
            ("AI003-EV-noref", json.dumps({"company": "AI003 Gold 2026"}).encode()),
            ("AI003-EV-nopayload", json.dumps(
                {"ref": "AI003-EV-nopayload", "company": "c", "as_of_date": "2026-09-26",
                 "signal_id": "AP_DUE_CLUSTER"}).encode()),
            ("AI003-EV-baddate", json.dumps(
                {"ref": "AI003-EV-baddate", "company": "c", "as_of_date": 20260926,
                 "signal_id": "AP_DUE_CLUSTER", "payload": {}}).encode()),
            ("AI003-EV-badsignal", json.dumps(
                {"ref": "AI003-EV-badsignal", "company": "c", "as_of_date": "2026-09-26",
                 "signal_id": "NOT_A_SIGNAL", "payload": {}}).encode()),
            ("AI003-EV-badhash", json.dumps(
                {"ref": "AI003-EV-badhash", "company": "c", "as_of_date": "2026-09-26",
                 "signal_id": "AP_DUE_CLUSTER", "payload": {}, "payload_hash": 7}).encode()),
        ):
            with self.subTest(ref=ref):
                self._seed_raw(ref, raw)
                with self.assertRaises(ev.EvidenceStorageUnavailable):
                    self.store.get(ref, correlation_id="dec-struct")
                self.assertEqual(
                    ev.evidence_get(ref, "AI003 Gold 2026", lambda r: {}).outcome,
                    ev.ReplayOutcome.UNAVAILABLE,
                )

    def test_each_decode_failure_one_sanitized_diagnostic(self):
        self._seed_raw(
            "AI003-EV-legacy02",
            pickle.dumps({self.SENSITIVE: "party-names-raw-rows"}, protocol=4),
        )
        logged = self._logged()
        with self.assertRaises(ev.EvidenceStorageUnavailable):
            self.store.get("AI003-EV-legacy02", correlation_id="corr-dec-1")
        self.assertEqual(len(logged), 1)
        event = logged[0]
        self.assertEqual(event["operation"], "evidence_cache_decode")
        self.assertEqual(event["correlation_id"], "corr-dec-1")
        self.assertEqual(event["exception_type"], "UnicodeDecodeError")
        # Missing/expired keys stay a clean miss (no decode diagnostic at all).
        missing_logged = self._logged()
        self.assertIsNone(self.store.get("AI003-EV-never-stored"))
        self.assertEqual(len(missing_logged), 0)

    def test_diagnostics_never_contain_content_or_message(self):
        for ref, raw in (
            ("AI003-EV-p", pickle.dumps({self.SENSITIVE: "x"}, protocol=4)),
            ("AI003-EV-u", b"\xff\xfe" + self.SENSITIVE.encode("utf-16")),
            ("AI003-EV-j", b"{oops:" + self.SENSITIVE.encode()[:5] + b"}"),
        ):
            self._seed_raw(ref, raw)
            logged = self._logged()
            with self.assertRaises(ev.EvidenceStorageUnavailable):
                self.store.get(ref, correlation_id="corr-dec-2")
            serialized = json.dumps(logged, default=str)
            self.assertNotIn("SENSITIVE", serialized)
            self.assertNotIn("party-names", serialized)
            self.assertNotIn("pickle", serialized)


class ServiceDiagnosticsTests(unittest.TestCase):
    def test_structured_diagnostics_on_replay_failure(self):
        ev._STORE = _make_store()
        record = _make_record()
        logged = []
        with mock.patch("lotus_fin.risk_signal.evidence.log_ai003_event", side_effect=lambda **kw: logged.append(kw) or {}):
            def bad_replay(r):
                raise RuntimeError("backend_exploded")
            result = ev.evidence_get(record.ref, "AI003 Gold 2026", bad_replay, correlation_id="test-corr-42")
            self.assertEqual(result.outcome, ev.ReplayOutcome.UNAVAILABLE)
            matching = [e for e in logged if e.get("event_type") == "ai003_evidence_replay_unexpected_failure"]
            self.assertTrue(len(matching) >= 1)
            self.assertEqual(matching[0]["exception_type"], "RuntimeError")
            self.assertEqual(matching[0]["correlation_id"], "test-corr-42")
            self.assertEqual(matching[0]["operation"], "replay_source_fetch")

    def test_structured_diagnostics_on_store_failure(self):
        logged = []
        from lotus_fin.risk_signal.service import _ap_evidence
        with mock.patch("lotus_fin.risk_signal.service.create_evidence_record", side_effect=ValueError("redis_down")):
            with mock.patch("lotus_fin.risk_signal.service.log_ai003_event", side_effect=lambda **kw: logged.append(kw) or {}):
                dummy_snapshot = mock.MagicMock()
                dummy_snapshot.report_key = "accounts_payable"
                dummy_snapshot.source_hash = "h" * 64
                dummy_snapshot.filters_applied = {}
                refs, ref = _ap_evidence(
                    dummy_snapshot, (), "AI003 Gold 2026", date(2026, 9, 26), "2026-10-02T00:00:00Z",
                    correlation_id="store-fail-corr"
                )
                self.assertEqual(refs, ())
                self.assertIsNone(ref)
                matching = [e for e in logged if e.get("event_type") == "ai003_evidence_store_failed"]
                self.assertTrue(len(matching) >= 1)
                self.assertEqual(matching[0]["exception_type"], "ValueError")
                self.assertEqual(matching[0]["correlation_id"], "store-fail-corr")
                self.assertEqual(matching[0]["operation"], "store_ap_evidence")

    def test_evidence_delete_eviction(self):
        shared = FakeFrappeRedis()
        store = ev.EvidenceStore(client=shared)
        record = _make_record()
        ref = store.put(record)
        self.assertIsNotNone(store.get(ref))
        store.delete(ref)
        self.assertIsNone(store.get(ref))

    def test_delete_failure_surfaces(self):
        store = ev.EvidenceStore(client=FakeFrappeRedis(fail_on={"delete"}))
        with self.assertRaises(ev.EvidenceStorageUnavailable):
            store.delete("AI003-EV-x", correlation_id="del-corr")


if __name__ == "__main__":
    unittest.main()
