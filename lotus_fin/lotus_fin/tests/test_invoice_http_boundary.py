"""Request/response boundary tests, not qualified live Frappe HTTP acceptance."""

import json
import sys
from types import SimpleNamespace
import pytest
from werkzeug.wrappers import Request, Response
from lotus_fin.api.invoice_actions_api import _frappe_post_handler

RID = "12345678-1234-4234-8234-123456789012"
CAPS = ["invoice.context", "invoice.search", "invoice.open"]


def valid_body(cap):
    base = {"request_id": RID}
    if cap == "invoice.context":
        return {**base, "company_candidate": "Synthetic Company"}
    base.update(context_ref="ref.v1.synthetic.only", expected_context_version="scope")
    return {**base, "filters": {}} if cap == "invoice.search" else {**base, "selection_ref": "ref.v2.synthetic.only"}


def invoke(monkeypatch, cap, data=None, *, user="ordinary@example.invalid", method="POST", raw=None,
           content_type="application/json"):
    request = Request.from_values(method=method, data=raw if raw is not None else json.dumps(data or valid_body(cap)),
                                  content_type=content_type)
    f = SimpleNamespace(request=request, session=SimpleNamespace(user=user), response=SimpleNamespace(),
                        form_dict={"request_id": RID})
    monkeypatch.setitem(sys.modules, "frappe", f)
    return _frappe_post_handler(cap)


def outcome(response):
    assert isinstance(response, Response), "Frappe must bypass automatic dictionary wrapping"
    wire = response.get_json()
    assert set(wire) == {"message"}
    body = wire["message"]
    assert "message" not in body
    assert body["data"] is None and body["source"] is None
    assert response.headers["X-Correlation-ID"] == body["correlation_id"]
    assert "no-store" in response.headers["Cache-Control"]
    assert "private" in response.headers["Cache-Control"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    return body


@pytest.mark.parametrize("cap", CAPS)
def test_valid_authenticated_request_is_truthfully_disabled(monkeypatch, cap):
    response = invoke(monkeypatch, cap)
    body = outcome(response)
    assert response.status_code == 503
    assert body["reason_code"] == "CAPABILITY_DISABLED"
    assert body["request_id"] == RID and body["capability"] == cap


@pytest.mark.parametrize("user", [None, "", "Guest"])
def test_missing_identity_denied_before_request_parsing(monkeypatch, user):
    response = invoke(monkeypatch, CAPS[0], user=user, raw="{" * 20000)
    assert response.status_code == 401
    assert outcome(response)["reason_code"] == "AUTH_REQUIRED"


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_non_post_denied(monkeypatch, method):
    response = invoke(monkeypatch, CAPS[0], method=method)
    assert response.status_code == 405
    outcome(response)


@pytest.mark.parametrize("raw", [
    '{"request_id":"' + RID + '","request_id":"' + RID + '","company_candidate":"A"}',
    '{"request_id":"' + RID + '","company_candidate":"A","nested":{"x":1,"x":2}}',
    '[]', 'null', 'false', '{', '{"company_candidate":NaN}',
])
def test_invalid_json_is_rejected_without_echoing_input(monkeypatch, raw):
    response = invoke(monkeypatch, CAPS[0], raw=raw)
    assert response.status_code == 422
    assert outcome(response)["reason_code"] == "INVALID_REQUEST"
    assert outcome(response)["user_message"] == "Yêu cầu không hợp lệ hoặc sai định dạng."
    assert not ({"exception", "traceback", "input", "nested"} & set(response.get_json()["message"]))


def test_body_limit_before_json_decode(monkeypatch):
    response = invoke(monkeypatch, CAPS[0], raw='{"secret":"' + "x" * 17000 + '"}')
    assert response.status_code == 413
    assert outcome(response)["reason_code"] == "INVALID_REQUEST"


@pytest.mark.parametrize("content_type", ["text/plain", "application/x-www-form-urlencoded"])
def test_form_dict_does_not_bypass_json_contract(monkeypatch, content_type):
    response = invoke(monkeypatch, CAPS[0], content_type=content_type)
    assert response.status_code == 422
    assert outcome(response)["reason_code"] == "INVALID_REQUEST"


@pytest.mark.parametrize("cap", CAPS)
def test_extra_authority_fields_rejected(monkeypatch, cap):
    response = invoke(monkeypatch, cap, {**valid_body(cap), "actor": "Administrator"})
    assert response.status_code == 422
    assert outcome(response)["reason_code"] == "INVALID_REQUEST"


def test_cid_is_generated_per_request(monkeypatch):
    first = outcome(invoke(monkeypatch, CAPS[0]))["correlation_id"]
    second = outcome(invoke(monkeypatch, CAPS[0]))["correlation_id"]
    assert first != second
