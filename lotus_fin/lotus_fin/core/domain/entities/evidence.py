from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class EvidenceRef:
    """
    Immutable audit provenance reference tracking ledger reports and records.
    Conforms to Data Strategy §6 and INV-05.
    """
    source_type: str
    source_name: str
    company: str
    filters: Dict[str, Any] = field(default_factory=dict)
    as_of: Optional[str] = None
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    checksum_or_version: Optional[str] = None
    source_record_id: Optional[str] = None
    record_count: Optional[int] = None

    @staticmethod
    def compute_checksum(raw_payload: Any) -> str:
        """Computes deterministic 16-character SHA-256 checksum of payload."""
        if raw_payload is None:
            return ""
        try:
            payload_bytes = json.dumps(raw_payload, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(payload_bytes).hexdigest()[:16]
        except Exception:
            return "unhashable_payload"

    @classmethod
    def create(
        cls,
        source_type: str,
        source_name: str,
        company: str,
        filters: Dict[str, Any],
        as_of: Optional[str] = None,
        raw_payload: Optional[Any] = None,
        source_record_id: Optional[str] = None,
        record_count: Optional[int] = None
    ) -> "EvidenceRef":
        """Factory method to construct an EvidenceRef with auto-checksum."""
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        checksum = cls.compute_checksum(raw_payload) if raw_payload is not None else None
        return cls(
            source_type=source_type,
            source_name=source_name,
            company=company,
            filters=filters,
            as_of=as_of or now_iso,
            retrieved_at=now_iso,
            checksum_or_version=checksum,
            source_record_id=source_record_id,
            record_count=record_count
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes EvidenceRef to a JSON-compatible dictionary."""
        d: Dict[str, Any] = {
            "source_type": self.source_type,
            "source_name": self.source_name,
            "company": self.company,
            "filters": self.filters,
            "as_of": self.as_of,
            "retrieved_at": self.retrieved_at,
            "checksum_or_version": self.checksum_or_version
        }
        if self.source_record_id is not None:
            d["source_record_id"] = self.source_record_id
        if self.record_count is not None:
            d["record_count"] = self.record_count
        return d
