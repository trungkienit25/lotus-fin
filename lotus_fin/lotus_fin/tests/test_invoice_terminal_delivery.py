"""F02/F03: actual controller terminal audit/CID/echo, no ERP business access."""

import io
import json
import logging
import sys
import types
import uuid
import pytest
from lotus_fin.application.port.i_action_events import ActionEventDeliveryError
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.infrastructure.config.invoice_actions_config import ApprovedConnection, InvoiceActionsConfig
from lotus_fin.infrastructure.security.frappe_invoice_authorizer import FrappeInvoiceAuthorizer
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents
from lotus_fin.presentation.controller.invoice_actions_controller import InvoiceActionsController

PATHS = ["invalid", "search", "open", "guest", "denied", "allowed", "disabled"]


@pytest.fixture
def factory(monkeypatch):
    owned = []
    def build(path="allowed", broken=False, missing=False):
        reads = []
        f = types.ModuleType("frappe")
        f.session = types.SimpleNamespace(user="Guest" if path == "guest" else "actor@example.invalid", sid="PRIVATE_SID")
        f.local = types.SimpleNamespace(site="site")
        f.has_permission = lambda dt, **kw: path != "denied" and (dt, kw) == (
            "Company", dict(ptype="read", doc="Company A", user="actor@example.invalid"))
        def forbidden(*a, **kw):
            reads.append(True)
            raise AssertionError("Invoice business access must not occur")
        f.get_doc = f.get_list = f.get_all = forbidden
        monkeypatch.setitem(sys.modules, "frappe", f)
        conn = ApprovedConnection(product_id="prod", site_id="site", connection_id="conn",
                                  connection_version="v1", allowed_companies=["Company A"])
        cfg = InvoiceActionsConfig(enabled=path != "disabled", signing_key_id="test-key",
            signing_secret="synthetic-key-material-" * 2, connections={"site": conn})
        class Stream(io.StringIO):
            def write(self, message):
                if broken:
                    raise OSError("PRIVATE_SINK_CANARY")
                return super().write(message)
        class CountingSink(SafeStructuredActionEvents):
            def __init__(self, log):
                super().__init__(log)
                self.attempts = []
            def record_event(self, event):
                self.attempts.append(event.model_dump(mode="json"))
                super().record_event(event)
        stream = Stream()
        handler = logging.StreamHandler(stream)
        log = logging.Logger("test.terminal.private", logging.INFO)
        log.propagate = False
        log.addHandler(handler)
        owned.append((log, handler))
        sink = CountingSink(log)
        ctrl = InvoiceActionsController(cfg, ResolveReadContextService(FrappeInvoiceAuthorizer(cfg)),
            ActionReferenceCodec("test-key", cfg.signing_secret), None if missing else sink)
        return ctrl, sink, stream, reads
    yield build
    for log, handler in owned:
        log.removeHandler(handler)
        handler.close()


def call(ctrl, path, request_id, cid=None):
    body = {"company_candidate": "Company A"}
    if request_id is not None:
        body["request_id"] = request_id
    if path == "invalid":
        body["private_payload"] = "PRIVATE_REQUEST_CANARY"
    fn = ctrl.search_invoices if path == "search" else ctrl.open_invoice if path == "open" else ctrl.get_context
    return fn(body, correlation_id=cid)


@pytest.mark.parametrize("path", PATHS)
def test_valid_request_id_terminal_event_and_server_cid(factory, path):
    ctrl, sink, stream, reads = factory(path)
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    http, headers, body = call(ctrl, path, rid, cid)
    expected = dict(invalid=(422, "INVALID_REQUEST"), search=(503, "CAPABILITY_DISABLED"),
        open=(503, "CAPABILITY_DISABLED"), guest=(401, "AUTH_REQUIRED"), denied=(403, "COMPANY_DENIED"),
        allowed=(200, "CONTEXT_READY"), disabled=(503, "CAPABILITY_DISABLED"))[path]
    assert (http, body["reason_code"]) == expected
    assert len(sink.recorded_events) == len(sink.attempts) == 1
    assert body["request_id"] == rid and body["correlation_id"] == cid
    assert uuid.UUID(body["correlation_id"]).version == 4
    assert headers["X-Correlation-ID"] == body["correlation_id"]
    event = sink.recorded_events[0]
    assert event["stage"] == "RESPONSE_DELIVERY"
    assert (event["status"], event["reason_code"]) == (body["status"], body["reason_code"])
    assert (event["correlation_id"], event["request_id"]) == (body["correlation_id"], rid)
    assert [json.loads(line) for line in stream.getvalue().splitlines()] == sink.recorded_events
    for private in ["PRIVATE_REQUEST_CANARY", "UNTRUSTED_CID_CANARY", "PRIVATE_SID",
                    "actor@example.invalid", "ref.v1.", "synthetic-key-material-"]:
        assert private not in stream.getvalue()
    assert not reads
    if path != "allowed":
        assert body["data"] is None and body["source"] is None


@pytest.mark.parametrize("path", ["invalid", "search", "open"])
@pytest.mark.parametrize("rid", [None, "PRIVATE_REQUEST_CANARY", 7])
def test_invalid_missing_ids_replaced_without_logging_raw_values(factory, path, rid):
    ctrl, sink, stream, reads = factory(path)
    http, headers, body = call(ctrl, path, rid)
    assert http == 422 and body["reason_code"] == "INVALID_REQUEST"
    assert uuid.UUID(body["request_id"]).version == 4
    assert headers["X-Correlation-ID"] == body["correlation_id"]
    assert len(sink.recorded_events) == 1
    assert sink.recorded_events[0]["request_id"] == body["request_id"]
    assert "PRIVATE_REQUEST_CANARY" not in stream.getvalue() and not reads


@pytest.mark.parametrize("path", PATHS)
def test_actual_sink_outage_is_safe_single_attempt_no_success(factory, path):
    ctrl, sink, stream, reads = factory(path, broken=True)
    with pytest.raises(ActionEventDeliveryError, match="Required action audit delivery failed") as error:
        call(ctrl, path, str(uuid.uuid4()))
    assert len(sink.attempts) == 1 and sink.recorded_events == []
    assert stream.getvalue() == "" and not reads
    assert "PRIVATE_SINK_CANARY" not in str(error.value)


@pytest.mark.parametrize("path", ["allowed", "search", "open"])
def test_missing_sink_rejects_admission_without_false_audit(factory, path):
    ctrl, sink, stream, reads = factory(path, missing=True)
    rid = str(uuid.uuid4())
    http, _, body = call(ctrl, path, rid)
    assert http == 503 and body["reason_code"] == "CAPABILITY_DISABLED"
    assert body["request_id"] == rid and body["data"] is None
    assert sink.attempts == [] and sink.recorded_events == [] and stream.getvalue() == ""
    assert not reads


def test_invalid_correlation_metadata_replaced_at_server_boundary(factory):
    ctrl, sink, stream, reads = factory()
    http, heads, body = call(ctrl, "allowed", str(uuid.uuid4()), "UNTRUSTED_CID_CANARY")
    assert http == 200 and uuid.UUID(body["correlation_id"]).version == 4
    assert heads["X-Correlation-ID"] == sink.recorded_events[0]["correlation_id"] == body["correlation_id"]
    assert "UNTRUSTED_CID_CANARY" not in stream.getvalue() and not reads
