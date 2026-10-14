"""Final delivery revalidation: mutated denial/source, safe terminal metadata."""

import json
import uuid
import pytest
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R
from lotus_fin.presentation.response.invoice_action_delivery import InvoiceActionDelivery
from lotus_fin.tests.test_action_denial_policy import outcome
from lotus_fin.tests.test_invoice_terminal_delivery import factory


@pytest.mark.parametrize("status", [S.OK, S.PARTIAL])
@pytest.mark.parametrize("reason", ["AUTH_REQUIRED", "CSRF_OR_ORIGIN_DENIED",
    "COMPANY_DENIED", "CAPABILITY_DENIED", "ACCESS_DENIED"])
def test_mutated_nested_denial_delivers_null_forbidden_once(factory, status, reason):
    _, sink, stream, reads = factory()
    value = outcome(status, {"items": []})
    value.data = {"items": [{"reason_code": reason, "private": "PROTECTED_CANARY"}]}
    http, headers, body = InvoiceActionDelivery(sink).complete(value)
    assert http == 403 and body["status"] == "FORBIDDEN"
    assert body["reason_code"] == "ACCESS_DENIED"
    assert body["data"] is None and body["source"] is None
    assert body["request_id"] == value.request_id
    assert headers["X-Correlation-ID"] == value.correlation_id
    assert len(sink.attempts) == len(sink.recorded_events) == 1
    assert "PROTECTED_CANARY" not in json.dumps(body) + stream.getvalue()
    assert not reads


@pytest.mark.parametrize("mutation", ["unknown_shape", "source"])
def test_invalid_mutated_success_safe_source_error_once(factory, mutation):
    _, sink, stream, reads = factory()
    value = outcome(data={"items": []})
    if mutation == "source":
        value.source.observed_at = "PRIVATE_PROVIDER_CANARY"
    else:
        value.data = {"result": {"status": "PRIVATE_PROVIDER_CANARY"}}
    http, _, body = InvoiceActionDelivery(sink).complete(value)
    assert http == 502 and body["reason_code"] == "INVALID_PROVIDER_RESPONSE"
    assert body["data"] is None and body["source"] is None
    assert len(sink.attempts) == len(sink.recorded_events) == 1
    assert "PRIVATE_PROVIDER_CANARY" not in json.dumps(body) + stream.getvalue()
    assert not reads


@pytest.mark.parametrize("status", [S.OK, S.PARTIAL])
def test_benign_delivery_and_audit_are_consistent(factory, status):
    _, sink, stream, reads = factory()
    value = outcome(status, {"items": []})
    http, _, body = InvoiceActionDelivery(sink).complete(value)
    assert http == 200 and body["status"] == status and body["data"] == {"items": []}
    assert len(sink.attempts) == len(sink.recorded_events) == 1
    assert [json.loads(line) for line in stream.getvalue().splitlines()] == sink.recorded_events
    assert not reads


@pytest.mark.parametrize("reason,http", [(R.AUTH_REQUIRED, 401), (R.COMPANY_DENIED, 403)])
def test_root_denial_survives_bad_request_id(factory, reason, http):
    _, sink, stream, reads = factory()
    code, _, body = InvoiceActionDelivery(sink).failure(
        S.FORBIDDEN, reason, "invoice.context", "PRIVATE_REQUEST_CANARY", str(uuid.uuid4()))
    assert code == http and body["reason_code"] == reason
    assert uuid.UUID(body["request_id"]).version == 4
    assert body["data"] is None and body["source"] is None
    assert len(sink.attempts) == len(sink.recorded_events) == 1
    assert "PRIVATE_REQUEST_CANARY" not in stream.getvalue() and not reads
