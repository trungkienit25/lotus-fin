"""Adversarial offline oracle: independent synthetic values, no ERP fixture."""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import pytest
from pydantic import ValidationError
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R, SourceEvidence
from lotus_fin.domain.schema.invoice_read import InvoiceReadRow, InvoiceReadPage, InvoiceReadDocument, InvoiceReadFilters
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec


@pytest.fixture
def fixture():
    now = datetime.now(timezone.utc)
    ctx = AuthorizedReadContext(actor_id="synthetic", auth_session_binding="private-session",
        site_id="site", product_id="product", connection_id="connection", connection_version="v1",
        company_id="Company A", capability="invoice.search", context_version="context-v1",
        observed_at_utc=now.isoformat(), timezone="Asia/Ho_Chi_Minh",
        deadline_at_utc=(now + timedelta(seconds=5)).isoformat(),
        correlation_id="c0000000-0000-4000-8000-000000000001",
        request_id="a0000000-0000-4000-8000-000000000001", adapter_mode="ERP_READ")
    src = SourceEvidence(mode="ERP_READ", product_ref="product", site_ref="site",
        connection_ref="connection", connection_version="v1", projection_version="invoice.min.v1",
        observed_at=now.isoformat(), timezone=ctx.timezone, coverage="PAGE_COMPLETE")
    row = InvoiceReadRow(invoice_id="INV-A", posting_date=date.today(), docstatus=1, record_version="rev1")
    page = InvoiceReadPage(items=[row], returned_count=1, page_complete=True, has_more=False)
    doc = InvoiceReadDocument(invoice_id=row.invoice_id, company_label=ctx.company_id,
        posting_date=row.posting_date, docstatus=1, record_version=row.record_version)
    class Port:
        calls = 0
        error = None
        def search_invoices(self, **kwargs):
            self.calls += 1
            if self.error:
                raise self.error
            return self.result
        def open_invoice(self, **kwargs):
            return self.search_invoices(**kwargs)
    port = Port()
    codec = ActionReferenceCodec("synthetic-key", "s" * 32)
    return ctx, src, row, page, doc, port, codec


@pytest.mark.parametrize("kind", ["missing-source", "foreign-source", "missing-page", "oversized",
    "wrong-count", "duplicate", "wrong-row-filter", "invalid-reason", "prefilled-denial"])
def test_search_rejects_invalid_provider(fixture, kind):
    ctx, src, row, page, _, port, codec = fixture
    reason = R.RESULTS_FOUND
    if kind == "missing-source": src = None
    if kind == "foreign-source": src = src.model_copy(update={"site_ref": "other-site"})
    if kind == "missing-page": page = None
    if kind == "oversized": page = page.model_copy(update={"items": [row] * 21, "returned_count": 21})
    if kind == "wrong-count": page = page.model_copy(update={"returned_count": 5})
    if kind == "duplicate": page = page.model_copy(update={"items": [row, row], "returned_count": 2})
    if kind == "wrong-row-filter": row = row.model_copy(update={"docstatus": 2}); page = page.model_copy(update={"items": [row]})
    if kind == "invalid-reason": reason = R.DOCUMENT_READY
    if kind == "prefilled-denial": page = page.model_copy(update={"limitations": ["ACCESS_DENIED"]})
    port.result = page, src, S.OK, reason
    result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20)
    assert result[0] is None and result[1] is None
    assert result[2] in (S.SOURCE_ERROR, S.FORBIDDEN)


def test_incomplete_ok_becomes_nonactionable_partial(fixture):
    ctx, src, _, page, _, port, codec = fixture
    port.result = page.model_copy(update={"page_complete": False}), src, S.OK, R.RESULTS_FOUND
    data, source, status, reason = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20)
    assert (status, reason) == (S.PARTIAL, R.COVERAGE_INCOMPLETE)
    assert source.coverage == "INCOMPLETE" and not data.page_complete
    assert data.items[0].selection_ref is None and data.next_cursor is None and data.has_more is None


@pytest.mark.parametrize("kind", ["wrong-id", "wrong-company", "missing-source", "foreign-source", "navigation", "partial-source"])
def test_open_rejects_wrong_observation(fixture, kind):
    ctx, src, _, _, doc, port, codec = fixture
    ctx = ctx.model_copy(update={"capability": "invoice.open"})
    token = codec.sign_selection_v2(ctx, "INV-A", "rev1")
    if kind == "wrong-id": doc = doc.model_copy(update={"invoice_id": "INV-B"})
    if kind == "wrong-company": doc = doc.model_copy(update={"company_label": "Company B"})
    if kind == "missing-source": src = None
    if kind == "foreign-source": src = src.model_copy(update={"product_ref": "foreign"})
    if kind == "navigation": doc = doc.model_copy(update={"navigation": {"kind": "EDIT", "view": "native"}})
    if kind == "partial-source": src = src.model_copy(update={"coverage": "INCOMPLETE"})
    port.result = doc, src, S.OK, R.DOCUMENT_READY
    result = OpenAuthorizedInvoiceService(port, codec).execute(ctx, token)
    assert result == (None, None, S.SOURCE_ERROR, R.INVALID_PROVIDER_RESPONSE)


@pytest.mark.parametrize("exception,expected", [(TimeoutError("private"), S.TIMEOUT), (RuntimeError("private"), S.SOURCE_ERROR)])
@pytest.mark.parametrize("operation", ["search", "open"])
def test_safe_port_exception(fixture, exception, expected, operation):
    ctx, _, _, _, _, port, codec = fixture
    port.error = exception
    if operation == "search": result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20)
    else:
        ctx = ctx.model_copy(update={"capability": "invoice.open"})
        result = OpenAuthorizedInvoiceService(port, codec).execute(ctx, codec.sign_selection_v2(ctx, "INV-A", "rev1"))
    assert result[0] is None and result[1] is None and result[2] == expected


@pytest.mark.parametrize("status,reason", [(S.FORBIDDEN, R.ACCESS_DENIED), (S.TIMEOUT, R.DEADLINE_EXCEEDED), (S.SOURCE_ERROR, R.SOURCE_FAILURE)])
def test_open_terminal_drops_source(fixture, status, reason):
    ctx, src, _, _, doc, port, codec = fixture
    ctx = ctx.model_copy(update={"capability": "invoice.open"})
    port.result = doc, src, status, reason
    assert OpenAuthorizedInvoiceService(port, codec).execute(ctx, codec.sign_selection_v2(ctx, "INV-A", "rev1")) == (None, None, status, reason)


@pytest.mark.parametrize("bad", [True, 1.5, "20", 0, 51])
def test_search_strict_size_before_port(fixture, bad):
    ctx, src, _, page, _, port, codec = fixture
    port.result = page, src, S.OK, R.RESULTS_FOUND
    result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), bad)
    assert result == (None, None, S.NOT_AVAILABLE, R.INVALID_REQUEST) and port.calls == 0


def test_no_forged_cursor_forwarding(fixture):
    ctx, src, _, page, _, port, codec = fixture
    port.result = page, src, S.OK, R.RESULTS_FOUND
    result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20, "ref.v2.fake.fake")
    assert result == (None, None, S.FORBIDDEN, R.ACCESS_DENIED) and port.calls == 0


def test_expired_context_does_not_read(fixture):
    ctx, src, _, page, _, port, codec = fixture
    ctx = ctx.model_copy(update={"deadline_at_utc": "2000-01-01T00:00:00+00:00"})
    port.result = page, src, S.OK, R.RESULTS_FOUND
    assert SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20) == (None, None, S.TIMEOUT, R.DEADLINE_EXCEEDED)
    assert port.calls == 0


def test_selection_contains_normalized_query_contract(fixture):
    ctx, src, _, page, _, port, codec = fixture
    port.result = page, src, S.OK, R.RESULTS_FOUND
    result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20)
    valid, claims, _ = codec.verify_selection_v2(result[0].items[0].selection_ref, ctx)
    assert valid and claims.contract_version == "p1.invoice.v1" and len(claims.query_fingerprint) == 64


def test_filters_accept_strict_json_dates_and_nfc():
    f = InvoiceReadFilters.model_validate({"posting_from": "2026-01-01", "posting_to": "2026-01-02", "docstatus": "SUBMITTED", "invoice_name_prefix": "e\u0301"})
    assert f.posting_from == date(2026, 1, 1) and f.invoice_name_prefix == "é"


def test_bool_docstatus_is_not_integer(fixture):
    _, _, row, *_ = fixture
    with pytest.raises(ValidationError): InvoiceReadRow(**{**row.model_dump(), "docstatus": True})
