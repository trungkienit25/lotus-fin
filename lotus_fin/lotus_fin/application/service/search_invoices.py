"""Bounded typed search boundary; actual permission enforcement belongs to read port."""
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from lotus_fin.application.port.i_invoice_references import IInvoiceReferences
from lotus_fin.application.port.i_authorized_invoice_read import IAuthorizedInvoiceReadPort
from lotus_fin.application.service.invoice_read_validation import failure, terminal, validate_source, exception_result, response_bytes
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R, scan_for_nested_denial
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters, InvoiceReadPage
from lotus_fin.domain.model.invoice_read_budget import InvoiceReadBudget


class SearchInvoicesService:
    def __init__(self, port: IAuthorizedInvoiceReadPort, codec: IInvoiceReferences):
        self._port, self._codec = port, codec

    def execute(self, context, filters: InvoiceReadFilters, page_size: int, cursor: Optional[str] = None):
        if type(page_size) is not int or not 1 <= page_size <= 50 or type(filters) is not InvoiceReadFilters:
            return failure(S.NOT_AVAILABLE, R.INVALID_REQUEST)
        if context.capability != "invoice.search":
            return failure(S.FORBIDDEN, R.CAPABILITY_DENIED)
        try:
            today = datetime.fromisoformat(context.observed_at_utc).astimezone(ZoneInfo(context.timezone)).date()
            filters = InvoiceReadFilters(**filters.model_dump()).normalized(today)
            digest = filters.fingerprint(page_size)
        except (ValueError, TypeError):
            return failure(S.NOT_AVAILABLE, R.INVALID_REQUEST)
        cursor_claims = None
        if cursor is not None:
            valid, cursor_claims, error = self._codec.verify_cursor_v2(cursor, context)
            if not valid:
                return failure(S.NOT_AVAILABLE, R.STALE_CURSOR) if error == "Reference expired." else failure(S.FORBIDDEN, R.ACCESS_DENIED)
            if cursor_claims.query_fingerprint != digest or cursor_claims.page_size != page_size:
                return failure(S.NOT_AVAILABLE, R.STALE_CURSOR)
        try:
            budget = InvoiceReadBudget(context.deadline_at_utc)
            budget.limits["detail_reads"] = 0
            page, source, status, reason = self._port.search_invoices(
                context=context, filters=filters, page_size=page_size, cursor=cursor, budget=budget)
            denied = terminal(status, reason)
            if denied is not None:
                return denied
            if status == S.OK and reason not in (R.RESULTS_FOUND, R.EMPTY_RESULT):
                return failure()
            if page is not None and scan_for_nested_denial(page.model_dump(mode="json")):
                return failure(S.FORBIDDEN, R.ACCESS_DENIED)
            source = validate_source(source, context)
            if type(page) is not InvoiceReadPage:
                return failure()
            page = InvoiceReadPage(**page.model_dump())
            if len(page.items) > page_size:
                return failure()
            for row in page.items:
                if not filters.posting_from <= row.posting_date <= filters.posting_to:
                    return failure()
                if filters.invoice_name_prefix and not row.invoice_id.startswith(filters.invoice_name_prefix):
                    return failure()
                if filters.docstatus.value != "BOTH" and row.docstatus != (0 if filters.docstatus.value == "DRAFT" else 1):
                    return failure()
            partial = status == S.PARTIAL or not page.page_complete or source.coverage == "INCOMPLETE"
            next_claims = None
            if page.next_cursor is not None and not partial:
                valid, next_claims, _ = self._codec.verify_cursor_v2(page.next_cursor, context)
                expected_index = cursor_claims.page_index + 1 if cursor_claims else 2
                if (not valid or next_claims.query_fingerprint != digest or next_claims.page_size != page_size
                        or next_claims.page_index != expected_index):
                    return failure()
                if cursor_claims and next_claims.upper_id != cursor_claims.upper_id:
                    return failure()
                if not page.items or next_claims.last_id != page.items[-1].invoice_id:
                    return failure()
            if page.has_more is True and not partial:
                partial = bool(cursor_claims and cursor_claims.page_index == 5)
                if not partial and next_claims is None:
                    return failure()
            if not partial and (page.has_more is None or (not page.has_more and page.next_cursor is not None)):
                return failure()
            rows = [row.model_copy(update={"selection_ref": None if partial else self._codec.sign_selection_v2(
                context, row.invoice_id, row.record_version, query_fingerprint=digest)}) for row in page.items]
            result = InvoiceReadPage(items=rows, returned_count=len(rows), page_complete=not partial,
                has_more=None if partial else page.has_more, next_cursor=None if partial else page.next_cursor,
                selection_required=bool(rows), limitations=["COVERAGE_INCOMPLETE"] if partial else (page.limitations or []))
            source = source.model_copy(update={"coverage": "INCOMPLETE" if partial else "PAGE_COMPLETE"})
            final_status, final_reason = (S.PARTIAL, R.COVERAGE_INCOMPLETE) if partial else (S.OK, R.RESULTS_FOUND if rows else R.EMPTY_RESULT)
            budget.consume("response_bytes", response_bytes(context, result.model_dump(mode="json"), source, final_status, final_reason))
            budget.check()
            return result, source, final_status, final_reason
        except Exception as exc:
            return exception_result(exc)
