"""Core Provider for overdue invoice observations.

Returns NOT_AVAILABLE when native provider is unconfigured. Never invents synthetic data.
SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §5.
"""

from typing import List, Optional, Tuple

from lotus_fin.application.port.i_overdue_observation_port import IAuthorizedOverdueObservationPort
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.overdue_invoice_read import PastFinalDueFilterParams


class CoreOverdueObservationProvider(IAuthorizedOverdueObservationPort):
    """Core production-default provider.
    
    Truthfully reports NOT_AVAILABLE / TARGET_UNQUALIFIED when native ERP adapter is not configured.
    Zero synthetic or hallucinated records.
    """

    def __init__(self, is_configured: bool = False) -> None:
        self.is_configured = is_configured

    def scan_invoice_observations(
        self,
        context: AuthorizedReadContext,
        filters: PastFinalDueFilterParams,
        max_scan_limit: int = 250,
        cursor: Optional[str] = None,
    ) -> Tuple[
        List[AuthorizedOutstandingInvoiceObservation],
        Optional[SourceEvidence],
        bool,
        ActionStatus,
        ActionReasonCode,
        Optional[str],
    ]:
        if not self.is_configured:
            return (
                [],
                None,
                False,
                ActionStatus.NOT_AVAILABLE,
                ActionReasonCode.TARGET_UNQUALIFIED,
                None,
            )

        # Future configured native handoff will route here
        return [], None, False, ActionStatus.OK, ActionReasonCode.EMPTY_RESULT, None
