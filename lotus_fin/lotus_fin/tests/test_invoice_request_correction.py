"""F03: omission versus null at typed request boundary; zero read on invalid input."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import pytest
from pydantic import ValidationError
from lotus_fin.tests.test_invoice_read_family_correction import family, resolve, ReadPort, RID
from lotus_fin.presentation.dto.invoice_action_request import SearchRequestDTO
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.application.service.search_invoices import SearchInvoicesService

BASE = dict(request_id=RID, context_ref="ref", expected_context_version="ctx", filters={})


def execute_request(raw, ctx, port, codec):
    try:
        request = SearchRequestDTO(**raw)
    except ValidationError:
        return None, None, S.NOT_AVAILABLE, R.INVALID_REQUEST
    return SearchInvoicesService(port, codec).execute(ctx, request.filters, request.page_size, request.cursor)


@pytest.mark.parametrize("patch", [
    {"filters": None}, {"page_size": None}, {"filters": {"posting_from": None}},
    {"filters": {"posting_to": None}}, {"filters": {"posting_from": None, "posting_to": None}},
])
def test_known_explicit_null_schema_negatives(patch):
    with pytest.raises(ValidationError):
        SearchRequestDTO(**{**BASE, **patch})


def test_required_filters_missing():
    with pytest.raises(ValidationError):
        SearchRequestDTO(**{k: v for k, v in BASE.items() if k != "filters"})


@pytest.mark.parametrize("raw", [
    {k: v for k, v in BASE.items() if k != "filters"},
    {**BASE, "filters": None}, {**BASE, "page_size": None},
    *[{**BASE, "filters": dates} for dates in (
        {"posting_from": None}, {"posting_to": None}, {"posting_from": None, "posting_to": None})],
])
def test_invalid_request_boundary_calls_port_zero_times(family, raw):
    _, config, _ = family
    ctx = resolve(config, "invoice.search")
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    port = ReadPort()
    assert execute_request(raw, ctx, port, codec) == (None, None, S.NOT_AVAILABLE, R.INVALID_REQUEST)
    assert port.search_calls == port.open_calls == 0


def test_unvalidated_explicit_null_cannot_reach_port(family):
    _, config, _ = family
    port = ReadPort()
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    filters = InvoiceReadFilters.model_construct(posting_from=None)
    result = SearchInvoicesService(port, codec).execute(resolve(config, "invoice.search"), filters, 20)
    assert result == (None, None, S.NOT_AVAILABLE, R.INVALID_REQUEST)
    assert port.search_calls == 0


@pytest.mark.parametrize("page_size", [None, 1, 20, 50])
def test_valid_empty_filters_omitted_or_supplied_page_size(family, page_size):
    _, config, _ = family
    ctx = resolve(config, "invoice.search")
    raw = {**BASE}
    if page_size is not None:
        raw["page_size"] = page_size
    request = SearchRequestDTO(**raw)
    assert request.page_size == (20 if page_size is None else page_size)
    assert request.filters.model_fields_set == set()
    port = ReadPort()
    result = execute_request(raw, ctx, port, ActionReferenceCodec(config.signing_key_id, config.signing_secret))
    assert result[2:] == (S.OK, R.RESULTS_FOUND) and port.search_calls == 1


def test_valid_supplied_dates_and_nfc_prefix(family):
    _, config, _ = family
    ctx = resolve(config, "invoice.search")
    today = datetime.fromisoformat(ctx.observed_at_utc).astimezone(ZoneInfo(ctx.timezone)).date()
    req = SearchRequestDTO(**{**BASE, "page_size": 10,
        "filters": {"posting_from": (today - timedelta(days=1)).isoformat(), "posting_to": today.isoformat(), "docstatus": "SUBMITTED"}})
    port = ReadPort()
    result = SearchInvoicesService(port, ActionReferenceCodec(config.signing_key_id, config.signing_secret)).execute(ctx, req.filters, req.page_size)
    assert result[2:] == (S.OK, R.RESULTS_FOUND) and port.search_calls == 1
    assert InvoiceReadFilters(invoice_name_prefix="e\u0301").invoice_name_prefix == "é"


@pytest.mark.parametrize("patch", [
    {"filters": []}, {"filters": "{}"}, {"page_size": True}, {"page_size": "20"},
    {"page_size": 20.0}, {"page_size": 0}, {"page_size": 51}, {"company_id": "B"},
    {"method": "run_method"}, {"filters": {"fields": ["*"]}},
    {"filters": {"posting_from": True, "posting_to": False}},
    {"filters": {"posting_from": "20261001", "posting_to": "2026-10-02"}},
    {"filters": {"posting_from": "2026-10-01"}},
    {"filters": {"posting_from": "2026-10-02", "posting_to": "2026-10-01"}},
    {"filters": {"posting_from": "2025-01-01", "posting_to": "2026-01-01"}},
    {"filters": {"invoice_name_prefix": "\x00"}},
])
def test_wrong_types_extra_scope_rpc_and_ranges_remain_rejected(patch):
    with pytest.raises(ValidationError):
        SearchRequestDTO(**{**BASE, **patch})


def test_future_date_still_invalid_before_port(family):
    _, config, _ = family
    ctx = resolve(config, "invoice.search")
    tomorrow = datetime.fromisoformat(ctx.observed_at_utc).astimezone(ZoneInfo(ctx.timezone)).date() + timedelta(days=1)
    port = ReadPort()
    result = execute_request({**BASE, "filters": {"posting_from": tomorrow.isoformat(), "posting_to": tomorrow.isoformat()}},
        ctx, port, ActionReferenceCodec(config.signing_key_id, config.signing_secret))
    assert result == (None, None, S.NOT_AVAILABLE, R.INVALID_REQUEST) and port.search_calls == 0
