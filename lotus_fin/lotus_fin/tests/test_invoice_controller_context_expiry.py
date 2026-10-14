"""Context admission failures must return the frozen reason, never an enum error."""

import uuid
import pytest
from lotus_fin.tests.test_invoice_controller_wiring import wired_env, FakePort
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.presentation.controller.invoice_actions_controller import InvoiceActionsController


@pytest.mark.parametrize("capability", ["search", "open"])
@pytest.mark.parametrize("fault", ["expired", "changed_version"])
def test_context_fault_returns_safe_contract_without_read(wired_env, monkeypatch, capability, fault):
    _, config, resolver, codec, events = wired_env
    port = FakePort()
    controller = InvoiceActionsController(config, resolver, codec, events_port=events,
        search_service=SearchInvoicesService(port, codec), open_service=OpenAuthorizedInvoiceService(port, codec))
    now = [1900000000]
    monkeypatch.setattr("lotus_fin.infrastructure.security.action_reference_codec.time.time", lambda: now[0])
    code, _, ready = controller.get_context({"request_id": str(uuid.uuid4()), "company_candidate": "Lotus Corp"})
    assert code == 200
    request_id = str(uuid.uuid4())
    body = {"request_id": request_id, "context_ref": ready["data"]["context_ref"],
            "expected_context_version": ready["data"]["context_version"]}
    if fault == "expired":
        now[0] += config.reference_ttl_seconds + 1  # Preserve P1 historical equality semantics.
    else:
        body["expected_context_version"] = "different-version"
    if capability == "search":
        response = controller.search_invoices({**body, "filters": {}})
    else:
        response = controller.open_invoice({**body, "selection_ref": "never-read-before-scope-check"})
    status, headers, failure = response
    assert status == 409
    assert failure["reason_code"] == "CONTEXT_CHANGED"
    assert failure["status"] == "NOT_AVAILABLE"
    assert failure["data"] is None and failure["source"] is None
    assert failure["request_id"] == request_id
    assert failure["correlation_id"] == headers["X-Correlation-ID"]
    assert port.search_calls == port.open_calls == 0
