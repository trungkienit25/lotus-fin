"""Authenticated malformed claims/cursor oracle, synthetic signing material only."""
import base64
import hashlib
import hmac
import json
import pytest
from lotus_fin.domain.schema.invoice_read import InvoiceReadFilters
from lotus_fin.domain.schema.action_outcome import ActionStatus as S, ActionReasonCode as R
from lotus_fin.application.service.search_invoices import SearchInvoicesService
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec
from lotus_fin.tests.test_invoice_read_security import fixture


def recode(codec, token, mutate=None, duplicate=False):
    segment = token.split(".")[2]
    claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
    if mutate: mutate(claims)
    wire = json.dumps(claims, separators=(",", ":"))
    if duplicate: wire = wire[:-1] + ',"doc_id":"INV-B"}'
    raw = wire.encode()
    encode = lambda data: base64.urlsafe_b64encode(data).decode().rstrip("=")
    return "ref.v2." + encode(raw) + "." + encode(hmac.digest(codec.secret_key, raw, "sha256"))


@pytest.mark.parametrize("axis", ["actor_id", "auth_session_binding", "site_id", "product_id", "connection_id",
    "connection_version", "company_id", "context_version"])
def test_scope_axes_reject_even_after_expiry(fixture, axis):
    ctx, _, _, _, _, _, codec = fixture
    token = codec.sign_selection_v2(ctx, "INV-A", "rev1", ttl_seconds=-10)
    foreign = ctx.model_copy(update={axis: "foreign"})
    valid, claims, error = codec.verify_selection_v2(token, foreign)
    assert not valid and claims is None and error != "Reference expired."


@pytest.mark.parametrize("key", ["contract_version", "query_fingerprint", "purpose", "binding_version", "doc_type"])
def test_missing_authenticated_claim_not_repaired(fixture, key):
    ctx, _, _, _, _, _, codec = fixture
    token = recode(codec, codec.sign_selection_v2(ctx, "INV-A", "rev1"), lambda data: data.pop(key))
    assert codec.verify_selection_v2(token, ctx)[0] is False


def test_duplicate_keys_are_rejected(fixture):
    ctx, _, _, _, _, _, codec = fixture
    token = recode(codec, codec.sign_selection_v2(ctx, "INV-A", "rev1"), duplicate=True)
    assert codec.verify_selection_v2(token, ctx)[0] is False


def test_expiry_equality_and_retired_key(fixture, monkeypatch):
    ctx, _, _, _, _, _, codec = fixture
    token = codec.sign_selection_v2(ctx, "INV-A", "rev1")
    valid, claims, _ = codec.verify_selection_v2(token, ctx)
    assert valid
    monkeypatch.setattr("time.time", lambda: claims.expires_at)
    assert codec.verify_selection_v2(token, ctx) == (False, None, "Reference expired.")
    assert ActionReferenceCodec("retired", "r" * 32).verify_selection_v2(token, ctx)[0] is False


def test_p2_public_claims_are_private(fixture):
    ctx, _, _, _, _, _, codec = fixture
    ctx = ctx.model_copy(update={"actor_id": "private-actor-canary@example.invalid"})
    token = codec.sign_selection_v2(ctx, "INV-A", "rev1")
    segment = token.split(".")[2]
    wire = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)).decode()
    assert ctx.actor_id not in wire and ctx.auth_session_binding not in wire and "s" * 32 not in wire


@pytest.mark.parametrize("change", ["query", "page-size", "expired"])
def test_authenticated_cursor_staleness_before_port(fixture, change):
    ctx, src, _, page, _, port, codec = fixture
    from datetime import datetime
    from zoneinfo import ZoneInfo
    filters = InvoiceReadFilters().normalized(datetime.fromisoformat(ctx.observed_at_utc).astimezone(ZoneInfo(ctx.timezone)).date())
    digest = filters.fingerprint(20)
    token = codec.sign_cursor_v2(ctx, "a" * 64 if change == "query" else digest,
        "INV-A", "INV-Z", 2, 19 if change == "page-size" else 20,
        ttl_seconds=-10 if change == "expired" else 300)
    port.result = page, src, S.OK, R.RESULTS_FOUND
    result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20, token)
    assert result == (None, None, S.NOT_AVAILABLE, R.STALE_CURSOR) and port.calls == 0


def test_valid_cursor_next_page_and_window_limit(fixture):
    ctx, src, _, page, _, port, codec = fixture
    from datetime import datetime
    from zoneinfo import ZoneInfo
    filters = InvoiceReadFilters().normalized(datetime.fromisoformat(ctx.observed_at_utc).astimezone(ZoneInfo(ctx.timezone)).date())
    digest = filters.fingerprint(20)
    port.result = page, src, S.OK, R.RESULTS_FOUND
    cursor = codec.sign_cursor_v2(ctx, digest, "INV-0", "INV-Z", 2, 20)
    assert SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20, cursor)[2] == S.OK
    port.result = page.model_copy(update={"has_more": True}), src, S.OK, R.RESULTS_FOUND
    cursor = codec.sign_cursor_v2(ctx, digest, "INV-0", "INV-Z", 5, 20)
    result = SearchInvoicesService(port, codec).execute(ctx, InvoiceReadFilters(), 20, cursor)
    assert result[2:] == (S.PARTIAL, R.COVERAGE_INCOMPLETE) and result[0].items[0].selection_ref is None
