"""Verify selected identity; fresh document/field authorization belongs to read port."""
from lotus_fin.application.port.i_invoice_references import IInvoiceReferences
from lotus_fin.application.port.i_authorized_invoice_read import IAuthorizedInvoiceReadPort
from lotus_fin.application.service.invoice_read_validation import failure, terminal, validate_source, exception_result, response_bytes
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R, scan_for_nested_denial
from lotus_fin.domain.schema.invoice_read import InvoiceReadDocument
from lotus_fin.domain.model.invoice_read_budget import InvoiceReadBudget


class OpenAuthorizedInvoiceService:
    def __init__(self, port: IAuthorizedInvoiceReadPort, codec: IInvoiceReferences):
        self._port, self._codec = port, codec

    def execute(self, context, selection_ref: str):
        if context.capability != "invoice.open":
            return failure(S.FORBIDDEN, R.CAPABILITY_DENIED)
        valid, claims, error = self._codec.verify_selection_v2(selection_ref, context)
        if not valid or claims is None:
            return failure(S.NOT_AVAILABLE, R.STALE_SELECTION) if error == "Reference expired." else failure(S.FORBIDDEN, R.ACCESS_DENIED)
        try:
            budget = InvoiceReadBudget(context.deadline_at_utc)
            budget.limits.update(list_calls=0, document_checks=1)
            doc, source, status, reason = self._port.open_invoice(context=context, doc_id=claims.doc_id,
                expected_record_version=claims.record_version, budget=budget)
            denied = terminal(status, reason)
            if denied is not None:
                return denied
            if doc is not None and scan_for_nested_denial(doc.model_dump(mode="json")):
                return failure(S.FORBIDDEN, R.ACCESS_DENIED)
            if status != S.OK or reason != R.DOCUMENT_READY or type(doc) is not InvoiceReadDocument:
                return failure()
            source = validate_source(source, context)
            if source.coverage != "PAGE_COMPLETE":
                return failure()
            doc = InvoiceReadDocument(**doc.model_dump())
            if doc.invoice_id != claims.doc_id or doc.company_label != context.company_id:
                return failure()
            if doc.record_version != claims.record_version:
                return failure(S.NOT_AVAILABLE, R.STALE_SELECTION)
            data = {"document": doc.model_dump(mode="json", exclude={"company_label", "navigation"}),
                "company_label": doc.company_label, "navigation": doc.navigation}
            budget.consume("response_bytes", response_bytes(context, data, source, status, reason))
            budget.check()
            return doc, source, status, reason
        except Exception as exc:
            return exception_result(exc)
