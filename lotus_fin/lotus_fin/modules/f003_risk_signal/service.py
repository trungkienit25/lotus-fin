"""AI003 service (S5) — first-failed-stage pipeline A1..A11 (SSOT §19.2).

Sole normative ordering; the first failed stage wins and is never replaced by
a later outcome. Outcome mapping (gold-pinned): stage-A failure -> FORBIDDEN,
B -> VALIDATION_ERROR, C -> FORBIDDEN, D -> SOURCE_ERROR, E -> INCONCLUSIVE,
F -> POLICY_PENDING.

Synchronous request-context only: every evaluation runs under the checked
session user; there is no ambient Administrator path and no queue/background
execution (a missing session user fails closed at A1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Mapping, Optional, Tuple

from lotus_fin.modules.f003_risk_signal import evaluation as evaluation_mod
from lotus_fin.modules.f003_risk_signal.contracts import (
    BaselineBlock,
    BaselineStatus,
    BaselineType,
    CountBasis,
    Coverage,
    DataMode,
    EvidenceRef,
    Explanation,
    ExplanationStatus,
    Finding,
    MaterialityDefinition,
    ObservedBlock,
    ReasonCode,
    RuleBlock,
    SignalId,
    SignalRequest,
    SignalResult,
    SourceKind,
    SourceRef,
    Stage,
    Status,
    Unit,
    forbidden_result,
    parse_signal_request,
    utc_now_iso,
)
from lotus_fin.modules.f003_risk_signal.coverage import (
    previous_month_same_day,
    resolve_due_dates,
    select_ap_observations,
)
from lotus_fin.modules.f003_risk_signal.evidence import (
    EvidenceStorageUnavailable,
    ReplayResult,
    ReplayOutcome,
    create_evidence_record,
    evidence_get,
)
from lotus_fin.modules.f003_risk_signal.observability import LatencyTimer, log_ai003_event
from lotus_fin.modules.f003_risk_signal.policy import PolicyPending, resolve_policy
from lotus_fin.modules.f003_risk_signal.provenance import (
    SourceFailure,
    distinct_voucher_count,
    gate_company_currency,
    reconcile_observations,
)
from lotus_fin.modules.f003_risk_signal.sources import (
    AI001PublicARProvider,
    APReportAdapter,
    FrappeScheduleMetadataProvider,
    SUPPORTED_AP_SOURCE_DOC_TYPES,
    fetch_ar_pair,
)

AR_BASELINE_SPEC = "PREVIOUS_MONTH_SAME_DAY_CLAMP_V1"


@dataclass
class ServiceDeps:
    """Injected boundary bundle (DIP): hermetic tests provide fakes, the API
    layer wires the Frappe-bound adapters."""

    company_verifier: Callable[[str], str]
    currency_provider: Callable[[str], str]
    today_provider: Callable[[], date]
    ar_provider: object
    ap_provider: object
    schedule_provider: object
    data_mode: DataMode
    report_permission: Callable[[str], bool]


def _is_authenticated(user: Optional[str]) -> bool:
    return bool(user) and user not in ("Guest", "")


def evaluate_signal(
    payload: Mapping,
    *,
    checked_user: Optional[str],
    deps: ServiceDeps,
    include_explanation: bool = False,
    explain: Optional[Callable] = None,
) -> SignalResult:
    """Run the A1..A11 pipeline for one evaluation request."""
    timer = LatencyTimer()
    trace: Tuple[str, ...] = ()

    def _enter(stage: Stage) -> None:
        nonlocal trace
        trace = trace + (stage.value,)

    # --- A1 Authentication (no company lookup, no structural validation yet) ---
    _enter(Stage.A1_AUTH)
    if not _is_authenticated(checked_user):
        return _finish(
            forbidden_result(None, trace, _correlation(payload), ReasonCode.UNAUTHORIZED_ACCESS),
            timer,
            checked_user,
        )
    correlation_id = _correlation(payload)

    # --- A2 Structural request validation (shape only; no company resolution) ---
    _enter(Stage.A2_STRUCTURE)
    try:
        request = parse_signal_request(payload)
    except Exception:
        return _finish(
            SignalResult(
                signal_id=SignalId.AR_OVERDUE_SPIKE,  # placeholder id; no scope resolved
                status=Status.VALIDATION_ERROR,
                reason_code=ReasonCode.INVALID_REQUEST,
                correlation_id=correlation_id,
                stage_trace=trace,
            ),
            timer,
            checked_user,
        )

    # --- A3 Company authorization (untrusted company param -> verified scope) ---
    _enter(Stage.A3_COMPANY)
    try:
        verified_company = deps.company_verifier(request.company)
    except Exception:
        return _finish(
            forbidden_result(request.signal_id, trace, correlation_id, ReasonCode.ACCESS_DENIED),
            timer,
            checked_user,
        )

    # --- A4 Supported semantic scope (future-date rejection in company tz) ---
    _enter(Stage.A4_SEMANTIC_SCOPE)
    today = deps.today_provider()
    if request.as_of_date > today:
        return _finish(
            SignalResult(
                signal_id=request.signal_id,
                status=Status.VALIDATION_ERROR,
                reason_code=ReasonCode.FUTURE_AS_OF,
                correlation_id=correlation_id,
                stage_trace=trace,
            ),
            timer,
            checked_user,
        )

    # --- A5 Source/resource authorization (checked user, explicit report allowlist) ---
    _enter(Stage.A5_SOURCE_AUTH)
    required_report = "Accounts Receivable" if request.signal_id is SignalId.AR_OVERDUE_SPIKE else "Accounts Payable"
    try:
        if not deps.report_permission(required_report):
            raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "report permission denied")
    except SourceFailure:
        return _finish(
            forbidden_result(request.signal_id, trace, correlation_id, ReasonCode.ACCESS_DENIED),
            timer,
            checked_user,
        )

    captured_at = utc_now_iso()
    baseline_cutoff: Optional[date] = None
    if request.signal_id is SignalId.AR_OVERDUE_SPIKE:
        baseline_cutoff = previous_month_same_day(request.as_of_date)

    # --- A6 Source + currency validation ---
    _enter(Stage.A6_SOURCE_CURRENCY)
    try:
        gate_company_currency(deps.currency_provider(verified_company))
        ap_snapshot = None
        ar_pair = None
        if request.signal_id is SignalId.AR_OVERDUE_SPIKE:
            ar_pair = fetch_ar_pair(deps.ar_provider, verified_company, request.as_of_date, baseline_cutoff)
        else:
            ap_snapshot = deps.ap_provider.fetch(verified_company, request.as_of_date)
    except SourceFailure as failure:
        return _finish(
            _typed_failure_result(request, failure, trace, correlation_id),
            timer,
            checked_user,
        )

    # --- A7 Integrity + identity (dedupe/conflict precedes aggregation) ---
    _enter(Stage.A7_INTEGRITY_IDENTITY)
    reconciled = ()
    if request.signal_id is SignalId.AP_DUE_CLUSTER:
        try:
            if any(row.currency not in ("", "VND") for row in ap_snapshot.rows):
                raise SourceFailure(
                    Status.SOURCE_ERROR, ReasonCode.INCONSISTENT_DATA, "row currency contradiction"
                )
            reconciled = reconcile_observations(ap_snapshot.rows, verified_company)
        except SourceFailure as failure:
            return _finish(
                _typed_failure_result(request, failure, trace, correlation_id),
                timer,
                checked_user,
            )
    else:
        reconciled = ()

    # --- A8 Method prerequisites (schedule preflight / baseline comparability) ---
    _enter(Stage.A8_METHOD_PREREQ)
    try:
        if request.signal_id is SignalId.AP_DUE_CLUSTER:
            resolved, gaps = _schedule_preflight(reconciled, deps, verified_company)
            if gaps:
                return _finish(
                    _coverage_inconclusive(request, gaps, trace, correlation_id, ap_snapshot,
                                           reconciled, resolved, verified_company, captured_at,
                                           deps.data_mode),
                    timer,
                    checked_user,
                )
            selection = select_ap_observations(reconciled, request.as_of_date, resolved)
        else:
            selection = None
    except SourceFailure as failure:
        return _finish(
            _typed_failure_result(request, failure, trace, correlation_id),
            timer,
            checked_user,
        )

    # --- A9 Policy (registry resolution; pending only after valid inputs exist) ---
    _enter(Stage.A9_POLICY)
    try:
        policy = resolve_policy(request.signal_id)
    except PolicyPending as pending:
        result = _policy_pending_result(
            request, pending.reason_code, trace, correlation_id, ap_snapshot,
            reconciled, selection, verified_company, captured_at, deps.data_mode,
        )
        return _finish(result, timer, checked_user)
    except SourceFailure as failure:
        return _finish(
            _typed_failure_result(request, failure, trace, correlation_id),
            timer,
            checked_user,
        )

    # --- A10 Deterministic evaluation ---
    _enter(Stage.A10_EVALUATION)
    try:
        if request.signal_id is SignalId.AR_OVERDUE_SPIKE:
            outcome = evaluation_mod.evaluate_ar(policy, ar_pair[0], ar_pair[1])
        else:
            outcome = evaluation_mod.evaluate_ap(policy, selection)
    except SourceFailure as failure:
        return _finish(
            _typed_failure_result(request, failure, trace, correlation_id),
            timer,
            checked_user,
        )

    result = _ok_result(
        request, policy, outcome, trace, correlation_id, verified_company, captured_at,
        deps.data_mode, ap_snapshot=ap_snapshot, selection=selection, ar_pair=ar_pair,
    )

    # --- A11 Explanation (deterministic result already fixed; failure only degrades this) ---
    _enter(Stage.A11_EXPLANATION)
    result = _with_trace(result, trace)
    if include_explanation and explain is not None:
        try:
            explanation = explain(result)
        except Exception:
            explanation = Explanation(
                status=ExplanationStatus.UNAVAILABLE,
                reason_code="PROVIDER_FAILURE",
            )
        if explanation.status is ExplanationStatus.AVAILABLE and explanation.text:
            # A11 enforces its own screening even for injected explain callables.
            from lotus_fin.modules.f003_risk_signal.agent import validate_explanation_text

            violation = validate_explanation_text(explanation.text, result)
            if violation is not None:
                explanation = Explanation(
                    status=ExplanationStatus.UNAVAILABLE, reason_code=violation
                )
        result = _with_explanation(result, explanation)
    return _finish(result, timer, checked_user)


# --- helpers -----------------------------------------------------------------


def _correlation(payload: Mapping) -> Optional[str]:
    value = payload.get("correlation_id") if isinstance(payload, Mapping) else None
    return value if isinstance(value, str) and value else None


def _finish(result: SignalResult, timer: LatencyTimer, user: Optional[str]) -> SignalResult:
    log_ai003_event(
        event_type="ai003_evaluate_completed",
        correlation_id=result.correlation_id,
        status=result.status.value,
        signal_type=result.signal_id.value,
        stage=result.stage_trace[-1] if result.stage_trace else None,
        reason_code=result.reason_code.value if result.reason_code else None,
        policy_version=result.policy_version,
        data_mode=result.data_mode.value if result.data_mode else None,
        latency_ms=timer.elapsed_ms(),
    )
    return result


def _typed_failure_result(
    request: SignalRequest, failure: SourceFailure, trace, correlation_id
) -> SignalResult:
    return SignalResult(
        signal_id=request.signal_id,
        status=failure.status,
        reason_code=failure.reason_code,
        correlation_id=correlation_id,
        stage_trace=trace,
    )


def _coverage_inconclusive(request, gaps, trace, correlation_id, ap_snapshot, reconciled,
                           resolved, company, captured_at, data_mode) -> SignalResult:
    reason = ReasonCode.UNSUPPORTED_MULTI_SCHEDULE
    for _, gap in gaps:
        if gap == "UNSUPPORTED_MULTI_SCHEDULE":
            break
        if gap in ("NO_METADATA", "NO_VALID_DUE_DATE", "CHILD_HEADER_DISAGREEMENT",
                   "CHILD_REPORT_DISAGREEMENT", "HEADER_REPORT_DISAGREEMENT"):
            reason = ReasonCode.INCOMPLETE_DUE_DATE_COVERAGE
    evidence, _ref = _ap_evidence(
        ap_snapshot, reconciled, company, request.as_of_date, captured_at, correlation_id=correlation_id
    )
    return SignalResult(
        signal_id=request.signal_id,
        status=Status.INCONCLUSIVE,
        reason_code=reason,
        correlation_id=correlation_id,
        evidence=evidence,
        source_refs=_ap_source_refs(ap_snapshot),
        count_basis=CountBasis.DISTINCT_VOUCHER,
        count_positive_vouchers=distinct_voucher_count([o for o in reconciled if o.amount > 0]),
        as_of_date=request.as_of_date,
        data_mode=data_mode,
        stage_trace=trace,
        coverage=Coverage(missing_inputs=tuple(sorted({g for _, g in gaps}))),
        limitations=("Evaluation stopped at the first incomplete observation coverage gap.",),
    )


def _schedule_preflight(reconciled, deps: ServiceDeps, company):
    """SSOT §17.4: every unique positive voucher; fixed DocType map; explicit
    checked-user permission; >1 schedules -> UNSUPPORTED_MULTI_SCHEDULE."""
    positive = [obs for obs in reconciled if obs.amount > 0]
    metadata_by_voucher = {}
    for obs in positive:
        if obs.voucher_type not in SUPPORTED_AP_SOURCE_DOC_TYPES:
            raise SourceFailure(
                Status.INCONCLUSIVE,
                ReasonCode.UNSUPPORTED_ALLOCATION_SCOPE,
                "non-Purchase-Invoice payable voucher is unsupported P0 allocation scope",
            )
    for obs in positive:
        if obs.voucher_no in metadata_by_voucher:
            continue
        metadata_by_voucher[obs.voucher_no] = deps.schedule_provider.get(obs.voucher_no, company)
        meta = metadata_by_voucher[obs.voucher_no]
        if meta.schedule_count > 1:
            raise SourceFailure(
                Status.INCONCLUSIVE,
                ReasonCode.UNSUPPORTED_MULTI_SCHEDULE,
                "parent invoice has multiple payment schedules",
            )
    return resolve_due_dates(positive, metadata_by_voucher)


def _policy_pending_result(request, reason_code, trace, correlation_id, ap_snapshot,
                           reconciled, selection, company, captured_at, data_mode) -> SignalResult:
    """POLICY_PENDING with independently valid authorized partials (gold STAGE_F)."""
    kwargs = dict(
        signal_id=request.signal_id,
        status=Status.POLICY_PENDING,
        reason_code=reason_code,
        correlation_id=correlation_id,
        as_of_date=request.as_of_date,
        data_mode=data_mode,
        stage_trace=trace,
    )
    if request.signal_id is SignalId.AP_DUE_CLUSTER and selection is not None:
        from lotus_fin.modules.f003_risk_signal.coverage import sum_amounts

        evidence, _ref = _ap_evidence(
            ap_snapshot, reconciled, company, request.as_of_date, captured_at, correlation_id=correlation_id
        )
        kwargs.update(
            observed=ObservedBlock(
                value=None,
                unit=Unit.RATIO,
                supporting_amount=sum_amounts(selection.numerator),
                supporting_amount_definition=MaterialityDefinition.AP_DUE_WINDOW_AMOUNT,
            ),
            count_basis=CountBasis.DISTINCT_VOUCHER,
            count_positive_vouchers=selection.denominator_voucher_count,
            count_due_vouchers=selection.numerator_voucher_count,
            evidence=evidence,
            source_refs=_ap_source_refs(ap_snapshot),
        )
    return SignalResult(**kwargs)


def _ok_result(request, policy, outcome, trace, correlation_id, company, captured_at,
               data_mode, ap_snapshot=None, selection=None, ar_pair=None) -> SignalResult:
    materiality_def = evaluation_mod.materiality_definition_for(policy)
    kwargs = dict(
        signal_id=request.signal_id,
        status=Status.OK,
        finding=outcome.finding,
        severity=outcome.severity,
        triggered=(outcome.finding is Finding.TRIGGERED),
        policy_version=policy.policy_version,
        policy_scope=policy.policy_scope,
        production_calibrated=policy.production_calibrated,
        as_of_date=request.as_of_date,
        data_mode=data_mode,
        correlation_id=correlation_id,
        stage_trace=trace,
        rule=RuleBlock(
            threshold=policy.watch_threshold,
            high_threshold=policy.high_threshold,
            threshold_unit=policy.threshold_unit,
            comparator=policy.comparator,
            floor=policy.floor,
            materiality_definition=materiality_def,
            window_start=None,
            window_end=None,
        ),
    )
    if request.signal_id is SignalId.AR_OVERDUE_SPIKE:
        current, baseline = ar_pair
        kwargs.update(
            observed=ObservedBlock(
                value=outcome.observed_value,
                supporting_amount=outcome.supporting_amount,
                supporting_amount_definition=MaterialityDefinition.CURRENT_NET_AR_TOTAL,
            ),
            delta_pp=outcome.delta_pp,
            baseline=BaselineBlock(
                type=BaselineType.PREVIOUS_COMPARABLE_CUTOFF,
                status=BaselineStatus.AVAILABLE,
                value=outcome.baseline_value,
                denominator=outcome.baseline_denominator,
                cutoff=baseline.as_of,
                resolver_version=AR_BASELINE_SPEC,
            ),
            source_refs=(
                SourceRef(kind=SourceKind.AI001_METRIC, cutoff=current.as_of, captured_at=captured_at,
                          contract_version=current.contract_version, formula_version=current.formula_version),
                SourceRef(kind=SourceKind.AI001_METRIC, cutoff=baseline.as_of, captured_at=captured_at,
                          contract_version=baseline.contract_version, formula_version=baseline.formula_version),
            ),
        )
    else:
        from lotus_fin.modules.f003_risk_signal.coverage import ap_window

        window_start, window_end = ap_window(request.as_of_date)
        evidence, _ref = _ap_evidence(
            ap_snapshot, (), company, request.as_of_date, captured_at,
            selection=selection, outcome=outcome, correlation_id=correlation_id
        )
        kwargs.update(
            observed=ObservedBlock(
                value=outcome.observed_value,
                supporting_amount=outcome.supporting_amount,
                supporting_amount_definition=MaterialityDefinition.AP_DUE_WINDOW_AMOUNT,
            ),
            count_basis=CountBasis.DISTINCT_VOUCHER,
            count_positive_vouchers=selection.denominator_voucher_count,
            count_due_vouchers=selection.numerator_voucher_count,
            rule=RuleBlock(
                threshold=policy.watch_threshold,
                high_threshold=policy.high_threshold,
                threshold_unit=policy.threshold_unit,
                comparator=policy.comparator,
                floor=policy.floor,
                materiality_definition=materiality_def,
                window_start=window_start,
                window_end=window_end,
            ),
            evidence=evidence,
            source_refs=_ap_source_refs(ap_snapshot),
        )
    return SignalResult(**kwargs)


def _ap_source_refs(ap_snapshot):
    if ap_snapshot is None:
        return ()
    return (
        SourceRef(
            kind=SourceKind.ERP_AP_REPORT,
            cutoff=ap_snapshot.as_of,
            captured_at=utc_now_iso(),
            source_schema_version="ap_report_v1",
        ),
    )


def _ap_evidence(
    ap_snapshot, reconciled, company, as_of, captured_at,
    selection=None, outcome=None, correlation_id=None
):
    """Build (and store) the AP report-snapshot evidence record; return (refs, ref)."""
    if ap_snapshot is None:
        return (), None
    # Stored hash basis = report-snapshot identity only; derived values stay in
    # the SignalResult wire. Replay re-fetches and re-hashes the same identity.
    payload = {
        "report_key": ap_snapshot.report_key,
        "source_hash": ap_snapshot.source_hash,
    }
    try:
        record = create_evidence_record(
            company=company,
            signal_id=SignalId.AP_DUE_CLUSTER,
            as_of_date=as_of,
            report_key=ap_snapshot.report_key,
            filters=ap_snapshot.filters_applied,
            currency="VND",
            source_schema_version="ap_report_v1",
            payload=payload,
            captured_at=captured_at,
            correlation_id=correlation_id,
        )
        return (EvidenceRef(kind="REPORT_SNAPSHOT", company=company, ref=record.ref,
                            as_of_date=as_of, captured_at=captured_at),), record.ref
    except EvidenceStorageUnavailable:
        # Boundary failure already logged by the store with correlation id;
        # deterministic result keeps its frozen-contract behavior (no refs).
        return (), None
    except Exception as exc:
        log_ai003_event(
            event_type="ai003_evidence_store_failed",
            correlation_id=correlation_id,
            stage=Stage.A10_EVALUATION.value,
            status=Status.SOURCE_ERROR.value,
            reason_code=ReasonCode.SOURCE_UNAVAILABLE.value,
            exception_type=type(exc).__name__,
            operation="store_ap_evidence",
        )
        return (), None  # evidence must never break the deterministic result


def get_evidence(
    ref: str,
    *,
    checked_user: Optional[str],
    verified_company: str,
    replay_factory: Callable[[object], Callable],
    correlation_id: Optional[str] = None,
) -> ReplayResult:
    """Authorized evidence replay for the agent/tool layer (SSOT §16.7).

    ``replay_factory(record)`` returns the zero-arg replay callable bound to the
    captured record (cutoff/scope) once authorization has passed."""
    if not _is_authenticated(checked_user):
        log_ai003_event(
            event_type="ai003_evidence_unauthenticated",
            correlation_id=correlation_id,
            stage=Stage.A5_SOURCE_AUTH.value,
            status=Status.FORBIDDEN.value,
            reason_code=ReasonCode.ACCESS_DENIED.value,
            operation="get_evidence",
        )
        return ReplayResult(ReplayOutcome.FORBIDDEN, None)

    def _replay(record):
        return replay_factory(record)()

    result = evidence_get(ref, verified_company, _replay, correlation_id=correlation_id)
    log_ai003_event(
        event_type="ai003_evidence_" + result.outcome.lower(),
        correlation_id=correlation_id,
        signal_type=result.record.signal_id.value if result.record and hasattr(result.record.signal_id, "value") else (str(result.record.signal_id) if result.record else None),
        status="OK" if result.outcome in (ReplayOutcome.MATCH, ReplayOutcome.RESTATED) else result.outcome,
        stage=Stage.A10_EVALUATION.value,
        operation="evidence_replay_completed",
    )
    return result


def _current_data_mode() -> DataMode:
    """Server-controlled data mode; conservative default CONTROLLED_FIXTURE.
    A deployment may declare LIVE via site config ``ai003_data_mode``."""
    try:
        import frappe

        value = frappe.get_site_config().get("ai003_data_mode")
        if value == "LIVE":
            return DataMode.LIVE
    except Exception:
        pass
    return DataMode.CONTROLLED_FIXTURE


def _with_trace(result: SignalResult, trace: Tuple[str, ...]) -> SignalResult:
    """Refresh the stage trace (stages entered after result composition)."""
    return SignalResult(
        **{
            **{f: getattr(result, f) for f in result.__dataclass_fields__},
            "stage_trace": trace,
        }
    )


def _with_explanation(result: SignalResult, explanation: Explanation) -> SignalResult:
    """Replace only the explanation block; every deterministic field is preserved."""
    return SignalResult(
        **{
            **{f: getattr(result, f) for f in result.__dataclass_fields__},
            "explanation": explanation,
        }
    )


def default_deps(checked_user: str) -> ServiceDeps:
    """Frappe-bound dependency bundle for the live runtime path."""
    from lotus_fin.security.access import (
        check_ai003_report_permission,
        get_company_accounting_currency,
        get_verified_company,
    )

    def _verify(company: str) -> str:
        return get_verified_company(company, user=checked_user)

    def _permission(report_name: str) -> bool:
        try:
            check_ai003_report_permission(report_name, user=checked_user)
        except Exception:
            return False  # denial/nonexistent collapse to the same generic FORBIDDEN
        return True

    def _today() -> date:
        import frappe

        # Accounting dates are date-only in the site's accounting timezone.
        return frappe.utils.getdate(frappe.utils.today())

    return ServiceDeps(
        company_verifier=_verify,
        currency_provider=get_company_accounting_currency,
        today_provider=_today,
        ar_provider=AI001PublicARProvider(),
        ap_provider=APReportAdapter(),
        schedule_provider=FrappeScheduleMetadataProvider(checked_user),
        data_mode=_current_data_mode(),
        report_permission=_permission,
    )
