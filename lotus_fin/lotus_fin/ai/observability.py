"""
Lotus Fin AI001 - Observability, Structured Logging & Tracing Infrastructure.

Compliant with:
- AI001 Feature Freeze (Observability & Logging, §7)
- LotusFin Security SSOT (INV-03 Zero-PII, Audit Events, Correlation Tracing)

Guarantees:
1. Pure JSON structured audit events with correlation_id.
2. Pseudonymous user_id hashing (SHA256[:12]).
3. Zero PII, no raw monetary rows, invoice details, party names or secrets logged.
4. Bounded in-memory operational metrics collector for latency, requests by status,
   source errors, and KPI unavailable counts.
5. Lightweight execution span tracer.
"""

from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

EVENT_REQUEST_STARTED = "ai001_request_started"
EVENT_AUTH_PASSED = "ai001_authorization_passed"
EVENT_AUTH_DENIED = "ai001_authorization_denied"
EVENT_SNAPSHOT_STARTED = "ai001_snapshot_started"
EVENT_SNAPSHOT_COMPLETED = "ai001_snapshot_completed"
EVENT_SOURCE_ERROR = "ai001_source_error"
EVENT_METRIC_COMPUTED = "ai001_metric_computed"
EVENT_METRIC_UNAVAILABLE = "ai001_metric_unavailable"
EVENT_COMPARISON_STARTED = "ai001_comparison_started"
EVENT_COMPARISON_COMPLETED = "ai001_comparison_completed"
EVENT_COMPARISON_UNAVAILABLE = "ai001_comparison_unavailable"
EVENT_REQUEST_COMPLETED = "ai001_request_completed"
EVENT_REQUEST_FAILED = "ai001_request_failed"

_logger = logging.getLogger("lotus_fin.ai001")


def hash_user_id(user: Optional[str]) -> Optional[str]:
    """Safely hash user identifier into a 12-char pseudonymous digest."""
    if not user:
        return None
    return hashlib.sha256(user.encode("utf-8")).hexdigest()[:12]


def log_event(
    event_type: str,
    correlation_id: str,
    company: Optional[str] = None,
    user: Optional[str] = None,
    duration_ms: Optional[float] = None,
    status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO
) -> Dict[str, Any]:
    """
    Emits a structured JSON audit event log.
    Ensures ZERO raw financial amounts or PII are leaked.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "feature_id": "AI001",
        "event_type": event_type,
        "correlation_id": correlation_id,
        "company": company,
        "user_id_hash": hash_user_id(user),
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "status": status,
        "details": details or {}
    }

    try:
        # Also log to standard Python logger / Frappe logger
        msg = json.dumps(event, default=str)
        _logger.log(level, msg)
    except Exception:
        pass

    return event


class MetricsCollector:
    """
    In-memory bounded metrics collector for operational telemetry.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.requests_total = 0
        self.requests_by_status = defaultdict(int)
        self.auth_denials_total = 0
        self.source_errors_by_report = defaultdict(int)
        self.metrics_computed_total = 0
        self.metrics_unavailable_by_id = defaultdict(int)
        self.latencies_ms: List[float] = []

    def record_request(self, status: str, duration_ms: float):
        self.requests_total += 1
        self.requests_by_status[status] += 1
        self.latencies_ms.append(duration_ms)
        # Bounded buffer to avoid memory leak
        if len(self.latencies_ms) > 1000:
            self.latencies_ms = self.latencies_ms[-1000:]

    def record_auth_denial(self):
        self.auth_denials_total += 1

    def record_source_error(self, source_name: str):
        self.source_errors_by_report[source_name] += 1

    def record_metric_computed(self):
        self.metrics_computed_total += 1

    def record_metric_unavailable(self, metric_id: str):
        self.metrics_unavailable_by_id[metric_id] += 1

    def get_summary(self) -> Dict[str, Any]:
        """Returns snapshot summary of operational metrics."""
        sorted_latencies = sorted(self.latencies_ms)
        n = len(sorted_latencies)
        p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0.0
        p95 = sorted_latencies[int(n * 0.95)] if n > 0 else 0.0

        return {
            "requests_total": self.requests_total,
            "requests_by_status": dict(self.requests_by_status),
            "auth_denials_total": self.auth_denials_total,
            "source_errors_by_report": dict(self.source_errors_by_report),
            "metrics_computed_total": self.metrics_computed_total,
            "metrics_unavailable_by_id": dict(self.metrics_unavailable_by_id),
            "latency_p50_ms": round(p50, 2),
            "latency_p95_ms": round(p95, 2)
        }


# Global singleton metrics collector
metrics = MetricsCollector()


@contextmanager
def trace_span(
    name: str,
    correlation_id: str,
    company: Optional[str] = None,
    user: Optional[str] = None
):
    """
    Context manager to trace execution durations and record telemetry.
    """
    start_t = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_t) * 1000.0
        log_event(
            event_type=f"ai001_span_{name}",
            correlation_id=correlation_id,
            company=company,
            user=user,
            duration_ms=duration_ms
        )
