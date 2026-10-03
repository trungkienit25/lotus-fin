"""AI003 evidence service (S4) — dynamic authorized replay + saved-hash comparison.

Semantics pinned by SSOT §16.7 and the IVL replay harness evidence
(docker/ai003-local/ivl_phase_c_replay_harness.py):
- An evidence ref is an opaque, resolvable server-side record id — NEVER an
  authorization token.
- Authorization runs on EVERY access: ref existence, verified company binding,
  and the live replay itself are all fail-closed. Nonexistence, denial and
  cross-company references collapse to the same generic FORBIDDEN.
- Replay outcomes: MATCH (fresh payload hash equals saved hash), RESTATED
  (source actually changed since capture), UNAVAILABLE (typed source failure),
  FORBIDDEN (revoked/denied). A changed report hash is never silently MATCHed.
- Scope fingerprint binds company, report key, filters, cutoff, currency,
  timezone, schema and method versions.

No dedicated evaluation cache exists (SSOT §16.7/§19.2); this store holds only
evidence records, bounded, FIFO-evicted, never serving stale authorization.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Callable, Dict, Mapping, Optional

from lotus_fin.risk_signal.contracts import (
    ACCOUNTING_TIMEZONE,
    METHOD_VERSION,
    ReasonCode,
    SignalId,
    Stage,
    Status,
)
from lotus_fin.risk_signal.observability import hash_id, log_ai003_event
from lotus_fin.risk_signal.provenance import (
    SourceFailure,
    canonical_payload_hash,
)

EVIDENCE_KIND_REPORT_SNAPSHOT = "REPORT_SNAPSHOT"
MAX_EVIDENCE_RECORDS = 500
DEFAULT_EVIDENCE_TTL_SECONDS = 3600  # 1 hour bounded TTL


class ReplayOutcome:
    MATCH = "MATCH"
    RESTATED = "RESTATED"
    UNAVAILABLE = "UNAVAILABLE"
    FORBIDDEN = "FORBIDDEN"


@dataclass(frozen=True)
class EvidenceRecord:
    ref: str
    company: str
    signal_id: SignalId
    as_of_date: date
    kind: str = EVIDENCE_KIND_REPORT_SNAPSHOT
    scope_fingerprint: str = ""
    payload_hash: str = ""
    payload: Mapping = field(default_factory=dict)
    captured_at: str = ""


@dataclass(frozen=True)
class ReplayResult:
    outcome: str
    record: Optional[EvidenceRecord]
    fresh_payload: Optional[Mapping] = None


def _serialize_record(record: EvidenceRecord) -> dict:
    return {
        "ref": record.ref,
        "company": record.company,
        "signal_id": record.signal_id.value if isinstance(record.signal_id, SignalId) else str(record.signal_id),
        "as_of_date": record.as_of_date.isoformat() if isinstance(record.as_of_date, date) else str(record.as_of_date),
        "kind": record.kind,
        "scope_fingerprint": record.scope_fingerprint,
        "payload_hash": record.payload_hash,
        "payload": {k: str(v) if isinstance(v, Decimal) else v for k, v in record.payload.items()},
        "captured_at": record.captured_at,
    }


def _deserialize_record(data: dict) -> EvidenceRecord:
    as_of = data.get("as_of_date")
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)
    raw_signal = data.get("signal_id")
    try:
        signal_id = SignalId(raw_signal)
    except Exception:
        signal_id = raw_signal
    raw_payload = data.get("payload") or {}
    sanitized_payload = {}
    for k, v in raw_payload.items():
        if k in ("numerator", "denominator", "display_share") and isinstance(v, str):
            try:
                sanitized_payload[k] = Decimal(v)
            except Exception:
                sanitized_payload[k] = v
        else:
            sanitized_payload[k] = v
    return EvidenceRecord(
        ref=data["ref"],
        company=data["company"],
        signal_id=signal_id,
        as_of_date=as_of,
        kind=data.get("kind", EVIDENCE_KIND_REPORT_SNAPSHOT),
        scope_fingerprint=data.get("scope_fingerprint", ""),
        payload_hash=data.get("payload_hash", ""),
        payload=sanitized_payload,
        captured_at=data.get("captured_at", ""),
    )


class EvidenceStore:
    """Server-side bounded evidence record store shared across Gunicorn workers
    via Frappe/Redis cache with hermetic in-memory fallback.
    """

    def __init__(
        self,
        max_records: int = MAX_EVIDENCE_RECORDS,
        ttl_seconds: int = DEFAULT_EVIDENCE_TTL_SECONDS,
        client: Optional[Any] = None,
    ) -> None:
        self._ttl = ttl_seconds
        self._max = max_records
        self._client = client
        self._local_records: Dict[str, dict] = {}
        self._local_order: list = []
        self._lock = threading.Lock()

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import frappe

            if getattr(frappe.local, "site", None) or getattr(frappe.local, "conf", None):
                cache = frappe.cache()
                if cache is not None:
                    return cache
        except Exception:
            pass
        return None

    def put(self, record: EvidenceRecord) -> str:
        """Store an evidence record with bounded TTL; return opaque ref."""
        serialized = _serialize_record(record)
        client = self._get_client()
        if client is not None:
            try:
                key = f"ai003:evidence:{record.ref}"
                client.set_value(key, serialized, expires_in_sec=self._ttl)
                return record.ref
            except Exception as exc:
                log_ai003_event(
                    event_type="ai003_evidence_storage_error",
                    correlation_id=None,
                    stage=Stage.A10_EVALUATION.value,
                    status=Status.SOURCE_ERROR.value,
                    reason_code=ReasonCode.SOURCE_UNAVAILABLE.value,
                    exception_type=type(exc).__name__,
                    operation="evidence_cache_set",
                )

        with self._lock:
            self._local_records[record.ref] = serialized
            self._local_order.append(record.ref)
            while len(self._local_order) > self._max:
                evicted = self._local_order.pop(0)
                self._local_records.pop(evicted, None)
        return record.ref

    def create(self, record: EvidenceRecord) -> EvidenceRecord:
        """Backward-compatible put returning the record."""
        self.put(record)
        return record

    def get(self, ref: str) -> Optional[EvidenceRecord]:
        """Fetch record by ref, returning None if expired or nonexistent."""
        if not isinstance(ref, str) or not ref:
            return None

        client = self._get_client()
        if client is not None:
            try:
                key = f"ai003:evidence:{ref}"
                data = client.get_value(key, expires=True, use_local_cache=False)
                if data is not None:
                    return _deserialize_record(data)
                return None
            except Exception as exc:
                log_ai003_event(
                    event_type="ai003_evidence_storage_error",
                    correlation_id=None,
                    stage=Stage.A5_SOURCE_AUTH.value,
                    status=Status.SOURCE_ERROR.value,
                    reason_code=ReasonCode.SOURCE_UNAVAILABLE.value,
                    exception_type=type(exc).__name__,
                    operation="evidence_cache_get",
                )

        with self._lock:
            data = self._local_records.get(ref)
            if data is not None:
                return _deserialize_record(data)
        return None

    def delete(self, ref: str) -> None:
        """Evict record by ref."""
        if not isinstance(ref, str) or not ref:
            return

        client = self._get_client()
        if client is not None:
            try:
                key = f"ai003:evidence:{ref}"
                client.delete_value(key)
            except Exception as exc:
                log_ai003_event(
                    event_type="ai003_evidence_storage_error",
                    correlation_id=None,
                    stage=Stage.A10_EVALUATION.value,
                    status=Status.SOURCE_ERROR.value,
                    reason_code=ReasonCode.SOURCE_UNAVAILABLE.value,
                    exception_type=type(exc).__name__,
                    operation="evidence_cache_delete",
                )

        with self._lock:
            self._local_records.pop(ref, None)
            if ref in self._local_order:
                self._local_order.remove(ref)

    def __len__(self) -> int:
        with self._lock:
            return len(self._local_records)


_STORE = EvidenceStore()


def build_scope_fingerprint(
    *,
    company: str,
    report_key: str,
    filters: Mapping,
    cutoff: date,
    currency: str,
    source_schema_version: str,
) -> str:
    """Hash binding company/report/filters/cutoff/currency/tz/schema/method."""
    return canonical_payload_hash(
        {
            "company": hash_id(company),
            "report_key": report_key,
            "filters": {k: str(v) for k, v in sorted(filters.items())},
            "cutoff": cutoff.isoformat(),
            "currency": currency,
            "accounting_timezone": ACCOUNTING_TIMEZONE,
            "source_schema_version": source_schema_version,
            "method_version": METHOD_VERSION,
        }
    )


def make_evidence_ref(scope_fingerprint: str, payload_hash: str) -> str:
    """Opaque resolvable ref derived from scope + payload; not a bearer token."""
    return "AI003-EV-%s-%s" % (scope_fingerprint[:12], payload_hash[:12])


def create_evidence_record(
    *,
    company: str,
    signal_id: SignalId,
    as_of_date: date,
    report_key: str,
    filters: Mapping,
    currency: str,
    source_schema_version: str,
    payload: Mapping,
    captured_at: str,
) -> EvidenceRecord:
    """Build, hash and store one sanitized report-snapshot evidence record."""
    scope_fingerprint = build_scope_fingerprint(
        company=company,
        report_key=report_key,
        filters=filters,
        cutoff=as_of_date,
        currency=currency,
        source_schema_version=source_schema_version,
    )
    payload = _sanitize_payload(payload)
    payload_hash = canonical_payload_hash(payload)
    record = EvidenceRecord(
        ref=make_evidence_ref(scope_fingerprint, payload_hash),
        company=company,
        signal_id=signal_id,
        as_of_date=as_of_date,
        scope_fingerprint=scope_fingerprint,
        payload_hash=payload_hash,
        payload=payload,
        captured_at=captured_at,
    )
    return _STORE.create(record)


def _sanitize_payload(payload: Mapping) -> Mapping:
    """Evidence payloads carry only authorized derived values — never raw rows,
    party names, remarks or exception text."""
    allowed_keys = (
        "report_key",
        "numerator",
        "denominator",
        "display_share",
        "numerator_voucher_count",
        "denominator_voucher_count",
        "excluded_past_due_count",
        "excluded_credit_count",
        "source_hash",
    )
    return {key: payload[key] for key in allowed_keys if key in payload}


def evidence_get(
    ref: str,
    verified_company: str,
    replay: Callable[[EvidenceRecord], Mapping],
    *,
    correlation_id: Optional[str] = None,
) -> ReplayResult:
    """Authorized dynamic replay: reauthorization first, then hash comparison.

    ``replay`` re-runs the approved source path in checked-user context for the
    captured record (its cutoff/scope) and returns the fresh sanitized payload;
    it raises SourceFailure on typed failures. The deterministic result of the
    original evaluation is never altered by evidence access.
    """
    if not isinstance(ref, str) or not ref.startswith("AI003-EV-"):
        log_ai003_event(
            event_type="ai003_evidence_malformed_ref",
            correlation_id=correlation_id,
            stage=Stage.A5_SOURCE_AUTH.value,
            status=Status.FORBIDDEN.value,
            reason_code=ReasonCode.ACCESS_DENIED.value,
            operation="evidence_get",
        )
        return ReplayResult(ReplayOutcome.FORBIDDEN, None)

    record = _STORE.get(ref)
    if record is None:
        log_ai003_event(
            event_type="ai003_evidence_not_found",
            correlation_id=correlation_id,
            stage=Stage.A5_SOURCE_AUTH.value,
            status=Status.FORBIDDEN.value,
            reason_code=ReasonCode.ACCESS_DENIED.value,
            operation="evidence_lookup",
        )
        return ReplayResult(ReplayOutcome.FORBIDDEN, None)

    if record.company != verified_company:
        log_ai003_event(
            event_type="ai003_evidence_cross_company_denied",
            correlation_id=correlation_id,
            signal_type=record.signal_id.value if isinstance(record.signal_id, SignalId) else str(record.signal_id),
            stage=Stage.A5_SOURCE_AUTH.value,
            status=Status.FORBIDDEN.value,
            reason_code=ReasonCode.ACCESS_DENIED.value,
            operation="evidence_company_check",
        )
        return ReplayResult(ReplayOutcome.FORBIDDEN, None)

    try:
        fresh_payload = _sanitize_payload(replay(record))
        fresh_hash = canonical_payload_hash(fresh_payload)
    except SourceFailure as failure:
        # Revoked/denied access is FORBIDDEN; other typed failures are UNAVAILABLE.
        outcome = ReplayOutcome.FORBIDDEN if failure.status.value == "FORBIDDEN" else ReplayOutcome.UNAVAILABLE
        log_ai003_event(
            event_type="ai003_evidence_replay_source_failure",
            correlation_id=correlation_id,
            signal_type=record.signal_id.value if isinstance(record.signal_id, SignalId) else str(record.signal_id),
            stage=Stage.A6_SOURCE_CURRENCY.value,
            status=failure.status.value,
            reason_code=failure.reason_code.value if hasattr(failure.reason_code, "value") else str(failure.reason_code),
            exception_type=type(failure).__name__,
            operation="replay_source_fetch",
        )
        return ReplayResult(outcome, record)
    except Exception as exc:
        log_ai003_event(
            event_type="ai003_evidence_replay_unexpected_failure",
            correlation_id=correlation_id,
            signal_type=record.signal_id.value if isinstance(record.signal_id, SignalId) else str(record.signal_id),
            stage=Stage.A6_SOURCE_CURRENCY.value,
            status=Status.SOURCE_ERROR.value,
            reason_code=ReasonCode.SOURCE_UNAVAILABLE.value,
            exception_type=type(exc).__name__,
            operation="replay_source_fetch",
        )
        return ReplayResult(ReplayOutcome.UNAVAILABLE, record)

    if fresh_hash == record.payload_hash:
        return ReplayResult(ReplayOutcome.MATCH, record, fresh_payload)
    return ReplayResult(ReplayOutcome.RESTATED, record, fresh_payload)
