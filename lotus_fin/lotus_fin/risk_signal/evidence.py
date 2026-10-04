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
evidence records, TTL-bounded (3600s) in the site-scoped Redis cache, never
serving stale authorization.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Callable, Mapping, Optional

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
DEFAULT_EVIDENCE_TTL_SECONDS = 3600  # 1 hour bounded TTL
EVIDENCE_KEY_PREFIX = "ai003:evidence:"


class EvidenceStorageUnavailable(Exception):
    """Typed fail-closed evidence-cache failure.

    Raised whenever the Redis boundary (init, SET, GET, DELETE) fails or the
    store cannot resolve a cache client. The message is generic — internal
    error detail stays in the structured audit event only. Callers map this to
    typed UNAVAILABLE (replay) or a suppressed evidence ref (store path).
    """

    def __init__(self, cause_type: str = "Unknown") -> None:
        super().__init__("evidence storage unavailable")
        self.cause_type = cause_type


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


def _deserialize_record(data) -> EvidenceRecord:
    """Strictly validate + rebuild a stored record. Any malformed legacy or
    corrupt payload raises here so the caller's typed boundary catches it —
    never pickle.loads, never silent partial records."""
    if not isinstance(data, dict):
        raise ValueError("evidence record is not an object")
    ref = data.get("ref")
    company = data.get("company")
    if not isinstance(ref, str) or not ref.startswith("AI003-EV-"):
        raise ValueError("evidence record ref malformed")
    if not isinstance(company, str) or not company:
        raise ValueError("evidence record company malformed")
    as_of = data.get("as_of_date")
    if not isinstance(as_of, str):
        raise ValueError("evidence record as_of_date malformed")
    as_of = date.fromisoformat(as_of)
    try:
        signal_id = SignalId(data.get("signal_id"))
    except Exception:
        raise ValueError("evidence record signal_id malformed") from None
    raw_payload = data.get("payload")
    if not isinstance(raw_payload, dict):
        raise ValueError("evidence record payload malformed")
    scope_fingerprint = data.get("scope_fingerprint")
    payload_hash = data.get("payload_hash")
    captured_at = data.get("captured_at")
    kind = data.get("kind", EVIDENCE_KIND_REPORT_SNAPSHOT)
    if not all(isinstance(v, str) for v in (scope_fingerprint, payload_hash, captured_at, kind)):
        raise ValueError("evidence record metadata malformed")
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
        ref=ref,
        company=company,
        signal_id=signal_id,
        as_of_date=as_of,
        kind=kind,
        scope_fingerprint=scope_fingerprint,
        payload_hash=payload_hash,
        payload=sanitized_payload,
        captured_at=captured_at,
    )


class EvidenceStore:
    """Server-side evidence record store shared across Gunicorn workers via the
    Frappe Redis cache client.

    Boundary rules (G4B remediation):
    - Raw Redis commands (``setex``/``get``/``delete``) are used directly — the
      Frappe convenience wrappers (``set_value``/``get_value``) swallow
      ConnectionError and would turn a store failure into a silent miss.
    - Keys are site-namespaced via ``make_key()`` under ``ai003:evidence:``.
    - Any Redis connection error/timeout is surfaced as typed
      ``EvidenceStorageUnavailable``; there is NO process-local fallback.
    - Missing/expired keys are a clean ``None`` (distinct from failures).
    """

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_EVIDENCE_TTL_SECONDS,
        client: Optional[Any] = None,
    ) -> None:
        self._ttl = ttl_seconds
        self._client = client

    def _get_client(self, *, operation: str, stage: str, correlation_id: Optional[str]):
        """Resolve the cache client. Failure is never silent (no local
        fallback): it is logged once and surfaced as a typed error."""
        if self._client is not None:
            return self._client
        try:
            import frappe

            if not (getattr(frappe.local, "site", None) or getattr(frappe.local, "conf", None)):
                raise RuntimeError("no frappe site context for evidence cache")
            cache = frappe.cache()
            if cache is None:
                raise RuntimeError("frappe cache unavailable")
            return cache
        except Exception as exc:
            self._storage_failure(
                exc, operation=operation, stage=stage, correlation_id=correlation_id
            )

    @staticmethod
    def _make_key(client: Any, ref: str) -> str:
        key = f"{EVIDENCE_KEY_PREFIX}{ref}"
        make_key = getattr(client, "make_key", None)
        if callable(make_key):
            return make_key(key)  # site-namespaced by Frappe's RedisWrapper
        return key

    def _storage_failure(
        self,
        exc: Exception,
        *,
        operation: str,
        stage: str,
        correlation_id: Optional[str],
    ) -> None:
        log_ai003_event(
            event_type="ai003_evidence_storage_error",
            correlation_id=correlation_id,
            stage=stage,
            status=Status.SOURCE_ERROR.value,
            reason_code=ReasonCode.SOURCE_UNAVAILABLE.value,
            exception_type=type(exc).__name__,
            operation=operation,
        )
        raise EvidenceStorageUnavailable(cause_type=type(exc).__name__) from exc

    def put(self, record: EvidenceRecord, correlation_id: Optional[str] = None) -> str:
        """Persist one record with bounded TTL; return the opaque ref only
        after a successful SET. Returns nothing on failure — the typed error
        propagates so no un-persisted ref is ever handed out."""
        serialized = _serialize_record(record)
        client = self._get_client(
            operation="evidence_cache_init",
            stage=Stage.A10_EVALUATION.value,
            correlation_id=correlation_id,
        )
        key = self._make_key(client, record.ref)
        try:
            client.setex(key, self._ttl, json.dumps(serialized, sort_keys=True, default=str))
        except Exception as exc:
            self._storage_failure(
                exc,
                operation="evidence_cache_set",
                stage=Stage.A10_EVALUATION.value,
                correlation_id=correlation_id,
            )
        return record.ref

    def create(self, record: EvidenceRecord, correlation_id: Optional[str] = None) -> EvidenceRecord:
        """Backward-compatible put returning the record."""
        self.put(record, correlation_id=correlation_id)
        return record

    def get(self, ref: str, correlation_id: Optional[str] = None) -> Optional[EvidenceRecord]:
        """Fetch record by ref. ``None`` means missing/expired (clean miss);
        command, decode, JSON-parse or record-validation failures raise typed
        ``EvidenceStorageUnavailable`` (legacy pickle or corrupt records must
        never surface as unhandled endpoint exceptions)."""
        if not isinstance(ref, str) or not ref:
            return None

        client = self._get_client(
            operation="evidence_cache_init",
            stage=Stage.A5_SOURCE_AUTH.value,
            correlation_id=correlation_id,
        )
        key = self._make_key(client, ref)
        try:
            raw = client.get(key)
        except Exception as exc:
            self._storage_failure(
                exc,
                operation="evidence_cache_get",
                stage=Stage.A5_SOURCE_AUTH.value,
                correlation_id=correlation_id,
            )
        if raw is None:
            return None
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            if not isinstance(raw, str):
                raise TypeError("unexpected cache payload type")
            record = _deserialize_record(json.loads(raw))
        except Exception as exc:
            # One structured, sanitized diagnostic; no raw bytes, record
            # content or exception text is ever logged or surfaced.
            self._storage_failure(
                exc,
                operation="evidence_cache_decode",
                stage=Stage.A5_SOURCE_AUTH.value,
                correlation_id=correlation_id,
            )
        return record

    def delete(self, ref: str, correlation_id: Optional[str] = None) -> None:
        """Evict record by ref; Redis failures are surfaced, not swallowed."""
        if not isinstance(ref, str) or not ref:
            return

        client = self._get_client(
            operation="evidence_cache_init",
            stage=Stage.A10_EVALUATION.value,
            correlation_id=correlation_id,
        )
        key = self._make_key(client, ref)
        try:
            client.delete(key)
        except Exception as exc:
            self._storage_failure(
                exc,
                operation="evidence_cache_delete",
                stage=Stage.A10_EVALUATION.value,
                correlation_id=correlation_id,
            )


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
    correlation_id: Optional[str] = None,
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
    return _STORE.create(record, correlation_id=correlation_id)


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

    try:
        record = _STORE.get(ref, correlation_id=correlation_id)
    except EvidenceStorageUnavailable:
        # Redis boundary failure (outage/timeout) — distinct from a clean miss;
        # the boundary event with correlation id was logged by the store.
        return ReplayResult(ReplayOutcome.UNAVAILABLE, None)

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
