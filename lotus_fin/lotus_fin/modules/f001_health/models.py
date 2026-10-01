"""
Module F001 - Financial Health Models and DTOs.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class HealthMetric:
    metric_id: str
    status: str
    value: Optional[Decimal]
    currency_or_unit: str
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "status": self.status,
            "value": float(self.value) if self.value is not None else None,
            "currency_or_unit": self.currency_or_unit,
            "limitations": self.limitations,
        }


@dataclass
class AuditEvidence:
    report_key: str
    source_name: str
    record_count: int
    retrieved_at: str
    checksum: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_key": self.report_key,
            "source_name": self.source_name,
            "record_count": self.record_count,
            "retrieved_at": self.retrieved_at,
            "checksum": self.checksum,
            "parameters": self.parameters,
        }


@dataclass
class HealthSnapshot:
    company: str
    period: Dict[str, str]
    metrics: List[HealthMetric]
    evidences: List[AuditEvidence]
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "period": self.period,
            "metrics": [m.to_dict() for m in self.metrics],
            "evidence": [e.to_dict() for e in self.evidences],
            "limitations": self.limitations,
        }
