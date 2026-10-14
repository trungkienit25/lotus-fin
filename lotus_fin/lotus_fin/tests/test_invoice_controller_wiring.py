"""Tests for Controller and Application Service Wiring (Batch B4).

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §3, §4, §8.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

from types import SimpleNamespace
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import uuid
import pytest
from lotus_fin.infrastructure.config.invoice_actions_config import ApprovedConnection, InvoiceActionsConfig
from lotus_fin.infrastructure.security.frappe_invoice_authorizer import FrappeInvoiceAuthorizer
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.application.service.open_authorized_invoice import OpenAuthorizedInvoiceService
from lotus_fin.presentation.controller.invoice_actions_controller import InvoiceActionsController
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R, SourceEvidence
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters, InvoiceReadRow, InvoiceReadPage, InvoiceReadDocument


import io, logging
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents


@pytest.fixture
def wired_env(monkeypatch):
    framework = SimpleNamespace(
        session=SimpleNamespace(user="accountant@lotus.vn", sid="sid_001"),
        local=SimpleNamespace(site="site_001"),
        get_system_settings=lambda key: "Asia/Ho_Chi_Minh",
        has_permission=lambda dt, **kw: dt == "Company" and kw.get("doc") == "Lotus Corp"
    )
    import sys
    monkeypatch.setitem(sys.modules, "frappe", framework)
    conn = ApprovedConnection(
        product_id="lotus_fin", site_id="site_001", connection_id="conn_001",
        connection_version="v1", allowed_companies=["Lotus Corp"]
    )
    config = InvoiceActionsConfig(
        enabled=True, signing_key_id="key_001", signing_secret="s" * 32,
        connections={"site_001": conn}
    )
    authorizer = FrappeInvoiceAuthorizer(config)
    resolve_svc = ResolveReadContextService(authorizer)
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    log = logging.Logger("test.wiring.events", logging.INFO)
    log.addHandler(logging.StreamHandler(io.StringIO()))
    events = SafeStructuredActionEvents(log)
    return framework, config, resolve_svc, codec, events


class FakePort:
    def __init__(self):
        self.search_calls = 0
        self.open_calls = 0

    def search_invoices(self, *, context, **kwargs):
        self.search_calls += 1
        day = datetime.fromisoformat(context.observed_at_utc).astimezone(ZoneInfo(context.timezone)).date()
        row = InvoiceReadRow(invoice_id="INV-001", posting_date=day, docstatus=1, record_version="v1")
        page = InvoiceReadPage(items=[row], returned_count=1, page_complete=True, has_more=False)
        src = SourceEvidence(mode=context.adapter_mode, product_ref=context.product_id,
            site_ref=context.site_id, connection_ref=context.connection_id,
            connection_version=context.connection_version, projection_version=context.projection_version,
            observed_at=context.observed_at_utc, timezone=context.timezone, coverage="PAGE_COMPLETE")
        return page, src, S.OK, R.RESULTS_FOUND

    def open_invoice(self, *, context, doc_id, **kwargs):
        self.open_calls += 1
        day = datetime.fromisoformat(context.observed_at_utc).astimezone(ZoneInfo(context.timezone)).date()
        doc = InvoiceReadDocument(invoice_id=doc_id, company_label=context.company_id,
            posting_date=day, docstatus=1, record_version="v1")
        src = SourceEvidence(mode=context.adapter_mode, product_ref=context.product_id,
            site_ref=context.site_id, connection_ref=context.connection_id,
            connection_version=context.connection_version, projection_version=context.projection_version,
            observed_at=context.observed_at_utc, timezone=context.timezone, coverage="PAGE_COMPLETE")
        return doc, src, S.OK, R.DOCUMENT_READY


def test_controller_disabled_by_default_without_services(wired_env):
    _, config, resolve_svc, codec, events = wired_env
    ctrl = InvoiceActionsController(config, resolve_svc, codec, events_port=events)
    req_id = str(uuid.uuid4())
    _, _, body = ctrl.search_invoices({"request_id": req_id, "context_ref": "ref",
        "expected_context_version": "v1", "filters": {}})
    assert body["status"] == "NOT_AVAILABLE"
    assert body["reason_code"] == "CAPABILITY_DISABLED"


def test_controller_full_pipeline_with_injected_services(wired_env):
    _, config, resolve_svc, codec, events = wired_env
    port = FakePort()
    search_svc = SearchInvoicesService(port, codec)
    open_svc = OpenAuthorizedInvoiceService(port, codec)
    ctrl = InvoiceActionsController(config, resolve_svc, codec, events_port=events,
        search_service=search_svc, open_service=open_svc)

    # 1. get_context
    req_id1 = str(uuid.uuid4())
    code1, _, body1 = ctrl.get_context({"request_id": req_id1, "company_candidate": "Lotus Corp"})
    assert code1 == 200 and body1["status"] == "OK"
    ctx_ref = body1["data"]["context_ref"]
    ctx_ver = body1["data"]["context_version"]

    # 2. search_invoices
    req_id2 = str(uuid.uuid4())
    code2, _, body2 = ctrl.search_invoices({
        "request_id": req_id2, "context_ref": ctx_ref, "expected_context_version": ctx_ver,
        "filters": {}
    })
    assert code2 == 200 and body2["status"] == "OK"
    assert len(body2["data"]["items"]) == 1
    sel_ref = body2["data"]["items"][0]["selection_ref"]
    assert sel_ref is not None

    # 3. open_invoice
    req_id3 = str(uuid.uuid4())
    code3, _, body3 = ctrl.open_invoice({
        "request_id": req_id3, "context_ref": ctx_ref, "expected_context_version": ctx_ver,
        "selection_ref": sel_ref
    })
    assert code3 == 200 and body3["status"] == "OK"
    assert body3["data"]["document"]["invoice_id"] == "INV-001"
    assert port.search_calls == 1 and port.open_calls == 1


def test_controller_invalid_request_fails_closed(wired_env):
    _, config, resolve_svc, codec, events = wired_env
    port = FakePort()
    ctrl = InvoiceActionsController(config, resolve_svc, codec, events_port=events,
        search_service=SearchInvoicesService(port, codec),
        open_service=OpenAuthorizedInvoiceService(port, codec))
    code, _, body = ctrl.search_invoices({"invalid": "payload"})
    assert code == 422 and body["reason_code"] == "INVALID_REQUEST"
    assert port.search_calls == 0


def test_controller_tampered_context_ref_fails_closed(wired_env):
    _, config, resolve_svc, codec, events = wired_env
    port = FakePort()
    ctrl = InvoiceActionsController(config, resolve_svc, codec, events_port=events,
        search_service=SearchInvoicesService(port, codec),
        open_service=OpenAuthorizedInvoiceService(port, codec))
    code, _, body = ctrl.search_invoices({
        "request_id": str(uuid.uuid4()), "context_ref": "ref.v1.tampered.signature",
        "expected_context_version": "v1", "filters": {}
    })
    assert code in (403, 503) and port.search_calls == 0
