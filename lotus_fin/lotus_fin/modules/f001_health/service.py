"""
Module F001 - Financial Health Service.
Coordinates deterministic snapshot building, period comparison, and diagnostics.
"""

from typing import Any, Dict, Optional
from lotus_fin.core.use_cases.snapshot_coordinator import SnapshotCoordinator


class HealthService:
    """Service facade for Module F001 Financial Health."""

    def __init__(self, coordinator: Optional[SnapshotCoordinator] = None):
        self._coordinator = coordinator or SnapshotCoordinator()

    def get_financial_snapshot(
        self,
        company: str,
        period_start: str,
        period_end: str,
        include_explanation: bool = False,
        as_of: Optional[str] = None,
        comparison: Optional[str] = None
    ) -> Dict[str, Any]:
        """Builds verified deterministic financial snapshot."""
        return self._coordinator.build_snapshot(
            company=company,
            period_start=period_start,
            period_end=period_end,
            include_explanation=include_explanation,
            as_of=as_of,
            comparison=comparison
        )

