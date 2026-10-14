"""Tests for Stage C OpenAuthorizedInvoice Service.

SSOT: CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md §3, §6.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple
import pytest

from lotus_fin.application.port.i_authorized_invoice_read import IAuthorizedInvoiceReadPort
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.invoice_read import InvoiceReadDocument
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec


def make_dummy_context(company_id="Lotus Corp", capability="invoice.open"):
    return AuthorizedReadContext(
        actor_id="test_user",
        auth_session_binding="sess_12345",
        site_id="site1",
        product_id="lotus",
        connection_id="conn1",
        connection_version="1.0.0",
        company_id=company_id,
        capability=capability,
        projection_version="invoice.min.v1",
        context_version="ctx_12345678",
        observed_at_utc=datetime.now(timezone.utc).isoformat(),
        timezone="Asia/Ho_Chi_Minh",
        deadline_at_utc=(datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat(),
        correlation_id="c0000000-0000-4000-8000-000000000001",
        request_id="a0000000-0000-4000-8000-000000000001",
        adapter_mode="ERP_READ",
    )


class MockOpenInvoicePort(IAuthorizedInvoiceReadPort):
    def __init__(self, doc=None, source=None, status=ActionStatus.OK, reason=ActionReasonCode.DOCUMENT_READY):
        self._doc = doc
        self._source = source
        self._status = status
        self._reason = reason
        self.call_count = 0

    def search_invoices(self, context, filters, page_size, cursor=None, budget=None):
        raise NotImplementedError()

    def open_invoice(self, context, doc_id, expected_record_version, budget=None):
        self.call_count += 1
        return self._doc, self._source, self._status, self._reason


def test_open_invoice_valid_selection():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    ctx = make_dummy_context()
    selection_ref = codec.sign_selection_v2(context=ctx, doc_id="SINV-001", record_version="rec_1")

    doc = InvoiceReadDocument(
        invoice_id="SINV-001",
        company_label="Lotus Corp",
        posting_date=date(2026, 1, 1),
        docstatus=1,
        record_version="rec_1",
    )
    source = SourceEvidence(
        mode="ERP_READ",
        verification="AUTHORIZED_READ",
        product_ref="lotus",
        site_ref="site1",
        connection_ref="conn1",
        connection_version="1.0.0",
        projection_version="invoice.min.v1",
        observed_at="2026-10-12T00:00:00+00:00",
        timezone="Asia/Ho_Chi_Minh",
        coverage="PAGE_COMPLETE",
        consistency="LIVE_KEYSET",
    )
    port = MockOpenInvoicePort(doc=doc, source=source, status=ActionStatus.OK, reason=ActionReasonCode.DOCUMENT_READY)
    svc = OpenAuthorizedInvoiceService(port=port, codec=codec)

    res_doc, res_src, status, reason = svc.execute(ctx, selection_ref=selection_ref)
    assert status == ActionStatus.OK
    assert reason == ActionReasonCode.DOCUMENT_READY
    assert res_doc is not None
    assert res_doc.invoice_id == "SINV-001"
    assert port.call_count == 1


def test_open_invoice_rejects_forged_selection():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    port = MockOpenInvoicePort()
    svc = OpenAuthorizedInvoiceService(port=port, codec=codec)
    ctx = make_dummy_context()

    res_doc, res_src, status, reason = svc.execute(ctx, selection_ref="ref.v2.invalid_payload.invalid_sig")
    assert status == ActionStatus.FORBIDDEN
    assert reason == ActionReasonCode.ACCESS_DENIED
    assert res_doc is None
    assert port.call_count == 0


def test_open_invoice_rejects_cross_scope_context():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    ctx_orig = make_dummy_context(company_id="Company A")
    selection_ref = codec.sign_selection_v2(context=ctx_orig, doc_id="SINV-001", record_version="rec_1")

    # Attacker tries to open with context for Company B
    ctx_b = make_dummy_context(company_id="Company B")
    port = MockOpenInvoicePort()
    svc = OpenAuthorizedInvoiceService(port=port, codec=codec)

    res_doc, res_src, status, reason = svc.execute(ctx_b, selection_ref=selection_ref)
    assert status == ActionStatus.FORBIDDEN
    assert reason == ActionReasonCode.ACCESS_DENIED
    assert res_doc is None
    assert port.call_count == 0


def test_open_invoice_rejects_expired_selection():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    ctx = make_dummy_context()
    selection_ref = codec.sign_selection_v2(context=ctx, doc_id="SINV-001", record_version="rec_1", ttl_seconds=-10)

    port = MockOpenInvoicePort()
    svc = OpenAuthorizedInvoiceService(port=port, codec=codec)

    res_doc, res_src, status, reason = svc.execute(ctx, selection_ref=selection_ref)
    assert status == ActionStatus.NOT_AVAILABLE
    assert reason == ActionReasonCode.STALE_SELECTION
    assert res_doc is None
    assert port.call_count == 0
