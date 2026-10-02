"""AI003 Risk Signal typed contracts — contract V2.2 (reviewed method spec).

Normative sources (docs/features/AI003/):
- AI003_MASTER_SSOT.md §10 (typed contract), §16.4 (ordered evaluation),
  §16.5 (AP scope and identity), §16.6 (wire schema), §16.7 (evidence/agent),
  §19.2 (V2.2 first-failed-stage A1..A11).
- AI003_METHOD_GOLD_MANIFEST.yaml (66/66 PASS, method_version
  V2.2_REVIEWED_METHOD_SPEC) and AI003_POLICY_GOLD_EVIDENCE.md (17/17 PASS,
  policy AI003_DEMO_POLICY_V1).

Invariants enforced here (impossible states are unrepresentable):
- status != OK  -> finding/severity/triggered are None.
- OK + TRIGGERED -> triggered True and severity in (WATCH, HIGH).
- OK + BENIGN   -> triggered False and severity None.
- FORBIDDEN / VALIDATION_ERROR / SOURCE_ERROR carry no financial payload,
  no source/evidence refs and no explanation text.
- INCONCLUSIVE / POLICY_PENDING may carry only independently valid authorized
  partial values, never evaluation output.
- Money serializes at 2dp, ratios at 4dp, percentage points at 2dp, always
  fixed-point ROUND_HALF_UP, negative zero normalized (POLICY GOLD trap).

The owner task packet (2026-10-02) labels the AR method
"AI003_AR_SPIKE_PREV_MONTH_V1"; the executable identifier is the METHOD GOLD
manifest string METHOD_VERSION below. The packet label is a documented alias.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
from enum import Enum
from typing import Dict, Mapping, Optional, Tuple

FEATURE_ID = "AI003"
# Stable wire versions (explicitly chosen, not "draft"): the implementation
# contract is the reviewed V2.2 ruleset validated in SSOT §19.
CONTRACT_VERSION = "2.2.0"
METHOD_VERSION = "V2.2_REVIEWED_METHOD_SPEC"
DEMO_POLICY_VERSION = "AI003_DEMO_POLICY_V1"
ACCOUNTING_TIMEZONE = "Asia/Ho_Chi_Minh"
TEMPORAL_BASIS = "CURRENT_STATE_RECONSTRUCTED_BY_POSTING_DATE"

SIGNAL_ALLOWLIST = ("AR_OVERDUE_SPIKE", "AP_DUE_CLUSTER")

MAX_CORRELATION_ID_LENGTH = 128
REQUEST_ALLOWED_KEYS = frozenset({"company", "signal_id", "as_of_date", "correlation_id"})


class ContractViolation(ValueError):
    """A construction or parse attempt would create an impossible state."""


class SignalId(str, Enum):
    AR_OVERDUE_SPIKE = "AR_OVERDUE_SPIKE"
    AP_DUE_CLUSTER = "AP_DUE_CLUSTER"


class Status(str, Enum):
    OK = "OK"
    INCONCLUSIVE = "INCONCLUSIVE"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SOURCE_ERROR = "SOURCE_ERROR"
    POLICY_PENDING = "POLICY_PENDING"


class Finding(str, Enum):
    TRIGGERED = "TRIGGERED"
    BENIGN = "BENIGN"


class Severity(str, Enum):
    WATCH = "WATCH"
    HIGH = "HIGH"


class ReasonCode(str, Enum):
    # SSOT §16.6 minimum set
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    INVALID_REQUEST = "INVALID_REQUEST"
    FUTURE_AS_OF = "FUTURE_AS_OF"
    UNSUPPORTED_CURRENCY = "UNSUPPORTED_CURRENCY"
    FINANCE_BOOK_NOT_SUPPORTED = "FINANCE_BOOK_NOT_SUPPORTED"
    HISTORY_INSUFFICIENT = "HISTORY_INSUFFICIENT"
    INVALID_DENOMINATOR = "INVALID_DENOMINATOR"
    ZERO_DENOMINATOR = "ZERO_DENOMINATOR"
    INCOMPLETE_DUE_DATE_COVERAGE = "INCOMPLETE_DUE_DATE_COVERAGE"
    UNSUPPORTED_ALLOCATION_SCOPE = "UNSUPPORTED_ALLOCATION_SCOPE"
    INCONSISTENT_DATA = "INCONSISTENT_DATA"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_TIMEOUT = "SOURCE_TIMEOUT"
    POLICY_UNAVAILABLE = "POLICY_UNAVAILABLE"
    INVALID_POLICY_CONFIG = "INVALID_POLICY_CONFIG"
    UNSUPPORTED_SOURCE_VERSION = "UNSUPPORTED_SOURCE_VERSION"
    # Method-gold-observed codes (SSOT §16.5 / §17.4 / METHOD GOLD manifest)
    ACCESS_DENIED = "ACCESS_DENIED"
    UNSUPPORTED_COMPANY_CURRENCY = "UNSUPPORTED_COMPANY_CURRENCY"
    BASELINE_DENOMINATOR_INVALID = "BASELINE_DENOMINATOR_INVALID"
    CURRENT_DENOMINATOR_INVALID = "CURRENT_DENOMINATOR_INVALID"
    CONFLICTING_OBSERVATION = "CONFLICTING_OBSERVATION"
    SOURCE_INVALID = "SOURCE_INVALID"
    UNSUPPORTED_MULTI_SCHEDULE = "UNSUPPORTED_MULTI_SCHEDULE"
    POLICY_NOT_APPROVED = "POLICY_NOT_APPROVED"


class BaselineType(str, Enum):
    PREVIOUS_COMPARABLE_CUTOFF = "PREVIOUS_COMPARABLE_CUTOFF"
    NONE = "NONE"


class BaselineStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    HISTORY_INSUFFICIENT = "HISTORY_INSUFFICIENT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"


class ExplanationStatus(str, Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class SourceKind(str, Enum):
    AI001_METRIC = "AI001_METRIC"
    ERP_AP_REPORT = "ERP_AP_REPORT"
    ERP_DOCUMENT_METADATA = "ERP_DOCUMENT_METADATA"


class DataMode(str, Enum):
    LIVE = "LIVE"
    CONTROLLED_FIXTURE = "CONTROLLED_FIXTURE"


class CountBasis(str, Enum):
    DISTINCT_VOUCHER = "distinct_voucher"
    VERIFIED_INSTALLMENT = "verified_installment"


class Unit(str, Enum):
    VND = "VND"
    RATIO = "ratio"
    PERCENTAGE_POINTS = "percentage_points"
    COUNT = "count"


class MaterialityDefinition(str, Enum):
    CURRENT_NET_AR_TOTAL = "CURRENT_NET_AR_TOTAL"
    AP_DUE_WINDOW_AMOUNT = "AP_DUE_WINDOW_AMOUNT"


class ThresholdUnit(str, Enum):
    PERCENTAGE_POINTS = "percentage_points"
    RATIO = "ratio"


# Pipeline stages (SSOT §19.2 normative A1..A11 ordering, first failed wins).
class Stage(str, Enum):
    A1_AUTH = "A1_AUTH"
    A2_STRUCTURE = "A2_STRUCTURE"
    A3_COMPANY = "A3_COMPANY"
    A4_SEMANTIC_SCOPE = "A4_SEMANTIC_SCOPE"
    A5_SOURCE_AUTH = "A5_SOURCE_AUTH"
    A6_SOURCE_CURRENCY = "A6_SOURCE_CURRENCY"
    A7_INTEGRITY_IDENTITY = "A7_INTEGRITY_IDENTITY"
    A8_METHOD_PREREQ = "A8_METHOD_PREREQ"
    A9_POLICY = "A9_POLICY"
    A10_EVALUATION = "A10_EVALUATION"
    A11_EXPLANATION = "A11_EXPLANATION"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def serialize_decimal(value: Decimal, places: int) -> str:
    """Fixed-point ROUND_HALF_UP wire text; no exponent form; no negative zero.

    POLICY GOLD trap: values like Decimal('1E-5') or Decimal('-0.0') must never
    leak exponent/negative-zero text into the wire (first policy-gold run
    failed comparing '10000' vs '10000.0' lexically; serialization scales were
    then pinned money=2 / ratio=4 / pp=2).
    """
    if not isinstance(value, Decimal):
        raise ContractViolation("wire values must be Decimal, got %r" % type(value).__name__)
    quantum = Decimal(1).scaleb(-places)
    with localcontext() as ctx:
        ctx.prec = 60
        q = value.quantize(quantum, rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    text = format(q, "f")
    if "E" in text or "e" in text:
        raise ContractViolation("exponent form leaked into wire text: %s" % text)
    return text


def money_str(value: Decimal) -> str:
    return serialize_decimal(value, 2)


def ratio_str(value: Decimal) -> str:
    return serialize_decimal(value, 4)


def pp_str(value: Decimal) -> str:
    return serialize_decimal(value, 2)


def parse_strict_date(text: object, field_name: str) -> date:
    """Strict YYYY-MM-DD only; no datetime, no loose formats, no whitespace."""
    if not isinstance(text, str):
        raise ContractViolation("%s must be a YYYY-MM-DD string" % field_name)
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        raise ContractViolation("%s must be strict YYYY-MM-DD" % field_name)
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ContractViolation("%s is not a valid calendar date: %s" % (field_name, text)) from exc


@dataclass(frozen=True)
class SignalRequest:
    """SSOT §16.6: additional_properties false; client supplies scope/date/signal only."""

    company: str
    signal_id: SignalId
    as_of_date: date
    correlation_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.company, str) or not self.company.strip():
            raise ContractViolation("company must be a nonempty string")
        if not isinstance(self.signal_id, SignalId):
            raise ContractViolation("signal_id must be an allowed SignalId")
        if not isinstance(self.as_of_date, date):
            raise ContractViolation("as_of_date must be a parsed date")
        if self.correlation_id is not None:
            if not isinstance(self.correlation_id, str) or not self.correlation_id:
                raise ContractViolation("correlation_id must be a nonempty string or None")
            if len(self.correlation_id) > MAX_CORRELATION_ID_LENGTH:
                raise ContractViolation("correlation_id exceeds bounded length")


def parse_signal_request(payload: Mapping) -> SignalRequest:
    """Parse an untrusted request mapping; unknown keys are rejected, never ignored."""
    if not isinstance(payload, Mapping):
        raise ContractViolation("request payload must be a mapping")
    unknown = set(payload.keys()) - REQUEST_ALLOWED_KEYS
    if unknown:
        raise ContractViolation("unsupported request keys: %s" % ",".join(sorted(unknown)))
    company = payload.get("company")
    if not isinstance(company, str) or not company.strip():
        raise ContractViolation("company must be a nonempty string")
    signal_raw = payload.get("signal_id")
    try:
        signal_id = SignalId(signal_raw)
    except ValueError as exc:
        raise ContractViolation("signal_id must be one of %s" % (SIGNAL_ALLOWLIST,)) from exc
    as_of = parse_strict_date(payload.get("as_of_date"), "as_of_date")
    correlation_id = payload.get("correlation_id")
    if correlation_id is not None and (
        not isinstance(correlation_id, str) or not correlation_id
    ):
        raise ContractViolation("correlation_id must be a nonempty string or None")
    if isinstance(correlation_id, str) and len(correlation_id) > MAX_CORRELATION_ID_LENGTH:
        raise ContractViolation("correlation_id exceeds bounded length")
    return SignalRequest(
        company=company,
        signal_id=signal_id,
        as_of_date=as_of,
        correlation_id=correlation_id,
    )


@dataclass(frozen=True)
class SourceRef:
    """SSOT §16.6 source_refs entry: versioned, cutoff-bound provenance."""

    kind: SourceKind
    cutoff: date
    captured_at: str
    contract_version: Optional[str] = None
    formula_version: Optional[str] = None
    source_schema_version: Optional[str] = None


@dataclass(frozen=True)
class BaselineBlock:
    type: BaselineType
    status: BaselineStatus
    value: Optional[Decimal] = None
    denominator: Optional[Decimal] = None
    cutoff: Optional[date] = None
    resolver_version: Optional[str] = None


@dataclass(frozen=True)
class ObservedBlock:
    value: Optional[Decimal] = None
    unit: Unit = Unit.RATIO
    supporting_amount: Optional[Decimal] = None
    supporting_amount_definition: Optional[MaterialityDefinition] = None


@dataclass(frozen=True)
class RuleBlock:
    """Approved threshold/materiality as evaluated (server-owned, never client-supplied).

    ``threshold`` is the WATCH-band (first TRIGGERED) threshold; ``high_threshold``
    is the HIGH band. Both evaluate with GTE; HIGH runs first (V2.2).
    """

    threshold: Optional[Decimal] = None
    threshold_unit: Optional[ThresholdUnit] = None
    comparator: str = "GTE"
    high_threshold: Optional[Decimal] = None
    floor: Optional[Decimal] = None
    materiality_unit: Unit = Unit.VND
    materiality_definition: Optional[MaterialityDefinition] = None
    window_start: Optional[date] = None
    window_end: Optional[date] = None


@dataclass(frozen=True)
class EvidenceRef:
    """Discriminated evidence reference; never an authorization token (SSOT §16.7)."""

    kind: str  # REPORT_SNAPSHOT | DOCUMENT
    company: str
    ref: str
    as_of_date: Optional[date] = None
    captured_at: Optional[str] = None


@dataclass(frozen=True)
class Coverage:
    missing_inputs: Tuple[str, ...] = ()
    history: Optional[str] = None
    identity: Optional[str] = None
    precision: Optional[str] = None


@dataclass(frozen=True)
class Explanation:
    status: ExplanationStatus = ExplanationStatus.NOT_REQUESTED
    text: Optional[str] = None
    reason_code: Optional[str] = None


_EMPTY_COVERAGE = Coverage()


@dataclass(frozen=True)
class SignalResult:
    """Merged normative envelope: SSOT §10 shape + §16.6 additions + §19.2 stage trace.

    stage_trace records, in order, every pipeline stage entered (including the
    stage that failed) — safe debug metadata, never raw internals.
    """

    signal_id: SignalId
    status: Status
    reason_code: Optional[ReasonCode] = None
    finding: Optional[Finding] = None
    severity: Optional[Severity] = None
    triggered: Optional[bool] = None
    observed: Optional[ObservedBlock] = None
    delta_pp: Optional[Decimal] = None
    baseline: Optional[BaselineBlock] = None
    rule: Optional[RuleBlock] = None
    count_basis: Optional[CountBasis] = None
    count_positive_vouchers: Optional[int] = None
    count_due_vouchers: Optional[int] = None
    policy_version: Optional[str] = None
    policy_scope: Optional[str] = None
    production_calibrated: Optional[bool] = None
    source_refs: Tuple[SourceRef, ...] = ()
    evidence: Tuple[EvidenceRef, ...] = ()
    coverage: Coverage = _EMPTY_COVERAGE
    limitations: Tuple[str, ...] = ()
    as_of_date: Optional[date] = None
    accounting_timezone: str = ACCOUNTING_TIMEZONE
    generated_at: str = field(default_factory=utc_now_iso)
    data_mode: Optional[DataMode] = None
    correlation_id: Optional[str] = None
    explanation: Explanation = field(default_factory=Explanation)
    stage_trace: Tuple[str, ...] = ()
    feature_id: str = FEATURE_ID
    contract_version: str = CONTRACT_VERSION
    method_version: str = METHOD_VERSION

    def __post_init__(self) -> None:
        _validate_result(self)


def _validate_result(r: SignalResult) -> None:
    if not isinstance(r.status, Status):
        raise ContractViolation("status must be a Status")
    if r.triggered is not None and not isinstance(r.triggered, bool):
        raise ContractViolation("triggered must be a bool or None (no bool-as-int)")
    if r.finding is not None and not isinstance(r.finding, Finding):
        raise ContractViolation("finding must be a Finding")
    if r.severity is not None and not isinstance(r.severity, Severity):
        raise ContractViolation("severity must be a Severity")
    if r.reason_code is not None and not isinstance(r.reason_code, ReasonCode):
        raise ContractViolation("reason_code must be a ReasonCode")
    if r.accounting_timezone != ACCOUNTING_TIMEZONE:
        raise ContractViolation("accounting_timezone is fixed to %s" % ACCOUNTING_TIMEZONE)

    if r.status is Status.OK:
        if r.finding is None:
            raise ContractViolation("OK requires a finding")
        if r.finding is Finding.TRIGGERED:
            if r.triggered is not True:
                raise ContractViolation("OK+TRIGGERED requires triggered=True")
            if r.severity not in (Severity.WATCH, Severity.HIGH):
                raise ContractViolation("OK+TRIGGERED requires severity WATCH/HIGH")
        else:
            if r.triggered is not False:
                raise ContractViolation("OK+BENIGN requires triggered=False")
            if r.severity is not None:
                raise ContractViolation("OK+BENIGN must not carry severity")
        if r.as_of_date is None or r.data_mode is None:
            raise ContractViolation("OK requires as_of_date and data_mode")
    else:
        if r.finding is not None or r.severity is not None or r.triggered is not None:
            raise ContractViolation("status %s must not carry finding/severity/triggered" % r.status.value)

    if r.status in (Status.FORBIDDEN, Status.VALIDATION_ERROR, Status.SOURCE_ERROR):
        _assert_no_financial_payload(r)
        if r.status is Status.FORBIDDEN and (r.limitations or r.explanation.text):
            raise ContractViolation("FORBIDDEN carries no limitations or explanation text")

    if r.status is Status.POLICY_PENDING:
        if r.reason_code not in (ReasonCode.POLICY_NOT_APPROVED, ReasonCode.POLICY_UNAVAILABLE):
            raise ContractViolation("POLICY_PENDING requires a pending-policy reason code")

    if r.status is Status.OK and r.reason_code is not None:
        raise ContractViolation("OK does not carry a reason code")

    for stage in r.stage_trace:
        try:
            Stage(stage)
        except ValueError as exc:
            raise ContractViolation("unknown stage in trace: %s" % stage) from exc

    if r.evidence or r.source_refs:
        for ref in r.evidence:
            if not isinstance(ref, EvidenceRef):
                raise ContractViolation("evidence entries must be EvidenceRef")
        for ref in r.source_refs:
            if not isinstance(ref, SourceRef):
                raise ContractViolation("source_refs entries must be SourceRef")


def _assert_no_financial_payload(r: SignalResult) -> None:
    payload_fields = (
        r.observed,
        r.delta_pp,
        r.baseline,
        r.rule,
        r.count_positive_vouchers,
        r.count_due_vouchers,
    )
    if any(f is not None for f in payload_fields):
        raise ContractViolation("status %s must not carry financial payload" % r.status.value)
    if r.source_refs or r.evidence:
        raise ContractViolation("status %s must not carry source/evidence refs" % r.status.value)
    if r.coverage.missing_inputs or r.coverage.history or r.coverage.identity or r.coverage.precision:
        raise ContractViolation("status %s must not carry coverage detail" % r.status.value)
    if r.limitations:
        raise ContractViolation("status %s must not carry limitations" % r.status.value)
    if r.explanation.text is not None:
        raise ContractViolation("status %s must not carry explanation text" % r.status.value)


def forbidden_result(
    signal_id: Optional[SignalId],
    stage_trace: Tuple[str, ...],
    correlation_id: Optional[str] = None,
    reason_code: ReasonCode = ReasonCode.ACCESS_DENIED,
) -> SignalResult:
    """Generic denial envelope: no company identity, no financial/evidence payload."""
    return SignalResult(
        signal_id=signal_id if signal_id is not None else SignalId.AR_OVERDUE_SPIKE,
        status=Status.FORBIDDEN,
        reason_code=reason_code,
        correlation_id=correlation_id,
        stage_trace=stage_trace,
    )


def result_to_dict(result: SignalResult, include_debug: bool = False) -> Dict:
    """Strict wire serialization. Decimal fields serialize at pinned scales."""

    def dec(value: Optional[Decimal], places: int) -> Optional[str]:
        return None if value is None else serialize_decimal(value, places)

    payload: Dict = {
        "feature_id": result.feature_id,
        "contract_version": result.contract_version,
        "method_version": result.method_version,
        "signal_id": result.signal_id.value,
        "status": result.status.value,
        "accounting_timezone": result.accounting_timezone,
        "temporal_basis": TEMPORAL_BASIS,
        "generated_at": result.generated_at,
        "correlation_id": result.correlation_id,
    }
    if result.status is Status.FORBIDDEN:
        # Generic denial: only status/reason/correlation/generated_at/contract metadata.
        payload["reason_code"] = result.reason_code.value if result.reason_code else None
        if include_debug:
            payload["stage_trace"] = list(result.stage_trace)
        return payload

    payload.update(
        {
            "reason_code": result.reason_code.value if result.reason_code else None,
            "finding": result.finding.value if result.finding else None,
            "severity": result.severity.value if result.severity else None,
            "triggered": result.triggered,
            "as_of_date": result.as_of_date.isoformat() if result.as_of_date else None,
            "data_mode": result.data_mode.value if result.data_mode else None,
            "policy_version": result.policy_version,
            "policy_scope": result.policy_scope,
            "production_calibrated": result.production_calibrated,
            "delta_pp": dec(result.delta_pp, 2),
            "count_basis": result.count_basis.value if result.count_basis else None,
            "count_positive_vouchers": result.count_positive_vouchers,
            "count_due_vouchers": result.count_due_vouchers,
            "limitations": list(result.limitations),
            "stage_trace": list(result.stage_trace),
        }
    )
    if result.observed is not None:
        payload["observed"] = {
            "value": dec(result.observed.value, 4),
            "unit": result.observed.unit.value,
            "supporting_amount": dec(result.observed.supporting_amount, 2),
            "supporting_amount_definition": (
                result.observed.supporting_amount_definition.value
                if result.observed.supporting_amount_definition
                else None
            ),
        }
    else:
        payload["observed"] = None
    if result.baseline is not None:
        payload["baseline"] = {
            "type": result.baseline.type.value,
            "status": result.baseline.status.value,
            "value": dec(result.baseline.value, 4),
            "denominator": dec(result.baseline.denominator, 2),
            "cutoff": result.baseline.cutoff.isoformat() if result.baseline.cutoff else None,
            "resolver_version": result.baseline.resolver_version,
        }
    else:
        payload["baseline"] = None
    if result.rule is not None:
        # Threshold scale follows its unit: pp at 2dp, ratio at 4dp.
        threshold_places = 2 if result.rule.threshold_unit is ThresholdUnit.PERCENTAGE_POINTS else 4
        payload["rule"] = {
            "threshold": dec(result.rule.threshold, threshold_places),
            "threshold_unit": result.rule.threshold_unit.value if result.rule.threshold_unit else None,
            "comparator": result.rule.comparator,
            "high_threshold": dec(result.rule.high_threshold, threshold_places),
            "floor": dec(result.rule.floor, 2),
            "materiality_unit": result.rule.materiality_unit.value,
            "materiality_definition": (
                result.rule.materiality_definition.value
                if result.rule.materiality_definition
                else None
            ),
            "window_start": result.rule.window_start.isoformat() if result.rule.window_start else None,
            "window_end": result.rule.window_end.isoformat() if result.rule.window_end else None,
        }
    else:
        payload["rule"] = None
    payload["source_refs"] = [
        {
            "kind": ref.kind.value,
            "contract_version": ref.contract_version,
            "formula_version": ref.formula_version,
            "source_schema_version": ref.source_schema_version,
            "cutoff": ref.cutoff.isoformat(),
            "captured_at": ref.captured_at,
        }
        for ref in result.source_refs
    ]
    payload["evidence"] = [
        {
            "kind": ref.kind,
            "company": ref.company,
            "ref": ref.ref,
            "as_of_date": ref.as_of_date.isoformat() if ref.as_of_date else None,
            "captured_at": ref.captured_at,
        }
        for ref in result.evidence
    ]
    payload["coverage"] = {
        "missing_inputs": list(result.coverage.missing_inputs),
        "history": result.coverage.history,
        "identity": result.coverage.identity,
        "precision": result.coverage.precision,
    }
    payload["explanation"] = {
        "status": result.explanation.status.value,
        "text": result.explanation.text,
        "reason_code": result.explanation.reason_code,
    }
    return payload


def json_dumps(payload: Dict) -> str:
    return json.dumps(payload, sort_keys=True)
