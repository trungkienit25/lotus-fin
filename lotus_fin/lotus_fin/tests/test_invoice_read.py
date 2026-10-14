"""Tests for P2-A Stage A Invoice Read Schema and Ports.

SSOT: CHATBOT_P2A_IMPLEMENTATION_HANDOFF.md §2, §4, §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import pytest
from datetime import date
from pydantic import ValidationError
from lotus_fin.domain.schema.invoice_read import (
    InvoiceReadFilters,
    InvoiceReadRow,
    InvoiceReadPage,
    InvoiceReadDocument,
    DocStatusFilter,
)


def test_filters_valid_defaults():
    f = InvoiceReadFilters()
    assert f.docstatus == DocStatusFilter.BOTH
    assert f.invoice_name_prefix is None
    assert f.posting_from is None
    assert f.posting_to is None


def test_filters_valid_custom():
    f = InvoiceReadFilters(
        invoice_name_prefix="INV-2026-",
        posting_from=date(2026, 1, 1),
        posting_to=date(2026, 3, 31),
        docstatus=DocStatusFilter.SUBMITTED,
    )
    assert f.invoice_name_prefix == "INV-2026-"
    assert f.docstatus == DocStatusFilter.SUBMITTED
    assert f.posting_from == date(2026, 1, 1)


def test_filters_rejects_extra_fields():
    with pytest.raises(ValidationError):
        InvoiceReadFilters(extra_field="malicious")


def test_filters_rejects_invalid_date_order():
    with pytest.raises(ValidationError, match="posting_to must not be earlier than posting_from"):
        InvoiceReadFilters(
            posting_from=date(2026, 5, 1),
            posting_to=date(2026, 4, 1),
        )


def test_filters_rejects_date_range_exceeding_365_days():
    with pytest.raises(ValidationError, match="Date range must not exceed 365 days"):
        InvoiceReadFilters(
            posting_from=date(2025, 1, 1),
            posting_to=date(2026, 1, 2),
        )


def test_filters_rejects_only_one_date_supplied():
    with pytest.raises(ValidationError, match="Both posting_from and posting_to must be provided together"):
        InvoiceReadFilters(posting_from=date(2026, 1, 1))
    with pytest.raises(ValidationError, match="Both posting_from and posting_to must be provided together"):
        InvoiceReadFilters(posting_to=date(2026, 1, 1))


def test_filters_rejects_prefix_with_control_chars_or_empty():
    with pytest.raises(ValidationError):
        InvoiceReadFilters(invoice_name_prefix="")
    with pytest.raises(ValidationError):
        InvoiceReadFilters(invoice_name_prefix="INV\x00123")
    with pytest.raises(ValidationError):
        InvoiceReadFilters(invoice_name_prefix="INV\n123")
    with pytest.raises(ValidationError):
        InvoiceReadFilters(invoice_name_prefix="A" * 129)


def test_invoice_read_row_strict_projection():
    row = InvoiceReadRow(
        invoice_id="SINV-2026-0001",
        posting_date=date(2026, 2, 1),
        docstatus=1,
        record_version="rec_abc123",
        selection_ref="ref.v2.mock_selection_ref",
    )
    assert row.invoice_type == "SALES"
    assert row.invoice_id == "SINV-2026-0001"
    assert row.selection_ref == "ref.v2.mock_selection_ref"


def test_invoice_read_row_rejects_financial_amounts():
    with pytest.raises(ValidationError):
        InvoiceReadRow(
            invoice_id="SINV-2026-0001",
            posting_date=date(2026, 2, 1),
            docstatus=1,
            record_version="rec_abc123",
            selection_ref="ref.v2.mock_selection_ref",
            grand_total=1000000,
        )


def test_invoice_read_page_strict():
    row = InvoiceReadRow(
        invoice_id="SINV-2026-0001",
        posting_date=date(2026, 2, 1),
        docstatus=1,
        record_version="rec_abc123",
        selection_ref="ref.v2.mock_selection_ref",
    )
    page = InvoiceReadPage(
        items=[row],
        returned_count=1,
        total_count=None,
        page_complete=True,
        has_more=False,
        next_cursor=None,
        selection_required=True,
    )
    assert page.total_count is None
    assert page.returned_count == 1
    assert page.page_complete is True


def test_invoice_read_document_descriptor():
    doc = InvoiceReadDocument(
        invoice_id="SINV-2026-0001",
        company_label="Lotus Corp",
        posting_date=date(2026, 2, 1),
        docstatus=1,
        record_version="rec_abc123",
        navigation={"kind": "LOTUS_READ_VIEW", "view": "sales-invoice-minimal-v1"},
    )
    assert doc.invoice_type == "SALES"
    assert doc.navigation["kind"] == "LOTUS_READ_VIEW"
