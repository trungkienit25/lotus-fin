"""Tests for Invoice Actions Controller & Admission Delivery (Stages B4 & B5).

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3, §7.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import uuid
import sys
from types import SimpleNamespace
import io
import logging
import pytest
from lotus_fin.application.port.i_action_events import (
    ActionEventDeliveryError,
)
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.domain.schema.action_outcome import ActionReasonCode, ActionStatus
from lotus_fin.infrastructure.config.invoice_actions_config import (
    ApprovedConnection,
    InvoiceActionsConfig,
)
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.infrastructure.security.frappe_invoice_authorizer import FrappeInvoiceAuthorizer
from lotus_fin.presentation.controller.invoice_actions_controller import InvoiceActionsController
from lotus_fin.api.invoice_actions_api import get_context, open_invoice, search_invoices


def build_controller(enabled=False, sink_failing=False):
    conn = ApprovedConnection(
        product_id="prod_1", site_id="site_1", connection_id="conn_1",
        connection_version="v1", allowed_companies=["Lotus Corp"],
    )
    cfg = InvoiceActionsConfig(
        enabled=enabled, signing_key_id="k1",
        signing_secret="super_secret_signing_key_32_bytes_long_min",
        connections={"site_1": conn},
    )
    authorizer = FrappeInvoiceAuthorizer(
        config=cfg, session_user="user1", session_id="s1", site_name="site_1"
    )
    svc = ResolveReadContextService(authorizer)
    codec = ActionReferenceCodec("k1", "super_secret_signing_key_32_bytes_long_min")

    class FailingStream(io.StringIO):
        def write(self, msg):
            raise OSError("Audit sink unavailable")

    log = logging.Logger("test.controller.required", logging.INFO)
    log.propagate = False
    log.addHandler(logging.StreamHandler(FailingStream() if sink_failing else io.StringIO()))
    events = SafeStructuredActionEvents(log)
    return InvoiceActionsController(cfg, svc, codec, events)


def test_controller_disabled_by_default_fails_closed():
    ctrl = build_controller(enabled=False)
    req_body = {"request_id": str(uuid.uuid4()), "company_candidate": "Lotus Corp"}
    status_code, headers, body = ctrl.get_context(req_body)

    assert status_code == 503
    assert body["status"] == "NOT_AVAILABLE"
    assert body["reason_code"] == "CAPABILITY_DISABLED"
    assert body["data"] is None


def test_controller_invalid_request_dto_fails_closed():
    ctrl = build_controller(enabled=True)
    req_body = {"request_id": "not-a-valid-uuid", "company_candidate": "Lotus Corp"}
    status_code, headers, body = ctrl.get_context(req_body)

    assert status_code == 422
    assert body["status"] == "NOT_AVAILABLE"
    assert body["reason_code"] == "INVALID_REQUEST"


def test_controller_enabled_successful_context(monkeypatch):
    monkeypatch.setitem(sys.modules, "frappe", SimpleNamespace(get_system_settings=lambda key: "Asia/Ho_Chi_Minh", has_permission=lambda dt, **kw:
        (dt, kw) == ("Company", dict(ptype="read", doc="Lotus Corp", user="user1"))))
    ctrl = build_controller(enabled=True)
    cid = str(uuid.uuid4())
    req_id = str(uuid.uuid4())
    req_body = {"request_id": req_id, "company_candidate": "Lotus Corp"}
    status_code, headers, body = ctrl.get_context(req_body, correlation_id=cid)

    assert status_code == 200
    assert body["status"] == "OK"
    assert body["reason_code"] == "CONTEXT_READY"
    assert body["data"]["context_ref"].startswith("ref.v1.")
    assert headers["X-Correlation-ID"] == cid == body["correlation_id"]


def test_controller_search_and_open_strictly_disabled():
    ctrl = build_controller(enabled=True)
    status_code, _, body = ctrl.search_invoices({"request_id": str(uuid.uuid4())})
    assert status_code == 503 and body["reason_code"] == "CAPABILITY_DISABLED"

    status_code, _, body = ctrl.open_invoice({"request_id": str(uuid.uuid4())})
    assert status_code == 503 and body["reason_code"] == "CAPABILITY_DISABLED"


def test_audit_sink_failure_prevents_unobserved_admission():
    ctrl = build_controller(enabled=False, sink_failing=True)
    req_body = {"request_id": str(uuid.uuid4()), "company_candidate": "Lotus Corp"}
    with pytest.raises(ActionEventDeliveryError):
        ctrl.get_context(req_body)


def test_frappe_api_handlers_fail_closed():
    for fn, cap in [(get_context, "invoice.context"), (search_invoices, "invoice.search"), (open_invoice, "invoice.open")]:
        res = fn()
        assert "message" in res
        msg = res["message"]
        assert msg["status"] == "NOT_AVAILABLE"
        assert msg["reason_code"] == "CAPABILITY_DISABLED"
        assert msg["capability"] == cap
