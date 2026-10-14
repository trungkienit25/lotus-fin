"""Offline resource/late-return checks; no claim of hard DB/audit cancellation."""
from datetime import datetime, timedelta, timezone
import pytest
from lotus_fin.domain.model.invoice_read_budget import InvoiceReadBudget, ReadBudgetExceeded
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.tests.test_invoice_read_security import fixture


@pytest.mark.parametrize("axis,limit", [("list_calls", 2), ("document_checks", 51), ("metadata_calls", 10),
    ("scan_rows", 100), ("provider_bytes", 256 * 1024), ("response_bytes", 64 * 1024), ("detail_reads", 1)])
def test_exact_limit_and_reject_before_extra(axis, limit):
    b = InvoiceReadBudget((datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat())
    b.consume(axis, limit)
    with pytest.raises(ReadBudgetExceeded): b.consume(axis)
    assert b.counters[axis] == limit


@pytest.mark.parametrize("amount", [-1, True, 1.5, "1"])
def test_invalid_count_never_bypasses_limit(amount):
    b = InvoiceReadBudget((datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat())
    with pytest.raises(ValueError): b.consume("list_calls", amount)
    assert b.counters == {}


def test_monotonic_deadline_equality():
    ticks = [0]
    b = InvoiceReadBudget((datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(), clock=lambda: ticks[0])
    ticks[0] = 5
    with pytest.raises(ReadBudgetExceeded, match="budget"): b.check()


@pytest.mark.parametrize("operation,axis", [("search", "list_calls"), ("search", "document_checks"),
    ("search", "scan_rows"), ("search", "provider_bytes"), ("search", "detail_reads"),
    ("open", "list_calls"), ("open", "document_checks"), ("open", "detail_reads")])
def test_port_must_stop_at_budget(fixture, operation, axis):
    ctx, src, _, page, doc, _, codec = fixture
    writes = []
    class Port:
        def search_invoices(self, **kwargs):
            b = kwargs["budget"]
            b.consume(axis, b.limits[axis] + 1)
            writes.append("must not execute excess I/O")
            return page, src, S.OK, R.RESULTS_FOUND
        def open_invoice(self, **kwargs): return self.search_invoices(**kwargs)
    if operation == "search": result = SearchInvoicesService(Port(), codec).execute(ctx, InvoiceReadFilters(), 20)
    else:
        ctx = ctx.model_copy(update={"capability": "invoice.open"})
        result = OpenAuthorizedInvoiceService(Port(), codec).execute(ctx, codec.sign_selection_v2(ctx, "INV-A", "rev1"))
    assert result == (None, None, S.SOURCE_ERROR, R.INVALID_PROVIDER_RESPONSE)
    assert writes == []


def test_late_port_success_is_not_delivered(fixture):
    ctx, src, _, page, _, _, codec = fixture
    class Port:
        def search_invoices(self, **kwargs):
            b = kwargs["budget"]
            b.started -= 10
            return page, src, S.OK, R.RESULTS_FOUND
    result = SearchInvoicesService(Port(), codec).execute(ctx, InvoiceReadFilters(), 20)
    assert result == (None, None, S.TIMEOUT, R.DEADLINE_EXCEEDED)


def test_each_open_rechecks_permission_and_deny_beats_stale(fixture):
    ctx, src, _, _, doc, _, codec = fixture
    ctx = ctx.model_copy(update={"capability": "invoice.open"})
    class Port:
        calls = 0
        denied = False
        def open_invoice(self, **kwargs):
            self.calls += 1
            kwargs["budget"].consume("document_checks")
            if self.denied: return doc, src, S.FORBIDDEN, R.ACCESS_DENIED
            return doc, src, S.OK, R.DOCUMENT_READY
    port = Port()
    service = OpenAuthorizedInvoiceService(port, codec)
    token = codec.sign_selection_v2(ctx, "INV-A", "rev1")
    assert service.execute(ctx, token)[2] == S.OK
    port.denied = True
    assert service.execute(ctx, token) == (None, None, S.FORBIDDEN, R.ACCESS_DENIED)
    assert port.calls == 2


def test_stale_record_with_current_grant(fixture):
    ctx, src, _, _, doc, port, codec = fixture
    ctx = ctx.model_copy(update={"capability": "invoice.open"})
    port.result = doc.model_copy(update={"record_version": "rev2"}), src, S.OK, R.DOCUMENT_READY
    assert OpenAuthorizedInvoiceService(port, codec).execute(ctx, codec.sign_selection_v2(ctx, "INV-A", "rev1")) == (None, None, S.NOT_AVAILABLE, R.STALE_SELECTION)


def test_page_limit_empty_complete_and_no_automatic_selection(fixture):
    ctx, src, _, page, _, port, codec = fixture
    port.result = page.model_copy(update={"items": [], "returned_count": 0}), src, S.OK, R.EMPTY_RESULT
    result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20)
    assert result[2:] == (S.OK, R.EMPTY_RESULT) and result[0].selection_required is False


def test_denial_reason_wins_outer_success(fixture):
    ctx, src, _, page, _, port, codec = fixture
    port.result = page, src, S.OK, R.ACCESS_DENIED
    assert SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20) == (None, None, S.FORBIDDEN, R.ACCESS_DENIED)


def test_response_budget_counts_full_envelope(fixture):
    ctx, src, _, page, _, _, codec = fixture
    from lotus_fin.domain.schema.action_outcome import ActionOutcome
    captured = []
    class Port:
        def search_invoices(self, **kwargs):
            captured.append(kwargs["budget"])
            return page, src, S.OK, R.RESULTS_FOUND
    data, source, status, reason = SearchInvoicesService(Port(), codec).execute(ctx, InvoiceReadFilters(), 20)
    value = ActionOutcome(status=status, reason_code=reason, capability=ctx.capability,
        correlation_id=ctx.correlation_id, request_id=ctx.request_id,
        context_version=ctx.context_version, source=source, data=data.model_dump(mode="json"), user_message="safe")
    assert captured[0].counters["response_bytes"] >= len(value.model_dump_json().encode())
