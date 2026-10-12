"""Invoice Actions Presentation Controller.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3, §4, §8; CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Any, Dict, Optional, Tuple
from lotus_fin.application.port.i_action_events import IActionEventsPort
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.domain.schema.action_outcome import ActionOutcome, ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.infrastructure.config.invoice_actions_config import InvoiceActionsConfig
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.presentation.dto.invoice_action_request import (
    ContextRequestDTO,
    OpenRequestDTO,
    SearchRequestDTO,
)
from lotus_fin.presentation.response.action_response import ActionResponseBuilder
from lotus_fin.presentation.response.invoice_action_delivery import InvoiceActionDelivery


class InvoiceActionsController:
    """Controller handling invoice actions boundary. Disabled by default."""

    def __init__(
        self,
        config: InvoiceActionsConfig,
        resolve_service: ResolveReadContextService,
        codec: ActionReferenceCodec,
        events_port: Optional[IActionEventsPort] = None,
        search_service: Optional[SearchInvoicesService] = None,
        open_service: Optional[OpenAuthorizedInvoiceService] = None,
    ) -> None:
        self._config = config
        self._resolve_service = resolve_service
        self._codec = codec
        self._delivery = InvoiceActionDelivery(events_port)
        self._search_service = search_service
        self._open_service = open_service

    def _failure(self, raw_body, capability, cid, status, reason):
        request_id = raw_body.get("request_id") if isinstance(raw_body, dict) else None
        return self._delivery.failure(status, reason, capability, request_id, cid)

    def get_context(
        self, raw_body: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        cid = self._delivery.server_cid(correlation_id)
        try:
            req = ContextRequestDTO(**raw_body)
        except (ValueError, TypeError):
            return self._failure(raw_body, "invoice.context", cid,
                ActionStatus.NOT_AVAILABLE, ActionReasonCode.INVALID_REQUEST)

        if not self._delivery.available or not self._config.enabled:
            return self._failure(raw_body, "invoice.context", cid,
                ActionStatus.NOT_AVAILABLE, ActionReasonCode.CAPABILITY_DISABLED)

        context, check = self._resolve_service.execute(
            candidate_company=req.company_candidate,
            capability="invoice.context",
            client_request_id=req.request_id,
            correlation_id=cid,
        )
        if not check.is_authorized or not context:
            return self._failure(raw_body, "invoice.context", cid, check.status, check.reason_code)

        ctx_ref = self._codec.sign_reference(
            purpose="invoice.context", context=context, ttl_seconds=self._config.reference_ttl_seconds
        )
        data = {
            "context_ref": ctx_ref,
            "context_version": context.context_version,
            "company_label": context.company_id,
            "allowed_filters": ["invoice_name_prefix", "posting_date", "docstatus"],
            "expires_at": context.deadline_at_utc,
        }
        src = SourceEvidence(
            mode=context.adapter_mode,
            verification="AUTHORIZED_READ",
            product_ref=context.product_id,
            site_ref=context.site_id,
            connection_ref=context.connection_id,
            connection_version=context.connection_version,
            projection_version=context.projection_version,
            observed_at=context.observed_at_utc,
            timezone=context.timezone,
            coverage="PAGE_COMPLETE",
            consistency="LIVE_KEYSET",
        )
        outcome = ActionOutcome(
            contract_version="p1.invoice.v1",
            status=ActionStatus.OK,
            reason_code=ActionReasonCode.CONTEXT_READY,
            correlation_id=cid,
            request_id=req.request_id,
            capability="invoice.context",
            source=src,
            context_version=context.context_version,
            data=data,
            user_message=ActionResponseBuilder.get_safe_message(ActionReasonCode.CONTEXT_READY),
        )
        return self._delivery.complete(outcome)

    def search_invoices(
        self, raw_body: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        cid = self._delivery.server_cid(correlation_id)
        # Search is strictly disabled in offline default configuration
        return self._failure(raw_body, "invoice.search", cid,
            ActionStatus.NOT_AVAILABLE, ActionReasonCode.CAPABILITY_DISABLED)

    def open_invoice(
        self, raw_body: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        cid = self._delivery.server_cid(correlation_id)
        # Open is strictly disabled in offline default configuration
        return self._failure(raw_body, "invoice.open", cid,
            ActionStatus.NOT_AVAILABLE, ActionReasonCode.CAPABILITY_DISABLED)
