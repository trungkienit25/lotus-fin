"""S3 policy registry + deterministic evaluation boundary tests (hermetic).

Pins the owner-approved AI003_DEMO_POLICY_V1 constants and the POLICY GOLD
boundary vectors exactly:
- AR: 4.99/5.00/10.00/14.99/15.00/15.01 pp on the published-ratio .01pp grid,
  HIGH before WATCH, equality uses >=, negative/zero deltas BENIGN.
- AP: N/D=400 pairs 199.99 (BENIGN, display 0.5000 trap), 200 (WATCH),
  250 (WATCH), 299.99 (WATCH, display 0.7500 trap), 300 (HIGH), 300.01 (HIGH)
  with exact N >= T*D — the rounded display share is never an operand.
- Registry: DEMO_ONLY metadata, production_calibrated=false, pending-policy
  -> POLICY_PENDING, invalid active configuration -> INVALID_POLICY_CONFIG.
"""

import os
import sys
import unittest
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lotus_fin.modules.f003_risk_signal import policy as policy_module  # noqa: E402
from lotus_fin.modules.f003_risk_signal.contracts import (  # noqa: E402
    Finding,
    ReasonCode,
    Severity,
    SignalId,
    Status,
    ThresholdUnit,
)
from lotus_fin.modules.f003_risk_signal.coverage import APSelection  # noqa: E402
from lotus_fin.modules.f003_risk_signal.evaluation import evaluate_ap, evaluate_ar, materiality_definition_for  # noqa: E402
from lotus_fin.modules.f003_risk_signal.interfaces import ARSnapshot  # noqa: E402
from lotus_fin.modules.f003_risk_signal.policy import (  # noqa: E402
    APPROVAL_PENDING,
    PolicyPending,
    SignalPolicy,
    resolve_policy,
)
from lotus_fin.modules.f003_risk_signal.provenance import SourceFailure  # noqa: E402


class _FakeObs:
    def __init__(self, voucher, amount):
        self.voucher_no = voucher
        self.amount = Decimal(amount)


def _selection(numerators, denominators):
    return APSelection(
        numerator=tuple((_FakeObs("N%d" % i, amount), None) for i, amount in enumerate(numerators)),
        denominator=tuple((_FakeObs("D%d" % i, amount), None) for i, amount in enumerate(denominators)),
    )


def _snapshot(total, ratio):
    return ARSnapshot(
        status="OK",
        contract_version="1.0.0",
        formula_version="2026.1",
        company="C",
        currency="VND",
        as_of=date(2026, 9, 26),
        total_ar=Decimal(total),
        overdue_ratio=Decimal(ratio),
        ar_metrics_available=True,
    )


class RegistryTests(unittest.TestCase):
    def test_ar_demo_policy_values(self):
        policy = resolve_policy(SignalId.AR_OVERDUE_SPIKE)
        self.assertEqual(policy.policy_version, "AI003_DEMO_POLICY_V1")
        self.assertEqual(policy.floor, Decimal("0"))
        self.assertEqual(policy.watch_threshold, Decimal("5.00"))
        self.assertEqual(policy.high_threshold, Decimal("15.00"))
        self.assertEqual(policy.threshold_unit, ThresholdUnit.PERCENTAGE_POINTS)
        self.assertEqual(policy.policy_scope, "DEMO_ONLY")
        self.assertFalse(policy.production_calibrated)
        self.assertEqual(policy.approver, "Project Owner")
        self.assertEqual(policy.approved_date, date(2026, 10, 2))
        self.assertEqual(policy.baseline_spec, "PREV_MONTH_SAME_DAY_CLAMP_V1")

    def test_ap_demo_policy_values(self):
        policy = resolve_policy(SignalId.AP_DUE_CLUSTER)
        self.assertEqual(policy.floor, Decimal("0"))
        self.assertEqual(policy.watch_threshold, Decimal("0.50"))
        self.assertEqual(policy.high_threshold, Decimal("0.75"))
        self.assertEqual(policy.threshold_unit, ThresholdUnit.RATIO)
        self.assertEqual(policy.window_days, 30)
        self.assertEqual(policy.policy_scope, "DEMO_ONLY")
        self.assertFalse(policy.production_calibrated)

    def test_pending_policy_raises_policy_pending(self):
        pending = SignalPolicy(
            policy_version="AI003_TEST_PENDING",
            signal_id=SignalId.AR_OVERDUE_SPIKE,
            approval_status=APPROVAL_PENDING,
            policy_scope="DEMO_ONLY",
            data_mode_scope="ALL",
            approver="Nobody",
            approved_date=date(2026, 10, 2),
            validation_evidence="none",
            floor=Decimal("0"),
            watch_threshold=Decimal("5.00"),
            high_threshold=Decimal("15.00"),
            threshold_unit=ThresholdUnit.PERCENTAGE_POINTS,
            precision="0.01",
            baseline_spec="PREV_MONTH_SAME_DAY_CLAMP_V1",
            window_days=None,
        )
        original_registry = dict(policy_module._REGISTRY)
        original_active = dict(policy_module._ACTIVE_VERSIONS)
        try:
            policy_module._REGISTRY[(SignalId.AR_OVERDUE_SPIKE, "AI003_TEST_PENDING")] = pending
            policy_module._ACTIVE_VERSIONS[SignalId.AR_OVERDUE_SPIKE] = "AI003_TEST_PENDING"
            with self.assertRaises(PolicyPending) as ctx:
                resolve_policy(SignalId.AR_OVERDUE_SPIKE)
            self.assertEqual(ctx.exception.reason_code, ReasonCode.POLICY_NOT_APPROVED)
        finally:
            policy_module._REGISTRY.clear()
            policy_module._REGISTRY.update(original_registry)
            policy_module._ACTIVE_VERSIONS.clear()
            policy_module._ACTIVE_VERSIONS.update(original_active)

    def test_unregistered_active_version_is_invalid_config(self):
        original_active = dict(policy_module._ACTIVE_VERSIONS)
        try:
            policy_module._ACTIVE_VERSIONS[SignalId.AR_OVERDUE_SPIKE] = "AI003_MISSING_V9"
            with self.assertRaises(SourceFailure) as ctx:
                resolve_policy(SignalId.AR_OVERDUE_SPIKE)
            self.assertEqual(ctx.exception.status, Status.SOURCE_ERROR)
            self.assertEqual(ctx.exception.reason_code, ReasonCode.INVALID_POLICY_CONFIG)
        finally:
            policy_module._ACTIVE_VERSIONS.clear()
            policy_module._ACTIVE_VERSIONS.update(original_active)

    def test_policy_construction_rejects_invalid_configs(self):
        base = dict(
            policy_version="X",
            signal_id=SignalId.AR_OVERDUE_SPIKE,
            approval_status="APPROVED",
            policy_scope="DEMO_ONLY",
            data_mode_scope="ALL",
            approver="A",
            approved_date=date(2026, 10, 2),
            validation_evidence="e",
            floor=Decimal("0"),
            watch_threshold=Decimal("5.00"),
            high_threshold=Decimal("15.00"),
            threshold_unit=ThresholdUnit.PERCENTAGE_POINTS,
            precision="0.01",
            baseline_spec=None,
            window_days=None,
        )
        with self.assertRaises(ValueError):  # reversed
            SignalPolicy(**{**base, "watch_threshold": Decimal("16"), "high_threshold": Decimal("15")})
        with self.assertRaises(ValueError):  # non-finite
            SignalPolicy(**{**base, "watch_threshold": Decimal("NaN")})
        with self.assertRaises(ValueError):  # negative floor
            SignalPolicy(**{**base, "floor": Decimal("-1")})
        with self.assertRaises(ValueError):  # production calibrated
            SignalPolicy(**{**base, "production_calibrated": True})
        with self.assertRaises(ValueError):  # AP threshold out of [0,1]
            SignalPolicy(**{**base, "threshold_unit": ThresholdUnit.RATIO, "watch_threshold": Decimal("1.5")})
        with self.assertRaises(ValueError):  # negative window
            SignalPolicy(**{**base, "window_days": -1})

    def test_materiality_definition_mapping(self):
        self.assertEqual(
            materiality_definition_for(resolve_policy(SignalId.AR_OVERDUE_SPIKE)).value,
            "CURRENT_NET_AR_TOTAL",
        )
        self.assertEqual(
            materiality_definition_for(resolve_policy(SignalId.AP_DUE_CLUSTER)).value,
            "AP_DUE_WINDOW_AMOUNT",
        )


class ARBoundaryTests(unittest.TestCase):
    """POLICY GOLD AR boundary table on the published 4dp-ratio .01pp grid."""

    def _evaluate(self, current_ratio, baseline_ratio="0.0000", total="1000"):
        policy = resolve_policy(SignalId.AR_OVERDUE_SPIKE)
        return evaluate_ar(policy, _snapshot(total, current_ratio), _snapshot("1000", baseline_ratio))

    def test_boundaries(self):
        cases = [
            ("0.0499", "0.0000", Finding.BENIGN, None),        # 4.99pp
            ("0.0500", "0.0000", Finding.TRIGGERED, Severity.WATCH),  # 5.00pp
            ("0.1000", "0.0000", Finding.TRIGGERED, Severity.WATCH),  # 10.00pp WATCH-only
            ("0.1499", "0.0000", Finding.TRIGGERED, Severity.WATCH),  # 14.99pp
            ("0.1500", "0.0000", Finding.TRIGGERED, Severity.HIGH),   # 15.00pp
            ("0.1501", "0.0000", Finding.TRIGGERED, Severity.HIGH),   # 15.01pp
        ]
        for current, baseline, finding, severity in cases:
            outcome = self._evaluate(current, baseline)
            self.assertEqual(outcome.finding, finding, msg=current)
            self.assertEqual(outcome.severity, severity, msg=current)

    def test_negative_delta_benign(self):
        outcome = self._evaluate("0.2292", "0.2727")  # -4.35pp
        self.assertEqual(outcome.finding, Finding.BENIGN)
        self.assertEqual(outcome.delta_pp, Decimal("-4.3500"))

    def test_zero_delta_benign(self):
        outcome = self._evaluate("0.1150", "0.1150")
        self.assertEqual(outcome.finding, Finding.BENIGN)
        self.assertEqual(outcome.delta_pp, Decimal("0.0000"))

    def test_large_positive_delta_high(self):
        outcome = self._evaluate("1.0000", "0.2727")  # +72.73pp
        self.assertEqual(outcome.finding, Finding.TRIGGERED)
        self.assertEqual(outcome.severity, Severity.HIGH)
        self.assertEqual(outcome.delta_pp, Decimal("72.7300"))

    def test_delta_on_published_precision_grid(self):
        # published ratios are 4dp; delta_pp lands on the .01 grid
        outcome = self._evaluate("0.0500", "0.0000")
        self.assertEqual(outcome.delta_pp, Decimal("5.0000"))

    def test_below_floor_test_only_policy(self):
        policy = SignalPolicy(
            policy_version="AI003_TEST_ONLY_FLOOR",
            signal_id=SignalId.AR_OVERDUE_SPIKE,
            approval_status="APPROVED",
            policy_scope="DEMO_ONLY",
            data_mode_scope="ALL",
            approver="Test",
            approved_date=date(2026, 10, 2),
            validation_evidence="unit-test-only",
            floor=Decimal("100"),
            watch_threshold=Decimal("5.00"),
            high_threshold=Decimal("15.00"),
            threshold_unit=ThresholdUnit.PERCENTAGE_POINTS,
            precision="0.01",
            baseline_spec=None,
            window_days=None,
        )
        # Strictly below floor: not material -> BENIGN without threshold evaluation.
        outcome = evaluate_ar(policy, _snapshot("99.99", "0.1500"), _snapshot("1000", "0.0000"))
        self.assertEqual(outcome.finding, Finding.BENIGN)
        # Exactly at floor remains eligible -> 15pp delta evaluates HIGH.
        outcome = evaluate_ar(policy, _snapshot("100.00", "0.1500"), _snapshot("1000", "0.0000"))
        self.assertEqual(outcome.finding, Finding.TRIGGERED)
        self.assertEqual(outcome.severity, Severity.HIGH)


class APBoundaryTests(unittest.TestCase):
    """POLICY GOLD AP boundary table with D=400 and both display traps."""

    D = ["400"]

    def _evaluate(self, numerator, denominators=None, policy=None):
        policy = policy or resolve_policy(SignalId.AP_DUE_CLUSTER)
        if denominators is None:
            denominators = self.D
        return evaluate_ap(policy, _selection([numerator], denominators))

    def test_boundaries(self):
        cases = [
            ("199.99", Finding.BENIGN, None),      # display trap: 0.5000
            ("200", Finding.TRIGGERED, Severity.WATCH),     # exact .50
            ("250", Finding.TRIGGERED, Severity.WATCH),     # .625 WATCH-only
            ("299.99", Finding.TRIGGERED, Severity.WATCH),  # display trap: 0.7500
            ("300", Finding.TRIGGERED, Severity.HIGH),      # exact .75
            ("300.01", Finding.TRIGGERED, Severity.HIGH),   # beyond .75
        ]
        for numerator, finding, severity in cases:
            outcome = self._evaluate(numerator)
            self.assertEqual(outcome.finding, finding, msg=numerator)
            self.assertEqual(outcome.severity, severity, msg=numerator)

    def test_display_traps_are_not_operands(self):
        benign = self._evaluate("199.99")
        self.assertEqual(benign.display_share, Decimal("0.5000"))  # equals threshold on display
        self.assertEqual(benign.finding, Finding.BENIGN)  # but exact comparison says below
        watch = self._evaluate("299.99")
        self.assertEqual(watch.display_share, Decimal("0.7500"))
        self.assertEqual(watch.finding, Finding.TRIGGERED)
        self.assertEqual(watch.severity, Severity.WATCH)  # below HIGH on exact operands

    def test_non_terminating_share_exact_comparison(self):
        """METHOD GOLD: T=.33332 exact N>=T*D True vs rounded display False (V2-02)."""
        policy = SignalPolicy(
            policy_version="AI003_TEST_ONLY_FRACTION",
            signal_id=SignalId.AP_DUE_CLUSTER,
            approval_status="APPROVED",
            policy_scope="DEMO_ONLY",
            data_mode_scope="ALL",
            approver="Test",
            approved_date=date(2026, 10, 2),
            validation_evidence="unit-test-only",
            floor=Decimal("0"),
            watch_threshold=Decimal("0.33332"),
            high_threshold=Decimal("0.33332"),
            threshold_unit=ThresholdUnit.RATIO,
            precision="0.0001",
            baseline_spec=None,
            window_days=30,
        )
        outcome = self._evaluate("1", denominators=["3"], policy=policy)
        self.assertEqual(outcome.finding, Finding.TRIGGERED)  # 1 >= 0.99996 exactly
        self.assertEqual(outcome.severity, Severity.HIGH)  # equality -> HIGH band
        self.assertEqual(outcome.display_share, Decimal("0.3333"))

        # Same share display; threshold beyond it -> BENIGN despite display rounding.
        above = SignalPolicy(**{**policy.__dict__, "watch_threshold": Decimal("0.34"), "high_threshold": Decimal("0.34")})
        outcome = self._evaluate("1", denominators=["3"], policy=above)
        self.assertEqual(outcome.finding, Finding.BENIGN)

    def test_zero_numerator_with_positive_denominator(self):
        outcome = self._evaluate("0")  # N=0, D=400: floor equality eligible -> BENIGN
        self.assertEqual(outcome.finding, Finding.BENIGN)
        self.assertEqual(outcome.observed_value, Decimal("0"))

    def test_first_positive_full_share_is_high(self):
        outcome = self._evaluate("0.01", denominators=["0.01"])
        self.assertEqual(outcome.finding, Finding.TRIGGERED)
        self.assertEqual(outcome.severity, Severity.HIGH)

    def test_zero_denominator_inconclusive(self):
        with self.assertRaises(SourceFailure) as ctx:
            self._evaluate("0", denominators=[])
        self.assertEqual(ctx.exception.status, Status.INCONCLUSIVE)
        self.assertEqual(ctx.exception.reason_code, ReasonCode.ZERO_DENOMINATOR)


if __name__ == "__main__":
    unittest.main()
