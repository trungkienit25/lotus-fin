"""F02: site calendar boundaries, signed expiry and safe configuration failure."""
import base64
import io
import json
import logging
from datetime import datetime, date, timedelta, timezone
import pytest
from lotus_fin.tests.test_invoice_read_family_correction import family, resolve, RID
from lotus_fin.infrastructure.security import frappe_invoice_authorizer as auth_module
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.application.service.resolve_read_context import ResolveReadContextService
from lotus_fin.infrastructure.observability.action_events import SafeStructuredActionEvents
from lotus_fin.presentation.controller.invoice_actions_controller import InvoiceActionsController


def deliver(config, codec):
    stream = io.StringIO()
    log = logging.Logger("context-data-private", logging.INFO)
    handler = logging.StreamHandler(stream)
    log.addHandler(handler)
    sink = SafeStructuredActionEvents(log)
    try:
        controller = InvoiceActionsController(config,
            ResolveReadContextService(auth_module.FrappeInvoiceAuthorizer(config)), codec, sink)
        response = controller.get_context({"request_id": RID, "company_candidate": "Company A"})
        assert len(sink.recorded_events) == 1
        return response
    finally:
        log.removeHandler(handler)
        handler.close()
        stream.close()


@pytest.mark.parametrize("instant,tz,expected", [
    ("2026-12-31T17:00:00+00:00", "Asia/Ho_Chi_Minh", "2027-01-01"),
    ("2026-10-31T17:00:00+00:00", "Asia/Ho_Chi_Minh", "2026-11-01"),
    ("2024-02-29T17:00:00+00:00", "Asia/Ho_Chi_Minh", "2024-03-01"),
    ("2026-01-01T00:30:00+00:00", "America/Los_Angeles", "2025-12-31"),
])
def test_exact_inclusive_site_date_defaults(family, monkeypatch, instant, tz, expected):
    framework, config, _ = family
    framework.get_system_settings = lambda key: tz if key == "time_zone" else None
    frozen = datetime.fromisoformat(instant)
    class Clock(datetime):
        @classmethod
        def now(cls, zone=None):
            return frozen.astimezone(zone) if zone else frozen.replace(tzinfo=None)
    monkeypatch.setattr(auth_module, "datetime", Clock)
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    http, _, body = deliver(config, codec)
    assert http == 200
    data = body["data"]
    assert data["default_posting_to"] == expected
    assert data["default_posting_from"] == (date.fromisoformat(expected) - timedelta(days=89)).isoformat()
    assert body["source"]["timezone"] == tz


@pytest.mark.parametrize("ttl,deadline", [(60, 1000), (300, 5000), (600, 30000)])
def test_expiry_exactly_matches_signed_claim_not_deadline(family, ttl, deadline):
    _, config, _ = family
    config = config.model_copy(update={"reference_ttl_seconds": ttl, "deadline_ms": deadline})
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    http, _, body = deliver(config, codec)
    assert http == 200
    data = body["data"]
    segment = data["context_ref"].split(".")[2]
    claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
    assert datetime.fromisoformat(data["expires_at"]).timestamp() == claims["expires_at"]
    assert claims["expires_at"] - claims["issued_at"] == ttl
    assert datetime.fromisoformat(data["expires_at"]) > datetime.now(timezone.utc) + timedelta(seconds=deadline / 1000)
    assert set(data) == {"context_ref", "context_version", "company_label", "allowed_filters",
        "default_posting_from", "default_posting_to", "expires_at"}
    assert config.signing_secret not in str(body)


def test_effective_codec_expiry_is_not_fabricated_from_config(family, monkeypatch):
    _, config, _ = family
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    original = codec.sign_reference
    monkeypatch.setattr(codec, "sign_reference", lambda **kw: original(**{**kw, "ttl_seconds": 60}))
    http, _, body = deliver(config, codec)
    assert http == 200
    data = body["data"]
    payload = data["context_ref"].split(".")[2]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    assert datetime.fromisoformat(data["expires_at"]).timestamp() == claims["expires_at"]
    assert claims["expires_at"] - claims["issued_at"] == 60


@pytest.mark.parametrize("value", [None, "", "Invalid/Zone", 7])
def test_missing_invalid_site_timezone_fails_safely(family, value):
    framework, config, _ = family
    framework.get_system_settings = lambda key: value
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    http, _, body = deliver(config, codec)
    assert http == 503 and body["reason_code"] == "TARGET_UNQUALIFIED"
    assert body["data"] is body["source"] is None


def test_missing_timezone_interface_fails_safely(family):
    framework, config, _ = family
    del framework.get_system_settings
    http, _, body = deliver(config, ActionReferenceCodec(config.signing_key_id, config.signing_secret))
    assert http == 503 and body["data"] is None


def test_timezone_change_invalidates_old_context(family):
    framework, config, _ = family
    codec = ActionReferenceCodec(config.signing_key_id, config.signing_secret)
    old = resolve(config, "invoice.context")
    token = codec.sign_reference("invoice.context", old)
    framework.get_system_settings = lambda key: "America/Los_Angeles"
    current = resolve(config, "invoice.search")
    assert current.context_version != old.context_version
    assert codec.verify_reference(token, "invoice.context", current)[0] is False
