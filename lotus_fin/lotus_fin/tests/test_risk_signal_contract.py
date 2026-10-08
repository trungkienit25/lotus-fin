"""S1 contract tests for the AI003 Risk Signal typed envelope.

Hermetic unittest suite (no Frappe import). Pins:
- impossible-state invariants (SSOT §16.6 serialization invariants),
- strict request parsing with unknown-key rejection (additional_properties false),
- Decimal wire serialization scales money=2dp / ratio=4dp / pp=2dp with the
  POLICY GOLD traps (exponent form, negative zero, lexical 10000 vs 10000.0),
- generic FORBIDDEN suppression shape,
- POLICY_PENDING partial-payload rules,
- gold string identity for statuses/reasons/method version.
"""

import os
import sys
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.modules.f003_risk_signal.contracts import (  # noqa: E402
    BaselineBlock,
    BaselineStatus,
    BaselineType,
    ContractViolation,
    DataMode,
    EvidenceRef,
    Explanation,
    ExplanationStatus,
    Finding,
    MaterialityDefinition,
    ObservedBlock,
    ReasonCode,
    RuleBlock,
    Severity,
    SignalId,
    SignalRequest,
    SignalResult,
    SourceKind,
    SourceRef,
    Status,
    ThresholdUnit,
    Unit,
    forbidden_result,
    money_str,
    parse_signal_request,
    pp_str,
    ratio_str,
    result_to_dict,
    serialize_decimal,
)


def _ok_kwargs(**overrides):
    base = dict(
        signal_id=SignalId.AR_OVERDUE_SPIKE,
        status=Status.OK,
        finding=Finding.BENIGN,
        triggered=False,
        as_of_date=date(2026, 9, 26),
        data_mode=DataMode.CONTROLLED_FIXTURE,
    )
    base.update(overrides)
    return base


class DecimalWireSerialization(unittest.TestCase):
    def test_money_2dp(self):
        self.assertEqual(money_str(Decimal("275")), "275.00")
        self.assertEqual(money_str(Decimal("275.005")), "275.01")  # HALF_UP
        self.assertEqual(money_str(Decimal("10000")), "10000.00")

    def test_ratio_4dp(self):
        self.assertEqual(ratio_str(Decimal("0.2292")), "0.2292")
        self.assertEqual(ratio_str(Decimal("0.5")), "0.5000")
        self.assertEqual(ratio_str(Decimal(1) / Decimal(3)), "0.3333")  # HALF_UP of 1/3

    def test_pp_2dp(self):
        self.assertEqual(pp_str(Decimal("11.5")), "11.50")
        self.assertEqual(pp_str(Decimal("4.99")), "4.99")
        self.assertEqual(pp_str(Decimal("72.727272")), "72.73")

    def test_exponent_form_never_leaks(self):
        self.assertEqual(money_str(Decimal("1E-5")), "0.00")
        self.assertEqual(ratio_str(Decimal("1E-7")), "0.0000")
        self.assertEqual(pp_str(Decimal("1E-9")), "0.00")
        self.assertEqual(money_str(Decimal("1E+3")), "1000.00")

    def test_negative_zero_normalized(self):
        self.assertEqual(money_str(Decimal("-0.0")), "0.00")
        self.assertEqual(ratio_str(Decimal("-0.00001")), "0.0000")
        self.assertEqual(pp_str(Decimal("-0.001")), "0.00")

    def test_non_decimal_rejected(self):
        with self.assertRaises(ContractViolation):
            money_str(0.5)  # no float authority on the wire
        with self.assertRaises(ContractViolation):
            serialize_decimal("0.5", 2)


class RequestParsing(unittest.TestCase):
    def test_valid_roundtrip(self):
        request = parse_signal_request(
            {
                "company": "AI003 Gold 2026",
                "signal_id": "AP_DUE_CLUSTER",
                "as_of_date": "2026-09-26",
                "correlation_id": "corr-1",
            }
        )
        self.assertEqual(request.company, "AI003 Gold 2026")
        self.assertEqual(request.signal_id, SignalId.AP_DUE_CLUSTER)
        self.assertEqual(request.as_of_date, date(2026, 9, 26))

    def test_unknown_keys_rejected_not_ignored(self):
        with self.assertRaises(ContractViolation):
            parse_signal_request(
                {
                    "company": "C",
                    "signal_id": "AR_OVERDUE_SPIKE",
                    "as_of_date": "2026-09-26",
                    "threshold": 5.0,
                }
            )

    def test_unknown_signal_rejected(self):
        with self.assertRaises(ContractViolation):
            parse_signal_request({"company": "C", "signal_id": "AR_OVERDUE_SPIKE_X", "as_of_date": "2026-09-26"})

    def test_strict_date_only(self):
        for bad in ("2026-9-6", "2026/09/26", "26-09-2026", "2026-09-26T00:00:00", " 2026-09-26", "2026-13-01"):
            with self.assertRaises(ContractViolation):
                parse_signal_request({"company": "C", "signal_id": "AR_OVERDUE_SPIKE", "as_of_date": bad})

    def test_company_and_correlation_bounds(self):
        with self.assertRaises(ContractViolation):
            parse_signal_request({"company": "", "signal_id": "AR_OVERDUE_SPIKE", "as_of_date": "2026-09-26"})
        with self.assertRaises(ContractViolation):
            parse_signal_request(
                {"company": "C", "signal_id": "AR_OVERDUE_SPIKE", "as_of_date": "2026-09-26", "correlation_id": "x" * 129}
            )
        SignalRequest(company="C", signal_id=SignalId.AP_DUE_CLUSTER, as_of_date=date(2026, 9, 26))

    def test_non_mapping_rejected(self):
        with self.assertRaises(ContractViolation):
            parse_signal_request("company=C")


class ImpossibleStateInvariants(unittest.TestCase):
    def test_ok_requires_finding(self):
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(finding=None, triggered=None))

    def test_ok_triggered_requires_severity(self):
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(finding=Finding.TRIGGERED, triggered=True, severity=None))
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(finding=Finding.TRIGGERED, triggered=True, severity="CRITICAL"))

    def test_benign_must_not_carry_severity(self):
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(finding=Finding.BENIGN, triggered=False, severity=Severity.WATCH))
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(finding=Finding.BENIGN, triggered=True))

    def test_non_ok_carries_no_evaluation(self):
        for status in (Status.INCONCLUSIVE, Status.FORBIDDEN, Status.VALIDATION_ERROR, Status.SOURCE_ERROR, Status.POLICY_PENDING):
            with self.assertRaises(ContractViolation):
                SignalResult(**_ok_kwargs(status=status, finding=Finding.BENIGN, triggered=False))

    def test_triggered_must_be_bool_not_int(self):
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(finding=Finding.TRIGGERED, triggered=1, severity=Severity.HIGH))

    def test_gold_string_identity(self):
        self.assertEqual(Status.POLICY_PENDING.value, "POLICY_PENDING")
        self.assertEqual(ReasonCode.UNSUPPORTED_MULTI_SCHEDULE.value, "UNSUPPORTED_MULTI_SCHEDULE")
        self.assertEqual(ReasonCode.POLICY_NOT_APPROVED.value, "POLICY_NOT_APPROVED")
        self.assertEqual(ReasonCode.CONFLICTING_OBSERVATION.value, "CONFLICTING_OBSERVATION")
        self.assertEqual(ReasonCode.INCOMPLETE_DUE_DATE_COVERAGE.value, "INCOMPLETE_DUE_DATE_COVERAGE")
        self.assertEqual(ReasonCode.UNSUPPORTED_ALLOCATION_SCOPE.value, "UNSUPPORTED_ALLOCATION_SCOPE")
        self.assertEqual(ReasonCode.ACCESS_DENIED.value, "ACCESS_DENIED")


class PayloadSuppression(unittest.TestCase):
    def _rich_kwargs(self):
        return dict(
            observed=ObservedBlock(
                value=Decimal("0.5"),
                unit=Unit.RATIO,
                supporting_amount=Decimal("200"),
                supporting_amount_definition=MaterialityDefinition.AP_DUE_WINDOW_AMOUNT,
            ),
            delta_pp=Decimal("6.25"),
            baseline=BaselineBlock(
                type=BaselineType.PREVIOUS_COMPARABLE_CUTOFF,
                status=BaselineStatus.AVAILABLE,
                value=Decimal("0.1150"),
                denominator=Decimal("650000.00"),
                cutoff=date(2026, 8, 26),
                resolver_version="PREV_MONTH_SAME_DAY_CLAMP_V1",
            ),
            rule=RuleBlock(
                threshold=Decimal("0.50"),
                threshold_unit=ThresholdUnit.RATIO,
                floor=Decimal("0"),
                materiality_definition=MaterialityDefinition.AP_DUE_WINDOW_AMOUNT,
            ),
            count_positive_vouchers=4,
            count_due_vouchers=2,
            source_refs=(SourceRef(kind=SourceKind.ERP_AP_REPORT, cutoff=date(2026, 9, 26), captured_at="2026-10-02T00:00:00.000Z"),),
            evidence=(EvidenceRef(kind="REPORT_SNAPSHOT", company="C", ref="snap-1"),),
            limitations=("demo",),
            explanation=Explanation(status=ExplanationStatus.AVAILABLE, text="ok"),
        )

    def test_forbidden_is_generic_envelope(self):
        result = forbidden_result(SignalId.AP_DUE_CLUSTER, ("A1_AUTH",), correlation_id="c-1")
        self.assertEqual(result.status, Status.FORBIDDEN)
        self.assertEqual(result.reason_code, ReasonCode.ACCESS_DENIED)
        wire = result_to_dict(result)
        self.assertEqual(
            set(wire.keys()),
            {"feature_id", "contract_version", "method_version", "signal_id", "status", "accounting_timezone",
             "temporal_basis", "generated_at", "correlation_id", "reason_code"},
        )
        self.assertNotIn("company", wire)
        self.assertEqual(wire["reason_code"], "ACCESS_DENIED")

    def test_suppressed_statuses_strip_payload(self):
        rich = self._rich_kwargs()
        for status in (Status.FORBIDDEN, Status.VALIDATION_ERROR, Status.SOURCE_ERROR):
            with self.assertRaises(ContractViolation):
                SignalResult(**_ok_kwargs(status=status, reason_code=ReasonCode.SOURCE_INVALID, **rich))

        stripped = SignalResult(
            signal_id=SignalId.AR_OVERDUE_SPIKE,
            status=Status.SOURCE_ERROR,
            reason_code=ReasonCode.SOURCE_INVALID,
        )
        self.assertIsNone(stripped.observed)
        self.assertEqual(stripped.source_refs, ())
        self.assertIsNone(stripped.explanation.text)

    def test_policy_pending_may_carry_partial_but_no_evaluation(self):
        result = SignalResult(
            signal_id=SignalId.AP_DUE_CLUSTER,
            status=Status.POLICY_PENDING,
            reason_code=ReasonCode.POLICY_NOT_APPROVED,
            observed=ObservedBlock(
                value=Decimal("0.5"),
                supporting_amount=Decimal("200"),
                supporting_amount_definition=MaterialityDefinition.AP_DUE_WINDOW_AMOUNT,
            ),
            evidence=(EvidenceRef(kind="REPORT_SNAPSHOT", company="C", ref="snap-1"),),
            as_of_date=date(2026, 9, 26),
            data_mode=DataMode.CONTROLLED_FIXTURE,
        )
        self.assertIsNone(result.finding)
        self.assertIsNone(result.severity)
        self.assertIsNone(result.triggered)
        with self.assertRaises(ContractViolation):
            SignalResult(
                signal_id=SignalId.AP_DUE_CLUSTER,
                status=Status.POLICY_PENDING,
                reason_code=ReasonCode.SOURCE_INVALID,  # not a pending-policy reason
                as_of_date=date(2026, 9, 26),
                data_mode=DataMode.CONTROLLED_FIXTURE,
            )

    def test_ok_rejects_reason_code_and_requires_context(self):
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(reason_code=ReasonCode.INVALID_REQUEST))
        with self.assertRaises(ContractViolation):
            SignalResult(signal_id=SignalId.AR_OVERDUE_SPIKE, status=Status.OK, finding=Finding.BENIGN, triggered=False)

    def test_unknown_stage_rejected(self):
        with self.assertRaises(ContractViolation):
            forbidden_result(SignalId.AR_OVERDUE_SPIKE, ("A1_AUTH", "A99_MADE_UP"))

    def test_timezone_fixed(self):
        with self.assertRaises(ContractViolation):
            SignalResult(**_ok_kwargs(accounting_timezone="UTC"))


class WireRoundTrip(unittest.TestCase):
    def test_ok_result_serializes_pinned_scales(self):
        result = SignalResult(
            signal_id=SignalId.AP_DUE_CLUSTER,
            status=Status.OK,
            finding=Finding.TRIGGERED,
            triggered=True,
            severity=Severity.HIGH,
            observed=ObservedBlock(
                value=Decimal("0.75"),
                supporting_amount=Decimal("300"),
                supporting_amount_definition=MaterialityDefinition.AP_DUE_WINDOW_AMOUNT,
            ),
            rule=RuleBlock(
                threshold=Decimal("0.75"),
                threshold_unit=ThresholdUnit.RATIO,
                floor=Decimal("0"),
                materiality_definition=MaterialityDefinition.AP_DUE_WINDOW_AMOUNT,
                window_start=date(2026, 9, 26),
                window_end=date(2026, 10, 26),
            ),
            as_of_date=date(2026, 9, 26),
            data_mode=DataMode.CONTROLLED_FIXTURE,
            policy_version="AI003_DEMO_POLICY_V1",
            policy_scope="DEMO_ONLY",
            production_calibrated=False,
        )
        wire = result_to_dict(result)
        self.assertEqual(wire["observed"]["value"], "0.7500")
        self.assertEqual(wire["observed"]["supporting_amount"], "300.00")
        self.assertEqual(wire["rule"]["threshold"], "0.7500")
        self.assertEqual(wire["rule"]["floor"], "0.00")
        self.assertEqual(wire["policy_scope"], "DEMO_ONLY")
        self.assertFalse(wire["production_calibrated"])
        self.assertEqual(wire["method_version"], "V2.2_REVIEWED_METHOD_SPEC")
        self.assertNotIn("company", wire)  # verified company never leaks into result wire


if __name__ == "__main__":
    unittest.main()
