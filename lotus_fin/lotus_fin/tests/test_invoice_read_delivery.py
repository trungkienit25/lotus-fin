"""Synthetic core→DTO→real required stream delivery; not live Frappe HTTP."""
import io
import logging
import pytest
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters
from lotus_fin.domain.schema.action_outcome import ActionOutcome, ActionStatus as S, ActionReasonCode as R
from lotus_fin.presentation.dto.invoice_action_response import SearchResponseDataDTO, OpenResponseDataDTO
from lotus_fin.presentation.response.invoice_action_delivery import InvoiceActionDelivery
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents
from lotus_fin.application.port.i_action_events import ActionEventDeliveryError
from lotus_fin.tests.test_invoice_read_security import fixture


def test_open_dto_is_master_minimum(fixture):
    ctx, _, _, _, doc, _, _ = fixture
    data = OpenResponseDataDTO.from_document(doc).model_dump(mode="json")
    assert set(data) == {"document", "company_label", "navigation"}
    assert set(data["document"]) == {"invoice_type", "invoice_id", "posting_date", "docstatus", "record_version"}
    assert data["company_label"] == ctx.company_id
    assert data["navigation"] == {"kind": "LOTUS_READ_VIEW", "view": "sales-invoice-minimal-v1"}


@pytest.mark.parametrize("operation", ["search", "open"])
@pytest.mark.parametrize("sink_state", ["healthy", "outage"])
def test_core_to_terminal_is_single_safe_delivery(fixture, operation, sink_state):
    ctx, src, _, page, doc, port, codec = fixture
    logger = logging.Logger("private-action-fixture", logging.INFO)
    class BrokenStream(io.StringIO):
        def write(self, value): raise OSError("private-error-canary")
    stream = io.StringIO() if sink_state == "healthy" else BrokenStream()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    sink = SafeStructuredActionEvents(logger)
    delivery = InvoiceActionDelivery(sink)
    try:
        assert delivery.available
        if operation == "search":
            port.result = page, src, S.OK, R.RESULTS_FOUND
            result, source, status, reason = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20)
            data = SearchResponseDataDTO(**result.model_dump()).model_dump(mode="json")
        else:
            ctx = ctx.model_copy(update={"capability": "invoice.open"})
            port.result = doc, src, S.OK, R.DOCUMENT_READY
            result, source, status, reason = OpenAuthorizedInvoiceService(port, codec).execute(ctx, codec.sign_selection_v2(ctx, "INV-A", "rev1"))
            data = OpenResponseDataDTO.from_document(result).model_dump(mode="json")
        outcome = ActionOutcome(status=status, reason_code=reason, correlation_id=ctx.correlation_id,
            request_id=ctx.request_id, capability=ctx.capability, source=source,
            context_version=ctx.context_version, data=data, user_message="safe")
        if sink_state == "outage":
            with pytest.raises(ActionEventDeliveryError): delivery.complete(outcome)
            assert sink.recorded_events == []
        else:
            http, headers, body = delivery.complete(outcome)
            assert http == 200 and headers["X-Correlation-ID"] == body["correlation_id"] == ctx.correlation_id
            assert body["request_id"] == ctx.request_id and len(sink.recorded_events) == 1
            assert len(stream.getvalue().splitlines()) == 1
            assert "INV-A" not in stream.getvalue() and "ref.v2" not in stream.getvalue()
    finally:
        logger.removeHandler(handler)
        handler.close()
        stream.close()
