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
        source_fetcher = None
        user = None
        try:
            import frappe
            if hasattr(frappe, "local") and hasattr(frappe.local, "db") and frappe.local.db:
                from lotus_fin.api.ai_insights import extract_key_report_data
                user = getattr(frappe.session, "user", "Administrator") if hasattr(frappe, "session") else "Administrator"

                def _frappe_report_fetcher(report_key: str, filters: Dict[str, Any], comp: str):
                    res = extract_key_report_data(report_key=report_key, filters=filters, company=comp)
                    if hasattr(frappe, "message_log") and isinstance(frappe.message_log, list):
                        frappe.message_log.clear()
                    return res

                source_fetcher = _frappe_report_fetcher
        except Exception:
            pass

        return self._coordinator.build_snapshot(
            company=company,
            period_start=period_start,
            period_end=period_end,
            include_explanation=include_explanation,
            as_of=as_of,
            comparison=comparison,
            source_fetcher=source_fetcher,
            user=user
        )

