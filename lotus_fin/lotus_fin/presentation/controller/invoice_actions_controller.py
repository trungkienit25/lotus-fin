"""Invoice Actions Presentation Controller.

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3, §4, §8; CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from typing import Any, Dict, Optional, Tuple
import base64
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters
from lotus_fin.application.port.i_action_events import IActionEventsPort
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.domain.schema.action_outcome import ActionOutcome, ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.infrastructure.config.invoice_actions_config import InvoiceActionsConfig
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.presentation.dto.invoice_action_request import ContextRequestDTO, ContextDataDTO, OpenRequestDTO, SearchRequestDTO
from lotus_fin.presentation.response.action_response import ActionResponseBuilder
from lotus_fin.presentation.response.invoice_action_delivery import InvoiceActionDelivery


class InvoiceActionsController:
    """Controller handling invoice actions boundary. Disabled by default."""

    def __init__(
        self, config: InvoiceActionsConfig, resolve_service: ResolveReadContextService,
        codec: ActionReferenceCodec, events_port: Optional[IActionEventsPort] = None,
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

        try:
            observed = datetime.fromisoformat(context.observed_at_utc)
            if observed.utcoffset() is None:
                raise ValueError("Unqualified observation time")
            dates = InvoiceReadFilters().normalized(observed.astimezone(ZoneInfo(context.timezone)).date())
            ctx_ref = self._codec.sign_reference(
                purpose="invoice.context", context=context, ttl_seconds=self._config.reference_ttl_seconds)
            if not self._codec.verify_reference(ctx_ref, "invoice.context", context)[0]:
                raise ValueError("Unqualified context reference")
            payload = ctx_ref.split(".")[2]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            data = ContextDataDTO(context_ref=ctx_ref, context_version=context.context_version,
                company_label=context.company_id, default_posting_from=dates.posting_from,
                default_posting_to=dates.posting_to,
                expires_at=datetime.fromtimestamp(claims["expires_at"], timezone.utc)).model_dump(mode="json")
        except (ValueError, TypeError, KeyError, OverflowError):
            return self._failure(raw_body, "invoice.context", cid,
                ActionStatus.NOT_AVAILABLE, ActionReasonCode.TARGET_UNQUALIFIED)
        src = SourceEvidence(
            mode=context.adapter_mode, verification="AUTHORIZED_READ", product_ref=context.product_id,
            site_ref=context.site_id, connection_ref=context.connection_id,
            connection_version=context.connection_version, projection_version=context.projection_version,
            observed_at=context.observed_at_utc, timezone=context.timezone,
            coverage="PAGE_COMPLETE", consistency="LIVE_KEYSET")
        outcome = ActionOutcome(
            contract_version="p1.invoice.v1", status=ActionStatus.OK,
            reason_code=ActionReasonCode.CONTEXT_READY, correlation_id=cid,
            request_id=req.request_id, capability="invoice.context", source=src,
            context_version=context.context_version, data=data,
            user_message=ActionResponseBuilder.get_safe_message(ActionReasonCode.CONTEXT_READY))
        return self._delivery.complete(outcome)

    def _scope_context(self, raw: Dict[str, Any], cap: str, cid: str, ref: str, exp_ver: str):
        try:
            parts = ref.split(".")
            if len(parts) != 4 or (parts[0], parts[1]) != ("ref", "v1"):
                return None, self._failure(raw, cap, cid, ActionStatus.NOT_AVAILABLE, ActionReasonCode.TARGET_UNQUALIFIED)
            payload = parts[2]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            company_id = claims.get("company_id")
        except Exception:
            return None, self._failure(raw, cap, cid, ActionStatus.NOT_AVAILABLE, ActionReasonCode.TARGET_UNQUALIFIED)

        ctx, chk = self._resolve_service.execute(company_id, cap, raw.get("request_id"), cid)
        if not chk.is_authorized or not ctx:
            return None, self._failure(raw, cap, cid, chk.status, chk.reason_code)

        ok, err = self._codec.verify_reference(ref, "invoice.context", ctx)
        if not ok:
            s = ActionStatus.NOT_AVAILABLE if err == "Reference expired." else ActionStatus.FORBIDDEN
            r = ActionReasonCode.CONTEXT_CHANGED if err == "Reference expired." else ActionReasonCode.ACCESS_DENIED
            return None, self._failure(raw, cap, cid, s, r)

        if exp_ver != ctx.context_version:
            return None, self._failure(raw, cap, cid, ActionStatus.NOT_AVAILABLE, ActionReasonCode.CONTEXT_CHANGED)
        return ctx, None

    def search_invoices(
        self, raw_body: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        cid = self._delivery.server_cid(correlation_id)
        if not self._delivery.available or not self._config.enabled or self._search_service is None:
            return self._failure(raw_body, "invoice.search", cid,
                ActionStatus.NOT_AVAILABLE, ActionReasonCode.CAPABILITY_DISABLED)
        try:
            req = SearchRequestDTO(**raw_body)
        except (ValueError, TypeError):
            return self._failure(raw_body, "invoice.search", cid,
                ActionStatus.NOT_AVAILABLE, ActionReasonCode.INVALID_REQUEST)

        ctx, fail = self._scope_context(raw_body, "invoice.search", cid, req.context_ref, req.expected_context_version)
        if fail:
            return fail

        page, source, status, reason = self._search_service.execute(ctx, req.filters, req.page_size, req.cursor)
        if status != ActionStatus.OK:
            return self._failure(raw_body, "invoice.search", cid, status, reason)

        outcome = ActionOutcome(
            contract_version="p1.invoice.v1", status=ActionStatus.OK, reason_code=reason,
            correlation_id=cid, request_id=req.request_id, capability="invoice.search",
            source=source, context_version=ctx.context_version, data=page.model_dump(mode="json"),
            user_message=ActionResponseBuilder.get_safe_message(reason))
        return self._delivery.complete(outcome)

    def open_invoice(
        self, raw_body: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Tuple[int, Dict[str, str], Dict[str, Any]]:
        cid = self._delivery.server_cid(correlation_id)
        if not self._delivery.available or not self._config.enabled or self._open_service is None:
            return self._failure(raw_body, "invoice.open", cid,
                ActionStatus.NOT_AVAILABLE, ActionReasonCode.CAPABILITY_DISABLED)
        try:
            req = OpenRequestDTO(**raw_body)
        except (ValueError, TypeError):
            return self._failure(raw_body, "invoice.open", cid,
                ActionStatus.NOT_AVAILABLE, ActionReasonCode.INVALID_REQUEST)

        ctx, fail = self._scope_context(raw_body, "invoice.open", cid, req.context_ref, req.expected_context_version)
        if fail:
            return fail

        doc, source, status, reason = self._open_service.execute(ctx, req.selection_ref)
        if status != ActionStatus.OK:
            return self._failure(raw_body, "invoice.open", cid, status, reason)

        data = {"document": doc.model_dump(mode="json", exclude={"company_label", "navigation"}),
            "company_label": doc.company_label, "navigation": doc.navigation}
        outcome = ActionOutcome(
            contract_version="p1.invoice.v1", status=ActionStatus.OK, reason_code=reason,
            correlation_id=cid, request_id=req.request_id, capability="invoice.open",
            source=source, context_version=ctx.context_version, data=data,
            user_message=ActionResponseBuilder.get_safe_message(reason))
        return self._delivery.complete(outcome)
