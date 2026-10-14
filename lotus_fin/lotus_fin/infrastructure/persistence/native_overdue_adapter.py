"""Native Overdue Adapter Interface & Configuration Stub.

SSOT: V1_OVERDUE_SOURCE_AND_CONTRACT_CLOSURE.md §5.
Remains strictly BLOCKED until N0 authoritative data approval.
No ERPNext fallback or ad-hoc table coupling.
"""

from typing import List, Optional, Tuple

from lotus_fin.application.port.i_overdue_observation_port import IAuthorizedOverdueObservationPort
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.model.overdue_invoice_observation import AuthorizedOutstandingInvoiceObservation
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.overdue_invoice_read import PastFinalDueFilterParams


class NativeOverdueAdapterConfig:
    """Configuration contract for future native data connection."""
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        auth_token_secret_name: Optional[str] = None,
        tenant_mapping: Optional[dict] = None,
        is_n0_approved: bool = False,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.auth_token_secret_name = auth_token_secret_name
        self.tenant_mapping = tenant_mapping or {}
        self.is_n0_approved = is_n0_approved


class NativeOverdueObservationAdapter(IAuthorizedOverdueObservationPort):
    """Native source adapter skeleton.
    
    Fails closed with TARGET_UNQUALIFIED until N0 gate is unlocked and authoritative
    data pipeline is provisioned and audited.
    """

    def __init__(self, config: Optional[NativeOverdueAdapterConfig] = None) -> None:
        self.config = config or NativeOverdueAdapterConfig(is_n0_approved=False)

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
        if not self.config.is_n0_approved:
            # Strictly blocked by N0 gate
            return (
                [],
                None,
                False,
                ActionStatus.NOT_AVAILABLE,
                ActionReasonCode.TARGET_UNQUALIFIED,
                None,
            )

        raise NotImplementedError("Native adapter execution is awaiting N0 gate qualification.")
