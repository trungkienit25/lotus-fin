"""F01: keyed actor privacy and complete reference binding; offline only."""

import base64
import hashlib
import hmac
import io
import json
import logging
import sys
import types
import uuid
import pytest
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.infrastructure.config.invoice_actions_config import ApprovedConnection, InvoiceActionsConfig
from lotus_fin.infrastructure.security.frappe_invoice_authorizer import FrappeInvoiceAuthorizer
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents
from lotus_fin.presentation.controller.invoice_actions_controller import InvoiceActionsController

ACTOR, SID, KEY = "private.actor@example.invalid", "PRIVATE_TEST_SID", "test-key-material-" * 3


@pytest.fixture
def foundation(monkeypatch):
    f = types.ModuleType("frappe")
    f.session = types.SimpleNamespace(user=ACTOR, sid=SID)
    f.local = types.SimpleNamespace(site="site")
    f.get_system_settings = lambda key: "Asia/Ho_Chi_Minh"
    f.has_permission = lambda dt, **kw: (dt, kw) == (
        "Company", dict(ptype="read", doc="Company A", user=ACTOR))
    monkeypatch.setitem(sys.modules, "frappe", f)
    conn = ApprovedConnection(product_id="prod", site_id="site", connection_id="conn",
                              connection_version="v1", allowed_companies=["Company A"])
    cfg = InvoiceActionsConfig(enabled=True, signing_key_id="test-key", signing_secret=KEY,
                               connections={"site": conn})
    auth = FrappeInvoiceAuthorizer(cfg)
    ctx, check = auth.resolve_context("Company A", "invoice.context", str(uuid.uuid4()), str(uuid.uuid4()))
    assert check.is_authorized
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.Logger("test.private.actor", logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    codec = ActionReferenceCodec("test-key", KEY)
    ctrl = InvoiceActionsController(cfg, ResolveReadContextService(auth), codec,
                                    SafeStructuredActionEvents(logger))
    yield codec, ctx, ctrl, stream
    logger.removeHandler(handler)
    handler.close()


def payload(token):
    part = token.split(".")[2]
    return json.loads(base64.urlsafe_b64decode(part + "=" * ((-len(part)) % 4)))


def encode_signed(claims):
    data = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode()
    part = base64.urlsafe_b64encode(data).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(hmac.new(KEY.encode(), data, hashlib.sha256).digest()).decode().rstrip("=")
    return f"ref.v1.{part}.{sig}"


def test_controller_reference_decoding_reveals_no_actor_session_key(foundation):
    codec, ctx, ctrl, stream = foundation
    http, _, body = ctrl.get_context(dict(request_id=str(uuid.uuid4()), company_candidate="Company A"))
    assert http == 200
    token = body["data"]["context_ref"]
    claims = payload(token)
    assert claims["actor_id"] != ACTOR and claims["actor_id"].startswith("aref_")
    assert claims["auth_session_binding"].startswith("sref_")
    for secret in [ACTOR, SID, KEY]:
        assert secret not in json.dumps(claims) and secret not in json.dumps(body)
        assert secret not in stream.getvalue()
    assert codec.verify_reference(token, "invoice.context", ctx) == (True, None)


@pytest.mark.parametrize("field,value", [
    ("actor_id", "other@example.invalid"), ("auth_session_binding", "other-session"),
    ("site_id", "other-site"), ("product_id", "other-product"),
    ("company_id", "Company B"), ("connection_id", "other-connection"),
    ("connection_version", "v2"), ("context_version", "ctx_changed"),
    ("projection_version", "invoice.min.v2"),
])
def test_changed_context_never_verifies(foundation, field, value):
    codec, ctx, _, _ = foundation
    token = codec.sign_reference("invoice.context", ctx)
    assert codec.verify_reference(token, "invoice.context", ctx)[0]
    valid, error = codec.verify_reference(token, "invoice.context", ctx.model_copy(update={field: value}))
    assert not valid
    assert ACTOR not in error and SID not in error and KEY not in error


def test_legacy_signed_raw_actor_claims_fail_closed(foundation):
    codec, ctx, _, _ = foundation
    claims = payload(codec.sign_reference("invoice.context", ctx))
    claims["actor_id"] = ACTOR
    claims.pop("binding_version", None)
    claims.pop("projection_version", None)
    assert not codec.verify_reference(encode_signed(claims), "invoice.context", ctx)[0]


@pytest.mark.parametrize("purpose", ["invoice.context", "invoice.open", "invoice.cursor"])
def test_privacy_preserves_purpose_mac_key_and_expiry(foundation, purpose):
    codec, ctx, _, _ = foundation
    token = codec.sign_reference(purpose, ctx)
    assert codec.verify_reference(token, purpose, ctx)[0]
    assert not codec.verify_reference(token, "invoice.cursor" if purpose != "invoice.cursor" else "invoice.open", ctx)[0]
    assert not codec.verify_reference(token[:-6] + "AAAAAA", purpose, ctx)[0]
    assert not codec.verify_reference(codec.sign_reference(purpose, ctx, ttl_seconds=-1), purpose, ctx)[0]
    assert not ActionReferenceCodec("other-key", KEY).verify_reference(token, purpose, ctx)[0]
    claims = payload(token)
    assert claims["actor_id"] != ACTOR and claims["actor_id"] != claims["auth_session_binding"]
