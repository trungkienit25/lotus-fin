from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from lotus_fin.core.domain.values.money import Money
from lotus_fin.core.domain.values.ratio import Ratio
from lotus_fin.core.domain.values.period import AccountingPeriod
from lotus_fin.core.domain.values.metric_types import MetricId, MetricStatus, SnapshotStatus
from lotus_fin.core.domain.entities.evidence import EvidenceRef


@dataclass(frozen=True)
class MetricEntry:
    """Represents a validated financial metric within a snapshot."""
    metric_id: MetricId
    status: MetricStatus
    amount: Optional[Money] = None
    ratio: Optional[Ratio] = None
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        return self.status == MetricStatus.AVAILABLE

    def to_dict(self) -> Dict[str, Any]:
        """Serializes MetricEntry conforming to API contracts."""
        d: Dict[str, Any] = {
            "status": self.status.value,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
        }
        if self.amount is not None:
            d["amount"] = float(self.amount.amount)
            d["currency"] = self.amount.currency
        if self.ratio is not None:
            d["ratio"] = float(self.ratio.value)
        return d


@dataclass(frozen=True)
class FinancialSnapshot:
    """
    Pure domain entity representing a point-in-time or period financial inspection snapshot.
    Immutable, deterministic, and free of framework dependencies.
    """
    company: str
    period: AccountingPeriod
    currency: str = "VND"
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: SnapshotStatus = SnapshotStatus.OK
    contract_version: str = "1.0.0"
    formula_version: str = "2026.1"
    metrics: Dict[str, MetricEntry] = field(default_factory=dict)
    evidence: Dict[str, EvidenceRef] = field(default_factory=dict)
    system_limitations: List[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def get_metric(self, metric_id: str) -> Optional[MetricEntry]:
        return self.metrics.get(metric_id)

    def is_metric_available(self, metric_id: str) -> bool:
        m = self.metrics.get(metric_id)
        return m is not None and m.is_available

    def to_dict(self) -> Dict[str, Any]:
        """Serializes complete snapshot for API envelope."""
        return {
            "snapshot_id": self.snapshot_id,
            "company": self.company,
            "period_start": self.period.start_date.isoformat(),
            "period_end": self.period.end_date.isoformat(),
            "currency": self.currency,
            "status": self.status.value,
            "contract_version": self.contract_version,
            "formula_version": self.formula_version,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "evidence": {k: v.to_dict() for k, v in self.evidence.items()},
            "system_limitations": list(self.system_limitations),
            "created_at": self.created_at,
        }
