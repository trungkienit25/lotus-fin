"""Port interface for authorized overdue invoice observation read providers.

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §3, §5.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.overdue_invoice_read import PastFinalDueFilterParams


class IAuthorizedOverdueObservationPort(ABC):
    """Port for fetching authoritative invoice observations across providers."""

    @abstractmethod
    def scan_invoice_observations(
        self,
        context: AuthorizedReadContext,
        filters: PastFinalDueFilterParams,
        max_scan_limit: int = 250,
        cursor: Optional[str] = None,
    ) -> Tuple[
        List[AuthorizedOutstandingInvoiceObservation],
        Optional[SourceEvidence],
        bool,  # is_truncated
        ActionStatus,
        ActionReasonCode,
        Optional[str],  # next_cursor
    ]:
        """Scans authoritative candidate observations within authorized scope.
        
        Must enforce tenant/company boundary and fail closed if unconfigured or unauthorized.
        """
        pass
