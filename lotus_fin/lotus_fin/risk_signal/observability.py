"""AI003 observability (S4) — structured JSON audit events, zero PII.

Mirrors the AI001/AI002 observability guarantees without modifying that module
(scaffold plan S4 allows only this file): pure JSON events, SHA256[:12]
pseudonymous company/user hashes, allowlisted detail fields (unknown keys fail
closed), no raw report rows, party names, invoice text, prompts or tokens.

Every AI003 evaluation/evidence event carries: correlation_id, signal_type,
stage, status, reason_code, method_version, policy_version, data_mode, latency.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
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
_METHOD_VERSION = "V2.2_REVIEWED_METHOD_SPEC"


def hash_id(value: Optional[str]) -> Optional[str]:
    """12-char pseudonymous digest; None passes through."""
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _safe_token(value: Any, fallback: str) -> str:
    return value if isinstance(value, str) and _SAFE_TOKEN.fullmatch(value) else fallback


def log_ai003_event(
    *,
    event_type: str,
    correlation_id: Optional[str],
    status: Optional[str] = None,
    signal_type: Optional[str] = None,
    stage: Optional[str] = None,
    reason_code: Optional[str] = None,
    policy_version: Optional[str] = None,
    data_mode: Optional[str] = None,
    record_count: Optional[int] = None,
    latency_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """Typed AI003 audit boundary. Company/user must never be passed here in
    raw form; callers pass nothing identifying — hashed ids are derived by the
    service layer through hash_id when needed."""
    event: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "feature_id": "AI003",
        "event_type": _safe_token(event_type, "unclassified_event"),
        "correlation_id": _safe_token(correlation_id, "unspecified"),
        "status": status if status in _STATUS_VALUES else None,
        "signal_type": signal_type if signal_type in _SIGNAL_VALUES else None,
        "stage": stage if stage in _STAGE_VALUES else None,
        "reason_code": reason_code if reason_code in _REASON_VALUES else None,
        "method_version": _METHOD_VERSION,
        "policy_version": policy_version if policy_version in (None, "AI003_DEMO_POLICY_V1") else None,
        "data_mode": data_mode if data_mode in _DATA_MODE_VALUES else None,
        "latency_ms": None,
        "record_count": None,
    }
    if isinstance(record_count, int) and not isinstance(record_count, bool) and 0 <= record_count <= 10**9:
        event["record_count"] = record_count
    if isinstance(latency_ms, (int, float)) and not isinstance(latency_ms, bool) and 0 <= latency_ms <= 86_400_000:
        event["latency_ms"] = round(float(latency_ms), 2)
    try:
        _logger.info(json.dumps(event, default=str))
    except Exception:
        pass
    return event


class LatencyTimer:
    """Monotonic latency measurement for evaluation spans."""

    def __init__(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000.0
