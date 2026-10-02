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
from typing import Callable, Dict, Mapping, Optional

from lotus_fin.risk_signal.contracts import (
    ACCOUNTING_TIMEZONE,
    METHOD_VERSION,
    SignalId,
)
from lotus_fin.risk_signal.observability import hash_id
from lotus_fin.risk_signal.provenance import (
    SourceFailure,
    canonical_payload_hash,
)

EVIDENCE_KIND_REPORT_SNAPSHOT = "REPORT_SNAPSHOT"
MAX_EVIDENCE_RECORDS = 500


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


class EvidenceStore:
    """Server-side bounded evidence record store (in-memory, per process)."""

    def __init__(self, max_records: int = MAX_EVIDENCE_RECORDS) -> None:
        self._records: Dict[str, EvidenceRecord] = {}
        self._order: list = []
        self._max = max_records
        self._lock = threading.Lock()

    def create(self, record: EvidenceRecord) -> EvidenceRecord:
        with self._lock:
            self._records[record.ref] = record
            self._order.append(record.ref)
            while len(self._order) > self._max:
                evicted = self._order.pop(0)
                self._records.pop(evicted, None)
        return record

    def get(self, ref: str) -> Optional[EvidenceRecord]:
        with self._lock:
            return self._records.get(ref)

    def __len__(self) -> int:
        with self._lock:
            return len(self._records)


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
) -> ReplayResult:
    """Authorized dynamic replay: reauthorization first, then hash comparison.

    ``replay`` re-runs the approved source path in checked-user context for the
    captured record (its cutoff/scope) and returns the fresh sanitized payload;
    it raises SourceFailure on typed failures. The deterministic result of the
    original evaluation is never altered by evidence access.
    """
    if not isinstance(ref, str) or not ref.startswith("AI003-EV-"):
        return ReplayResult(ReplayOutcome.FORBIDDEN, None)
    record = _STORE.get(ref)
    if record is None or record.company != verified_company:
        return ReplayResult(ReplayOutcome.FORBIDDEN, None)
    try:
        fresh_payload = _sanitize_payload(replay(record))
        fresh_hash = canonical_payload_hash(fresh_payload)
    except SourceFailure as failure:
        # Revoked/denied access is FORBIDDEN; other typed failures are UNAVAILABLE.
        outcome = ReplayOutcome.FORBIDDEN if failure.status.value == "FORBIDDEN" else ReplayOutcome.UNAVAILABLE
        return ReplayResult(outcome, record)
    except Exception:
        return ReplayResult(ReplayOutcome.UNAVAILABLE, record)
    if fresh_hash == record.payload_hash:
        return ReplayResult(ReplayOutcome.MATCH, record, fresh_payload)
    return ReplayResult(ReplayOutcome.RESTATED, record, fresh_payload)
