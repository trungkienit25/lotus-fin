"""AI003 policy registry (S3) — immutable, versioned, server-resolved (SSOT §16.4).

The client can never pass policy, thresholds, floors or baseline/window specs
(SignalRequest has no such fields — additional_properties false). The registry
resolves the active policy server-side:

- healthy registry entry with approval_status=PENDING_APPROVAL -> POLICY_PENDING
  (reason POLICY_NOT_APPROVED) — only after all method prerequisites pass;
- missing active version, malformed, partial or invalid-configuration entries
  -> SOURCE_ERROR / INVALID_POLICY_CONFIG (never silent POLICY_PENDING);
- approved entry -> deterministic evaluation with the owner-approved constants.

Bounded by AI003_DEMO_POLICY_V1 (owner-approved 2026-10-02, DEMO_ONLY,
production_calibrated=false — NOT APPROVED FOR PRODUCTION, no promotion path).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional

from lotus_fin.risk_signal.contracts import (
    DEMO_POLICY_VERSION,
    ReasonCode,
    SignalId,
    Status,
    ThresholdUnit,
    Unit,
)
from lotus_fin.risk_signal.coverage import AP_WINDOW_DAYS, BASELINE_RESOLVER_VERSION
from lotus_fin.risk_signal.provenance import SourceFailure

APPROVAL_APPROVED = "APPROVED"
APPROVAL_PENDING = "PENDING_APPROVAL"


class PolicyPending(Exception):
    """A registered but unapproved policy: stage A9 outcome POLICY_PENDING."""

    def __init__(self, reason_code: ReasonCode = ReasonCode.POLICY_NOT_APPROVED) -> None:
        super().__init__(reason_code.value)
        self.reason_code = reason_code


@dataclass(frozen=True)
class SignalPolicy:
    """Immutable approved policy record (SSOT §16.4 validity constraints)."""

    policy_version: str
    signal_id: SignalId
    approval_status: str
    policy_scope: str  # DEMO_ONLY
    data_mode_scope: str  # ALL | LIVE | CONTROLLED_FIXTURE
    approver: str
    approved_date: date
    validation_evidence: str
    floor: Decimal  # materiality floor, VND
    watch_threshold: Decimal
    high_threshold: Decimal
    threshold_unit: ThresholdUnit
    precision: str  # display quantum, e.g. "0.0001"
    baseline_spec: Optional[str]  # AR resolver version; None for AP
    window_days: Optional[int]  # AP W=30; None for AR
    production_calibrated: bool = False
    materiality_unit: Unit = Unit.VND
    comparator: str = "GTE"

    def __post_init__(self) -> None:
        if self.production_calibrated:
            raise ValueError("no production-calibrated policy may be registered in this scope")
        for value in (self.floor, self.watch_threshold, self.high_threshold):
            if not isinstance(value, Decimal) or not value.is_finite():
                raise ValueError("policy constants must be finite Decimals")
        if self.floor < 0:
            raise ValueError("materiality floor must be nonnegative")
        if self.high_threshold < self.watch_threshold:
            raise ValueError("reversed thresholds (HIGH < WATCH)")
        if self.threshold_unit is ThresholdUnit.PERCENTAGE_POINTS:
            if self.watch_threshold < 0:
                raise ValueError("AR PP thresholds must be nonnegative")
        elif self.threshold_unit is ThresholdUnit.RATIO:
            for value in (self.watch_threshold, self.high_threshold):
                if not (Decimal(0) <= value <= Decimal(1)):
                    raise ValueError("AP thresholds must lie in [0,1]")
        else:
            raise ValueError("unsupported threshold unit")
        if self.window_days is not None and (not isinstance(self.window_days, int) or self.window_days < 0):
            raise ValueError("window W must be a nonnegative integer")
        if self.approval_status not in (APPROVAL_APPROVED, APPROVAL_PENDING):
            raise ValueError("unknown approval status")


def _decimal(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("invalid policy constant %r" % text) from exc
    if not value.is_finite():
        raise ValueError("policy constant must be finite")
    return value


_AR_DEMO = SignalPolicy(
    policy_version=DEMO_POLICY_VERSION,
    signal_id=SignalId.AR_OVERDUE_SPIKE,
    approval_status=APPROVAL_APPROVED,
    policy_scope="DEMO_ONLY",
    data_mode_scope="ALL",
    approver="Project Owner",
    approved_date=date(2026, 10, 2),
    validation_evidence="AI003_POLICY_GOLD_EVIDENCE.md (17 REQUIRED PASS / 4 NOT_APPLICABLE)",
    floor=_decimal("0"),
    watch_threshold=_decimal("5.00"),
    high_threshold=_decimal("15.00"),
    threshold_unit=ThresholdUnit.PERCENTAGE_POINTS,
    precision="0.01",
    baseline_spec=BASELINE_RESOLVER_VERSION,
    window_days=None,
)

_AP_DEMO = SignalPolicy(
    policy_version=DEMO_POLICY_VERSION,
    signal_id=SignalId.AP_DUE_CLUSTER,
    approval_status=APPROVAL_APPROVED,
    policy_scope="DEMO_ONLY",
    data_mode_scope="ALL",
    approver="Project Owner",
    approved_date=date(2026, 10, 2),
    validation_evidence="AI003_POLICY_GOLD_EVIDENCE.md (17 REQUIRED PASS / 4 NOT_APPLICABLE)",
    floor=_decimal("0"),
    watch_threshold=_decimal("0.50"),
    high_threshold=_decimal("0.75"),
    threshold_unit=ThresholdUnit.RATIO,
    precision="0.0001",
    baseline_spec=None,
    window_days=AP_WINDOW_DAYS,
)

# (signal_id, policy_version) -> policy. Immutable at runtime; future policy
# versions are added by a new explicit release, never by client input.
_REGISTRY: Dict[tuple, SignalPolicy] = {
    (SignalId.AR_OVERDUE_SPIKE, DEMO_POLICY_VERSION): _AR_DEMO,
    (SignalId.AP_DUE_CLUSTER, DEMO_POLICY_VERSION): _AP_DEMO,
}

# Server-side active version resolution (no client-supplied policy version).
_ACTIVE_VERSIONS: Dict[SignalId, str] = {
    SignalId.AR_OVERDUE_SPIKE: DEMO_POLICY_VERSION,
    SignalId.AP_DUE_CLUSTER: DEMO_POLICY_VERSION,
}


def resolve_policy(signal_id: SignalId) -> SignalPolicy:
    """Stage A9: resolve the active policy for a signal, fail-closed.

    Raises PolicyPending (-> POLICY_PENDING) for registered-but-unapproved
    policies and SourceFailure INVALID_POLICY_CONFIG for missing or invalid
    active configuration.
    """
    active_version = _ACTIVE_VERSIONS.get(signal_id)
    if active_version is None:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.INVALID_POLICY_CONFIG,
            "no active policy version configured for %s" % signal_id.value,
        )
    policy = _REGISTRY.get((signal_id, active_version))
    if policy is None:
        raise SourceFailure(
            Status.SOURCE_ERROR,
            ReasonCode.INVALID_POLICY_CONFIG,
            "active policy version %s is not registered" % active_version,
        )
    if policy.approval_status == APPROVAL_PENDING:
        raise PolicyPending(ReasonCode.POLICY_NOT_APPROVED)
    return policy
