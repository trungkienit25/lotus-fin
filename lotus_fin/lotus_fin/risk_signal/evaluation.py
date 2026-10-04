"""AI003 deterministic evaluation engines (S3).

AR (AR_OVERDUE_SPIKE, method V2.2_REVIEWED_METHOD_SPEC):
    delta_pp = (current_published_ratio - baseline_published_ratio) * 100
    computed from AI001's published 4-decimal ratios via Decimal(str(...)) —
    the .01pp grid. Materiality gates CURRENT_NET_AR_TOTAL with strict <.
    HIGH evaluated first with >=, then WATCH with >=, else BENIGN.

AP (AP_DUE_CLUSTER):
    Authoritative comparison is exact N >= T * D (finite Decimal operands,
    headroom context) — the rounded 4dp display share is NEVER an operand
    (V2-02; both POLICY GOLD display traps). D > 0 required; materiality
    gates AP_DUE_WINDOW_AMOUNT (N) with strict <; HIGH before WATCH.

Zero/negative denominators and out-of-domain numerators are method-prerequisite
failures (stage A8/A10 family -> INCONCLUSIVE with typed reason codes); they
are never BENIGN and never POLICY_PENDING.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Optional

from lotus_fin.risk_signal.contracts import (
    Finding,
    MaterialityDefinition,
    ReasonCode,
    Severity,
    Status,
    ThresholdUnit,
)
from lotus_fin.risk_signal.coverage import APSelection, sum_amounts
from lotus_fin.risk_signal.policy import SignalPolicy
from lotus_fin.risk_signal.provenance import SourceFailure

_EVAL_PRECISION = 60  # operand-derived headroom for finite money/ratio operands


@dataclass(frozen=True)
class EvaluationOutcome:
    """Pure evaluation result; the service composes the SignalResult envelope."""

    finding: Finding
    severity: Optional[Severity]
    observed_value: Optional[Decimal]  # AR: published ratio; AP: exact N/D
    supporting_amount: Optional[Decimal]  # AR: CURRENT_NET_AR_TOTAL; AP: N
    delta_pp: Optional[Decimal]  # AR only
    baseline_value: Optional[Decimal]  # AR only (published baseline ratio)
    baseline_denominator: Optional[Decimal]  # AR only
    numerator: Optional[Decimal]  # AP only
    denominator: Optional[Decimal]  # AP only
    display_share: Optional[Decimal]  # AP only: 4dp HALF_UP display operand


def _gte(value: Decimal, threshold: Decimal) -> bool:
    with localcontext() as ctx:
        ctx.prec = _EVAL_PRECISION
        return value >= threshold


def _ap_failure(status: Status, reason: ReasonCode, message: str) -> SourceFailure:
    return SourceFailure(status, reason, message)


def evaluate_ar(policy: SignalPolicy, current, baseline) -> EvaluationOutcome:
    """AR delta evaluation on the published-ratio .01pp grid (gold-pinned)."""
    with localcontext() as ctx:
        ctx.prec = _EVAL_PRECISION
        delta_pp = (current.overdue_ratio - baseline.overdue_ratio) * Decimal(100)
        delta_pp = +delta_pp

    # Materiality gates the CURRENT NET AR TOTAL (SSOT §16.3), strict <.
    if current.total_ar < policy.floor:
        finding, severity = Finding.BENIGN, None
    elif _gte(delta_pp, policy.high_threshold):
        finding, severity = Finding.TRIGGERED, Severity.HIGH  # HIGH before WATCH
    elif _gte(delta_pp, policy.watch_threshold):
        finding, severity = Finding.TRIGGERED, Severity.WATCH
    else:
        finding, severity = Finding.BENIGN, None

    return EvaluationOutcome(
        finding=finding,
        severity=severity,
        observed_value=current.overdue_ratio,
        supporting_amount=current.total_ar,
        delta_pp=delta_pp,
        baseline_value=baseline.overdue_ratio,
        baseline_denominator=baseline.total_ar,
        numerator=None,
        denominator=None,
        display_share=None,
    )


def evaluate_ap(policy: SignalPolicy, selection: APSelection) -> EvaluationOutcome:
    """AP D0..D30 concentration with exact N >= T*D comparison (V2-02)."""
    numerator = sum_amounts(selection.numerator)
    denominator = sum_amounts(selection.denominator)
    if denominator < 0:
        raise _ap_failure(
            Status.INCONCLUSIVE, ReasonCode.INVALID_DENOMINATOR, "negative AP denominator"
        )
    if denominator == 0:
        raise _ap_failure(
            Status.INCONCLUSIVE,
            ReasonCode.ZERO_DENOMINATOR,
            "positive future AP denominator is zero",
        )
    if numerator < 0 or numerator > denominator:
        raise _ap_failure(
            Status.INCONCLUSIVE,
            ReasonCode.INCONSISTENT_DATA,
            "AP numerator outside [0, D]",
        )

    with localcontext() as ctx:
        ctx.prec = _EVAL_PRECISION
        exact_share = numerator / denominator
        high_product = policy.high_threshold * denominator
        watch_product = policy.watch_threshold * denominator
    # Display-only quantization: 4dp HALF_UP, never an operand (V2-02).
    with localcontext() as ctx:
        ctx.prec = _EVAL_PRECISION
        display_share = exact_share.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    # Materiality gates the DUE WINDOW AMOUNT N (SSOT §16.3), strict <.
    if numerator < policy.floor:
        finding, severity = Finding.BENIGN, None
    elif _gte(numerator, high_product):
        finding, severity = Finding.TRIGGERED, Severity.HIGH  # HIGH before WATCH
    elif _gte(numerator, watch_product):
        finding, severity = Finding.TRIGGERED, Severity.WATCH
    else:
        finding, severity = Finding.BENIGN, None

    return EvaluationOutcome(
        finding=finding,
        severity=severity,
        observed_value=+exact_share,
        supporting_amount=numerator,
        delta_pp=None,
        baseline_value=None,
        baseline_denominator=None,
        numerator=numerator,
        denominator=denominator,
        display_share=display_share,
    )


def materiality_definition_for(policy: SignalPolicy) -> MaterialityDefinition:
    if policy.threshold_unit is ThresholdUnit.PERCENTAGE_POINTS:
        return MaterialityDefinition.CURRENT_NET_AR_TOTAL
    return MaterialityDefinition.AP_DUE_WINDOW_AMOUNT
