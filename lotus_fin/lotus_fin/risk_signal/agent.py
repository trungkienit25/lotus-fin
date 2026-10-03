"""AI003 bounded agent layer (S5).

The agent may only: identify signal intent, invoke the typed tools, explain
the deterministic result, and suggest allowlisted next-check actions. It can
never calculate metrics, set thresholds, select reports, alter severity or
findings, or convert INCONCLUSIVE to BENIGN (packet §14; SSOT §11/§16.7).

Explanation reuse: the AI001 LLMExplanationProvider (env-configured, mock
default, 15s timeout) supplies transport; AI003 adds its own fail-closed
validation — banned-term screening and numeric grounding against the
deterministic result. Any provider/validation failure degrades ONLY the
explanation to UNAVAILABLE; the deterministic result is untouched.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from lotus_fin.risk_signal.contracts import (
    Explanation,
    ExplanationStatus,
    Status,
    ThresholdUnit,
    money_str,
    pp_str,
    ratio_str,
)
from lotus_fin.risk_signal.observability import log_ai003_event

# Packet §15: wording never supported by the frozen V2.2 feature scope.
AI003_BANNED_TERMS = (
    "fraud",
    "default",
    "bankruptcy",
    "guaranteed cash shortage",
    "creditworthiness",
    "guaranteed profit",
    "tax exempt",
)

_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

_NEXT_CHECK_ACTIONS: Dict[str, List[str]] = {
    "AR_OVERDUE_SPIKE": [
        "Review the Accounts Receivable aging report for overdue invoices",
        "Open the signal evidence snapshot for the evaluated cutoff",
        "Re-run the signal after the next posting cycle",
    ],
    "AP_DUE_CLUSTER": [
        "Review the Accounts Payable report for the due window",
        "Open the signal evidence snapshot for the evaluated cutoff",
        "Inspect Purchase Invoice payment schedules for multi-installment invoices",
    ],
}
_NEXT_CHECK_FORBIDDEN = ["Contact an administrator to verify your company access"]
_NEXT_CHECK_INCONCLUSIVE = [
    "Open the evidence snapshot to inspect the blocking observation",
    "Resolve the flagged invoice schedule or due-date coverage, then re-run",
]
_NEXT_CHECK_SOURCE_ERROR = ["Retry the evaluation; if it persists, contact an administrator"]
_NEXT_CHECK_POLICY_PENDING = ["Await policy approval; the deterministic inputs are already validated"]


def next_check_actions(signal_id_value: str, status_value: str) -> List[str]:
    """Allowlisted next-check suggestions (never arbitrary agent output)."""
    if status_value == Status.FORBIDDEN.value:
        return list(_NEXT_CHECK_FORBIDDEN)
    if status_value in (Status.VALIDATION_ERROR.value,):
        return ["Correct the request parameters and re-run the evaluation"]
    if status_value == Status.INCONCLUSIVE.value:
        return list(_NEXT_CHECK_INCONCLUSIVE)
    if status_value == Status.SOURCE_ERROR.value:
        return list(_NEXT_CHECK_SOURCE_ERROR)
    if status_value == Status.POLICY_PENDING.value:
        return list(_NEXT_CHECK_POLICY_PENDING)
    return list(_NEXT_CHECK_ACTIONS.get(signal_id_value, []))


def _minimized_payload(result) -> Dict[str, Any]:
    """Authorized, minimized model input: no raw rows, parties, remarks, filters."""
    payload: Dict[str, Any] = {
        "signal_id": result.signal_id.value,
        "status": result.status.value,
        "as_of_date": result.as_of_date.isoformat() if result.as_of_date else None,
        "accounting_timezone": result.accounting_timezone,
        "policy_scope": result.policy_scope,
        "production_calibrated": result.production_calibrated,
        "limitations": list(result.limitations),
    }
    if result.finding is not None:
        payload["finding"] = result.finding.value
        payload["severity"] = result.severity.value if result.severity else None
    if result.reason_code is not None:
        payload["reason_code"] = result.reason_code.value
    if result.observed is not None and result.observed.value is not None:
        payload["observed_ratio"] = ratio_str(result.observed.value)
    if result.observed is not None and result.observed.supporting_amount is not None:
        payload["supporting_amount"] = money_str(result.observed.supporting_amount)
    if result.delta_pp is not None:
        payload["delta_pp"] = pp_str(result.delta_pp)
    if result.rule is not None and result.rule.threshold is not None:
        fmt = pp_str if result.rule.threshold_unit is ThresholdUnit.PERCENTAGE_POINTS else ratio_str
        payload["watch_threshold"] = fmt(result.rule.threshold)
    if result.rule is not None and result.rule.high_threshold is not None:
        fmt_high = pp_str if result.rule.threshold_unit is ThresholdUnit.PERCENTAGE_POINTS else ratio_str
        payload["high_threshold"] = fmt_high(result.rule.high_threshold)
    if result.count_positive_vouchers is not None:
        payload["count_positive_vouchers"] = result.count_positive_vouchers
    if result.count_due_vouchers is not None:
        payload["count_due_vouchers"] = result.count_due_vouchers
    return payload


def _allowed_numbers(result) -> set:
    allowed = set()
    payload = _minimized_payload(result)
    for value in payload.values():
        if isinstance(value, str):
            allowed.add(value)
            allowed.add(value.replace(",", ""))
    return allowed


def validate_explanation_text(text: str, result) -> Optional[str]:
    """Return a sanitized failure code, or None when the text is acceptable."""
    lowered = text.lower()
    for term in AI003_BANNED_TERMS:
        if term in lowered:
            return "BANNED_TERM"
    # Dates are citation context, not financial claims; remove before scanning.
    text_for_numbers = _DATE_RE.sub(" ", text)
    for number in _NUMBER_RE.findall(text_for_numbers):
        normalized = number.replace(",", "")
        if normalized not in _allowed_numbers(result) and number not in _allowed_numbers(result):
            return "GROUNDING_FAILED"
    return None


def _mock_handler(result):
    def handler(payload: Dict[str, Any]) -> str:
        status = payload["status"]
        if status == "OK":
            finding = payload.get("finding")
            severity = payload.get("severity")
            if finding == "TRIGGERED":
                if payload.get("delta_pp") is not None:
                    return (
                        "The overdue receivables ratio moved by %s percentage points to %s as of %s, "
                        "which reaches the approved %s band. Review the aging report and the evidence "
                        "snapshot before acting."
                        % (payload.get("delta_pp"), payload.get("observed_ratio"),
                           payload.get("as_of_date"), severity)
                    )
                return (
                    "Share of positive future payables inside the due window is %s as of %s, "
                    "reaching the approved %s band. Review the payable report and the evidence snapshot."
                    % (payload.get("observed_ratio"), payload.get("as_of_date"), severity)
                )
            return (
                "The deterministic evaluation completed as of %s with no threshold breach "
                "(delta %s pp, ratio %s). Continued monitoring is recommended."
                % (payload.get("as_of_date"), payload.get("delta_pp"), payload.get("observed_ratio"))
            )
        if status == "INCONCLUSIVE":
            return (
                "The evaluation could not complete deterministically as of %s (reason: %s). "
                "Inspect the evidence snapshot; no finding was produced."
                % (payload.get("as_of_date"), payload.get("reason_code"))
            )
        if status == "POLICY_PENDING":
            return (
                "Deterministic inputs are valid as of %s, but the applicable policy is not "
                "approved, so no finding or severity can be produced."
                % payload.get("as_of_date")
            )
        return (
            "The evaluation did not produce a result (status %s). No financial data is included."
            % status
        )

    return handler


def explain_result(result, provider=None) -> Explanation:
    """A11: explanation-only LLM step. Failure degrades explanation, never the result."""
    if result.status is Status.FORBIDDEN:
        return Explanation(status=ExplanationStatus.NOT_REQUESTED)
    payload = _minimized_payload(result)
    if provider is None:
        from lotus_fin.ai.explanation import LLMExplanationProvider

        provider = LLMExplanationProvider(mock_handler=_mock_handler(result))
    try:
        status_code, text, _usage = provider.generate_explanation_raw(payload)
    except Exception:
        log_ai003_event(
            event_type="ai003_explanation_failed",
            correlation_id=result.correlation_id,
            status=result.status.value,
            signal_type=result.signal_id.value,
        )
        return Explanation(status=ExplanationStatus.UNAVAILABLE, reason_code="PROVIDER_FAILURE")
    if status_code != 200 or not text or not str(text).strip():
        return Explanation(status=ExplanationStatus.UNAVAILABLE, reason_code="PROVIDER_FAILURE")
    violation = validate_explanation_text(str(text), result)
    if violation is not None:
        log_ai003_event(
            event_type="ai003_explanation_rejected",
            correlation_id=result.correlation_id,
            status=result.status.value,
            signal_type=result.signal_id.value,
        )
        return Explanation(status=ExplanationStatus.UNAVAILABLE, reason_code=violation)
    return Explanation(status=ExplanationStatus.AVAILABLE, text=str(text))


# --- Agent tools (internal, schema-allowlisted; the whitelisted surface is the API) ---


def risk_signal_evaluate(
    company: str,
    signal_id: str,
    as_of_date: str,
    correlation_id: Optional[str] = None,
    include_explanation: bool = True,
) -> Dict[str, Any]:
    """Typed tool: one deterministic evaluation in the checked session context."""
    import frappe

    from lotus_fin.risk_signal.service import default_deps, evaluate_signal

    checked_user = getattr(frappe.session, "user", None)
    result = evaluate_signal(
        {
            "company": company,
            "signal_id": signal_id,
            "as_of_date": as_of_date,
            "correlation_id": correlation_id,
        },
        checked_user=checked_user,
        deps=default_deps(checked_user),
        include_explanation=include_explanation,
        explain=explain_result,
    )
    from lotus_fin.risk_signal.contracts import result_to_dict

    wire = result_to_dict(result, include_debug=False)
    wire["next_check_actions"] = next_check_actions(result.signal_id.value, result.status.value)
    return wire


def risk_signal_evidence_get(
    evidence_ref: str,
    company: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Typed tool: authorized evidence replay; the ref is never an auth token."""
    import frappe

    from lotus_fin.risk_signal.service import default_deps, get_evidence
    from lotus_fin.security.access import get_verified_company

    checked_user = getattr(frappe.session, "user", None)
    if not checked_user:
        return {"status": "FORBIDDEN"}
    try:
        verified_company = get_verified_company(company, user=checked_user)
    except Exception:
        return {"status": "FORBIDDEN"}
    deps = default_deps(checked_user)

    def replay_factory(record):
        def replay():
            if not deps.report_permission("Accounts Payable"):
                from lotus_fin.risk_signal.provenance import SourceFailure, Status, ReasonCode
                raise SourceFailure(Status.FORBIDDEN, ReasonCode.ACCESS_DENIED, "report permission denied")
            snapshot = deps.ap_provider.fetch(verified_company, record.as_of_date)
            return {"report_key": snapshot.report_key, "source_hash": snapshot.source_hash}

        return replay

    result = get_evidence(
        evidence_ref,
        checked_user=checked_user,
        verified_company=verified_company,
        replay_factory=replay_factory,
        correlation_id=correlation_id,
    )
    return {
        "status": result.outcome,
        "payload": dict(result.fresh_payload) if result.fresh_payload else None,
    }
