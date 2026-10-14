"""B1 Hardening: Pydantic v2 validation, calendar boundaries, wire round-trip and safe errors."""
from datetime import date, datetime, timezone
import json
import pytest
from pydantic import ValidationError
from lotus_fin.domain.schema.invoice_read import (
    InvoiceReadFilters,
    InvoiceReadRow,
    InvoiceReadDocument,
    DocStatusFilter,
)
from lotus_fin.presentation.dto.invoice_action_request import (
    ContextDataDTO,
    ContextRequestDTO,
    SearchRequestDTO,
    OpenRequestDTO,
)
from lotus_fin.presentation.dto.invoice_action_response import (
    OpenResponseDataDTO,
)


def test_invoice_read_row_wire_string_date():
    """Verify InvoiceReadRow parses ISO date string at wire/deserialization boundary."""
    row = InvoiceReadRow(
        invoice_type="SALES",
        invoice_id="INV-001",
        posting_date="2026-10-12",
        docstatus=1,
        record_version="v1",
    )
    assert row.posting_date == date(2026, 10, 12)
    assert row.model_dump(mode="json")["posting_date"] == "2026-10-12"


def test_invoice_read_document_wire_string_date():
    """Verify InvoiceReadDocument parses ISO date string at wire boundary."""
    doc = InvoiceReadDocument(
        invoice_type="SALES",
        invoice_id="INV-001",
        company_label="Lotus Corp",
        posting_date="2026-10-12",
        docstatus=1,
        record_version="v1",
    )
    assert doc.posting_date == date(2026, 10, 12)


def test_context_data_dto_wire_string_dates():
    """Verify ContextDataDTO parses ISO date strings and datetime strings."""
    dto = ContextDataDTO(
        context_ref="ref.v1.abc.xyz",
        context_version="ctx_v1",
        company_label="Lotus Corp",
        default_posting_from="2026-07-15",
        default_posting_to="2026-10-12",
        expires_at="2026-10-12T16:28:00Z",
    )
    assert dto.default_posting_from == date(2026, 7, 15)
    assert dto.default_posting_to == date(2026, 10, 12)
    assert dto.expires_at == datetime(2026, 10, 12, 16, 28, 0, tzinfo=timezone.utc)


def test_open_response_data_dto_wire_roundtrip():
    """Verify OpenResponseDataDTO accepts dict with wire date string."""
    raw_doc = {
        "invoice_type": "SALES",
        "invoice_id": "INV-001",
        "posting_date": "2026-10-12",
        "docstatus": 1,
        "record_version": "v1",
    }
    resp = OpenResponseDataDTO(
        document=raw_doc,
        company_label="Lotus Corp",
        navigation={"kind": "LOTUS_READ_VIEW", "view": "sales-invoice-minimal-v1"},
    )
    assert resp.document["posting_date"] == date(2026, 10, 12)


@pytest.mark.parametrize("invalid_date", [
    "2025-02-29",  # Non-leap year Feb 29
    "2026-04-31",  # April 31 does not exist
    "2026-13-01",  # Month 13
    "2026-00-01",  # Month 0
    "2026-10-32",  # Day 32
    "2026/10/12",  # Non-ISO format
    "12-10-2026",  # Non-ISO format
    "20261012",    # Non-hyphenated
    "2026-1-1",    # Non-canonical padding
])
def test_calendar_and_noncanonical_date_rejections(invalid_date):
    """Verify calendar boundaries and non-canonical dates are rejected."""
    with pytest.raises(ValidationError):
        InvoiceReadFilters(posting_from=invalid_date, posting_to=invalid_date)


def test_leap_year_valid_date():
    """Verify 2024-02-29 (valid leap year) is accepted."""
    filters = InvoiceReadFilters(posting_from="2024-02-29", posting_to="2024-02-29")
    assert filters.posting_from == date(2024, 2, 29)


@pytest.mark.parametrize("unsupported_docstatus", [
    "CANCELLED", "PENDING", "ACTIVE", "DELETED", "", "null", 2, -1, 0, 1
])
def test_unsupported_docstatus_filter_rejection(unsupported_docstatus):
    """Verify only DRAFT, SUBMITTED, BOTH are valid for filter."""
    with pytest.raises(ValidationError):
        InvoiceReadFilters(docstatus=unsupported_docstatus)


@pytest.mark.parametrize("invalid_row_docstatus", [
    True, False, 2, -1, "0", "1", 0.0, 1.0, None
])
def test_invoice_read_row_docstatus_strict_integers(invalid_row_docstatus):
    """Verify row docstatus rejects booleans, floats, strings, and non-0/1 integers."""
    with pytest.raises(ValidationError):
        InvoiceReadRow(
            invoice_id="INV-01",
            posting_date=date(2026, 10, 12),
            docstatus=invalid_row_docstatus,
            record_version="v1",
        )


def test_unknown_fields_in_filters_rejected():
    """Verify extra/unknown query fields are strictly rejected by forbid."""
    with pytest.raises(ValidationError):
        InvoiceReadFilters(unknown_field="injected_param")


def test_pydantic_error_safe_representation():
    """Verify ValidationError on DTO does not leak private internal secrets."""
    with pytest.raises(ValidationError) as exc_info:
        SearchRequestDTO(
            request_id="not-a-uuid",
            context_ref="ref",
            expected_context_version="v1",
            filters={},
        )
    err_str = str(exc_info.value)
    assert "not-a-uuid" in err_str
    assert "signing_secret" not in err_str
    assert "private" not in err_str
