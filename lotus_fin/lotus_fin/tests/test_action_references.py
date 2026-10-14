"""Tests for Purpose-Bound Reference Codec (Stage B3).

SSOT: CHATBOT_P1_AUTHORIZED_ACTIONS_MASTER_SSOT.md §5.
ADR001: Clean Architecture, < 200 lines, no ad-hoc scripts.
"""

import time
import uuid
import pytest
from lotus_fin.domain.model.authorized_read_context import AuthorizedReadContext
from lotus_fin.infrastructure.security.action_reference_codec import ActionReferenceCodec


def make_test_context(actor="test_user", company="Lotus Corp") -> AuthorizedReadContext:
    return AuthorizedReadContext(
        actor_id=actor,
        auth_session_binding="sid_test_123",
        site_id="site_erp",
        product_id="prod_lotus",
        connection_id="conn_main",
        connection_version="v1",
        company_id=company,
        capability="invoice.context",
        context_version="ctx_v1_fingerprint",
        observed_at_utc="2026-10-11T10:00:00Z",
        timezone="Asia/Ho_Chi_Minh",
        deadline_at_utc="2026-10-11T10:05:00Z",
        correlation_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
    )


def test_codec_valid_signing_and_verification():
    codec = ActionReferenceCodec(key_id="k1", secret_key="super_secret_key_minimum_32_bytes_long")
    ctx = make_test_context()

    token = codec.sign_reference(purpose="invoice.context", context=ctx)
    valid, err = codec.verify_reference(token, expected_purpose="invoice.context", context=ctx)
    assert valid is True
    assert err is None


def test_codec_tampered_signature_rejected():
    codec = ActionReferenceCodec(key_id="k1", secret_key="super_secret_key_minimum_32_bytes_long")
    ctx = make_test_context()

    token = codec.sign_reference(purpose="invoice.context", context=ctx)
    tampered = token[:-4] + "AAAA"
    valid, err = codec.verify_reference(tampered, expected_purpose="invoice.context", context=ctx)
    assert valid is False
    assert "Signature mismatch" in err or "Decoding failed" in err


def test_codec_purpose_mismatch_rejected():
    codec = ActionReferenceCodec(key_id="k1", secret_key="super_secret_key_minimum_32_bytes_long")
    ctx = make_test_context()

    token = codec.sign_reference(purpose="invoice.context", context=ctx)
    valid, err = codec.verify_reference(token, expected_purpose="invoice.open", context=ctx)
    assert valid is False
    assert "Purpose mismatch" in err


def test_codec_cross_actor_or_company_rejected():
    codec = ActionReferenceCodec(key_id="k1", secret_key="super_secret_key_minimum_32_bytes_long")
    ctx1 = make_test_context(actor="alice", company="Lotus Corp")
    ctx2 = make_test_context(actor="bob", company="Lotus Corp")

    token = codec.sign_reference(purpose="invoice.context", context=ctx1)
    valid, err = codec.verify_reference(token, expected_purpose="invoice.context", context=ctx2)
    assert valid is False
    assert "Actor mismatch" in err


def test_codec_expired_token_rejected():
    codec = ActionReferenceCodec(key_id="k1", secret_key="super_secret_key_minimum_32_bytes_long")
    ctx = make_test_context()

    token = codec.sign_reference(purpose="invoice.context", context=ctx, ttl_seconds=-10)
    valid, err = codec.verify_reference(token, expected_purpose="invoice.context", context=ctx)
    assert valid is False
    assert "Reference expired" in err


def test_codec_key_id_mismatch_rejected():
    codec1 = ActionReferenceCodec(key_id="k1", secret_key="super_secret_key_minimum_32_bytes_long")
    codec2 = ActionReferenceCodec(key_id="k2", secret_key="super_secret_key_minimum_32_bytes_long")
    ctx = make_test_context()

    token = codec1.sign_reference(purpose="invoice.context", context=ctx)
    valid, err = codec2.verify_reference(token, expected_purpose="invoice.context", context=ctx)
    assert valid is False
    assert "Mismatched key ID" in err
