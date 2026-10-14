"""Tests for Stage B SearchInvoices Service.

SSOT: CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md §2, §4, §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple
import pytest

from lotus_fin.application.port.i_authorized_invoice_read import IAuthorizedInvoiceReadPort
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus, SourceEvidence
from lotus_fin.domain.schema.invoice_read import (
    DocStatusFilter,
    InvoiceReadFilters,
    InvoiceReadPage,
    InvoiceReadRow,
)
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec


def make_dummy_context(company_id="Lotus Corp", capability="invoice.search"):
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


class MockInvoiceReadPort(IAuthorizedInvoiceReadPort):
    def __init__(self, page=None, source=None, status=ActionStatus.OK, reason=ActionReasonCode.RESULTS_FOUND):
        self._page = page
        self._source = source
        self._status = status
        self._reason = reason
        self.call_count = 0

    def search_invoices(self, context, filters, page_size, cursor=None, budget=None):
        self.call_count += 1
        return self._page, self._source, self._status, self._reason

    def open_invoice(self, context, doc_id, expected_record_version, budget=None):
        raise NotImplementedError()


def test_search_complete_results_signs_selection_refs():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    row = InvoiceReadRow(
        invoice_id="SINV-001",
        posting_date=date.today(),
        docstatus=1,
        record_version="rec_1",
        selection_ref=None,
    )
    page = InvoiceReadPage(
        items=[row],
        returned_count=1,
        total_count=None,
        page_complete=True,
        has_more=False,
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
    port = MockInvoiceReadPort(page=page, source=source, status=ActionStatus.OK, reason=ActionReasonCode.RESULTS_FOUND)
    svc = SearchInvoicesService(port=port, codec=codec)
    ctx = make_dummy_context()
    filters = InvoiceReadFilters()

    res_page, res_src, status, reason = svc.execute(ctx, filters, page_size=20)
    assert status == ActionStatus.OK
    assert reason == ActionReasonCode.RESULTS_FOUND
    assert res_page is not None
    assert len(res_page.items) == 1
    # Check that selection_ref was signed
    assert res_page.items[0].selection_ref is not None
    assert res_page.items[0].selection_ref.startswith("ref.v2.")

    # Verify that the signed ref can be decoded and verified by codec
    valid, claims, err = codec.verify_selection_v2(res_page.items[0].selection_ref, ctx)
    assert valid is True
    assert claims.doc_id == "SINV-001"
    assert claims.record_version == "rec_1"


def test_search_partial_results_strips_all_selection_refs():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    row = InvoiceReadRow(
        invoice_id="SINV-001",
        posting_date=date.today(),
        docstatus=1,
        record_version="rec_1",
        selection_ref="ref.v2.adversarial_prefilled",
    )
    page = InvoiceReadPage(
        items=[row],
        returned_count=1,
        total_count=None,
        page_complete=False,
        has_more=None,
        next_cursor=None,
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
        coverage="INCOMPLETE",
        consistency="LIVE_KEYSET",
    )
    port = MockInvoiceReadPort(page=page, source=source, status=ActionStatus.PARTIAL, reason=ActionReasonCode.COVERAGE_INCOMPLETE)
    svc = SearchInvoicesService(port=port, codec=codec)
    ctx = make_dummy_context()
    filters = InvoiceReadFilters()

    res_page, res_src, status, reason = svc.execute(ctx, filters, page_size=20)
    assert status == ActionStatus.PARTIAL
    assert reason == ActionReasonCode.COVERAGE_INCOMPLETE
    assert res_page is not None
    assert res_page.items[0].selection_ref is None
    assert res_page.page_complete is False


def test_search_empty_result_complete():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    page = InvoiceReadPage(
        items=[],
        returned_count=0,
        total_count=None,
        page_complete=True,
        has_more=False,
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
    port = MockInvoiceReadPort(page=page, source=source, status=ActionStatus.OK, reason=ActionReasonCode.EMPTY_RESULT)
    svc = SearchInvoicesService(port=port, codec=codec)
    ctx = make_dummy_context()
    filters = InvoiceReadFilters()

    res_page, res_src, status, reason = svc.execute(ctx, filters, page_size=20)
    assert status == ActionStatus.OK
    assert reason == ActionReasonCode.EMPTY_RESULT
    assert res_page.returned_count == 0


def test_search_denied_or_error_port():
    codec = ActionReferenceCodec(key_id="k1", secret_key="supersecretkey1234567890123456789012")
    port = MockInvoiceReadPort(page=None, source=None, status=ActionStatus.FORBIDDEN, reason=ActionReasonCode.ACCESS_DENIED)
    svc = SearchInvoicesService(port=port, codec=codec)
    ctx = make_dummy_context()

    res_page, res_src, status, reason = svc.execute(ctx, InvoiceReadFilters(), page_size=20)
    assert status == ActionStatus.FORBIDDEN
    assert reason == ActionReasonCode.ACCESS_DENIED
    assert res_page is None
    assert res_src is None
