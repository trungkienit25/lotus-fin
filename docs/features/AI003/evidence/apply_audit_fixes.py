"""One-shot audit-fix applier (runs on host, edits working tree)."""
import io

def rw(path, replacements, expect=1):
    src = io.open(path, encoding="utf-8").read()
    for old, new in replacements:
        count = src.count(old)
        assert count >= 1, "NOT FOUND in %s: %r..." % (path, old[:70])
        src = src.replace(old, new)
    io.open(path, "w", encoding="utf-8", newline="\n").write(src)
    print("ok:", path.split("lotus_fin")[-1])

BASE = r"E:\lotus-fin\lotus_fin\lotus_fin"

# 1. coverage.py — split 1-schedule-no-usable-child from multi-schedule
rw(BASE + r"\risk_signal\coverage.py", [(
'''        else:
            gaps.append((obs.voucher_no, "UNSUPPORTED_MULTI_SCHEDULE"))''',
'''        else:
            # 1 schedule declared but no usable child due date.
            gaps.append((obs.voucher_no, "NO_VALID_DUE_DATE"))''')])

# 2. service.py — honor injected data_mode; cleanups; evidence audit log
rw(BASE + r"\risk_signal\service.py", [
    ("data_mode=_current_data_mode(),", "data_mode=data_mode,"),
    ("coverage=Coverage(missing_inputs=tuple({g for _, g in gaps})),",
     "coverage=Coverage(missing_inputs=tuple(sorted({g for _, g in gaps}))),"),
    ('''        try:
            rows = [row for row in ap_snapshot.rows if row.currency in ("", "VND")]
            if any(row.currency not in ("", "VND") for row in ap_snapshot.rows):
                raise SourceFailure(
                    Status.SOURCE_ERROR, ReasonCode.INCONSISTENT_DATA, "row currency contradiction"
                )
            reconciled = reconcile_observations(rows, verified_company)''',
     '''        try:
            if any(row.currency not in ("", "VND") for row in ap_snapshot.rows):
                raise SourceFailure(
                    Status.SOURCE_ERROR, ReasonCode.INCONSISTENT_DATA, "row currency contradiction"
                )
            reconciled = reconcile_observations(ap_snapshot.rows, verified_company)'''),
    ('''        if obs.voucher_type not in ("Purchase Invoice",):''',
     '''        if obs.voucher_type not in SUPPORTED_AP_SOURCE_DOC_TYPES:'''),
    ('''from lotus_fin.risk_signal.sources import (
    AI001PublicARProvider,
    APReportAdapter,
    FrappeScheduleMetadataProvider,
    fetch_ar_pair,
)''',
     '''from lotus_fin.risk_signal.sources import (
    AI001PublicARProvider,
    APReportAdapter,
    FrappeScheduleMetadataProvider,
    SUPPORTED_AP_SOURCE_DOC_TYPES,
    fetch_ar_pair,
)'''),
    ("return _finish(result, timer, checked_user, request=request)",
     "return _finish(result, timer, checked_user)"),
    ("def _finish(result: SignalResult, timer: LatencyTimer, user: Optional[str], request: Optional[SignalRequest] = None) -> SignalResult:",
     "def _finish(result: SignalResult, timer: LatencyTimer, user: Optional[str]) -> SignalResult:"),
    ('''    def _replay(record):
        return replay_factory(record)()

    return evidence_get(ref, verified_company, _replay)''',
     '''    def _replay(record):
        return replay_factory(record)()

    result = evidence_get(ref, verified_company, _replay)
    log_ai003_event(
        event_type="ai003_evidence_" + result.outcome.lower(),
        correlation_id=None,
        signal_type=result.record.signal_id.value if result.record else None,
    )
    return result'''),
])

# 3. observability.py — derive allowlists from contracts enums
rw(BASE + r"\risk_signal\observability.py", [(
'''from datetime import datetime, timezone
from typing import Any, Dict, Optional

_logger = logging.getLogger("lotus_fin.ai003")

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")

_STAGE_VALUES = {
    "A1_AUTH", "A2_STRUCTURE", "A3_COMPANY", "A4_SEMANTIC_SCOPE", "A5_SOURCE_AUTH",
    "A6_SOURCE_CURRENCY", "A7_INTEGRITY_IDENTITY", "A8_METHOD_PREREQ", "A9_POLICY",
    "A10_EVALUATION", "A11_EXPLANATION",
}
_SIGNAL_VALUES = {"AR_OVERDUE_SPIKE", "AP_DUE_CLUSTER"}
_STATUS_VALUES = {"OK", "INCONCLUSIVE", "FORBIDDEN", "VALIDATION_ERROR", "SOURCE_ERROR", "POLICY_PENDING"}
_REASON_VALUES = {
    "UNAUTHORIZED_ACCESS", "INVALID_REQUEST", "FUTURE_AS_OF", "UNSUPPORTED_CURRENCY",
    "FINANCE_BOOK_NOT_SUPPORTED", "HISTORY_INSUFFICIENT", "INVALID_DENOMINATOR", "ZERO_DENOMINATOR",
    "INCOMPLETE_DUE_DATE_COVERAGE", "UNSUPPORTED_ALLOCATION_SCOPE", "INCONSISTENT_DATA",
    "SOURCE_UNAVAILABLE", "SOURCE_TIMEOUT", "POLICY_UNAVAILABLE", "INVALID_POLICY_CONFIG",
    "UNSUPPORTED_SOURCE_VERSION", "ACCESS_DENIED", "UNSUPPORTED_COMPANY_CURRENCY",
    "BASELINE_DENOMINATOR_INVALID", "CURRENT_DENOMINATOR_INVALID", "CONFLICTING_OBSERVATION",
    "SOURCE_INVALID", "UNSUPPORTED_MULTI_SCHEDULE", "POLICY_NOT_APPROVED",
}
_DATA_MODE_VALUES = {"LIVE", "CONTROLLED_FIXTURE"}
_METHOD_VERSION = "V2.2_REVIEWED_METHOD_SPEC"''',
'''from datetime import datetime, timezone
from typing import Any, Dict, Optional

from lotus_fin.risk_signal.contracts import (
    METHOD_VERSION,
    DataMode,
    ReasonCode,
    SignalId,
    Stage,
    Status,
)

_logger = logging.getLogger("lotus_fin.ai003")

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")

_STAGE_VALUES = {s.value for s in Stage}
_SIGNAL_VALUES = {s.value for s in SignalId}
_STATUS_VALUES = {s.value for s in Status}
_REASON_VALUES = {r.value for r in ReasonCode}
_DATA_MODE_VALUES = {m.value for m in DataMode}'''),
    ('"method_version": _METHOD_VERSION,', '"method_version": METHOD_VERSION,')])

# 4. policy.py — bool cannot masquerade as window_days int
rw(BASE + r"\risk_signal\policy.py", [(
'''        if self.window_days is not None and (not isinstance(self.window_days, int) or self.window_days < 0):''',
'''        if self.window_days is not None and (
            isinstance(self.window_days, bool) or not isinstance(self.window_days, int) or self.window_days < 0
        ):''')])

# 5. agent.py — unit-aware threshold serialization in minimized payload
rw(BASE + r"\risk_signal\agent.py", [
    ('''from lotus_fin.risk_signal.contracts import (
    Explanation,
    ExplanationStatus,
    Finding,
    ReasonCode,
    SignalId,
    Status,
    pp_str,
    ratio_str,
    money_str,
)''',
     '''from lotus_fin.risk_signal.contracts import (
    Explanation,
    ExplanationStatus,
    Finding,
    ReasonCode,
    SignalId,
    Status,
    ThresholdUnit,
    money_str,
    pp_str,
    ratio_str,
)'''),
    ('''    if result.rule is not None and result.rule.threshold is not None:
        payload["watch_threshold"] = ratio_str(result.rule.threshold)
    if result.rule is not None and result.rule.high_threshold is not None:
        payload["high_threshold"] = ratio_str(result.rule.high_threshold)''',
     '''    if result.rule is not None and result.rule.threshold is not None:
        fmt = pp_str if result.rule.threshold_unit is ThresholdUnit.PERCENTAGE_POINTS else ratio_str
        payload["watch_threshold"] = fmt(result.rule.threshold)
    if result.rule is not None and result.rule.high_threshold is not None:
        fmt_high = pp_str if result.rule.threshold_unit is ThresholdUnit.PERCENTAGE_POINTS else ratio_str
        payload["high_threshold"] = fmt_high(result.rule.high_threshold)'''),
])

# 6. api/ai_insights.py — remove dead helper; server-side log; align denial envelope
rw(r"E:\lotus-fin\lotus_fin\lotus_fin\api\ai_insights.py", [
    ('''def _ai003_forbidden(correlation_id=None) -> Dict[str, Any]:
    from lotus_fin.risk_signal.contracts import forbidden_result, result_to_dict

    return result_to_dict(forbidden_result(None, ("A1_AUTH",), correlation_id))


''', ''),
    ('''    unknown = set((frappe.form_dict or {}).keys()) - _AI003_REQUEST_KEYS
    if unknown:
        return {
            "feature_id": "AI003",
            "status": "VALIDATION_ERROR",
            "reason_code": "INVALID_REQUEST",
            "explanation": {"status": "NOT_REQUESTED", "text": None, "reason_code": None},
        }''',
     '''    unknown = set((frappe.form_dict or {}).keys()) - _AI003_REQUEST_KEYS
    if unknown:
        return {
            "feature_id": "AI003",
            "status": "VALIDATION_ERROR",
            "reason_code": "INVALID_REQUEST",
            "correlation_id": correlation_id if isinstance(correlation_id, str) else None,
            "stage_trace": ("A1_AUTH", "A2_STRUCTURE"),
            "explanation": {"status": "NOT_REQUESTED", "text": None, "reason_code": None},
        }'''),
    ('''    try:
        return _run()
    except Exception:
        # Unexpected failure: sanitized typed envelope, no internals on the wire.
        return result_to_dict(
            SignalResult(
                signal_id=SignalId.AR_OVERDUE_SPIKE,
                status=Status.SOURCE_ERROR,
                reason_code=ReasonCode.SOURCE_UNAVAILABLE,
                correlation_id=correlation_id if isinstance(correlation_id, str) else None,
                stage_trace=("A1_AUTH",),
            ),
            include_debug=False,
        )''',
     '''    try:
        return _run()
    except Exception:
        # Unexpected failure: sanitized typed envelope, no internals on the wire;
        # the full traceback stays server-side for debugging.
        frappe.log_error(message=frappe.get_traceback(), title="AI003 get_risk_signal failed")
        return result_to_dict(
            SignalResult(
                signal_id=SignalId.AR_OVERDUE_SPIKE,
                status=Status.SOURCE_ERROR,
                reason_code=ReasonCode.SOURCE_UNAVAILABLE,
                correlation_id=correlation_id if isinstance(correlation_id, str) else None,
            ),
            include_debug=False,
        )'''),
])

# 7. risk_signal.js — invalidate company scope on any filter change
rw(r"E:\lotus-fin\lotus_fin\lotus_fin\lotus_fin_ai\page\risk_signal\risk_signal.js", [
    ('''			change() {
				me.clear_result(__("Company changed — the previous result was cleared."));
			}''',
     '''			change() {
				me.current_company = null;
				me.clear_result(__("Company changed — the previous result was cleared."));
			}'''),
    ('''			change() {
				me.clear_result(__("Signal changed — the previous result was cleared."));
			}''',
     '''			change() {
				me.current_company = null;
				me.clear_result(__("Signal changed — the previous result was cleared."));
			}'''),
    ('''			change() {
				me.clear_result(__("Date changed — the previous result was cleared."));
			}''',
     '''			change() {
				me.current_company = null;
				me.clear_result(__("Date changed — the previous result was cleared."));
			}'''),
])

print("ALL AUDIT FIXES APPLIED")
